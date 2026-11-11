from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError

from lecture_notes.web.storage import ObjectStorage


DISPLAY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class SlideCache:
    """Whole-version, local cache for slide transcript artefacts.

    The Object Storage source remains authoritative.  A complete marker is written
    only after Markdown, manifest and every image have been staged successfully.
    """

    def __init__(self, storage: ObjectStorage, root: Path, max_bytes: int, max_age_seconds: int) -> None:
        self.storage = storage
        self.root = root
        self.max_bytes = max_bytes
        self.max_age_seconds = max_age_seconds
        self._lock = threading.Lock()

    def prepare(self, lecture_id: int, operation_id: int, markdown_path: Path) -> Path:
        target = self.root / str(lecture_id) / str(operation_id)
        marker = target / ".complete"
        with self._lock:
            if marker.is_file():
                os.utime(marker, None)
                return target

            self.root.mkdir(parents=True, exist_ok=True)
            stage = self.root / f".staging-{uuid.uuid4()}"
            try:
                stage.mkdir()
                markdown_target = stage / "transcript_with_slides.md"
                self.storage.read_file(markdown_path.as_posix(), markdown_target)
                self._stage_optional(markdown_path.with_name("slides.json"), stage / "slides.json")
                archive_path = markdown_path.with_name("images.zip")
                archive_target = stage / "images.zip"
                if not self._stage_optional(archive_path, archive_target):
                    raise FileNotFoundError(f"Missing slide image archive: {archive_path}")
                self._extract_images(archive_target, stage)
                archive_target.unlink()

                required = _directory_size(stage)
                self._evict(required, target)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    shutil.rmtree(target)
                stage.rename(target)
                marker.touch()
                return target
            except Exception:
                shutil.rmtree(stage, ignore_errors=True)
                raise

    def _stage_optional(self, source: Path, target: Path) -> bool:
        try:
            self.storage.read_file(source.as_posix(), target)
            return True
        except (FileNotFoundError, HTTPError) as exc:
            if isinstance(exc, HTTPError) and exc.code != 404:
                raise
            target.unlink(missing_ok=True)
            return False

    def _extract_images(self, archive_path: Path, stage: Path) -> None:
        seen: set[str] = set()
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member = PurePosixPath(info.filename)
                if (
                    len(member.parts) != 2
                    or member.parts[0] != "images"
                    or member.name != member.parts[1]
                    or member.suffix.lower() not in DISPLAY_IMAGE_EXTENSIONS
                    or info.filename in seen
                ):
                    raise ValueError("images.zip contains an invalid slide image path")
                seen.add(info.filename)
                target = stage / member.as_posix()
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)

    def _evict(self, required: int, target: Path) -> None:
        if required > self.max_bytes:
            raise ValueError("Slide package exceeds the configured cache size")
        now = time.time()
        entries: list[tuple[float, Path, int]] = []
        total = 0
        for marker in self.root.glob("*/*/.complete"):
            directory = marker.parent
            if directory == target:
                continue
            size = _directory_size(directory)
            total += size
            entries.append((marker.stat().st_mtime, directory, size))
        for accessed, directory, size in sorted(entries):
            if now - accessed < self.max_age_seconds:
                continue
            shutil.rmtree(directory, ignore_errors=True)
            total -= size
        if total + required <= self.max_bytes:
            return
        for _, directory, size in sorted(entries):
            if not directory.exists():
                continue
            shutil.rmtree(directory, ignore_errors=True)
            total -= size
            if total + required <= self.max_bytes:
                return
        raise ValueError("Slide cache has insufficient free space")


def _directory_size(root: Path) -> int:
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
