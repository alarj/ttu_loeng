from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import resource
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from lecture_notes.config import ensure_runtime_output, settings
from lecture_notes.echo360 import EchoClient, EchoError, build_resolver_manifest
from lecture_notes.manifests import atomic_write_json, get_audio_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-notes-asr")
    subparsers = parser.add_subparsers(dest="command", required=True)
    benchmark = subparsers.add_parser("benchmark", help="Käivita lukustatud lõikudel üks ASR-konfiguratsioon")
    benchmark.add_argument("--audio", type=Path, required=True)
    benchmark.add_argument("--dataset", type=Path, required=True)
    benchmark.add_argument("--output-dir", type=Path, required=True)
    benchmark.add_argument("--model", required=True)
    benchmark.add_argument("--revision", required=True)
    benchmark.add_argument("--model-subfolder")
    benchmark.add_argument("--configuration-id", required=True)
    benchmark.add_argument("--compute-type", default="int8")
    benchmark.add_argument("--language", default="et")
    benchmark.add_argument("--cpu-threads", type=int, default=3)
    benchmark.add_argument("--beam-size", type=int, default=5)
    full = subparsers.add_parser("transcribe-full", help="Loo kogu Echo loengust ajastatud transkript")
    full.add_argument("public_url")
    full.add_argument("--lesson-id", required=True)
    full.add_argument("--output-dir", type=Path, required=True)
    full.add_argument("--model", required=True)
    full.add_argument("--revision", required=True)
    full.add_argument("--model-subfolder")
    full.add_argument("--configuration-id", required=True)
    full.add_argument("--compute-type", default="int8")
    full.add_argument("--language", default="et")
    full.add_argument("--cpu-threads", type=int, default=3)
    full.add_argument("--beam-size", type=int, default=5)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = settings()
    try:
        output_dir = ensure_runtime_output(args.output_dir, config)
        if args.command == "benchmark":
            audio_path = _external_input(args.audio, config.runtime_root, "audio")
            dataset = _load_dataset(args.dataset)
            result = run_benchmark(
                audio_path=audio_path,
                dataset=dataset,
                model_id=args.model,
                revision=args.revision,
                model_subfolder=args.model_subfolder,
                configuration_id=args.configuration_id,
                compute_type=args.compute_type,
                language=args.language,
                cpu_threads=max(1, args.cpu_threads),
                beam_size=max(1, args.beam_size),
                hf_cache=config.runtime_root / "models" / "huggingface" / "hub",
            )
            target_dir = output_dir / dataset["dataset_id"] / args.configuration_id
            atomic_write_json(target_dir / "result.json", result)
            (target_dir / "review.md").write_text(_render_review(result), encoding="utf-8")
            print(json.dumps({"status": "ok", "output": str(target_dir), **result["performance"]}, sort_keys=True))
            return 0
        if args.command == "transcribe-full":
            result = run_full_transcription_job(
                public_url=args.public_url,
                lesson_id=args.lesson_id,
                output_dir=output_dir,
                work_root=config.work_root,
                model_id=args.model,
                revision=args.revision,
                model_subfolder=args.model_subfolder,
                configuration_id=args.configuration_id,
                compute_type=args.compute_type,
                language=args.language,
                cpu_threads=max(1, args.cpu_threads),
                beam_size=max(1, args.beam_size),
                hf_cache=config.runtime_root / "models" / "huggingface" / "hub",
            )
            print(json.dumps({"status": "ok", "output": str(output_dir), **result["performance"]}, sort_keys=True))
            return 0
    except (OSError, ValueError, KeyError, RuntimeError, EchoError) as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)[:1000]}), file=sys.stderr)
        return 2
    return 2


