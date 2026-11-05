from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import importlib.metadata
import io
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from lecture_notes.config import ensure_runtime_output, settings
from lecture_notes.echo360 import EchoClient, EchoError, build_resolver_manifest
from lecture_notes.manifests import atomic_write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-slides")
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser("extract-pdf", help="Eralda PDF-i lehekülgede tekst JSON-i")
    extract.add_argument("--input", type=Path, required=True)
    extract.add_argument("--output-dir", type=Path, required=True)
    extract.add_argument("--document-id", required=True)

    frames = subparsers.add_parser("extract-frames", help="Eralda Echo videost ajastatud kaadrid ja OCR")
    frames.add_argument("public_url")
    frames.add_argument("--lesson-id", required=True)
    frames.add_argument("--output-dir", type=Path, required=True)
    frames.add_argument("--start-seconds", type=float, required=True)
    frames.add_argument("--end-seconds", type=float, required=True)
    frames.add_argument("--interval-seconds", type=float, default=30.0)

    process = subparsers.add_parser("process", help="Tuvasta videost slaidid ja ühenda need valmis transkriptiga")
    process.add_argument("public_url")
    process.add_argument("--lesson-id", required=True)
    process.add_argument("--transcript", type=Path, required=True)
    process.add_argument("--output-dir", type=Path, required=True)
    process.add_argument("--slides-input", type=Path)
    process.add_argument("--coarse-seconds", type=float, default=20.0)
    process.add_argument("--refine-seconds", type=float, default=2.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = settings()
    try:
        output_dir = ensure_runtime_output(args.output_dir, config)
        if args.command == "extract-pdf":
            source = args.input.resolve()
            if not source.is_file():
                raise ValueError(f"PDF does not exist: {source}")
            result = extract_pdf(source, args.document_id)
            atomic_write_json(output_dir / "document.json", result)
            (output_dir / "document.txt").write_text(
                "\n\n".join(f"--- page {page['page_number']} ---\n{page['text']}" for page in result["pages"]),
                encoding="utf-8",
            )
            print(json.dumps({"status": "ok", "output": str(output_dir), "page_count": result["page_count"]}, sort_keys=True))
            return 0

        if args.command == "extract-frames":
            if args.end_seconds <= args.start_seconds or args.interval_seconds <= 0:
                raise ValueError("Invalid frame extraction interval")
            result = extract_frames(
                public_url=args.public_url,
                lesson_id=args.lesson_id,
                output_dir=output_dir,
                work_root=config.work_root,
                start_seconds=args.start_seconds,
                end_seconds=args.end_seconds,
                interval_seconds=args.interval_seconds,
            )
            print(json.dumps({"status": "ok", "output": str(output_dir), "frame_count": result["frame_count"]}, sort_keys=True))
            return 0

        if args.command == "process":
            if args.coarse_seconds <= 0 or args.refine_seconds <= 0:
                raise ValueError("Coarse and refinement intervals must be positive")
            if args.refine_seconds > args.coarse_seconds:
                raise ValueError("Refinement interval must not exceed the coarse interval")
            transcript_path = args.transcript.resolve()
            if not transcript_path.is_file():
                raise ValueError(f"Transcript does not exist: {transcript_path}")
            slides_input = args.slides_input.resolve() if args.slides_input else None
            if slides_input is not None and not slides_input.is_file():
                raise ValueError(f"Slide input does not exist: {slides_input}")
            result = process_slides(
                public_url=args.public_url,
                lesson_id=args.lesson_id,
                transcript_path=transcript_path,
                slides_input=slides_input,
                output_dir=output_dir,
                work_root=config.work_root,
                coarse_seconds=args.coarse_seconds,
                refine_seconds=args.refine_seconds,
            )
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "output": str(output_dir),
                        "slide_count": result["slide_count"],
                        "appearance_count": result["appearance_count"],
                    },
                    sort_keys=True,
                )
            )
            return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, EchoError) as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)[:1000]}), file=sys.stderr)
        return 2
    return 2


