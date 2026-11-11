from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from lecture_notes.web.app import _validate_google_profile, create_app
from lecture_notes.web.models import Course, Lecture, Operation, User
from lecture_notes.web.services import VideoStream
from lecture_notes.web.settings import WebSettings
from storage_test_utils import FileStorage


class FakeRepository:
    def __init__(self, role="USER"):
        self.sharing_calls = []
        self.delete_calls = []
        self.user = User(1, "user-public", "user@example.com", "Test User", role, True)
        self.course = Course(
            "course-section-id",
            "Testkursus",
            1,
            "https://echo360.org.uk/section/existing-course/public",
        )
        self.lecture = Lecture(
            lecture_processing_id=12,
            public_id="public-lecture-id",
            submission_id=3,
            echo_canonical_section_id="course-section-id",
            course_title="Testkursus",
            lecture_title="Testloeng",
            echo_lesson_id="lesson-id",
            lecture_start_at=datetime(2026, 9, 4, 14, 45),
            duration_seconds=3600,
            recording_status="available",
            created=datetime(2026, 11, 4, 12, 0),
            default_slides_operation_id=None,
            operations=[],
        )

    def get_or_create_google_user(self, subject, email, display_name):
        return self.user

    def get_user(self, user_id):
        if user_id != self.user.user_id:
            raise KeyError(user_id)
        return self.user

    def list_courses(self):
        return [self.course]

    def get_course(self, canonical_section_id):
        if canonical_section_id != self.course.echo_canonical_section_id:
            raise KeyError(canonical_section_id)
        return self.course

    def list_lectures(self, canonical_section_id=None):
        if canonical_section_id not in (None, self.course.echo_canonical_section_id):
            return []
        return [self.lecture]

    def active_echo_lesson_ids(self, canonical_section_id):
        if canonical_section_id != self.course.echo_canonical_section_id:
            return set()
        return {self.lecture.echo_lesson_id}

    def get_lecture(self, lecture_id):
        if lecture_id != 12:
            raise KeyError(lecture_id)
        return self.lecture

    def get_public_lecture(self, public_id):
        if public_id != self.lecture.public_id:
            raise KeyError(public_id)
        return self.lecture

    def find_submission(self, user_id, public_id):
        return None

    def set_public_sharing(self, lecture_id, enabled):
        if lecture_id != self.lecture.lecture_processing_id:
            raise KeyError(lecture_id)
        self.sharing_calls.append((lecture_id, enabled))
        self.lecture.public_id = "public-lecture-id" if enabled else None
        return self.lecture.public_id

    def soft_delete_lecture(self, lecture_id):
        if lecture_id != self.lecture.lecture_processing_id:
            raise KeyError(lecture_id)
        self.delete_calls.append(lecture_id)


class FakeOrds:
    def job_status(self, job_id):
        return {"status": "RUNNING" if job_id == 2 else "SUCCEEDED"}


