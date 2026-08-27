"""Migration 0004: the seeded station time zone correction (marker: pg).

The seed fix in 603d5cb changes what a FUTURE seed writes. It does not touch a database that
already holds the legacy alias, and re-seeding is a separate manual act — so production kept
`PST8PDT` after the seed fix landed. This migration is what carries the correction along the
path the deployment already runs, and these tests are what say it is safe to put there.

What must be true, and is asserted here rather than reasoned about:

1. Rows carrying the legacy alias get the canonical name.
2. **Nothing else changes.** Not another column of the same row, not another station, not
   another table. A data migration that quietly moved a `lat` or a `tidal_class` would be far
   worse than the defect it fixes.
3. It is idempotent — the second run matches nothing.
4. It is a no-op on a database seeded after the fix, so redeploying a correct database is safe.

A scratch database is created at revision 0003, populated with the shapes production actually
had, and then upgraded. Testing it any other way — seeding first, then upgrading — would prove
nothing, because a post-fix seed writes the canonical name and the migration would match zero rows.
"""

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

PG_URL = os.environ.get("CASCADE_TEST_PG_URL", "")

pytestmark = [
    pytest.mark.pg,
    pytest.mark.skipif(not PG_URL, reason="CASCADE_TEST_PG_URL not set"),
]

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "infra" / "migrations" / "alembic.ini"

LEGACY = "PST8PDT"
CANONICAL = "America/Los_Angeles"

#: The shapes production actually had, plus the ones that must be left alone. `basin_id` is
#: nullable, so these need no basin rows and the fixture stays about the one column under test.
STATIONS = (
    # (id, agency, external_id, name, lon, lat, vertical_datum, time_zone, tidal_class)
    ("station:usgs:11111111", "usgs", "11111111", "Legacy alias A", -122.1, 48.1, "NAVD88", LEGACY, "FLUVIAL"),
    ("station:usgs:22222222", "usgs", "22222222", "Legacy alias B", -121.2, 47.2, None, LEGACY, None),
    ("station:usgs:33333333", "usgs", "33333333", "Already canonical", -120.3, 46.3, "NGVD29", CANONICAL, "TIDAL"),
    ("station:usgs:44444444", "usgs", "44444444", "A different zone", -75.4, 40.4, None, "America/New_York", None),
    ("station:usgs:55555555", "usgs", "55555555", "No zone at all", -119.5, 45.5, None, None, "FLUVIAL"),
    # Lowercase is NOT the alias; an exact-match WHERE must leave it alone rather than guess.
    ("station:usgs:66666666", "usgs", "66666666", "Lookalike casing", -118.6, 44.6, None, "pst8pdt", None),
)

COLUMNS = "id, agency, external_id, name, basin_id, lon, lat, vertical_datum, time_zone, tidal_class"


def _alembic(url: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), *args],
        env=dict(os.environ, CASCADE_ALEMBIC_URL=url),
        cwd=str(ROOT), capture_output=True, text=True, timeout=300,
    )


