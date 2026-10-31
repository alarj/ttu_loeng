from __future__ import annotations

import unittest

from lecture_notes.asr_benchmark import _edit_distance, _format_hms, _quality_metrics, build_parser
from lecture_notes.stage3 import extract_syllabus_item, select_video_source, validate_generated_notes


class AsrMetricTests(unittest.TestCase):
    def test_edit_distance(self) -> None:
        self.assertEqual(_edit_distance("üks kaks kolm".split(), "üks kolm".split()), 1)

    def test_quality_metrics_require_reference(self) -> None:
        result = _quality_metrics(None, "RTO ja RPO", ["rto", "mtd"])
        self.assertFalse(result["reference_available"])
        self.assertIsNone(result["wer"])
        self.assertEqual(result["expected_terms"], {"rto": True, "mtd": False})

    def test_quality_metrics_normalize_punctuation_and_case(self) -> None:
        result = _quality_metrics("Tere, maailm!", "tere maailm", [])
        self.assertEqual(result["wer"], 0.0)
        self.assertEqual(result["cer"], 0.0)

    def test_full_transcript_timestamp_format(self) -> None:
        self.assertEqual(_format_hms(0), "00:00:00")
        self.assertEqual(_format_hms(7199.98), "01:59:59")

    def test_full_transcript_command_parses(self) -> None:
        args = build_parser().parse_args(
            [
                "transcribe-full",
                "https://echo360.org.uk/section/00000000-0000-0000-0000-000000000000/public",
                "--lesson-id",
                "lesson-1",
                "--output-dir",
                "/runtime/outputs/job",
                "--model",
                "model-id",
                "--revision",
                "revision-id",
                "--configuration-id",
                "config-id",
            ]
        )
        self.assertEqual(args.command, "transcribe-full")


class Stage3SourceTests(unittest.TestCase):
    def test_select_video_source_prefers_smallest_resolution(self) -> None:
        payload = {
            "video": {
                "media": {
                    "media": {
                        "current": {
                            "primaryFiles": [
                                {"s3Url": "https://content.echo360.org.uk/hd.mp4", "size": 300, "width": 1920, "height": 1080},
                                {"s3Url": "https://content.echo360.org.uk/sd.mp4", "size": 100, "width": 640, "height": 360},
                            ]
                        }
                    }
                }
            }
        }
        self.assertEqual(
            select_video_source(payload),
            ("https://content.echo360.org.uk/sd.mp4", 100, 640, 360),
        )

    def test_extract_syllabus_item_stops_at_next_item(self) -> None:
        text = "3.d. Eelmine punkt.\n3.e. Põhitekst.\no Täpsustus.\nNädal 4 - järgmine teema"
        self.assertEqual(extract_syllabus_item(text, "3.e"), "3.e. Põhitekst. o Täpsustus.")

    def test_generated_notes_validation_requires_known_evidence_and_slide(self) -> None:
        evidence = {
            "evidence": [{"id": "evidence_001"}],
            "slides": {"items": [{"path": "/runtime/slide.jpg", "markdown_path": "../../slide.jpg"}]},
            "coverage": {"missing_aspects": ["kriisisuhtluse meetmed"]},
        }
        passed = validate_generated_notes(
            "# 1. Dokumendi päritolu\nAI mustand.\n## 2. Sisukord\n- Sisu\n## 3. Sisu\n"
            "Tekst [evidence_001]\n![](../../slide.jpg)\nPuuduvad kriisisuhtluse meetmed.",
            evidence,
        )
        self.assertEqual(passed["status"], "passed")
        needs_review = validate_generated_notes("Tekst [evidence_unknown]", evidence)
        self.assertEqual(needs_review["status"], "needs_review")
        self.assertEqual(needs_review["missing_evidence_ids"], ["evidence_001"])


if __name__ == "__main__":
    unittest.main()