def extract_frames(
    *,
    public_url: str,
    lesson_id: str,
    output_dir: Path,
    work_root: Path,
    start_seconds: float,
    end_seconds: float,
    interval_seconds: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    client = EchoClient(timeout_seconds=60.0)
    resolver = build_resolver_manifest(client, public_url)
    if not any(item.get("lesson_id") == lesson_id for item in resolver["lessons"]):
        raise ValueError("Lesson does not belong to the resolved course")
    media = client.get_lesson_media(lesson_id)
    video_url, expected_size, width, height = select_video_source(media)
    work_key = hashlib.sha256(f"{lesson_id}:frames".encode("utf-8")).hexdigest()[:16]
    work_dir = work_root / "slides" / work_key
    video_path = work_dir / "source.mp4"
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    try:
        download = client.download_media(video_url, video_path)
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start_seconds),
            "-i",
            str(video_path),
            "-t",
            str(end_seconds - start_seconds),
            "-vf",
            f"fps=1/{interval_seconds}",
            "-q:v",
            "2",
            str(frames_dir / "frame_%03d.jpg"),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        frames: list[dict[str, Any]] = []
        for index, frame_path in enumerate(sorted(frames_dir.glob("frame_*.jpg"))):
            timestamp = start_seconds + index * interval_seconds
            ocr = subprocess.run(
                ["tesseract", str(frame_path), "stdout", "-l", "est+eng"],
                check=True,
                capture_output=True,
                text=True,
            )
            frames.append(
                {
                    "id": f"frame_{round(timestamp * 1000):010d}",
                    "timestamp_seconds": round(timestamp, 3),
                    "path": str(frame_path),
                    "sha256": _file_sha256(frame_path),
                    "ocr_text": ocr.stdout.strip(),
                    "review_status": "unreviewed",
                }
            )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    manifest = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "lesson_id": lesson_id,
        "source": {
            "kind": "primary_video",
            "width": width,
            "height": height,
            "expected_size_bytes": expected_size,
            "download_size_bytes": download["size_bytes"],
            "download_sha256": download["sha256"],
            "temporary_video_removed": not video_path.exists(),
            "source_host": download["source_host"],
            "source_path": download["source_path"],
            "source_query_persisted": False,
        },
        "selection": {
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "interval_seconds": interval_seconds,
        },
        "tools": {
            "ffmpeg": _tool_version(["ffmpeg", "-version"]),
            "tesseract": _tool_version(["tesseract", "--version"]),
            "ocr_languages": ["est", "eng"],
        },
        "duration_seconds": round(time.perf_counter() - started, 3),
        "frame_count": len(frames),
        "frames": frames,
    }
    atomic_write_json(output_dir / "frames.json", manifest)
    return manifest


def select_video_source(media_payload: dict[str, Any]) -> tuple[str, int | None, int | None, int | None]:
    return select_video_source_by_quality(media_payload, prefer_highest=False)


def select_video_source_by_quality(
    media_payload: dict[str, Any], *, prefer_highest: bool
) -> tuple[str, int | None, int | None, int | None]:
    video = media_payload.get("video") if isinstance(media_payload.get("video"), dict) else None
    wrapper = video.get("media") if isinstance(video, dict) and isinstance(video.get("media"), dict) else None
    media = wrapper.get("media") if isinstance(wrapper, dict) and isinstance(wrapper.get("media"), dict) else None
    current = media.get("current") if isinstance(media, dict) and isinstance(media.get("current"), dict) else None
    primary = current.get("primaryFiles") if isinstance(current, dict) else None
    if not isinstance(primary, list):
        raise ValueError("Lesson has no primary video source")
    candidates = [item for item in primary if isinstance(item, dict) and isinstance(item.get("s3Url"), str)]
    if not candidates:
        raise ValueError("Lesson has no downloadable primary video source")
    if prefer_highest:
        selected = max(candidates, key=lambda item: (item.get("height") or 0, item.get("size") or 0))
    else:
        selected = min(candidates, key=lambda item: (item.get("height") or 100000, item.get("size") or 1000000000000))
    return selected["s3Url"], selected.get("size"), selected.get("width"), selected.get("height")


def _tool_version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return (result.stdout or result.stderr).splitlines()[0]


def extract_pdf(source: Path, document_id: str) -> dict[str, Any]:
    import pymupdf

    document = pymupdf.open(source)
    pages = [
        {"page_number": index + 1, "text": page.get_text("text", sort=True).strip()}
        for index, page in enumerate(document)
    ]
    metadata = {key: value for key, value in document.metadata.items() if value}
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "document_id": document_id,
        "source": {
            "filename": source.name,
            "sha256": _file_sha256(source),
            "size_bytes": source.stat().st_size,
        },
        "extractor": {"name": "PyMuPDF", "version": importlib.metadata.version("PyMuPDF")},
        "metadata": metadata,
        "page_count": len(pages),
        "pages": pages,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


SLIDE_PIPELINE_VERSION = "video-slides-v5"
SIGNATURE_SIZE = (160, 90)
SIGNATURE_COLOR_MODE = "RGB"
CHANGE_DISTANCE = 0.020
STABLE_DISTANCE = 0.025
DUPLICATE_DISTANCE = 0.012
ANIMATION_DISTANCE = 0.18


