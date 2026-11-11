from __future__ import annotations

import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from lecture_notes.web.settings import OrdsSettings, WorkerSettings
from lecture_notes.web.worker import Worker
from storage_test_utils import FileStorage


class FakeRepository:
    def __init__(self):
        self.started = []
        self.completed = []
        self.local_outcome = None
        self.missing_operation = False

    def operation_context(self, operation_id):
        if self.missing_operation:
            raise KeyError(operation_id)
        return {
            "operation_id": operation_id,
            "operation_type": "slides",
            "lecture_processing_id": 12,
            "echo_lesson_id": "lesson-id",
            "echo_public_url": "https://echo360.org.uk/section/id/public",
            "slides_relative_path": "inputs/12/slides.pdf",
            "slide_sensitivity_level": 2,
            "local_outcome": self.local_outcome,
        }

    def mark_operation_started(self, operation_id):
        self.started.append(operation_id)

    def mark_operation_completed(self, *values):
        self.completed.append(values)


class FakeOrds:
    def __init__(self):
        self.settings = OrdsSettings("https://ords", "id", "secret", 60, 300, 5)
        self.started = []
        self.heartbeats = []
        self.completed = []

    def start(self, job, identity):
        self.started.append(job["job_id"])

    def heartbeat(self, job, identity):
        self.heartbeats.append(job["job_id"])

    def complete(self, job, identity, **values):
        self.completed.append((job["job_id"], values))


class FakeProcess:
    def __init__(self, command, stdout, stderr):
        self.command = command
        self.waits = 0

    def wait(self, timeout):
        self.waits += 1
        if self.waits == 1:
            raise subprocess.TimeoutExpired(self.command, timeout)
        return 0


class WorkerTests(unittest.TestCase):
    def test_worker_starts_heartbeats_and_completes_process(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = FakeRepository()
            ords = FakeOrds()
            settings = WorkerSettings(
                runtime_root=Path(directory),
                host_id="host",
                cpu_threads=3,
                asr_model="model",
                asr_revision="revision",
                asr_model_subfolder="ct2",
                asr_configuration_id="config",
                slide_coarse_seconds=20,
                slide_refine_seconds=2,
                slide_change_distance=0.020,
            )
            created = []

            def factory(command, stdout, stderr):
                output_dir = Path(command[command.index("--output-dir") + 1])
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "transcript_with_slides.md").write_text(
                    "![Slaid](images/slide_001.png)", encoding="utf-8"
                )
                (output_dir / "slides.json").write_text("{}", encoding="utf-8")
                (output_dir / "images").mkdir()
                (output_dir / "images/slide_001.png").write_bytes(b"slide")
                process = FakeProcess(command, stdout, stderr)
                created.append(process)
                return process

            worker = Worker(repository, ords, settings, process_factory=factory, storage=FileStorage(Path(directory)))
            raw = Path(directory) / "outputs/jobs/12/transcript/config/transcript.json"
            raw.parent.mkdir(parents=True)
            raw.write_text("{}", encoding="utf-8")
            upload = Path(directory) / "inputs/12/slides.pdf"
            upload.parent.mkdir(parents=True)
            upload.write_bytes(b"slides")
            reference = Path(directory) / "work/jobs/12/slides/55/reference"
            reference.mkdir(parents=True)
            (reference / "slide_001.png").write_bytes(b"reference")
            worker.execute(
                {
                    "job_id": 99,
                    "application_job_id": "55",
                    "job_type_code": "slides",
                    "parameters": {"lecture_processing_id": 12},
                    "execution_token": "token",
                    "status": "CLAIMED",
                }
            )

            self.assertEqual(repository.started, [55])
            self.assertEqual(ords.started, [99])
            self.assertEqual(ords.heartbeats, [99])
            self.assertEqual(ords.completed[0][1]["outcome"], "SUCCEEDED")
            self.assertIn("--slides-input", created[0].command)
            self.assertIn("--change-distance", created[0].command)
            self.assertIn("0.014000", created[0].command)
            self.assertIn(str(Path(directory) / "work/jobs/12/slides/55"), created[0].command)
            self.assertFalse(reference.exists())
            archive = Path(directory) / "outputs/jobs/12/slides/55/images.zip"
            self.assertTrue(archive.is_file())
            with zipfile.ZipFile(archive) as contents:
                self.assertEqual(contents.namelist(), ["images/slide_001.png"])
            self.assertFalse((Path(directory) / "outputs/jobs/12/slides/55/images/slide_001.png").exists())

    def test_recovered_completed_operation_is_not_run_again(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = FakeRepository()
            repository.local_outcome = "SUCCEEDED"
            ords = FakeOrds()
            settings = WorkerSettings(
                runtime_root=Path(directory),
                host_id="host",
                cpu_threads=3,
                asr_model="model",
                asr_revision="revision",
                asr_model_subfolder="ct2",
                asr_configuration_id="config",
                slide_coarse_seconds=20,
                slide_refine_seconds=2,
                slide_change_distance=0.020,
            )
            worker = Worker(
                repository,
                ords,
                settings,
                process_factory=lambda *args, **kwargs: self.fail("process must not be started"), storage=FileStorage(Path(directory)),
            )
            worker.execute(
                {
                    "job_id": 99,
                    "application_job_id": "55",
                    "job_type_code": "slides",
                    "parameters": {"lecture_processing_id": 12},
                    "execution_token": "token",
                    "status": "RUNNING",
                },
                recovered=True,
            )
            self.assertEqual(ords.completed[0][1]["outcome"], "SUCCEEDED")

    def test_missing_local_operation_interrupts_claimed_ords_job(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = FakeRepository()
            repository.missing_operation = True
            ords = FakeOrds()
            settings = WorkerSettings(
                runtime_root=Path(directory),
                host_id="host",
                cpu_threads=3,
                asr_model="model",
                asr_revision="revision",
                asr_model_subfolder="ct2",
                asr_configuration_id="config",
                slide_coarse_seconds=20,
                slide_refine_seconds=2,
                slide_change_distance=0.020,
            )
            worker = Worker(
                repository,
                ords,
                settings,
                process_factory=lambda *args, **kwargs: self.fail("process must not be started"), storage=FileStorage(Path(directory)),
            )

            worker.execute(
                {
                    "job_id": 99,
                    "application_job_id": "55",
                    "job_type_code": "slides",
                    "parameters": {"lecture_processing_id": 12},
                    "execution_token": "token",
                    "status": "CLAIMED",
                }
            )

            self.assertEqual(repository.started, [])
            self.assertEqual(repository.completed, [])
            self.assertEqual(ords.completed, [(99, {"outcome": "INTERRUPTED", "exit_code": 0, "end_reason": "APPLICATION_OPERATION_NOT_FOUND"})])


if __name__ == "__main__":
    unittest.main()
