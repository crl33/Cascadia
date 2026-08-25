"""The two susceptibility ingest jobs: build the climatology (annual), rank today against it (daily).

Both write `DerivedFeature` rows and nothing else — no Observation rows, because a day-of-year
climatology is not an observation and today's percentile is a Cascadia Papsukkal derivation, not
a measurement (DOMAIN_MODEL §2.3).

Job 1 · `usgs.build_climatology` (annual). Per basin susceptibility gauge: pull the ENTIRE
approved daily-mean record in one request and build `method:streamflow-doy-climatology@1.0.0`;
then pull the legacy USGS published table and store it SEPARATELY under
`method:usgs-published-doy-stats@1.0.0`. The two are never averaged. The published fetch is
allowed to fail: it is the cross-check, and WaterServices decommissions in Q1 2027 (design §2.2
step 2). A whole ladder is one row with the 366-day ladder in `values_json` — see
`_climatology_row` for why.

Job 2 · `usgs.fetch_daily_percentile` (daily). One `latest-daily` request for every gauge, then
each site's most recent daily mean is ranked inside its stored ladder. Deliberately absent: any
fallback to the 15-minute instantaneous value. A daily mean belongs against a daily-mean
climatology; when the daily mean is stale the surface says so (design §2.2 step 3).

Idempotency is `DATA_DOCTRINE.md` §8: `derived_feature` is append-only and its identity is
(method_id, feature, scope_id, window, valid_time, issued_at), so a re-run finds its own row and
skips rather than updating or duplicating. Recomputation under a changed method is a new
`method_id` and therefore a new row.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.models import Basin, DerivedFeature, Station
from cascade_core.registry import PRODUCT_USGS_DAILY_STATS, PRODUCT_USGS_OGC_DAILY
from cascade_core.timeutils import available_at, utcnow
from cascade_providers_usgs.climatology import (
    METHOD_ID,
    PUBLISHED_METHOD_ID,
    DoyClimatology,
    build_doy_climatology,
    daily_mean_valid_time,
    doy_key,
    from_values_json,
    p50_disagreement,
    percentile_of,
    published_climatology,
)
from cascade_providers_usgs.stats_client import (
    fetch_daily_record,
    fetch_latest_daily,
    fetch_published_doy_stats,
)
from cascade_providers_usgs.stats_parser import (
    parse_daily_csv,
    parse_latest_daily_json,
    parse_nwis_stat_rdb,
)

BUILD_JOB_NAME = "usgs.build_climatology"
BUILD_CADENCE_SECONDS = 31_536_000  # annual; scheduler needs an explicit cron (design §6 stage 2)
DAILY_JOB_NAME = "usgs.fetch_daily_percentile"
DAILY_CADENCE_SECONDS = 86400

CLIMATOLOGY_FEATURE = "streamflow_doy_climatology"
PERCENTILE_FEATURE = "streamflow_doy_percentile"
# Ranking today's flow inside the ladder IS the susceptibility method's step 3, so the row
# carries that method id and cascade_hydrology.susceptibility reads it back under the same one.
PERCENTILE_METHOD_ID = "method:susceptibility-index@0.1.0"
FLOW_UNIT = "cfs"
# Above this the Cascade-built and USGS-published p50 are treated as disagreeing, which costs
# the surface one confidence level and is recorded as a driver (design §2.2 step 2).
DISAGREEMENT_FRACTION = 0.10


async def _susceptibility_gauges(session: AsyncSession) -> list[tuple[str, Station]]:
    """(basin_id, Station) for every basin that names a susceptibility gauge in the seed."""
    basins = list((await session.execute(select(Basin).order_by(Basin.id))).scalars())
    out: list[tuple[str, Station]] = []
    for basin in basins:
        if not basin.susceptibility_gauge_id:
            continue
        station = await session.get(Station, basin.susceptibility_gauge_id)
        if station is not None and station.agency == "usgs":
            out.append((basin.id, station))
    return out


async def _exists(session: AsyncSession, *, method_id: str, feature: str, scope_id: str, valid_time: datetime) -> bool:
    q = (
        select(DerivedFeature.id)
        .where(DerivedFeature.method_id == method_id, DerivedFeature.feature == feature)
        .where(DerivedFeature.scope_id == scope_id, DerivedFeature.window.is_(None))
        .where(DerivedFeature.valid_time == valid_time, DerivedFeature.issued_at.is_(None))
        .limit(1)
    )
    return (await session.execute(q)).scalar_one_or_none() is not None


async def latest_climatology(session: AsyncSession, *, station_id: str, method_id: str = METHOD_ID) -> DoyClimatology | None:
    """The most recently computed stored ladder for a station under one method, or None.

    The write path reads this directly; the API read path goes through
    `Knowledge.latest_derived_feature`, which additionally applies the knowledge-time filter.
    """
    q = (
        select(DerivedFeature)
        .where(DerivedFeature.feature == CLIMATOLOGY_FEATURE, DerivedFeature.scope_id == station_id)
        .where(DerivedFeature.method_id == method_id)
        .order_by(DerivedFeature.valid_time.desc(), DerivedFeature.id.desc())
        .limit(1)
    )
    row = (await session.execute(q)).scalar_one_or_none()
    if row is None or not row.values_json:
        return None
    return from_values_json(row.values_json, method_id=method_id)


def _climatology_row(
    climatology: DoyClimatology,
    *,
    station_id: str,
    valid_time: datetime,
    retrieved_at: datetime,
    product_id: str,
    artifact_id: int | None,
    quality: list[str],
) -> DerivedFeature:
    """One row per build, with the whole 366-day ladder in `values_json`.

    The §2.5 sketch imagined 366 rows per gauge. One row is the better fit for the table that
    was actually built: a ladder has no per-day `valid_time` (it is a statement about a period
    of record, not about a moment), and the identity constraint then means one build = one row,
    which is exactly the append-only semantics wanted. `value` stays NULL because a climatology
    is not a single number.
    """
    return DerivedFeature(
        feature=CLIMATOLOGY_FEATURE,
        scope_kind="station",
        scope_id=station_id,
        window=None,
        valid_time=valid_time,
        issued_at=None,
        computed_at=retrieved_at,
        available_at=available_at(valid_time=valid_time, retrieved_at=retrieved_at),
        method_id=climatology.method_id,
        product_id=product_id,
        value=None,
        values_json=climatology.to_values_json(),
        unit=climatology.unit,
        percentile=None,
        climatology_ref=climatology.climatology_ref,
        confidence_label="moderate" if climatology.method_id == METHOD_ID else "unknown",
        quality=quality,
        inputs=[] if artifact_id is None else [{"table": "raw_artifact", "id": artifact_id}],
        raw_artifact_id=artifact_id,
    )


async def run_build_climatology(
    session: AsyncSession,
    fetcher: ArchivingFetcher,
    *,
    now: datetime | None = None,
    with_cross_check: bool = True,
) -> int:
    """Build (and store) both climatologies for every configured susceptibility gauge."""
    now = now or utcnow()
    written = 0
    for _basin_id, station in await _susceptibility_gauges(session):
        site = station.external_id
        result = await fetch_daily_record(fetcher, session, site=site)
        rows = parse_daily_csv(result.content, site=site)
        climatology = build_doy_climatology(rows, site=site, unit=FLOW_UNIT)
        if not climatology.ladders:
            continue  # no approved record: no ladder, and nothing invented in its place
        last_day = max(r.day for r in rows)
        valid_time, flags = daily_mean_valid_time(last_day, time_zone=station.time_zone)
        if not await _exists(session, method_id=METHOD_ID, feature=CLIMATOLOGY_FEATURE, scope_id=station.id, valid_time=valid_time):
            session.add(_climatology_row(
                climatology, station_id=station.id, valid_time=valid_time, retrieved_at=result.fetched_at,
                product_id=PRODUCT_USGS_OGC_DAILY, artifact_id=result.artifact_id, quality=list(flags),
            ))
            written += 1
        if not with_cross_check:
            continue
        try:
            stat_result = await fetch_published_doy_stats(fetcher, session, site=site)
        except FetchError:
            # The cross-check is allowed to be unavailable; the surface loses a confidence input,
            # never its value. WaterServices decommissions Q1 2027 and this is the rehearsal.
            continue
        published = published_climatology(parse_nwis_stat_rdb(stat_result.content), site=site, unit=FLOW_UNIT)
        if not published.ladders:
            continue
        if not await _exists(session, method_id=PUBLISHED_METHOD_ID, feature=CLIMATOLOGY_FEATURE, scope_id=station.id, valid_time=valid_time):
            session.add(_climatology_row(
                published, station_id=station.id, valid_time=valid_time, retrieved_at=stat_result.fetched_at,
                product_id=PRODUCT_USGS_DAILY_STATS, artifact_id=stat_result.artifact_id, quality=["cross_check_only"],
            ))
            written += 1
    await session.flush()
    return written


async def run_fetch_daily_percentile(session: AsyncSession, fetcher: ArchivingFetcher, *, now: datetime | None = None) -> int:
    """Rank each gauge's latest daily mean inside its stored ladder and append the percentile."""
    now = now or utcnow()
    gauges = await _susceptibility_gauges(session)
    if not gauges:
        return 0
    by_site = {station.external_id: station for _basin_id, station in gauges}
    result = await fetch_latest_daily(fetcher, session, sites=sorted(by_site))
    latest = parse_latest_daily_json(result.content)
    written = 0
    for row in latest:
        station = by_site.get(row.site)
        if station is None or row.raw_value is None:
            continue
        try:
            value = float(row.raw_value)
        except ValueError:
            continue
        climatology = await latest_climatology(session, station_id=station.id)
        if climatology is None:
            continue  # no ladder: susceptibility.assess() reports the specific UNKNOWN reason
        key = doy_key(row.day)
        ladder = climatology.ladders.get(key)
        if ladder is None:
            continue
        ranked = percentile_of(value, ladder)
        valid_time, flags = daily_mean_valid_time(row.day, time_zone=station.time_zone)
        if await _exists(session, method_id=PERCENTILE_METHOD_ID, feature=PERCENTILE_FEATURE, scope_id=station.id, valid_time=valid_time):
            continue
        quality = list(flags) + list(ranked.quality)
        if row.approval_status:
            quality.append(row.approval_status.lower())
        values_json: dict = {
            "day": row.day.isoformat(),
            "doy_key": key,
            "sample_count": ranked.sample_count,
            "ladder": {f"p{p:02d}": ladder.values[p] for p in sorted(ladder.values)},
            "climatology": {"method_id": climatology.method_id, "ref": climatology.climatology_ref,
                            "begin_year": climatology.begin_year, "end_year": climatology.end_year},
            "approval_status": row.approval_status,
        }
        published = await latest_climatology(session, station_id=station.id, method_id=PUBLISHED_METHOD_ID)
        if published is not None:
            disagreement = p50_disagreement(climatology, published, key)
            values_json["cross_check"] = {
                "method_id": PUBLISHED_METHOD_ID,
                "ref": published.climatology_ref,
                "cascade_p50": ladder.values.get(50),
                "published_p50": published.ladders[key].values.get(50) if key in published.ladders else None,
                "disagreement_fraction": None if disagreement is None else round(disagreement, 4),
                "threshold": DISAGREEMENT_FRACTION,
            }
            if disagreement is not None and abs(disagreement) > DISAGREEMENT_FRACTION:
                quality.append("climatology_disagreement")
        else:
            values_json["cross_check"] = None
            quality.append("no_published_cross_check")
        session.add(
            DerivedFeature(
                feature=PERCENTILE_FEATURE,
                scope_kind="station",
                scope_id=station.id,
                window=None,
                valid_time=valid_time,
                issued_at=None,
                computed_at=result.fetched_at,
                available_at=available_at(valid_time=valid_time, retrieved_at=result.fetched_at),
                method_id=PERCENTILE_METHOD_ID,
                product_id=PRODUCT_USGS_OGC_DAILY,
                value=value,
                values_json=values_json,
                unit=FLOW_UNIT,
                percentile=round(ranked.percentile, 2),
                climatology_ref=climatology.climatology_ref,
                confidence_label="unknown",  # the SURFACE decides confidence: gauge ceiling x freshness x agreement
                quality=list(dict.fromkeys(quality)),
                inputs=[{"table": "raw_artifact", "id": result.artifact_id}],
                raw_artifact_id=result.artifact_id,
            )
        )
        written += 1
    await session.flush()
    return written