@pytest.fixture(scope="module")
def upgraded():
    """A scratch database stopped at 0003, populated, then upgraded to head.

    Yields (url, before, after): full row snapshots either side of the upgrade.
    """
    admin = create_engine(PG_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    name = f"cascadia_tzmig_{uuid.uuid4().hex[:8]}"
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(PG_URL).set(database=name).render_as_string(hide_password=False)
    try:
        stop = _alembic(url, "upgrade", "0003")
        assert stop.returncode == 0, f"upgrade to 0003 failed:\n{stop.stdout}\n{stop.stderr}"

        engine = create_engine(url, poolclass=NullPool)
        with engine.begin() as c:
            for row in STATIONS:
                c.execute(
                    text(
                        "INSERT INTO station (id, agency, external_id, name, lon, lat,"
                        " vertical_datum, time_zone, tidal_class)"
                        " VALUES (:id, :agency, :ext, :name, :lon, :lat, :datum, :tz, :tidal)"
                    ),
                    dict(zip(("id", "agency", "ext", "name", "lon", "lat", "datum", "tz", "tidal"), row)),
                )
        with engine.connect() as c:
            before = {r[0]: r for r in c.execute(text(f"SELECT {COLUMNS} FROM station ORDER BY id"))}

        up = _alembic(url, "upgrade", "head")
        assert up.returncode == 0, f"upgrade to head failed:\n{up.stdout}\n{up.stderr}"

        with engine.connect() as c:
            after = {r[0]: r for r in c.execute(text(f"SELECT {COLUMNS} FROM station ORDER BY id"))}
        engine.dispose()
        yield url, before, after
    finally:
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def test_the_legacy_alias_becomes_the_canonical_name(upgraded) -> None:
    _, before, after = upgraded
    legacy_ids = [s[0] for s in STATIONS if s[7] == LEGACY]
    assert legacy_ids, "anti-vacuity: the fixture must contain rows the migration should change"
    for sid in legacy_ids:
        assert before[sid][8] == LEGACY
        assert after[sid][8] == CANONICAL, f"{sid} was not corrected"
    assert not [r for r in after.values() if r[8] == LEGACY]


def test_nothing_but_that_one_column_changes(upgraded) -> None:
    """The load-bearing assertion: every other value on every row is byte-identical."""
    _, before, after = upgraded
    assert set(before) == set(after), "the migration must not add or remove stations"
    tz = COLUMNS.split(", ").index("time_zone")
    for sid, old in before.items():
        new = after[sid]
        assert old[:tz] == new[:tz], f"{sid}: a column before time_zone changed"
        assert old[tz + 1 :] == new[tz + 1 :], f"{sid}: a column after time_zone changed"


def test_rows_that_did_not_carry_the_alias_are_untouched(upgraded) -> None:
    """Including a NULL zone, an unrelated zone, and a lookalike that differs only in case."""
    _, before, after = upgraded
    for sid in (s[0] for s in STATIONS if s[7] != LEGACY):
        assert before[sid] == after[sid], f"{sid} changed but carried no legacy alias"
    assert after["station:usgs:55555555"][8] is None, "a NULL zone must stay NULL, not be filled in"
    assert after["station:usgs:66666666"][8] == "pst8pdt", "matching must be exact, not case-folded"
    assert after["station:usgs:44444444"][8] == "America/New_York"


def test_a_second_run_changes_nothing(upgraded) -> None:
    """Idempotent by construction: the WHERE clause is the guard, so re-running matches nothing."""
    url, _, after = upgraded
    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.begin() as c:
            result = c.execute(
                text("UPDATE station SET time_zone = :canonical WHERE time_zone = :legacy"),
                {"canonical": CANONICAL, "legacy": LEGACY},
            )
            assert result.rowcount == 0
        with engine.connect() as c:
            again = {r[0]: r for r in c.execute(text(f"SELECT {COLUMNS} FROM station ORDER BY id"))}
        assert again == after
    finally:
        engine.dispose()


def test_no_other_table_is_touched_and_downgrade_is_a_no_op(upgraded) -> None:
    """0004 changes no schema, so `downgrade` must leave the data exactly as it is.

    Writing the alias back would recreate the defect AND produce a state the current seed can no
    longer write, since `_validate_time_zones` refuses `PST8PDT`.
    """
    url, _, after = upgraded
    engine = create_engine(url, poolclass=NullPool)
    try:
        with engine.connect() as c:
            others = {
                t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                for t in ("basin", "forecast_point", "data_source", "source_product", "derived_feature")
            }
        assert others["derived_feature"] == 0, "the fixture writes none; the migration must not either"

        down = _alembic(url, "downgrade", "0003")
        assert down.returncode == 0, f"downgrade failed:\n{down.stdout}\n{down.stderr}"
        with engine.connect() as c:
            after_down = {r[0]: r for r in c.execute(text(f"SELECT {COLUMNS} FROM station ORDER BY id"))}
            counts = {
                t: c.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                for t in ("basin", "forecast_point", "data_source", "source_product", "derived_feature")
            }
        assert after_down == after, "downgrade must not write the legacy alias back"
        assert counts == others, "downgrade must not touch any other table"
    finally:
        engine.dispose()
        _alembic(url, "upgrade", "head")
