from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from lecture_notes.config import ensure_runtime_output, settings
from lecture_notes.echo360 import EchoClient, EchoError, build_resolver_manifest
from lecture_notes.manifests import atomic_write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-notes-stage3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract-pdf", help="Eralda PDF-i lehekülgede tekst auditeeritavasse JSON-i")
    extract.add_argument("--input", type=Path, required=True)
    extract.add_argument("--output-dir", type=Path, required=True)
    extract.add_argument("--document-id", required=True)
    frames = subparsers.add_parser("extract-frames", help="Eralda Echo videost ajastatud slaidikaadrid ja OCR")
    frames.add_argument("public_url")
    frames.add_argument("--lesson-id", required=True)
    frames.add_argument("--output-dir", type=Path, required=True)
    frames.add_argument("--start-seconds", type=float, required=True)
    frames.add_argument("--end-seconds", type=float, required=True)
    frames.add_argument("--interval-seconds", type=float, default=30.0)
    evidence = subparsers.add_parser("build-evidence", help="Koosta kontrollitud valiku järgi ühe teema tõendipakett")
    evidence.add_argument("--syllabus", type=Path, required=True)
    evidence.add_argument("--transcript", type=Path, required=True)
    evidence.add_argument("--frames", type=Path, required=True)
    evidence.add_argument("--selection", type=Path, required=True)
    evidence.add_argument("--output-dir", type=Path, required=True)
    generate = subparsers.add_parser("generate-notes", help="Genereeri tõendipaketist kohaliku Ollamaga peatüki mustand")
    generate.add_argument("--evidence", type=Path, required=True)
    generate.add_argument("--output-dir", type=Path, required=True)
    generate.add_argument("--ollama-url", default=None)
    generate.add_argument("--model", default=None)
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
        if args.command == "build-evidence":
            result = build_evidence_package(
                syllabus_path=args.syllabus,
                transcript_path=args.transcript,
                frames_path=args.frames,
                selection_path=args.selection,
            )
            atomic_write_json(output_dir / "evidence.json", result)
            atomic_write_json(output_dir / "coverage.json", result["coverage"])
            print(json.dumps({"status": "ok", "output": str(output_dir), "evidence_count": len(result["evidence"])}, sort_keys=True))
            return 0
        if args.command == "generate-notes":
            result = generate_notes(
                evidence_path=args.evidence,
                output_dir=output_dir,
                ollama_url=args.ollama_url or __import__("os").environ.get("OLLAMA_URL", "http://host.docker.internal:11434"),
                model=args.model or __import__("os").environ.get("STAGE3_LLM_MODEL", "mistral:latest"),
            )
            print(json.dumps({"status": "ok", "output": str(output_dir), "model": result["model"]["name"]}, sort_keys=True))
            return 0
    except (OSError, ValueError, RuntimeError, EchoError) as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)[:1000]}), file=sys.stderr)
        return 2
    return 2


