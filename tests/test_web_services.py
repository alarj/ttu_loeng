from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from lecture_notes.web.models import Lecture, Operation, UploadInput
from lecture_notes.web.ords import OrdsError
from lecture_notes.web.services import LectureService, ValidationError
from storage_test_utils import FileStorage


RESOLVER = {
    "input_public_url": "https://echo360.org.uk/section/11111111-1111-1111-1111-111111111111/public",
    "public_section_id": "11111111-1111-1111-1111-111111111111",
    "canonical_section_id": "22222222-2222-2222-2222-222222222222",
    "course_title": "Testkursus",
    "lessons": [
        {
            "lesson_id": "33333333-3333-3333-3333-333333333333",
            "display_name": "Loeng 1",
            "start_time_utc": "2026-11-01T10:00:00Z",
            "end_time_utc": "2026-11-01T11:00:00Z",
            "recording_status": "available",
        },
        {
            "lesson_id": "44444444-4444-4444-4444-444444444444",
            "display_name": "Loeng 2",
            "start_time_utc": "2026-11-02T10:00:00Z",
            "end_time_utc": "2026-11-02T11:00:00Z",
            "recording_status": "processing",
        },
    ],
}


class FakeTransaction:
    def __init__(self) -> None:
        self.uploads = []
        self.operations = []

    def insert_submission(self, user_id, public_id, resolver, resolver_path):
        self.submission = (user_id, public_id, resolver, resolver_path)
        return 10

    def insert_lecture(self, submission_id, lesson):
        self.lecture = (submission_id, lesson)
        return 20

    def insert_upload(self, lecture_id, upload):
        self.uploads.append((lecture_id, upload))
        return 30

    def insert_operation(self, lecture_id, operation_type, previous_id, slide_sensitivity_level=None):
        operation_id = 40 if operation_type == "asr" else 41
        self.operations.append((lecture_id, operation_type, previous_id, slide_sensitivity_level))
        return operation_id, f"key-{operation_type}"


class FakeRepository:
    def __init__(self) -> None:
        self.tx = FakeTransaction()
        self.registered = []
        self.errors = []
        self.existing_submission_id = None
        self.sharing_calls = []
        self.delete_calls = []
        self.reprocess_calls = []
        self.default_calls = []
        self.public_lecture = Lecture(
            lecture_processing_id=20,
            public_id="public-id",
            submission_id=10,
            lecture_title="Loeng 1",
            echo_canonical_section_id="22222222-2222-2222-2222-222222222222",
            course_title="Testkursus",
            echo_lesson_id="33333333-3333-3333-3333-333333333333",
            lecture_start_at=None,
            duration_seconds=None,
            recording_status="available",
            created=None,
            default_slides_operation_id=None,
            operations=[
                Operation(40, "asr", 1, 100, local_outcome="SUCCEEDED"),
                Operation(41, "slides", 1, 101, slide_sensitivity_level=0, local_outcome="SUCCEEDED"),
            ],
        )
        self.course = SimpleNamespace(
            echo_canonical_section_id="22222222-2222-2222-2222-222222222222",
            echo_public_url=RESOLVER["input_public_url"],
        )

    def find_submission(self, user_id, public_id):
        self.find_submission_call = (user_id, public_id)
        return self.existing_submission_id

    @contextmanager
    def transaction(self):
        yield self.tx

    def set_operation_registered(self, operation_id, job_id):
        self.registered.append((operation_id, job_id))

    def set_registration_error(self, operation_id, code, message):
        self.errors.append((operation_id, code, message))

    def get_lecture(self, lecture_id):
        if lecture_id != 20:
            raise KeyError(lecture_id)
        return self.public_lecture

    def get_public_lecture(self, public_id):
        if public_id != "public-id":
            raise KeyError(public_id)
        return self.public_lecture

    def get_course(self, canonical_section_id):
        if canonical_section_id != self.course.echo_canonical_section_id:
            raise KeyError(canonical_section_id)
        return self.course

    def set_public_sharing(self, lecture_id, enabled):
        self.sharing_calls.append((lecture_id, enabled))
        return "public-id" if enabled else None

    def soft_delete_lecture(self, lecture_id):
        self.delete_calls.append(lecture_id)

    def create_slide_reprocessing(self, lecture_id, sensitivity_level):
        self.reprocess_calls.append((lecture_id, sensitivity_level))
        return 42, "key-slides-2", 100

    def set_default_slides_operation(self, lecture_id, operation_id):
        self.default_calls.append((lecture_id, operation_id))


