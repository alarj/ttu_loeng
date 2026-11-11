from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lecture_notes.web.migrate_slide_versions import ARTIFACT_NAMES, migrate
from lecture_notes.web.models import Operation
from storage_test_utils import FileStorage


class SlideVersionMigrationTests(unittest.TestCase):
    def test_copies_complete_legacy_result_to_operation_directory_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            storage = FileStorage(root)
            legacy = root / "outputs/jobs/12/slides"
            legacy.mkdir(parents=True)
            for name in ARTIFACT_NAMES:
                (legacy / name).write_bytes(f"{name}-content".encode("ascii"))
            lecture = SimpleNamespace(
                lecture_processing_id=12,
                operations=[Operation(2, "slides", 1, 1, local_outcome="SUCCEEDED")],
            )
            repository = SimpleNamespace(list_lectures=lambda: [lecture])

            self.assertEqual(migrate(repository, storage, dry_run=True), {"migrated": 1, "already_versioned": 0, "missing": 0, "files": 4})
            self.assertEqual(migrate(repository, storage, dry_run=False), {"migrated": 1, "already_versioned": 0, "missing": 0, "files": 4})
            for name in ARTIFACT_NAMES:
                self.assertEqual((legacy / name).read_bytes(), (legacy / "2" / name).read_bytes())
            self.assertEqual(migrate(repository, storage, dry_run=False), {"migrated": 0, "already_versioned": 1, "missing": 0, "files": 0})