def build_evidence_package(
    *,
    syllabus_path: Path,
    transcript_path: Path,
    frames_path: Path,
    selection_path: Path,
) -> dict[str, Any]:
    syllabus = _read_json(syllabus_path)
    transcript = _read_json(transcript_path)
    frame_manifest = _read_json(frames_path)
    selection = _read_json(selection_path)

    syllabus_item_id = selection["syllabus_item_id"]
    syllabus_page_number = int(selection["syllabus_page_number"])
    syllabus_page = next(
        (page for page in syllabus.get("pages", []) if page.get("page_number") == syllabus_page_number),
        None,
    )
    if not syllabus_page:
        raise ValueError(f"Syllabus page not found: {syllabus_page_number}")
    syllabus_item = extract_syllabus_item(syllabus_page["text"], syllabus_item_id)

    clip_id = selection["transcript_clip_id"]
    clip = next((item for item in transcript.get("clips", []) if item.get("id") == clip_id), None)
    if not clip:
        raise ValueError(f"Transcript clip not found: {clip_id}")
    source_segments = clip.get("segments", [])
    segments: list[dict[str, Any]] = []
    segment_by_index: dict[int, dict[str, Any]] = {}
    for index, source_segment in enumerate(source_segments):
        segment = {
            "id": _segment_id(source_segment),
            "source_index": index,
            "start_ms": round(source_segment["start_seconds"] * 1000),
            "end_ms": round(source_segment["end_seconds"] * 1000),
            "text_raw": source_segment["text"].strip(),
            "text_normalized": None,
            "speaker_id": None,
            "asr_review_status": "unreviewed",
        }
        segments.append(segment)
        segment_by_index[index] = segment

    frames_by_id = {frame["id"]: frame for frame in frame_manifest.get("frames", [])}
    selected_slides: list[dict[str, Any]] = []
    for slide_selection in selection.get("slides", []):
        source_frame = frames_by_id.get(slide_selection["frame_id"])
        if not source_frame:
            raise ValueError(f"Selected frame not found: {slide_selection['frame_id']}")
        selected_slides.append(
            {
                "id": source_frame["id"],
                "timestamp_ms": round(source_frame["timestamp_seconds"] * 1000),
                "path": source_frame["path"],
                "markdown_path": slide_selection["markdown_path"],
                "sha256": source_frame["sha256"],
                "ocr_text": source_frame.get("ocr_text", ""),
                "caption": slide_selection["caption"],
                "review_status": slide_selection.get("review_status", "unreviewed"),
            }
        )

    evidence: list[dict[str, Any]] = []
    selected_slide_ids = {slide["id"] for slide in selected_slides}
    for candidate in selection.get("evidence", []):
        indices = candidate["segment_indexes"]
        try:
            selected_segments = [segment_by_index[index] for index in indices]
        except KeyError as exc:
            raise ValueError(f"Selected transcript segment not found: {exc.args[0]}") from exc
        slide_ids = candidate.get("slide_ids", [])
        missing_slides = set(slide_ids) - selected_slide_ids
        if missing_slides:
            raise ValueError(f"Evidence refers to unselected slides: {sorted(missing_slides)}")
        evidence.append(
            {
                "id": candidate["id"],
                "kind": candidate["kind"],
                "claim_candidate": candidate["claim_candidate"],
                "lesson_id": selection["lesson_id"],
                "segment_ids": [segment["id"] for segment in selected_segments],
                "start_ms": min(segment["start_ms"] for segment in selected_segments),
                "end_ms": max(segment["end_ms"] for segment in selected_segments),
                "slide_ids": slide_ids,
                "syllabus_items": [syllabus_item_id],
                "confidence": candidate.get("confidence", "medium"),
                "review_status": candidate.get("review_status", "unreviewed"),
            }
        )

    return {
        "schema_version": "1.0",
        "created_at": _utc_now(),
        "topic_id": selection["topic_id"],
        "title": selection["title"],
        "lesson_id": selection["lesson_id"],
        "lesson_url": selection["lesson_url"],
        "syllabus": {
            "item_id": syllabus_item_id,
            "page_number": syllabus_page_number,
            "text": syllabus_item,
            "document_id": syllabus.get("document_id"),
            "source_sha256": syllabus.get("source", {}).get("sha256"),
        },
        "transcript": {
            "clip_id": clip_id,
            "source_sha256": _file_sha256(transcript_path),
            "model": transcript.get("model"),
            "reference_status": clip.get("reference_status"),
            "segments": segments,
        },
        "slides": {
            "source_sha256": _file_sha256(frames_path),
            "items": selected_slides,
        },
        "evidence": evidence,
        "coverage": {
            "syllabus_item_id": syllabus_item_id,
            "status": selection["coverage"]["status"],
            "covered_aspects": selection["coverage"]["covered_aspects"],
            "missing_aspects": selection["coverage"]["missing_aspects"],
            "reason": selection["coverage"]["reason"],
            "review_status": "unreviewed",
        },
        "selection": {
            "source": selection_path.name,
            "sha256": _file_sha256(selection_path),
            "curation": selection["curation"],
        },
    }


