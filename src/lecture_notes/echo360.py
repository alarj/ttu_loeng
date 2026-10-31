from __future__ import annotations

import json
import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener


BASE_URL = "https://echo360.org.uk"
RESOLVER_VERSION = "0.1.0"
PUBLIC_URL_RE = re.compile(r"^/section/([0-9a-f-]{36})/public/?$")
CANONICAL_URL_RE = re.compile(r"^/section/([0-9a-f-]{36})/home/?$")


class EchoError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _HeadingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_h1 = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "h1" and not self._parts:
            self._in_h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._in_h1:
            value = " ".join(data.split())
            if value:
                self._parts.append(value)

    @property
    def heading(self) -> str | None:
        value = " ".join(self._parts).strip()
        return value or None


@dataclass(frozen=True)
class PublicSession:
    input_public_url: str
    public_section_id: str
    canonical_url: str
    canonical_section_id: str
    course_title: str | None


class EchoClient:
    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._cookies = CookieJar()
        self._opener = build_opener(HTTPCookieProcessor(self._cookies))

    def open_public_session(self, public_url: str) -> PublicSession:
        parsed = urlsplit(public_url)
        match = PUBLIC_URL_RE.fullmatch(parsed.path)
        if parsed.scheme != "https" or parsed.hostname != "echo360.org.uk" or not match:
            raise EchoError(
                "INVALID_PUBLIC_URL",
                "Oodatud on https://echo360.org.uk/section/<uuid>/public link.",
            )

        try:
            response = self._open(public_url, accept="text/html")
            body = response.read().decode("utf-8", errors="replace")
            canonical_url = response.geturl()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise EchoError("PUBLIC_SESSION_FAILED", f"Avaliku sessiooni loomine ebaõnnestus: {type(exc).__name__}") from exc

        canonical = urlsplit(canonical_url)
        canonical_match = CANONICAL_URL_RE.fullmatch(canonical.path)
        if canonical.hostname != "echo360.org.uk" or not canonical_match:
            raise EchoError("SECTION_NOT_FOUND", "Avalik link ei suunanud kanoonilisele kursusele.")

        parser = _HeadingParser()
        parser.feed(body)
        return PublicSession(
            input_public_url=public_url,
            public_section_id=match.group(1),
            canonical_url=f"{BASE_URL}{canonical.path}",
            canonical_section_id=canonical_match.group(1),
            course_title=parser.heading,
        )

    def get_syllabus(self, section_id: str) -> list[dict[str, Any]]:
        payload = self._get_json(f"/section/{section_id}/syllabus")
        data = payload.get("data")
        if payload.get("status") != "ok" or not isinstance(data, list):
            raise EchoError("SECTION_NOT_FOUND", "Kursuse loengute nimekiri ei olnud kasutatav.")
        return data

    def get_lesson_media(self, lesson_id: str) -> dict[str, Any]:
        payload = self._get_json(f"/lesson/{lesson_id}/media")
        data = payload.get("data")
        if payload.get("status") != "ok" or not isinstance(data, list) or not data:
            raise EchoError("MEDIA_NOT_FOUND", "Loengu meediaandmeid ei leitud.")
        first = data[0]
        if not isinstance(first, dict):
            raise EchoError("MEDIA_NOT_FOUND", "Loengu meediaandmete kuju ei olnud kasutatav.")
        return first

    def session_metadata(self) -> dict[str, Any]:
        cookies = list(self._cookies)
        expiries = sorted(cookie.expires for cookie in cookies if cookie.expires is not None)
        return {
            "cookie_count": len(cookies),
            "cookie_names": sorted({cookie.name for cookie in cookies}),
            "persistent_cookie_count": len(expiries),
            "earliest_expiry_utc": _format_timestamp(expiries[0]) if expiries else None,
            "latest_expiry_utc": _format_timestamp(expiries[-1]) if expiries else None,
            "cookie_values_persisted": False,
        }

    def download_media(self, source_url: str, target: Path) -> dict[str, Any]:
        parsed = urlsplit(source_url)
        if (
            parsed.scheme != "https"
            or parsed.hostname is None
            or not (parsed.hostname == "echo360.org.uk" or parsed.hostname.endswith(".echo360.org.uk"))
        ):
            raise EchoError("MEDIA_SOURCE_NOT_ALLOWED", "Meediaallikas ei kuulu lubatud Echo360 HTTPS domeeni alla.")

        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        temporary = Path(temporary_name)
        digest = hashlib.sha256()
        size = 0
        content_type: str | None = None
        try:
            with os.fdopen(descriptor, "wb") as handle:
                response = self._open(source_url, accept="audio/*,video/*;q=0.5")
                content_type = response.headers.get_content_type()
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(target)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            temporary.unlink(missing_ok=True)
            raise EchoError("DOWNLOAD_FAILED", f"Meedia allalaadimine ebaõnnestus: {type(exc).__name__}") from exc

        return {
            "path": str(target),
            "size_bytes": size,
            "sha256": digest.hexdigest(),
            "content_type": content_type,
            "source_host": parsed.hostname,
            "source_path": parsed.path,
            "source_query_persisted": False,
        }

    def _get_json(self, path: str) -> dict[str, Any]:
        try:
            response = self._open(urljoin(BASE_URL, path), accept="application/json")
            payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EchoError("ECHO_REQUEST_FAILED", f"Echo360 JSON-päring ebaõnnestus: {type(exc).__name__}") from exc
        if not isinstance(payload, dict):
            raise EchoError("ECHO_REQUEST_FAILED", "Echo360 JSON-vastus ei olnud objekt.")
        return payload

    def _open(self, url: str, accept: str):
        request = Request(
            url,
            headers={
                "Accept": accept,
                "User-Agent": f"ttu-loeng-importer/{RESOLVER_VERSION}",
            },
        )
        return self._opener.open(request, timeout=self.timeout_seconds)


