"""Settings from the environment (12-factor). Defaults are local-dev only; nothing secret lives here.

Secrets policy:
- S3 credentials are NEVER stored in Settings. obstore reads the standard
  ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` variables straight from the
  process environment; Settings carries only the non-secret endpoint and bucket.
- ``usgs_api_key`` is a secret: it is excluded from ``repr()`` and must never be
  logged or serialized.
- ``db_url`` / ``queue_db_url`` embed a password in production (Neon DSNs); they are
  likewise excluded from ``repr()`` so a logged/raised Settings can never leak them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SEED_FILE = Path(__file__).resolve().parent / "seed" / "stations.json"

_OBJECT_STORES = ("local", "s3")


@dataclass(frozen=True)
class Settings:
    # Excluded from repr(): production DSNs embed a password (see module docstring).
    db_url: str = field(default="sqlite+aiosqlite:///./data/cascade.db", repr=False)
    raw_dir: Path = Path("./data/raw")
    contact: str = "cascadia-papsukkal@example.invalid"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    geo_dir: Path = Path("./tests/fixtures/geo")
    seed_file: Path = field(default=SEED_FILE)
    # Worker queue connection string. Exists because Neon's pooled hosts (PgBouncer,
    # "-pooler" in the hostname) cannot carry LISTEN/NOTIFY, which the procrastinate
    # queue depends on — so the queue must get the DIRECT connection string. None
    # falls back to db_url (see ``effective_queue_db_url``), which is correct for
    # local dev where db_url is already direct. Excluded from repr() like db_url.
    queue_db_url: str | None = field(default=None, repr=False)
    # Raw payload archive backend: "local" (filesystem) or "s3" (any S3-compatible
    # store, e.g. Cloudflare R2).
    object_store: str = "local"
    # S3-compatible endpoint; R2 pattern: https://<account-id>.r2.cloudflarestorage.com
    s3_endpoint: str | None = None
    s3_bucket: str | None = None
    # Not used by the legacy IV adapter; plumbing for the USGS OGC API migration.
    # Secret: excluded from repr(); must never be logged.
    usgs_api_key: str | None = field(default=None, repr=False)
    #: Git revision this process was built from, stamped at deploy time. Reconciliation only:
    #: a running build with no identity cannot be checked against the repository (RUNBOOK-deploy).
    git_revision: str | None = None

    def __post_init__(self) -> None:
        if self.object_store not in _OBJECT_STORES:
            raise ValueError(
                f"object_store must be one of {'|'.join(_OBJECT_STORES)}, got {self.object_store!r}"
            )

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env
        extra = tuple(o.strip() for o in e.get("CASCADE_CORS_ORIGINS", "").split(",") if o.strip())
        return cls(
            db_url=e.get("CASCADE_DB_URL", cls.db_url),
            raw_dir=Path(e.get("CASCADE_RAW_DIR", str(cls.raw_dir))),
            contact=e.get("CASCADE_CONTACT", cls.contact),
            cors_origins=tuple(dict.fromkeys(("http://localhost:5173", *extra))),
            geo_dir=Path(e.get("CASCADE_GEO_DIR", str(cls.geo_dir))),
            seed_file=Path(e.get("CASCADE_SEED_FILE", str(SEED_FILE))),
            queue_db_url=e.get("CASCADE_QUEUE_DB_URL") or None,
            object_store=(e.get("CASCADE_OBJECT_STORE") or cls.object_store).strip(),
            s3_endpoint=e.get("CASCADE_S3_ENDPOINT") or None,
            s3_bucket=e.get("CASCADE_S3_BUCKET") or None,
            usgs_api_key=e.get("CASCADE_USGS_API_KEY") or None,
            # Platform-attested first. Railway's GitHub integration deploys every push to main
            # and injects RAILWAY_GIT_COMMIT_SHA for the commit it actually built — discovered
            # 2026-08-28 when production served code from a commit the manual stamp postdated:
            # CASCADE_GIT_REVISION froze at the last hand-set value while auto-deploys moved on,
            # so /system/version LIED. A stamp someone typed can never outrank one the platform
            # derived from the build itself. The manual var stays as the fallback for
            # workdir-upload deploys (`railway up`), which have no git identity of their own.
            git_revision=e.get("RAILWAY_GIT_COMMIT_SHA") or e.get("CASCADE_GIT_REVISION") or None,
        )

    @property
    def effective_queue_db_url(self) -> str:
        """The queue's connection string: ``queue_db_url`` when set, else ``db_url``."""
        return self.queue_db_url or self.db_url

    @property
    def user_agent(self) -> str:
        return f"CascadiaPapsukkal/0.1 (+contact: {self.contact})"