def run_full_transcription_job(
    *,
    public_url: str,
    lesson_id: str,
    output_dir: Path,
    work_root: Path,
    model_id: str,
    revision: str,
    model_subfolder: str | None,
    configuration_id: str,
    compute_type: str,
    language: str,
    cpu_threads: int,
    beam_size: int,
    hf_cache: Path,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    run_path = output_dir / "run.json"
    work_key = hashlib.sha256(f"{lesson_id}:full-asr:{configuration_id}".encode("utf-8")).hexdigest()[:16]
    work_dir = work_root / "transcribe" / work_key
    audio_path = work_dir / "source.mp3"
    atomic_write_json(
        run_path,
        {
            "schema_version": "1.0",
            "status": "running",
            "started_at": started_at.isoformat().replace("+00:00", "Z"),
            "lesson_id": lesson_id,
            "configuration_id": configuration_id,
            "model_id": model_id,
            "model_revision": revision,
            "temporary_audio_path": str(audio_path),
        },
    )
    try:
        client = EchoClient(timeout_seconds=60.0)
        resolver = build_resolver_manifest(client, public_url)
        lesson = next((item for item in resolver["lessons"] if item.get("lesson_id") == lesson_id), None)
        if lesson is None:
            raise ValueError("Lesson does not belong to the resolved public course")
        media = client.get_lesson_media(lesson_id)
        audio_source = get_audio_source(media)
        if audio_source is None:
            raise ValueError("Lesson has no separate downloadable audio source")
        source_url, expected_size = audio_source
        shutil.rmtree(work_dir, ignore_errors=True)
        download = client.download_media(source_url, audio_path)
        download["expected_size_bytes"] = expected_size
        download["size_matches_expected"] = expected_size is None or download["size_bytes"] == expected_size
        result = run_full_transcription(
            audio_path=audio_path,
            lesson_id=lesson_id,
            lesson_title=lesson["display_name"],
            public_url=public_url,
            model_id=model_id,
            revision=revision,
            model_subfolder=model_subfolder,
            configuration_id=configuration_id,
            compute_type=compute_type,
            language=language,
            cpu_threads=cpu_threads,
            beam_size=beam_size,
            hf_cache=hf_cache,
            download=download,
        )
        shutil.rmtree(work_dir, ignore_errors=True)
        result["audio"]["temporary_audio_removed"] = not audio_path.exists()
        atomic_write_json(output_dir / "transcript.json", result)
        (output_dir / "transcript.md").write_text(_render_full_transcript(result), encoding="utf-8")
        atomic_write_json(
            run_path,
            {
                "schema_version": "1.0",
                "status": "completed",
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "lesson_id": lesson_id,
                "configuration_id": configuration_id,
                "model_id": model_id,
                "model_revision": revision,
                "segment_count": len(result["segments"]),
                "temporary_audio_removed": not audio_path.exists(),
                "performance": result["performance"],
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
                "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "lesson_id": lesson_id,
                "configuration_id": configuration_id,
                "model_id": model_id,
                "model_revision": revision,
                "temporary_audio_removed": not audio_path.exists(),
                "error": {"type": type(exc).__name__, "message": str(exc)[:2000]},
            },
        )
        raise


def run_full_transcription(
    *,
    audio_path: Path,
    lesson_id: str,
    lesson_title: str,
    public_url: str,
    model_id: str,
    revision: str,
    model_subfolder: str | None,
    configuration_id: str,
    compute_type: str,
    language: str,
    cpu_threads: int,
    beam_size: int,
    hf_cache: Path,
    download: dict[str, Any],
) -> dict[str, Any]:
    from faster_whisper import WhisperModel

    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    hf_cache.mkdir(parents=True, exist_ok=True)
    model_path = model_id
    if model_subfolder:
        from huggingface_hub import snapshot_download

        snapshot = snapshot_download(
            repo_id=model_id,
            revision=revision,
            cache_dir=hf_cache,
            allow_patterns=[f"{model_subfolder}/*"],
        )
        model_path = str(Path(snapshot) / model_subfolder)
    model_load_started = time.perf_counter()
    model = WhisperModel(
        model_path,
        device="cpu",
        compute_type=compute_type,
        cpu_threads=cpu_threads,
        num_workers=1,
        download_root=str(hf_cache),
        revision=None if model_subfolder else revision,
    )
    model_load_seconds = time.perf_counter() - model_load_started
    transcription_started = time.perf_counter()
    generated_segments, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=beam_size,
        word_timestamps=True,
        vad_filter=False,
        condition_on_previous_text=False,
    )
    segments: list[dict[str, Any]] = []
    for index, segment in enumerate(generated_segments):
        words = [
            {
                "start_seconds": round(word.start, 3),
                "end_seconds": round(word.end, 3),
                "text": word.word,
                "probability": round(word.probability, 5),
            }
            for word in (segment.words or [])
        ]
        segments.append(
            {
                "id": f"seg_{index:06d}",
                "start_seconds": round(segment.start, 3),
                "end_seconds": round(segment.end, 3),
                "text": segment.text.strip(),
                "avg_logprob": round(segment.avg_logprob, 5),
                "no_speech_prob": round(segment.no_speech_prob, 5),
                "words": words,
            }
        )
    transcription_seconds = time.perf_counter() - transcription_started
    audio_duration_seconds = float(info.duration)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "schema_version": "1.0",
        "created_at": started_at.isoformat().replace("+00:00", "Z"),
        "lesson": {
            "lesson_id": lesson_id,
            "title": lesson_title,
            "public_url": public_url,
            "language": language,
        },
        "audio": {
            "sha256": download["sha256"],
            "size_bytes": download["size_bytes"],
            "expected_size_bytes": download.get("expected_size_bytes"),
            "size_matches_expected": download.get("size_matches_expected"),
            "duration_seconds": round(audio_duration_seconds, 3),
            "source_host": download["source_host"],
            "source_path": download["source_path"],
            "source_query_persisted": False,
            "temporary_audio_removed": False,
        },
        "configuration": {
            "id": configuration_id,
            "runtime": "faster-whisper",
            "faster_whisper_version": importlib.metadata.version("faster-whisper"),
            "ctranslate2_version": importlib.metadata.version("ctranslate2"),
            "model_id": model_id,
            "model_revision": revision,
            "model_subfolder": model_subfolder,
            "device": "cpu",
            "compute_type": compute_type,
            "language": language,
            "cpu_threads": cpu_threads,
            "num_workers": 1,
            "beam_size": beam_size,
            "word_timestamps": True,
            "vad_filter": False,
            "condition_on_previous_text": False,
        },
        "detected_language": info.language,
        "language_probability": round(info.language_probability, 5),
        "quality_status": "unreviewed",
        "performance": {
            "model_load_seconds": round(model_load_seconds, 3),
            "transcription_seconds": round(transcription_seconds, 3),
            "duration_seconds": round(time.perf_counter() - started, 3),
            "transcribed_audio_seconds": round(audio_duration_seconds, 3),
            "real_time_factor": round(transcription_seconds / audio_duration_seconds, 4),
            "max_rss_kib": usage.ru_maxrss,
        },
        "segment_count": len(segments),
        "transcript": " ".join(item["text"] for item in segments).strip(),
        "segments": segments,
    }


