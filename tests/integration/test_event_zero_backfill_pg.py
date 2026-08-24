"""Event Zero backfill against real PostgreSQL (marker: pg; offline suite unaffected).

Scratch database migrated via the real Alembic chain (same pattern as test_pg_migration),
seeded, then backfill_site is run against a respx-mocked OGC API serving the REAL captured
Dec-12-2025 payload. Verifies: rows route into the observation_y2025m12 partition, the golden
MVEW1 crest (EVENT_ZERO §3: 37.73 ft @ 2025-12-12T08:15Z, 133,000 cfs @ 09:00Z) is stored
exactly, every row carries quality 'backfilled' with available_at = retrieved_at, and a
re-run writes zero rows."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

PG_URL = os.environ.get("CASCADE_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not PG_URL, reason="CASCADE_TEST_PG_URL not set"),
]

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "infra" / "migrations" / "alembic.ini"
CLOCK = datetime(2026, 8, 24, 0, 0, tzinfo=UTC)
START = datetime(2025, 12, 12, tzinfo=UTC)
END = datetime(2025, 12, 13, tzinfo=UTC)


@pytest.fixture(scope="module")
def scratch_url():
    """A scratch database, migrated to head via the alembic CLI; dropped afterwards."""
    admin = create_engine(PG_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    name = f"cascadia_eztest_{uuid.uuid4().hex[:8]}"
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


@respx.mock
async def test_backfill_routes_to_dec_2025_partition_and_is_idempotent(scratch_url: str, tmp_path) -> None:
    from sqlalchemy import func, select

    from cascade_core.db import make_engine, make_session_factory
    from cascade_core.models import Observation, RawArtifact, Station
    from cascade_core.objectstore import LocalFilesystemStore
    from cascade_core.seed import seed_all
    from cascade_core.settings import SEED_FILE
    from cascade_providers_usgs.backfill import backfill_site
    from cascade_providers_usgs.ogc_client import OGC_BASE_URL, build_backfill_fetcher, close_fetcher
    from tests.conftest import FIXTURES, GEO

    body = (FIXTURES / "usgs_ogc/day_12200500.json").read_bytes()
    respx.get(OGC_BASE_URL).mock(return_value=httpx.Response(200, content=body, headers={"content-type": "application/geo+json"}))

    engine = make_engine(scratch_url)
    fetcher = build_backfill_fetcher(LocalFilesystemStore(tmp_path), user_agent="test", api_key=None, clock=lambda: CLOCK)
    try:
        sessions = make_session_factory(engine)
        async with sessions() as s:
            await seed_all(s, geo_dir=GEO, seed_file=SEED_FILE)

        async with sessions() as s:
            station = (await s.execute(select(Station).where(Station.external_id == "12200500"))).scalar_one()
            report = await backfill_site(s, fetcher, station=station, start=START, end=END)
            await s.commit()
        assert report.pages == 1 and report.written == 194 and report.skipped_identical == 0
        assert report.peaks["stage"]["value"] == 37.73 and report.peaks["flow"]["value"] == 133000.0

        async with sessions() as s:
            # partition routing: every backfilled row lives in the December 2025 partition
            routed = (await s.execute(text("SELECT DISTINCT tableoid::regclass::text FROM observation"))).scalars().all()
            assert routed == ["observation_y2025m12"]
            # doctrine: backfilled flag on every row; available_at = retrieved_at, never valid_time
            n = (await s.execute(select(func.count()).select_from(Observation))).scalar_one()
            assert n == 194
            flagged = (await s.execute(text("SELECT count(*) FROM observation WHERE quality::jsonb ? 'backfilled'"))).scalar_one()
            assert flagged == 194
            dishonest = (await s.execute(text("SELECT count(*) FROM observation WHERE available_at <> retrieved_at OR available_at < retrieved_at"))).scalar_one()
            assert dishonest == 0
            # the golden crest, exactly as EVENT_ZERO §3 records it
            stage_peak = (await s.execute(
                text("SELECT value, valid_time FROM observation WHERE variable = 'stage' ORDER BY value DESC LIMIT 1")
            )).one()
            assert stage_peak.value == pytest.approx(37.73, abs=0.005)
            assert stage_peak.valid_time == datetime(2025, 12, 12, 8, 15)  # stored naive-UTC
            flow_max = (await s.execute(
                text("SELECT max(value) FROM observation WHERE variable = 'flow'")
            )).scalar_one()
            assert flow_max == pytest.approx(133000.0, rel=0.01)
            # the series holds a 133,000 cfs plateau; §3's crest time 09:00Z is inside it
            at_crest = (await s.execute(
                text("SELECT value FROM observation WHERE variable = 'flow' AND valid_time = :t"),
                {"t": datetime(2025, 12, 12, 9, 0)},
            )).scalar_one()
            assert at_crest == pytest.approx(133000.0, rel=0.01)
            assert (await s.execute(select(func.count()).select_from(RawArtifact))).scalar_one() == 1

        # idempotent re-run: zero new observation rows (unique natural key + revision compare)
        async with sessions() as s:
            station = (await s.execute(select(Station).where(Station.external_id == "12200500"))).scalar_one()
            report2 = await backfill_site(s, fetcher, station=station, start=START, end=END)
            await s.commit()
        assert report2.written == 0 and report2.skipped_identical == 194
        async with sessions() as s:
            assert (await s.execute(select(func.count()).select_from(Observation))).scalar_one() == 194
    finally:
        await close_fetcher(fetcher)
        await engine.dispose()
