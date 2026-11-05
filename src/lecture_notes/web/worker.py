from __future__ import annotations

import logging
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from lecture_notes.web.database import OracleRepository
from lecture_notes.web.ords import OrdsClient, OrdsError
from lecture_notes.web.settings import OrdsSettings, WorkerSettings


LOGGER = logging.getLogger("lecture_notes.worker")


class Worker:
    def __init__(
        self,
        repository: Any,
        ords: OrdsClient,
        settings: WorkerSettings,
        *,
        sleeper: Any = time.sleep,
        process_factory: Any = subprocess.Popen,
    ) -> None:
        self.repository = repository
        self.ords = ords
        self.settings = settings
        self.sleeper = sleeper
        self.process_factory = process_factory
        self.identity = {
            "worker_instance_id": f"ttu-loeng-{uuid.uuid4()}",
            "host_id": settings.host_id,
            "boot_id": self._boot_id(),
        }

    @staticmethod
    def _boot_id() -> str:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()

    def run_forever(self) -> None:
        startup = self.ords.worker_startup(self.identity)
        active = startup.get("active_job")
        if isinstance(active, dict):
            self.execute(active, recovered=True)
        while True:
            request_id = str(uuid.uuid4())
            try:
                job = self.ords.claim(self.identity, request_id)
                if job is not None:
                    self.execute(job)
                    continue
            except OrdsError:
                LOGGER.exception("ORDS claim failed")
            self.sleeper(self.ords.settings.claim_interval_seconds)

    def execute(self, job: dict[str, Any], *, recovered: bool = False) -> None:
        operation_id = int(job["application_job_id"])
        context = self.repository.operation_context(operation_id)
        if recovered and context.get("local_outcome") in {"SUCCEEDED", "FAILED"}:
            outcome = context["local_outcome"]
            self.ords.complete(
                job,
                self.identity,
                outcome=outcome,
                exit_code=0 if outcome == "SUCCEEDED" else 1,
                end_reason="COMPLETED" if outcome == "SUCCEEDED" else "PROCESS_EXIT",
            )
            return
        parameters = job.get("parameters")
        if not isinstance(parameters, dict) or int(parameters.get("lecture_processing_id", -1)) != int(
            context["lecture_processing_id"]
        ):
            self._fail_without_process(job, operation_id, "INVALID_PARAMETERS", "lecture_processing_id does not match")
            return
        if job.get("job_type_code") != context["operation_type"]:
            self._fail_without_process(job, operation_id, "INVALID_JOB_TYPE", "job_type_code does not match")
            return

        command = self._command(context)
        log_path = (
            self.settings.runtime_root
            / "outputs"
            / "jobs"
            / str(context["lecture_processing_id"])
            / "logs"
            / f"{operation_id}.log"
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = None
        try:
            log = log_path.open("ab")
            process = self.process_factory(command, stdout=log, stderr=subprocess.STDOUT)
        except Exception as exc:
            if log is not None:
                log.close()
            LOGGER.exception("Worker process failed")
            self.repository.mark_operation_completed(operation_id, "FAILED", type(exc).__name__, str(exc))
            try:
                self.ords.complete(
                    job,
                    self.identity,
                    outcome="FAILED",
                    exit_code=1,
                    end_reason="PROCESS_START_FAILED",
                )
            except OrdsError:
                LOGGER.exception("ORDS completion failed after process error")
            return
        try:
            self.repository.mark_operation_started(operation_id)
            if not recovered or job.get("status") == "CLAIMED":
                try:
                    self.ords.start(job, self.identity)
                except OrdsError:
                    LOGGER.exception("ORDS start acknowledgement failed; process continues")
            return_code = self._wait_with_heartbeat(process, job)
        finally:
            log.close()

        outcome = "SUCCEEDED" if return_code == 0 else "FAILED"
        self.repository.mark_operation_completed(
            operation_id,
            outcome,
            None if return_code == 0 else "PROCESS_EXIT",
            None if return_code == 0 else f"Process exited with code {return_code}",
        )
        self.ords.complete(
            job,
            self.identity,
            outcome=outcome,
            exit_code=return_code,
            end_reason="COMPLETED" if return_code == 0 else "PROCESS_EXIT",
        )

    def _wait_with_heartbeat(self, process: Any, job: dict[str, Any]) -> int:
        interval = self.ords.settings.heartbeat_interval_seconds
        while True:
            try:
                return process.wait(timeout=interval)
            except subprocess.TimeoutExpired:
                try:
                    self.ords.heartbeat(job, self.identity)
                except OrdsError:
                    LOGGER.exception("ORDS heartbeat failed; process continues")

    def _command(self, context: dict[str, Any]) -> list[str]:
        lecture_id = str(context["lecture_processing_id"])
        output_root = self.settings.runtime_root / "outputs" / "jobs" / lecture_id
        if context["operation_type"] == "asr":
            return [
                "lecture-notes-asr",
                "transcribe-full",
                context["echo_public_url"],
                "--lesson-id",
                context["echo_lesson_id"],
                "--output-dir",
                str(output_root / "transcript" / self.settings.asr_configuration_id),
                "--model",
                self.settings.asr_model,
                "--revision",
                self.settings.asr_revision,
                "--model-subfolder",
                self.settings.asr_model_subfolder,
                "--configuration-id",
                self.settings.asr_configuration_id,
                "--cpu-threads",
                str(self.settings.cpu_threads),
            ]
        if context["operation_type"] == "slides":
            command = [
                "lecture-slides",
                "process",
                context["echo_public_url"],
                "--lesson-id",
                context["echo_lesson_id"],
                "--transcript",
                str(output_root / "transcript" / self.settings.asr_configuration_id / "transcript.json"),
                "--output-dir",
                str(output_root / "slides"),
                "--coarse-seconds",
                str(self.settings.slide_coarse_seconds),
                "--refine-seconds",
                str(self.settings.slide_refine_seconds),
            ]
            if context.get("slides_relative_path"):
                command.extend(["--slides-input", str(self.settings.runtime_root / context["slides_relative_path"])])
            return command
        raise ValueError(f"Unsupported operation type: {context['operation_type']}")

    def _fail_without_process(self, job: dict[str, Any], operation_id: int, code: str, message: str) -> None:
        self.repository.mark_operation_completed(operation_id, "FAILED", code, message)
        self.ords.complete(
            job,
            self.identity,
            outcome="FAILED",
            exit_code=2,
            end_reason=code,
        )


def main() -> int:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    repository = OracleRepository.from_env()
    try:
        worker = Worker(repository, OrdsClient(OrdsSettings.from_env()), WorkerSettings.from_env())
        worker.run_forever()
    finally:
        repository.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
