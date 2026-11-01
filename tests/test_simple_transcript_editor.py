from __future__ import annotations

import unittest

from lecture_notes.simple_transcript_editor import PROMPT, extract_chunks


class SimpleTranscriptEditorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transcript = {
            "segments": [
                {"id": "seg_1", "start_seconds": 1.0, "end_seconds": 2.0, "text": "Ja ja esimene mõte."},
                {"id": "seg_2", "start_seconds": 2.0, "end_seconds": 3.0, "text": "Teine mõte jätkub."},
            ]
        }
        self.selection = {
            "samples": [
                {"id": "sample_1", "label": "Test", "segment_ids": ["seg_1", "seg_2"]}
            ]
        }

    def test_prompt_is_plain_language(self) -> None:
        self.assertEqual(
            PROMPT,
            "See on automaatne loengu transkriptsioon -- koostatud salvestise põhjal.\n"
            "Koosta selle alusel normaalne kirjakeelne tekst, eemalda tarbetud kordused ja vaata üle lauselõpud.\n"
            "Säilita erialaterminid ja ingliskeelsed terminid.",
        )

    def test_extract_chunks_joins_segments_as_plain_text(self) -> None:
        chunk = extract_chunks(self.transcript, self.selection)[0]
        self.assertEqual(chunk["text"], "Ja ja esimene mõte.\n\nTeine mõte jätkub.")
        self.assertEqual(chunk["start_seconds"], 1.0)
        self.assertEqual(chunk["end_seconds"], 3.0)

    def test_extract_chunks_can_select_one_sample(self) -> None:
        self.assertEqual(len(extract_chunks(self.transcript, self.selection, sample_id="sample_1")), 1)


if __name__ == "__main__":
    unittest.main()
