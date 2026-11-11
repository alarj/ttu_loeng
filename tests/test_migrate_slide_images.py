from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from lecture_notes.web.migrate_slide_images import create_images_zip, migrate
from lecture_notes.web.models import Operation
from storage_test_utils import FileStorage


class MigrationTests(unittest.TestCase):
    def test_creates_one_zip_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = FileStorage(root)
            base = root / "outputs/jobs/12/slides/2"
            (base / "images").mkdir(parents=True)
            (base / "transcript_with_slides.md").write_text("![Slaid](images/slide_001.png)\n", encoding="utf-8")
            (base / "images/slide_001.png").write_bytes(b"image")
            lecture = SimpleNamespace(
                lecture_processing_id=12,
                operations=[Operation(2, "slides", 1, 1, local_outcome="SUCCEEDED")],
            )
            repository = SimpleNamespace(list_lectures=lambda: [lecture])

            self.assertEqual(migrate(repository, storage, dry_run=True), {"created": 1, "skipped": 0, "missing": 0, "images": 0})
            self.assertEqual(migrate(repository, storage, dry_run=False), {"created": 1, "skipped": 0, "missing": 0, "images": 1})
            with zipfile.ZipFile(base / "images.zip") as archive:
                self.assertEqual(archive.namelist(), ["images/slide_001.png"])
                self.assertEqual(archive.read("images/slide_001.png"), b"image")
            self.assertEqual(migrate(repository, storage, dry_run=False), {"created": 0, "skipped": 1, "missing": 0, "images": 0})

    def test_uses_legacy_result_location_when_versioned_markdown_is_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = FileStorage(root)
            base = root / "outputs/jobs/12/slides"
            (base / "images").mkdir(parents=True)
            (base / "transcript_with_slides.md").write_text("![Slaid](images/slide_001.png)\n", encoding="utf-8")
            (base / "images/slide_001.png").write_bytes(b"image")
            lecture = SimpleNamespace(
                lecture_processing_id=12,
                operations=[Operation(2, "slides", 1, 1, local_outcome="SUCCEEDED")],
            )
            repository = SimpleNamespace(list_lectures=lambda: [lecture])

            self.assertEqual(migrate(repository, storage, dry_run=False), {"created": 1, "skipped": 0, "missing": 0, "images": 1})
            self.assertTrue((base / "images.zip").is_file())
