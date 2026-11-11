from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from lecture_notes.web.database import OracleRepository
from lecture_notes.web.settings import WebSettings
from lecture_notes.web.storage import ObjectStorage


ARTIFACT_NAMES = ("run.json", "slides.json", "images.zip", "transcript_with_slides.md")


def migrate(repository: Any, storage: Any, *, dry_run: bool) -> dict[str, int]:
    """Copy legacy root-level slide results to their immutable operation directory.

    Markdown is copied last: the web application treats its presence as a complete
    result, so users never observe an incomplete new version.
    """
    result = {"migrated": 0, "already_versioned": 0, "missing": 0, "files": 0}
    for lecture in repository.list_lectures():
        for operation in lecture.operations:
            if operation.operation_type != "slides" or operation.local_outcome != "SUCCEEDED":
                continue
            slides_root = Path("outputs") / "jobs" / str(lecture.lecture_processing_id) / "slides"
            legacy_root = slides_root
            version_root = slides_root / str(operation.operation_id)
            version_markdown = version_root / "transcript_with_slides.md"
            if storage.exists(version_markdown.as_posix()):
                result["already_versioned"] += 1
                continue
            sources = [legacy_root / name for name in ARTIFACT_NAMES]
            if not all(storage.exists(source.as_posix()) for source in sources):
                result["missing"] += 1
                continue
            if dry_run:
                result["migrated"] += 1
                result["files"] += len(ARTIFACT_NAMES)
                continue
            for name in (*ARTIFACT_NAMES[:-1], ARTIFACT_NAMES[-1]):
                _copy_verified(storage, legacy_root / name, version_root / name)
                result["files"] += 1
            result["migrated"] += 1
    return result


def _copy_verified(storage: Any, source: Path, target: Path) -> None:
    source_data = storage.read_bytes(source.as_posix())
    source_digest = hashlib.sha256(source_data).digest()
    if storage.exists(target.as_posix()):
        if hashlib.sha256(storage.read_bytes(target.as_posix())).digest() != source_digest:
            raise RuntimeError(f"Existing versioned artifact differs: {target}")
        return
    storage.write_bytes(target.as_posix(), source_data)
    if hashlib.sha256(storage.read_bytes(target.as_posix())).digest() != source_digest:
        raise RuntimeError(f"Copied artifact verification failed: {target}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy slide results to operation directories")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    settings = WebSettings.from_env()
    storage = ObjectStorage(settings.oci_inputs_r, settings.oci_inputs_rw, settings.oci_outputs_r, settings.oci_outputs_rw)
    repository = OracleRepository.from_env()
    try:
        result = migrate(repository, storage, dry_run=args.dry_run)
    finally:
        repository.close()
    print(" ".join(f"{key}={value}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
