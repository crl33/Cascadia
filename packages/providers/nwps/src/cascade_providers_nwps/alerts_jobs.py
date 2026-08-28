"""``nws.fetch_alerts`` — poll active WA alerts, store append-only, route to basins by UGC.

Idempotent by CAP id: an alert already stored is skipped, an Update or Cancel arrives as a NEW id
whose ``references`` name what it supersedes, and no row ever mutates — so the alert set known at
any past instant replays exactly (``available_at`` is the poll that first held the bytes, not the
NWS ``sent`` time; a poll loop learns an alert minutes late and a replay must not pretend
otherwise).

Nothing here filters by event type. A "Flood Warning" and an "Air Quality Alert" are both
knowledge; which events a SURFACE displays is the consumer's versioned policy, and filtering at
ingest would make that policy invisible and unauditable.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import OfficialAlertRecord
from cascade_providers_nwps.alerts import (
    fetch_active_alerts,
    load_ugc_mapping,
    parse_active_alerts,
)

log = logging.getLogger("cascade.providers.nws.alerts")

JOB_NAME = "nws.fetch_alerts"
#: Five minutes: alerts carry Cache-Control max-age=5 upstream, and the provider's abusive-user
#: page allows far more than this. The poll is one ~5-50 KB request.
CADENCE_SECONDS = 300


async def run_fetch_alerts(
    session: AsyncSession, fetcher: ArchivingFetcher, *, geo_dir: Path
) -> int:
    mapping = load_ugc_mapping(geo_dir / "basin_ugc.json")
    result = await fetch_active_alerts(fetcher, session)
    alerts = parse_active_alerts(result.content)
    if not alerts:
        # An empty active list is a legitimate, common answer — quiet weather, not an outage.
        return 0
    have = {
        alert_id
        for (alert_id,) in await session.execute(
            select(OfficialAlertRecord.id).where(
                OfficialAlertRecord.id.in_([a.id for a in alerts])
            )
        )
    }
    written = 0
    for alert in alerts:
        if alert.id in have:
            continue
        basin_ids = mapping.basins_for(alert.ugc)
        session.add(
            OfficialAlertRecord(
                id=alert.id,
                event=alert.event,
                status=alert.status,
                message_type=alert.message_type,
                severity=alert.severity,
                certainty=alert.certainty,
                urgency=alert.urgency,
                headline=alert.headline,
                sender_name=alert.sender_name,
                sent=alert.sent,
                onset=alert.onset,
                expires=alert.expires,
                ends=alert.ends,
                ugc=list(alert.ugc),
                basin_ids=list(basin_ids),
                mapping_method_id=mapping.method_id,
                references=list(alert.references),
                retrieved_at=result.fetched_at,
                available_at=result.fetched_at,
                raw_artifact_id=result.artifact_id,
            )
        )
        written += 1
        if basin_ids:
            log.info("alert %s (%s) -> %s", alert.event, alert.id[-12:], ", ".join(basin_ids))
    await session.flush()
    return written
