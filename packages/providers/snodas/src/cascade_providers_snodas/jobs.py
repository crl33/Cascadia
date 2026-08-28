"""``snodas.fetch_swe`` — the NOHRSC snow model's daily SWE per basin, honestly qualified.

MODELED, and the label must say so: SNODAS assimilates the very SNOTEL pillows the platform
already carries, so it is not independent validation, and NOHRSC's own guide calls it "model
output ... not ... actual observations" with a documented unbounded-growth failure in
unobserved alpine cells. What it adds that the point network cannot: a spatially complete
basin surface — the basin-mean SWE and, above all, the SNOW-COVERED FRACTION, which is the
missing input the rain-on-snow gate names (DATA_SOURCES S2; HYDROLOGY §7).

**Knowledge time.** ``valid_time`` is the 06:00 UTC snapshot from the file's own header;
``available_at`` is the origin's Last-Modified (~13:15 UTC, a measured ~7.25 h lag), never the
fetch clock. ``issued_at`` is None — a daily analysis, not a cycle of forecasts.

**Coverage.** The −9999 pattern is a STATIC water/domain mask (measured bit-identical across
days), so in-basin no-data is permanent water and the mean over valid cells is the basin LAND
mean. The refusal threshold is therefore set BELOW the static floor (Nooksack's lakes cost
~2 % of weight on a normal day): a drop under ``MIN_VALID_FRACTION`` means the grid itself
changed or arrived damaged, not that a lake appeared. Saturated cells (32767 — the alpine
artifact) are excluded from the mean and flagged, never averaged.
"""

from __future__ import annotations

import gzip
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.models import Basin, DerivedFeature, GridMask
from cascade_core.registry import PRODUCT_SNODAS_SWE
from cascade_core.timeutils import to_utc, utcnow
from cascade_geo.latlon import LatLonGridSpec
from cascade_geo.masks import BasinMask, build_basin_mask
from cascade_providers_snodas.client import fetch_day_tar
from cascade_providers_snodas.parser import NODATA, SATURATED, parse_snodas_swe

log = logging.getLogger("cascade.providers.snodas")

JOB_NAME = "snodas.fetch_swe"
CADENCE_SECONDS = 86400
#: Files land 13:15 UTC with clockwork regularity (measured across a month of listings).
CRON = "40 13 * * *"

METHOD_SWE = "method:basin-snodas-swe@1.0.0"
FEATURE_SWE = "basin_swe_mm"
FEATURE_SCF = "basin_snow_covered_fraction"
#: Below this valid-weight fraction the mean is refused. The static water mask costs the
#: Nooksack ~2 % on EVERY day (measured), so the floor sits under that; a drop below it is
#: damage or a changed grid, not geography.
MIN_VALID_FRACTION = 0.93
#: How many days back a missed cron reaches (the NSIDC archive holds everything; older
#: backfill is a deliberate act, not an accident of an outage).
LOOKBACK_DAYS = 3

INSUFFICIENT_COVERAGE = "insufficient_grid_coverage"
WATER_CELLS = "static_water_cells_present"
SATURATED_CELLS = "swe_saturated_cells_excluded"
CORRUPT_CELLS = "negative_non_sentinel_cells_excluded"


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
            log.warning("snodas: no full-resolution geometry for %s; basin skipped", basin.id)
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
        log.info("snodas: built mask for %s on grid %s (%d cells)", basin.id, grid.definition_hash[:12], len(mask.cells))
    await session.flush()
    return masks


def _aggregate(mask: BasinMask, values) -> dict:
    """Area-weighted SWE mean (mm) and snow-covered fraction over VALID land cells."""
    import numpy as np

    idx = np.fromiter((c for c, _ in mask.cells), dtype=np.int64, count=len(mask.cells))
    w = np.fromiter((wt for _, wt in mask.cells), dtype=np.float64, count=len(mask.cells))
    v = values[idx]
    valid = (v != NODATA) & (v != SATURATED) & (v >= 0)
    corrupt = (v < 0) & (v != NODATA)  # negatives that are NOT the sentinel: damage, named
    wsum = float(w.sum())
    valid_fraction = float(w[valid].sum() / wsum) if wsum else 0.0
    out = {
        "valid_fraction": round(valid_fraction, 6),
        "water_fraction": round(float(w[v == NODATA].sum() / wsum), 6) if wsum else 0.0,
        "saturated_fraction": round(float(w[v == SATURATED].sum() / wsum), 6) if wsum else 0.0,
        "corrupt_fraction": round(float(w[corrupt].sum() / wsum), 6) if wsum else 0.0,
        "cell_count": int(idx.size),
    }
    if valid_fraction >= MIN_VALID_FRACTION:
        vw = w[valid]
        swe = v[valid]  # the stored integer IS millimetres (metres / 1000)
        out["swe_mean_mm"] = float((swe * vw).sum() / vw.sum())
        out["swe_max_mm"] = float(swe.max())
        out["snow_covered_fraction"] = float(vw[swe > 0].sum() / vw.sum())
    else:
        out["swe_mean_mm"] = None
        out["swe_max_mm"] = None
        out["snow_covered_fraction"] = None
    return out


