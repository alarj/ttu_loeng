from __future__ import annotations

import argparse
import hashlib
import json
import resource
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from lecture_notes.config import ensure_runtime_output, settings
from lecture_notes.echo360 import EchoClient, EchoError, build_resolver_manifest
from lecture_notes.manifests import atomic_write_json, build_lesson_manifests, get_audio_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-notes")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout sekundites")
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve = subparsers.add_parser("resolve", help="Loo kursuse ja loengute manifest")
    resolve.add_argument("public_url")
    resolve.add_argument("--output-dir", type=Path, required=True)

    ingest = subparsers.add_parser("ingest", help="Loo valitud loengu meedia- ja slaidimanifest")
    ingest.add_argument("public_url")
    ingest.add_argument("--lesson-id", required=True)
    ingest.add_argument("--output-dir", type=Path, required=True)
    ingest.add_argument("--download-audio", action="store_true", help="Laadi Echo audio ajutiselt work/ kataloogi ja kontrolli see")
    ingest.add_argument("--keep-audio", action="store_true", help="Säilita ajutine audio teadlikult veaotsinguks")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = settings()
    client = EchoClient(timeout_seconds=args.timeout)
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    try:
        try:
            output_dir = ensure_runtime_output(args.output_dir, config)
        except ValueError as exc:
            raise EchoError("INVALID_OUTPUT_DIR", str(exc)) from exc
        if getattr(args, "keep_audio", False) and not getattr(args, "download_audio", False):
            raise EchoError("INVALID_ARGUMENT", "--keep-audio vajab ka --download-audio valikut.")
        resolver = build_resolver_manifest(client, args.public_url)
        if args.command == "resolve":
            output = output_dir / "resolver.json"
            atomic_write_json(output, resolver)
            _print_result("resolved", output, {"lesson_count": resolver["lesson_count"]})
            return 0

        if args.command == "ingest":
            media = client.get_lesson_media(args.lesson_id)
            try:
                lesson_manifest, media_manifest, slides_manifest = build_lesson_manifests(
                    resolver,
                    args.lesson_id,
                    media,
                )
            except KeyError as exc:
                raise EchoError("LESSON_NOT_FOUND", "Valitud lesson ID ei kuulu sellele kursusele.") from exc
            lesson_dir = output_dir / "lessons" / args.lesson_id
            if args.download_audio:
                _verify_audio(client, media, media_manifest, args.lesson_id, config.work_root, args.keep_audio)
            atomic_write_json(output_dir / "resolver.json", resolver)
            atomic_write_json(lesson_dir / "lesson.json", lesson_manifest)
            atomic_write_json(lesson_dir / "media.json", media_manifest)
            atomic_write_json(lesson_dir / "slides.json", slides_manifest)
            atomic_write_json(
                lesson_dir / "run.json",
                _run_manifest(started_at, started, args.command, "ok"),
            )
            _print_result(
                "ingested",
                lesson_dir,
                {
                    "recording_status": media_manifest["recording_status"],
                    "slide_status": slides_manifest["status"],
                    "source_count": len(media_manifest["sources"]),
                    "audio_verified": "audio_verification" in media_manifest,
                },
            )
            return 0
    except EchoError as exc:
        print(json.dumps({"status": "error", "code": exc.code, "message": exc.message}, ensure_ascii=False), file=sys.stderr)
        return 2

    return 2


def _verify_audio(
    client: EchoClient,
    media: dict[str, object],
    media_manifest: dict[str, object],
    lesson_id: str,
    work_root: Path,
    keep_audio: bool,
) -> None:
    audio_source = get_audio_source(media)
    if audio_source is None:
        raise EchoError("MEDIA_NOT_FOUND", "Loengul ei ole eraldi allalaaditavat audioallikat.")
    source_url, expected_size = audio_source
    work_key = hashlib.sha256(lesson_id.encode("utf-8")).hexdigest()[:16]
    work_dir = work_root / "ingest" / work_key
    audio_path = work_dir / "source.mp3"
    download: dict[str, object] | None = None
    try:
        download = client.download_media(source_url, audio_path)
        download["expected_size_bytes"] = expected_size
        download["size_matches_expected"] = expected_size is None or download["size_bytes"] == expected_size
    finally:
        if not keep_audio:
            shutil.rmtree(work_dir, ignore_errors=True)

    if download is None:
        return
    download["retained"] = keep_audio
    download["cleanup_status"] = "retained_by_request" if keep_audio else "removed"
    download["path"] = str(audio_path) if keep_audio else None
    media_manifest["audio_verification"] = download


def _print_result(status: str, output: Path, details: dict[str, object]) -> None:
    print(
        json.dumps(
            {"status": status, "output": str(output), **details},
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _run_manifest(started_at: datetime, started: float, command: str, status: str) -> dict[str, object]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "schema_version": "1.0",
        "command": command,
        "status": status,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "duration_seconds": round(time.perf_counter() - started, 3),
        "max_rss_kib": usage.ru_maxrss,
    }
