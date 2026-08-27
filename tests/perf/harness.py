"""One ingested database, three non-UNKNOWN surfaces, no network — the fixed ground the
before/after measurement stands on.

The ingest is not re-implemented here. `tests/integration/test_p3_surfaces_api.py` already walks
the whole distance — checked-in provider payloads through the real ingest jobs into
`derived_feature` / `forecast_run` rows — and it is the module that pins what "all three surfaces
computed" means. Re-implementing it would give a second definition of a seeded database that
could drift from the first, so this imports it.

**Fixtures, not live ingest.** The brief allows the real network here. Captured payloads are used
instead because a baseline whose numbers change with the weather cannot serve as a semantic
baseline: the whole point is that a body captured today and a body captured after the optimiser
has finished must be diffable byte for byte. Fixed payloads + fixed clock = a body that is a
function of the code alone. The SQL the read path issues is the same either way — it is decided
by `Knowledge` and the assemblers, not by what the numbers happen to be.

The same function seeds a scratch PostgreSQL database (`create_schema` is a checkfirst no-op on
an Alembic-migrated schema, and `seed_all` materialises the PostGIS surface itself), which is how
the query counts here were confirmed against the production driver.

**One step is added on top: `usgs.fetch_iv`.** The P3 module does not run it — its subject is the
three P3 surfaces, none of which reads `observation`. `/viz/basins` does: `assemble.assess_point`
issues THREE observation reads per point (the latest value, the secondary variable at that same
instant, and the six-hour trend window) plus a station lookup, and skips all four when no
observation exists. Leaving USGS out would have hidden eighteen of the queries the endpoint
really issues — the single largest N+1 on the path — and produced a baseline the optimiser could
"beat" without touching production's actual shape. With it in, the local count matches the ~120
measured in production; without it, it reads 102.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from cascade_core.fetch import ArchivingFetcher
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.settings import Settings
from cascade_worker.runtime import Runtime

from tests.conftest import FIXTURES, GEO
from tests.integration.test_p3_surfaces_api import AS_OF, BEFORE, _ingest_everything

__all__ = ["AS_OF", "BEFORE", "BASELINE_DIR", "SKAGIT", "T_USGS_IV", "ingest", "settings_for", "iso"]

#: When the USGS instantaneous-values fixture was really captured. Used as that job's retrieval
#: clock so `available_at` and freshness are computed from the instant production would have seen,
#: and so the rows are knowledge-visible at AS_OF two days later.
T_USGS_IV = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)

USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"

BASELINE_DIR = Path(__file__).resolve().parent / "baseline"

#: The single-basin endpoint the brief asks for beside `/viz/basins`.
SKAGIT = "basin:skagit"


def iso(when: datetime) -> str:
    """The `as_of` query-parameter spelling, identical everywhere so captures are comparable."""
    return when.isoformat().replace("+00:00", "Z")


def settings_for(root: Path, db_url: str | None = None) -> Settings:
    """Settings pointing at a scratch database under ``root`` (SQLite unless ``db_url`` is given)."""
    return Settings(
        db_url=db_url or f"sqlite+aiosqlite:///{root}/perf.db",
        raw_dir=root / "raw",
        geo_dir=GEO,
    )


async def _ingest_usgs_iv(settings: Settings) -> None:
    """The instantaneous-values ingest the P3 module has no reason to run, against its fixture.

    Imported inside the function, not at module scope: `cascade_api` may not import a provider
    adapter (the import-linter contract), and while this is a test module and not the API, keeping
    provider imports local to the one function that needs them costs nothing and keeps the import
    graph of anything that imports this harness honest.
    """
    import httpx
    import respx
    from cascade_providers_usgs.jobs import run_fetch_iv

    rt = Runtime.build(settings, fetcher=_fetcher(settings.raw_dir, T_USGS_IV), clock=lambda: T_USGS_IV)
    try:
        with respx.mock:
            respx.get(USGS_IV_URL).mock(
                return_value=httpx.Response(
                    200,
                    content=(FIXTURES / "usgs" / "valid.json").read_bytes(),
                    headers={"content-type": "application/json"},
                )
            )
            async with rt.sessions() as s:
                await run_fetch_iv(s, _fetcher(settings.raw_dir, T_USGS_IV))
                await s.commit()
    finally:
        await rt.engine.dispose()


def _fetcher(raw_dir: Path, clock: datetime) -> ArchivingFetcher:
    return ArchivingFetcher(store=LocalFilesystemStore(raw_dir), user_agent="CascadiaPapsukkal/0.1 (perf)", clock=lambda: clock)


async def _ingest_all(settings: Settings) -> None:
    await _ingest_everything(settings)
    await _ingest_usgs_iv(settings)


def ingest(settings: Settings) -> Settings:
    """Seed + run every ingest job once against the checked-in payloads. Synchronous on purpose:
    the suite's fixture loop scope is per function, so this owns its own loop."""
    asyncio.run(_ingest_all(settings))
    return settings