def run_benchmark(
    *,
    audio_path: Path,
    dataset: dict[str, Any],
    model_id: str,
    revision: str,
    model_subfolder: str | None,
    configuration_id: str,
    compute_type: str,
    language: str,
    cpu_threads: int,
    beam_size: int,
    hf_cache: Path,
) -> dict[str, Any]:
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    hf_cache.mkdir(parents=True, exist_ok=True)
    model_path = model_id
    if model_subfolder:
        from huggingface_hub import snapshot_download

        snapshot = snapshot_download(
            repo_id=model_id,
            revision=revision,
            cache_dir=hf_cache,
            allow_patterns=[f"{model_subfolder}/*"],
        )
        model_path = str(Path(snapshot) / model_subfolder)

    model_load_started = time.perf_counter()
    model = WhisperModel(
        model_path,
        device="cpu",
        compute_type=compute_type,
        cpu_threads=cpu_threads,
        num_workers=1,
        download_root=str(hf_cache),
        revision=None if model_subfolder else revision,
    )
    model_load_seconds = time.perf_counter() - model_load_started
    audio = decode_audio(str(audio_path), sampling_rate=16000)
    clips: list[dict[str, Any]] = []
    transcribed_audio_seconds = 0.0
    transcription_started = time.perf_counter()
    for definition in dataset["clips"]:
        clip_start = float(definition["start_seconds"])
        clip_end = float(definition["end_seconds"])
        if clip_end <= clip_start:
            raise ValueError(f"Invalid clip interval: {definition['id']}")
        sample = audio[int(clip_start * 16000) : int(clip_end * 16000)]
        transcribed_audio_seconds += clip_end - clip_start
        segments, info = model.transcribe(
            sample,
            language=language,
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        normalized_segments = []
        for segment in segments:
            words = [
                {
                    "start_seconds": round(clip_start + word.start, 3),
                    "end_seconds": round(clip_start + word.end, 3),
                    "text": word.word,
                    "probability": round(word.probability, 5),
                }
                for word in (segment.words or [])
            ]
            normalized_segments.append(
                {
                    "start_seconds": round(clip_start + segment.start, 3),
                    "end_seconds": round(clip_start + segment.end, 3),
                    "text": segment.text.strip(),
                    "avg_logprob": round(segment.avg_logprob, 5),
                    "no_speech_prob": round(segment.no_speech_prob, 5),
                    "words": words,
                }
            )
        text = " ".join(item["text"] for item in normalized_segments).strip()
        reference = definition.get("reference_text")
        metrics = _quality_metrics(reference, text, definition.get("expected_terms") or [])
        clips.append(
            {
                **definition,
                "detected_language": info.language,
                "language_probability": round(info.language_probability, 5),
                "transcript": text,
                "segments": normalized_segments,
                "metrics": metrics,
            }
        )
    transcription_seconds = time.perf_counter() - transcription_started
    duration_seconds = time.perf_counter() - started
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "schema_version": "1.0",
        "created_at": started_at.isoformat().replace("+00:00", "Z"),
        "dataset": {
            "id": dataset["dataset_id"],
            "status": dataset["status"],
            "sha256": _json_sha256(dataset),
            "clip_count": len(dataset["clips"]),
            "reference_clip_count": sum(1 for item in dataset["clips"] if item.get("reference_status") == "human_verified"),
        },
        "audio": {"path": str(audio_path), "sha256": _file_sha256(audio_path)},
        "configuration": {
            "id": configuration_id,
            "runtime": "faster-whisper",
            "faster_whisper_version": importlib.metadata.version("faster-whisper"),
            "ctranslate2_version": importlib.metadata.version("ctranslate2"),
            "model_id": model_id,
            "model_revision": revision,
            "model_subfolder": model_subfolder,
            "device": "cpu",
            "compute_type": compute_type,
            "language": language,
            "cpu_threads": cpu_threads,
            "num_workers": 1,
            "beam_size": beam_size,
            "word_timestamps": True,
            "vad_filter": False,
            "condition_on_previous_text": False,
        },
        "performance": {
            "model_load_seconds": round(model_load_seconds, 3),
            "transcription_seconds": round(transcription_seconds, 3),
            "duration_seconds": round(duration_seconds, 3),
            "transcribed_audio_seconds": round(transcribed_audio_seconds, 3),
            "real_time_factor": round(transcription_seconds / transcribed_audio_seconds, 4),
            "max_rss_kib": usage.ru_maxrss,
        },
        "quality_status": "measured" if all(item["metrics"]["reference_available"] for item in clips) else "human_reference_required",
        "clips": clips,
    }


