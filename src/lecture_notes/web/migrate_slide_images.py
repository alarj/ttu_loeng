from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from lecture_notes.web.database import OracleRepository
from lecture_notes.web.services import MARKDOWN_IMAGE_RE
from lecture_notes.web.settings import WebSettings
from lecture_notes.web.storage import ObjectStorage


def create_images_zip(storage: Any, markdown_path: Path, target: Path) -> int:
    """Create a local `images.zip` from one legacy OCI slide version."""
    markdown = storage.read_bytes(markdown_path.as_posix()).decode("utf-8")
    names = list(dict.fromkeys(MARKDOWN_IMAGE_RE.findall(markdown)))
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, mode="w", compression=zipfile.ZIP_STORED) as archive:
        for name in names:
            archive.writestr(
                f"images/{name}",
                storage.read_bytes((markdown_path.parent / "images" / name).as_posix()),
            )
    return len(names)


def migrate(repository: Any, storage: Any, *, dry_run: bool) -> dict[str, int]:
    result = {"created": 0, "skipped": 0, "missing": 0, "images": 0}
    seen_archives: set[str] = set()
    for lecture in repository.list_lectures():
        for operation in lecture.operations:
            if operation.operation_type != "slides" or operation.local_outcome != "SUCCEEDED":
                continue
            slides_root = Path("outputs") / "jobs" / str(lecture.lecture_processing_id) / "slides"
            versioned_markdown = slides_root / str(operation.operation_id) / "transcript_with_slides.md"
            legacy_markdown = slides_root / "transcript_with_slides.md"
            if storage.exists(versioned_markdown.as_posix()):
                markdown = versioned_markdown
            elif storage.exists(legacy_markdown.as_posix()):
                markdown = legacy_markdown
            else:
                result["missing"] += 1
                continue
            archive = markdown.with_name("images.zip")
            if archive.as_posix() in seen_archives:
                continue
            seen_archives.add(archive.as_posix())
            if storage.exists(archive.as_posix()):
                result["skipped"] += 1
                continue
            if dry_run:
                result["created"] += 1
                continue
            with tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "images.zip"
                image_count = create_images_zip(storage, markdown, target)
                try:
                    storage.write_file(archive.as_posix(), target)
                except RuntimeError as exc:
                    # A previous interrupted process may have finished the same PUT
                    # after its client exited.  Do not overwrite a valid immutable ZIP.
                    if "HTTP 409" not in str(exc) or not storage.exists(archive.as_posix()):
                        raise
                    result["skipped"] += 1
                    continue
                result["images"] += image_count
            result["created"] += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Create images.zip for completed legacy slide versions")
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
