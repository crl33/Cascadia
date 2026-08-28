"""``wpc.fetch_qpf`` — the official human QPF per basin: three 24-h windows, twice daily.

The value this adds beside NBM is KIND, not resolution: NBM is a calibrated model blend
(MODELED); this is the WPC forecaster's judgment (OFFICIAL_FORECAST). The two are never
averaged — they are the two ends the agreement surface will eventually compare.

**Knowledge time is inverted here and that is real.** ``issued_at`` is the cycle identity
(00Z/12Z, from the GRIB reference time); ``available_at`` is the origin's Last-Modified, which
is ~48 min BEFORE the nominal cycle hour (measured) because WPC publishes ahead. A 23:00Z
replay honestly sees the 00Z-cycle QPF — the forecaster had genuinely published it. Where the
origin omits Last-Modified, the fetch instant stands in (later than truth, never earlier).

**Idempotent per cycle.** The newest candidate cycle whose Day-1 file exists is ingested; rows
carry the DerivedFeature identity (method, feature, scope, window, valid_time, issued_at), and
a cycle already stored for every basin is skipped before any bytes move.

Masks are the shared ``grid_mask`` machinery keyed by Section-3 hash (NBM/MRMS convention);
the 5-km LCC grid gets its own masks the first time this job meets it.
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
from cascade_core.models import Basin, DerivedFeature, GridMask
from cascade_core.registry import PRODUCT_WPC_QPF
from cascade_core.timeutils import utcnow
from cascade_geo.lcc import GridSpec
from cascade_geo.masks import BasinMask, build_basin_mask
from cascade_providers_wpc.client import (
    FORECAST_HOURS,
    cycle_candidates,
    fetch_qpf_file,
)
from cascade_providers_wpc.parser import (
    MISSING_FLOOR,
    NEGATIVE_NOISE,
    WpcField,
    parse_wpc_qpf,
)

log = logging.getLogger("cascade.providers.wpc")

JOB_NAME = "wpc.fetch_qpf"
CADENCE_SECONDS = 43200
#: ~20 min after each cycle's measured publication (12Z at 10:48Z, 00Z at 22:48Z the day before).
CRON = "10 11,23 * * *"

METHOD_QPF = "method:basin-qpf-wpc@1.0.0"
#: One feature, three window END offsets: Day 1/2/3 as 24-h accumulations. The name says
#: `official` because the KIND is the distinguishing fact against the NBM-derived QPF features.
FEATURE_QPF = "basin_qpf_24h_official"
#: Below this valid-weight fraction the mean is refused (the MRMS convention). The 9999 missing
#: cells are the off-CONUS corners of the LCC rectangle; the seed basins measured 0 of them.
MIN_VALID_FRACTION = 0.995

INSUFFICIENT_COVERAGE = "insufficient_grid_coverage"
MISSING_PRESENT = "missing_cells"
NEGATIVE_CLAMPED = "jpeg_negative_clamped"


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
    session: AsyncSession, grid: GridSpec, basins: list[Basin], geo_dir: Path
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
            log.warning("wpc: no full-resolution geometry for %s; basin skipped", basin.id)
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
        log.info("wpc: built mask for %s on grid %s (%d cells)", basin.id, grid.definition_hash[:12], len(mask.cells))
    await session.flush()
    return masks


def _aggregate(mask: BasinMask, values) -> dict:
    """Area-weighted stats over one basin.

    Missing cells (>= MISSING_FLOOR, the bitmap sentinel) reduce the valid fraction; small
    NEGATIVE values are JPEG reconstruction noise around zero and clamp to 0.0 rather than
    reducing coverage — "no rain" is a value. Anything more negative than the noise floor is
    treated as missing: a real QPF is never negative.
    """
    import numpy as np

    idx = np.fromiter((c for c, _ in mask.cells), dtype=np.int64, count=len(mask.cells))
    w = np.fromiter((wt for _, wt in mask.cells), dtype=np.float64, count=len(mask.cells))
    v = values[idx].astype(np.float64)
    clamped = (v < 0.0) & (v >= -NEGATIVE_NOISE)
    v = np.where(clamped, 0.0, v)
    valid = (v >= 0.0) & (v < MISSING_FLOOR)
    wsum = float(w.sum())
    valid_fraction = float(w[valid].sum() / wsum) if wsum else 0.0
    out = {
        "valid_fraction": round(valid_fraction, 6),
        "missing_fraction": round(1.0 - valid_fraction, 6),
        "negative_clamped_cells": int(clamped.sum()),
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
    if stats["missing_fraction"] > 0:
        flags.append(MISSING_PRESENT)
    if stats["negative_clamped_cells"] > 0:
        flags.append(NEGATIVE_CLAMPED)
    return flags


async def _stored_pairs(session: AsyncSession, cycle: datetime) -> set[tuple[str, datetime]]:
    """The (scope, valid_time) pairs already stored for this cycle — the write loop's skip set.

    Keyed on (scope, valid_time), NOT (scope, window): the window string is always "24h" here.
    Returning the SET rather than a complete/incomplete verdict serves two review findings at
    once: a partially stored cycle is completed row-by-row instead of re-inserted whole (the
    re-insert tripped uq_derived_feature_identity on PostgreSQL — a crash-loop), and the
    denominator no longer counts basins the write loop would skip.
    """
    rows = (
        await session.execute(
            select(DerivedFeature.scope_id, DerivedFeature.valid_time)
            .where(
                DerivedFeature.feature == FEATURE_QPF,
                DerivedFeature.issued_at == cycle,
            )
        )
    ).all()
    return {(sid, t) for sid, t in rows}


async def run_fetch_qpf(
    session: AsyncSession, fetcher: ArchivingFetcher, *, geo_dir: Path, now: datetime | None = None
) -> int:
    """Ingest EVERY candidate cycle not yet fully stored, oldest gaps included.

    Two review findings shape the loop (2026-08-28, both reproduced): returning on the first
    complete cycle permanently skipped a cycle whose publication landed inside the 2-minute
    late edge of its measured spread — the official 00Z judgment then read as "never issued"
    to any later hindcast — so every candidate is now visited; and a half-published cycle
    (Day 1 up, Day 2 not yet) is NOT-READY — skipped whole to be retried, never crashed on
    and never stored as a Day-1-only picture that reads as dry Day 2/3.
    """
    now = now or utcnow()
    basins = await _basins(session)
    if not basins:
        log.warning("wpc: no basins seeded; nothing to aggregate")
        return 0

    total_written = 0
    for cycle in cycle_candidates(now):
        stored = await _stored_pairs(session, cycle)
        expected = {
            (b.id, cycle + timedelta(hours=fh)) for b in basins for fh in FORECAST_HOURS
        }
        if not (expected - {(sid, t.replace(tzinfo=cycle.tzinfo)) for sid, t in stored}):
            log.info("wpc: cycle %s already stored", cycle.isoformat())
            continue
        try:
            results = {
                fhour: await fetch_qpf_file(fetcher, session, cycle, fhour)
                for fhour in FORECAST_HOURS
            }
        except FetchError as e:
            log.info("wpc: cycle %s not fully served yet (%s); will retry", cycle.isoformat(), e)
            continue
        written = 0
        masks: dict[str, BasinMask] | None = None
        for fhour, result in sorted(results.items()):
            field: WpcField = parse_wpc_qpf(result.content)
            if field.reference_time != cycle:
                raise ValueError(
                    f"wpc: {fhour:03d} file says cycle {field.reference_time.isoformat()}, "
                    f"expected {cycle.isoformat()} — the file server served a stale name"
                )
            if field.step_end_h != fhour:
                raise ValueError(
                    f"wpc: f{fhour:03d} file carries window {field.step_start_h}-{field.step_end_h}"
                )
            if masks is None:
                masks = await _masks_for(session, field.grid, basins, geo_dir)
            available_at = result.last_modified or result.fetched_at
            row_valid_time = cycle + timedelta(hours=field.step_end_h)
            for basin in basins:
                mask = masks.get(basin.id)
                if mask is None:
                    continue
                if any(sid == basin.id and t.replace(tzinfo=cycle.tzinfo) == row_valid_time for sid, t in stored):
                    continue  # complete a partial cycle row-by-row; never re-insert
                stats = _aggregate(mask, field.values)
                session.add(
                    DerivedFeature(
                        feature=FEATURE_QPF,
                        scope_kind="basin",
                        scope_id=basin.id,
                        window="24h",
                        valid_time=cycle + timedelta(hours=field.step_end_h),  # window END
                        issued_at=cycle,
                        computed_at=result.fetched_at,
                        available_at=available_at,
                        method_id=METHOD_QPF,
                        product_id=PRODUCT_WPC_QPF,
                        value=stats["mean"],
                        values_json={
                            **stats,
                            "window_start_h": field.step_start_h,
                            "window_end_h": field.step_end_h,
                            "grid_definition_hash": field.grid.definition_hash,
                            "masked_area_km2": mask.masked_area_km2,
                        },
                        unit="mm",
                        # A human-drawn 5-km national field read at basin scale: 'moderate' by
                        # the same convention as the NBM basin mean; 'unknown' with the value
                        # when coverage is refused.
                        confidence_label="moderate" if stats["mean"] is not None else "unknown",
                        quality=_flags(stats),
                        inputs=[{"table": "raw_artifact", "id": result.artifact_id}],
                        raw_inputs_hash=result.sha256,
                        raw_artifact_id=result.artifact_id,
                    )
                )
                written += 1
        await session.flush()
        log.info("wpc: cycle %s -> %d rows", cycle.isoformat(), written)
        total_written += written
    if total_written == 0:
        log.info("wpc: no candidate cycle needed ingesting")
    return total_written