def _flags(stats: dict) -> list[str]:
    flags: list[str] = []
    if stats["swe_mean_mm"] is None:
        flags.append(INSUFFICIENT_COVERAGE)
    if stats["water_fraction"] > 0:
        flags.append(WATER_CELLS)
    if stats["saturated_fraction"] > 0:
        flags.append(SATURATED_CELLS)
    if stats["corrupt_fraction"] > 0:
        flags.append(CORRUPT_CELLS)
    return flags


async def _stored_scopes_by_day(session: AsyncSession, since: datetime) -> dict[date, set[str]]:
    """Per UTC calendar day: the basins whose BOTH features are already stored.

    Keyed by DATE, not the 06:00 instant — the header's own Start hour is the authority and
    a day NOHRSC ships at a different hour must not be refetched forever against a hard-coded
    six. Returning scope sets (not a complete/incomplete verdict) lets the write loop complete
    a partial day row-by-row instead of re-inserting whole — the re-insert tripped
    uq_derived_feature_identity on PostgreSQL (both from the adversarial review, 2026-08-28).
    """
    rows = (
        await session.execute(
            select(DerivedFeature.valid_time, DerivedFeature.scope_id, DerivedFeature.feature)
            .where(DerivedFeature.feature.in_([FEATURE_SWE, FEATURE_SCF]),
                   DerivedFeature.valid_time >= since)
        )
    ).all()
    seen: dict[tuple[date, str], set[str]] = {}
    for t, sid, feature in rows:
        seen.setdefault((t.date(), sid), set()).add(feature)
    out: dict[date, set[str]] = {}
    for (day, sid), feats in seen.items():
        if feats >= {FEATURE_SWE, FEATURE_SCF}:
            out.setdefault(day, set()).add(sid)
    return out


async def run_fetch_swe(
    session: AsyncSession, fetcher: ArchivingFetcher, *, geo_dir: Path, now: datetime | None = None
) -> int:
    """Ingest every recent day not yet fully stored, newest last. Returns rows written."""
    # UTC throughout: a non-UTC (or naive) `now` made the membership probe never match the
    # stored 06:00 UTC instants — every stored day refetched, and on PostgreSQL the re-insert
    # wedged on the identity constraint (reproduced by the adversarial review, 2026-08-28).
    now = to_utc(now) if now is not None else utcnow()
    basins = await _basins(session)
    if not basins:
        log.warning("snodas: no basins seeded; nothing to aggregate")
        return 0
    since = now - timedelta(days=LOOKBACK_DAYS + 1)
    stored_by_day = await _stored_scopes_by_day(session, since)
    written = 0
    masks_by_hash: dict[str, dict[str, BasinMask]] = {}
    for back in range(LOOKBACK_DAYS, -1, -1):
        day = (now - timedelta(days=back)).date()
        done = stored_by_day.get(day, set())
        if {b.id for b in basins} <= done:
            continue
        try:
            result = await fetch_day_tar(fetcher, session, day)
        except FetchError as e:
            # today's file simply may not exist yet before ~13:15Z; yesterday's absence is real
            log.info("snodas: %s not served (%s)", day.isoformat(), e)
            continue
        field = parse_snodas_swe(result.content)
        if field.valid_time.date() != day:
            raise ValueError(
                f"snodas: file for {day.isoformat()} says snapshot {field.valid_time.isoformat()}"
            )
        # masks are keyed by EACH field's own grid hash — resolving once from the first file
        # and reusing across a mid-run grid change would aggregate with the wrong flat indices
        # (the convention the hash exists for; adversarial review 2026-08-28)
        if field.grid.definition_hash not in masks_by_hash:
            masks_by_hash[field.grid.definition_hash] = await _masks_for(session, field.grid, basins, geo_dir)
        masks = masks_by_hash[field.grid.definition_hash]
        available_at = result.last_modified or result.fetched_at
        for basin in basins:
            if basin.id in done:
                continue  # complete a partial day row-by-row; never re-insert
            mask = masks.get(basin.id)
            if mask is None:
                continue
            stats = _aggregate(mask, field.values)
            shared = dict(
                scope_kind="basin",
                scope_id=basin.id,
                window=None,
                valid_time=field.valid_time,
                issued_at=None,
                computed_at=result.fetched_at,
                available_at=available_at,
                product_id=PRODUCT_SNODAS_SWE,
                values_json={**stats, "grid_definition_hash": field.grid.definition_hash,
                             "masked_area_km2": mask.masked_area_km2},
                # MODELED with assimilation of the same pillows we already carry — 'moderate'
                # would overstate it; the label class comes from the product's source kind.
                confidence_label="low" if stats["swe_mean_mm"] is not None else "unknown",
                quality=_flags(stats),
                inputs=[{"table": "raw_artifact", "id": result.artifact_id}],
                raw_inputs_hash=result.sha256,
                raw_artifact_id=result.artifact_id,
            )
            session.add(DerivedFeature(
                feature=FEATURE_SWE, method_id=METHOD_SWE, value=stats["swe_mean_mm"],
                unit="mm", **shared))
            session.add(DerivedFeature(
                feature=FEATURE_SCF, method_id=METHOD_SWE, value=stats["snow_covered_fraction"],
                unit="fraction", **shared))
            written += 2
    await session.flush()
    return written
