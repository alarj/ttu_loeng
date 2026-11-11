from __future__ import annotations

from pathlib import Path


class FileStorage:
    """Test double with the same object-key contract as ObjectStorage."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        if not key or key.startswith("/") or ".." in Path(key).parts:
            raise ValueError("Invalid Object Storage key")
        return self.root / key

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def read_file(self, key: str, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.read_bytes(key))

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def write_file(self, key: str, source: Path) -> None:
        self.write_bytes(key, source.read_bytes())

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()