class WebAppTests(unittest.TestCase):
    def make_client(self, root: Path, role="USER"):
        app = create_app(
            WebSettings(
                base_url="https://ttu-loeng.fun-o.eu",
                google_client_id="client",
                session_secret="unit-test-session-secret",
                runtime_root=root,
                ui_status_poll_interval_seconds=30,
            ),
            repository=FakeRepository(role),
            ords_client=FakeOrds(),
            storage=FileStorage(root),
        )
        return TestClient(app, base_url="https://ttu-loeng.fun-o.eu")

    def login(self, client):
        profile = {
            "aud": "client",
            "sub": "google-subject",
            "email": "user@example.com",
            "email_verified": "true",
            "name": "Test User",
        }
        with patch(
            "lecture_notes.web.app._verify_google_id_token",
            new=AsyncMock(return_value=profile),
        ):
            response = client.post("/api/auth/google", json={"id_token": "google-id-token"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})

    def test_google_config_exposes_only_public_client_id(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory)) as client:
                response = client.get("/api/auth/google/config")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"enabled": True, "client_id": "client"})

    def test_google_profile_must_match_client_and_verified_email(self):
        valid = {
            "aud": "client",
            "sub": "google-subject",
            "email": "user@example.com",
            "email_verified": "true",
        }
        self.assertEqual(_validate_google_profile(valid, "client"), valid)
        with self.assertRaises(HTTPException):
            _validate_google_profile({**valid, "aud": "other-client"}, "client")
        with self.assertRaises(HTTPException):
            _validate_google_profile({**valid, "email_verified": "false"}, "client")

    def test_expired_session_redirects_to_clean_login_page(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory)) as client:
                response = client.get("/lectures/12", follow_redirects=False)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["location"], "/")
                login = client.get("/")
                self.assertEqual(login.status_code, 200)
                self.assertIn('id="googleLoginMount"', login.text)
                self.assertNotIn("Palun logi sisse.", login.text)

    def test_anonymous_user_cannot_see_job_list_but_public_download_works(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "outputs/jobs/12/slides/2/transcript_with_slides.md"
            image = root / "outputs/jobs/12/slides/2/images/slide_001.png"
            output.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            output.write_text("![Slaid](images/slide_001.png)\n", encoding="utf-8")
            image.write_bytes(b"public-slide")
            with self.make_client(root) as client:
                client.app.state.repository.lecture.operations = [
                    Operation(2, "slides", 1, 2, slide_sensitivity_level=0, local_outcome="SUCCEEDED")
                ]
                index = client.get("/")
                self.assertIn("Logi Google", index.text)
                self.assertNotIn("Testloeng", index.text)
                download = client.get("/public/public-lecture-id/download")
                self.assertEqual(download.status_code, 200)
                self.assertEqual(download.headers["content-type"], "application/zip")
                self.assertIn("Testloeng.zip", download.headers["content-disposition"])
                with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                    self.assertEqual(
                        archive.namelist(),
                        [
                            "Testloeng/",
                            "Testloeng/Testloeng.md",
                            "Testloeng/images/",
                            "Testloeng/images/slide_001.png",
                        ],
                    )
                    self.assertEqual(
                        archive.read("Testloeng/Testloeng.md"),
                        b"![Slaid](images/slide_001.png)\n",
                    )
                    self.assertEqual(
                        archive.read("Testloeng/images/slide_001.png"),
                        b"public-slide",
                    )

    def test_user_sees_all_jobs_but_cannot_open_admin_form(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "outputs/jobs/12/transcript/taltechnlp-turbo-et-verbatim-2604-int8/transcript.md"
            output.parent.mkdir(parents=True)
            output.write_text("authenticated transcript", encoding="utf-8")
            with self.make_client(root, "USER") as client:
                self.login(client)
                index = client.get("/")
                self.assertIn("Testkursus", index.text)
                self.assertIn('data-auto-refresh="true"', index.text)
                self.assertIn(">Loengud</a>", index.text)
                self.assertIn("Kõik loengud ja nendes avaldatud materjalid kuuluvad Tallinna Tehnikaülikoolile ja / või loengu autorile.", index.text)
                self.assertIn("Loengute transkriptsioonid on loodud AI poolt TalTechNLP kõnetuvastusmudeliga loengusalvestiste heliribast.", index.text)
                self.assertNotIn("Testloeng", index.text)
                course = client.get("/courses/course-section-id")
                self.assertIn("Testloeng", course.text)
                self.assertIn('data-auto-refresh="true"', course.text)
                self.assertIn("<h2>Testkursus</h2>", course.text)
                self.assertIn("← Tagasi", course.text)
                self.assertIn('class="button-link secondary-button compact-view header-button" href="/"', course.text)
                self.assertIn(">TalTech<", course.text)
                self.assertIn('class="secondary-button compact-view header-button" type="submit"', course.text)
                self.assertIn('class="lecture-date" datetime="2026-09-04T14:45:00Z">(04.09.2026)</time>', course.text)
                self.assertNotIn("Kustuta", course.text)
                self.assertEqual(client.get("/submissions/new").status_code, 403)
                download = client.get("/lectures/12/download")
                self.assertEqual(download.status_code, 200)
                with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                    self.assertEqual(archive.namelist(), ["Testloeng/", "Testloeng/Testloeng.md"])
                    self.assertEqual(
                        archive.read("Testloeng/Testloeng.md"),
                        b"authenticated transcript",
                    )

    def test_admin_can_open_submission_form(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory), "ADMIN") as client:
                self.login(client)
                response = client.get("/submissions/new")
                self.assertEqual(response.status_code, 200)
                self.assertIn("Echo360 avalik kursuselink", response.text)
                self.assertIn("Olemasolev kursus", response.text)
                self.assertIn('<option value="course-section-id">Testkursus</option>', response.text)
                self.assertNotIn(">https://echo360.org.uk/section/existing-course/public</option>", response.text)
                self.assertEqual(response.text.count("data-resolve-button disabled"), 2)
                self.assertRegex(response.text, r"/static/app\.css\?v=[0-9a-f]{12}")
                self.assertRegex(response.text, r"/static/app\.js\?v=[0-9a-f]{12}")

    def test_existing_course_selection_resolves_its_stored_url(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory), "ADMIN") as client:
                self.login(client)
                form = client.get("/submissions/new")
                csrf = form.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]
                resolved_urls = []

                def resolve(url):
                    resolved_urls.append(url)
                    return {"lessons": []}

                client.app.state.service.resolve = resolve
                response = client.post(
                    "/submissions/resolve",
                    data={"csrf_token": csrf, "canonical_section_id": "course-section-id"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    resolved_urls,
                    ["https://echo360.org.uk/section/existing-course/public"],
                )

    def test_resolved_lecture_list_shows_date_and_compact_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory), "ADMIN") as client:
                self.login(client)
                form = client.get("/submissions/new")
                csrf = form.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]
                client.app.state.service.resolve = lambda _url: {
                    "canonical_section_id": "course-section-id",
                    "lessons": [
                        {
                            "lesson_id": "lesson-id",
                            "display_name": "Nimetu loeng",
                            "start_time_utc": "2026-09-04T14:45:00Z",
                            "recording_status": "available",
                        }
                    ]
                }
                response = client.post(
                    "/submissions/resolve",
                    data={
                        "csrf_token": csrf,
                        "public_url": "https://echo360.org.uk/section/test/public",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("Nimetu loeng", response.text)
                self.assertNotIn("Toimumisaeg", response.text)
                self.assertIn('datetime="2026-09-04T14:45:00Z"', response.text)
                self.assertIn("submission-card lecture-selection-card", response.text)
                self.assertIn("lecture-choice-name", response.text)
                self.assertIn("Lisa slaidid", response.text)
                self.assertIn("slide-upload-button", response.text)
                self.assertIn("Juba lisatud", response.text)
                self.assertIn('id="submissionProgress"', response.text)
                self.assertIn('name="submission_request_id" value="', response.text)
                self.assertIn("Loenguid lisatakse ja taustatöid registreeritakse. Palun oota.", response.text)

    def test_lecture_detail_has_modal_slides_compact_actions_and_course_back_button(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "outputs/jobs/12/slides/2/transcript_with_slides.md"
            image = root / "outputs/jobs/12/slides/2/images/slide_001.png"
            output.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            output.write_text(
                "# Transkript\n\n![Slaid 1](images/slide_001.png)\n\n"
                "[00:00:27–00:00:30] Testlause.\n",
                encoding="utf-8",
            )
            image.write_bytes(b"slide-image")
            with self.make_client(root, "ADMIN") as client:
                client.app.state.repository.lecture.operations = [
                    Operation(
                        operation_id=1,
                        operation_type="asr",
                        attempt_number=1,
                        ords_job_id=1,
                        local_outcome="SUCCEEDED",
                        local_started_at=datetime(2026, 11, 5, 6, 12, 23),
                        local_completed_at=datetime(2026, 11, 5, 8, 3, 0),
                    ),
                    Operation(
                        operation_id=2,
                        operation_type="slides",
                        attempt_number=1,
                        ords_job_id=2,
                        slide_sensitivity_level=0,
                        local_outcome="SUCCEEDED",
                        local_started_at=datetime(2026, 11, 5, 8, 4, 0),
                    ),
                ]
                client.app.state.repository.lecture.default_slides_operation_id = 2
                self.login(client)
                response = client.get("/lectures/12")
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('data-auto-refresh="true"', response.text)
                self.assertIn('id="globalLoadingIndicator"', response.text)
                self.assertIn("Laadin andmeid…", response.text)
                self.assertIn('<dialog id="transcriptViewer"', response.text)
                self.assertIn('data-primary-video-url="/lectures/12/video?track=primary"', response.text)
                self.assertIn('data-secondary-video-url="/lectures/12/video?track=secondary"', response.text)
                self.assertIn('id="transcriptVideoContainer"', response.text)
                self.assertIn('id="transcriptVideo"', response.text)
                self.assertIn('id="transcriptSecondaryVideo"', response.text)
                self.assertIn('id="followTranscript"', response.text)
                self.assertIn("Jälgi teksti", response.text)
                self.assertIn('href="#video-at-27">00:00:27–00:00:30</a>', response.text)
                self.assertIn("<h1>Transkript</h1>", response.text)
                self.assertIn('src="/lectures/12/slides/2/slide_001.png"', response.text)
                self.assertIn('id="openReprocessSlidesDialog"', response.text)
                self.assertIn('id="slideVersionSelect"', response.text)
                self.assertIn("Versioon 1 — default", response.text)
                self.assertNotIn("Versioon 1 (vaikimisi)", response.text)
                self.assertIn('id="openDefaultSlideVersionDialog"', response.text)
                self.assertIn('href="/courses/course-section-id"', response.text)
                self.assertIn('id="openOriginalVideoDialog"', response.text)
                self.assertIn('id="originalVideoDialog"', response.text)
                self.assertIn('data-video-url="/lectures/12/video"', response.text)
                self.assertIn('id="originalLectureVideo"', response.text)
                self.assertIn('href="https://echo360.org.uk/lesson/lesson-id/classroom" target="_blank"', response.text)
                self.assertIn("Echo360 leht avaneb, kui brauseris on juba kehtiv Echo360 sessioon.", response.text)
                self.assertIn('aria-label="Laadi transkript ja slaidid ZIP-failina alla"', response.text)
                self.assertNotIn("Echo lesson ID", response.text)
                self.assertIn('datetime="2026-09-04T14:45:00Z"', response.text)
                self.assertNotIn('datetime="2026-11-04T12:00:00Z"', response.text)
                self.assertNotIn("Rakenduse tulemus", response.text)
                self.assertIn('class="browser-date-time" datetime="2026-11-05T06:12:23Z"', response.text)
                self.assertIn('class="browser-date-time" datetime="2026-11-05T08:03:00Z"', response.text)
                self.assertIn('class="status-badge compact-status status-running">RUNNING</span>', response.text)
                slide = client.get("/lectures/12/slides/2/slide_001.png")
                self.assertEqual(slide.status_code, 200)
                self.assertEqual(slide.content, b"slide-image")
                download = client.get("/lectures/12/download")
                self.assertEqual(download.status_code, 200)
                with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                    self.assertEqual(
                        archive.read("Testloeng/Testloeng.md"),
                        output.read_bytes(),
                    )
                    self.assertEqual(
                        archive.read("Testloeng/images/slide_001.png"),
                        b"slide-image",
                    )

    def test_original_transcript_is_selectable_and_downloaded_without_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "outputs/jobs/12/transcript/taltechnlp-turbo-et-verbatim-2604-int8/transcript.md"
            combined = root / "outputs/jobs/12/slides/2/transcript_with_slides.md"
            raw.parent.mkdir(parents=True)
            combined.parent.mkdir(parents=True)
            raw.write_text("# Algne\n\nIlma slaidideta.\n", encoding="utf-8")
            combined.write_text("# Slaididega\n", encoding="utf-8")
            with self.make_client(root, "USER") as client:
                client.app.state.repository.lecture.operations = [
                    Operation(2, "slides", 1, 2, slide_sensitivity_level=0, local_outcome="SUCCEEDED")
                ]
                self.login(client)
                detail = client.get("/lectures/12")
                self.assertIn('value="0">Algne transkript (ilma slaidideta)</option>', detail.text)

                version = client.get("/lectures/12/versions/0")
                self.assertEqual(version.status_code, 200)
                self.assertTrue(version.json()["is_original"])
                self.assertEqual(version.json()["download_url"], "/lectures/12/download?version=0")
                self.assertIn("Ilma slaidideta.", version.json()["html"])

                download = client.get("/lectures/12/download?version=0")
                self.assertEqual(download.status_code, 200)
                with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                    self.assertEqual(archive.namelist(), ["Testloeng/", "Testloeng/Testloeng.md"])
                    self.assertEqual(archive.read("Testloeng/Testloeng.md"), raw.read_bytes())

    def test_video_endpoint_forwards_requested_byte_range_as_stream(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory), "USER") as client:
                self.login(client)
                calls = []

                def video_stream(lecture_id, range_header, track):
                    calls.append((lecture_id, range_header, track))
                    return VideoStream(
                        status_code=206,
                        content_type="video/mp4",
                        headers={
                            "Accept-Ranges": "bytes",
                            "Content-Length": "3",
                            "Content-Range": "bytes 27-29/100",
                            "Cache-Control": "private, no-store",
                        },
                        body=iter([b"abc"]),
                    )

                client.app.state.service.video_stream = video_stream
                response = client.get(
                    "/lectures/12/video?track=secondary",
                    headers={"Range": "bytes=27-29"},
                )
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response.content, b"abc")
                self.assertEqual(response.headers["content-type"], "video/mp4")
                self.assertEqual(response.headers["content-range"], "bytes 27-29/100")
                self.assertEqual(response.headers["accept-ranges"], "bytes")
                self.assertEqual(calls, [(12, "bytes=27-29", "secondary")])

    def test_sharing_is_hidden_and_cannot_be_enabled_before_combined_result_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.make_client(root, "ADMIN") as client:
                client.app.state.repository.lecture.public_id = None
                self.login(client)

                detail = client.get("/lectures/12")
                self.assertEqual(detail.status_code, 200)
                self.assertNotIn("Avalik otselink", detail.text)
                csrf = detail.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]
                response = client.post(
                    "/lectures/12/sharing",
                    data={"csrf_token": csrf, "enabled": "1"},
                    follow_redirects=False,
                )
                self.assertEqual(response.status_code, 409)
                self.assertEqual(client.app.state.repository.sharing_calls, [])

                client.app.state.repository.lecture.operations = [
                    Operation(2, "slides", 1, 2, slide_sensitivity_level=0, local_outcome="SUCCEEDED")
                ]
                combined = root / "outputs/jobs/12/slides/2/transcript_with_slides.md"
                combined.parent.mkdir(parents=True)
                combined.write_text("combined", encoding="utf-8")
                ready_detail = client.get("/lectures/12")
                self.assertIn("Avalik otselink", ready_detail.text)
                ready_csrf = ready_detail.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]
                enabled = client.post(
                    "/lectures/12/sharing",
                    data={"csrf_token": ready_csrf, "enabled": "1"},
                    follow_redirects=False,
                )
                self.assertEqual(enabled.status_code, 303)
                self.assertEqual(client.app.state.repository.sharing_calls, [(12, True)])

    def test_admin_soft_deletes_only_selected_lecture(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory), "ADMIN") as client:
                self.login(client)
                course = client.get("/courses/course-section-id")
                self.assertNotIn('action="/lectures/12/delete"', course.text)
                self.assertNotIn("Kustuta", course.text)

                detail = client.get("/lectures/12")
                self.assertIn('id="openDeleteLectureDialog"', detail.text)
                self.assertIn('id="deleteLectureDialog"', detail.text)
                self.assertIn('action="/lectures/12/delete"', detail.text)
                self.assertIn("Soovid kustutada loengu „Testloeng“?", detail.text)
                self.assertIn('id="cancelDeleteLecture"', detail.text)
                self.assertIn('name="confirmed" value="1"', detail.text)
                csrf = detail.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]

                unconfirmed = client.post(
                    "/lectures/12/delete",
                    data={"csrf_token": csrf},
                )
                self.assertEqual(unconfirmed.status_code, 400)
                self.assertEqual(client.app.state.repository.delete_calls, [])

                response = client.post(
                    "/lectures/12/delete",
                    data={"csrf_token": csrf, "confirmed": "1"},
                    follow_redirects=False,
                )
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["location"], "/courses/course-section-id")
                self.assertEqual(client.app.state.repository.delete_calls, [12])

    def test_regular_user_cannot_delete_lecture(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.make_client(Path(directory), "USER") as client:
                self.login(client)
                course = client.get("/courses/course-section-id")
                csrf = course.text.split('name="csrf_token" value="', 1)[1].split('"', 1)[0]
                detail = client.get("/lectures/12")
                self.assertNotIn('id="openDeleteLectureDialog"', detail.text)
                self.assertNotIn('id="deleteLectureDialog"', detail.text)
                response = client.post(
                    "/lectures/12/delete",
                    data={"csrf_token": csrf, "confirmed": "1"},
                )
                self.assertEqual(response.status_code, 403)
                self.assertEqual(client.app.state.repository.delete_calls, [])


if __name__ == "__main__":
    unittest.main()
