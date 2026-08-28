"""The spike API routes. Read-only; input limits are explicit (vibesec addendum §3)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import PlainTextResponse, Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_api.events import sse_stream
from cascade_contracts import FieldGridSpec, FieldRasterState, SceneSummary
from cascade_contracts.common import CONTRACT_VERSION
from cascade_contracts.visualization import ProvenanceRef
from cascade_core.freshness import DEGRADED_MULTIPLIER, compute_freshness
from cascade_core.knowledge import as_known_at
from cascade_core.registry import (
    EXPECTED_PRODUCTS,
    JOBS,
    PRODUCT_HEFS_QUANTILES,
    PRODUCT_MRMS_QPE,
    PRODUCT_SNODAS_SWE,
    PRODUCT_USGS_IV,
    PRODUCT_WRITERS,
    PRODUCTS,
    SRC_NWPS_HEFS,
)
from cascade_core.timeutils import parse_iso, utcnow
from cascade_hydrology import agreement
from cascade_hydrology.assemble import (
    assess_point,
    basin_envelope,
    forecast_run_ref,
    resolved_source_kind,
    river_envelope,
)

router = APIRouter()

BASIN_ID = r"^basin:[a-z0-9-]+$"
LID = r"^[A-Z0-9]{3,8}$"
STATION_ID = r"^station:[a-z]+:[A-Za-z0-9._-]+$"

# --- /system/health vocabulary -----------------------------------------------------------------
# Both maps are DERIVED from cascade_core.registry.JOBS. They used to be written out here, three
# jobs of ten and the same three products, which is how `nbm.fetch_core_snowlvl` failed on every
# cycle while this endpoint answered `ok` (pg-migration-verification-2026-08-24 §P3.6 finding C).
# A hand-kept list falls behind silently; a derived one cannot. cascade_api may not import the
# worker (that would pull the provider adapters in and break the import contract), so
# tests/unit/test_job_registry.py imports the scheduler and the registry together and fails if a
# registered job is missing from the catalogue these are built from.
JOB_TO_PROVIDER: dict[str, str] = {job.name: job.provider for job in JOBS}
HEALTH_PRODUCTS: tuple[str, ...] = EXPECTED_PRODUCTS

#: A job counts as late when its last SUCCESS is older than this many cadences. Same multiplier as
#: the freshness DEGRADED rule so the two halves of the payload cannot disagree about the same
#: silence, and loose enough that one skipped cycle is not an alarm.
JOB_LATE_MULTIPLIER = DEGRADED_MULTIPLIER
#: A failing job is `down` rather than `failing` once no success is left inside this window.
JOB_RECOVERY_SECONDS = 24 * 3600

#: Job state -> the provider vocabulary the clients already know. `pending` is deliberately
#: `unknown`, not `degraded`: a job that has never run has not failed, and a fresh deployment
#: must not raise an alarm about work nothing has asked for yet.
PROVIDER_STATE_BY_JOB_STATE = {"ok": "healthy", "pending": "unknown", "late": "degraded", "failing": "degraded", "down": "down"}
#: The job states that are evidence of something being WRONG (as opposed to unknown).
ALARMING_JOB_STATES = frozenset({"late", "failing", "down"})
PROVIDER_RANK = {"healthy": 0, "unknown": 1, "degraded": 2, "down": 3}
#: Freshness states that mean data arrived and then stopped / went old — an alarm. `missing` is
#: NOT here: nothing has ever arrived, which is unknown, not broken.
ALARMING_FRESHNESS_STATES = frozenset({"stale", "degraded"})


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


def _hypsometry(request: Request) -> dict | None:
    """The startup-loaded elevation-area curves, or None — an absent input, never a crash."""
    hyps = getattr(request.app.state, "hypsometry", None)
    return hyps.basins if hyps is not None else None



def _dump(model) -> dict:
    return model.model_dump(mode="json", by_alias=True)


@router.get("/basins")
async def list_basins(request: Request) -> dict:
    geo = request.app.state.geo
    return {"items": geo.basins(), "provenance": geo.provenance()}


@router.get("/geo/rivers")
async def river_network(request: Request) -> dict:
    """The derived river network for every seed basin — cartographic, static, no as_of.

    Where the rivers ARE (OSM waterways clipped to the seeded basins, offline derivation
    `method:river-network-osm@1.0.0`); what they are DOING stays on truth-classed elements.
    404 when the fixture is absent: an empty network would read as a riverless Cascadia.
    """
    geo = request.app.state.geo
    if geo.river_network is None:
        raise HTTPException(status_code=404, detail="no river network derived in this deployment")
    return geo.river_network


@router.get("/geo/labels")
async def geo_labels(request: Request) -> dict:
    """The app-owned label set (GNIS names + editorial tiers) — cartographic, static.

    404 when the fixture was not derived for this deployment: an unlabeled world is a loud
    absence the client falls back from, never an empty document pretending the map has no
    names."""
    geo = request.app.state.geo
    if geo.labels is None:
        raise HTTPException(status_code=404, detail="no label set derived in this deployment")
    return geo.labels


@router.get("/geo/cameras")
async def geo_cameras(request: Request) -> dict:
    """The curated flood-observation cameras — static metadata; frames come from providers.

    Tiers carry their REASONS (spatial joins against the platform's own fixtures plus
    provider-stated facts), never a numeric score. 404 when no camera set was derived."""
    geo = request.app.state.geo
    if geo.cameras is None:
        raise HTTPException(status_code=404, detail="no camera set derived in this deployment")
    return geo.cameras


@router.get("/geo/flood")
async def geo_flood(request: Request) -> Response:
    """Static flood-hazard geography: FEMA regulatory zones + NLD levee centerlines.

    STATIC HAZARD register — study-vintage map geometry, never a prediction. The provenance
    block carries the honest captions, including the Skagit valley-floor data gap; a basin
    with `availability != 'covered'` draws nothing and the client states the absence."""
    geo = request.app.state.geo
    if geo.flood_gz is None:
        raise HTTPException(status_code=404, detail="no flood geography derived in this deployment")
    # Pre-compressed: ~1.3 MB over the wire instead of 7.6 MB. Every browser accepts gzip;
    # the Vary header keeps caches honest for any client that does not.
    return Response(
        content=geo.flood_gz,
        media_type="application/json",
        headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding", "Cache-Control": "public, max-age=3600"},
    )


@router.get("/basins/{basin_id}/geometry")
async def basin_geometry(request: Request, basin_id: Annotated[str, Path(pattern=BASIN_ID)], lod: Literal["state", "basin"] = "basin") -> dict:
    feature = request.app.state.geo.feature(basin_id, lod)
    if feature is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return feature


@router.get("/basins/{basin_id}/state")
async def basin_state(request: Request, session: Session, as_of: AsOf, basin_id: Annotated[str, Path(pattern=BASIN_ID)]) -> dict:
    k = as_known_at(session, as_of)
    basin = await k.basin(basin_id)
    if basin is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return _dump(await basin_envelope(k, [basin], generated_at=utcnow(), hypsometry=_hypsometry(request)))


@router.get("/viz/basins")
async def viz_basins(request: Request, session: Session, as_of: AsOf) -> dict:
    k = as_known_at(session, as_of)
    return _dump(await basin_envelope(k, await k.basins(), generated_at=utcnow(), hypsometry=_hypsometry(request)))


@router.get("/viz/rivers")
async def viz_rivers(session: Session, as_of: AsOf, basin: Annotated[str, Query(pattern=BASIN_ID)]) -> dict:
    k = as_known_at(session, as_of)
    if await k.basin(basin) is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    return _dump(await river_envelope(k, await k.forecast_points(basin), generated_at=utcnow()))


#: The field layers the API serves (ADR-0020): the whole current catalogue, each with its
#: own freshness bound and label — a daily analysis 30 h old is current in a way an hourly
#: accumulation 30 h old never is. C4 adds forecast kinds.
class _FieldLayer:
    def __init__(self, product_id: str, fld: str, window: str, kind: str, truth: str,
                 lookback: timedelta, label: str) -> None:
        self.product_id, self.field, self.window = product_id, fld, window
        self.kind, self.truth, self.lookback, self.label = kind, truth, lookback, label


FIELD_LAYERS: dict[str, _FieldLayer] = {
    "precip_observed": _FieldLayer(
        PRODUCT_MRMS_QPE, "qpe_01h", "1h", kind="observed", truth="observation",
        lookback=timedelta(hours=6),
        label="MRMS multi-sensor QPE pass 2, 1 h accumulation ending {valid:%Y-%m-%d %H:%M}Z",
    ),
    "snow_cover": _FieldLayer(
        PRODUCT_SNODAS_SWE, "swe_daily", "daily", kind="analysis", truth="authoritative_model",
        lookback=timedelta(hours=36),
        label="SNODAS modeled snow water equivalent, {valid:%Y-%m-%d %H:%M}Z snapshot — an assimilation analysis, not a gauge measurement",
    ),
}


@router.get("/viz/fields/{layer}")
async def viz_field(session: Session, as_of: AsOf, layer: Annotated[str, Path(pattern=r"^[a-z_]{1,40}$")]) -> dict:
    """The newest window raster for one observed field, known at as_of (ADR-0020, C3b).

    UNKNOWN is a 404 with the reason, never an empty raster: a client that gets 404 renders
    no field and says why, which is the honest difference from rendering a dry hour.
    """
    import base64

    entry = FIELD_LAYERS.get(layer)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"unknown field layer {layer!r}; known: {sorted(FIELD_LAYERS)}")
    k = as_known_at(session, as_of)
    row = await k.latest_field_raster(entry.product_id, entry.field, lookback=entry.lookback)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"no {layer} field within {int(entry.lookback.total_seconds() // 3600)} h of "
                "this knowledge time — nothing current to draw"
            ),
        )
    products = await k.products()
    product = products.get(entry.product_id)
    prov_key = f"field-{layer}"
    ref = ProvenanceRef(
        source_id=product.source_id if product else "src:unknown",
        source_kind=resolved_source_kind(product),
        product_id=entry.product_id,
        valid_time=row.valid_time,
        retrieved_at=row.retrieved_at,
        freshness=compute_freshness(
            expected_cadence_seconds=product.expected_cadence_seconds if product else None,
            grace_seconds=product.grace_seconds if product else None,
            valid_time=row.valid_time,
            retrieved_at=row.retrieved_at,
            now=k.as_of,
        ),
        label=(
            entry.label.format(valid=row.valid_time)
            + f", cut to the seeded window ({row.nx}x{row.ny} at {row.dlon:g} deg) and "
            f"quantized to {row.scale:g} {row.unit} steps ({row.method_id})"
        ),
        raw_artifact_id=None if row.raw_artifact_id is None else str(row.raw_artifact_id),
    )
    state = FieldRasterState(
        kind=entry.kind,
        field=entry.field,
        window=entry.window,
        valid_time=row.valid_time,
        as_of=k.as_of,
        generated_at=utcnow(),
        truth=entry.truth,
        unit=row.unit,
        spec=FieldGridSpec(lo1=row.lo1, la1=row.la1, dlon=row.dlon, dlat=row.dlat, nx=row.nx, ny=row.ny),
        scale=row.scale,
        display_max=row.max_value,
        cells_b64=base64.b64encode(row.cells).decode("ascii"),
        prov=prov_key,
        provenance_refs={prov_key: ref},
    )
    return _dump(state)


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


#: Written by cascade_providers_nwrfc.jobs; shared DATA, pinned by test (the api may not
#: import a provider adapter).
RESERVOIR_PRODUCT = "product:nwrfc-reservoir-obs"
RESERVOIR_VARIABLES = ("forebay_elevation", "storage", "inflow", "outflow")


@router.get("/basins/{basin_id}/reservoirs")
async def basin_reservoirs(session: Session, as_of: AsOf, basin_id: Annotated[str, Path(pattern=BASIN_ID)]) -> dict:
    """The basin's reservoir state known at as_of: latest observation per (dam, variable).

    Five of the six seed basins are regulated; this is the observable state of those decisions
    (HYDROLOGY §10). Values are VERBATIM — long-form units as the provider serves them, no
    vertical datum on forebay elevations because none is stated (ADR-0009), the SHEF
    type-source code in `qualifier` — and a basin with no reservoir stations answers an empty
    list, which for the Nooksack is the truth, not a gap.
    """
    k = as_known_at(session, as_of)
    basin = await k.basin(basin_id)
    if basin is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    stations = [
        st for st in await k.stations()
        if st.agency == "nwrfc" and st.basin_id == basin_id
    ]
    latest = await k.latest_observations(
        [st.id for st in stations], RESERVOIR_VARIABLES, lookback=timedelta(days=3),
        product_id=RESERVOIR_PRODUCT,  # the argmax itself is product-scoped: a newer row from
        # another product must not shadow the reservoir series (adversarial review 2026-08-28)
    )
    products = await k.products()
    product = products.get(RESERVOIR_PRODUCT)
    reservoirs = []
    refs: dict[str, dict] = {}
    for st in sorted(stations, key=lambda s: s.id):
        variables: dict[str, dict] = {}
        newest = None
        for variable in RESERVOIR_VARIABLES:
            obs = latest.get((st.id, variable))
            if obs is None or obs.product_id != RESERVOIR_PRODUCT:
                continue  # a variable this dam does not (currently) report is simply absent
            variables[variable] = {
                "value": obs.value,
                "unit": obs.unit,
                "valid_time": obs.valid_time,
                "quality": list(obs.quality or []),
                "qualifier": obs.qualifier_raw,
            }
            if newest is None or obs.valid_time > newest.valid_time:
                newest = obs
        ref_key = f"nwrfc-reservoir-{st.external_id.lower()}"
        if newest is not None:
            refs[ref_key] = _dump(ProvenanceRef(
                source_id=product.source_id if product else "src:nwrfc-web",
                source_kind=resolved_source_kind(product),
                product_id=RESERVOIR_PRODUCT,
                valid_time=newest.valid_time,
                retrieved_at=newest.retrieved_at,
                freshness=_freshness_for(product, valid_time=newest.valid_time, retrieved_at=newest.retrieved_at, now=k.as_of),
                quality=tuple(newest.quality or ()),
                label=(
                    f"{st.name} — NWRFC observed reservoir series, verbatim units. Forebay "
                    "elevations carry no vertical datum because the provider states none."
                ),
                raw_artifact_id=str(newest.raw_artifact_id),
            ))
        reservoirs.append({
            "station_id": st.id,
            "lid": st.external_id,
            "name": st.name,
            "variables": variables,
            "prov": ref_key if newest is not None else None,
        })
    return {"basin_id": basin_id, "as_of": k.as_of, "reservoirs": reservoirs, "provenance_refs": refs}


#: Written by cascade_providers_nwps.hefs_jobs; the api may not import a provider adapter
#: (import contract), so the names are shared DATA, pinned to the job's constants by test.
HEFS_QUANTILES_FEATURE = "hefs_exceedance_quantiles"
HEFS_QUANTILES_METHOD = "method:nwps-hefs-quantiles@1.0.0"


def _freshness_for(product, *, valid_time, retrieved_at, now):
    return compute_freshness(
        expected_cadence_seconds=product.expected_cadence_seconds if product else None,
        grace_seconds=product.grace_seconds if product else None,
        valid_time=valid_time,
        retrieved_at=retrieved_at,
        now=now,
    )


@router.get("/forecast-points/{lid}/hefs/latest")
async def latest_hefs_quantiles(session: Session, as_of: AsOf, lid: Annotated[str, Path(pattern=LID)]) -> dict:
    """The newest HEFS exceedance-quantile ladder known at as_of — the PROVIDER'S OWN numbers.

    DATA_DOCTRINE §9(a): a probability may be displayed when an authority issued it. These are
    NWRFC's published exceedance quantiles, stored verbatim at ingest and served verbatim here
    — never interpolated, never re-derived from the members, and never converted. The provider
    itself labels HEFS EXPERIMENTAL (not supported 24/7), so the provenance carries that
    caution alongside the MODELED source kind; `exceedance_levels` are probabilities of
    EXCEEDANCE per the provider's schema, and each row's `values` aligns with them by index.
    """
    k = as_known_at(session, as_of)
    fp = await k.forecast_point_by_lid(lid)
    if fp is None:
        raise HTTPException(status_code=404, detail="unknown forecast point")
    rows = await k.derived_features(HEFS_QUANTILES_FEATURE, fp.id, method_id=HEFS_QUANTILES_METHOD)
    if not rows:
        raise HTTPException(status_code=404, detail="no HEFS quantile cycle known at this knowledge time")
    newest = max(rows, key=lambda r: (r.issued_at or r.valid_time, r.available_at))
    doc = newest.values_json or {}
    products = await k.products()
    product = products.get(PRODUCT_HEFS_QUANTILES)
    prov = ProvenanceRef(
        source_id=product.source_id if product else SRC_NWPS_HEFS,
        source_kind=resolved_source_kind(product),
        product_id=PRODUCT_HEFS_QUANTILES,
        method_id=newest.method_id,
        issued_at=newest.issued_at,
        valid_time=newest.valid_time,
        retrieved_at=newest.computed_at,
        freshness=_freshness_for(product, valid_time=newest.issued_at, retrieved_at=newest.available_at, now=k.as_of),
        quality=tuple(newest.quality or ()),
        label=(
            "NWRFC HEFS published exceedance quantiles — the provider's own numbers, served "
            "verbatim (DATA_DOCTRINE §9(a)). HEFS is EXPERIMENTAL by the provider's own "
            "labelling: not supported 24/7 and may change without notice."
        ),
        raw_artifact_id=str(newest.raw_artifact_id) if newest.raw_artifact_id is not None else None,
    )
    return {
        "fp_id": fp.id,
        "lid": lid,
        "issued_at": newest.issued_at,
        "available_at": newest.available_at,
        "parameter_id": doc.get("parameter_id"),
        "unit": newest.unit,
        "exceedance_levels": doc.get("exceedance_levels", []),
        "rows": doc.get("rows", []),
        "note": doc.get("note"),
        "provenance": _dump(prov),
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


def _job_health(spec, last, last_ok, now: datetime) -> dict:
    """One registered job's state, with the reason in words, from its job_run history.

    Four distinctions the old three-line version could not make, each of which reads the same on a
    dashboard and means something different:

    - `pending`  — no run recorded. Not a failure: nothing has been asked of it yet.
    - `ok`       — succeeded inside its cadence.
    - `late`     — last success is older than JOB_LATE_MULTIPLIER cadences. The scheduler is
                   behind, or the cron never fired; nothing has failed, but nothing is arriving.
    - `failing`  — the last run failed and a success still stands inside JOB_RECOVERY_SECONDS.
    - `down`     — the last run failed with no recent success, or none ever.

    A run still in flight has `ok IS NULL` (`run_job` writes the row before calling the job), so
    it is not read as a failure; the job is judged on its last completed success instead.
    """
    late_after = spec.cadence_seconds * JOB_LATE_MULTIPLIER
    common = {
        "provider": spec.provider,
        "cadence_seconds": spec.cadence_seconds,
        "late_after_seconds": late_after,
        "last_run_at": last.started_at if last is not None else None,
        "last_success_at": last_ok.started_at if last_ok is not None else None,
        "last_error": None if last is None or last.ok else last.error,
    }
    age = None if last_ok is None else int((now - last_ok.started_at).total_seconds())
    if last is not None and last.ok is False:
        if last_ok is None:
            return {**common, "state": "down", "age_seconds": None, "reason": f"the last run failed and this job has never succeeded: {last.error}"}
        if age is not None and age > max(JOB_RECOVERY_SECONDS, late_after):
            return {**common, "state": "down", "age_seconds": age, "reason": f"the last run failed and the last success was {age} s ago: {last.error}"}
        return {**common, "state": "failing", "age_seconds": age, "reason": f"the last run failed: {last.error}"}
    if last_ok is not None:
        if age is not None and age > late_after:
            return {**common, "state": "late", "age_seconds": age, "reason": f"the last success started {age} s ago, more than {JOB_LATE_MULTIPLIER} cadences ({late_after} s)"}
        return {**common, "state": "ok", "age_seconds": age, "reason": None}
    if last is not None:  # a run exists but recorded no outcome: in flight, or the process died
        in_flight = int((now - last.started_at).total_seconds())
        if in_flight > late_after:
            return {**common, "state": "down", "age_seconds": None, "reason": f"a run started {in_flight} s ago never recorded an outcome and this job has never succeeded"}
        return {**common, "state": "pending", "age_seconds": None, "reason": f"a run started {in_flight} s ago has not recorded an outcome yet"}
    return {**common, "state": "pending", "age_seconds": None, "reason": "registered, never run: no job_run row exists at this knowledge time"}


@router.get("/explanations/{basin_id}/agreement")
async def agreement_explanation(session: Session, as_of: AsOf, basin_id: Annotated[str, Path(pattern=BASIN_ID)]) -> dict:
    """The structured record behind an agreement level — the target of `AgreementState.explanation_ref`.

    The panel shows one sentence; this is the long form it was reduced from: the window both
    crests were taken over, both hydrograph shapes, the band parameters WITH the sentence saying
    they are uncalibrated assumptions, and the full text of every quality flag that did not fit
    in two clauses. Recomputed at the requested knowledge time rather than stored, so the
    explanation can never describe a different reading than the one being explained.

    Structured features only — nothing here is generated prose (DATA_DOCTRINE §11).
    """
    k = as_known_at(session, as_of)
    basin = await k.basin(basin_id)
    if basin is None:
        raise HTTPException(status_code=404, detail="unknown basin")
    outlet = await k.forecast_point_by_lid(basin.outlet_fp_id.split(":")[-1]) if basin.outlet_fp_id else None
    if outlet is None:
        raise HTTPException(status_code=404, detail=f"{basin_id} has no outlet forecast point to compare forecasts at")
    products = await k.products()
    pa = await assess_point(k, outlet, basin, products)
    ag = await agreement.assess(k, outlet, thresholds=pa.thresholds)
    return {
        "basin_id": basin_id,
        "surface": "agreement",
        "as_of": k.as_of,
        "forecast_point_id": outlet.id,
        "state": ag.state.state.value,
        "reason": ag.state.reason,
        "method": ag.result.method_record,
        "quality": list(ag.result.quality),
    }


@router.get("/system/events")
async def system_events(request: Request) -> StreamingResponse:
    """Server-sent events: `{kind, available_at}` when a product's ingest advances.

    Notify-then-fetch (CINEMATIC_ROADMAP C3a): no payloads ride the stream — a client
    invalidates what `kind` feeds and refetches through the normal read path, which is the only
    read path. Replay (`as_of`) never touches this endpoint: the past does not change.
    The poller behind it runs only while at least one client is connected (events.py).
    """
    return StreamingResponse(
        sse_stream(request.app.state.events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.get("/system/metrics", response_class=PlainTextResponse)
async def metrics(session: Session, as_of: AsOf) -> str:
    """Prometheus text exposition of the health model — the SAME numbers /system/health serves.

    Deliberately a projection of `health()`, never a second computation: the M2 lesson was a
    hand-kept list knowing three jobs of ten, and a metrics endpoint with its own registry walk
    would reopen that gap the day one of them learns a job first. Gauges only; counters would
    need in-process state that a single-replica deploy loses on every push anyway.
    """
    h = await health(session, as_of)
    lines: list[str] = [
        "# HELP cascade_up 1 when the API answers; the label carries the overall status word.",
        "# TYPE cascade_up gauge",
        f'cascade_up{{status="{h["status"]}"}} 1',
        "# HELP cascade_job_age_seconds Seconds since the job last succeeded (absent before its first run).",
        "# TYPE cascade_job_age_seconds gauge",
    ]
    for name, j in sorted(h["jobs"].items()):
        if j["age_seconds"] is not None:
            lines.append(f'cascade_job_age_seconds{{job="{name}",provider="{j["provider"]}"}} {j["age_seconds"]}')
    lines += [
        "# HELP cascade_job_state 1 for the state each job is in (ok|late|failing|down|pending).",
        "# TYPE cascade_job_state gauge",
    ]
    for name, j in sorted(h["jobs"].items()):
        lines.append(f'cascade_job_state{{job="{name}",state="{j["state"]}"}} 1')
    lines += [
        "# HELP cascade_product_freshness_age_seconds Age of the product freshness anchor (absent while missing).",
        "# TYPE cascade_product_freshness_age_seconds gauge",
    ]
    for pid, f in sorted(h["freshness"].items()):
        if f["age_seconds"] is not None:
            lines.append(f'cascade_product_freshness_age_seconds{{product="{pid}"}} {f["age_seconds"]}')
    lines += [
        "# HELP cascade_product_freshness_state 1 for the state each product is in (current|partial|stale|degraded|missing|unknown).",
        "# TYPE cascade_product_freshness_state gauge",
    ]
    for pid, f in sorted(h["freshness"].items()):
        lines.append(f'cascade_product_freshness_state{{product="{pid}",state="{f["state"]}"}} 1')
    lines += [
        "# HELP cascade_config_drift 1 when a seeded product row disagrees with the registry (re-seed).",
        "# TYPE cascade_config_drift gauge",
    ]
    for pid, f in sorted(h["freshness"].items()):
        lines.append(f'cascade_config_drift{{product="{pid}"}} {1 if f["config_drift"] else 0}')
    return "\n".join(lines) + "\n"


@router.get("/system/version")
async def version(request: Request) -> dict:
    """What this running build is, so a deployment can be checked against the repository.

    `revision` prefers the platform-attested commit (RAILWAY_GIT_COMMIT_SHA, injected by the
    GitHub-linked auto-deploy for the commit it actually built) over the manual stamp
    (CASCADE_GIT_REVISION, the only identity a workdir `railway up` has), and is UNKNOWN when a
    build carries neither — which is itself the answer worth having: an unidentifiable build is
    exactly the state this endpoint exists to make visible. No secrets, no environment dump;
    identity only.
    """
    settings = request.app.state.settings
    return {
        "revision": settings.git_revision or "unknown",
        "contract_version": CONTRACT_VERSION,
    }


#: What `cascade_core.registry` DECLARES for each product's freshness bounds, so `/system/health`
#: can notice when the seeded `source_product` row no longer matches. Built from the registry
#: rather than restated, so the two cannot drift the way the row and the registry did.
_DECLARED_PRODUCT_CONFIG: dict[str, dict[str, object]] = {
    str(p["id"]): {
        "expected_cadence_seconds": p.get("expected_cadence_seconds"),
        "grace_seconds": p.get("grace_seconds"),
    }
    for p in PRODUCTS
}


@router.get("/system/health")
async def health(session: Session, as_of: AsOf) -> dict:
    """Every registered job and every expected product, or the reason there is nothing to say.

    Derived from `cascade_core.registry.JOBS` and its product sets, never from a list kept here.
    The list kept here knew about three jobs of ten, which is precisely how `nbm.fetch_core_snowlvl`
    failed on every single cycle while this endpoint answered `status: ok`
    (pg-migration-verification-2026-08-24 §P3.6 finding C).

    `status` is three-valued, because two values could not tell "nothing has run yet" from
    "something is broken" without lying in one direction or the other:

    - `degraded` — evidence of failure: a job is late, failing or down, or a product that WAS
      arriving has gone stale.
    - `unknown`  — no evidence yet: a registered job has never run, or an expected product has
      never been ingested. A fresh deployment reads `unknown`, never `degraded`, and stays there
      until the first cycle completes rather than raising an alarm nobody can act on. Every such
      gap is named in `reasons`, so `unknown` is a list of what is missing, not a shrug.
    - `ok`       — every registered job has succeeded inside its cadence and every expected
      product is current.

    Nothing here is aggregated away: `jobs` carries all ten, with a reason in words, whatever the
    summary says. `providers` keeps the pre-existing shape and vocabulary (healthy / degraded /
    down / unknown), rolled up as the worst job of that provider.
    """
    k = as_known_at(session, as_of)
    runs = await k.latest_job_runs()
    jobs: dict[str, dict] = {}
    providers: dict[str, dict] = {}
    reasons: list[str] = []
    for spec in JOBS:
        st = _job_health(spec, *runs.get(spec.name, (None, None)), now=k.as_of)
        jobs[spec.name] = st
        if st["reason"] is not None:
            reasons.append(f"{spec.name}: {st['reason']}")
        provider_state = {"state": PROVIDER_STATE_BY_JOB_STATE[st["state"]], "last_success_at": st["last_success_at"], "last_error": st["last_error"]}
        cur = providers.get(spec.provider)
        if cur is None or PROVIDER_RANK[provider_state["state"]] > PROVIDER_RANK[cur["state"]]:
            providers[spec.provider] = provider_state

    products = await k.products()
    anchors = await k.product_freshness_anchors()
    freshness: dict[str, dict] = {}
    for pid in HEALTH_PRODUCTS:
        p = products.get(pid)
        a = anchors.get(pid)
        f = compute_freshness(
            expected_cadence_seconds=p.expected_cadence_seconds if p else None,
            grace_seconds=p.grace_seconds if p else None,
            valid_time=a.valid_time if a else None,
            retrieved_at=a.retrieved_at if a else None,
            now=k.as_of,
        )
        writers = PRODUCT_WRITERS.get(pid, ())
        # A seeded row that disagrees with the registry means every freshness verdict for this
        # product is computed against a threshold NOBODY DECLARED. Seeding runs on demand, so a
        # registry edit reaches production only if someone re-seeds — and until 2026-08-27
        # nothing detected that they had not. Measured that day: `product:nwm-mr-via-nwps` was
        # raised 28800 -> 43200 s of grace in 361a8dd and production still held 28800, so the
        # endpoint had been reporting `stale` against a bound the codebase no longer declared.
        declared = _DECLARED_PRODUCT_CONFIG.get(pid)
        drift = None
        if p is not None and declared is not None:
            differs = {
                name: (getattr(p, name), want)
                for name, want in declared.items()
                if getattr(p, name) != want
            }
            if differs:
                drift = ", ".join(f"{k}: database {a} != registry {b}" for k, (a, b) in sorted(differs.items()))
        if p is None:
            reason = "registered in cascade_core.registry but not seeded in this database (no source_product row)"
        elif a is None:
            # Registered, expected, never ingested. Reported rather than dropped: an expected
            # product that never arrives is exactly the thing a shorter list would hide.
            reason = f"expected but never ingested at this knowledge time; written by {', '.join(writers)}"
        elif f.state.value in ALARMING_FRESHNESS_STATES:
            reason = f"{f.state.value}: {f.age_seconds} s old against a {p.expected_cadence_seconds} s cadence (+{p.grace_seconds} s grace)"
        else:
            reason = None
        if reason is not None:
            reasons.append(f"{pid}: {reason}")
        if drift is not None:
            reasons.append(f"{pid}: seeded configuration has drifted from the registry — {drift}; re-seed")
        freshness[pid] = {
            "age_seconds": f.age_seconds,
            "state": f.state.value,
            "expected_cadence_seconds": p.expected_cadence_seconds if p else None,
            "anchor": a.kind if a else None,
            "writers": list(writers),
            "reason": reason,
            "config_drift": drift,
        }

    alarming = (
        any(j["state"] in ALARMING_JOB_STATES for j in jobs.values())
        or any(f["state"] in ALARMING_FRESHNESS_STATES for f in freshness.values())
        # Drift is evidence of failure, not absence of evidence: the platform is measuring
        # freshness against a rule its own registry does not state.
        or any(f["config_drift"] is not None for f in freshness.values())
    )
    unknown = any(j["state"] == "pending" for j in jobs.values()) or any(f["state"] in ("missing", "unknown") for f in freshness.values())
    status = "degraded" if alarming else ("unknown" if unknown else "ok")
    return {"status": status, "as_of": k.as_of, "reasons": reasons, "jobs": jobs, "providers": providers, "freshness": freshness}