def build_resolver_manifest(
    client: EchoClient,
    public_url: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    observed_at = _as_utc(now or datetime.now(timezone.utc))
    session = client.open_public_session(public_url)
    syllabus = client.get_syllabus(session.canonical_section_id)
    lessons = [normalize_lesson(wrapper, observed_at) for wrapper in iter_lesson_wrappers(syllabus)]
    warnings = [
        {"lesson_id": lesson["lesson_id"], **warning}
        for lesson in lessons
        for warning in lesson["warnings"]
    ]
    return {
        "schema_version": "1.0",
        "resolver_version": RESOLVER_VERSION,
        "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "input_public_url": session.input_public_url,
        "public_section_id": session.public_section_id,
        "canonical_url": session.canonical_url,
        "canonical_section_id": session.canonical_section_id,
        "course_title": session.course_title,
        "session": client.session_metadata(),
        "lesson_count": len(lessons),
        "lessons": lessons,
        "warnings": warnings,
    }


def iter_lesson_wrappers(rows: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("type") == "SyllabusLessonType" and isinstance(row.get("lesson"), dict):
            yield row["lesson"]
        elif row.get("type") == "SyllabusGroupType":
            nested = row.get("lessons")
            if isinstance(nested, list):
                yield from iter_lesson_wrappers(nested)


def normalize_lesson(wrapper: dict[str, Any], observed_at: datetime) -> dict[str, Any]:
    lesson = wrapper.get("lesson") if isinstance(wrapper.get("lesson"), dict) else {}
    medias = wrapper.get("medias") if isinstance(wrapper.get("medias"), list) else []
    media_items = [normalize_media_summary(item) for item in medias if isinstance(item, dict)]
    start = _parse_echo_datetime(wrapper.get("startTimeUTC"))
    end = _parse_echo_datetime(wrapper.get("endTimeUTC"))
    derived_status = derive_time_status(start, end, observed_at)
    echo_status = {
        "is_past": _bool_or_none(wrapper.get("isPast")),
        "is_future": _bool_or_none(wrapper.get("isFuture")),
        "is_live": _bool_or_none(wrapper.get("isLive")),
        "is_scheduled": _bool_or_none(wrapper.get("isScheduled")),
    }
    recording_status = derive_recording_status(media_items)
    warnings: list[dict[str, str]] = []
    if time_status_conflicts(echo_status, derived_status):
        warnings.append(
            {
                "code": "ECHO_TIME_STATUS_CONFLICT",
                "message": "Echo ajatuse lipud ei ühti ajatemplist tuletatud olekuga.",
            }
        )
    has_content = bool(wrapper.get("hasContent"))
    if not has_content and media_items:
        warnings.append(
            {
                "code": "ECHO_CONTENT_MEDIA_CONFLICT",
                "message": "Echo hasContent=false, kuid loengul on meediakirjeid.",
            }
        )
    return {
        "lesson_id": lesson.get("id"),
        "name": lesson.get("name"),
        "display_name": lesson.get("displayName"),
        "start_time_utc": _format_datetime(start),
        "end_time_utc": _format_datetime(end),
        "echo_time_status": echo_status,
        "derived_time_status": derived_status,
        "content_status": "present" if has_content else "not_present",
        "recording_status": recording_status,
        "has_video_flag": _bool_or_none(wrapper.get("hasVideo")),
        "has_slide_deck_flag": _bool_or_none(wrapper.get("hasSlideDeck")),
        "media_count": len(media_items),
        "media": media_items,
        "warnings": warnings,
    }


def normalize_media_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "media_id": item.get("id"),
        "title": item.get("title"),
        "media_type": item.get("mediaType"),
        "is_available": _bool_or_none(item.get("isAvailable")),
        "is_processing": _bool_or_none(item.get("isProcessing")),
        "is_failed": _bool_or_none(item.get("isFailed")),
        "is_preliminary": _bool_or_none(item.get("isPreliminary")),
        "is_audio_only": _bool_or_none(item.get("isAudioOnly")),
        "is_scheduled": _bool_or_none(item.get("isScheduled")),
    }


def derive_recording_status(media_items: list[dict[str, Any]]) -> str:
    recordings = [item for item in media_items if item.get("media_type") in {"Video", "Audio"}]
    if any(item.get("is_available") is True for item in recordings):
        return "available"
    if any(item.get("is_processing") is True for item in recordings):
        return "processing"
    if any(item.get("is_failed") is True for item in recordings):
        return "failed"
    return "not_available"


def derive_time_status(start: datetime | None, end: datetime | None, now: datetime) -> str:
    if start is None or end is None:
        return "unknown"
    if end < now:
        return "past"
    if start > now:
        return "future"
    return "current"


def time_status_conflicts(echo_status: dict[str, bool | None], derived_status: str) -> bool:
    if derived_status == "past":
        return echo_status["is_past"] is False or echo_status["is_future"] is True
    if derived_status == "future":
        return echo_status["is_future"] is False or echo_status["is_past"] is True
    if derived_status == "current":
        return echo_status["is_past"] is True or echo_status["is_future"] is True
    return False


def _parse_echo_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_datetime(value: datetime | None) -> str | None:
    return value.isoformat().replace("+00:00", "Z") if value else None


def _format_timestamp(value: int) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
