"""Idempotent USGS IV job: fetch (archive first) -> parse -> normalize -> append.

Idempotency: the unique key (product, station, variable, valid_time, revision_seq) plus a
compare against the latest known revision: identical values are skipped, changed values become
revision rows (DATA_DOCTRINE §8). Default window 72 h; scheduled every 15 min."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import Observation, Station
from cascade_core.registry import PRODUCT_USGS_IV
from cascade_providers_usgs.client import fetch_iv
from cascade_providers_usgs.normalize import to_observations
from cascade_providers_usgs.parser import parse_iv

JOB_NAME = "usgs.fetch_iv"
CADENCE_SECONDS = 900
DEFAULT_HOURS = 72


async def run_fetch_iv(session: AsyncSession, fetcher: ArchivingFetcher, *, hours: int = DEFAULT_HOURS) -> int:
    stations = {s.external_id: s for s in (await session.execute(select(Station).where(Station.agency == "usgs"))).scalars()}
    if not stations:
        return 0
    result = await fetch_iv(fetcher, session, sites=sorted(stations), hours=hours)
    series_list = parse_iv(result.content)  # raw already archived by the fetcher
    written = 0
    for series in series_list:
        station = stations.get(series.site)
        if station is None:
            continue
        records = to_observations(series, retrieved_at=result.fetched_at, station_id=station.id, datum=station.vertical_datum)
        if not records:
            continue
        lo = min(r.valid_time for r in records) - timedelta(seconds=1)
        hi = max(r.valid_time for r in records) + timedelta(seconds=1)
        existing = (
            await session.execute(
                select(Observation)
                .where(Observation.product_id == PRODUCT_USGS_IV, Observation.station_id == station.id, Observation.variable == series.variable)
                .where(Observation.valid_time >= lo, Observation.valid_time <= hi)
                .order_by(Observation.valid_time, Observation.revision_seq)
            )
        ).scalars()
        latest: dict = {}
        for row in existing:
            latest[row.valid_time] = row
        for r in records:
            prev = latest.get(r.valid_time)
            if prev is not None and prev.value == r.value and list(prev.quality) == list(r.quality):
                continue
            session.add(
                Observation(
                    station_id=r.station_id,
                    product_id=PRODUCT_USGS_IV,
                    variable=r.variable,
                    value=r.value,
                    unit=r.unit,
                    datum=r.datum,
                    valid_time=r.valid_time,
                    retrieved_at=r.retrieved_at,
                    available_at=r.available_at,
                    quality=list(r.quality),
                    qualifier_raw=r.qualifier_raw,
                    revision_of=None if prev is None else prev.id,
                    revision_seq=0 if prev is None else prev.revision_seq + 1,
                    raw_artifact_id=result.artifact_id,
                )
            )
            written += 1
    await session.flush()
    return written
