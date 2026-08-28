"""/system/health must see every registered job, and must tell "never run" from "failing".

The endpoint used to be driven by a three-entry map over ten registered jobs. On the live P3 run
`nbm.fetch_core_snowlvl` failed on every cycle and health answered `status: ok`
(docs/research/pg-migration-verification-2026-08-24.md §P3.6 finding C). Everything below is the
regression surface for that: coverage (every job is looked at), discrimination (a job that has never
run is not a job that failed), and honesty about products that are expected but have never arrived.

Offline: SQLite + the ASGI transport, no network (docs/TESTING.md).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import delete

from cascade_api.main import create_app
from cascade_api.routes import JOB_LATE_MULTIPLIER
from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.models import DerivedFeature, JobRun, Observation, RawArtifact
from cascade_core.registry import (
    EXPECTED_PRODUCTS,
    METADATA_ONLY_PRODUCTS,
    JOBS,
    JOBS_BY_NAME,
    PRODUCT_NBM_CORE,
    PRODUCT_USGS_IV,
)
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE, Settings
from tests.conftest import GEO

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
ALL_JOB_NAMES = tuple(job.name for job in JOBS)
#: The three jobs the old hand-written map covered. Everything else was invisible.
OLD_MAP_JOBS = ("usgs.fetch_instantaneous", "nwps.fetch_thresholds", "nwps.fetch_forecast")
#: The exact failure the live run recorded, verbatim from §P3.6.
CORE_SNOWLVL_ERROR = "NbmParseError: field_missing: core f072 carries no SNOWLVL percentile field"


@pytest.fixture
async def db(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/health.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield engine, factory
    await engine.dispose()


async def add_runs(factory, runs) -> None:
    """`runs` is (job, started_at, ok, error). `ok=None` is a run still in flight."""
    async with factory() as session:
        for job, started_at, ok, error in runs:
            session.add(JobRun(job=job, started_at=started_at, finished_at=None if ok is None else started_at, ok=ok, error=error, rows_written=0))
        await session.commit()


def succeeded(names, at: datetime):
    return [(name, at, True, None) for name in names]


async def artifact(session, product_id: str, at: datetime, tag: str = "a") -> RawArtifact:
    """The archived bytes a value row points back at (observation.raw_artifact_id is NOT NULL)."""
    art = RawArtifact(sha256=f"{tag}{product_id}".ljust(64, "0")[:64], object_key=f"test/{tag}", product_id=product_id, fetched_at=at, request_url="https://example.invalid/health", bytes=1, http_status=200, content_type="application/json", retention_class=None)
    session.add(art)
    await session.flush()
    return art


async def get_health(engine, **params) -> dict:
    app = create_app(Settings(db_url="sqlite+aiosqlite://", geo_dir=GEO), engine=engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/system/health", params={"as_of": NOW.isoformat().replace("+00:00", "Z"), **params})
        assert r.status_code == 200
        return r.json()


# --- coverage: every registered job is looked at ------------------------------------------------


async def test_health_reports_every_registered_job(db) -> None:
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    h = await get_health(engine)
    assert set(h["jobs"]) == set(ALL_JOB_NAMES)
    # eleven scheduler jobs + the queue-only partition maintenance job. The literal is the
    # guard: a job that health cannot see is exactly the blindness this file exists to prevent.
    assert len(h["jobs"]) == 17
    assert "maintenance.ensure_observation_partitions" in h["jobs"]
    # `nwps-hefs` is its own provider key, not folded into `nwps`: one upstream service can be
    # healthy while the other is down, and HEFS is the one whose outage costs irrecoverable history.
    assert set(h["providers"]) == {"usgs", "nwps", "nwps-hefs", "nbm", "nwm", "mrms", "nws-api", "wpc", "snodas", "nwrfc", "usgs-stats", "usgs-ogc", "awdb", "cascade"}


async def test_health_reports_every_expected_product(db) -> None:
    """A registered, expected product that has never been ingested stays IN the report, with a reason."""
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    h = await get_health(engine)
    assert set(h["freshness"]) == set(EXPECTED_PRODUCTS)
    core = h["freshness"][PRODUCT_NBM_CORE]
    assert core["state"] == "missing" and core["anchor"] is None
    assert "never ingested" in core["reason"] and "nbm.fetch_core_snowlvl" in core["reason"]
    assert core["writers"] == ["nbm.fetch_core_snowlvl"]


# --- finding C: the failure that used to be invisible -------------------------------------------


async def test_the_core_snowlvl_failure_is_visible(db) -> None:
    """§P3.6 exactly: the three jobs the old map knew about are green, one it did not know about
    failed on every cycle. That combination used to read `status: ok`."""
    engine, factory = db
    green = [name for name in ALL_JOB_NAMES if name != "nbm.fetch_core_snowlvl"]
    await add_runs(factory, [*succeeded(green, NOW - timedelta(minutes=1)), ("nbm.fetch_core_snowlvl", NOW - timedelta(minutes=1), False, CORE_SNOWLVL_ERROR)])
    h = await get_health(engine)
    assert all(h["jobs"][name]["state"] == "ok" for name in OLD_MAP_JOBS)
    assert h["providers"]["usgs"]["state"] == "healthy" and h["providers"]["nwps"]["state"] == "healthy"
    assert h["status"] == "degraded"  # NOT ok, which is what the old three-entry map answered
    failed = h["jobs"]["nbm.fetch_core_snowlvl"]
    assert failed["state"] == "down" and failed["last_error"] == CORE_SNOWLVL_ERROR
    assert h["providers"]["nbm"]["state"] == "down"
    assert any("nbm.fetch_core_snowlvl" in r and "SNOWLVL" in r for r in h["reasons"])


async def test_a_failing_job_degrades_status_even_when_everything_else_is_green(db) -> None:
    engine, factory = db
    for name in ALL_JOB_NAMES:
        others = [n for n in ALL_JOB_NAMES if n != name]
        await add_runs(factory, [*succeeded(others, NOW - timedelta(minutes=1)), (name, NOW - timedelta(minutes=1), False, "boom")])
        h = await get_health(engine)
        assert h["status"] == "degraded", name
        assert h["jobs"][name]["state"] in ("failing", "down"), name
        async with factory() as session:  # reset for the next job under test
            await session.execute(delete(JobRun))
            await session.commit()


# --- discrimination: never-run is not failing ---------------------------------------------------


async def test_a_fresh_deployment_is_unknown_not_degraded(db) -> None:
    """Nothing has run: no evidence, no alarm. Every gap is named rather than summarised away."""
    engine, _ = db
    h = await get_health(engine)
    assert h["status"] == "unknown"
    assert {j["state"] for j in h["jobs"].values()} == {"pending"}
    assert {p["state"] for p in h["providers"].values()} == {"unknown"}
    assert all("never run" in h["jobs"][name]["reason"] for name in ALL_JOB_NAMES)
    assert len(h["reasons"]) == len(ALL_JOB_NAMES) + len(EXPECTED_PRODUCTS)


async def test_one_never_run_job_does_not_degrade_the_others(db) -> None:
    """`usgs.build_climatology` fires on 1 January. A deployment in August must not read `degraded`
    for the eleven months before it is due."""
    engine, factory = db
    ran = [name for name in ALL_JOB_NAMES if name != "usgs.build_climatology"]
    await add_runs(factory, succeeded(ran, NOW - timedelta(minutes=1)))
    h = await get_health(engine)
    assert h["jobs"]["usgs.build_climatology"]["state"] == "pending"
    assert h["providers"]["usgs-stats"]["state"] == "unknown"
    assert h["status"] == "unknown"
    assert "down" not in {p["state"] for p in h["providers"].values()}


async def test_a_run_in_flight_is_not_read_as_a_failure(db) -> None:
    engine, factory = db
    await add_runs(factory, [*succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=2)), ("usgs.fetch_instantaneous", NOW - timedelta(seconds=5), None, None)])
    h = await get_health(engine)
    assert h["jobs"]["usgs.fetch_instantaneous"]["state"] == "ok"
    assert h["providers"]["usgs"]["state"] == "healthy"


async def test_a_first_run_still_in_flight_is_pending_not_failing(db) -> None:
    engine, factory = db
    await add_runs(factory, [("usgs.fetch_instantaneous", NOW - timedelta(seconds=5), None, None)])
    h = await get_health(engine)
    assert h["jobs"]["usgs.fetch_instantaneous"]["state"] == "pending"
    assert "has not recorded an outcome yet" in h["jobs"]["usgs.fetch_instantaneous"]["reason"]


# --- discrimination: silence is not health ------------------------------------------------------


async def test_a_job_whose_last_success_is_many_cadences_old_is_late(db) -> None:
    """A long-cadence provider is not stale five minutes after boot; a 15-minute one that last
    succeeded five hours ago is."""
    engine, factory = db
    spec = JOBS_BY_NAME["usgs.fetch_instantaneous"]
    assert spec.cadence_seconds == 900
    fresh = [name for name in ALL_JOB_NAMES if name != "usgs.fetch_instantaneous"]
    await add_runs(factory, [*succeeded(fresh, NOW - timedelta(minutes=1)), ("usgs.fetch_instantaneous", NOW - timedelta(hours=5), True, None)])
    h = await get_health(engine)
    late = h["jobs"]["usgs.fetch_instantaneous"]
    assert late["state"] == "late" and late["late_after_seconds"] == 900 * JOB_LATE_MULTIPLIER
    assert h["providers"]["usgs"]["state"] == "degraded"
    assert h["status"] == "degraded"


async def test_one_skipped_cycle_is_not_late(db) -> None:
    engine, factory = db
    fresh = [name for name in ALL_JOB_NAMES if name != "usgs.fetch_instantaneous"]
    await add_runs(factory, [*succeeded(fresh, NOW - timedelta(minutes=1)), ("usgs.fetch_instantaneous", NOW - timedelta(seconds=1800), True, None)])
    h = await get_health(engine)
    assert h["jobs"]["usgs.fetch_instantaneous"]["state"] == "ok"


async def test_a_failure_with_a_recent_success_is_failing_and_without_one_is_down(db) -> None:
    engine, factory = db
    await add_runs(factory, [("nwps.fetch_forecast", NOW - timedelta(hours=2), True, None), ("nwps.fetch_forecast", NOW - timedelta(minutes=1), False, "HTTP 503")])
    h = await get_health(engine)
    assert h["jobs"]["nwps.fetch_forecast"]["state"] == "failing"
    assert h["jobs"]["nwps.fetch_forecast"]["last_success_at"] is not None
    await add_runs(factory, [("nwps.fetch_thresholds", NOW - timedelta(days=3), True, None), ("nwps.fetch_thresholds", NOW - timedelta(minutes=1), False, "HTTP 503")])
    h = await get_health(engine)
    assert h["jobs"]["nwps.fetch_thresholds"]["state"] == "down"


# --- freshness: anchored on value rows wherever they live ---------------------------------------


async def test_freshness_is_anchored_on_the_table_the_product_actually_writes(db) -> None:
    """The old anchor knew three product ids and sent everything else to the threshold table, so
    every P3 product read `missing` no matter how much had been ingested."""
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    async with factory() as session:
        art = await artifact(session, PRODUCT_USGS_IV, NOW - timedelta(minutes=4))
        session.add(Observation(product_id=PRODUCT_USGS_IV, station_id="station:usgs:12200500", variable="stage", value=4.0, unit="ft", datum="NGVD29", valid_time=NOW - timedelta(minutes=5), retrieved_at=NOW - timedelta(minutes=4), available_at=NOW - timedelta(minutes=4), quality=["provisional"], revision_seq=0, raw_artifact_id=art.id))
        session.add(DerivedFeature(feature="basin_snow_level_p50", scope_kind="basin", scope_id="basin:skagit", window=None, valid_time=NOW + timedelta(hours=24), issued_at=NOW - timedelta(minutes=30), computed_at=NOW - timedelta(minutes=20), available_at=NOW - timedelta(minutes=20), method_id="method:basin-snow-level@1.0.0", product_id=PRODUCT_NBM_CORE, value=1500.0, unit="m", confidence_label="moderate"))
        await session.commit()
    h = await get_health(engine)
    assert h["freshness"][PRODUCT_USGS_IV]["anchor"] == "observation"
    assert h["freshness"][PRODUCT_USGS_IV]["state"] == "current"
    core = h["freshness"][PRODUCT_NBM_CORE]
    assert core["anchor"] == "derived_feature" and core["state"] == "current"
    # Anchored on the CYCLE, not on a valid_time 24 h in the future: a forecast is not fresh
    # because the thing it forecasts has not happened yet.
    assert core["age_seconds"] == 1800


async def test_a_product_that_stopped_arriving_is_degraded_not_missing(db) -> None:
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    async with factory() as session:
        old = NOW - timedelta(days=2)
        art = await artifact(session, PRODUCT_USGS_IV, old)
        session.add(Observation(product_id=PRODUCT_USGS_IV, station_id="station:usgs:12200500", variable="stage", value=4.0, unit="ft", datum="NGVD29", valid_time=old, retrieved_at=old, available_at=old, quality=["provisional"], revision_seq=0, raw_artifact_id=art.id))
        await session.commit()
    h = await get_health(engine)
    assert h["freshness"][PRODUCT_USGS_IV]["state"] in ("stale", "degraded")
    assert h["status"] == "degraded"
    assert any(PRODUCT_USGS_IV in r for r in h["reasons"])


async def test_everything_green_still_reads_ok(db) -> None:
    """`ok` remains reachable: every job succeeded inside its cadence and every expected product
    has produced VALUES. Otherwise the endpoint would just be permanently pessimistic, which is
    its own lie. (Verified live on 2026-08-25 too: a fresh database after one full ingest plus the
    queue-only partition job answered `status: ok, reasons: []` — §P3.9.)

    Every anchor here is a value row, except the one product that legitimately has none:
    `product:awdb-stations` is station metadata, is declared `METADATA_ONLY` in the registry, and
    is the only product allowed to anchor on the bytes that were fetched.
    """
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    async with factory() as session:
        for i, pid in enumerate(EXPECTED_PRODUCTS):
            if pid in METADATA_ONLY_PRODUCTS:
                session.add(RawArtifact(sha256=f"{i:064d}", object_key=f"test/{i}", product_id=pid, fetched_at=NOW - timedelta(minutes=2), request_url="https://example.invalid/health", bytes=1, http_status=200, content_type="application/json", retention_class=None))
                continue
            session.add(DerivedFeature(feature=f"health_probe_{i}", scope_kind="basin", scope_id="basin:skagit", window=None, valid_time=NOW - timedelta(minutes=2), issued_at=NOW - timedelta(minutes=2), computed_at=NOW - timedelta(minutes=2), available_at=NOW - timedelta(minutes=2), method_id="method:test-probe@1.0.0", product_id=pid, value=1.0, unit="pct", confidence_label="moderate"))
        await session.commit()
    h = await get_health(engine)
    assert h["status"] == "ok", h["reasons"]
    assert h["reasons"] == []
    assert {p["state"] for p in h["providers"].values()} == {"healthy"}
    value_anchored = {pid: f["anchor"] for pid, f in h["freshness"].items() if pid not in METADATA_ONLY_PRODUCTS}
    assert set(value_anchored.values()) == {"derived_feature"}
    assert all(h["freshness"][pid]["anchor"] == "raw_artifact" for pid in METADATA_ONLY_PRODUCTS)


async def test_bytes_alone_never_make_a_product_current(db) -> None:
    """A product that is supposed to yield values and has yielded none reads `missing`, not
    `current` — even when its bytes are on disk and freshly fetched.

    `nbm.build_grid_masks` fetches a `product:nbm-v5-core` file of its own, so on a database where
    `nbm.fetch_core_snowlvl` has NEVER succeeded there are still raw_artifact rows for that
    product. Measured live 2026-08-25 before this guard existed, `/system/health` answered
    `{"state": "current", "anchor": "raw_artifact", "reason": null}` for a product of which not one
    value had ever been produced (§P3.9). `state: current` is a claim about data; bytes that never
    parsed are not data.
    """
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    async with factory() as session:
        await artifact(session, PRODUCT_NBM_CORE, NOW - timedelta(minutes=2))
        await session.commit()
    h = await get_health(engine)
    core = h["freshness"][PRODUCT_NBM_CORE]
    assert core["state"] == "missing" and core["anchor"] is None
    assert "never ingested" in core["reason"] and "nbm.fetch_core_snowlvl" in core["reason"]
    assert h["status"] == "unknown" and any(PRODUCT_NBM_CORE in r for r in h["reasons"])


async def test_replay_before_any_ingestion_is_unknown_with_reasons(db) -> None:
    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    h = await get_health(engine, as_of="2026-01-01T00:00:00Z")
    assert h["status"] == "unknown"
    assert {j["state"] for j in h["jobs"].values()} == {"pending"}
    assert all(f["state"] == "missing" for f in h["freshness"].values())


async def test_a_threshold_that_has_not_changed_is_current_not_stale(tmp_path) -> None:
    """Valid-until-superseded: freshness is "when did we last check", not "how old is the value".

    NWS changes an official flood threshold perhaps once a year, and rows are written only on
    change, so on a healthy system the newest threshold row is months old. Anchoring on value-age
    made /system/health answer `degraded` forever — the same disease as answering `ok` on a broken
    system: a signal nobody can act on. The parse-failure hole that argument could open is closed
    by the other half of health: a parse failure fails the job, and every job is accounted for.
    """
    from datetime import timedelta

    from cascade_core.db import create_schema, make_engine, make_session_factory
    from cascade_core.knowledge import as_known_at
    from cascade_core.models import RawArtifact, Threshold
    from cascade_core.registry import PRODUCT_NWPS_THRESHOLDS, VALID_UNTIL_SUPERSEDED_PRODUCTS
    from cascade_core.timeutils import utcnow

    assert PRODUCT_NWPS_THRESHOLDS in VALID_UNTIL_SUPERSEDED_PRODUCTS
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/h.db")
    await create_schema(engine)
    now = utcnow()
    async with make_session_factory(engine)() as s:
        long_ago = now - timedelta(days=200)
        art = RawArtifact(sha256="c" * 64, object_key="t/x", product_id=PRODUCT_NWPS_THRESHOLDS,
                          fetched_at=long_ago, request_url="https://example.invalid/t", bytes=1,
                          http_status=200, content_type="application/json")
        s.add(art)
        await s.flush()
        s.add(Threshold(fp_id="fp:nwps:MVEW1", product_id=PRODUCT_NWPS_THRESHOLDS, category="action",
                        value=23.5, unit="ft", basis="stage", datum="NGVD29",
                        source_kind="OFFICIAL_FORECAST", effective_from=long_ago,
                        retrieved_at=long_ago, raw_artifact_id=art.id))
        # ...and a poll ten minutes ago that found nothing changed, so it wrote no threshold row
        s.add(RawArtifact(sha256="d" * 64, object_key="t/y", product_id=PRODUCT_NWPS_THRESHOLDS,
                          fetched_at=now - timedelta(minutes=10), request_url="https://example.invalid/t",
                          bytes=1, http_status=200, content_type="application/json"))
        await s.commit()

        anchors = await as_known_at(s, now).product_freshness_anchors()
    await engine.dispose()

    anchor = anchors[PRODUCT_NWPS_THRESHOLDS]
    # the recent CHECK is what freshness reads, while the value's own age is still 200 days
    assert anchor.retrieved_at is not None and (now - anchor.retrieved_at) < timedelta(hours=1)
    assert "raw_artifact" in anchor.kind and "threshold" in anchor.kind


async def test_a_seeded_product_row_that_drifts_from_the_registry_is_reported(db) -> None:
    """A registry edit that never reached the database is a SILENT change to what "stale" means.

    Measured 2026-08-27: `product:nwm-mr-via-nwps` had its grace raised 28800 -> 43200 s in
    commit 361a8dd, and production still held 28800 — so `/system/health` had been reporting
    `stale` against a bound the codebase no longer declared, and nothing anywhere noticed.
    Seeding runs on demand, so this cannot be fixed by seeding harder; it has to be observable.
    """
    from sqlalchemy import select

    from cascade_core.models import SourceProduct

    engine, factory = db
    await add_runs(factory, succeeded(ALL_JOB_NAMES, NOW - timedelta(minutes=1)))
    async with factory() as session:
        for i, pid in enumerate(EXPECTED_PRODUCTS):
            if pid in METADATA_ONLY_PRODUCTS:
                session.add(RawArtifact(sha256=f"{i:064d}", object_key=f"test/{i}", product_id=pid, fetched_at=NOW - timedelta(minutes=2), request_url="https://example.invalid/health", bytes=1, http_status=200, content_type="application/json", retention_class=None))
                continue
            session.add(DerivedFeature(feature=f"health_probe_{i}", scope_kind="basin", scope_id="basin:skagit", window=None, valid_time=NOW - timedelta(minutes=2), issued_at=NOW - timedelta(minutes=2), computed_at=NOW - timedelta(minutes=2), available_at=NOW - timedelta(minutes=2), method_id="method:test-probe@1.0.0", product_id=pid, value=1.0, unit="pct", confidence_label="moderate"))
        await session.commit()

    # baseline: a database seeded from the registry reports no drift anywhere
    clean = await get_health(engine)
    assert clean["status"] == "ok", clean["reasons"]
    assert all(f["config_drift"] is None for f in clean["freshness"].values())

    # now move ONE seeded row away from what the registry declares
    target = "product:nwm-mr-via-nwps"
    async with factory() as session:
        row = (await session.execute(select(SourceProduct).where(SourceProduct.id == target))).scalar_one()
        original = row.grace_seconds
        row.grace_seconds = original + 14400
        await session.commit()

    drifted = await get_health(engine)
    assert drifted["freshness"][target]["config_drift"] is not None
    assert "grace_seconds" in drifted["freshness"][target]["config_drift"]
    assert str(original) in drifted["freshness"][target]["config_drift"], "the registry's value must be named"
    assert any("drifted from the registry" in r for r in drifted["reasons"])
    # evidence of failure, not absence of evidence
    assert drifted["status"] == "degraded"
    # and it does not smear: every other product still reads clean
    assert [pid for pid, f in drifted["freshness"].items() if f["config_drift"] is not None] == [target]


async def test_a_quiet_alert_week_is_current_and_alert_rows_anchor_their_product(tmp_path) -> None:
    """The alerts product is judged by its POLL, and its own table is in the anchor union.

    Two lessons in one test. First: an empty active-alert list is a legitimate, common answer —
    zero rows through a quiet week must read `current` while polls keep landing, so the product
    is valid-until-superseded and the raw_artifact fetch anchors it even with NO value rows
    (`have is None`). Second: finding C repeated itself on 2026-08-28 — `official_alert` was
    missing from the per-table anchor union, so production health said "never ingested" over two
    correctly stored rows. The union must cover every table a product's values land in.
    """
    from datetime import timedelta

    from cascade_core.db import create_schema, make_engine, make_session_factory
    from cascade_core.knowledge import as_known_at
    from cascade_core.models import OfficialAlertRecord, RawArtifact
    from cascade_core.registry import PRODUCT_NWS_ALERTS, VALID_UNTIL_SUPERSEDED_PRODUCTS
    from cascade_core.timeutils import utcnow

    assert PRODUCT_NWS_ALERTS in VALID_UNTIL_SUPERSEDED_PRODUCTS
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/h.db")
    await create_schema(engine)
    now = utcnow()
    async with make_session_factory(engine)() as s:
        # Quiet weather: a poll five minutes ago found nothing active; no alert row exists.
        s.add(RawArtifact(sha256="e" * 64, object_key="a/x", product_id=PRODUCT_NWS_ALERTS,
                          fetched_at=now - timedelta(minutes=5), request_url="https://example.invalid/a",
                          bytes=1, http_status=200, content_type="application/geo+json"))
        await s.commit()
        quiet = (await as_known_at(s, now).product_freshness_anchors())[PRODUCT_NWS_ALERTS]
        assert quiet.kind == "raw_artifact"
        assert quiet.retrieved_at is not None and (now - quiet.retrieved_at) < timedelta(minutes=6)

        # An alert lands: its own table joins the anchor, merged with the poll.
        s.add(OfficialAlertRecord(id="urn:test.anchor.1", event="Flood Warning", status="Actual",
                                  message_type="Alert", sent=now - timedelta(hours=2),
                                  ugc=["WAC057"], basin_ids=["basin:skagit"],
                                  mapping_method_id="method:basin-ugc-mapping@1.0.0", references=[],
                                  retrieved_at=now - timedelta(minutes=4),
                                  available_at=now - timedelta(minutes=4)))
        await s.commit()
    async with make_session_factory(engine)() as s:
        merged = (await as_known_at(s, now).product_freshness_anchors())[PRODUCT_NWS_ALERTS]
    await engine.dispose()
    assert "official_alert" in merged.kind and "raw_artifact" in merged.kind


async def test_metrics_is_a_projection_of_health_never_a_second_computation(db) -> None:
    """Every job and every product in /system/health appears in /system/metrics, with the same
    states — so the two can never know different registries (the M2 /metrics item, closed the
    same way the health endpoint itself was fixed: derive, don't list)."""
    from httpx import ASGITransport, AsyncClient

    from cascade_api.main import create_app
    from cascade_core.settings import Settings

    engine, _factory = db
    app = create_app(Settings(db_url="sqlite+aiosqlite://", geo_dir=GEO), engine=engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        h = (await client.get("/system/health")).json()
        m = (await client.get("/system/metrics"))
    assert m.status_code == 200 and "text/plain" in m.headers["content-type"]
    text = m.text
    assert f'cascade_up{{status="{h["status"]}"}} 1' in text
    for name, j in h["jobs"].items():
        assert f'cascade_job_state{{job="{name}",state="{j["state"]}"}} 1' in text
    for pid, f in h["freshness"].items():
        assert f'cascade_product_freshness_state{{product="{pid}",state="{f["state"]}"}} 1' in text
    # Prometheus text discipline: every non-comment line is `name{labels} value`
    for line in text.strip().splitlines():
        if not line.startswith("#"):
            assert line.startswith("cascade_") and line.rsplit(" ", 1)[1].replace(".", "").isdigit()


async def test_valid_until_products_read_current_by_the_poll_at_the_computed_state(tmp_path) -> None:
    """The regression the anchor-only assertions let through (caught in production
    2026-08-28): keeping valid_time content-pure flipped healthy thresholds/alerts to STALE,
    because compute_freshness anchors its age on valid_time. This pins the COMPUTED STATE —
    old content + fresh poll must read `current` end to end — and pins the broker's separate
    instant: content_time stays the pure value-side clock."""
    from datetime import timedelta

    from cascade_core.db import create_schema, make_engine, make_session_factory
    from cascade_core.freshness import compute_freshness
    from cascade_core.knowledge import as_known_at
    from cascade_core.models import OfficialAlertRecord, RawArtifact
    from cascade_core.registry import PRODUCT_NWS_ALERTS
    from cascade_core.timeutils import utcnow

    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/h.db")
    await create_schema(engine)
    now = utcnow()
    async with make_session_factory(engine)() as s:
        old_content = now - timedelta(hours=16)
        s.add(OfficialAlertRecord(id="urn:vu.1", event="Air Quality Alert", status="Actual",
                                  message_type="Alert", sent=old_content, ugc=["WAC007"],
                                  basin_ids=[], mapping_method_id="m", references=[],
                                  retrieved_at=old_content, available_at=old_content))
        s.add(RawArtifact(sha256="f" * 64, object_key="a/z", product_id=PRODUCT_NWS_ALERTS,
                          fetched_at=now - timedelta(minutes=3), request_url="https://example.invalid/a",
                          bytes=1, http_status=200, content_type="application/geo+json"))
        await s.commit()
        anchor = (await as_known_at(s, now).product_freshness_anchors())[PRODUCT_NWS_ALERTS]
    await engine.dispose()

    fresh = compute_freshness(expected_cadence_seconds=300, grace_seconds=600,
                              valid_time=anchor.valid_time, retrieved_at=anchor.retrieved_at, now=now)
    assert fresh.state.value == "current", (
        "16-hour-old content behind a 3-minute-old poll is a HEALTHY valid-until product"
    )
    assert anchor.content_time is not None
    assert (now - anchor.content_time) > timedelta(hours=15), (
        "the broker's instant stays the pure content clock, not the poll"
    )


async def test_the_river_network_serves_whole_and_absent_is_a_404_not_an_empty_earth(db) -> None:
    """GET /geo/rivers: the cartographic skeleton, with its OSM attribution and HUC8-union
    caveat riding in provenance; a deployment without the derivation answers 404 — an empty
    network would read as a riverless Cascadia."""
    from httpx import ASGITransport, AsyncClient

    from cascade_api.main import create_app
    from cascade_core.settings import Settings

    engine, _factory = db
    app = create_app(Settings(db_url="sqlite+aiosqlite://", geo_dir=GEO), engine=engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/geo/rivers")
        assert r.status_code == 200
        doc = r.json()
        assert "OpenStreetMap" in doc["_provenance"]["attribution"]
        assert "HUC8-union" in doc["_provenance"]["polygon_source"]["caveat"]
        assert set(doc["basins"]) >= {"basin:skagit", "basin:nooksack", "basin:cedar"}
        skagit = doc["basins"]["basin:skagit"]["rivers"]
        assert any(riv["name"] == "Skagit River" and riv["mainstem"] for riv in skagit)
        for riv in skagit:
            assert all(len(pt) == 2 for path in riv["paths"] for pt in path)

    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as td:
        for name in ("basins_seed_state_lod.geojson", "basins_seed_basin_lod.geojson"):
            (P(td) / name).write_bytes((GEO / name).read_bytes())
        bare = create_app(Settings(db_url="sqlite+aiosqlite://", geo_dir=P(td)), engine=engine)
        async with AsyncClient(transport=ASGITransport(app=bare), base_url="http://test") as client:
            assert (await client.get("/geo/rivers")).status_code == 404


async def test_the_label_set_serves_whole_and_absent_is_a_404_not_a_nameless_earth(tmp_path) -> None:
    """/geo/labels mirrors /geo/rivers: the whole document when derived, a reasoned 404 when
    not — an empty label list would read as 'the world has no names', which is never true."""
    import httpx

    from cascade_api.main import create_app
    from cascade_core.db import create_schema, make_engine
    from cascade_core.settings import Settings
    from tests.conftest import GEO

    settings = Settings(db_url=f"sqlite+aiosqlite:///{tmp_path}/labels.db", raw_dir=tmp_path, geo_dir=GEO)
    engine = make_engine(settings.db_url)
    await create_schema(engine)
    app = create_app(settings, engine=engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/geo/labels")
        assert r.status_code == 200
        doc = r.json()
        kinds = {row["kind"] for row in doc["labels"]}
        assert {"city", "town", "river", "basin", "peak", "water"} <= kinds
        assert doc["_provenance"]["method_id"] == "method:labels-gnis@1.0.0"
        # the editorial hierarchy's anchors: a name that moved basins would be a build bug
        seattle = next(row for row in doc["labels"] if row["name"] == "Seattle")
        assert abs(seattle["lat"] - 47.606) < 0.01 and seattle["tier"] == 1

    bare = Settings(db_url=f"sqlite+aiosqlite:///{tmp_path}/labels2.db", raw_dir=tmp_path, geo_dir=tmp_path)
    # a geo dir with no fixtures at all cannot even seed basins; only the labels absence matters,
    # so copy the basin fixtures and omit labels.json
    import shutil
    for name in ("basins_seed_state_lod.geojson", "basins_seed_basin_lod.geojson"):
        shutil.copy(GEO / name, tmp_path / name)
    engine2 = make_engine(bare.db_url)
    await create_schema(engine2)
    app2 = create_app(bare, engine=engine2)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app2), base_url="http://test") as c:
        r = await c.get("/geo/labels")
        assert r.status_code == 404 and "no label set" in r.json()["detail"]
    await engine.dispose()
    await engine2.dispose()
