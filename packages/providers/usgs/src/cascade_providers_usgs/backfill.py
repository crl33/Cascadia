"""Event Zero observation backfill (EVENT_ZERO.md T5 at seed-station scope): fetch the OGC
`continuous` collection for one site over a valid-time window (archive every page first) ->
parse -> normalize (quality gains 'backfilled'; available_at = retrieval time, NEVER the
historical valid time — ADR-0010) -> append-only Observation rows.

Idempotency: same pattern as jobs.run_fetch_iv — load the latest known revision per
(variable, valid_time) in the window once, skip identical (value + quality), append a revision
row when changed. The unique key (product, station, variable, valid_time, revision_seq)
protects re-runs. Product is PRODUCT_USGS_IV (the same USGS instantaneous series; the
RawArtifact.request_url records the true OGC endpoint)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import Observation, Station
from cascade_core.registry import PRODUCT_USGS_IV
from cascade_providers_usgs.ogc_client import (
    fetch_continuous_first_page,
    fetch_continuous_next_page,
)
from cascade_providers_usgs.ogc_normalize import to_observation_records
from cascade_providers_usgs.ogc_parser import parse_continuous

log = logging.getLogger(__name__)

JOB_NAME = "usgs.backfill_event_zero"
MAX_PAGES = 50  # a whole month of 15-min stage+flow is ~6k rows; 50 pages of 10k is a hard stop


@dataclass
class SiteBackfillReport:
    site: str
    station_id: str
    pages: int = 0
    features: int = 0
    written: int = 0
    skipped_identical: int = 0
    skipped_non_instantaneous: int = 0
    artifact_ids: list[int] = field(default_factory=list)
    peaks: dict[str, dict] = field(default_factory=dict)  # variable -> {value, unit, valid_time}

    def as_dict(self) -> dict:
        return {
            "site": self.site,
            "station_id": self.station_id,
            "pages": self.pages,
            "features": self.features,
            "written": self.written,
            "skipped_identical": self.skipped_identical,
            "skipped_non_instantaneous": self.skipped_non_instantaneous,
            "artifact_ids": self.artifact_ids,
            "peaks": self.peaks,
        }


async def backfill_site(
    session: AsyncSession,
    fetcher: ArchivingFetcher,
    *,
    station: Station,
    start: datetime,
    end: datetime,
    page_limit: int = 10000,
    dry_run: bool = False,
) -> SiteBackfillReport:
    """Backfill one station's stage+flow observations for [start, end). Caller commits."""
    report = SiteBackfillReport(site=station.external_id, station_id=station.id)
    # Fetch and normalize every page first (each page archived -> its own RawArtifact).
    page_records: list[tuple[int, list]] = []  # (artifact_id, records)
    next_url: str | None = None
    for _page in range(MAX_PAGES):
        if next_url is None and report.pages == 0:
            result = await fetch_continuous_first_page(fetcher, session, site=station.external_id, start=start, end=end, limit=page_limit)
        elif next_url is not None:
            result = await fetch_continuous_next_page(fetcher, session, next_url=next_url)
        else:
            break
        page = parse_continuous(result.content)  # raw already archived by the fetcher
        report.pages += 1
        report.features += page.number_returned
        report.artifact_ids.append(result.artifact_id)
        records, skipped = to_observation_records(
            page.values, retrieved_at=result.fetched_at, station_id=station.id, datum=station.vertical_datum
        )
        report.skipped_non_instantaneous += skipped["non_instantaneous"]
        page_records.append((result.artifact_id, records))
        next_url = page.next_url
        if next_url is None:
            break
    else:
        raise RuntimeError(f"more than {MAX_PAGES} pages for site {station.external_id}; refusing to loop")

    # Latest known revision per (variable, valid_time) in the window, once.
    lo, hi = start - timedelta(seconds=1), end + timedelta(seconds=1)
    existing = (
        await session.execute(
            select(Observation)
            .where(Observation.product_id == PRODUCT_USGS_IV, Observation.station_id == station.id)
            .where(Observation.variable.in_(("stage", "flow")))
            .where(Observation.valid_time >= lo, Observation.valid_time <= hi)
            .order_by(Observation.valid_time, Observation.revision_seq)
        )
    ).scalars()
    latest: dict[tuple[str, datetime], Observation] = {}
    for row in existing:
        latest[(row.variable, row.valid_time)] = row

    for artifact_id, records in page_records:
        for r in records:
            key = (r.variable, r.valid_time)
            prev = latest.get(key)
            if prev is not None and prev.value == r.value and list(prev.quality) == list(r.quality):
                report.skipped_identical += 1
                continue
            if prev is not None and prev.id is None and not dry_run:
                await session.flush()  # a within-run revision chain needs the previous row's id
            row = Observation(
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
                raw_artifact_id=artifact_id,
            )
            if not dry_run:
                session.add(row)
            latest[key] = row
            report.written += 1
            peak = report.peaks.get(r.variable)
            if r.value is not None and (peak is None or r.value > peak["value"]):
                report.peaks[r.variable] = {"value": r.value, "unit": r.unit, "valid_time": r.valid_time.isoformat()}
    if not dry_run:
        await session.flush()
    log.info(
        "backfill %s: pages=%d features=%d written=%d skipped_identical=%d dry_run=%s",
        station.external_id, report.pages, report.features, report.written, report.skipped_identical, dry_run,
    )
    return report
