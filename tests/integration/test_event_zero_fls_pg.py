"""PostgreSQL-gated Event Zero T3 loader test (marker: pg; offline suite unaffected).

Scratch database migrated via the real Alembic chain (same pattern as
test_pg_migration.py), seeded, then the archived December 2025 fixture products are
loaded through cascade_providers_nwps.afos_jobs.load_crest_products with raw artifacts
written first (archive-before-parse). Asserts the byte-derived MVEW1 golden chain of
tests/unit/test_nws_afos.py lands as 12 supersession-chained ForecastRun rows whose
available_at is the 2026 retrieval time (ADR-0010: never the 2025 issuance time),
plus the flow-defined AUBW1 run and the refused missing-crest-time RNTW1 segment.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.pool import NullPool

from cascade_core.db import make_engine, make_session_factory
from cascade_core.models import ForecastRun, ForecastValue, RawArtifact
from cascade_core.objectstore import sha256_hex
from cascade_core.registry import PRODUCT_NWS_FLS_CREST
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from cascade_providers_nwps.afos_jobs import (
    AfosLoadReport,
    forecast_points_by_lid,
    load_crest_products,
)
from tests.conftest import FIXTURES, GEO
from tests.unit.test_nws_afos import GOLDEN

PG_URL = os.environ.get("CASCADE_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not PG_URL, reason="CASCADE_TEST_PG_URL not set"),
]

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "infra" / "migrations" / "alembic.ini"
RETRIEVED = datetime(2026, 8, 24, 13, 0, tzinfo=UTC)  # backfill retrieval clock (2026)
EXTRA = ("202512091736-KSEW-WGUS46-FLWSEW.txt", "202512160055-KSEW-WGUS86-FLSSEW.txt")


def _issued_at(fname: str) -> datetime:
    # Fixture names carry the IEM product id; its minute stamp equals the listing
    # 'entered' transmission time for every fixture (manifest.yaml documents each).
    return datetime.strptime(fname[:12], "%Y%m%d%H%M").replace(tzinfo=UTC)


@pytest.fixture(scope="module")
def scratch_url():
    from sqlalchemy.engine import make_url

    admin = create_engine(PG_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    name = f"cascadia_flstest_{uuid.uuid4().hex[:8]}"
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


async def _load_all(sessions, report: AfosLoadReport) -> None:
    files = sorted([g[0] for g in GOLDEN] + list(EXTRA), key=_issued_at)
    async with sessions() as session:
        fp_by_lid = await forecast_points_by_lid(session)
        for fname in files:
            data = (FIXTURES / f"nws_afos/{fname}").read_bytes()
            art = RawArtifact(
                sha256=sha256_hex(data),
                object_key=f"test/nws_afos/{fname}",
                product_id=PRODUCT_NWS_FLS_CREST,
                fetched_at=RETRIEVED,
                request_url=f"https://mesonet.agron.iastate.edu/api/1/nwstext/{fname[:-4]}",
                bytes=len(data),
                http_status=200,
                content_type="text/plain",
            )
            session.add(art)
            await session.flush()
            await load_crest_products(
                session,
                content=data,
                issued_at=_issued_at(fname),
                retrieved_at=RETRIEVED,
                raw_artifact_id=art.id,
                fp_by_lid=fp_by_lid,
                report=report,
            )
        await session.commit()


async def test_fls_backfill_reproduces_golden_chain(scratch_url: str) -> None:
    engine = make_engine(scratch_url)
    try:
        sessions = make_session_factory(engine)
        async with sessions() as session:
            await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
        report = AfosLoadReport()
        await _load_all(sessions, report)

        async with sessions() as session:
            rows = (
                await session.execute(
                    select(ForecastRun, ForecastValue)
                    .join(ForecastValue, ForecastValue.run_id == ForecastRun.id)
                    .where(
                        ForecastRun.product_id == PRODUCT_NWS_FLS_CREST,
                        ForecastRun.fp_id == "fp:nwps:MVEW1",
                    )
                    .order_by(ForecastRun.issued_at)
                )
            ).all()

        # GOLDEN: all 12 issuance times, crest values, crest time bins — exactly.
        assert [
            (r.issued_at, v.stage, v.valid_time) for r, v in rows
        ] == [(_issued_at(f), crest, ct) for f, _, _, crest, ct in GOLDEN]
        # supersedes chain per LID in issuance order; every row carries provenance and
        # ADR-0010 knowledge time: available_at = retrieval (2026), never issuance (2025).
        assert rows[0][0].supersedes_run_id is None
        for (prev, _), (run, value) in zip(rows, rows[1:], strict=False):
            assert run.supersedes_run_id == prev.id
        for run, value in rows:
            assert run.available_at == RETRIEVED and run.retrieved_at == RETRIEVED
            assert run.issued_at.year == 2025 and run.available_at > run.issued_at
            assert run.issuer == "NWRFC via KSEW" and run.raw_artifact_id is not None
            assert (run.primary_variable, run.unit, run.stage_unit, run.datum) == ("stage", "ft", "ft", "NGVD29")
            assert value.flow is None

        async with sessions() as session:
            aub = (
                await session.execute(
                    select(ForecastRun, ForecastValue)
                    .join(ForecastValue, ForecastValue.run_id == ForecastRun.id)
                    .where(
                        ForecastRun.product_id == PRODUCT_NWS_FLS_CREST,
                        ForecastRun.fp_id == "fp:nwps:AUBW1",
                        ForecastRun.issued_at == _issued_at(EXTRA[0]),
                    )
                )
            ).one()
        run, value = aub  # Green: flow-defined crest, cfs, no datum
        assert (run.primary_variable, run.unit, run.flow_unit, run.stage_unit, run.datum) == ("flow", "cfs", "cfs", None, None)
        assert value.flow == pytest.approx(12828.6) and value.stage is None

        # RNTW1 2025-12-16T00:55Z: crest value present but H-VTEC crest time all-zero ->
        # refused (a run with zero values is refusable), and named in the report.
        async with sessions() as session:
            n_rnt = (
                await session.execute(
                    select(func.count())
                    .select_from(ForecastRun)
                    .where(
                        ForecastRun.product_id == PRODUCT_NWS_FLS_CREST,
                        ForecastRun.fp_id == "fp:nwps:RNTW1",
                        ForecastRun.issued_at == _issued_at(EXTRA[1]),
                    )
                )
            ).scalar_one()
        assert n_rnt == 0
        assert ("RNTW1", "FLSSEW 160055") in report.missing_crest_time
        assert report.unknown_lids["CONW1"] > 0  # unseeded LIDs skipped, counted, never guessed

        # Idempotency: a second load writes nothing new.
        async with sessions() as session:
            before = (await session.execute(select(func.count()).select_from(ForecastRun))).scalar_one()
        report2 = AfosLoadReport()
        await _load_all(sessions, report2)
        async with sessions() as session:
            after = (await session.execute(select(func.count()).select_from(ForecastRun))).scalar_one()
        assert after == before and report2.runs_written == 0
        assert report2.skipped_existing == report.runs_written
    finally:
        await engine.dispose()
