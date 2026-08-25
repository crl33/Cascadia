"""Idempotent AWDB job: fetch (archive first) -> parse -> map to basins -> append DerivedFeature.

One job, once a day, two requests: station metadata (for the HUC mapping and elevations) and one
values call for every mapped site. `DATA_SOURCES.md` open item 27 notes AWDB publishes no rate
limit and no headers; one call a day is conservative regardless.

Idempotency follows `DATA_DOCTRINE.md` §8 exactly: `derived_feature` is append-only and its
identity is (method_id, feature, scope_id, window, valid_time, issued_at). A re-run inside the
same day therefore finds its own row and SKIPS — it never updates one in place and never writes
a duplicate. A changed method is a new `method_id` and so a new row by construction.

Nothing this job writes is scored. Both features carry `direction="context_not_scored"` when the
susceptibility surface renders them (HYDROLOGY §7).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import Basin, DerivedFeature
from cascade_core.registry import PRODUCT_AWDB_DAILY
from cascade_core.timeutils import available_at, utcnow
from cascade_providers_awdb.client import fetch_daily_values, fetch_stations
from cascade_providers_awdb.normalize import (
    ContextResult,
    daily_value_valid_time,
    latest_common_day,
    map_stations_to_basins,
    precip_14d_percent_of_median,
    swe_percent_of_median,
)
from cascade_providers_awdb.parser import (
    AwdbSeries,
    AwdbStation,
    parse_data,
    parse_stations,
)

JOB_NAME = "awdb.fetch_snotel_context"
CADENCE_SECONDS = 86400
# 21 days: the 14-day precipitation window plus a week of slack for sites that report late.
DEFAULT_DAYS = 21


async def _already_written(session: AsyncSession, *, method_id: str, feature: str, scope_id: str, valid_time: datetime) -> bool:
    q = (
        select(DerivedFeature.id)
        .where(DerivedFeature.method_id == method_id, DerivedFeature.feature == feature)
        .where(DerivedFeature.scope_id == scope_id, DerivedFeature.window.is_(None))
        .where(DerivedFeature.valid_time == valid_time, DerivedFeature.issued_at.is_(None))
        .limit(1)
    )
    return (await session.execute(q)).scalar_one_or_none() is not None


def _offset(sites: Sequence[AwdbStation]) -> float | None:
    offsets = {s.utc_offset_hours for s in sites if s.utc_offset_hours is not None}
    return next(iter(offsets)) if len(offsets) == 1 else None


async def _append(
    session: AsyncSession,
    *,
    result: ContextResult,
    basin_id: str,
    element: str,
    valid_time: datetime,
    quality: tuple[str, ...],
    retrieved_at: datetime,
    artifact_id: int | None,
) -> int:
    if await _already_written(session, method_id=result.method_id, feature=result.feature, scope_id=basin_id, valid_time=valid_time):
        return 0
    flags = list(quality)
    if result.value is None:
        flags.append("unavailable")
    session.add(
        DerivedFeature(
            feature=result.feature,
            scope_kind="basin",
            scope_id=basin_id,
            window=None,
            valid_time=valid_time,
            issued_at=None,
            computed_at=retrieved_at,
            available_at=available_at(valid_time=valid_time, retrieved_at=retrieved_at),
            method_id=result.method_id,
            product_id=PRODUCT_AWDB_DAILY,
            value=result.value,
            values_json={**result.to_values_json(), "label": result.label(element=element), "reason": result.reason},
            unit=result.unit,
            percentile=None,
            climatology_ref=None,
            # A point-network statistic standing in for a basin can never be better than low
            # confidence, whatever the arithmetic says (design §2.6).
            confidence_label="low" if result.value is not None else "unknown",
            quality=flags,
            inputs=[] if artifact_id is None else [{"table": "raw_artifact", "id": artifact_id}],
            raw_artifact_id=artifact_id,
        )
    )
    return 1


async def run_fetch_snotel_context(
    session: AsyncSession,
    fetcher: ArchivingFetcher,
    *,
    now: datetime | None = None,
    days: int = DEFAULT_DAYS,
) -> int:
    """Fetch WA SNOTEL, map sites to basins by HUC8, write the two context features per basin."""
    now = now or utcnow()
    basins = list((await session.execute(select(Basin).order_by(Basin.id))).scalars())
    basin_huc8 = {b.id: list(b.huc8 or []) for b in basins if b.huc8}
    if not basin_huc8:
        return 0

    stations_result = await fetch_stations(fetcher, session)
    stations = parse_stations(stations_result.content)
    mapping = map_stations_to_basins(stations, basin_huc8)
    triplets = sorted({s.triplet for sites in mapping.values() for s in sites})
    if not triplets:
        return 0

    end: date = now.date()
    data_result = await fetch_daily_values(fetcher, session, triplets=triplets, begin=end - timedelta(days=days), end=end)
    series: tuple[AwdbSeries, ...] = parse_data(data_result.content)

    written = 0
    for basin_id, sites in mapping.items():
        if not sites:
            continue
        mine = tuple(s for s in series if s.triplet in {x.triplet for x in sites})
        offset = _offset(sites)
        for element, compute in (("WTEQ", swe_percent_of_median), ("PREC", precip_14d_percent_of_median)):
            day = latest_common_day(mine, element=element)
            result = compute(mine, sites, day=day)
            anchor = day if day is not None else end
            valid_time, flags = daily_value_valid_time(anchor, utc_offset_hours=offset)
            written += await _append(
                session, result=result, basin_id=basin_id, element=element, valid_time=valid_time,
                quality=flags, retrieved_at=data_result.fetched_at, artifact_id=data_result.artifact_id,
            )
    await session.flush()
    return written
