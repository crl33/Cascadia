"""Content-addressed object store for raw payloads (docs/DATA_DOCTRINE.md §13, ADR-0004).

Keys are ``<sha256[:2]>/<sha256[2:4]>/<sha256><suffix>``, derived from the payload bytes by
:func:`object_key_for`. Callers never choose keys, which is the immutability contract:
identical bytes map to the same key, different bytes map to different keys (up to sha256
collision, which we treat as impossible), so writing the "same" key twice can only ever be
a rewrite of identical content — a safe no-op. Nothing in the archive is ever overwritten
with different bytes (ADR-0004: R2 lacks object versioning; content-addressed keys are the
compensation).

Backends:

- :class:`LocalFilesystemStore` — plain directory tree, dev/CI default.
- :class:`ObstoreStore` — any ``obstore`` store (``S3Store`` for Cloudflare R2 / AWS S3,
  ``LocalStore``/``MemoryStore`` in tests). ``obstore`` is imported lazily so the local
  backend keeps working without it installed.

Pick a backend from :class:`~cascade_core.settings.Settings` with :func:`store_from_settings`.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from cascade_core.settings import Settings


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def object_key_for(data: bytes, suffix: str = ".json", prefix: str = "") -> str:
    """Content-addressed key, optionally under a lifecycle prefix.

    ``prefix`` exists so a bucket lifecycle rule can bound one product family without
    touching the rest of the archive: the R2 rule ``expire-nbm-90d`` expires objects under
    ``nbm/`` after 90 days (infra/CONTEXT.md, DATA_DOCTRINE §13), which only works if the
    NBM subsets are actually written there. It never changes the address of existing
    objects: the default is the empty prefix, and the sha256 part is unchanged.
    """
    h = sha256_hex(data)
    if prefix and not prefix.endswith("/"):
        raise ValueError(f"object key prefix must end with '/': {prefix!r}")
    return f"{prefix}{h[:2]}/{h[2:4]}/{h}{suffix}"


class ObjectStore(Protocol):
    def put(self, data: bytes, *, suffix: str = ".json", prefix: str = "") -> str:
        """Store bytes under ``prefix``; return the content-addressed object key."""

    def get(self, key: str) -> bytes:
        """Return the stored bytes; raise ``KeyError`` if the key is absent."""

    def exists(self, key: str) -> bool: ...


class LocalFilesystemStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def put(self, data: bytes, *, suffix: str = ".json", prefix: str = "") -> str:
        key = object_key_for(data, suffix, prefix)
        path = self.root / key
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(data)
            tmp.replace(path)
        return key

    def get(self, key: str) -> bytes:
        try:
            return (self.root / key).read_bytes()
        except FileNotFoundError as exc:
            raise KeyError(key) from exc

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()


class ObstoreStore:
    """:class:`ObjectStore` over any ``obstore`` store object (obstore >= 0.11, sync API).

    Use ``obstore.store.S3Store`` for Cloudflare R2 / AWS S3 (see
    :func:`store_from_settings`), ``LocalStore`` or ``MemoryStore`` in tests. The wrapped
    store is byte-compatible with :class:`LocalFilesystemStore`: an ``ObstoreStore`` over
    ``LocalStore(root)`` reads and writes the same tree as ``LocalFilesystemStore(root)``.

    Immutability contract (ADR-0004): ``put`` writes with create-mode semantics
    (``obstore.put(..., mode="create")``), which refuses to overwrite an existing object.
    An ``AlreadyExistsError`` is treated as success, because keys are sha256-derived from
    the payload: an object already stored under this key holds byte-identical content by
    construction, so there is nothing to write and nothing is ever overwritten. Putting
    *different* bytes under a colliding key is impossible through this interface — the
    caller never chooses the key — so create-mode plus content addressing together make
    the archive append-only even on backends without object versioning (R2).
    """

    def __init__(self, store: Any) -> None:
        self.store = store

    def put(self, data: bytes, *, suffix: str = ".json", prefix: str = "") -> str:
        import obstore
        from obstore.exceptions import AlreadyExistsError

        key = object_key_for(data, suffix, prefix)
        try:
            obstore.put(self.store, key, data, mode="create")
        except AlreadyExistsError:
            # Identical key implies identical bytes (sha256-derived): already archived.
            pass
        return key

    def get(self, key: str) -> bytes:
        import obstore
        from obstore.exceptions import NotFoundError

        # LocalStore surfaces missing objects as builtins.FileNotFoundError; S3-backed
        # stores raise obstore.exceptions.NotFoundError. Translate both to KeyError.
        try:
            return bytes(obstore.get(self.store, key).bytes())
        except (FileNotFoundError, NotFoundError) as exc:
            raise KeyError(key) from exc

    def exists(self, key: str) -> bool:
        import obstore
        from obstore.exceptions import NotFoundError

        try:
            obstore.head(self.store, key)
        except (FileNotFoundError, NotFoundError):
            return False
        return True


def store_from_settings(settings: Settings) -> ObjectStore:
    """Build the raw-archive backend selected by ``settings.object_store``.

    - ``"local"`` → :class:`LocalFilesystemStore` over ``settings.raw_dir``.
    - ``"s3"`` → :class:`ObstoreStore` over an ``obstore`` ``S3Store`` at
      ``settings.s3_endpoint`` / ``settings.s3_bucket``. Credentials are NEVER carried by
      Settings: ``obstore`` itself reads the standard ``AWS_ACCESS_KEY_ID`` /
      ``AWS_SECRET_ACCESS_KEY`` environment variables (Settings secrets policy).

    Cloudflare R2 (ADR-0004 production target): endpoint
    ``https://<account-id>.r2.cloudflarestorage.com``, region ``auto``, path-style
    addressing — the factory passes ``region="auto"`` and
    ``virtual_hosted_style_request=False`` accordingly.

    Raises ``ValueError`` when ``"s3"`` is selected but ``s3_endpoint`` or ``s3_bucket``
    is missing.
    """
    if settings.object_store == "local":
        return LocalFilesystemStore(settings.raw_dir)
    if settings.object_store == "s3":
        missing = [
            name
            for name, value in (("s3_endpoint", settings.s3_endpoint), ("s3_bucket", settings.s3_bucket))
            if not value
        ]
        if missing:
            raise ValueError(
                "object_store='s3' requires "
                + " and ".join(missing)
                + " (env CASCADE_S3_ENDPOINT / CASCADE_S3_BUCKET)"
            )
        from obstore.store import S3Store

        return ObstoreStore(
            S3Store(
                bucket=settings.s3_bucket,
                endpoint=settings.s3_endpoint,
                region="auto",
                virtual_hosted_style_request=False,
            )
        )
    # Settings.__post_init__ already rejects unknown backends; defensive only.
    raise ValueError(f"unknown object_store backend: {settings.object_store!r}")
