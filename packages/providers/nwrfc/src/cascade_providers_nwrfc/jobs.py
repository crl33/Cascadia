"""``nwrfc.fetch_reservoirs`` — hourly reservoir state for the regulated basins.

21 small requests an hour (7 stations x their PE codes, ~5-10 KB each), each an Observation
row per new instant: variable in {forebay_elevation, storage, inflow, outflow}, units
verbatim, no invented datum. Idempotent per (station, variable): only instants NEWER than the
latest stored one are appended — xml.cgi occasionally re-serves past instants under a
different SHEF code, and rewriting history from a poll would need the revision machinery a
1-hour cadence does not justify (documented limitation; the chosen code rides in
``qualifier_raw`` either way).

A station that does not answer is reported and skipped — six reservoirs of state are not
hostage to the seventh — but if NONE answers the run fails loudly (provider outage, retry).
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.models import Observation, Station
from cascade_core.registry import PRODUCT_NWRFC_RESERVOIR
from cascade_providers_nwrfc.reservoirs import (
    SERIES,
    VARIABLE_BY_PE,
    ReservoirParseError,
    fetch_series,
    parse_series,
)

log = logging.getLogger("cascade.providers.nwrfc")

JOB_NAME = "nwrfc.fetch_reservoirs"
CADENCE_SECONDS = 3600
#: Hourly values arrive ~1-2 h behind (DATA_SOURCES R4); :50 keeps clear of the :00 rush.
CRON = "50 * * * *"

DATUM_UNSTATED = "datum_unstated_by_provider"
MULTI_SOURCE = "multi_source_values_differ"


def station_id(lid: str) -> str:
    return f"station:nwrfc:{lid}"


async def _latest_stored(session: AsyncSession) -> dict[tuple[str, str], datetime]:
    rows = (
        await session.execute(
            select(Observation.station_id, Observation.variable, func.max(Observation.valid_time))
            .where(Observation.product_id == PRODUCT_NWRFC_RESERVOIR)
            .group_by(Observation.station_id, Observation.variable)
        )
    ).all()
    return {(sid, var): t for sid, var, t in rows}


async def run_fetch_reservoirs(
    session: AsyncSession, fetcher: ArchivingFetcher, *, now: datetime | None = None
) -> int:
    seeded = {
        s.id
        for s in (await session.execute(select(Station).where(Station.agency == "nwrfc"))).scalars()
    }
    latest = await _latest_stored(session)
    written = 0
    answered: list[str] = []
    unreachable: list[str] = []
    for lid, pes in SERIES.items():
        sid = station_id(lid)
        if sid not in seeded:
            log.warning("nwrfc: %s not seeded; skipped (re-seed after adding reservoirs.json)", sid)
            continue
        ok = False
        for pe in pes:
            variable = VARIABLE_BY_PE[pe]
            try:
                result = await fetch_series(fetcher, session, lid, pe)
                values = parse_series(result.content, lid=lid, pe=pe)
            except (FetchError, ReservoirParseError) as e:
                log.warning("nwrfc: %s/%s did not answer cleanly (%s); series skipped", lid, pe, e)
                continue
            ok = True
            floor = latest.get((sid, variable))
            for v in values:
                if floor is not None and v.valid_time <= floor.replace(tzinfo=v.valid_time.tzinfo):
                    continue
                quality = [DATUM_UNSTATED] if variable == "forebay_elevation" else []
                if v.disagrees:
                    quality.append(MULTI_SOURCE)
                session.add(
                    Observation(
                        station_id=sid,
                        product_id=PRODUCT_NWRFC_RESERVOIR,
                        variable=variable,
                        value=v.value,
                        unit=v.unit,
                        datum=None,  # never invented (ADR-0009)
                        valid_time=v.valid_time,
                        retrieved_at=result.fetched_at,
                        available_at=result.last_modified or result.fetched_at,
                        quality=quality,
                        qualifier_raw=v.ts_code,
                        raw_artifact_id=result.artifact_id,
                    )
                )
                written += 1
        (answered if ok else unreachable).append(lid)
    await session.flush()
    if answered:
        log.info("nwrfc: %d rows from %s", written, ", ".join(answered))
    if not answered and unreachable:
        raise FetchError("provider_down", f"no reservoir station answered ({', '.join(unreachable)})")
    return written
