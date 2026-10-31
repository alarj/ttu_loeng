from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


def build_lesson_manifests(
    resolver: dict[str, Any],
    lesson_id: str,
    media_payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    lesson = next(
        (item for item in resolver["lessons"] if item.get("lesson_id") == lesson_id),
        None,
    )
    if lesson is None:
        raise KeyError(lesson_id)

    video = media_payload.get("video") if isinstance(media_payload.get("video"), dict) else None
    video_media = video.get("media") if isinstance(video, dict) and isinstance(video.get("media"), dict) else None
    media_data = video_media.get("media") if isinstance(video_media, dict) and isinstance(video_media.get("media"), dict) else {}
    current = media_data.get("current") if isinstance(media_data.get("current"), dict) else {}

    sources: list[dict[str, Any]] = []
    sources.extend(_source_descriptors(current.get("audioFiles"), "audio"))
    sources.extend(_source_descriptors(current.get("primaryFiles"), "primary_video"))
    sources.extend(_source_descriptors(current.get("secondaryFiles"), "secondary_video"))
    sources.extend(_source_descriptors(current.get("tertiaryFiles"), "tertiary_video"))
    sources.extend(_source_descriptors(current.get("quaternaryFiles"), "quaternary_video"))

    detailed_media = media_payload.get("medias") if isinstance(media_payload.get("medias"), list) else []
    safe_media = [
        {
            "media_id": item.get("id"),
            "title": item.get("title"),
            "media_type": item.get("mediaType"),
            "is_available": item.get("isAvailable"),
            "is_processing": item.get("isProcessing"),
            "is_failed": item.get("isFailed"),
            "is_preliminary": item.get("isPreliminary"),
            "is_downloadable": item.get("isDownloadable"),
        }
        for item in detailed_media
        if isinstance(item, dict)
    ]

    media_manifest = {
        "schema_version": "1.0",
        "lesson_id": lesson_id,
        "recording_status": lesson["recording_status"],
        "echo_flags": {
            "has_content": media_payload.get("hasContent"),
            "has_video": media_payload.get("hasVideo"),
            "has_available_video": media_payload.get("hasAvailableVideo"),
            "has_slide_deck": media_payload.get("hasSlideDeck"),
            "has_available_slide_deck": media_payload.get("hasAvailableSlideDeck"),
            "is_past": media_payload.get("isPast"),
            "is_future": media_payload.get("isFuture"),
            "is_live": media_payload.get("isLive"),
            "is_scheduled": media_payload.get("isScheduled"),
        },
        "media_id": video_media.get("id") if isinstance(video_media, dict) else None,
        "media_name": video_media.get("name") if isinstance(video_media, dict) else None,
        "media_status": video_media.get("status") if isinstance(video_media, dict) else None,
        "media_type": media_data.get("type"),
        "duration_ms": media_data.get("duration"),
        "items": safe_media,
        "sources": sources,
        "warnings": list(lesson.get("warnings") or []),
    }

    slide_available = media_payload.get("hasAvailableSlideDeck") is True
    slides_manifest = {
        "schema_version": "1.0",
        "lesson_id": lesson_id,
        "status": "available_not_yet_imported" if slide_available else "not_provided_by_echo",
        "echo_has_slide_deck": media_payload.get("hasSlideDeck"),
        "echo_has_available_slide_deck": media_payload.get("hasAvailableSlideDeck"),
        "slides": [],
        "warnings": []
        if slide_available
        else [
            {
                "code": "SLIDES_NOT_PROVIDED_BY_ECHO",
                "message": "Echo360 ei paku selle loengu juures eraldi slide deck'i.",
            }
        ],
    }

    lesson_manifest = {
        "schema_version": "1.0",
        "public_section_id": resolver["public_section_id"],
        "canonical_section_id": resolver["canonical_section_id"],
        "course_title": resolver.get("course_title"),
        **lesson,
    }
    return lesson_manifest, media_manifest, slides_manifest


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def get_audio_source(media_payload: dict[str, Any]) -> tuple[str, int | None] | None:
    video = media_payload.get("video") if isinstance(media_payload.get("video"), dict) else None
    video_media = video.get("media") if isinstance(video, dict) and isinstance(video.get("media"), dict) else None
    media_data = video_media.get("media") if isinstance(video_media, dict) and isinstance(video_media.get("media"), dict) else None
    current = media_data.get("current") if isinstance(media_data, dict) and isinstance(media_data.get("current"), dict) else None
    audio_files = current.get("audioFiles") if isinstance(current, dict) else None
    if not isinstance(audio_files, list):
        return None
    for item in audio_files:
        if isinstance(item, dict) and isinstance(item.get("s3Url"), str):
            expected_size = item.get("size") if isinstance(item.get("size"), int) else None
            return item["s3Url"], expected_size
    return None


def _source_descriptors(values: Any, kind: str) -> Iterable[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            continue
        url = item.get("s3Url")
        parsed = urlsplit(url) if isinstance(url, str) else None
        result.append(
            {
                "kind": kind,
                "source_index": index,
                "host": parsed.hostname if parsed else None,
                "path": parsed.path if parsed else None,
                "has_query": bool(parsed.query) if parsed else None,
                "size_bytes": item.get("size"),
                "width": item.get("width"),
                "height": item.get("height"),
            }
        )
    return result
