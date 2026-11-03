from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from lecture_notes.asr_benchmark import (
    _edit_distance,
    _format_hms,
    _load_hotwords,
    _quality_metrics,
    build_parser,
)
from lecture_notes.slides import (
    _annotate_candidate_reference_hints,
    _build_slide_identities,
    _render_transcript_with_slides,
    build_parser as build_slide_parser,
    image_distance,
    normalize_text,
    restore_metadata_acronyms,
    select_video_source,
    select_video_source_by_quality,
    text_similarity,
    token_similarity,
)


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
                "--hotwords-file",
                "/app/hotwords/icm0032/l08-1.txt",
            ]
        )
        self.assertEqual(args.command, "transcribe-full")
        self.assertEqual(args.hotwords_file, Path("/app/hotwords/icm0032/l08-1.txt"))

    def test_hotwords_file_ignores_comments_blanks_and_duplicates(self) -> None:
        with TemporaryDirectory() as directory:
            source = Path(directory) / "hotwords.txt"
            source.write_text("# kommentaar\n\nCOBIT\ncobit\nLLM\n", encoding="utf-8")
            entries, metadata = _load_hotwords(source)
        self.assertEqual(entries, ["COBIT", "LLM"])
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["entry_count"], 2)

class SlideSourceTests(unittest.TestCase):
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

    def test_select_video_source_can_prefer_highest_resolution(self) -> None:
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
            select_video_source_by_quality(payload, prefer_highest=True),
            ("https://content.echo360.org.uk/hd.mp4", 300, 1920, 1080),
        )

    def test_slide_text_normalization_and_similarity(self) -> None:
        self.assertEqual(normalize_text("  Äri-juhtimine!  "), "ari juhtimine")
        self.assertGreater(text_similarity("COBIT Governance System", "COBIT governance system"), 0.99)
        self.assertEqual(token_similarity("AI and COBIT", "COBIT and governance"), 0.5)
        self.assertEqual(
            restore_metadata_acronyms("From IT Governance to Al Governance", "AI in COBIT 2019"),
            "From IT Governance to AI Governance",
        )

    def test_image_distance(self) -> None:
        self.assertEqual(image_distance((0, 10, 20), (0, 10, 20)), 0.0)
        self.assertAlmostEqual(image_distance((0, 0), (255, 255)), 1.0)

    def test_slide_process_command_parses(self) -> None:
        args = build_slide_parser().parse_args(
            [
                "process",
                "https://echo360.org.uk/section/00000000-0000-0000-0000-000000000000/public",
                "--lesson-id",
                "lesson-1",
                "--transcript",
                "/runtime/transcript.json",
                "--output-dir",
                "/runtime/slides",
            ]
        )
        self.assertEqual(args.command, "process")
        self.assertEqual(args.coarse_seconds, 20.0)
        self.assertEqual(args.refine_seconds, 2.0)

    def test_animation_states_with_same_reference_hint_form_one_slide(self) -> None:
        candidates = [
            {
                "timestamp_seconds": 378.0,
                "path": "partial.jpg",
                "signature": (0, 0, 0, 0),
                "ocr_text": "COBIT Objectives Most Relevant to AI",
                "title": "COBIT Objectives Most Relevant to AI",
                "reference_hint": 4,
                "reference_hint_score": 0.75,
            },
            {
                "timestamp_seconds": 438.0,
                "path": "complete.jpg",
                "signature": (60, 60, 60, 60),
                "ocr_text": "COBIT Objectives Most Relevant to AI",
                "title": "COBIT Objectives Most Relevant to AI",
                "reference_hint": 4,
                "reference_hint_score": 0.91,
            },
        ]
        identities, appearances = _build_slide_identities(candidates)
        self.assertEqual(len(identities), 1)
        self.assertEqual(len(appearances), 1)
        self.assertEqual(appearances[0]["timestamp_seconds"], 378.0)
        self.assertEqual(identities[0]["source_path"], "complete.jpg")

    def test_unique_visual_match_can_identify_slide_when_ocr_fails(self) -> None:
        candidates = [
            {
                "title": "vigane ocr",
                "ocr_text": "vigane ocr",
                "signature": (10, 10, 10, 10),
            }
        ]
        references = [
            {"index": 1, "title": "AI in COBIT 2019", "text": "AI in COBIT 2019", "signature": (10, 10, 10, 10)},
            {"index": 2, "title": "Muu slaid", "text": "Muu slaid", "signature": (200, 200, 200, 200)},
        ]
        _annotate_candidate_reference_hints(candidates, references)
        self.assertEqual(candidates[0]["reference_hint"], 1)

    def test_slide_is_inserted_at_nearest_segment_boundary(self) -> None:
        transcript = {
            "lesson": {"lesson_id": "lesson-1", "title": "Test"},
            "segments": [
                {"start_seconds": 0.0, "end_seconds": 10.0, "text": "Esimene."},
                {"start_seconds": 10.0, "end_seconds": 20.0, "text": "Teine."},
            ],
        }
        identities = [
            {
                "id": "slide_001",
                "number": 1,
                "title": "Pealkiri",
                "output_source": "video",
            }
        ]
        result = _render_transcript_with_slides(
            transcript,
            identities,
            [{"slide_id": "slide_001", "timestamp_seconds": 9.0}],
        )
        self.assertLess(result.index("### Slaid 1"), result.index("[00:00:10–00:00:20]"))
        self.assertGreater(result.index("### Slaid 1"), result.index("[00:00:00–00:00:10]"))

if __name__ == "__main__":
    unittest.main()
