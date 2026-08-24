"""PostgreSQL migration + PostGIS seed integration (marker: pg; offline suite unaffected).

Creates a scratch database on the server CASCADE_TEST_PG_URL points at, runs the real
Alembic chain against it via the CLI (the same entry scripts/migrate.sh uses), seeds it
through `cascade_core.seed.seed_all`, and verifies the PostGIS surface: basin_geometry rows,
point geometries, monthly observation partitions, partition routing, and the
cascade_ensure_month_partitions fallback helper. Every test here is skipped unless
CASCADE_TEST_PG_URL is set, keeping `python -m pytest -q` SQLite-only and offline.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
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
CLOCK = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
# 15 premade monthly partitions (2025-11 .. 2027-01) + the DEFAULT partition.
EXPECTED_PARTITIONS = 16


@pytest.fixture(scope="module")
def scratch_url():
    """A scratch database, migrated to head via the alembic CLI; dropped afterwards."""
    admin = create_engine(PG_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    name = f"cascadia_migtest_{uuid.uuid4().hex[:8]}"
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


def test_migration_builds_postgis_partitioned_schema(scratch_url: str) -> None:
    eng = create_engine(scratch_url, poolclass=NullPool)
    try:
        with eng.connect() as c:
            assert c.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'postgis'")).scalar_one() == 1
            strat = c.execute(
                text("SELECT partstrat FROM pg_partitioned_table WHERE partrelid = 'observation'::regclass")
            ).scalar_one()
            assert strat == "r", "observation must be RANGE-partitioned"
            nparts = c.execute(
                text("SELECT count(*) FROM pg_inherits WHERE inhparent = 'observation'::regclass")
            ).scalar_one()
            assert nparts == EXPECTED_PARTITIONS
            geoms = {
                r.f_table_name: (r.type, r.srid)
                for r in c.execute(
                    text(
                        "SELECT f_table_name, type, srid FROM geometry_columns "
                        "WHERE f_table_name IN ('station', 'forecast_point', 'basin_geometry')"
                    )
                )
            }
            assert geoms == {
                "station": ("POINT", 4326),
                "forecast_point": ("POINT", 4326),
                "basin_geometry": ("MULTIPOLYGON", 4326),
            }
    finally:
        eng.dispose()


async def test_seed_loads_geometry_and_partitions_route(scratch_url: str) -> None:
    from cascade_core.db import make_engine, make_session_factory
    from cascade_core.models import Observation, RawArtifact
    from cascade_core.registry import PRODUCT_USGS_IV
    from cascade_core.seed import seed_all
    from cascade_core.settings import SEED_FILE
    from tests.conftest import GEO

    engine = make_engine(scratch_url)
    try:
        sessions = make_session_factory(engine)
        async with sessions() as session:
            counts = await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
        assert counts["basins"] == 6 and counts["forecast_points"] == 6
        assert counts["basin_geometries"] == 12  # 6 basins x 2 LODs

        async with sessions() as session:
            n = (await session.execute(text("SELECT count(*) FROM basin_geometry"))).scalar_one()
            assert n == 12
            well_formed = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM basin_geometry WHERE "
                        "GeometryType(geom) = 'MULTIPOLYGON' AND ST_SRID(geom) = 4326 AND NOT ST_IsEmpty(geom)"
                    )
                )
            ).scalar_one()
            assert well_formed == 12
            for table in ("station", "forecast_point"):
                pts = (
                    await session.execute(
                        text(f"SELECT count(*) FROM {table} WHERE geom IS NOT NULL")  # noqa: S608 - fixed identifiers
                    )
                ).scalar_one()
                assert pts == 6, table
            lon, lat = (
                await session.execute(
                    text("SELECT ST_X(geom), ST_Y(geom) FROM station WHERE id = 'station:usgs:12200500'")
                )
            ).one()
            assert lon == pytest.approx(-122.3342) and lat == pytest.approx(48.4453)

        # Idempotency: reseeding neither duplicates rows nor fails the upsert.
        async with sessions() as session:
            counts2 = await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
            assert counts2["basin_geometries"] == 12
            n2 = (await session.execute(text("SELECT count(*) FROM basin_geometry"))).scalar_one()
            assert n2 == 12

        # An ORM observation insert lands in the partition its valid_time selects.
        async with sessions() as session:
            art = RawArtifact(
                sha256="0" * 64, object_key="test/migration-fixture", product_id=PRODUCT_USGS_IV,
                fetched_at=CLOCK, request_url="https://example.invalid/fixture", bytes=2,
                http_status=200, content_type="application/json",
            )
            session.add(art)
            await session.flush()
            in_range = Observation(
                station_id="station:usgs:12200500", product_id=PRODUCT_USGS_IV, variable="stage",
                value=12.3, unit="ft", datum="NGVD29",
                valid_time=datetime(2025, 12, 5, 12, 0, tzinfo=UTC),
                retrieved_at=CLOCK, available_at=CLOCK, quality=[], qualifier_raw=None,
                revision_seq=0, raw_artifact_id=art.id,
            )
            out_of_range = Observation(
                station_id="station:usgs:12200500", product_id=PRODUCT_USGS_IV, variable="stage",
                value=1.0, unit="ft", datum="NGVD29",
                valid_time=datetime(2028, 2, 1, 0, 0, tzinfo=UTC),
                retrieved_at=CLOCK, available_at=CLOCK, quality=[], qualifier_raw=None,
                revision_seq=0, raw_artifact_id=art.id,
            )
            session.add_all([in_range, out_of_range])
            await session.commit()
            routed = dict(
                (
                    await session.execute(
                        text("SELECT id, tableoid::regclass::text FROM observation WHERE id IN (:a, :b)"),
                        {"a": in_range.id, "b": out_of_range.id},
                    )
                ).all()
            )
            assert routed[in_range.id] == "observation_y2025m12"
            assert routed[out_of_range.id] == "observation_default"
    finally:
        await engine.dispose()


def test_ensure_month_partitions_helper_is_idempotent(scratch_url: str) -> None:
    eng = create_engine(scratch_url, poolclass=NullPool)
    try:
        with eng.begin() as c:
            created = c.execute(
                text("SELECT cascade_ensure_month_partitions(DATE '2027-02-01', DATE '2027-03-01')")
            ).scalar_one()
            assert created == 2
            again = c.execute(
                text("SELECT cascade_ensure_month_partitions(DATE '2027-02-01', DATE '2027-03-01')")
            ).scalar_one()
            assert again == 0
    finally:
        eng.dispose()
