from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from lecture_notes.config import ensure_runtime_output, settings
from lecture_notes.manifests import atomic_write_json


PROMPT = (
    "See on automaatne loengu transkriptsioon -- koostatud salvestise põhjal.\n"
    "Koosta selle alusel normaalne kirjakeelne tekst, eemalda tarbetud kordused ja vaata üle lauselõpud.\n"
    "Säilita erialaterminid ja ingliskeelsed terminid."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-notes-editor")
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--sample-id")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--model", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = settings()
    try:
        result = run_trial(
            transcript_path=args.transcript,
            selection_path=args.selection,
            sample_id=args.sample_id,
            output_dir=ensure_runtime_output(args.output_dir, config),
            ollama_url=args.ollama_url
            or __import__("os").environ.get("EDITOR_OLLAMA_URL", "http://llm-ollama:11434"),
            model=args.model
            or __import__("os").environ.get(
                "EDITOR_LLM_MODEL",
                "hf.co/mradermacher/Llama-3.1-EstLLM-8B-Instruct-1125-GGUF:Q5_K_M",
            ),
        )
        print(json.dumps({"status": "ok", "output": str(args.output_dir), "samples": result["sample_count"]}))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)[:2000]}), file=sys.stderr)
        return 2


def run_trial(
    *,
    transcript_path: Path,
    selection_path: Path,
    sample_id: str | None,
    output_dir: Path,
    ollama_url: str,
    model: str,
) -> dict[str, Any]:
    transcript = _read_json(transcript_path)
    selection = _read_json(selection_path)
    chunks = extract_chunks(transcript, selection, sample_id=sample_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_path = output_dir / "run.json"
    started_at = _utc_now()
    base = {
        "schema_version": "1.0",
        "status": "running",
        "started_at": started_at,
        "model": model,
        "prompt_sha256": hashlib.sha256(PROMPT.encode("utf-8")).hexdigest(),
        "transcript_sha256": _file_sha256(transcript_path),
        "selection_sha256": _file_sha256(selection_path),
        "sample_count": len(chunks),
    }
    atomic_write_json(run_path, base)
    started = time.perf_counter()
    try:
        version = _ollama_json(ollama_url, "/api/version", None, timeout_seconds=30)
        tags = _ollama_json(ollama_url, "/api/tags", None, timeout_seconds=30)
        model_info = _find_model(tags, model)
        if model_info is None:
            raise RuntimeError(f"Requested Ollama model is not installed: {model}")
        sample_results: list[dict[str, Any]] = []
        for chunk in chunks:
            sample_dir = output_dir / chunk["id"]
            sample_dir.mkdir(parents=True, exist_ok=True)
            _write_text(sample_dir / "source.txt", chunk["text"])
            response = _ollama_json(
                ollama_url,
                "/api/generate",
                {
                    "model": model,
                    "prompt": PROMPT + "\n\n" + chunk["text"],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 2048},
                },
                timeout_seconds=7200,
            )
            edited = response.get("response", "").strip()
            if not edited:
                raise RuntimeError(f"Ollama returned an empty response for {chunk['id']}")
            _write_text(sample_dir / "edited.md", edited)
            _write_text(sample_dir / "review.md", render_review(chunk, edited))
            sample_results.append(
                {
                    "sample_id": chunk["id"],
                    "start_seconds": chunk["start_seconds"],
                    "end_seconds": chunk["end_seconds"],
                    "segment_ids": chunk["segment_ids"],
                    "total_duration_ns": response.get("total_duration"),
                    "prompt_eval_count": response.get("prompt_eval_count"),
                    "eval_count": response.get("eval_count"),
                    "human_review_status": "unreviewed",
                }
            )
        completed = {
            **base,
            "status": "completed",
            "completed_at": _utc_now(),
            "duration_seconds": round(time.perf_counter() - started, 3),
            "model": {
                "name": model_info.get("name") or model_info.get("model"),
                "digest": model_info.get("digest"),
            },
            "ollama_version": version.get("version"),
            "samples": sample_results,
            "human_review_status": "unreviewed",
        }
        atomic_write_json(run_path, completed)
        return completed
    except Exception as exc:
        atomic_write_json(
            run_path,
            {
                **base,
                "status": "failed",
                "completed_at": _utc_now(),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "error": {"type": type(exc).__name__, "message": str(exc)[:2000]},
            },
        )
        raise


def extract_chunks(
    transcript: dict[str, Any], selection: dict[str, Any], *, sample_id: str | None = None
) -> list[dict[str, Any]]:
    segment_by_id = {item.get("id"): item for item in transcript.get("segments", []) if isinstance(item, dict)}
    chunks: list[dict[str, Any]] = []
    for selected in selection.get("samples", []):
        if sample_id is not None and selected.get("id") != sample_id:
            continue
        segment_ids = selected.get("segment_ids")
        if not isinstance(segment_ids, list) or not segment_ids:
            raise ValueError(f"Sample has no segment IDs: {selected.get('id')}")
        missing = [segment_id for segment_id in segment_ids if segment_id not in segment_by_id]
        if missing:
            raise ValueError(f"Selected transcript segments do not exist: {missing}")
        segments = [segment_by_id[segment_id] for segment_id in segment_ids]
        chunks.append(
            {
                "id": selected["id"],
                "label": selected["label"],
                "segment_ids": segment_ids,
                "start_seconds": segments[0]["start_seconds"],
                "end_seconds": segments[-1]["end_seconds"],
                "text": "\n\n".join(segment["text"].strip() for segment in segments),
            }
        )
    if sample_id is not None and not chunks:
        raise ValueError(f"Selected sample does not exist: {sample_id}")
    if not chunks:
        raise ValueError("Selection contains no samples")
    return chunks


def render_review(chunk: dict[str, Any], edited: str) -> str:
    return (
        f"# {chunk['label']}\n\n"
        "## 1. Dokumendi päritolu\n\n"
        "Võrdlusvaate koostas AI automaatselt TalTechNLP transkriptsioonilõigu ja EstLLM-i toimetatud teksti põhjal. "
        "Tulemust ei ole inimene veel kinnitanud.\n\n"
        "## 2. Sisukord\n\n- [3. Lähtetekst](#3-lähtetekst)\n- [4. Toimetatud tekst](#4-toimetatud-tekst)\n\n"
        f"## 3. Lähtetekst\n\n{chunk['text']}\n\n"
        f"## 4. Toimetatud tekst\n\n{edited}\n"
    )


def _find_model(tags: dict[str, Any], requested: str) -> dict[str, Any] | None:
    candidates = {requested, requested.removesuffix(":latest")}
    for item in tags.get("models", []):
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and (name in candidates or name.removesuffix(":latest") in candidates):
            return item
    return None


def _ollama_json(base_url: str, path: str, payload: dict[str, Any] | None, *, timeout_seconds: int) -> dict[str, Any]:
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
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


def _write_text(path: Path, value: str) -> None:
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