def _external_input(path: Path, runtime_root: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(runtime_root)
    except ValueError as exc:
        raise ValueError(f"{label} must be inside TTU_LOENG_RUNTIME_ROOT") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} does not exist: {resolved}")
    return resolved


def _load_dataset(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("clips"), list) or not payload.get("dataset_id"):
        raise ValueError("Invalid benchmark dataset")
    return payload


def _quality_metrics(reference: Any, hypothesis: str, expected_terms: list[str]) -> dict[str, Any]:
    terms = {
        term: term in _normalize(hypothesis)
        for term in expected_terms
    }
    if not isinstance(reference, str) or not reference.strip():
        return {"reference_available": False, "wer": None, "cer": None, "expected_terms": terms}
    reference_words = _normalize(reference).split()
    hypothesis_words = _normalize(hypothesis).split()
    reference_chars = list(_normalize(reference).replace(" ", ""))
    hypothesis_chars = list(_normalize(hypothesis).replace(" ", ""))
    return {
        "reference_available": True,
        "wer": round(_edit_distance(reference_words, hypothesis_words) / max(1, len(reference_words)), 5),
        "cer": round(_edit_distance(reference_chars, hypothesis_chars) / max(1, len(reference_chars)), 5),
        "expected_terms": terms,
    }


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.sub(r"[^\wõäöüšž]+", " ", value, flags=re.UNICODE).split())


