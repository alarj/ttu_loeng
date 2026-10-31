from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from lecture_notes.cli import _verify_audio
from lecture_notes.config import Settings, ensure_runtime_output
from lecture_notes.echo360 import derive_recording_status, derive_time_status, normalize_lesson


NOW = datetime(2026, 10, 30, 9, 0, tzinfo=timezone.utc)


class EchoStatusTests(unittest.TestCase):
    def test_available_media_wins_over_inconsistent_future_flag(self) -> None:
        wrapper = {
            "lesson": {"id": "lesson-1", "name": "Käsitsi avaldatud loeng"},
            "startTimeUTC": "2026-09-12T06:00:00.000Z",
            "endTimeUTC": "2026-09-12T07:00:00.000Z",
            "isPast": False,
            "isFuture": True,
            "isLive": False,
            "isScheduled": False,
            "hasContent": True,
            "hasVideo": True,
            "hasSlideDeck": False,
            "medias": [
                {
                    "id": "media-1",
                    "mediaType": "Video",
                    "isAvailable": True,
                    "isProcessing": False,
                    "isFailed": False,
                }
            ],
        }
        result = normalize_lesson(wrapper, NOW)
        self.assertEqual(result["derived_time_status"], "past")
        self.assertEqual(result["recording_status"], "available")
        self.assertEqual([item["code"] for item in result["warnings"]], ["ECHO_TIME_STATUS_CONFLICT"])

    def test_scheduled_row_without_media_is_not_available(self) -> None:
        wrapper = {
            "lesson": {"id": "lesson-2", "name": "Tulevane loeng"},
            "startTimeUTC": "2026-11-06T15:45:00.000Z",
            "endTimeUTC": "2026-11-06T19:05:00.000Z",
            "isPast": False,
            "isFuture": True,
            "isLive": False,
            "isScheduled": True,
            "hasContent": False,
            "hasVideo": True,
            "hasSlideDeck": False,
            "medias": [],
        }
        result = normalize_lesson(wrapper, NOW)
        self.assertEqual(result["derived_time_status"], "future")
        self.assertEqual(result["recording_status"], "not_available")
        self.assertEqual(result["warnings"], [])

    def test_recording_state_precedence(self) -> None:
        self.assertEqual(derive_recording_status([{"media_type": "Video", "is_processing": True}]), "processing")
        self.assertEqual(derive_recording_status([{"media_type": "Video", "is_failed": True}]), "failed")
        self.assertEqual(derive_recording_status([]), "not_available")

    def test_content_without_media_is_not_automatically_a_conflict(self) -> None:
        wrapper = {
            "lesson": {"id": "lesson-3", "name": "Slaididega loeng"},
            "hasContent": True,
            "hasVideo": False,
            "hasSlideDeck": True,
            "medias": [],
        }
        result = normalize_lesson(wrapper, NOW)
        self.assertEqual(result["content_status"], "present")
        self.assertEqual(result["recording_status"], "not_available")
        self.assertEqual(result["warnings"], [])

    def test_time_status_boundaries(self) -> None:
        self.assertEqual(
            derive_time_status(
                datetime(2026, 10, 30, 8, 0, tzinfo=timezone.utc),
                datetime(2026, 10, 30, 10, 0, tzinfo=timezone.utc),
                NOW,
            ),
            "current",
        )


class RuntimePathTests(unittest.TestCase):
    def test_output_must_be_in_runtime_and_outside_repo(self) -> None:
        with TemporaryDirectory() as root:
            base = Path(root)
            config = Settings(repo_root=base / "repo", runtime_root=base / "runtime")
            self.assertEqual(
                ensure_runtime_output(base / "runtime" / "outputs" / "job", config),
                (base / "runtime" / "outputs" / "job").resolve(),
            )
            with self.assertRaises(ValueError):
                ensure_runtime_output(base / "repo" / "runtime", config)
            with self.assertRaises(ValueError):
                ensure_runtime_output(base / "elsewhere", config)


class AudioLifecycleTests(unittest.TestCase):
    class FakeClient:
        def download_media(self, source_url: str, target: Path) -> dict[str, object]:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"test-audio")
            return {
                "path": str(target),
                "size_bytes": 10,
                "sha256": "test-sha256",
                "content_type": "audio/mpeg",
                "source_host": "content.echo360.org.uk",
                "source_path": "/test/audio.mp3",
                "source_query_persisted": False,
            }

    @staticmethod
    def media_payload() -> dict[str, object]:
        return {
            "video": {
                "media": {
                    "media": {
                        "current": {
                            "audioFiles": [
                                {
                                    "s3Url": "https://content.echo360.org.uk/test/audio.mp3",
                                    "size": 10,
                                }
                            ]
                        }
                    }
                }
            }
        }

    def test_audio_is_removed_after_verification_by_default(self) -> None:
        with TemporaryDirectory() as root:
            work_root = Path(root) / "work"
            manifest: dict[str, object] = {}
            _verify_audio(self.FakeClient(), self.media_payload(), manifest, "lesson-1", work_root, False)

            verification = manifest["audio_verification"]
            self.assertIsInstance(verification, dict)
            self.assertEqual(verification["cleanup_status"], "removed")
            self.assertFalse(verification["retained"])
            self.assertIsNone(verification["path"])
            self.assertFalse(any(path.is_file() for path in work_root.rglob("*")))

    def test_audio_can_be_retained_only_by_explicit_request(self) -> None:
        with TemporaryDirectory() as root:
            work_root = Path(root) / "work"
            manifest: dict[str, object] = {}
            _verify_audio(self.FakeClient(), self.media_payload(), manifest, "lesson-1", work_root, True)

            verification = manifest["audio_verification"]
            self.assertIsInstance(verification, dict)
            self.assertEqual(verification["cleanup_status"], "retained_by_request")
            self.assertTrue(verification["retained"])
            self.assertTrue(Path(verification["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
