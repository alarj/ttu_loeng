from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from lecture_notes.config import ensure_runtime_output, settings
from lecture_notes.manifests import atomic_write_json


DEFAULT_MODEL = "hf.co/mradermacher/Llama-3.1-EstLLM-8B-Instruct-1125-GGUF:Q5_K_M"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-notes-full-notes")
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--syllabus", type=Path, required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--slides", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_URL", "http://llm-ollama:11434"))
    parser.add_argument("--model", default=os.environ.get("STAGE3_LLM_MODEL", DEFAULT_MODEL))
    parser.add_argument("--num-ctx", type=int, default=65536)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = settings()
    try:
        output_dir = ensure_runtime_output(args.output_dir, config)
        output_dir.mkdir(parents=True, exist_ok=True)
        source_prompt, slide_count = build_source_prompt(
            prompt_path=args.prompt,
            syllabus_path=args.syllabus,
            transcript_path=args.transcript,
            slides_path=args.slides,
            output_dir=output_dir,
        )
        (output_dir / "input.md").write_text(source_prompt, encoding="utf-8")
        run_generation(
            prompt=source_prompt,
            output_dir=output_dir,
            ollama_url=args.ollama_url,
            model=args.model,
            num_ctx=args.num_ctx,
            slide_count=slide_count,
        )
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)[:2000]}))
        return 2


def build_source_prompt(
    *,
    prompt_path: Path,
    syllabus_path: Path,
    transcript_path: Path,
    slides_path: Path,
    output_dir: Path,
) -> tuple[str, int]:
    template = prompt_path.read_text(encoding="utf-8")
    syllabus = syllabus_path.read_text(encoding="utf-8")
    transcript = transcript_path.read_text(encoding="utf-8")
    frames = json.loads(slides_path.read_text(encoding="utf-8"))

    syllabus_excerpt = _between(syllabus, "Nädal 3", "Nädal 4")
    slides_text, slide_count = _slides_for_prompt(frames, output_dir)
    replacements = {
        "[Siia lisatakse ainekava vastavad osad.]": syllabus_excerpt,
        "[Siia lisatakse kogu loengu ajatemplitega algtranskript.]": transcript,
        "[Siia lisatakse slaidide pilditeed, pealkirjad või kirjeldused ja täpsed ajamärgid.]": slides_text,
    }
    for marker, content in replacements.items():
        if marker not in template:
            raise ValueError(f"Prompt placeholder is missing: {marker}")
        template = template.replace(marker, content, 1)
    return template, slide_count


def run_generation(
    *,
    prompt: str,
    output_dir: Path,
    ollama_url: str,
    model: str,
    num_ctx: int,
    slide_count: int,
) -> None:
    started_at = _utc_now()
    started = time.perf_counter()
    run_path = output_dir / "run.json"
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    base_run: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "running",
        "started_at": started_at,
        "model": model,
        "prompt_sha256": prompt_sha256,
        "input_characters": len(prompt),
        "input_words": len(re.findall(r"\S+", prompt)),
        "slide_count": slide_count,
        "num_ctx": num_ctx,
    }
    atomic_write_json(run_path, base_run)
    try:
        response = _ollama_json(
            ollama_url,
            "/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": num_ctx,
                    "repeat_penalty": 1.15,
                    "repeat_last_n": 256,
                },
            },
            timeout_seconds=86400,
        )
        markdown = response.get("response", "").strip()
        if not markdown:
            raise RuntimeError("Ollama returned an empty response")
        (output_dir / "konspekt.md").write_text(markdown + "\n", encoding="utf-8")
        atomic_write_json(output_dir / "raw_response.json", response)
        atomic_write_json(
            run_path,
            {
                **base_run,
                "status": "completed",
                "completed_at": _utc_now(),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "output_characters": len(markdown),
                "output_words": len(re.findall(r"\S+", markdown)),
                "eval_count": response.get("eval_count"),
                "prompt_eval_count": response.get("prompt_eval_count"),
                "done_reason": response.get("done_reason"),
            },
        )
    except Exception as exc:
        atomic_write_json(
            run_path,
            {
                **base_run,
                "status": "failed",
                "completed_at": _utc_now(),
                "duration_seconds": round(time.perf_counter() - started, 3),
                "error": {"type": type(exc).__name__, "message": str(exc)[:2000]},
            },
        )
        raise


def _slides_for_prompt(manifest: dict[str, Any], output_dir: Path) -> tuple[str, int]:
    selected: list[dict[str, Any]] = []
    previous_title = ""
    for frame in manifest.get("frames", []):
        ocr_raw = str(frame.get("ocr_text", ""))
        ocr = " ".join(ocr_raw.split())
        title = next((line.strip() for line in ocr_raw.splitlines() if line.strip()), "")
        normalized = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
        if not normalized or normalized == previous_title:
            continue
        previous_title = normalized
        selected.append({**frame, "ocr_compact": ocr[:700]})

    lines: list[str] = []
    for frame in selected:
        timestamp = _format_time(float(frame["timestamp_seconds"]))
        source = Path(frame["path"].replace("/runtime", str(settings().runtime_root), 1))
        relative = os.path.relpath(source, output_dir)
        lines.extend(
            [
                f"- {frame['id']} · {timestamp}",
                f"  Pilditee: {relative}",
                f"  Slaidilt tuvastatud tekst: {frame['ocr_compact'] or '[tekst ei olnud tuvastatav]'}",
            ]
        )
    return "\n".join(lines), len(selected)


def _between(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise ValueError(f"Syllabus start marker not found: {start_marker}")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise ValueError(f"Syllabus end marker not found: {end_marker}")
    return text[start:end].strip()


def _format_time(seconds: float) -> str:
    total = round(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _ollama_json(base_url: str, path: str, payload: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
