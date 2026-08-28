"""``mrms.fetch_qpe`` — observed hourly precipitation per basin, with the covariate that
qualifies it.

A backfill on a schedule, like HEFS: each run lists the S3 day prefix, ingests every accumulation
not yet stored (bounded at 24 h back — older hours are the IEM archive's job, and a worker outage
longer than a day is an incident, not a backfill), and is idempotent per (basin, valid_time). One
missed cron costs nothing.

**Knowledge time.** ``valid_time`` is the END of the 1-h accumulation (from the key);
``available_at`` is the S3 object's ``LastModified`` — measured 57 min later — because a replay
must not know an accumulation before NODD served it. ``issued_at`` is None: nothing here is a
forecast.

**Coverage policy, set on measurement rather than caution.** On the probe file every seed basin
was 100.00 % valid — MRMS's gauge/model blending fills the BC headwaters — so full coverage is
the normal state and anything else is a signal. A basin whose valid weight drops below
``MIN_VALID_FRACTION`` gets ``value=None`` with the reason, never a mean over the part the radar
could see: a mean over 80 % of a basin is not the basin mean, and pretending otherwise is exactly
the bias the −3 sentinel exists to prevent. Small shortfalls above the threshold are flagged, not
hidden — the fractions ride in ``values_json`` either way.

**Masks are lazy and stored.** Built once per grid-definition hash from the full-resolution seed
polygons (the display-LOD 20 % overcount lesson, masks.py) into the same ``grid_mask`` table NBM
uses; a silently changed grid therefore misses its masks and this job REBUILDS from geometry
rather than aggregating with the wrong weights.
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.models import Basin, DerivedFeature, FieldRaster, GridMask
from cascade_core.registry import PRODUCT_MRMS_GAUGEINFL, PRODUCT_MRMS_QPE
from cascade_core.timeutils import utcnow
from cascade_geo.latlon import LatLonGridSpec
from cascade_geo.masks import BasinMask, build_basin_mask
from cascade_providers_mrms.client import (
    GAUGEINFL_PRODUCT_DIR,
    QPE_PRODUCT_DIR,
    S3Object,
    fetch_object,
    list_day,
    parse_listing,
)
from cascade_providers_mrms.parser import MISSING, NO_COVERAGE, parse_mrms_grib
from cascade_providers_mrms.raster import (
    FIELD_QPE,
    METHOD_RASTER,
    WindowOutsideGridError,
    cut_window,
)

log = logging.getLogger("cascade.providers.mrms")

JOB_NAME = "mrms.fetch_qpe"
CADENCE_SECONDS = 3600
#: Pass2 for hour H lands ~H+57 min (measured); :20 collects H−1 published at H:57 with margin.
CRON = "20 * * * *"

METHOD_QPE = "method:basin-qpe@1.0.0"
FEATURE_QPE = "basin_qpe_01h"
METHOD_GAUGEINFL = "method:basin-gauge-influence@1.0.0"
FEATURE_GAUGEINFL = "basin_gauge_influence_01h"

LOOKBACK = timedelta(hours=24)
#: field_raster retention (ADR-0020): the display window the timeline scrubs; the source
#: gribs stay archived, so a longer view is a backfill away, not a loss.
RASTER_RETENTION = timedelta(hours=72)
#: Below this valid-weight fraction the mean is refused. Normal state is 1.0000 (measured).
MIN_VALID_FRACTION = 0.995

INSUFFICIENT_COVERAGE = "insufficient_radar_coverage"
NO_COVERAGE_PRESENT = "radar_no_coverage_cells"
MISSING_PRESENT = "missing_cells"


class NoListingError(RuntimeError):
    """The day listing parsed to nothing on a day that should have files — retryable."""


async def _basins(session: AsyncSession) -> list[Basin]:
    return list((await session.execute(select(Basin).order_by(Basin.id))).scalars().all())


def _polygons_of(geometry: dict) -> list:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return list(geometry["coordinates"])
    if geometry["type"] == "GeometryCollection":
        out: list = []
        for sub in geometry["geometries"]:
            out.extend(_polygons_of(sub))
        return out
    return []


async def _masks_for(
    session: AsyncSession, grid: LatLonGridSpec, basins: list[Basin], geo_dir: Path
) -> dict[str, BasinMask]:
    """Load masks for this grid hash; build and store the absent ones from full-res geometry."""
    rows = (
        await session.execute(
            select(GridMask).where(GridMask.grid_definition_hash == grid.definition_hash)
        )
    ).scalars()
    masks = {r.basin_id: BasinMask(
        basin_id=r.basin_id, grid_definition_hash=r.grid_definition_hash,
        cells=tuple((int(i), float(w)) for i, w in r.cells),
        masked_area_km2=r.masked_area_km2, polygon_source=r.polygon_source,
    ) for r in rows}
    todo = [b for b in basins if b.id not in masks]
    if not todo:
        return masks
    source = geo_dir / "basins_seed_full.geojson.gz"
    features = {
        f["properties"]["id"]: f
        for f in json.loads(gzip.decompress(source.read_bytes()))["features"]
    }
    for basin in todo:
        feature = features.get(basin.id)
        if feature is None:
            log.warning("mrms: no full-resolution geometry for %s; basin skipped", basin.id)
            continue
        mask = build_basin_mask(
            basin_id=basin.id,
            polygons=_polygons_of(feature["geometry"]),
            grid=grid,
            polygon_source=source.name,
        )
        session.add(
            GridMask(
                basin_id=basin.id,
                grid_definition_hash=grid.definition_hash,
                method_id=mask.method_id,
                cells=[[i, w] for i, w in mask.cells],
                cell_count=len(mask.cells),
                masked_area_km2=mask.masked_area_km2,
                polygon_source=mask.polygon_source,
                computed_at=utcnow(),
            )
        )
        masks[basin.id] = mask
        log.info("mrms: built mask for %s on grid %s (%d cells)", basin.id, grid.definition_hash[:12], len(mask.cells))
    await session.flush()
    return masks


def _aggregate(mask: BasinMask, values) -> dict:
    """Area-weighted stats over one basin, sentinels respected."""
    import numpy as np

    idx = np.fromiter((c for c, _ in mask.cells), dtype=np.int64, count=len(mask.cells))
    w = np.fromiter((wt for _, wt in mask.cells), dtype=np.float64, count=len(mask.cells))
    v = values[idx]
    valid = v >= 0.0
    wsum = float(w.sum())
    valid_fraction = float(w[valid].sum() / wsum) if wsum else 0.0
    out = {
        "valid_fraction": round(valid_fraction, 6),
        "no_coverage_fraction": round(float(w[v == NO_COVERAGE].sum() / wsum), 6) if wsum else 0.0,
        "missing_fraction": round(float(w[v == MISSING].sum() / wsum), 6) if wsum else 0.0,
        "cell_count": int(idx.size),
    }
    if valid_fraction >= MIN_VALID_FRACTION:
        out["mean"] = float((v[valid] * w[valid]).sum() / w[valid].sum())
        out["max"] = float(v[valid].max())
    else:
        out["mean"] = None
        out["max"] = None
    return out


def _flags(stats: dict) -> list[str]:
    flags: list[str] = []
    if stats["mean"] is None:
        flags.append(INSUFFICIENT_COVERAGE)
    if stats["no_coverage_fraction"] > 0:
        flags.append(NO_COVERAGE_PRESENT)
    if stats["missing_fraction"] > 0:
        flags.append(MISSING_PRESENT)
    return flags


async def _stored_raster_times(session: AsyncSession, since: datetime) -> set[datetime]:
    rows = await session.execute(
        select(FieldRaster.valid_time).where(
            FieldRaster.product_id == PRODUCT_MRMS_QPE,
            FieldRaster.field == FIELD_QPE,
            FieldRaster.valid_time >= since,
        )
    )
    return {t for (t,) in rows}


def _store_raster(session: AsyncSession, *, obj: S3Object, field, qpe_result) -> bool:
    """Cut, quantize and stage the window raster for one hour (ADR-0020). Returns False —
    with the refusal logged — when the provider's grid stopped covering the seeded window;
    the basin means still store, because a mask that matches its grid hash is still right."""
    try:
        raster = cut_window(field)
    except WindowOutsideGridError as e:
        log.warning("mrms: %s", e)
        return False
    session.add(
        FieldRaster(
            product_id=PRODUCT_MRMS_QPE,
            field=FIELD_QPE,
            valid_time=obj.valid_time,
            retrieved_at=qpe_result.fetched_at,
            available_at=obj.last_modified,
            lo1=raster.lo1,
            la1=raster.la1,
            dlon=raster.dlon,
            dlat=raster.dlat,
            nx=raster.nx,
            ny=raster.ny,
            unit=raster.unit,
            scale=raster.scale,
            max_value=raster.max_value,
            cells=raster.cells,
            method_id=METHOD_RASTER,
            raw_artifact_id=qpe_result.artifact_id,
        )
    )
    return True


async def _prune_rasters(session: AsyncSession, now: datetime) -> int:
    """Retention (ADR-0020 §3): the one DELETE this codebase's writer performs on a data
    table, and it is scoped to rows this same job wrote and can rewrite from the archive."""
    from sqlalchemy import delete

    result = await session.execute(
        delete(FieldRaster).where(
            FieldRaster.product_id == PRODUCT_MRMS_QPE,
            FieldRaster.field == FIELD_QPE,
            FieldRaster.valid_time < now - RASTER_RETENTION,
        )
    )
    return int(result.rowcount or 0)


async def _stored_times(session: AsyncSession, feature: str, n_basins: int, since: datetime) -> set[datetime]:
    """valid_times already fully written (a row for every basin) — partial writes re-run."""
    rows = (
        await session.execute(
            select(DerivedFeature.valid_time)
            .where(DerivedFeature.feature == feature, DerivedFeature.valid_time >= since)
        )
    ).all()
    counts: dict[datetime, int] = {}
    for (t,) in rows:
        counts[t] = counts.get(t, 0) + 1
    return {t for t, n in counts.items() if n >= n_basins}


async def run_fetch_qpe(
    session: AsyncSession, fetcher: ArchivingFetcher, *, geo_dir: Path, now: datetime | None = None
) -> int:
    now = now or utcnow()
    basins = await _basins(session)
    if not basins:
        return 0

    days = [now]
    if now.hour < 2:  # the previous day's last accumulations publish after midnight
        days.append(now - timedelta(days=1))

    listings: dict[str, list[S3Object]] = {QPE_PRODUCT_DIR: [], GAUGEINFL_PRODUCT_DIR: []}
    for product_dir in listings:
        for day in days:
            result = await list_day(fetcher, session, product_dir=product_dir, day=day)
            listings[product_dir].extend(parse_listing(result.content))
    qpe_objects = sorted(
        (o for o in listings[QPE_PRODUCT_DIR] if o.valid_time >= now - LOOKBACK),
        key=lambda o: o.valid_time,
    )
    if not qpe_objects:
        raise NoListingError(
            f"no QPE objects in the last {LOOKBACK} — either NODD stopped publishing or the "
            "listing shape changed; both are worth a retry and a red job, not an empty success"
        )
    gaugeinfl_by_time = {o.valid_time: o for o in listings[GAUGEINFL_PRODUCT_DIR]}

    have = await _stored_times(session, FEATURE_QPE, len(basins), now - LOOKBACK)
    have_rasters = await _stored_raster_times(session, now - LOOKBACK)
    written = 0
    for obj in qpe_objects:
        if obj.valid_time in have and obj.valid_time in have_rasters:
            continue
        try:
            qpe_result = await fetch_object(fetcher, session, key=obj.key, product_id=PRODUCT_MRMS_QPE)
        except FetchError as e:
            # per accumulation, same rule as reaches/HEFS: one bad hour must not discard the rest
            log.warning("mrms: %s did not answer (%s)", obj.key, e)
            continue
        field = parse_mrms_grib(qpe_result.content)
        masks = await _masks_for(session, field.grid, basins, geo_dir)

        if obj.valid_time not in have_rasters and _store_raster(session, obj=obj, field=field, qpe_result=qpe_result):
            written += 1
        if obj.valid_time in have:
            continue  # only the raster was missing for this hour (pre-ADR-0020 rows)

        gauge_field = None
        gauge_result = None
        gauge_obj = gaugeinfl_by_time.get(obj.valid_time)
        if gauge_obj is not None:
            try:
                gauge_result = await fetch_object(
                    fetcher, session, key=gauge_obj.key, product_id=PRODUCT_MRMS_GAUGEINFL
                )
                gauge_field = parse_mrms_grib(gauge_result.content)
                if gauge_field.grid.definition_hash != field.grid.definition_hash:
                    log.warning(
                        "mrms: gauge-influence grid %s differs from QPE grid %s at %s; covariate skipped",
                        gauge_field.grid.definition_hash[:12], field.grid.definition_hash[:12], obj.valid_time,
                    )
                    gauge_field = None
            except FetchError as e:
                log.warning("mrms: gauge influence for %s did not answer (%s)", obj.valid_time, e)
        else:
            log.info("mrms: no gauge-influence object for %s yet", obj.valid_time)

        for basin in basins:
            mask = masks.get(basin.id)
            if mask is None:
                continue
            stats = _aggregate(mask, field.values)
            session.add(
                DerivedFeature(
                    feature=FEATURE_QPE,
                    scope_kind="basin",
                    scope_id=basin.id,
                    window="1h",
                    valid_time=obj.valid_time,  # the END of the accumulation
                    issued_at=None,  # an observation forecasts nothing
                    computed_at=qpe_result.fetched_at,
                    available_at=obj.last_modified,  # when NODD served it, not when we fetched it
                    method_id=METHOD_QPE,
                    product_id=PRODUCT_MRMS_QPE,
                    value=stats["mean"],
                    values_json={
                        **stats,
                        "grid_definition_hash": field.grid.definition_hash,
                        "masked_area_km2": mask.masked_area_km2,
                    },
                    unit="mm",
                    # A multi-sensor areal mean over full coverage is the best observed QPE that
                    # exists here; 'moderate' matches the NBM basin-mean convention, and it drops
                    # to 'unknown' with the value when coverage is refused.
                    confidence_label="moderate" if stats["mean"] is not None else "unknown",
                    quality=_flags(stats),
                    inputs=[{"table": "raw_artifact", "id": qpe_result.artifact_id}],
                    raw_inputs_hash=qpe_result.sha256,
                    raw_artifact_id=qpe_result.artifact_id,
                )
            )
            written += 1
            if gauge_field is not None and gauge_result is not None:
                gstats = _aggregate(mask, gauge_field.values)
                session.add(
                    DerivedFeature(
                        feature=FEATURE_GAUGEINFL,
                        scope_kind="basin",
                        scope_id=basin.id,
                        window="1h",
                        valid_time=obj.valid_time,
                        issued_at=None,
                        computed_at=gauge_result.fetched_at,
                        available_at=gauge_obj.last_modified if gauge_obj else obj.last_modified,
                        method_id=METHOD_GAUGEINFL,
                        product_id=PRODUCT_MRMS_GAUGEINFL,
                        value=gstats["mean"],
                        values_json={**gstats, "grid_definition_hash": gauge_field.grid.definition_hash},
                        unit="index",
                        confidence_label="moderate" if gstats["mean"] is not None else "unknown",
                        quality=_flags(gstats),
                        inputs=[{"table": "raw_artifact", "id": gauge_result.artifact_id}],
                        raw_inputs_hash=gauge_result.sha256,
                        raw_artifact_id=gauge_result.artifact_id,
                    )
                )
                written += 1
    pruned = await _prune_rasters(session, now)
    if pruned:
        log.info("mrms: pruned %d field_raster row(s) past %s retention", pruned, RASTER_RETENTION)
    await session.flush()
    return written
