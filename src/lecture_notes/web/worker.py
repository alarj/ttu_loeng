from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any

from lecture_notes.web.database import OracleRepository
from lecture_notes.web.ords import OrdsClient, OrdsError
from lecture_notes.web.settings import OrdsSettings, WorkerSettings
from lecture_notes.web.storage import ObjectStorage


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
        storage: ObjectStorage | None = None,
    ) -> None:
        self.repository = repository
        self.ords = ords
        self.settings = settings
        self.sleeper = sleeper
        self.process_factory = process_factory
        self.storage = storage or ObjectStorage(settings.oci_inputs_r, settings.oci_inputs_rw, settings.oci_outputs_r, settings.oci_outputs_rw)
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
        try:
            context = self.repository.operation_context(operation_id)
        except KeyError:
            LOGGER.warning("Claimed ORDS job has no active local operation operation_id=%d", operation_id)
            self.ords.complete(
                job,
                self.identity,
                outcome="INTERRUPTED",
                exit_code=0,
                end_reason="APPLICATION_OPERATION_NOT_FOUND",
            )
            return
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

        work_root = self.settings.runtime_root / "work" / "jobs" / str(context["lecture_processing_id"])
        try:
            self._stage_inputs(context, work_root)
            command = self._command(context, work_root)
        except Exception as exc:
            LOGGER.exception("Worker input staging failed operation_id=%d", operation_id)
            self._fail_without_process(job, operation_id, "INPUT_STAGE_FAILED", str(exc))
            return
        log_path = (
            self.settings.runtime_root
            / "work"
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
        if outcome == "SUCCEEDED":
            try:
                self._upload_outputs(context, work_root)
                if context["operation_type"] == "slides":
                    self._remove_reference_slides(work_root, context)
            except Exception as exc:
                LOGGER.exception("Worker output upload failed operation_id=%d", operation_id)
                outcome = "FAILED"
                return_code = 1
                failure_code = "OUTPUT_UPLOAD_FAILED"
                failure_message = str(exc)
            else:
                failure_code = None
                failure_message = None
        else:
            failure_code = "PROCESS_EXIT"
            failure_message = f"Process exited with code {return_code}"
        self.repository.mark_operation_completed(
            operation_id,
            outcome,
            failure_code,
            failure_message,
        )
        self.ords.complete(
            job,
            self.identity,
            outcome=outcome,
            exit_code=return_code,
            end_reason="COMPLETED" if outcome == "SUCCEEDED" else (failure_code or "PROCESS_EXIT"),
        )

    def _remove_reference_slides(self, work_root: Path, context: dict[str, Any]) -> None:
        """Remove rendered matching inputs after a successful slides operation.

        The original user file remains under ``inputs/<lecture_processing_id>`` and
        is rendered again if the lecture is later reprocessed.  Final images have
        already been written to the sibling ``images`` directory at this point.
        """
        reference_dir = (
            work_root
            / "slides"
            / str(context["operation_id"])
            / "reference"
        )
        if not reference_dir.is_dir():
            return
        try:
            shutil.rmtree(reference_dir)
        except OSError:
            LOGGER.exception("Could not remove rendered reference slides path=%s", reference_dir)

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

    def _stage_inputs(self, context: dict[str, Any], work_root: Path) -> None:
        if context["operation_type"] == "slides":
            lecture_id = str(context["lecture_processing_id"])
            raw = f"outputs/jobs/{lecture_id}/transcript/{self.settings.asr_configuration_id}/transcript.json"
            self.storage.read_file(raw, work_root / "transcript" / self.settings.asr_configuration_id / "transcript.json")
            if context.get("slides_relative_path"):
                key = context["slides_relative_path"]
                self.storage.read_file(key, work_root / key)

    def _upload_outputs(self, context: dict[str, Any], work_root: Path) -> None:
        lecture_id = str(context["lecture_processing_id"])
        relative = (
            Path("transcript") / self.settings.asr_configuration_id
            if context["operation_type"] == "asr"
            else Path("slides") / str(context["operation_id"])
        )
        source = work_root / relative
        if context["operation_type"] == "slides":
            self._create_images_archive(source)
        for path in source.rglob("*"):
            if path.is_file() and "reference" not in path.parts and "images" not in path.parts:
                relative = path.relative_to(work_root).as_posix()
                self.storage.write_file(f"outputs/jobs/{lecture_id}/{relative}", path)

    @staticmethod
    def _create_images_archive(source: Path) -> None:
        images = source / "images"
        if not images.is_dir():
            raise FileNotFoundError("Slide processing output has no images directory")
        archive_path = source / "images.zip"
        with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_STORED) as archive:
            for image in sorted(images.rglob("*")):
                if image.is_file():
                    archive.write(image, image.relative_to(source).as_posix())

    def _command(self, context: dict[str, Any], output_root: Path) -> list[str]:
        lecture_id = str(context["lecture_processing_id"])
        operation_id = str(context["operation_id"])
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
            sensitivity_level = int(context.get("slide_sensitivity_level") or 0)
            if not -3 <= sensitivity_level <= 3:
                raise ValueError("Slide sensitivity level must be between -3 and +3")
            change_distance = self.settings.slide_change_distance - (sensitivity_level * 0.003)
            if change_distance <= 0:
                raise ValueError("Slide change distance must be positive")
            command = [
                "lecture-slides",
                "process",
                context["echo_public_url"],
                "--lesson-id",
                context["echo_lesson_id"],
                "--transcript",
                str(output_root / "transcript" / self.settings.asr_configuration_id / "transcript.json"),
                "--output-dir",
                str(output_root / "slides" / operation_id),
                "--coarse-seconds",
                str(self.settings.slide_coarse_seconds),
                "--refine-seconds",
                str(self.settings.slide_refine_seconds),
                "--change-distance",
                f"{change_distance:.6f}",
                "--sensitivity-level",
                str(sensitivity_level),
            ]
            if context.get("slides_relative_path"):
                command.extend(["--slides-input", str(output_root / context["slides_relative_path"])])
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
