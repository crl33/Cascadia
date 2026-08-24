"""Offline Event Zero backfill end-to-end: tmp sqlite -> seed -> respx-mocked OGC API serving
the REAL captured pages -> backfill_site (archive-first, append-only, idempotent) -> the
valid-time-window series API and the forecast-run evolution API.

Doctrine assertions throughout (ADR-0010): every backfilled row carries quality 'backfilled'
and available_at = retrieval time; at any December 2025 as_of the rows are invisible (we did
not exist then); re-runs write zero rows."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import httpx
import pytest
import respx
from sqlalchemy import func, select

from cascade_api.main import create_app
from cascade_core.db import create_schema
from cascade_core.models import ForecastRun, ForecastValue, Observation, RawArtifact, Station
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.registry import (
    PRODUCT_NWPS_FORECAST,
    PRODUCT_NWS_FLS_CREST,
    PRODUCT_USGS_IV,
    SRC_NWPS,
    SRC_NWS_AFOS,
)
from cascade_contracts.common import CONTRACT_VERSION
from cascade_core.seed import seed_all
from cascade_core.settings import Settings
from cascade_providers_usgs.backfill import backfill_site
from cascade_providers_usgs.ogc_client import OGC_BASE_URL, build_backfill_fetcher, close_fetcher
from cascade_worker.runtime import Runtime
from tests.conftest import FIXTURES, GEO

CLOCK = datetime(2026, 8, 24, 0, 0, tzinfo=UTC)  # retrieval time: months after the event, before wall-clock "now"
START = datetime(2025, 12, 12, tzinfo=UTC)
END = datetime(2025, 12, 13, tzinfo=UTC)
CREST_T = datetime(2025, 12, 12, 8, 15, tzinfo=UTC)
SERIES = "/stations/station:usgs:12200500/series"


@pytest.fixture
async def runtime(tmp_path):
    settings = Settings(db_url=f"sqlite+aiosqlite:///{tmp_path}/cascade.db", raw_dir=tmp_path / "raw", geo_dir=GEO)
    rt = Runtime.build(settings, clock=lambda: CLOCK)
    await create_schema(rt.engine)
    async with rt.sessions() as s:
        await seed_all(s, geo_dir=settings.geo_dir, seed_file=settings.seed_file)
    yield rt
    await rt.engine.dispose()


def _mock_ogc_pages() -> None:
    """Serve the REAL captured cursor pair: register the next-URL route first so it wins."""
    p1 = (FIXTURES / "usgs_ogc/paged_12200500_p1.json").read_bytes()
    p2 = (FIXTURES / "usgs_ogc/paged_12200500_p2.json").read_bytes()
    next_url = next(link["href"] for link in json.loads(p1)["links"] if link["rel"] == "next")
    respx.get(next_url).mock(return_value=httpx.Response(200, content=p2, headers={"content-type": "application/geo+json"}))
    respx.get(OGC_BASE_URL).mock(return_value=httpx.Response(200, content=p1, headers={"content-type": "application/geo+json"}))


async def _run_backfill(rt: Runtime, fetcher, page_limit: int = 120):
    async with rt.sessions() as session:
        station = (await session.execute(select(Station).where(Station.external_id == "12200500"))).scalar_one()
        report = await backfill_site(session, fetcher, station=station, start=START, end=END, page_limit=page_limit)
        await session.commit()
    return report


@respx.mock
async def test_backfill_pagination_idempotency_and_window_api(runtime: Runtime) -> None:
    rt = runtime
    _mock_ogc_pages()
    fetcher = build_backfill_fetcher(LocalFilesystemStore(rt.settings.raw_dir), user_agent="test", api_key=None, clock=lambda: CLOCK)
    try:
        report = await _run_backfill(rt, fetcher)
        assert report.pages == 2 and report.features == 194 and report.written == 194
        assert report.skipped_identical == 0 and len(report.artifact_ids) == 2
        assert report.peaks["stage"]["value"] == 37.73 and report.peaks["stage"]["valid_time"].startswith("2025-12-12T08:15")
        assert report.peaks["flow"]["value"] == 133000.0 and report.peaks["flow"]["unit"] == "cfs"

        async with rt.sessions() as s:
            rows = (await s.execute(select(Observation))).scalars().all()
            assert len(rows) == 194
            # ADR-0010: available_at = retrieval time on every backfilled row, never Dec 2025
            assert all(row.available_at == CLOCK and row.retrieved_at == CLOCK for row in rows)
            assert all("backfilled" in row.quality for row in rows)
            assert {row.qualifier_raw for row in rows} == {"Approved"}  # §3 A/P audit trail
            assert all(row.raw_artifact_id in report.artifact_ids for row in rows)
            artifacts = (await s.execute(select(RawArtifact))).scalars().all()
            assert len(artifacts) == 2  # one RawArtifact per archived page
            assert all((rt.settings.raw_dir / a.object_key).exists() for a in artifacts)
            assert all("api.waterdata.usgs.gov" in a.request_url for a in artifacts)
            assert all(a.product_id == PRODUCT_USGS_IV for a in artifacts)

        # idempotent re-run: zero new observation rows; pages archived again (append-only record of the fetch)
        report2 = await _run_backfill(rt, fetcher)
        assert report2.written == 0 and report2.skipped_identical == 194
        async with rt.sessions() as s:
            assert (await s.execute(select(func.count()).select_from(Observation))).scalar_one() == 194
            assert (await s.execute(select(func.count()).select_from(RawArtifact))).scalar_one() == 4
    finally:
        await close_fetcher(fetcher)

    app = create_app(rt.settings, engine=rt.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        # Event Zero read: valid-time window, as_of omitted (= now) -> backfilled rows visible
        r = await c.get(SERIES, params={"variable": "stage", "start": "2025-12-12T00:00:00Z", "end": "2025-12-13T00:00:00Z"})
        assert r.status_code == 200
        series = r.json()
        assert len(series["points"]) == 97 and series["unit"] == "ft" and series["datum"] == "NGVD29"
        peak = max(series["points"], key=lambda p: p["v"])
        assert peak["v"] == 37.73 and peak["t"].startswith("2025-12-12T08:15")
        assert "backfilled" in peak["quality"]  # the flag is on every value the client renders
        assert all("backfilled" in p["quality"] for p in series["points"])
        assert series["provenance"]["product_id"] == PRODUCT_USGS_IV and "backfilled" in series["provenance"]["quality"]

        # knowledge honesty: at a December 2025 as_of the backfilled rows are UNKNOWN
        r = await c.get(SERIES, params={"variable": "stage", "start": "2025-12-12T00:00:00Z", "end": "2025-12-13T00:00:00Z", "as_of": "2025-12-15T00:00:00Z"})
        assert r.status_code == 200 and r.json()["points"] == []
        # the existing 72 h as_of scrub path is untouched (nothing within 72 h of this as_of)
        r = await c.get(SERIES, params={"variable": "stage", "as_of": "2026-08-24T13:30:00Z"})
        assert r.status_code == 200 and r.json()["points"] == []
        # input limits are explicit
        assert (await c.get(SERIES, params={"variable": "stage", "start": "2025-12-12T00:00:00Z"})).status_code == 422
        assert (await c.get(SERIES, params={"variable": "stage", "start": "2025-12-13T00:00:00Z", "end": "2025-12-12T00:00:00Z"})).status_code == 422
        assert (await c.get(SERIES, params={"variable": "stage", "start": "2025-10-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"})).status_code == 422
        assert (await c.get(SERIES, params={"variable": "stage", "start": "yesterday", "end": "2025-12-13T00:00:00Z"})).status_code == 422


async def test_forecast_runs_window_api(runtime: Runtime) -> None:
    rt = runtime
    # Two runs seeded directly (the FLS/FLW parser lands separately; this is the API contract):
    # issued in December 2025, retrieved/available only in August 2026 — the backfilled shape.
    async with rt.sessions() as s:
        art = RawArtifact(sha256="0" * 64, object_key="test/ez-fixture", product_id=PRODUCT_NWPS_FORECAST,
                          fetched_at=CLOCK, request_url="https://example.invalid/fixture", bytes=1,
                          http_status=200, content_type="application/json")
        s.add(art)
        await s.flush()
        run1 = ForecastRun(product_id=PRODUCT_NWPS_FORECAST, fp_id="fp:nwps:MVEW1",
                           issued_at=datetime(2025, 12, 9, 17, 1, tzinfo=UTC), retrieved_at=CLOCK, available_at=CLOCK,
                           issuer="NWRFC via KSEW", primary_variable="stage", unit="ft", stage_unit="ft",
                           flow_unit=None, datum="NGVD29", raw_artifact_id=art.id)
        s.add(run1)
        await s.flush()
        s.add(ForecastValue(run_id=run1.id, valid_time=datetime(2025, 12, 12, 12, 0, tzinfo=UTC), stage=36.9, flow=None))
        run2 = ForecastRun(product_id=PRODUCT_NWPS_FORECAST, fp_id="fp:nwps:MVEW1",
                           issued_at=datetime(2025, 12, 10, 1, 24, tzinfo=UTC), retrieved_at=CLOCK, available_at=CLOCK,
                           issuer="NWRFC via KSEW", primary_variable="stage", unit="ft", stage_unit="ft",
                           flow_unit=None, datum="NGVD29", raw_artifact_id=art.id, supersedes_run_id=run1.id)
        s.add(run2)
        await s.flush()
        s.add(ForecastValue(run_id=run2.id, valid_time=datetime(2025, 12, 12, 12, 0, tzinfo=UTC), stage=41.5, flow=None))
        # a third run RECONSTRUCTED from archived WFO FLS text: a different product, source and
        # artifact. Its provenance must name src:nws-afos — the whole reason identity is read from
        # the run's SourceProduct instead of hardcoded (ADR-0010; docs/DATA_DOCTRINE.md §14).
        fls_art = RawArtifact(sha256="1" * 64, object_key="test/ez-fls-fixture", product_id=PRODUCT_NWS_FLS_CREST,
                              fetched_at=CLOCK, request_url="https://example.invalid/fls", bytes=1,
                              http_status=200, content_type="text/plain")
        s.add(fls_art)
        await s.flush()
        run3 = ForecastRun(product_id=PRODUCT_NWS_FLS_CREST, fp_id="fp:nwps:MVEW1",
                           issued_at=datetime(2025, 12, 10, 23, 14, tzinfo=UTC), retrieved_at=CLOCK, available_at=CLOCK,
                           issuer="NWRFC via KSEW", primary_variable="stage", unit="ft", stage_unit="ft",
                           flow_unit=None, datum="NGVD29", raw_artifact_id=fls_art.id, supersedes_run_id=run2.id)
        s.add(run3)
        await s.flush()
        s.add(ForecastValue(run_id=run3.id, valid_time=datetime(2025, 12, 12, 12, 0, tzinfo=UTC), stage=42.3, flow=None))
        artifact_ids = {PRODUCT_NWPS_FORECAST: str(art.id), PRODUCT_NWS_FLS_CREST: str(fls_art.id)}
        await s.commit()

    app = create_app(rt.settings, engine=rt.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/forecast-points/MVEW1/runs", params={"start": "2025-12-01T00:00:00Z", "end": "2025-12-31T23:59:59Z"})
        assert r.status_code == 200
        body = r.json()
        assert body["fp_id"] == "fp:nwps:MVEW1" and len(body["items"]) == 3
        first, second, third = body["items"]
        # the forecast-evolution ordering: ascending issued_at (36.9 -> 41.5, the golden head)
        assert first["issued_at"].startswith("2025-12-09T17:01") and first["points"][0]["stage"] == 36.9
        assert second["issued_at"].startswith("2025-12-10T01:24") and second["points"][0]["stage"] == 41.5
        assert second["supersedes_run_id"] == first["run_id"]
        # backfilled surface: issued_at is FACT (Dec 2025), available_at is retrieval (Aug 2026)
        assert first["issued_at"].startswith("2025-") and first["available_at"].startswith("2026-")
        assert first["product_label"] and first["issuer"] == "NWRFC via KSEW"

        # every archived run answers the provenance question on its own (docs/DATA_DOCTRINE.md):
        # identity from the run's own SourceProduct, both knowledge times, and the bytes it was parsed from
        identity = {PRODUCT_NWPS_FORECAST: (SRC_NWPS, 86400), PRODUCT_NWS_FLS_CREST: (SRC_NWS_AFOS, 21600)}
        for item in body["items"]:
            prov = item["provenance"]
            source_id, cadence = identity[item["product_id"]]
            assert prov["source_id"] == source_id and prov["source_kind"] == "OFFICIAL_FORECAST"
            assert prov["product_id"] == item["product_id"]
            assert prov["label"] == item["product_label"]
            assert prov["issued_at"][:16] == item["issued_at"][:16] and prov["retrieved_at"].startswith("2026-")
            assert prov["raw_artifact_id"] == artifact_ids[item["product_id"]]  # the stored bytes, not a claim
            assert prov["freshness"]["expected_cadence_seconds"] == cadence

        # the reconstruction is never laundered into an NWPS forecast: a run parsed from archived
        # WFO text names its own source and says "reconstructed" in the label it carries
        assert third["product_id"] == PRODUCT_NWS_FLS_CREST
        assert third["provenance"]["source_id"] == SRC_NWS_AFOS != first["provenance"]["source_id"]
        assert "reconstructed" in third["provenance"]["label"]
        assert third["provenance"]["raw_artifact_id"] != first["provenance"]["raw_artifact_id"]

        # freshness is computed at READ time against the knowledge clock, not stored
        r = await c.get("/forecast-points/MVEW1/runs",
                        params={"start": "2025-12-01T00:00:00Z", "end": "2025-12-31T23:59:59Z", "as_of": "2026-08-24T12:00:00Z"})
        assert r.status_code == 200
        fresh = r.json()["items"][0]["provenance"]["freshness"]
        assert fresh["state"] == "stale" and fresh["age_seconds"] > 86400 + 64800  # issued Dec 2025, read Aug 2026

        # knowledge honesty: at a December 2025 as_of the reconstructed runs are invisible
        r = await c.get("/forecast-points/MVEW1/runs",
                        params={"start": "2025-12-01T00:00:00Z", "end": "2025-12-31T23:59:59Z", "as_of": "2025-12-15T00:00:00Z"})
        assert r.status_code == 200 and r.json()["items"] == []
        # a window with no runs is an honest empty list, not an error
        r = await c.get("/forecast-points/MVEW1/runs", params={"start": "2025-11-01T00:00:00Z", "end": "2025-11-30T00:00:00Z"})
        assert r.status_code == 200 and r.json()["items"] == []
        # limits and identity
        assert (await c.get("/forecast-points/MVEW1/runs", params={"start": "2025-12-01T00:00:00Z"})).status_code == 422
        assert (await c.get("/forecast-points/MVEW1/runs", params={"start": "2025-10-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"})).status_code == 422
        assert (await c.get("/forecast-points/ZZZW9/runs", params={"start": "2025-12-01T00:00:00Z", "end": "2025-12-31T00:00:00Z"})).status_code == 404


async def test_system_version_reports_the_deployed_revision(runtime: Runtime) -> None:
    """A running build states which revision it is, or admits it does not know.

    Production must be checkable against the repository (RUNBOOK-deploy §reconciliation); a build
    deployed without a stamp answers "unknown", which is the honest answer and a visible defect
    rather than a silent one.
    """
    from dataclasses import replace

    app = create_app(replace(runtime.settings, git_revision="df3a4fd413019c3cc432df59f20587153b3e8035"), engine=runtime.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        body = (await c.get("/system/version")).json()
        assert body["revision"] == "df3a4fd413019c3cc432df59f20587153b3e8035"
        assert body["contract_version"] == CONTRACT_VERSION
        assert "usgs_api_key" not in str(body).lower() and len(body) == 2  # identity only, never an env dump

    unstamped = create_app(replace(runtime.settings, git_revision=None), engine=runtime.engine)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=unstamped), base_url="http://test") as c:
        assert (await c.get("/system/version")).json()["revision"] == "unknown"
