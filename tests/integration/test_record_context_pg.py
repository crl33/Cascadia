"""`method:streamflow-record-context@1.0.0` on real PostgreSQL (marker: pg; offline suite unaffected).

The record context is by far the largest `values_json` the platform writes — 180 KiB at the
Skagit's 86-year record, against 54 KiB for the ladder built from the same rows. SQLite stores
that as text and never complains; PostgreSQL stores it as JSONB and TOASTs it, which is a
different code path in the driver, in the round trip and in the read. This test writes one at
production scale on real PostgreSQL and reads the exact rank back out through `Knowledge`, so
"it worked in the offline suite" cannot stand in for "it works where it runs".

Offline in the sense docs/TESTING.md §3 means: the USGS payloads are the checked-in captured
bytes, served by respx. Only the database is real.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from cascade_core.db import make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher
from cascade_core.knowledge import as_known_at
from cascade_core.models import DerivedFeature
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_hydrology import susceptibility
from cascade_providers_usgs import climatology as clim
from cascade_providers_usgs import stats_jobs
from tests.conftest import FIXTURES, GEO

PG_URL = os.environ.get("CASCADE_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not PG_URL, reason="CASCADE_TEST_PG_URL not set"),
]

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "infra" / "migrations" / "alembic.ini"
STATS = FIXTURES / "usgs_stats"
NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
SAUK = "station:usgs:12189500"

DAILY_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items"
LATEST_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/latest-daily/items"
NWIS_STAT_URL = "https://waterservices.usgs.gov/nwis/stat/"


@pytest.fixture()
def scratch_url():
    """A scratch database, migrated to head via the alembic CLI; dropped afterwards."""
    admin = create_engine(PG_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    name = f"cascadia_rctest_{uuid.uuid4().hex[:8]}"
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(PG_URL).set(database=name).render_as_string(hide_password=False)
    try:
        env = dict(os.environ, CASCADE_ALEMBIC_URL=url)
        proc = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
            env=env, cwd=str(ROOT), capture_output=True, text=True, timeout=300,
        )
        assert proc.returncode == 0, f"alembic upgrade head failed:\n{proc.stdout}\n{proc.stderr}"
        yield url
    finally:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def _mock_usgs() -> None:
    """The real captured payloads. The Skagit's 86-year record answers for every gauge here:
    this test is about the round trip at that size, not about which river it came from."""
    body = (STATS / "daily_12200500.csv").read_bytes()
    respx.get(DAILY_URL).mock(
        return_value=httpx.Response(200, content=body, headers={"content-type": "text/csv; charset=utf-8"})
    )
    respx.get(NWIS_STAT_URL).mock(return_value=httpx.Response(503))  # the cross-check may be gone
    respx.get(LATEST_URL).mock(
        return_value=httpx.Response(200, content=(STATS / "latest_daily_gauges.json").read_bytes(),
                                    headers={"content-type": "application/json"})
    )


@respx.mock
async def test_a_production_sized_record_context_round_trips_through_jsonb(scratch_url, tmp_path) -> None:
    _mock_usgs()
    engine = make_engine(scratch_url)
    try:
        sessions = make_session_factory(engine)
        fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="t", clock=lambda: NOW)
        async with sessions() as session:
            await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
            await session.commit()
        async with sessions() as session:
            await stats_jobs.run_build_climatology(session, fetcher, now=NOW)
            await stats_jobs.run_fetch_daily_percentile(session, fetcher, now=NOW)
            await session.commit()

        async with sessions() as session:
            rows = list((await session.execute(
                select(DerivedFeature).where(DerivedFeature.feature == stats_jobs.RECORD_CONTEXT_FEATURE)
            )).scalars())
            assert len(rows) == 6, "one context per susceptibility gauge"
            blob = next(r for r in rows if r.scope_id == SAUK).values_json
            # the real thing, not a truncated one: 366 keys, thousands of tail values, both windows
            assert len(blob["keys"]) == 366
            assert len(blob["tail"]) > 1000
            assert set(blob["growth"]) == {"24", "48"}
            assert blob["used_rows"] > 30000
            # JSONB is unordered and re-encodes floats; the reader must survive both
            context = clim.record_context_from_values_json(blob)
            assert context.keys["12-11"].maximum > 0
            assert context.growth[24].n > 30000

            # and the READ path finds it: a crest above the ladder's ceiling gets an exact rank
            key = "12-11"
            support = blob["keys"][key]
            crest = support["max"] * 2
            reading = susceptibility.window_rank(crest, key, blob)
            assert reading.rank == 1 and reading.exceeds_record
            assert reading.previous_max == support["max"]
            assert reading.previous_max_day == date.fromisoformat(support["max_day"])
    finally:
        await engine.dispose()


@respx.mock
async def test_the_surface_reads_the_context_back_at_a_knowledge_time(scratch_url, tmp_path) -> None:
    """End to end on PostgreSQL: build, store, then assess through the knowledge clock.

    The August fixture is a quiet river, so the surface sits below `RANK_READ_EDGE` and the
    context is deliberately NOT read — that is the design, and it is asserted here so a change
    that starts reading a 180 KiB blob on every quiet day shows up as a failing test rather than
    as a slower endpoint.
    """
    _mock_usgs()
    engine = make_engine(scratch_url)
    try:
        sessions = make_session_factory(engine)
        fetcher = ArchivingFetcher(store=LocalFilesystemStore(tmp_path), user_agent="t", clock=lambda: NOW)
        async with sessions() as session:
            await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
            await session.commit()
        async with sessions() as session:
            await stats_jobs.run_build_climatology(session, fetcher, now=NOW)
            await stats_jobs.run_fetch_daily_percentile(session, fetcher, now=NOW)
            await session.commit()

        async with sessions() as session:
            k = as_known_at(session, NOW)
            products = await k.products()
            basin = await k.basin("basin:skagit")
            a = await susceptibility.assess(k, basin, products)
            state = a.hydrologic_state
            assert state is not None
            assert state.multiple is not None and state.multiple.multiple > 0
            assert state.reference is not None and state.reference.n > 0
            # quiet river: below p90 the context is not READ and no rank is invented — but the
            # absence is published with its reason rather than as a bare null, so this asserts
            # the refusal, not the silence. `of` is the ladder's own sample size, which is known
            # without reading the context.
            assert state.percentile < susceptibility.RANK_READ_EDGE
            assert state.rank is not None and state.rank.rank is None
            assert "Not read" in (state.rank.reason or "")
            assert state.rank.reason != susceptibility.NO_RECORD_CONTEXT_REASON
            assert state.rank.of >= 1 and state.rank.previous_max is None
            # every prov key the state and the changes point at resolves to a real ref
            assert state.prov in a.refs
            assert all(c.prov in a.refs for c in a.state_changes)
            # and the knowledge clock still bounds it: nothing is known before it was available
            before = as_known_at(session, NOW - timedelta(days=365))
            assert await susceptibility.assess(before, basin, products) is not None
            assert (await susceptibility.assess(before, basin, products)).hydrologic_state is None
    finally:
        await engine.dispose()
