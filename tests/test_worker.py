from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from lecture_notes.web.settings import OrdsSettings, WorkerSettings
from lecture_notes.web.worker import Worker


class FakeRepository:
    def __init__(self):
        self.started = []
        self.completed = []
        self.local_outcome = None

    def operation_context(self, operation_id):
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
                process = FakeProcess(command, stdout, stderr)
                created.append(process)
                return process

            worker = Worker(repository, ords, settings, process_factory=factory)
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
            self.assertIn(str(Path(directory) / "outputs/jobs/12/slides/55"), created[0].command)

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
                process_factory=lambda *args, **kwargs: self.fail("process must not be started"),
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


if __name__ == "__main__":
    unittest.main()
