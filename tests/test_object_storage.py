from __future__ import annotations

import os
import uuid
import unittest

from lecture_notes.web.storage import ObjectStorage


class ObjectStorageIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        names = ("OCI_INPUTS_R", "OCI_INPUTS_RW", "OCI_OUTPUTS_R", "OCI_OUTPUTS_RW")
        if not all(os.getenv(name) for name in names):
            raise unittest.SkipTest("OCI prefix-PAR variables are not configured")
        cls.storage = ObjectStorage(*(os.environ[name] for name in names))

    def test_write_then_read_inputs_and_outputs(self) -> None:
        suffix = uuid.uuid4().hex
        for prefix in ("inputs", "outputs"):
            key = f"{prefix}/tests/{suffix}/probe.txt"
            payload = f"OCI integration probe {suffix}".encode("ascii")
            self.storage.write_bytes(key, payload)
            self.assertTrue(self.storage.exists(key))
            self.assertEqual(self.storage.read_bytes(key), payload)

