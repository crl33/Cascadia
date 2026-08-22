"""Content-addressed object store for raw payloads (docs/DATA_DOCTRINE.md §13, ADR-0004).

Keys are `<sha256[:2]>/<sha256[2:4]>/<sha256><suffix>` so an S3 backend can implement the same
two-method interface later. Writing the same bytes twice is a no-op.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def object_key_for(data: bytes, suffix: str = ".json") -> str:
    h = sha256_hex(data)
    return f"{h[:2]}/{h[2:4]}/{h}{suffix}"


class ObjectStore(Protocol):
    def put(self, data: bytes, *, suffix: str = ".json") -> str:
        """Store bytes; return the content-addressed object key."""

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


class LocalFilesystemStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def put(self, data: bytes, *, suffix: str = ".json") -> str:
        key = object_key_for(data, suffix)
        path = self.root / key
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
        return key

    def get(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()