class FakeOrds:
    def __init__(self, fail_asr=False) -> None:
        self.fail_asr = fail_asr
        self.calls = []

    def register_job(self, **values):
        self.calls.append(values)
        if self.fail_asr and values["operation_type"] == "asr":
            raise OrdsError("TEST", "asr failed")
        return {"job_id": 100 if values["operation_type"] == "asr" else 101}


class LectureServiceTests(unittest.TestCase):
    def service(self, root: Path, *, fail_asr: bool = False):
        repository = FakeRepository()
        ords = FakeOrds(fail_asr)
        service = LectureService(repository, ords, root, FileStorage(root))
        service.resolve = lambda url: RESOLVER
        return service, repository, ords

    def test_submission_stores_upload_and_registers_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            service, repository, ords = self.service(Path(directory))
            submission_id = service.create_submission(
                user_id=7,
                submission_request_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                public_url=RESOLVER["input_public_url"],
                selected_lesson_ids=["33333333-3333-3333-3333-333333333333"],
                uploads=[
                    UploadInput(
                        lesson_id="33333333-3333-3333-3333-333333333333",
                        filename="slides.pptx",
                        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        stream=io.BytesIO(b"slide data"),
                    )
                ],
            )

            self.assertEqual(submission_id, 10)
            self.assertEqual(repository.tx.operations, [(20, "asr", None, None), (20, "slides", 40, 0)])
            self.assertEqual(repository.registered, [(40, 100), (41, 101)])
            self.assertEqual(ords.calls[1]["previous_job_id"], 100)
            stored = repository.tx.uploads[0][1]
            self.assertEqual(stored.sha256, "61085577d24c91de3d8b696fefde88e25e80a548875027de4df4c7bff4f79926")
            self.assertEqual(service.storage.read_bytes(stored.relative_path), b"slide data")

    def test_slides_are_not_registered_when_asr_registration_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            service, repository, ords = self.service(Path(directory), fail_asr=True)
            service.create_submission(
                user_id=7,
                submission_request_id="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                public_url=RESOLVER["input_public_url"],
                selected_lesson_ids=["33333333-3333-3333-3333-333333333333"],
                uploads=[],
            )
            self.assertEqual(len(ords.calls), 1)
            self.assertEqual(repository.errors[0][:2], (40, "TEST"))
            self.assertEqual(repository.errors[1][:2], (41, "PREVIOUS_JOB_NOT_REGISTERED"))

    def test_unavailable_lecture_cannot_be_submitted(self):
        with tempfile.TemporaryDirectory() as directory:
            service, _, _ = self.service(Path(directory))
            with self.assertRaises(ValidationError):
                service.create_submission(
                    user_id=7,
                    submission_request_id="cccccccc-cccc-4ccc-8ccc-cccccccccccc",
                    public_url=RESOLVER["input_public_url"],
                    selected_lesson_ids=["44444444-4444-4444-4444-444444444444"],
                    uploads=[],
                )

    def test_repeated_submission_request_returns_existing_submission_without_new_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            service, repository, ords = self.service(Path(directory))
            repository.existing_submission_id = 77

            submission_id = service.create_submission(
                user_id=7,
                submission_request_id="dddddddd-dddd-4ddd-8ddd-dddddddddddd",
                public_url=RESOLVER["input_public_url"],
                selected_lesson_ids=["33333333-3333-3333-3333-333333333333"],
                uploads=[],
            )

            self.assertEqual(submission_id, 77)
            self.assertEqual(repository.tx.operations, [])
            self.assertEqual(ords.calls, [])

    def test_combined_markdown_is_preferred(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)
            transcript = root / "outputs/jobs/20/transcript/taltechnlp-turbo-et-verbatim-2604-int8/transcript.md"
            combined = root / "outputs/jobs/20/slides/41/transcript_with_slides.md"
            transcript.parent.mkdir(parents=True)
            combined.parent.mkdir(parents=True)
            transcript.write_text("transcript", encoding="utf-8")
            combined.write_text("combined", encoding="utf-8")
            self.assertEqual(service.result_path(repository.public_lecture), combined.relative_to(root))

    def test_public_sharing_requires_transcript_with_slides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)

            with self.assertRaisesRegex(ValidationError, "transcript with slides is not ready"):
                service.set_public_sharing(20, True)
            self.assertEqual(repository.sharing_calls, [])

            combined = root / "outputs/jobs/20/slides/41/transcript_with_slides.md"
            combined.parent.mkdir(parents=True)
            combined.write_text("combined", encoding="utf-8")
            self.assertEqual(service.set_public_sharing(20, True), "public-id")
            self.assertEqual(repository.sharing_calls, [(20, True)])

    def test_public_download_never_falls_back_to_raw_transcript(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)
            transcript = root / "outputs/jobs/20/transcript/taltechnlp-turbo-et-verbatim-2604-int8/transcript.md"
            transcript.parent.mkdir(parents=True)
            transcript.write_text("raw transcript", encoding="utf-8")

            with self.assertRaises(KeyError):
                service.public_result("public-id")

            combined = root / "outputs/jobs/20/slides/41/transcript_with_slides.md"
            combined.parent.mkdir(parents=True)
            combined.write_text("combined", encoding="utf-8")
            _, path = service.public_result("public-id")
            self.assertEqual(path, combined.relative_to(root))

    def test_download_archive_contains_named_markdown_and_referenced_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, _, _ = self.service(root)
            combined = root / "outputs/jobs/20/slides/41/transcript_with_slides.md"
            image = root / "outputs/jobs/20/slides/41/images/slide_001.png"
            combined.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            combined.write_text("![Slaid](images/slide_001.png)\n", encoding="utf-8")
            image.write_bytes(b"slide")

            archive_result = service.download_archive(20)
            with zipfile.ZipFile(io.BytesIO(b"".join(archive_result.body))) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [
                        "Loeng 1/",
                        "Loeng 1/Loeng 1.md",
                        "Loeng 1/images/",
                        "Loeng 1/images/slide_001.png",
                    ],
                )
                self.assertEqual(archive.read("Loeng 1/Loeng 1.md"), combined.read_bytes())
                self.assertEqual(archive.read("Loeng 1/images/slide_001.png"), b"slide")

            combined.write_text("![Puuduv](images/missing.png)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "Missing referenced slide image"):
                service.download_archive(20)

    def test_original_transcript_download_has_no_images_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, _, _ = self.service(root)
            transcript = root / "outputs/jobs/20/transcript/taltechnlp-turbo-et-verbatim-2604-int8/transcript.md"
            transcript.parent.mkdir(parents=True)
            transcript.write_text("algne transkript\n", encoding="utf-8")

            archive_result = service.download_archive(20, 0)
            with zipfile.ZipFile(io.BytesIO(b"".join(archive_result.body))) as archive:
                self.assertEqual(archive.namelist(), ["Loeng 1/", "Loeng 1/Loeng 1.md"])
                self.assertEqual(archive.read("Loeng 1/Loeng 1.md"), b"algne transkript\n")

    def test_slide_image_path_accepts_only_existing_image_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)
            image = root / "outputs/jobs/20/slides/41/images/slide_001.png"
            image.parent.mkdir(parents=True)
            (image.parent.parent / "transcript_with_slides.md").write_text("combined", encoding="utf-8")
            image.write_bytes(b"png")
            self.assertEqual(service.slide_image_path(repository.public_lecture, "slide_001.png"), image.relative_to(root))
            self.assertIsNone(service.slide_image_path(repository.public_lecture, "../slide_001.png"))
            self.assertIsNone(service.slide_image_path(repository.public_lecture, "slide_001.svg"))

    def test_reprocess_registers_only_new_dependent_slides_job(self):
        with tempfile.TemporaryDirectory() as directory:
            service, repository, ords = self.service(Path(directory))
            service.reprocess_slides(20, 2)
            self.assertEqual(repository.reprocess_calls, [(20, 2)])
            self.assertEqual(ords.calls[0]["operation_type"], "slides")
            self.assertEqual(ords.calls[0]["previous_job_id"], 100)

    def test_default_slide_version_must_be_available(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)
            path = root / "outputs/jobs/20/slides/41/transcript_with_slides.md"
            path.parent.mkdir(parents=True)
            path.write_text("combined", encoding="utf-8")
            service.set_default_slide_version(20, 41)
            self.assertEqual(repository.default_calls, [(20, 41)])

    def test_slide_versions_are_in_ascending_attempt_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)
            repository.public_lecture.operations.append(
                Operation(42, "slides", 2, 102, slide_sensitivity_level=2, local_outcome="SUCCEEDED")
            )
            for operation_id in (41, 42):
                path = root / f"outputs/jobs/20/slides/{operation_id}/transcript_with_slides.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("combined", encoding="utf-8")

            self.assertEqual(
                [version.attempt_number for version in service.slide_versions(repository.public_lecture)],
                [1, 2],
            )

    def test_latest_slide_version_is_selected_when_default_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service, repository, _ = self.service(root)
            repository.public_lecture.operations.append(
                Operation(42, "slides", 2, 102, slide_sensitivity_level=2, local_outcome="SUCCEEDED")
            )
            for operation_id in (41, 42):
                path = root / f"outputs/jobs/20/slides/{operation_id}/transcript_with_slides.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("combined", encoding="utf-8")

            self.assertEqual(service.selected_slide_version(repository.public_lecture).operation_id, 42)


    def test_soft_delete_targets_requested_lecture(self):
        with tempfile.TemporaryDirectory() as directory:
            service, repository, _ = self.service(Path(directory))
            service.soft_delete_lecture(20)
            self.assertEqual(repository.delete_calls, [20])

    def test_video_stream_uses_echo_range_response_without_storing_file(self):
        class FakeResponse(io.BytesIO):
            status = 206
            headers = {
                "Content-Type": "video/mp4",
                "Content-Length": "6",
                "Content-Range": "bytes 10-15/100",
            }

            def getcode(self):
                return self.status

        class FakeEcho:
            def __init__(self):
                self.public_urls = []
                self.range_headers = []

            def open_public_session(self, public_url):
                self.public_urls.append(public_url)

            def get_lesson_media(self, lesson_id):
                self.lesson_id = lesson_id
                return {
                    "video": {
                        "media": {
                            "media": {
                                "current": {
                                    "primaryFiles": [
                                        {
                                            "s3Url": "https://content.echo360.org.uk/video.mp4",
                                            "size": 100,
                                            "width": 640,
                                            "height": 360,
                                        }
                                    ],
                                    "secondaryFiles": [
                                        {
                                            "s3Url": "https://content.echo360.org.uk/camera.mp4",
                                            "size": 120,
                                            "width": 640,
                                            "height": 360,
                                        }
                                    ],
                                }
                            }
                        }
                    }
                }

            def open_media_stream(self, source_url, range_header):
                self.source_url = source_url
                self.range_headers.append(range_header)
                return FakeResponse(b"abcdef")

        with tempfile.TemporaryDirectory() as directory:
            service, repository, _ = self.service(Path(directory))
            echo = FakeEcho()
            service.echo_factory = lambda: echo

            stream = service.video_stream(20, "bytes=10-15")

            self.assertEqual(stream.status_code, 206)
            self.assertEqual(stream.content_type, "video/mp4")
            self.assertEqual(stream.headers["Content-Range"], "bytes 10-15/100")
            self.assertEqual(b"".join(stream.body), b"abcdef")
            self.assertEqual(echo.public_urls, [RESOLVER["input_public_url"]])
            self.assertEqual(echo.range_headers, ["bytes=10-15"])
            self.assertEqual(list(Path(directory).rglob("*")), [])

            secondary = service.video_stream(20, "bytes=20-25", "secondary")
            self.assertEqual(b"".join(secondary.body), b"abcdef")
            self.assertEqual(echo.source_url, "https://content.echo360.org.uk/camera.mp4")
            self.assertEqual(echo.range_headers, ["bytes=10-15", "bytes=20-25"])

            with self.assertRaisesRegex(ValidationError, "Invalid video byte range"):
                service.video_stream(20, "bytes=0-1,10-11")
            with self.assertRaisesRegex(ValidationError, "Invalid video track"):
                service.video_stream(20, None, "tertiary")


if __name__ == "__main__":
    unittest.main()
