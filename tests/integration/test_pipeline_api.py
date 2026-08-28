"""Offline end-to-end: tmp sqlite + tmp raw dir -> seed -> respx-mocked providers -> run-once ->
API via ASGI transport -> contract validation, knowledge time, idempotency, raw artifacts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

import respx
from sqlalchemy import func, select

from cascade_api.main import create_app
from cascade_contracts import ContractEnvelope, FloodCategory, SceneSummary
from cascade_core.db import create_schema
from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import ForecastRun, Observation, RawArtifact, Threshold
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.seed import seed_all
from cascade_core.settings import Settings
from cascade_providers_usgs.ogc_parser import parse_continuous
from cascade_worker.runtime import Runtime
from cascade_worker.scheduler import JOBS, run_once
from tests.conftest import FIXTURES, GEO

CLOCK = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)
LIDS = ["RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1"]

#: The jobs `_mock_providers` below actually mocks. `JOBS` also carries the six P3 ingest jobs
#: (NBM, NWM-via-NWPS, USGS statistics, AWDB), which have their own offline fixtures and tests;
#: re-mocking their payloads here would say nothing new about the API surface this file covers,
#: and running them unmocked would only assert that respx blocks unmocked hosts.
SPIKE_JOB_NAMES = ("nwps.fetch_thresholds", "nwps.fetch_forecast", "usgs.fetch_instantaneous")
#: The seeded USGS gauges the OGC transport is asked for, one request each.
OGC_SITES = ("12100490", "12113000", "12119000", "12149000", "12189500", "12200500", "12213100")
SPIKE_JOBS = tuple(job for job in JOBS if job.name in SPIKE_JOB_NAMES)


def _mock_providers(fixtures: Path, *, mvew1_stageflow: str = "stageflow_MVEW1.json") -> None:
    # The instantaneous transport is the OGC API since 2026-08-27 (see cascade_providers_usgs.jobs).
    # It is per-site, so the mock answers each gauge with a page carrying that gauge's own
    # monitoring_location_id — the job refuses a page belonging to a different river.
    def _ogc_page(request: httpx.Request) -> httpx.Response:
        site = request.url.params.get("monitoring_location_id", "").removeprefix("USGS-")
        return httpx.Response(200, content=(fixtures / f"usgs_ogc/pipeline/{site}.json").read_bytes(),
                              headers={"content-type": "application/json"})

    respx.get("https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items").mock(side_effect=_ogc_page)
    for lid in LIDS:
        respx.get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}").mock(return_value=httpx.Response(200, content=(fixtures / f"nwps/gauge_{lid}.json").read_bytes()))
        name = mvew1_stageflow if lid == "MVEW1" else f"stageflow_{lid}.json"
        respx.get(f"https://api.water.noaa.gov/nwps/v1/gauges/{lid}/stageflow").mock(return_value=httpx.Response(200, content=(fixtures / f"nwps/{name}").read_bytes()))


@pytest.fixture
async def runtime(tmp_path):
    settings = Settings(db_url=f"sqlite+aiosqlite:///{tmp_path}/cascade.db", raw_dir=tmp_path / "raw", geo_dir=GEO)
    rt = Runtime.build(settings, fetcher=ArchivingFetcher(store=LocalFilesystemStore(settings.raw_dir), user_agent=settings.user_agent, clock=lambda: CLOCK), clock=lambda: CLOCK)
    await create_schema(rt.engine)
    async with rt.sessions() as s:
        counts = await seed_all(s, geo_dir=settings.geo_dir, seed_file=settings.seed_file)
    assert counts["basins"] == 6 and counts["forecast_points"] == 6
    yield rt
    await rt.engine.dispose()


async def _count(rt: Runtime, model) -> int:
    async with rt.sessions() as s:
        return (await s.execute(select(func.count()).select_from(model))).scalar_one()


@respx.mock
async def test_pipeline_then_api(runtime: Runtime) -> None:
    rt = runtime
    _mock_providers(FIXTURES)
    results = await run_once(rt, SPIKE_JOBS)
    assert all(ok for _, ok, _, _ in results), results
    # One raw artifact per fetched payload: 6 gauges + 6 stageflows + 7 USGS gauges. The last
    # number is 7 and not 1 because the OGC API is per-site where NWIS IV answered every site in
    # one request — a real transport cost, measured and recorded in ogc_client.LIVE_WINDOW_HOURS.
    assert await _count(rt, RawArtifact) == 19
    async with rt.sessions() as s:
        for art in (await s.execute(select(RawArtifact))).scalars():
            assert (rt.settings.raw_dir / art.object_key).exists() and art.fetched_at == CLOCK
    n_obs, n_runs, n_thr = await _count(rt, Observation), await _count(rt, ForecastRun), await _count(rt, Threshold)
    # Each of the 7 seeded gauges gets its OWN real capture of the same 3 h window ending at
    # CLOCK — the like-for-like replacement of the single legacy `usgs/valid.json` batch.
    expected_obs = sum(len(parse_continuous((FIXTURES / f'usgs_ogc/pipeline/{s}.json').read_bytes()).values) for s in OGC_SITES)
    assert n_obs == expected_obs and n_runs == 6 and n_thr == 24

    # idempotency: a second run-once writes zero new observation/run/threshold rows but archives again
    results2 = await run_once(rt, SPIKE_JOBS)
    assert [(n, ok, rows) for n, ok, rows, _ in results2] == [(results2[0][0], True, 0), (results2[1][0], True, 0), (results2[2][0], True, 0)]
    assert await _count(rt, Observation) == n_obs and await _count(rt, ForecastRun) == n_runs and await _count(rt, Threshold) == n_thr
    assert await _count(rt, RawArtifact) == 38  # 19 per run; the archive row is per fetch

    app = create_app(rt.settings, engine=rt.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test", headers={"Origin": "http://localhost:5173"}) as c:
        r = await c.get("/basins/basin:skagit/state", params={"as_of": "2026-08-22T13:30:00Z"})
        assert r.status_code == 200 and r.headers["x-content-type-options"] == "nosniff" and r.headers["access-control-allow-origin"] == "http://localhost:5173"
        env = ContractEnvelope.model_validate(r.json())
        assert env.contract == "BasinVisualizationState" and len(env.items) == 1
        basin = env.items[0]
        assert basin.surfaces.hazard.official_category == FloodCategory.NONE and "below action stage 23.5 ft, NGVD29" in basin.surfaces.hazard.reason
        assert basin.surfaces.susceptibility.state == "unknown" and basin.surfaces.susceptibility.reason
        assert env.provenance_refs[basin.surfaces.hazard.official_prov].source_kind == "OFFICIAL_FORECAST"

        r = await c.get("/viz/rivers", params={"basin": "basin:skagit", "as_of": "2026-08-22T13:30:00Z"})
        env = ContractEnvelope.model_validate(r.json())
        item = env.items[0]
        assert item.id == "fp:nwps:MVEW1" and item.station_id == "station:usgs:12200500" and item.reach_id == "reach:nwm:24270288"
        assert item.thresholds.basis == "stage" and item.thresholds.datum == "NGVD29" and item.thresholds.action == 23.5
        assert item.observed.stage.unit == "ft" and item.observed.stage.datum == "NGVD29" and item.observed.flow.unit == "cfs"
        stage = sorted((v for v in parse_continuous((FIXTURES / 'usgs_ogc/pipeline/12200500.json').read_bytes()).values if v.variable == 'stage'), key=lambda v: v.time)
        assert item.observed_category == FloodCategory.NONE and item.observed.valid_time == stage[-1].time and item.observed.stage.value == float(stage[-1].raw_value)
        assert "provisional" in env.provenance_refs[item.observed.prov].quality and env.provenance_refs[item.observed.prov].freshness.state == "current"
        assert item.official_forecast.issuer == "NWRFC" and item.official_forecast.crest.unit == "ft" and item.official_forecast.points == 32
        assert item.trend is not None and item.trend.direction in ("steady", "rising", "falling")
        assert item.headroom.to_category == FloodCategory.ACTION and item.headroom.value.unit == "ft"
        assert item.topology.upstream == ("fp:nwps:CONW1",) and item.regulation.class_ == "regulated" and "reservoir:ross-lake" in item.regulation.regulated_by
        # no day-of-year percentile is ingested in this harness, so the display hint is None —
        # the renderer's cartographic fallback — never a fabricated calm
        assert item.flow_visual_intensity is None

        # Green River: official categories are FLOW in cfs; category computed from observed flow
        r = await c.get("/forecast-points/AUBW1/state", params={"as_of": "2026-08-22T13:30:00Z"})
        env = ContractEnvelope.model_validate(r.json())
        aub = env.items[0]
        assert aub.thresholds.basis == "flow" and aub.thresholds.unit == "cfs" and aub.thresholds.datum is None and aub.thresholds.action == 6000.0
        assert aub.observed.flow.unit == "cfs" and aub.observed_category == FloodCategory.NONE and "below action flow 6000 cfs" in aub.observed_category_reason
        assert aub.headroom.basis == "flow" and aub.official_forecast.crest.unit == "cfs"

        # knowledge time: before ingestion nothing is known -> UNKNOWN with reasons, never calm
        r = await c.get("/viz/rivers", params={"basin": "basin:skagit", "as_of": "2026-08-22T13:00:00Z"})
        env = ContractEnvelope.model_validate(r.json())
        early = env.items[0]
        assert early.observed is None and early.thresholds is None and early.official_forecast is None
        assert early.observed_category == FloodCategory.UNKNOWN and early.observed_category_reason
        r = await c.get("/basins/basin:skagit/state", params={"as_of": "2026-08-22T13:00:00Z"})
        env = ContractEnvelope.model_validate(r.json())
        assert env.items[0].surfaces.hazard.official_category == FloodCategory.UNKNOWN and env.provenance_refs[env.items[0].surfaces.hazard.prov].freshness.state == "missing"

        r = await c.get("/viz/basins", params={"as_of": "2026-08-22T13:30:00Z"})
        assert len(ContractEnvelope.model_validate(r.json()).items) == 6
        r = await c.get("/scene/summary", params={"band": "basin", "basin": "basin:green-duwamish", "as_of": "2026-08-22T13:30:00Z"})
        scene = SceneSummary.model_validate(r.json())
        assert scene.rivers is not None and scene.rivers.items[0].id == "fp:nwps:AUBW1"
        assert (await c.get("/scene/summary", params={"band": "orbital"})).status_code == 200
        assert (await c.get("/scene/summary", params={"band": "river"})).status_code == 422

        r = await c.get("/forecast-points/MVEW1/runs/latest", params={"as_of": "2026-08-22T13:30:00Z"})
        run = r.json()
        assert run["primary"] == "stage" and run["unit"] == "ft" and len(run["points"]) == 32 and run["provenance"]["source_kind"] == "OFFICIAL_FORECAST"
        assert run["stage_unit"] == "ft" and run["stage_datum"] == "NGVD29" and "datum" not in run
        # AUBW1 is issued on FLOW and carries a stage column alongside: the datum describes that
        # stage column, is named for it, and is never presented as the flow values' datum (ADR-0014).
        aub_run = (await c.get("/forecast-points/AUBW1/runs/latest", params={"as_of": "2026-08-22T13:30:00Z"})).json()
        assert aub_run["primary"] == "flow" and aub_run["unit"] == "cfs" and aub_run["flow_unit"] == "cfs"
        assert aub_run["stage_unit"] == "ft" and aub_run["stage_datum"] == "NGVD29" and "datum" not in aub_run
        assert all(p["stage"] is not None for p in aub_run["points"])
        r = await c.get("/stations/station:usgs:12200500/series", params={"variable": "flow", "hours": 72, "as_of": "2026-08-22T13:30:00Z"})
        series = r.json()
        sk_flow_values = [v for v in parse_continuous((FIXTURES / "usgs_ogc/pipeline/12200500.json").read_bytes()).values if v.variable == "flow"]
        assert series["unit"] == "cfs" and len(series["points"]) == len(sk_flow_values) and series["points"][-1]["quality"] == ["provisional"]
        assert (await c.get("/stations/station%3Ausgs%3A12200500/series", params={"variable": "stage"})).status_code == 200
        assert (await c.get("/stations/station:usgs:12200500/series", params={"hours": 721})).status_code == 422
        assert (await c.get("/basins/nope/state")).status_code == 422
        assert (await c.get("/viz/rivers", params={"basin": "basin:skagit", "as_of": "yesterday"})).status_code == 422

        r = await c.get("/search", params={"q": "ska"})
        assert {i["kind"] for i in r.json()["items"]} >= {"basin", "forecast_point"}
        r = await c.get("/basins")
        assert len(r.json()["items"]) == 6 and r.json()["provenance"]["source_id"] == "src:usgs-wbd"
        r = await c.get("/basins/basin:skagit/geometry", params={"lod": "state"})
        assert r.json()["type"] == "Feature" and r.json()["properties"]["provenance"]["lod"] == "state"
        r = await c.get("/system/health", params={"as_of": "2026-08-22T13:35:00Z"})
        h = r.json()
        # Health accounts for every REGISTERED job, not for the three this file happens to run.
        # The other seven have never run here, which is `unknown` — no evidence — and never
        # `degraded` (nothing failed) nor `ok` (seven jobs are unaccounted for). Before the
        # finding-C fix this read `ok` while seven jobs were invisible.
        assert h["providers"]["usgs"]["state"] == "healthy" and h["freshness"]["product:usgs-iv"]["state"] == "current"
        assert set(h["jobs"]) >= {job.name for job in JOBS}  # plus the queue-only maintenance job
        assert {h["jobs"][name]["state"] for name in SPIKE_JOB_NAMES} == {"ok"}
        assert {st["state"] for name, st in h["jobs"].items() if name not in SPIKE_JOB_NAMES} == {"pending"}
        assert h["status"] == "unknown"
        assert (await c.get("/openapi.json")).status_code == 200
        assert (await c.post("/basins")).status_code == 405


@respx.mock
async def test_forecast_supersession_and_threshold_versioning(runtime: Runtime) -> None:
    rt = runtime
    _mock_providers(FIXTURES)
    await run_once(rt, SPIKE_JOBS)
    # a later issuance arrives: a new run supersedes, the earlier run remains, and replay at the old T sees the old run
    respx.get("https://api.water.noaa.gov/nwps/v1/gauges/MVEW1/stageflow").mock(return_value=httpx.Response(200, content=(FIXTURES / "nwps/stageflow_MVEW1_later.json").read_bytes()))
    later_clock = CLOCK + timedelta(hours=1)
    rt.fetcher.clock = lambda: later_clock
    await run_once(rt, SPIKE_JOBS)
    async with rt.sessions() as s:
        runs = (await s.execute(select(ForecastRun).where(ForecastRun.fp_id == "fp:nwps:MVEW1").order_by(ForecastRun.issued_at))).scalars().all()
    assert len(runs) == 2 and runs[1].supersedes_run_id == runs[0].id
    app = create_app(rt.settings, engine=rt.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        old = (await c.get("/forecast-points/MVEW1/runs/latest", params={"as_of": "2026-08-22T13:30:00Z"})).json()
        new = (await c.get("/forecast-points/MVEW1/runs/latest", params={"as_of": "2026-08-22T14:30:00Z"})).json()
        assert old["issued_at"].startswith("2026-08-21T15:05") and new["issued_at"].startswith("2026-08-22T03:05")
        assert new["points"][0]["stage"] == pytest.approx(old["points"][0]["stage"] + 0.5)
