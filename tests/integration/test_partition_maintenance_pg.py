"""Partition-horizon maintenance on real PostgreSQL (marker: pg; offline suite unaffected).

Scratch database migrated to head via the alembic CLI (same pattern as test_pg_migration),
then the queue task's job function is invoked directly: the premade observation partitions
(2025-11 .. 2027-01) must extend to >= 13 months past the current month — beyond 2027-01 —
and a second invocation must be a no-op (idempotent)."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from cascade_core.db import make_engine, make_session_factory
from cascade_core.timeutils import utcnow
from cascade_worker.maintenance import month_window, run_ensure_partitions

PG_URL = os.environ.get("CASCADE_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not PG_URL, reason="CASCADE_TEST_PG_URL not set"),
]

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "infra" / "migrations" / "alembic.ini"

_PARTITIONS_SQL = text(
    "SELECT c.relname FROM pg_inherits i JOIN pg_class c ON c.oid = i.inhrelid "
    "WHERE i.inhparent = 'observation'::regclass"
)


@pytest.fixture()
def scratch_url():
    """A scratch database, migrated to head via the alembic CLI; dropped afterwards."""
    admin = create_engine(PG_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    name = f"cascadia_parttest_{uuid.uuid4().hex[:8]}"
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


async def test_task_fn_extends_partitions_beyond_premade_horizon(scratch_url: str) -> None:
    engine = make_engine(scratch_url)
    try:
        sessions = make_session_factory(engine)
        async with sessions() as session:
            created = await run_ensure_partitions(session, None)  # type: ignore[arg-type]  # fetcher unused
            await session.commit()
        assert created > 0  # today (>= 2026-08) plus 13 months always passes 2027-01

        async with engine.connect() as conn:
            rows = await conn.execute(_PARTITIONS_SQL)
            names = sorted(r[0] for r in rows if r[0] != "observation_default")
        _, horizon = month_window(utcnow().date())
        assert f"observation_y{horizon:%Y}m{horizon:%m}" in names  # current month + 13
        assert names[-1] > "observation_y2027m01"  # premade horizon extended past 2027-01

        # Idempotent: a second run creates nothing and leaves the partition set unchanged.
        async with sessions() as session:
            assert await run_ensure_partitions(session, None) == 0  # type: ignore[arg-type]
            await session.commit()
        async with engine.connect() as conn:
            rows = await conn.execute(_PARTITIONS_SQL)
            assert sorted(r[0] for r in rows if r[0] != "observation_default") == names
    finally:
        await engine.dispose()
