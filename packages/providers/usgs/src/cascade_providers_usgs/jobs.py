"""Idempotent USGS instantaneous job: fetch (archive first) -> parse -> normalize -> append.

TRANSPORT, 2026-08-27: this job reads the USGS Water Data **OGC API** `continuous` collection.
It previously read legacy `waterservices.usgs.gov/nwis/iv/`, which is scheduled for decommission
in Q1 2027 with degradation possible from August 2026. The migration changed the transport and
nothing else: semantic parity was measured over the same gauges and window before cutover and is
recorded in `docs/research/usgs-ogc-instantaneous-parity-2026-08-27.md` — identical values,
units, datums and quality flags, with the only difference being that the OGC API spells an
approval status "Provisional" where NWIS spelled it "P".

Idempotency: the unique key (product, station, variable, valid_time, revision_seq) plus a
compare against the latest known revision: identical values are skipped, changed values become
revision rows (DATA_DOCTRINE §8). This is UNCHANGED from the legacy job, and the parity result is
what makes cutover safe — because `quality` is identical across transports and `qualifier_raw` is
not part of the comparison, the first OGC poll after cutover writes no revisions for observations
the legacy path had already stored.

Shape: the legacy service answered every site in ONE request; the OGC API is per-site, so this
job issues one request per gauge. Seven gauges every 15 minutes is 28 requests/hour against a
keyed limit of 4,000/hour.

NO SILENT FALLBACK. If the OGC API fails, this job fails and `/system/health` says so. It never
quietly reaches for the legacy service, because a transport that changes itself under failure
makes both provenance and outage interpretation ambiguous.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import Observation, Station
from cascade_core.registry import PRODUCT_USGS_IV
from cascade_providers_usgs.ogc_client import LIVE_WINDOW_HOURS, fetch_continuous_window
from cascade_providers_usgs.ogc_normalize import to_observation_records
from cascade_providers_usgs.ogc_parser import parse_continuous

log = logging.getLogger(__name__)

JOB_NAME = "usgs.fetch_instantaneous"
CADENCE_SECONDS = 900
DEFAULT_HOURS = LIVE_WINDOW_HOURS


class NoInstantaneousDataError(RuntimeError):
    """Every gauge answered without a usable observation — a retryable provider condition.

    Reported rather than swallowed: a run that fetched nothing and returned success is exactly
    how a provider outage hides inside a green job.
    """


async def run_fetch_instantaneous(session: AsyncSession, fetcher: ArchivingFetcher, *, hours: int = DEFAULT_HOURS) -> int:
    stations = {s.external_id: s for s in (await session.execute(select(Station).where(Station.agency == "usgs"))).scalars()}
    if not stations:
        return 0
    written = 0
    answered = 0
    for site in sorted(stations):
        station = stations[site]
        result = await fetch_continuous_window(fetcher, session, site=site, hours=hours)
        page = parse_continuous(result.content)  # raw already archived by the fetcher
        if page.next_url is not None:
            # A live window that pages means the cadence assumption is wrong, not that the data
            # should be truncated. Say so; the next run asks again.
            log.warning("usgs ogc live window for %s returned a paged response; window may be too wide", site)
        # The payload must be for the gauge we asked for. The legacy path got this for free by
        # matching `series.site` against the station map; the per-site OGC request makes it
        # tempting to trust the request instead, which would silently file one river's discharge
        # under another's name — the single worst failure mode available to this job.
        foreign = sorted({v.site for v in page.values} - {site})
        if foreign:
            raise ValueError(
                f"OGC continuous page for {site} carries observations for {foreign}; refusing to "
                "attribute them to the requested gauge"
            )
        records, skipped = to_observation_records(
            page.values,
            retrieved_at=result.fetched_at,
            station_id=station.id,
            datum=station.vertical_datum,
            backfilled=False,  # a 15-minute poll is not a backfill; see ogc_normalize
        )
        if skipped.get("non_instantaneous"):
            log.info("usgs ogc: skipped %d non-instantaneous rows for %s", skipped["non_instantaneous"], site)
        if not records:
            continue
        answered += 1
        for variable in sorted({r.variable for r in records}):
            of_variable = [r for r in records if r.variable == variable]
            lo = min(r.valid_time for r in of_variable) - timedelta(seconds=1)
            hi = max(r.valid_time for r in of_variable) + timedelta(seconds=1)
            existing = (
                await session.execute(
                    select(Observation)
                    .where(Observation.product_id == PRODUCT_USGS_IV, Observation.station_id == station.id, Observation.variable == variable)
                    .where(Observation.valid_time >= lo, Observation.valid_time <= hi)
                    .order_by(Observation.valid_time, Observation.revision_seq)
                )
            ).scalars()
            latest: dict = {}
            for row in existing:
                latest[row.valid_time] = row
            for r in of_variable:
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
    if answered == 0 and stations:
        raise NoInstantaneousDataError(
            f"all {len(stations)} gauges answered without a usable instantaneous observation; "
            "the raw responses are archived. Retry rather than recording a successful run that "
            "stored nothing."
        )
    await session.flush()
    return written
