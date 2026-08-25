"""Idempotent NBM jobs: build basin masks once, then aggregate each cycle onto them.

Three jobs, in the order they must first run:

``nbm.build_grid_masks`` (bootstrap / after a grid change)
    Learns the live grid definition from the smallest available subset, then builds and stores
    one :class:`~cascade_core.models.GridMask` per basin from the FULL-RESOLUTION seed
    geometry. Deliberately separate from ingestion, and deliberately not automatic: masks are
    reference data whose correctness is checked (masked area against WBD), not something an
    ingest job should quietly invent mid-cycle.

``nbm.fetch_qmd`` (every 6 h, after the ~7 h 20 m qmd latency)
    Fetches the WA-box APCP subset for the 24/48/72-h cumulative windows, aggregates each
    percentile and the deterministic field onto the stored masks, and appends DerivedFeature
    rows. **If no mask exists for the cycle's grid definition it refuses**: it records one
    value-less row per basin carrying the reason, so the surface reports UNKNOWN with a
    specific explanation instead of a mean computed with the wrong weights.

``nbm.fetch_core_snowlvl`` (every 6 h)
    The same for SNOWLVL percentiles from ``core``. Snow level is CONTEXT: it is stored and
    displayed as an elevation, never scored, and never turned into a rain-exposed fraction
    without hypsometry (p3-surfaces-design §1.8, docs/HYDROLOGY.md §7).

Idempotency key is the DerivedFeature identity
``(method_id, feature, scope_id, window, valid_time, issued_at)``: re-running a cycle writes
nothing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.models import Basin, DerivedFeature, GridMask
from cascade_core.registry import PRODUCT_NBM_CORE, PRODUCT_NBM_QMD
from cascade_core.timeutils import utcnow
from cascade_geo import (
    METHOD_GRID_MASK,
    BasinMask,
    GridSpec,
    build_basin_mask,
    load_basin_polygons,
)
from cascade_hydrology.forcing import (
    GRID_CHANGED_FLAG,
    HEADLINE_PERCENTILE,
    METHOD_BASIN_QPF,
    METHOD_BASIN_SNOW_LEVEL,
    QPF_PERCENTILES,
    QPF_WINDOWS_H,
    SNOW_LEVEL_PERCENTILES,
    qpf_feature,
    qpf_label,
    snow_level_label,
    window_label,
)
from cascade_providers_nbm.client import (
    CORE_HORIZONS_H,
    QMD_HORIZONS_H,
    Cycle,
    fetch_core_snowlvl,
    fetch_qmd_apcp,
    latest_qmd_cycle,
)
from cascade_providers_nbm.normalize import BasinQpf, Refusal, basin_mean
from cascade_providers_nbm.parser import (
    Field,
    NbmParseError,
    cumulative_apcp,
    decode,
    snow_level,
)

JOB_BUILD_MASKS = "nbm.build_grid_masks"
JOB_FETCH_QMD = "nbm.fetch_qmd"
JOB_FETCH_CORE_SNOWLVL = "nbm.fetch_core_snowlvl"
#: 12-hourly: only the 00Z/12Z cycles publish the 0-N day cumulative windows the 72-hour
#: basin QPF is defined on (client.QMD_CYCLE_HOURS, measured live 2026-08-25).
CADENCE_QMD_SECONDS = 12 * 3600
CADENCE_CORE_SNOWLVL_SECONDS = 6 * 3600

#: Where the full-resolution basin polygons live. Display-LOD geometry over-counts the Skagit
#: footprint by 20 % (measured) and must never be used to build a mask.
BASIN_GEOMETRY_FILE = "basins_seed_full.geojson.gz"
DEFAULT_GEO_DIR = Path("tests/fixtures/geo")


@dataclass(frozen=True)
class MaskReport:
    basin_id: str
    grid_definition_hash: str
    cell_count: int
    masked_area_km2: float
    built: bool


async def _basins(session: AsyncSession) -> list[Basin]:
    return list((await session.execute(select(Basin).order_by(Basin.id))).scalars().all())


async def load_masks(session: AsyncSession, grid_definition_hash: str) -> dict[str, BasinMask]:
    """Stored masks for one grid definition. A changed grid returns an empty mapping."""
    rows = (
        await session.execute(select(GridMask).where(GridMask.grid_definition_hash == grid_definition_hash))
    ).scalars().all()
    return {
        row.basin_id: BasinMask.from_rows(
            row.cells,
            basin_id=row.basin_id,
            grid_definition_hash=row.grid_definition_hash,
            masked_area_km2=row.masked_area_km2,
            polygon_source=row.polygon_source,
            method_id=row.method_id,
        )
        for row in rows
    }


async def run_build_grid_masks(
    session: AsyncSession,
    fetcher: ArchivingFetcher,
    *,
    geo_dir: Path = DEFAULT_GEO_DIR,
    cycle: Cycle | None = None,
    grid: GridSpec | None = None,
) -> list[MaskReport]:
    """Build and store the basin masks for the live grid definition.

    Pass ``grid`` to build against an already-decoded grid (tests, backfill); otherwise the
    smallest subset available (``core`` SNOWLVL, ~172 KB) is fetched purely to read the grid
    definition out of it. Existing masks for the same grid are left alone: a mask is
    reference data, and rebuilding an identical one would only churn ``computed_at``.
    """
    if grid is None:
        cyc = cycle or latest_qmd_cycle(utcnow())
        result = await fetch_core_snowlvl(fetcher, session, cycle=cyc, fhour=CORE_HORIZONS_H[0])
        fields = decode(result.content, want=snow_level(percentile=HEADLINE_PERCENTILE), with_values=False)
        if not fields:
            raise NbmParseError("field_missing", "no SNOWLVL percentile field to read a grid definition from")
        grid = fields[0].grid
    polygons, _wbd_areas, polygon_source = load_basin_polygons(Path(geo_dir) / BASIN_GEOMETRY_FILE)
    existing = await load_masks(session, grid.definition_hash)
    reports: list[MaskReport] = []
    for basin in await _basins(session):
        if basin.id in existing:
            mask = existing[basin.id]
            reports.append(MaskReport(basin.id, grid.definition_hash, mask.cell_count, mask.masked_area_km2, built=False))
            continue
        if basin.id not in polygons:
            raise NbmParseError("geometry_missing", f"{basin.id} has no polygon in {BASIN_GEOMETRY_FILE}")
        mask = build_basin_mask(basin_id=basin.id, polygons=polygons[basin.id], grid=grid, polygon_source=polygon_source)
        session.add(
            GridMask(
                basin_id=mask.basin_id,
                grid_definition_hash=mask.grid_definition_hash,
                method_id=mask.method_id,
                cells=mask.as_rows(),
                cell_count=mask.cell_count,
                masked_area_km2=mask.masked_area_km2,
                polygon_source=mask.polygon_source,
                computed_at=utcnow(),
            )
        )
        reports.append(MaskReport(basin.id, grid.definition_hash, mask.cell_count, mask.masked_area_km2, built=True))
    await session.flush()
    return reports


async def _already_stored(session: AsyncSession, *, method_id: str, feature: str, scope_id: str, window: str | None, valid_time: datetime, issued_at: datetime | None) -> bool:
    q = select(DerivedFeature.id).where(
        DerivedFeature.method_id == method_id,
        DerivedFeature.feature == feature,
        DerivedFeature.scope_id == scope_id,
        DerivedFeature.window.is_(None) if window is None else DerivedFeature.window == window,
        DerivedFeature.valid_time == valid_time,
        DerivedFeature.issued_at.is_(None) if issued_at is None else DerivedFeature.issued_at == issued_at,
    )
    return (await session.execute(q.limit(1))).scalar_one_or_none() is not None


async def _append(
    session: AsyncSession,
    mean: BasinQpf,
    *,
    product_id: str,
    result: FetchResult,
    label: str,
    method_id: str = METHOD_BASIN_QPF,
) -> int:
    window = window_label(mean.window_h) if mean.window_h is not None else None
    if await _already_stored(session, method_id=method_id, feature=mean.feature, scope_id=mean.basin_id, window=window, valid_time=mean.valid_time, issued_at=mean.cycle):
        return 0
    session.add(
        DerivedFeature(
            feature=mean.feature,
            scope_kind="basin",
            scope_id=mean.basin_id,
            window=window,
            valid_time=mean.valid_time,
            issued_at=mean.cycle,
            computed_at=result.fetched_at,
            # Knowledge time: a cycle issued hours ago became knowable when it was fetched.
            available_at=max(mean.cycle, result.fetched_at),
            method_id=method_id,
            product_id=product_id,
            value=mean.value,
            values_json={
                "label": label,
                "percentile_level": mean.percentile,
                "native_unit": mean.native_unit,
                "grid_definition_hash": mean.grid_definition_hash,
                "mask_method_id": METHOD_GRID_MASK,
                "cell_count": mean.cell_count,
                "weight_sum": round(mean.weight_sum, 6),
                "masked_area_km2": round(mean.masked_area_km2, 3),
            },
            unit=mean.unit,
            # percentile stays NULL: this is a MODEL percentile level, not a percentile of
            # this value against any climatology, and the column means the latter.
            percentile=None,
            confidence_label="moderate",
            quality=list(mean.quality),
            inputs=[{"table": "raw_artifact", "id": result.artifact_id}, {"table": "grid_mask", "grid_definition_hash": mean.grid_definition_hash}],
            raw_inputs_hash=result.sha256,
            raw_artifact_id=result.artifact_id,
        )
    )
    return 1


async def _append_refusal(
    session: AsyncSession,
    refusal: Refusal,
    *,
    product_id: str,
    result: FetchResult,
    cycle: datetime,
    valid_time: datetime,
    window: str | None,
    grid_definition_hash: str,
) -> int:
    """Record that a basin mean was refused, with the reason, as a value-less row.

    UNKNOWN with a reason is a legitimate state and has to be storable: without this row the
    read path could not tell "the grid changed and we refused" from "the job never ran".
    """
    if await _already_stored(session, method_id=METHOD_BASIN_QPF, feature=refusal.feature, scope_id=refusal.basin_id, window=window, valid_time=valid_time, issued_at=cycle):
        return 0
    session.add(
        DerivedFeature(
            feature=refusal.feature,
            scope_kind="basin",
            scope_id=refusal.basin_id,
            window=window,
            valid_time=valid_time,
            issued_at=cycle,
            computed_at=result.fetched_at,
            available_at=max(cycle, result.fetched_at),
            method_id=METHOD_BASIN_QPF,
            product_id=product_id,
            value=None,
            values_json={"refused": refusal.reason, "grid_definition_hash": grid_definition_hash},
            unit="mm",
            percentile=None,
            confidence_label="unknown",
            quality=[refusal.kind if refusal.kind != "grid_definition_changed" else GRID_CHANGED_FLAG],
            inputs=[{"table": "raw_artifact", "id": result.artifact_id}],
            raw_inputs_hash=result.sha256,
            raw_artifact_id=result.artifact_id,
        )
    )
    return 1


def _selected_fields(content: bytes, *, hours: int) -> list[Field]:
    """The percentile and deterministic 0-N day APCP fields for one horizon."""
    wanted = [cumulative_apcp(hours=hours, percentile=p) for p in QPF_PERCENTILES]
    wanted.append(cumulative_apcp(hours=hours, percentile=None))
    return decode(content, want=lambda key: any(w(key) for w in wanted))


async def run_fetch_qmd(
    session: AsyncSession,
    fetcher: ArchivingFetcher,
    *,
    cycle: Cycle | None = None,
    horizons: Sequence[int] = QMD_HORIZONS_H,
) -> int:
    """Ingest one qmd cycle: three subsets, six fields each, six basins."""
    cyc = cycle or latest_qmd_cycle(utcnow())
    basins = await _basins(session)
    written = 0
    for fhour in horizons:
        if fhour not in QPF_WINDOWS_H:
            raise ValueError(f"unsupported QPF horizon {fhour}h")
        result = await fetch_qmd_apcp(fetcher, session, cycle=cyc, fhour=fhour)
        fields = _selected_fields(result.content, hours=fhour)
        if not fields:
            raise NbmParseError("field_missing", f"qmd f{fhour:03d} carries no 0-{fhour} h APCP field")
        grid_hash = fields[0].grid.definition_hash
        masks = await load_masks(session, grid_hash)
        for basin in basins:
            mask = masks.get(basin.id)
            if mask is None:
                # Refuse once per basin per horizon, on the feature the surface reads.
                written += await _append_refusal(
                    session,
                    Refusal(
                        basin_id=basin.id,
                        feature=qpf_feature(fhour, HEADLINE_PERCENTILE),
                        kind="grid_definition_changed",
                        reason=f"no stored basin mask for grid {grid_hash[:12]}; run {JOB_BUILD_MASKS}",
                    ),
                    product_id=PRODUCT_NBM_QMD,
                    result=result,
                    cycle=cyc.issued_at,
                    valid_time=fields[0].valid_time,
                    window=window_label(fhour),
                    grid_definition_hash=grid_hash,
                )
                continue
            for field in fields:
                outcome = basin_mean(field, mask, basin_id=basin.id)
                if isinstance(outcome, Refusal):
                    written += await _append_refusal(
                        session,
                        outcome,
                        product_id=PRODUCT_NBM_QMD,
                        result=result,
                        cycle=cyc.issued_at,
                        valid_time=field.valid_time,
                        window=window_label(fhour),
                        grid_definition_hash=grid_hash,
                    )
                    continue
                written += await _append(
                    session,
                    outcome,
                    product_id=PRODUCT_NBM_QMD,
                    result=result,
                    label=qpf_label(fhour, field.key.percentile),
                )
    await session.flush()
    return written


async def run_fetch_core_snowlvl(
    session: AsyncSession,
    fetcher: ArchivingFetcher,
    *,
    cycle: Cycle | None = None,
    horizons: Sequence[int] = CORE_HORIZONS_H,
) -> int:
    """Ingest snow-level percentiles for one cycle at each lead time. Context, never scored."""
    cyc = cycle or latest_qmd_cycle(utcnow())
    basins = await _basins(session)
    written = 0
    leads = tuple(horizons)
    without_percentiles: list[int] = []
    for fhour in leads:
        result = await fetch_core_snowlvl(fetcher, session, cycle=cyc, fhour=fhour)
        wanted = [snow_level(percentile=p, fhour=fhour) for p in SNOW_LEVEL_PERCENTILES]
        fields = decode(result.content, want=lambda key: any(w(key) for w in wanted))
        if not fields:
            # ONE lead time without percentiles is a provider fact, not an outage: NBM `core`
            # stops publishing SNOWLVL percentile levels after f048 (measured 2026-08-24, see
            # client.CORE_HORIZONS_H). Raising here used to discard the leads that HAD decoded,
            # so a single structurally-empty lead cost the whole cycle its snow-level context.
            # Only a cycle where NO requested lead carries a percentile is a break worth
            # retrying, and that is raised below.
            without_percentiles.append(fhour)
            continue
        masks = await load_masks(session, fields[0].grid.definition_hash)
        for basin in basins:
            mask = masks.get(basin.id)
            if mask is None:
                continue  # the qmd job records the refusal; snow level is a context driver
            for field in fields:
                outcome = basin_mean(field, mask, basin_id=basin.id)
                if isinstance(outcome, Refusal):
                    continue
                written += await _append(
                    session,
                    outcome,
                    product_id=PRODUCT_NBM_CORE,
                    result=result,
                    label=snow_level_label(field.key.percentile, fhour),
                    method_id=METHOD_BASIN_SNOW_LEVEL,
                )
    if leads and len(without_percentiles) == len(leads):
        raise NbmParseError(
            "field_missing",
            "core carries no SNOWLVL percentile field at any requested lead time "
            f"({', '.join(f'f{h:03d}' for h in leads)}); refusing to record a successful run "
            "that stored no snow-level context",
        )
    await session.flush()
    return written


__all__ = [
    "CADENCE_CORE_SNOWLVL_SECONDS",
    "CADENCE_QMD_SECONDS",
    "JOB_BUILD_MASKS",
    "JOB_FETCH_CORE_SNOWLVL",
    "JOB_FETCH_QMD",
    "MaskReport",
    "load_masks",
    "run_build_grid_masks",
    "run_fetch_core_snowlvl",
    "run_fetch_qmd",
]