def extract_syllabus_item(page_text: str, item_id: str) -> str:
    import re

    marker = re.compile(rf"(?m)^\s*{re.escape(item_id)}\.\s+")
    match = marker.search(page_text)
    if not match:
        raise ValueError(f"Syllabus item not found on selected page: {item_id}")
    next_item = re.compile(r"(?m)^\s*\d+(?:\.\d+)?\.[a-z]\.\s+|^\s*Nädal\s+\d+").search(page_text, match.end())
    end = next_item.start() if next_item else len(page_text)
    return " ".join(page_text[match.start():end].split())


def generate_notes(*, evidence_path: Path, output_dir: Path, ollama_url: str, model: str) -> dict[str, Any]:
    evidence = _read_json(evidence_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_path = output_dir / "run.json"
    started_at = _utc_now()
    atomic_write_json(
        run_path,
        {
            "schema_version": "1.0",
            "status": "running",
            "started_at": started_at,
            "model": model,
            "evidence_sha256": _file_sha256(evidence_path),
        },
    )
    started = time.perf_counter()
    try:
        tags = _ollama_json(ollama_url, "/api/tags", None, timeout_seconds=30)
        model_info = next((item for item in tags.get("models", []) if item.get("name") == model), None)
        if not model_info:
            raise RuntimeError(f"Requested Ollama model is not installed: {model}")
        prompt = _notes_prompt(evidence)
        response = _ollama_json(
            ollama_url,
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.15, "num_ctx": 8192},
            },
            timeout_seconds=7200,
        )
        markdown = response.get("response", "").strip()
        if not markdown:
            raise RuntimeError("Ollama returned an empty response")
        (output_dir / "draft.md").write_text(markdown + "\n", encoding="utf-8")
        atomic_write_json(output_dir / "raw_response.json", response)
        validation = validate_generated_notes(markdown, evidence)
        atomic_write_json(output_dir / "validation.json", validation)
        result = {
            "schema_version": "1.0",
            "status": "completed",
            "started_at": started_at,
            "completed_at": _utc_now(),
            "duration_seconds": round(time.perf_counter() - started, 3),
            "model": {
                "name": model,
                "digest": model_info.get("digest"),
                "details": model_info.get("details"),
            },
            "ollama": {"total_duration_ns": response.get("total_duration"), "eval_count": response.get("eval_count")},
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "evidence_sha256": _file_sha256(evidence_path),
            "validation_status": validation["status"],
        }
        atomic_write_json(run_path, result)
        return result
    except Exception as exc:
        atomic_write_json(
            run_path,
            {
                "schema_version": "1.0",
                "status": "failed",
                "started_at": started_at,
                "completed_at": _utc_now(),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "model": model,
                "evidence_sha256": _file_sha256(evidence_path),
                "error": {"type": type(exc).__name__, "message": str(exc)[:2000]},
            },
        )
        raise


def validate_generated_notes(markdown: str, evidence: dict[str, Any]) -> dict[str, Any]:
    import re

    evidence_ids = [item["id"] for item in evidence.get("evidence", [])]
    cited = [evidence_id for evidence_id in evidence_ids if f"[{evidence_id}]" in markdown]
    missing = sorted(set(evidence_ids) - set(cited))
    unknown = sorted(
        token[1:-1]
        for token in re.findall(r"\[evidence_[A-Za-z0-9_-]+\]", markdown)
        if token[1:-1] not in evidence_ids
    )
    slide_paths = [item["markdown_path"] for item in evidence.get("slides", {}).get("items", [])]
    embedded_slides = [path for path in slide_paths if path in markdown]
    first_heading = next((line.strip() for line in markdown.splitlines() if line.strip().startswith("#")), "")
    origin_first = "dokumendi päritolu" in first_heading.lower()
    has_toc = bool(re.search(r"(?im)^#{1,6}\s+(?:\d+\.\s+)?sisukord\s*$", markdown))
    missing_aspects = evidence.get("coverage", {}).get("missing_aspects", [])
    stated_missing_aspects = [aspect for aspect in missing_aspects if aspect.lower() in markdown.lower()]
    all_missing_aspects_stated = len(stated_missing_aspects) == len(missing_aspects)
    status = (
        "passed"
        if not missing and not unknown and embedded_slides and origin_first and has_toc and all_missing_aspects_stated
        else "needs_review"
    )
    return {
        "schema_version": "1.0",
        "status": status,
        "evidence_ids": evidence_ids,
        "cited_evidence_ids": cited,
        "missing_evidence_ids": missing,
        "unknown_evidence_ids": unknown,
        "embedded_slide_paths": embedded_slides,
        "stated_missing_aspects": stated_missing_aspects,
        "checks": {
            "all_evidence_referenced": not missing,
            "no_unknown_evidence_references": not unknown,
            "at_least_one_slide_embedded": bool(embedded_slides),
            "origin_is_first_heading": origin_first,
            "table_of_contents_present": has_toc,
            "all_coverage_gaps_stated": all_missing_aspects_stated,
        },
        "limitations": [
            "Deterministic validation checks references and assets, not factual truth.",
            "ASR text and generated prose remain unreviewed until a human confirms them.",
        ],
    }


