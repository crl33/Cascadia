"""The spike API routes. Read-only; input limits are explicit (vibesec addendum §3)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_contracts import SceneSummary
from cascade_core.freshness import compute_freshness
from cascade_core.knowledge import Knowledge, as_known_at
from cascade_core.registry import (
    PRODUCT_NWPS_FORECAST,
    PRODUCT_NWPS_THRESHOLDS,
    PRODUCT_USGS_IV,
)
from cascade_core.timeutils import parse_iso, utcnow
from cascade_hydrology.assemble import basin_envelope, forecast_run_ref, river_envelope

router = APIRouter()

BASIN_ID = r"^basin:[a-z0-9-]+$"
LID = r"^[A-Z0-9]{3,8}$"
STATION_ID = r"^station:[a-z]+:[A-Za-z0-9._-]+$"
JOB_TO_PROVIDER = {"usgs.fetch_iv": "usgs", "nwps.fetch_thresholds": "nwps", "nwps.fetch_forecast": "nwps"}
HEALTH_PRODUCTS = (PRODUCT_USGS_IV, PRODUCT_NWPS_FORECAST, PRODUCT_NWPS_THRESHOLDS)


async def get_session(request: Request):
    async with request.app.state.sessions() as session:
        yield session


def get_as_of(as_of: Annotated[str | None, Query(description="knowledge time, ISO-8601 with offset")] = None) -> datetime:
    if as_of is None:
        return utcnow()
    try:
        return parse_iso(as_of)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"as_of: {e}") from e


Session = Annotated[AsyncSession, Depends(get_session)]
AsOf = Annotated[datetime, Depends(get_as_of)]

WINDOW_MAX = timedelta(days=45)


def _parse_window(start: str | None, end: str | None) -> tuple[datetime, datetime] | None:
    """An explicit time window (both bounds or neither), length-capped (vibesec addendum §3)."""
    if start is None and end is None:
        return None
    if start is None or end is None:
        raise HTTPException(status_code=422, detail="start and end must be given together")
    try:
        lo, hi = parse_iso(start), parse_iso(end)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"window: {e}") from e
    if hi <= lo:
        raise HTTPException(status_code=422, detail="end must be after start")
    if hi - lo > WINDOW_MAX:
        raise HTTPException(status_code=422, detail=f"window longer than {WINDOW_MAX.days} days")
    return lo, hi


def _dump(model) -> dict:
    return model.model_dump(mode="json", by_alias=True)


@router.get("/basins")
async def list_basins(request: Request) -> dict:
    geo = request.app.state.geo
    return {"items": geo.basins(), "provenance": geo.provenance()}


@router.get("/basins/{basin_id}/geometry")
async def basin_geometry(request: Request, basin_id: Annotated[str, Path(pattern=BASIN_ID)], lod: Literal["state", "basin"] = "basin") -> dict:
    feature = request.app.state.geo.feature(basin_id, lod)
    if feature is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return feature


@router.get("/basins/{basin_id}/state")
async def basin_state(session: Session, as_of: AsOf, basin_id: Annotated[str, Path(pattern=BASIN_ID)]) -> dict:
    k = as_known_at(session, as_of)
    basin = await k.basin(basin_id)
    if basin is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return _dump(await basin_envelope(k, [basin], generated_at=utcnow()))


@router.get("/viz/basins")
async def viz_basins(session: Session, as_of: AsOf) -> dict:
    k = as_known_at(session, as_of)
    return _dump(await basin_envelope(k, await k.basins(), generated_at=utcnow()))


@router.get("/viz/rivers")
async def viz_rivers(session: Session, as_of: AsOf, basin: Annotated[str, Query(pattern=BASIN_ID)]) -> dict:
    k = as_known_at(session, as_of)
    if await k.basin(basin) is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return _dump(await river_envelope(k, await k.forecast_points(basin), generated_at=utcnow()))


@router.get("/forecast-points/{lid}/state")
async def forecast_point_state(session: Session, as_of: AsOf, lid: Annotated[str, Path(pattern=LID)]) -> dict:
    k = as_known_at(session, as_of)
    fp = await k.forecast_point_by_lid(lid)
    if fp is None:
        raise HTTPException(status_code=404, detail="unknown forecast point")
    return _dump(await river_envelope(k, [fp], generated_at=utcnow()))


@router.get("/forecast-points/{lid}/runs/latest")
async def latest_run(session: Session, as_of: AsOf, lid: Annotated[str, Path(pattern=LID)]) -> dict:
    """The latest official forecast run known at as_of, as issued — values are never converted.

    `primary`/`unit` name the variable the run is ISSUED on. Every point carries both columns
    because NWPS publishes a primary and a secondary series together (AUBW1 is issued on flow
    in cfs and carries stage in ft alongside), so the columns are declared per column, never
    per run: `stage_unit`/`flow_unit` are the units of `points[].stage`/`points[].flow`, and
    `stage_datum` is the gauge-zero vertical datum OF THE STAGE COLUMN ONLY — null when the
    run carries no stage column. Flow never has a datum (ADR-0009, ADR-0014).
    """
    k = as_known_at(session, as_of)
    fp = await k.forecast_point_by_lid(lid)
    if fp is None:
        raise HTTPException(status_code=404, detail="unknown forecast point")
    env = await river_envelope(k, [fp], generated_at=utcnow())
    run = await k.latest_forecast_run(fp.id)
    if run is None:
        raise HTTPException(status_code=404, detail="no forecast run known at this knowledge time")
    values = await k.forecast_values(run.id)
    return {
        "run_id": f"run:{run.id}",
        "issued_at": run.issued_at,
        "issuer": run.issuer,
        "primary": run.primary_variable,
        "unit": run.unit,
        "stage_unit": run.stage_unit,
        "flow_unit": run.flow_unit,
        "stage_datum": run.datum,  # the stage column's datum, never the flow column's (ADR-0014)
        "points": [{"t": v.valid_time, "stage": v.stage, "flow": v.flow} for v in values],
        "provenance": _dump(env.provenance_refs[f"nwps-forecast-{lid.lower()}"]),
    }


@router.get("/forecast-points/{lid}/runs")
async def forecast_runs_window(
    session: Session,
    as_of: AsOf,
    lid: Annotated[str, Path(pattern=LID)],
    start: Annotated[str, Query(description="issued_at window start, ISO-8601 with offset")],
    end: Annotated[str, Query(description="issued_at window end, ISO-8601 with offset")],
) -> dict:
    """Forecast-run evolution: every run known at as_of whose issued_at falls in [start, end].

    Event Zero selects runs by ISSUED time with as_of omitted (= now). Knowledge-time replay
    still holds: a reconstructed/backfilled run carries available_at = its retrieval time, so
    it is invisible at any historical as_of. The backfilled surface is the product identity
    plus available_at ≫ issued_at — both returned on every item; no flag is fabricated.

    Every item carries its own ProvenanceRef, built like the envelope's (assemble.forecast_run_ref):
    identity from the run's SourceProduct, freshness computed at read time against as_of, and the
    raw_artifact_id of the stored bytes. No displayed crest borrows its origin from a neighbour.
    """
    window = _parse_window(start, end)
    if window is None:
        raise HTTPException(status_code=422, detail="start and end are required")
    k = as_known_at(session, as_of)
    fp = await k.forecast_point_by_lid(lid)
    if fp is None:
        raise HTTPException(status_code=404, detail="unknown forecast point")
    products = await k.products()
    items = []
    for run in await k.forecast_runs(fp.id, window[0], window[1]):
        values = await k.forecast_values(run.id)
        product = products.get(run.product_id)
        items.append(
            {
                "run_id": f"run:{run.id}",
                "product_id": run.product_id,
                "product_label": product.label if product else None,
                "issued_at": run.issued_at,
                "available_at": run.available_at,
                "retrieved_at": run.retrieved_at,
                "issuer": run.issuer,
                "primary": run.primary_variable,
                "unit": run.unit,
                "stage_unit": run.stage_unit,
                "flow_unit": run.flow_unit,
                "stage_datum": run.datum,  # per /runs/latest: the stage column only (ADR-0014)
                "supersedes_run_id": None if run.supersedes_run_id is None else f"run:{run.supersedes_run_id}",
                "points": [{"t": v.valid_time, "stage": v.stage, "flow": v.flow} for v in values],
                "provenance": _dump(forecast_run_ref(run, products, now=k.as_of)),
            }
        )
    return {"lid": lid, "fp_id": fp.id, "start": window[0], "end": window[1], "items": items}


@router.get("/stations/{station_id:path}/series")
async def station_series(
    session: Session,
    as_of: AsOf,
    station_id: Annotated[str, Path()],
    variable: Literal["stage", "flow"] = "stage",
    hours: Annotated[int, Query(ge=1, le=720)] = 72,
    start: Annotated[str | None, Query(description="valid_time window start, ISO-8601 with offset; requires end, overrides hours (Event Zero: select event data by VALID time under today's knowledge)")] = None,
    end: Annotated[str | None, Query(description="valid_time window end, ISO-8601 with offset")] = None,
) -> dict:
    if not re.match(STATION_ID, station_id):
        raise HTTPException(status_code=422, detail="station_id must look like station:usgs:12200500")
    window = _parse_window(start, end)
    k = as_known_at(session, as_of)
    station = await k.station(station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="unknown station")
    if window is None:
        rows = await k.observations(station_id, variable, since=as_of - timedelta(hours=hours))
    else:
        # Valid-time selection; as_of semantics preserved: Knowledge still filters
        # available_at <= as_of, so backfilled rows stay invisible at historical as_of.
        rows = await k.observations(station_id, variable, since=window[0], until=window[1])
    products = await k.products()
    p = products[PRODUCT_USGS_IV]
    last = rows[-1] if rows else None
    unit = last.unit if last else ("ft" if variable == "stage" else "cfs")
    fresh = compute_freshness(expected_cadence_seconds=p.expected_cadence_seconds, grace_seconds=p.grace_seconds, valid_time=last.valid_time if last else None, retrieved_at=last.retrieved_at if last else None, now=as_of)
    return {
        "station_id": station_id,
        "variable": variable,
        "unit": unit,
        "datum": last.datum if last else (station.vertical_datum if variable == "stage" else None),
        "points": [{"t": o.valid_time, "v": o.value, "quality": list(o.quality)} for o in rows],
        "provenance": {
            "source_id": p.source_id,
            "source_kind": "OBSERVED" if rows else "UNKNOWN",
            "product_id": p.id,
            "valid_time": last.valid_time if last else None,
            "retrieved_at": last.retrieved_at if last else None,
            "freshness": _dump(fresh),
            "quality": list(last.quality) if last else [],
            "label": p.label,
        },
    }


@router.get("/scene/summary")
async def scene_summary(session: Session, as_of: AsOf, band: Literal["orbital", "state", "basin", "river"], basin: Annotated[str | None, Query(pattern=BASIN_ID)] = None) -> dict:
    k = as_known_at(session, as_of)
    now = utcnow()
    if band in ("orbital", "state"):
        return _dump(SceneSummary(band=band, as_of=k.as_of, basins=await basin_envelope(k, await k.basins(), generated_at=now), rivers=None))
    if basin is None:
        raise HTTPException(status_code=422, detail="basin is required for the basin and river bands")
    b = await k.basin(basin)
    if b is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return _dump(SceneSummary(band=band, as_of=k.as_of, basins=await basin_envelope(k, [b], generated_at=now), rivers=await river_envelope(k, await k.forecast_points(basin), generated_at=now)))


@router.get("/search")
async def search(session: Session, as_of: AsOf, q: Annotated[str, Query(min_length=1, max_length=64)]) -> dict:
    k = as_known_at(session, as_of)
    needle = q.strip().lower()
    items = []
    for b in await k.basins():
        if needle in b.name.lower() or needle in b.id.lower():
            items.append({"id": b.id, "kind": "basin", "name": b.name, "basin_id": b.id, "location": b.centroid})
    for fp in await k.forecast_points():
        if needle in fp.name.lower() or needle in fp.id.lower():
            items.append({"id": fp.id, "kind": "forecast_point", "name": fp.name, "basin_id": fp.basin_id, "location": [fp.lon, fp.lat]})
    for s in await k.stations():
        if needle in s.name.lower() or needle in s.id.lower():
            items.append({"id": s.id, "kind": "station", "name": s.name, "basin_id": s.basin_id, "location": [s.lon, s.lat]})
    return {"items": items[:50]}


def _provider_state(k: Knowledge, last, last_ok) -> dict:
    if last is None:
        return {"state": "unknown", "last_success_at": None, "last_error": None}
    if last.ok:
        state = "healthy"
    elif last_ok is not None and (k.as_of - last_ok.started_at).total_seconds() <= 24 * 3600:
        state = "degraded"
    else:
        state = "down"
    return {"state": state, "last_success_at": last_ok.started_at if last_ok else None, "last_error": None if last.ok else last.error}


@router.get("/system/health")
async def health(session: Session, as_of: AsOf) -> dict:
    k = as_known_at(session, as_of)
    runs = await k.latest_job_runs()
    providers: dict[str, dict] = {}
    rank = {"healthy": 0, "unknown": 1, "degraded": 2, "down": 3}
    for job, provider in JOB_TO_PROVIDER.items():
        st = _provider_state(k, *runs.get(job, (None, None)))
        cur = providers.get(provider)
        providers[provider] = st if cur is None or rank[st["state"]] > rank[cur["state"]] else cur
    products = await k.products()
    freshness = {}
    for pid in HEALTH_PRODUCTS:
        p = products.get(pid)
        v, r = await k.product_freshness_anchor(pid)
        f = compute_freshness(expected_cadence_seconds=p.expected_cadence_seconds if p else None, grace_seconds=p.grace_seconds if p else None, valid_time=v, retrieved_at=r, now=k.as_of)
        freshness[pid] = {"age_seconds": f.age_seconds, "state": f.state.value}
    ok = all(p["state"] == "healthy" for p in providers.values()) and all(f["state"] == "current" for f in freshness.values())
    return {"status": "ok" if ok else "degraded", "providers": providers, "freshness": freshness}
