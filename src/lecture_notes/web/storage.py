from __future__ import annotations

import http.client
import shutil
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import urlopen


class ObjectStorage:
    def __init__(self, inputs_read: str, inputs_write: str, outputs_read: str, outputs_write: str) -> None:
        self._bases = {
            "inputs": (inputs_read.rstrip("/") + "/", inputs_write.rstrip("/") + "/"),
            "outputs": (outputs_read.rstrip("/") + "/", outputs_write.rstrip("/") + "/"),
        }

    def _url(self, relative_path: str, write: bool = False) -> str:
        if not relative_path or relative_path.startswith("/") or ".." in Path(relative_path).parts:
            raise ValueError("Invalid Object Storage key")
        prefix = relative_path.split("/", 1)[0]
        if prefix not in self._bases:
            raise ValueError("Object key must begin with inputs/ or outputs/")
        return self._bases[prefix][1 if write else 0] + quote(relative_path, safe="/")

    def read_bytes(self, relative_path: str) -> bytes:
        with urlopen(self._url(relative_path), timeout=60) as response:
            return response.read()

    def read_file(self, relative_path: str, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(self._url(relative_path), timeout=60) as response, target.open("wb") as destination:
            shutil.copyfileobj(response, destination, length=1024 * 1024)

    def exists(self, relative_path: str) -> bool:
        try:
            self.read_bytes(relative_path)
        except HTTPError as exc:
            if exc.code == 404:
                return False
            raise
        return True

    def write_bytes(self, relative_path: str, data: bytes) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile() as source:
            source.write(data)
            source.flush()
            self.write_file(relative_path, Path(source.name))

    def write_file(self, relative_path: str, source: Path) -> None:
        url = urlsplit(self._url(relative_path, write=True))
        connection = http.client.HTTPSConnection(url.netloc, timeout=1800)
        try:
            connection.putrequest("PUT", url.path)
            connection.putheader("Content-Length", str(source.stat().st_size))
            connection.endheaders()
            with source.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    connection.send(chunk)
            response = connection.getresponse()
            response.read()
            if response.status not in {200, 201}:
                raise RuntimeError(f"Object Storage PUT failed: HTTP {response.status}")
        finally:
            connection.close()
