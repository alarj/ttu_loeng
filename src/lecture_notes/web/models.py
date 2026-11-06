from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO


@dataclass(frozen=True)
class User:
    user_id: int
    public_id: str
    email: str
    display_name: str
    role_code: str
    enabled: bool

    @property
    def is_admin(self) -> bool:
        return self.role_code == "ADMIN"


@dataclass(frozen=True)
class UploadInput:
    lesson_id: str
    filename: str
    media_type: str
    stream: BinaryIO


@dataclass(frozen=True)
class StoredUpload:
    public_id: str
    original_filename: str
    media_type: str
    relative_path: str
    size_bytes: int
    sha256: str
    absolute_path: Path


@dataclass(frozen=True)
class Operation:
    operation_id: int
    operation_type: str
    attempt_number: int
    ords_job_id: int | None
    slide_sensitivity_level: int | None = None
    local_outcome: str | None = None
    registration_error_message: str | None = None
    status: str | None = None
    local_started_at: object | None = None
    local_completed_at: object | None = None


@dataclass(frozen=True)
class Course:
    echo_canonical_section_id: str
    course_title: str
    lecture_count: int
    echo_public_url: str | None = None


@dataclass
class Lecture:
    lecture_processing_id: int
    public_id: str | None
    submission_id: int
    echo_canonical_section_id: str
    course_title: str | None
    lecture_title: str | None
    echo_lesson_id: str
    lecture_start_at: object | None
    duration_seconds: float | None
    recording_status: str
    created: object
    default_slides_operation_id: int | None
    operations: list[Operation]

    @property
    def asr_succeeded(self) -> bool:
        return any(
            operation.operation_type == "asr" and operation.local_outcome == "SUCCEEDED"
            for operation in self.operations
        )


@dataclass(frozen=True)
class SlideVersion:
    operation_id: int
    attempt_number: int
    sensitivity_level: int | None
    markdown_path: Path
    is_default: bool