def _edit_distance(left: list[str], right: list[str]) -> int:
    previous = list(range(len(right) + 1))
    for index, left_item in enumerate(left, start=1):
        current = [index]
        for other_index, right_item in enumerate(right, start=1):
            current.append(min(current[-1] + 1, previous[other_index] + 1, previous[other_index - 1] + (left_item != right_item)))
        previous = current
    return previous[-1]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _render_review(result: dict[str, Any]) -> str:
    config = result["configuration"]
    performance = result["performance"]
    lines = [
        "# ASR benchmarki kontrollvaade",
        "",
        "## 1. Dokumendi päritolu",
        "",
        "Koostaja: AI (OpenAI Codex), automaatselt ASR benchmarki auditeeritava JSON-väljundi põhjal.",
        "",
        "## 2. Tulemus",
        "",
        f"- Konfiguratsioon: `{config['id']}`",
        f"- Mudel: `{config['model_id']}` revisjon `{config['model_revision']}`",
        f"- Kvaliteedi olek: `{result['quality_status']}`",
        f"- Transkriptsiooniaeg: {performance['transcription_seconds']} s",
        f"- Reaalaja tegur: {performance['real_time_factor']}",
        f"- Maksimaalne RSS: {performance['max_rss_kib']} KiB",
        "",
        "## 3. Lõigud",
        "",
    ]
    for clip in result["clips"]:
        lines.extend(
            [
                f"### {clip['id']} ({clip['start_seconds']}–{clip['end_seconds']} s)",
                "",
                clip["transcript"] or "_Kõnet ei tuvastatud._",
                "",
                f"Referents: `{clip['reference_status']}`; WER: `{clip['metrics']['wer']}`; CER: `{clip['metrics']['cer']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def _render_full_transcript(result: dict[str, Any]) -> str:
    lesson = result["lesson"]
    config = result["configuration"]
    performance = result["performance"]
    lines = [
        f"# {lesson['title']} — ajastatud ASR-transkript",
        "",
        "## 1. Dokumendi päritolu",
        "",
        "Koostaja: AI (OpenAI Codex), automaatselt TalTechNLP ASR-i segmendiväljundi põhjal. "
        "Transkript on toimetamata ja inimese poolt kinnitamata; ajamärgid pärinevad ASR-ist.",
        "",
        "## 2. Sisukord",
        "",
        "- [3. Metaandmed](#3-metaandmed)",
        "- [4. Ajastatud transkript](#4-ajastatud-transkript)",
        "",
        "## 3. Metaandmed",
        "",
        f"- Lesson ID: `{lesson['lesson_id']}`",
        f"- Konfiguratsioon: `{config['id']}`",
        f"- Mudel: `{config['model_id']}` revisjon `{config['model_revision']}`",
        f"- Kvaliteedi olek: `{result['quality_status']}`",
        f"- Heli kestus: `{_format_hms(result['audio']['duration_seconds'])}`",
        f"- Segmente: `{result['segment_count']}`",
        f"- Transkriptsiooniaeg: `{performance['transcription_seconds']} s`",
        f"- Reaalaja tegur: `{performance['real_time_factor']}`",
        "",
        "## 4. Ajastatud transkript",
        "",
    ]
    for segment in result["segments"]:
        lines.extend(
            [
                f"**[{_format_hms(segment['start_seconds'])}–{_format_hms(segment['end_seconds'])}]** "
                f"{segment['text']}",
                "",
            ]
        )
    return "\n".join(lines)


def _format_hms(seconds: float) -> str:
    whole_seconds = max(0, int(seconds))
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    raise SystemExit(main())
