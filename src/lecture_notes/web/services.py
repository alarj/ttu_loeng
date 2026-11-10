from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import threading
import uuid
import zipfile
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

from lecture_notes.echo360 import EchoClient, EchoError, build_resolver_manifest
from lecture_notes.manifests import atomic_write_json
from lecture_notes.slides import select_video_source_by_quality
from lecture_notes.web.models import Course, Lecture, SlideVersion, StoredUpload, UploadInput
from lecture_notes.web.ords import OrdsClient, OrdsError


ALLOWED_SLIDE_EXTENSIONS = {".pdf", ".ppt", ".pptx"}
DISPLAY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_RANGE_RE = re.compile(r"bytes=(?:\d+-\d*|-\d+)", re.IGNORECASE)
MARKDOWN_IMAGE_RE = re.compile(
    r"\]\(images/([A-Za-z0-9_.-]+\.(?:jpe?g|png|webp))(?:\s+(?:\"[^\"]*\"|'[^']*'))?\)",
    re.IGNORECASE,
)
UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
ORIGINAL_TRANSCRIPT_VERSION_ID = 0


@dataclass(frozen=True)
class VideoStream:
    status_code: int
    content_type: str
    headers: dict[str, str]
    body: Iterable[bytes]


@dataclass(frozen=True)
class TranscriptArchive:
    filename: str
    body: Iterable[bytes]


class ValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class LectureService:
    def __init__(
        self,
        repository: Any,
        ords: OrdsClient,
        runtime_root: Path,
        echo_factory: Callable[[], EchoClient] = EchoClient,
    ) -> None:
        self.repository = repository
        self.ords = ords
        self.runtime_root = runtime_root
        self.echo_factory = echo_factory
        self._video_source_lock = threading.Lock()
        self._video_sources: dict[int, tuple[EchoClient, str]] = {}

    def resolve(self, public_url: str) -> dict[str, Any]:
        return build_resolver_manifest(self.echo_factory(), public_url.strip())

    def create_submission(
        self,
        *,
        user_id: int,
        submission_request_id: str,
        public_url: str,
        selected_lesson_ids: Iterable[str],
        uploads: Iterable[UploadInput],
    ) -> int:
        try:
            submission_public_id = str(uuid.UUID(submission_request_id))
        except (ValueError, AttributeError) as exc:
            raise ValidationError("INVALID_SUBMISSION_REQUEST", "Invalid submission request ID") from exc
        existing_submission_id = self.repository.find_submission(user_id, submission_public_id)
        if existing_submission_id is not None:
            return existing_submission_id

        resolver = self.resolve(public_url)
        selected_ids = list(dict.fromkeys(selected_lesson_ids))
        lessons = {
            lesson["lesson_id"]: lesson
            for lesson in resolver["lessons"]
            if lesson.get("lesson_id") in selected_ids and lesson.get("recording_status") == "available"
        }
        if not selected_ids or set(selected_ids) != set(lessons):
            raise ValidationError("INVALID_SELECTION", "At least one available lecture must be selected")

        upload_by_lesson = {upload.lesson_id: upload for upload in uploads if upload.filename}
        if not set(upload_by_lesson).issubset(lessons):
            raise ValidationError("INVALID_UPLOAD", "Upload does not belong to a selected lecture")
        for upload in upload_by_lesson.values():
            if Path(upload.filename).suffix.lower() not in ALLOWED_SLIDE_EXTENSIONS:
                raise ValidationError("INVALID_UPLOAD", "Slides must be PDF, PPT or PPTX")

        resolver_relative = f"outputs/submissions/{submission_public_id}/resolver.json"
        resolver_path = self.runtime_root / resolver_relative
        created_paths: list[Path] = [resolver_path.parent]
        registrations: list[dict[str, Any]] = []
        atomic_write_json(resolver_path, resolver)
        try:
            with self.repository.transaction() as transaction:
                submission_id = transaction.insert_submission(
                    user_id,
                    submission_public_id,
                    resolver,
                    resolver_relative,
                )
                for lesson_id in selected_ids:
                    lesson = lessons[lesson_id]
                    lecture_id = transaction.insert_lecture(submission_id, lesson)
                    upload = upload_by_lesson.get(lesson_id)
                    if upload is not None:
                        stored = self._store_upload(lecture_id, upload)
                        created_paths.append(stored.absolute_path.parent)
                        transaction.insert_upload(lecture_id, stored)
                    asr_id, asr_key = transaction.insert_operation(lecture_id, "asr", None)
                    slides_id, slides_key = transaction.insert_operation(lecture_id, "slides", asr_id, 0)
                    registrations.append(
                        {
                            "lecture_id": lecture_id,
                            "asr_id": asr_id,
                            "asr_key": asr_key,
                            "slides_id": slides_id,
                            "slides_key": slides_key,
                        }
                    )
        except Exception:
            for path in reversed(created_paths):
                shutil.rmtree(path, ignore_errors=True)
            raise

        for registration in registrations:
            self._register_operations(registration)
        return submission_id

    def _store_upload(self, lecture_id: int, upload: UploadInput) -> StoredUpload:
        extension = Path(upload.filename).suffix.lower()
        relative_path = f"inputs/{lecture_id}/slides{extension}"
        absolute_path = self.runtime_root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=False)
        digest = hashlib.sha256()
        size = 0
        try:
            with absolute_path.open("xb") as target:
                while chunk := upload.stream.read(1024 * 1024):
                    target.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
        except Exception:
            shutil.rmtree(absolute_path.parent, ignore_errors=True)
            raise
        return StoredUpload(
            public_id=str(uuid.uuid4()),
            original_filename=Path(upload.filename).name,
            media_type=upload.media_type or "application/octet-stream",
            relative_path=relative_path,
            size_bytes=size,
            sha256=digest.hexdigest(),
            absolute_path=absolute_path,
        )

    def _register_operations(self, registration: dict[str, Any]) -> None:
        try:
            asr = self.ords.register_job(
                operation_id=registration["asr_id"],
                operation_type="asr",
                idempotency_key=registration["asr_key"],
                lecture_processing_id=registration["lecture_id"],
                previous_job_id=None,
            )
            asr_job_id = int(asr["job_id"])
            self.repository.set_operation_registered(registration["asr_id"], asr_job_id)
        except (OrdsError, KeyError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, OrdsError) else "INVALID_ORDS_RESPONSE"
            self.repository.set_registration_error(registration["asr_id"], code, str(exc))
            self.repository.set_registration_error(
                registration["slides_id"],
                "PREVIOUS_JOB_NOT_REGISTERED",
                "ASR job registration failed",
            )
            return

        try:
            slides = self.ords.register_job(
                operation_id=registration["slides_id"],
                operation_type="slides",
                idempotency_key=registration["slides_key"],
                lecture_processing_id=registration["lecture_id"],
                previous_job_id=asr_job_id,
            )
            self.repository.set_operation_registered(registration["slides_id"], int(slides["job_id"]))
        except (OrdsError, KeyError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, OrdsError) else "INVALID_ORDS_RESPONSE"
            self.repository.set_registration_error(registration["slides_id"], code, str(exc))

    def list_courses(self) -> list[Course]:
        return self.repository.list_courses()

    def get_course(self, canonical_section_id: str) -> Course:
        return self.repository.get_course(canonical_section_id)

    def list_lectures(self, canonical_section_id: str | None = None) -> list[Lecture]:
        lectures = [
            self._with_statuses(lecture)
            for lecture in self.repository.list_lectures(canonical_section_id)
        ]
        return sorted(
            lectures,
            key=lambda lecture: (
                (lecture.lecture_title or "").casefold(),
                lecture.lecture_start_at is None,
                lecture.lecture_start_at or datetime.max,
                lecture.lecture_processing_id,
            ),
        )

    def active_echo_lesson_ids(self, canonical_section_id: str) -> set[str]:
        return self.repository.active_echo_lesson_ids(canonical_section_id)

    def get_lecture(self, lecture_id: int) -> Lecture:
        return self._with_statuses(self.repository.get_lecture(lecture_id))

    def reprocess_slides(self, lecture_id: int, sensitivity_level: int) -> int:
        if sensitivity_level not in range(-3, 4):
            raise ValidationError("INVALID_SENSITIVITY", "Slide sensitivity level must be between -3 and +3")
        lecture = self.repository.get_lecture(lecture_id)
        operation_id, idempotency_key, previous_job_id = self.repository.create_slide_reprocessing(
            lecture_id,
            sensitivity_level,
        )
        try:
            response = self.ords.register_job(
                operation_id=operation_id,
                operation_type="slides",
                idempotency_key=idempotency_key,
                lecture_processing_id=lecture_id,
                previous_job_id=previous_job_id,
            )
            self.repository.set_operation_registered(operation_id, int(response["job_id"]))
        except (OrdsError, KeyError, TypeError, ValueError) as exc:
            code = exc.code if isinstance(exc, OrdsError) else "INVALID_ORDS_RESPONSE"
            self.repository.set_registration_error(operation_id, code, str(exc))
        return lecture.lecture_processing_id

    def _with_statuses(self, lecture: Lecture) -> Lecture:
        operations = []
        for operation in lecture.operations:
            status = None
            if operation.ords_job_id is not None:
                try:
                    status = str(self.ords.job_status(operation.ords_job_id).get("status") or "UNKNOWN")
                except OrdsError:
                    status = "UNAVAILABLE"
            elif operation.registration_error_message:
                status = "REGISTRATION_ERROR"
            operations.append(replace(operation, status=status or "NOT_REGISTERED"))
        lecture.operations = operations
        return lecture

    def slide_versions(self, lecture: Lecture) -> list[SlideVersion]:
        versions: list[SlideVersion] = []
        for operation in lecture.operations:
            if operation.operation_type != "slides" or operation.local_outcome != "SUCCEEDED":
                continue
            path = self._slide_result_path(lecture.lecture_processing_id, operation.operation_id)
            if path is None:
                continue
            versions.append(
                SlideVersion(
                    operation_id=operation.operation_id,
                    attempt_number=operation.attempt_number,
                    sensitivity_level=operation.slide_sensitivity_level,
                    markdown_path=path,
                    is_default=operation.operation_id == lecture.default_slides_operation_id,
                )
            )
        return sorted(versions, key=lambda version: version.attempt_number)

    def selected_slide_version(
        self,
        lecture: Lecture,
        requested_operation_id: int | None = None,
    ) -> SlideVersion | None:
        versions = self.slide_versions(lecture)
        if requested_operation_id is not None:
            return next((version for version in versions if version.operation_id == requested_operation_id), None)
        return next((version for version in versions if version.is_default), versions[0] if versions else None)

    def result_path(self, lecture: Lecture, version: SlideVersion | None = None) -> Path | None:
        if version is not None:
            return version.markdown_path
        selected = self.selected_slide_version(lecture)
        if selected is not None:
            return selected.markdown_path
        return self.original_transcript_path(lecture)

    def original_transcript_path(self, lecture: Lecture) -> Path | None:
        lecture_id = lecture.lecture_processing_id
        base = self.runtime_root / "outputs" / "jobs" / str(lecture_id)
        candidates = [base / "transcript" / "taltechnlp-turbo-et-verbatim-2604-int8" / "transcript.md"]
        return next((path for path in candidates if path.is_file()), None)

    def _slide_result_path(self, lecture_id: int, operation_id: int) -> Path | None:
        base = self.runtime_root / "outputs" / "jobs" / str(lecture_id) / "slides"
        versioned = base / str(operation_id) / "transcript_with_slides.md"
        if versioned.is_file():
            return versioned
        legacy = base / "transcript_with_slides.md"
        return legacy if legacy.is_file() else None

    def publishable_result_path(self, lecture: Lecture, version: SlideVersion | None = None) -> Path | None:
        selected = version or self.selected_slide_version(lecture)
        return selected.markdown_path if selected is not None else None

    def slide_image_path(
        self,
        lecture: Lecture,
        filename: str,
        version: SlideVersion | None = None,
    ) -> Path | None:
        if Path(filename).name != filename or Path(filename).suffix.lower() not in DISPLAY_IMAGE_EXTENSIONS:
            return None
        selected = version or self.selected_slide_version(lecture)
        if selected is None:
            return None
        path = selected.markdown_path.parent / "images" / filename
        return path if path.is_file() else None

    def video_stream(self, lecture_id: int, range_header: str | None) -> VideoStream:
        if range_header and VIDEO_RANGE_RE.fullmatch(range_header.strip()) is None:
            raise ValidationError("INVALID_VIDEO_RANGE", "Invalid video byte range")

        response = None
        for attempt in range(2):
            client, source_url = self._video_source(lecture_id, refresh=attempt > 0)
            try:
                response = client.open_media_stream(source_url, range_header)
                break
            except EchoError:
                if attempt:
                    raise
        if response is None:
            raise RuntimeError("Video stream was not opened")

        status_code = int(getattr(response, "status", response.getcode()))
        content_type = response.headers.get("Content-Type") or "video/mp4"
        headers = {"Accept-Ranges": "bytes", "Cache-Control": "private, no-store"}
        for name in ("Content-Length", "Content-Range"):
            value = response.headers.get(name)
            if value:
                headers[name] = value
        return VideoStream(
            status_code=status_code,
            content_type=content_type,
            headers=headers,
            body=_stream_chunks(response),
        )

    def _video_source(self, lecture_id: int, *, refresh: bool) -> tuple[EchoClient, str]:
        with self._video_source_lock:
            if refresh:
                self._video_sources.pop(lecture_id, None)
            cached = self._video_sources.get(lecture_id)
            if cached is not None:
                return cached

            lecture = self.repository.get_lecture(lecture_id)
            course = self.repository.get_course(lecture.echo_canonical_section_id)
            if not course.echo_public_url:
                raise ValidationError("MISSING_ECHO_URL", "Echo360 public course URL is missing")
            client = self.echo_factory()
            client.open_public_session(course.echo_public_url)
            media = client.get_lesson_media(lecture.echo_lesson_id)
            try:
                source_url, _, _, _ = select_video_source_by_quality(media, prefer_highest=False)
            except ValueError as exc:
                raise ValidationError("VIDEO_NOT_AVAILABLE", "Echo360 video is not available") from exc
            result = (client, source_url)
            self._video_sources[lecture_id] = result
            return result

    def public_result(self, public_id: str) -> tuple[Lecture, Path]:
        lecture = self.repository.get_public_lecture(public_id)
        path = self.publishable_result_path(lecture)
        if path is None:
            raise KeyError(public_id)
        return lecture, path

    def download_archive(self, lecture_id: int, version_id: int | None = None) -> TranscriptArchive:
        lecture = self.repository.get_lecture(lecture_id)
        if version_id == ORIGINAL_TRANSCRIPT_VERSION_ID:
            path = self.original_transcript_path(lecture)
            if path is None:
                raise KeyError(lecture_id)
            return self._transcript_archive(lecture, path, None)
        version = self.selected_slide_version(lecture, version_id)
        path = self.publishable_result_path(lecture, version)
        if path is None and version_id is None:
            path = self.original_transcript_path(lecture)
        if path is None:
            raise KeyError(lecture_id)
        return self._transcript_archive(lecture, path, version)

    def public_download_archive(self, public_id: str) -> TranscriptArchive:
        lecture, path = self.public_result(public_id)
        return self._transcript_archive(lecture, path, self.selected_slide_version(lecture))

    def _transcript_archive(
        self,
        lecture: Lecture,
        markdown_path: Path,
        version: SlideVersion | None,
    ) -> TranscriptArchive:
        title = _safe_filename(lecture.lecture_title or "loeng")
        markdown = markdown_path.read_text(encoding="utf-8")
        image_names = list(dict.fromkeys(MARKDOWN_IMAGE_RE.findall(markdown)))
        images: list[tuple[str, Path]] = []
        for image_name in image_names:
            image_path = self.slide_image_path(lecture, image_name, version)
            if image_path is None:
                raise ValidationError("MISSING_SLIDE_IMAGE", f"Missing referenced slide image: {image_name}")
            images.append((image_name, image_path))

        output = tempfile.SpooledTemporaryFile(max_size=16 * 1024 * 1024, mode="w+b")
        try:
            with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_STORED) as archive:
                root = f"{title}/"
                archive.writestr(root, b"")
                archive.writestr(f"{root}{title}.md", markdown.encode("utf-8"))
                if images:
                    archive.writestr(f"{root}images/", b"")
                    for image_name, image_path in images:
                        archive.write(image_path, f"{root}images/{image_name}")
            output.seek(0)
        except Exception:
            output.close()
            raise
        return TranscriptArchive(filename=f"{title}.zip", body=_stream_chunks(output))

    def set_public_sharing(self, lecture_id: int, enabled: bool) -> str | None:
        lecture = self.repository.get_lecture(lecture_id)
        if enabled and self.publishable_result_path(lecture) is None:
            raise ValidationError(
                "RESULT_NOT_PUBLISHABLE",
                "The transcript with slides is not ready",
            )
        return self.repository.set_public_sharing(lecture_id, enabled)

    def set_default_slide_version(self, lecture_id: int, operation_id: int) -> None:
        lecture = self.repository.get_lecture(lecture_id)
        version = self.selected_slide_version(lecture, operation_id)
        if version is None:
            raise ValidationError("INVALID_SLIDE_VERSION", "Slide version is not available")
        self.repository.set_default_slides_operation(lecture_id, operation_id)

    def soft_delete_lecture(self, lecture_id: int) -> Lecture:
        lecture = self.repository.get_lecture(lecture_id)
        self.repository.soft_delete_lecture(lecture_id)
        return lecture


def _stream_chunks(response: Any, chunk_size: int = 256 * 1024) -> Iterable[bytes]:
    try:
        while chunk := response.read(chunk_size):
            yield chunk
    finally:
        response.close()


def _safe_filename(value: str) -> str:
    safe = UNSAFE_FILENAME_RE.sub("_", value).strip(" .")
    return safe[:150].rstrip(" .") or "loeng"
