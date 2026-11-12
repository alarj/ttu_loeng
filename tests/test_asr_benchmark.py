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
    _match_reference_slides,
    _render_transcript_with_slides,
    CHANGE_DISTANCE,
    SIGNATURE_COLOR_MODE,
    SIGNATURE_SIZE,
    build_parser as build_slide_parser,
    image_distance,
    normalize_text,
    restore_metadata_acronyms,
    select_video_source,
    select_video_source_by_quality,
    select_video_track_source_by_quality,
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

    def test_select_secondary_video_track_source(self) -> None:
        payload = {
            "video": {
                "media": {
                    "media": {
                        "current": {
                            "secondaryFiles": [
                                {"s3Url": "https://content.echo360.org.uk/camera.mp4", "size": 120, "width": 640, "height": 360},
                            ]
                        }
                    }
                }
            }
        }
        self.assertEqual(
            select_video_track_source_by_quality(payload, track="secondary", prefer_highest=False),
            ("https://content.echo360.org.uk/camera.mp4", 120, 640, 360),
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

    def test_slide_signature_size_is_detail_preserving(self) -> None:
        self.assertEqual(SIGNATURE_SIZE, (160, 90))
        self.assertEqual(SIGNATURE_COLOR_MODE, "RGB")
        self.assertEqual(CHANGE_DISTANCE, 0.020)

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
                "--lecture-start-at",
                "2026-09-12T14:45:00Z",
            ]
        )
        self.assertEqual(args.command, "process")
        self.assertEqual(args.coarse_seconds, 20.0)
        self.assertEqual(args.refine_seconds, 2.0)
        self.assertEqual(args.lecture_start_at, "2026-09-12T14:45:00Z")

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

    def test_full_frame_ocr_can_match_reference_despite_bad_title_ocr(self) -> None:
        identities = [
            {
                "title": "sash kat Comet Sogn frites",
                "ocr_text": "sash kat Comet Sogn frites",
                "reference_ocr_text": (
                    "Peidetud neuronite arv? Eksimismäär testandmetel "
                    "Neuronite arvu varieerides leida eksimismäära miinimum"
                ),
                "signature": (250, 250, 250, 250),
                "match_status": "video_only",
                "reference": None,
            }
        ]
        references = [
            {
                "index": 1,
                "title": "Muu slaid",
                "text": "Närvivõrgu mudel ja väljund",
                "signature": (250, 250, 250, 250),
            },
            {
                "index": 2,
                "title": "Peidetud neuronite arv?",
                "text": (
                    "Peidetud neuronite arv? Eksimismäär testandmetel "
                    "Neuronite arvu varieerides leida eksimismäära miinimum"
                ),
                "signature": (250, 250, 250, 250),
            },
        ]
        _match_reference_slides(identities, references)
        self.assertEqual(identities[0]["match_status"], "matched")
        self.assertEqual(identities[0]["reference"]["index"], 2)
        self.assertEqual(identities[0]["title"], "Peidetud neuronite arv?")

    def test_slide_is_inserted_at_nearest_segment_boundary(self) -> None:
        transcript = {
            "lesson": {"lesson_id": "lesson-1", "title": "Test"},
            "configuration": {"model_id": "TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604"},
            "audio": {"duration_seconds": 9928.0},
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
        self.assertNotIn("### Slaid 1 — Pealkiri", result)
        self.assertIn("- Mudel: `TalTechNLP/whisper-large-v3-turbo-et-verbatim-2604`", result)
        self.assertIn("- Heli kestus: `02:45:28`", result)
        self.assertIn("- Segmente: 2", result)

    def test_transcript_with_slides_includes_tallinn_lecture_date(self) -> None:
        transcript = {
            "lesson": {"lesson_id": "lesson-1", "title": "Test"},
            "segments": [{"start_seconds": 0.0, "end_seconds": 10.0, "text": "Esimene."}],
        }
        result = _render_transcript_with_slides(
            transcript,
            [],
            [],
            lecture_start_at="2026-09-12T21:30:00Z",
        )
        self.assertIn("- Loengu toimumise kuupäev: 13.09.2026", result)

    def test_confirmed_reference_title_is_shown_in_transcript(self) -> None:
        transcript = {
            "lesson": {"lesson_id": "lesson-1", "title": "Test"},
            "segments": [
                {"start_seconds": 0.0, "end_seconds": 10.0, "text": "Esimene."},
            ],
        }
        identities = [
            {
                "id": "slide_001",
                "number": 1,
                "title": "Peidetud neuronite arv?",
                "output_source": "user_file",
                "reference": {"index": 17},
            }
        ]
        result = _render_transcript_with_slides(
            transcript,
            identities,
            [{"slide_id": "slide_001", "timestamp_seconds": 0.0}],
        )
        self.assertIn("### Slaid 1 — Peidetud neuronite arv?", result)

if __name__ == "__main__":
    unittest.main()
