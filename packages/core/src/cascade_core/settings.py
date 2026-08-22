"""Settings from the environment (12-factor). Defaults are local-dev only; nothing secret lives here."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SEED_FILE = Path(__file__).resolve().parent / "seed" / "stations.json"


@dataclass(frozen=True)
class Settings:
    db_url: str = "sqlite+aiosqlite:///./data/cascade.db"
    raw_dir: Path = Path("./data/raw")
    contact: str = "cascade-oracle@example.invalid"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    geo_dir: Path = Path("./tests/fixtures/geo")
    seed_file: Path = field(default=SEED_FILE)

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
        )

    @property
    def user_agent(self) -> str:
        return f"CascadeOracle/0.1 (+contact: {self.contact})"