def process_slides(
    *,
    public_url: str,
    lesson_id: str,
    transcript_path: Path,
    slides_input: Path | None,
    output_dir: Path,
    work_root: Path,
    coarse_seconds: float,
    refine_seconds: float,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    run_path = output_dir / "run.json"
    work_key = hashlib.sha256(f"{lesson_id}:slide-pipeline".encode("utf-8")).hexdigest()[:16]
    work_dir = work_root / "slides" / work_key
    video_path = work_dir / "source.mp4"
    sampled_dir = work_dir / "sampled"
    atomic_write_json(
        run_path,
        {
            "schema_version": "1.0",
            "status": "running",
            "started_at": _utc_now(),
            "lesson_id": lesson_id,
            "pipeline_version": SLIDE_PIPELINE_VERSION,
        },
    )
    try:
        transcript = _read_object(transcript_path)
        transcript_lesson_id = transcript.get("lesson", {}).get("lesson_id")
        if transcript_lesson_id != lesson_id:
            raise ValueError("Transcript lesson ID does not match requested lesson")

        client = EchoClient(timeout_seconds=60.0)
        resolver = build_resolver_manifest(client, public_url)
        lesson = next((item for item in resolver["lessons"] if item.get("lesson_id") == lesson_id), None)
        if lesson is None:
            raise ValueError("Lesson does not belong to the resolved course")
        media = client.get_lesson_media(lesson_id)
        video_url, expected_size, width, height = select_video_source_by_quality(media, prefer_highest=True)

        shutil.rmtree(work_dir, ignore_errors=True)
        sampled_dir.mkdir(parents=True, exist_ok=True)
        download = client.download_media(video_url, video_path)
        duration_seconds = _video_duration(video_path)
        references: list[dict[str, Any]] = []
        reference_manifest: dict[str, Any] | None = None
        if slides_input is not None:
            references, reference_manifest = _render_reference_slides(
                slides_input,
                output_dir / "reference",
                work_dir / "reference-work",
            )

        candidates, sampling = _find_adaptive_slide_candidates(
            video_path,
            sampled_dir,
            duration_seconds,
            coarse_seconds,
            refine_seconds,
        )
        if references:
            _add_reference_matching_ocr(candidates)
            _annotate_candidate_reference_hints(candidates, references)
        identities, appearances = _build_slide_identities(candidates)
        if references:
            _match_reference_slides(identities, references)

        _write_slide_images(identities, output_dir / "images")
        manifest = _slide_manifest(
            lesson=lesson,
            duration_seconds=duration_seconds,
            identities=identities,
            appearances=appearances,
            sampling=sampling,
            reference_manifest=reference_manifest,
            video={
                "width": width,
                "height": height,
                "expected_size_bytes": expected_size,
                "download_size_bytes": download["size_bytes"],
                "download_sha256": download["sha256"],
                "source_host": download["source_host"],
                "source_path": download["source_path"],
                "source_query_persisted": False,
            },
            coarse_seconds=coarse_seconds,
            refine_seconds=refine_seconds,
        )
        atomic_write_json(output_dir / "slides.json", manifest)
        merged = _render_transcript_with_slides(transcript, identities, appearances)
        (output_dir / "transcript_with_slides.md").write_text(merged, encoding="utf-8")
        result = {
            "slide_count": len(identities),
            "appearance_count": len(appearances),
            "duration_seconds": round(time.perf_counter() - started, 3),
        }
        shutil.rmtree(work_dir, ignore_errors=True)
        atomic_write_json(
            run_path,
            {
                "schema_version": "1.0",
                "status": "completed",
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "completed_at": _utc_now(),
                "duration_seconds": result["duration_seconds"],
                "lesson_id": lesson_id,
                "pipeline_version": SLIDE_PIPELINE_VERSION,
                "slide_count": result["slide_count"],
                "appearance_count": result["appearance_count"],
                "temporary_video_removed": not video_path.exists(),
            },
        )
        return result
    except Exception as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        atomic_write_json(
            run_path,
            {
                "schema_version": "1.0",
                "status": "failed",
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "completed_at": _utc_now(),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "lesson_id": lesson_id,
                "pipeline_version": SLIDE_PIPELINE_VERSION,
                "temporary_video_removed": not video_path.exists(),
                "error": {"type": type(exc).__name__, "message": str(exc)[:2000]},
            },
        )
        raise


def _video_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(result.stdout.strip()), 3)