def _notes_prompt(evidence: dict[str, Any]) -> str:
    compact = {
        "title": evidence["title"],
        "lesson_url": evidence["lesson_url"],
        "syllabus": evidence["syllabus"],
        "coverage": evidence["coverage"],
        "segments": evidence["transcript"]["segments"],
        "slides": evidence["slides"]["items"],
        "evidence": evidence["evidence"],
    }
    return (
        "Koosta alloleva tõendipaketi põhjal iseseisvalt loetav eestikeelne ülikooli konspekti peatükk. "
        "Kasuta ainult paketis olevaid väiteid; ära lisa üldteadmisi ega oletusi. "
        "Peatükk ei pea järgima loengu ajalist järjekorda. Selgita mõisted ja seosed täislausetega. "
        "Dokumendi esimene jaotis peab olema 'Dokumendi päritolu' ning ütlema, et mustandi koostas kohalik AI tõendipaketi põhjal ja inimene pole seda veel kinnitanud. "
        "Teine jaotis peab olema 'Sisukord', sest peatükis on mitu sisulist alajaotist. "
        "Lisa vähemalt üks asjakohane slaid Markdowni pildina, kasutades paketis olevat markdown_path-väärtust. "
        "Iga sisulise lõigu lõpus lisa kasutatud tõendi ID täpselt kujul [evidence_...]. "
        "Lisa lõppu jaotis 'Allikate kontroll', kus esitad tõendid koos loengu ajatemplite, slaidide ja ainekava viitega. "
        "Ütle selgelt, et katvus on osaline, ja nimeta coverage.missing_aspects; ära täida neid ise. "
        "Ära nimeta kontrollimata ASR-teksti sõna-sõnalt autoriteetseks tsitaadiks. "
        "Väljasta ainult Markdown, ilma koodiploki piireteta.\n\nTÕENDIPAKETT:\n"
        + json.dumps(compact, ensure_ascii=False, indent=2)
    )


def _ollama_json(base_url: str, path: str, payload: dict[str, Any] | None, *, timeout_seconds: int) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama request failed: {path}: {exc}") from exc


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"JSON input does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON input: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON input must be an object: {path}")
    return value


def _segment_id(segment: dict[str, Any]) -> str:
    return f"seg_{round(segment['start_seconds'] * 1000):010d}_{round(segment['end_seconds'] * 1000):010d}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
    work_dir = work_root / "stage3" / work_key
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
    selected = min(candidates, key=lambda item: (item.get("height") or 100000, item.get("size") or 1000000000000))
    return selected["s3Url"], selected.get("size"), selected.get("width"), selected.get("height")


def _tool_version(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return (result.stdout or result.stderr).splitlines()[0]


def extract_pdf(source: Path, document_id: str) -> dict[str, Any]:
    import pymupdf

    document = pymupdf.open(source)
    pages = [
        {
            "page_number": index + 1,
            "text": page.get_text("text", sort=True).strip(),
        }
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
        "extractor": {
            "name": "PyMuPDF",
            "version": importlib.metadata.version("PyMuPDF"),
        },
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


if __name__ == "__main__":
    raise SystemExit(main())