def _extract_frame_interval(
    video_path: Path,
    output_dir: Path,
    *,
    prefix: str,
    start_seconds: float,
    end_seconds: float,
    interval_seconds: float,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = max(0.0, end_seconds - start_seconds)
    if duration <= 0:
        return []
    pattern = output_dir / f"{prefix}_%06d.jpg"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            str(start_seconds),
            "-i",
            str(video_path),
            "-t",
            str(duration),
            "-vf",
            f"fps=1/{interval_seconds},scale=1280:-2:force_original_aspect_ratio=decrease",
            "-q:v",
            "3",
            str(pattern),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        {
            "timestamp_seconds": round(start_seconds + index * interval_seconds, 3),
            "path": path,
        }
        for index, path in enumerate(sorted(output_dir.glob(f"{prefix}_*.jpg")))
    ]


def _image_signature(path: Path, size: tuple[int, int] = SIGNATURE_SIZE) -> tuple[int, ...]:
    from PIL import Image

    with Image.open(path) as image:
        rgb = image.convert(SIGNATURE_COLOR_MODE).resize(size)
        return tuple(channel for pixel in rgb.getdata() for channel in pixel)


def image_distance(left: tuple[int, ...], right: tuple[int, ...]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("Image signatures must have the same non-zero length")
    return sum(abs(a - b) for a, b in zip(left, right, strict=True)) / (len(left) * 255)


def _find_adaptive_slide_candidates(
    video_path: Path,
    sampled_dir: Path,
    duration_seconds: float,
    coarse_seconds: float,
    refine_seconds: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    coarse_dir = sampled_dir / "coarse"
    refined_dir = sampled_dir / "refined"
    coarse = _extract_frame_interval(
        video_path,
        coarse_dir,
        prefix="coarse",
        start_seconds=0.0,
        end_seconds=duration_seconds + min(coarse_seconds, 0.5),
        interval_seconds=coarse_seconds,
    )
    if not coarse:
        raise RuntimeError("Video coarse sampling produced no frames")
    for item in coarse:
        item["signature"] = _image_signature(item["path"])

    changed_windows: list[dict[str, float]] = []
    for left, right in zip(coarse, coarse[1:], strict=False):
        difference = image_distance(left["signature"], right["signature"])
        if difference >= CHANGE_DISTANCE:
            changed_windows.append(
                {
                    "start_seconds": left["timestamp_seconds"],
                    "end_seconds": right["timestamp_seconds"],
                    "coarse_difference": round(difference, 6),
                }
            )

    sampled_by_time: dict[float, dict[str, Any]] = {
        float(coarse[0]["timestamp_seconds"]): coarse[0]
    }
    refinement_frame_count = 0
    for index, window in enumerate(changed_windows):
        refined = _extract_frame_interval(
            video_path,
            refined_dir,
            prefix=f"window_{index:04d}",
            start_seconds=window["start_seconds"],
            end_seconds=min(duration_seconds, window["end_seconds"] + refine_seconds),
            interval_seconds=refine_seconds,
        )
        refinement_frame_count += len(refined)
        for item in refined:
            timestamp = float(item["timestamp_seconds"])
            item["signature"] = _image_signature(item["path"])
            sampled_by_time[timestamp] = item
        right = next(
            (item for item in coarse if item["timestamp_seconds"] == window["end_seconds"]),
            None,
        )
        if right is not None:
            sampled_by_time[float(right["timestamp_seconds"])] = right

    samples = [sampled_by_time[key] for key in sorted(sampled_by_time)]
    selected_indexes: list[int] = [0]
    last_selected = 0
    for index in range(1, len(samples)):
        change = image_distance(samples[last_selected]["signature"], samples[index]["signature"])
        if change < CHANGE_DISTANCE:
            continue
        stable = index == len(samples) - 1 or image_distance(
            samples[index]["signature"], samples[index + 1]["signature"]
        ) <= STABLE_DISTANCE
        if stable:
            selected_indexes.append(index)
            last_selected = index

    candidates: list[dict[str, Any]] = []
    for index in selected_indexes:
        item = samples[index]
        ocr_text, title = _ocr_slide(item["path"])
        signature = item["signature"]
        if not ocr_text and _signature_spread(signature) < 0.04:
            continue
        candidates.append(
            {
                "timestamp_seconds": item["timestamp_seconds"],
                "path": item["path"],
                "signature": signature,
                "ocr_text": ocr_text,
                "title": title,
                "title_normalized": normalize_text(title),
            }
        )
    return candidates, {
        "coarse_frame_count": len(coarse),
        "changed_window_count": len(changed_windows),
        "refinement_frame_count": refinement_frame_count,
        "analyzed_frame_count": len(samples),
        "candidate_count": len(candidates),
        "changed_windows": changed_windows,
    }


def _signature_spread(signature: tuple[int, ...]) -> float:
    mean = sum(signature) / len(signature)
    return (sum(abs(value - mean) for value in signature) / len(signature)) / 255


def _ocr_slide(path: Path) -> tuple[str, str]:
    from PIL import Image

    title_path = path.with_name(path.stem + "_title.png")
    try:
        with Image.open(path) as image:
            title_image = image.crop((0, 0, image.width, max(1, round(image.height * 0.30))))
            title_image.save(title_path)
        tsv = subprocess.run(
            ["tesseract", str(title_path), "stdout", "-l", "est+eng", "--psm", "6", "tsv"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    finally:
        title_path.unlink(missing_ok=True)
    lines: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t"):
        word = (row.get("text") or "").strip()
        if not word or not normalize_text(word):
            continue
        key = (row.get("block_num", ""), row.get("par_num", ""), row.get("line_num", ""))
        try:
            height = int(row.get("height") or 0)
            left = int(row.get("left") or 0)
            width = int(row.get("width") or 0)
            top = int(row.get("top") or 0)
        except ValueError:
            continue
        lines.setdefault(key, []).append(
            {"text": word, "height": height, "left": left, "width": width, "top": top}
        )

    line_items: list[dict[str, Any]] = []
    for words in lines.values():
        words.sort(key=lambda item: item["left"])
        text_value = " ".join(item["text"] for item in words).strip()
        if len(text_value) < 3:
            continue
        line_items.append(
            {
                "text": text_value,
                "height": max(item["height"] for item in words),
                "top": min(item["top"] for item in words),
                "width": max(item["left"] + item["width"] for item in words)
                - min(item["left"] for item in words),
            }
        )
    line_items.sort(key=lambda item: (item["top"], -item["height"]))
    title_text = "\n".join(item["text"] for item in line_items)
    title = (
        max(line_items, key=lambda item: (item["height"] * max(1, item["width"]), item["height"]))["text"]
        if line_items
        else ""
    )
    return title_text, title


def _ocr_full_image(path: Path) -> str:
    return subprocess.run(
        ["tesseract", str(path), "stdout", "-l", "est+eng", "--psm", "6"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _add_reference_matching_ocr(candidates: list[dict[str, Any]]) -> None:
    for candidate in candidates:
        candidate["reference_ocr_text"] = _ocr_full_image(candidate["path"])


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", without_marks))


def restore_metadata_acronyms(value: str, metadata_title: str) -> str:
    acronyms = {token for token in re.findall(r"\b[A-Z][A-Z0-9]{1,9}\b", metadata_title)}
    if not acronyms:
        return value

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        comparable = token.upper().replace("L", "I").replace("1", "I")
        return next((acronym for acronym in acronyms if comparable == acronym), token)

    return re.sub(r"\b[A-Za-z0-9]+\b", replace, value)


def text_similarity(left: str, right: str) -> float:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)
    if not left_normalized or not right_normalized:
        return 0.0
    return difflib.SequenceMatcher(None, left_normalized, right_normalized).ratio()


def token_similarity(left: str, right: str) -> float:
    left_tokens = set(normalize_text(left).split())
    right_tokens = set(normalize_text(right).split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _reference_score(
    item: dict[str, Any], reference: dict[str, Any], previous_index: int = 0
) -> tuple[float, float, float, float]:
    title_score = text_similarity(item["title"], reference["title"])
    token_score = token_similarity(
        item.get("reference_ocr_text", item["ocr_text"]), reference["text"]
    )
    visual_score = max(0.0, 1.0 - image_distance(item["signature"], reference["signature"]))
    order_score = 1.0 if reference["index"] >= previous_index else 0.0
    combined = 0.5 * title_score + 0.25 * token_score + 0.2 * visual_score + 0.05 * order_score
    return combined, title_score, token_score, visual_score


def _clear_text_reference_match(
    item: dict[str, Any], references: list[dict[str, Any]]
) -> tuple[dict[str, Any], float, float] | None:
    scored = [
        (
            token_similarity(
                item.get("reference_ocr_text", item["ocr_text"]), reference["text"]
            ),
            reference,
        )
        for reference in references
    ]
    scored.sort(key=lambda value: value[0], reverse=True)
    if not scored:
        return None
    best_score, best_reference = scored[0]
    margin = best_score - scored[1][0] if len(scored) > 1 else best_score
    if best_score < 0.18 or margin < 0.10:
        return None
    return best_reference, best_score, margin


def _annotate_candidate_reference_hints(
    candidates: list[dict[str, Any]], references: list[dict[str, Any]]
) -> None:
    previous_index = 0
    for candidate in candidates:
        clear_text_match = _clear_text_reference_match(candidate, references)
        if clear_text_match is not None:
            reference, score, _ = clear_text_match
            candidate["reference_hint"] = reference["index"]
            candidate["reference_hint_score"] = round(score, 4)
            previous_index = reference["index"]
            continue
        scored = [(*_reference_score(candidate, reference, previous_index), reference) for reference in references]
        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored:
            continue
        best = scored[0]
        margin = best[0] - scored[1][0] if len(scored) > 1 else best[0]
        visual_scored = sorted(scored, key=lambda item: item[3], reverse=True)
        visual_margin = (
            visual_scored[0][3] - visual_scored[1][3]
            if len(visual_scored) > 1
            else visual_scored[0][3]
        )
        strong_title = best[1] >= 0.78 and margin >= 0.05
        strong_combination = best[0] >= 0.58 and margin >= 0.05 and (best[1] >= 0.72 or best[2] >= 0.45)
        strong_visual = visual_scored[0][3] >= 0.92 and visual_margin >= 0.08
        selected = visual_scored[0] if strong_visual else best
        if strong_title or strong_combination or strong_visual:
            candidate["reference_hint"] = selected[4]["index"]
            candidate["reference_hint_score"] = round(selected[0], 4)
            previous_index = selected[4]["index"]


def _build_slide_identities(
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    identities: list[dict[str, Any]] = []
    appearances: list[dict[str, Any]] = []
    last_identity: dict[str, Any] | None = None
    for candidate in candidates:
        if last_identity is not None:
            distance = image_distance(last_identity["signature"], candidate["signature"])
            title_match = text_similarity(last_identity["title"], candidate["title"])
            same_reference = candidate.get("reference_hint") is not None and candidate.get(
                "reference_hint"
            ) == last_identity.get("reference_hint")
            if distance <= DUPLICATE_DISTANCE:
                continue
            if same_reference or (title_match >= 0.88 and distance <= ANIMATION_DISTANCE):
                last_identity["source_path"] = candidate["path"]
                last_identity["signature"] = candidate["signature"]
                last_identity["ocr_text"] = candidate["ocr_text"]
                last_identity["reference_ocr_text"] = candidate.get(
                    "reference_ocr_text", candidate["ocr_text"]
                )
                if len(candidate["title"]) > len(last_identity["title"]):
                    last_identity["title"] = candidate["title"]
                continue

        repeated = next(
            (
                identity
                for identity in identities
                if (
                    candidate.get("reference_hint") is not None
                    and candidate.get("reference_hint") == identity.get("reference_hint")
                )
                or (
                    text_similarity(identity["title"], candidate["title"]) >= 0.92
                    and image_distance(identity["signature"], candidate["signature"]) <= 0.08
                )
            ),
            None,
        )
        if repeated is None:
            repeated = {
                "id": f"slide_{len(identities) + 1:03d}",
                "number": len(identities) + 1,
                "title": candidate["title"] or f"Slaid {len(identities) + 1}",
                "ocr_text": candidate["ocr_text"],
                "reference_ocr_text": candidate.get(
                    "reference_ocr_text", candidate["ocr_text"]
                ),
                "source_path": candidate["path"],
                "signature": candidate["signature"],
                "match_status": "video_only",
                "reference": None,
                "reference_hint": candidate.get("reference_hint"),
                "reference_hint_score": candidate.get("reference_hint_score"),
            }
            identities.append(repeated)
        appearance = {
            "slide_id": repeated["id"],
            "timestamp_seconds": candidate["timestamp_seconds"],
        }
        appearances.append(appearance)
        last_identity = repeated
    return identities, appearances


def _render_reference_slides(
    source: Path,
    output_dir: Path,
    work_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import pymupdf

    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.casefold()
    converted = False
    if suffix in {".ppt", ".pptx"}:
        libreoffice_profile = work_dir / "libreoffice-profile"
        libreoffice_profile.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "libreoffice",
                f"-env:UserInstallation={libreoffice_profile.as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(work_dir),
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        pdf_path = work_dir / (source.stem + ".pdf")
        converted = True
    elif suffix == ".pdf":
        pdf_path = source
    else:
        raise ValueError("Slide input must be PPT, PPTX or PDF")
    if not pdf_path.is_file():
        raise RuntimeError("Slide conversion did not produce a PDF")

    document = pymupdf.open(pdf_path)
    document_title = (document.metadata.get("title") or "").strip()
    references: list[dict[str, Any]] = []
    for index, page in enumerate(document):
        image_path = output_dir / f"slide_{index + 1:03d}.png"
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        pixmap.save(image_path)
        text = page.get_text("text", sort=True).strip()
        if not text:
            text, _ = _ocr_slide(image_path)
        title = next((line.strip() for line in text.splitlines() if len(line.strip()) >= 3), "")
        title = restore_metadata_acronyms(title, document_title)
        text = restore_metadata_acronyms(text, document_title)
        if not title and document_title:
            title = document_title
        references.append(
            {
                "index": index + 1,
                "title": title,
                "text": text,
                "path": image_path,
                "signature": _image_signature(image_path),
                "sha256": _file_sha256(image_path),
            }
        )
    return references, {
        "source_filename": source.name,
        "source_sha256": _file_sha256(source),
        "source_size_bytes": source.stat().st_size,
        "source_format": suffix.lstrip("."),
        "converted_to_pdf": converted,
        "page_count": len(references),
        "libreoffice": _tool_version(["libreoffice", "--version"]) if converted else None,
        "pymupdf": importlib.metadata.version("PyMuPDF"),
    }


def _match_reference_slides(identities: list[dict[str, Any]], references: list[dict[str, Any]]) -> None:
    previous_index = 0
    for identity in identities:
        clear_text_match = _clear_text_reference_match(identity, references)
        if clear_text_match is not None:
            reference, _, token_margin = clear_text_match
            combined, _, _, _ = _reference_score(identity, reference, previous_index)
            identity["match_score"] = round(combined, 4)
            identity["match_margin"] = round(token_margin, 4)
            identity["match_status"] = "matched"
            identity["reference"] = reference
            identity["title"] = reference["title"] or identity["title"]
            previous_index = reference["index"]
            continue
        hinted_reference = next(
            (reference for reference in references if reference["index"] == identity.get("reference_hint")),
            None,
        )
        if hinted_reference is not None:
            combined, title_score, token_score, visual_score = _reference_score(
                identity, hinted_reference, previous_index
            )
            identity["match_score"] = round(combined, 4)
            identity["match_margin"] = None
            identity["match_status"] = "matched"
            identity["reference"] = hinted_reference
            identity["title"] = hinted_reference["title"] or identity["title"]
            previous_index = hinted_reference["index"]
            continue
        scored: list[tuple[float, float, float, float, dict[str, Any]]] = []
        for reference in references:
            combined, title_score, token_score, visual_score = _reference_score(
                identity, reference, previous_index
            )
            scored.append((combined, title_score, token_score, visual_score, reference))
        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored:
            continue
        best = scored[0]
        margin = best[0] - scored[1][0] if len(scored) > 1 else best[0]
        matched = (best[1] >= 0.72 and best[0] >= 0.58 and margin >= 0.05) or (
            best[2] >= 0.45 and best[3] >= 0.72 and margin >= 0.05
        )
        identity["match_score"] = round(best[0], 4)
        identity["match_margin"] = round(margin, 4)
        if matched:
            reference = best[4]
            identity["match_status"] = "matched"
            identity["reference"] = reference
            identity["title"] = reference["title"] or identity["title"]
            previous_index = reference["index"]
        elif best[0] >= 0.45:
            identity["match_status"] = "review_required"


def _write_slide_images(identities: list[dict[str, Any]], images_dir: Path) -> None:
    images_dir.mkdir(parents=True, exist_ok=True)
    for identity in identities:
        reference = identity.get("reference")
        source = reference["path"] if reference is not None else identity["source_path"]
        target = images_dir / f"{identity['id']}.png"
        from PIL import Image

        with Image.open(source) as image:
            image.convert("RGB").save(target, format="PNG", optimize=True)
        identity["output_path"] = f"images/{target.name}"
        identity["output_sha256"] = _file_sha256(target)
        identity["output_source"] = "user_file" if reference is not None else "video"


def _slide_manifest(
    *,
    lesson: dict[str, Any],
    duration_seconds: float,
    identities: list[dict[str, Any]],
    appearances: list[dict[str, Any]],
    sampling: dict[str, Any],
    reference_manifest: dict[str, Any] | None,
    video: dict[str, Any],
    coarse_seconds: float,
    refine_seconds: float,
) -> dict[str, Any]:
    slide_items = []
    for identity in identities:
        slide_items.append(
            {
                "id": identity["id"],
                "number": identity["number"],
                "title": identity["title"],
                "ocr_text": identity["ocr_text"],
                "image_path": identity["output_path"],
                "image_sha256": identity["output_sha256"],
                "image_source": identity["output_source"],
                "match_status": identity["match_status"],
                "match_score": identity.get("match_score"),
                "match_margin": identity.get("match_margin"),
                "reference_slide_number": identity.get("reference", {}).get("index")
                if identity.get("reference")
                else None,
                "appearance_times_seconds": [
                    item["timestamp_seconds"] for item in appearances if item["slide_id"] == identity["id"]
                ],
            }
        )
    ocr_count = sum(bool(item["ocr_text"]) for item in slide_items)
    presence = "video_slides" if len(slide_items) >= 2 and ocr_count >= max(1, len(slide_items) // 2) else "uncertain"
    return {
        "schema_version": "1.0",
        "created_at": _utc_now(),
        "pipeline_version": SLIDE_PIPELINE_VERSION,
        "lesson": {
            "lesson_id": lesson["lesson_id"],
            "title": lesson["display_name"],
            "duration_seconds": duration_seconds,
        },
        "slide_presence": presence,
        "video": video,
        "sampling": {
            "coarse_interval_seconds": coarse_seconds,
            "refinement_interval_seconds": refine_seconds,
            "signature_width": SIGNATURE_SIZE[0],
            "signature_height": SIGNATURE_SIZE[1],
            "signature_color_mode": SIGNATURE_COLOR_MODE,
            **sampling,
            "change_distance": CHANGE_DISTANCE,
            "stable_distance": STABLE_DISTANCE,
            "duplicate_distance": DUPLICATE_DISTANCE,
            "animation_distance": ANIMATION_DISTANCE,
        },
        "reference_slides": reference_manifest,
        "slide_count": len(slide_items),
        "appearance_count": len(appearances),
        "slides": slide_items,
        "appearances": appearances,
        "tools": {
            "ffmpeg": _tool_version(["ffmpeg", "-version"]),
            "tesseract": _tool_version(["tesseract", "--version"]),
            "pillow": importlib.metadata.version("Pillow"),
            "ocr_languages": ["est", "eng"],
        },
    }


def _render_transcript_with_slides(
    transcript: dict[str, Any],
    identities: list[dict[str, Any]],
    appearances: list[dict[str, Any]],
) -> str:
    segments = transcript.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("Transcript has no segments")
    by_id = {identity["id"]: identity for identity in identities}
    insertions: dict[int, list[dict[str, Any]]] = {}
    boundaries: list[tuple[float, int]] = [(float(segment["start_seconds"]), index) for index, segment in enumerate(segments)]
    boundaries.append((float(segments[-1]["end_seconds"]), len(segments)))
    for appearance in appearances:
        _, insertion_index = min(boundaries, key=lambda item: abs(item[0] - appearance["timestamp_seconds"]))
        insertions.setdefault(insertion_index, []).append(appearance)

    lesson = transcript.get("lesson", {})
    lines = [
        f"# {lesson.get('title', 'Loengu transkript')} — ajatemplitega transkript koos slaididega",
        "",
        "## Dokumendi päritolu",
        "",
        "Transkript on loodud TalTechNLP kõnetuvastusmudeliga loengusalvestise audiost. Slaidide ajastus ja järjekord pärinevad loenguvideost; slaidipildi allikas on märgitud iga slaidi juures. Transkriptsioonisegmentide teksti ei ole toimetatud ega slaidide lisamisel muudetud.",
        "",
        "## Loeng",
        "",
        f"- Pealkiri: {lesson.get('title', '')}",
        f"- Echo lesson ID: `{lesson.get('lesson_id', '')}`",
        f"- Transkriptsioonisegmente: {len(segments)}",
        f"- Slaide: {len(identities)}",
        f"- Slaidide ilmumisi: {len(appearances)}",
        "",
        "## Transkript",
        "",
    ]
    for index, segment in enumerate(segments):
        lines.extend(_render_slide_insertions(insertions.get(index, []), by_id))
        lines.append(
            f"[{_format_hms(float(segment['start_seconds']))}–{_format_hms(float(segment['end_seconds']))}] "
            f"{str(segment['text']).strip()}"
        )
        lines.append("")
    lines.extend(_render_slide_insertions(insertions.get(len(segments), []), by_id))
    return "\n".join(lines).rstrip() + "\n"


def _render_slide_insertions(
    insertions: list[dict[str, Any]], by_id: dict[str, dict[str, Any]]
) -> list[str]:
    lines: list[str] = []
    for appearance in sorted(insertions, key=lambda item: item["timestamp_seconds"]):
        slide = by_id[appearance["slide_id"]]
        heading = f"### Slaid {slide['number']}"
        if slide.get("reference") is not None and slide.get("title"):
            heading += f" — {slide['title']}"
        lines.extend(
            [
                heading,
                "",
                f"![Slaid {slide['number']}](images/{slide['id']}.png)",
                "",
                f"Ligikaudne ilmumisaeg: {_format_hms(appearance['timestamp_seconds'])}. "
                f"Pildi allikas: {'kasutaja slaidifail' if slide['output_source'] == 'user_file' else 'loenguvideo'}.",
                "",
            ]
        )
    return lines


def _format_hms(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_part = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON input: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON input must be an object: {path}")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
