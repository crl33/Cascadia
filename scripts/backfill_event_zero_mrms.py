"""Event Zero MRMS QPE backfill from the IEM MTArchive (P6 history; HYDROLOGY §12).

One-off, network. Fetches hourly ``MultiSensor_QPE_01H_Pass2`` grids for the December 2025
window from Iowa State's MTArchive mirror, aggregates them per basin with the SAME method,
masks and sentinel policy as the live ``mrms.fetch_qpe`` job, and appends DerivedFeature rows —
so the hindcast's antecedent-precipitation windows are computed by exactly the arithmetic the
live platform uses.

Doctrine (ADR-0010 bitemporal honesty, the P2 backfill convention):
- ``available_at`` = retrieval time (2026-08-xx), NEVER the historical instant. A knowledge
  replay of December 2025 correctly sees UNKNOWN: this platform did not exist then. What WAS
  knowable is preserved, not fabricated: IEM kept the original file mtimes (measured: the
  2025-12-12 08Z accumulation's Last-Modified is 08:56:51Z — the same ~57 min publication lag
  the live pipeline measures today), and that instant rides in
  ``values_json.original_available_at`` for the P6 hindcast harness to use explicitly.
- every row's quality carries 'backfilled', plus 'gaugeinfl_unavailable_in_archive': the IEM
  mirror does not carry GaugeInflIndex (DATA_SOURCES P1), so the covariate that qualifies the
  live rows cannot exist for these — said, not silently omitted.
- raw grids are NOT archived to the object store: ~1-2 MB x hundreds of hours of bytes that
  IEM has served stably since 2014 would spend the R2 free tier on re-fetchable data. The
  provenance chain instead cites the IEM URL and the sha256 of the exact bytes aggregated
  (``raw_inputs_hash``), which is what a verifier needs to re-derive any row.

DB resolution: --db-url > env DATABASE_URL > env CASCADE_DB_URL > settings default.

Usage:
  python scripts/backfill_event_zero_mrms.py [--start 2025-12-05T00:00Z] [--end 2025-12-16T00:00Z] \
      [--db-url URL] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import os
import sys
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from cascade_core.models import DerivedFeature
from cascade_core.registry import PRODUCT_MRMS_QPE
from cascade_core.timeutils import parse_iso, utcnow
from cascade_providers_mrms.jobs import (
    FEATURE_QPE,
    METHOD_QPE,
    _aggregate,
    _basins,
    _flags,
    _masks_for,
)
from cascade_providers_mrms.parser import parse_mrms_grib

log = logging.getLogger("cascade.backfill.mrms")

ARCHIVE = "https://mtarchive.geol.iastate.edu"
PRODUCT_DIR = "mrms/ncep/MultiSensor_QPE_01H_Pass2"
GEO_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "geo"


def hour_url(t: datetime) -> str:
    return (
        f"{ARCHIVE}/{t:%Y}/{t:%m}/{t:%d}/{PRODUCT_DIR}/"
        f"MultiSensor_QPE_01H_Pass2_00.00_{t:%Y%m%d}-{t:%H}0000.grib2.gz"
    )


async def _stored_hours(session, since: datetime, until: datetime, n_basins: int) -> set[datetime]:
    rows = (
        await session.execute(
            select(DerivedFeature.valid_time).where(
                DerivedFeature.feature == FEATURE_QPE,
                DerivedFeature.valid_time >= since,
                DerivedFeature.valid_time <= until,
            )
        )
    ).all()
    counts: dict[datetime, int] = {}
    for (t,) in rows:
        counts[t] = counts.get(t, 0) + 1
    return {t.replace(tzinfo=UTC) for t, n in counts.items() if n >= n_basins}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-12-05T00:00Z")
    parser.add_argument("--end", default="2025-12-16T00:00Z")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    start, end = parse_iso(args.start), parse_iso(args.end)

    db_url = args.db_url or os.environ.get("DATABASE_URL") or os.environ.get("CASCADE_DB_URL")
    if not db_url:
        print("no database URL (use --db-url or CASCADE_DB_URL)", file=sys.stderr)
        return 2
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1).split("?")[0]

    engine = create_async_engine(db_url, connect_args={"ssl": True} if "neon" in db_url else {})
    written = fetched = skipped = missing = 0
    retrieval = utcnow()
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            basins = await _basins(session)
            if not basins:
                print("no basins seeded", file=sys.stderr)
                return 2
            have = await _stored_hours(session, start, end, len(basins))
            masks = None
            async with httpx.AsyncClient(timeout=120.0, headers={"User-Agent": "CascadiaPapsukkal/0.1 (event-zero backfill)"}) as client:
                t = start
                while t <= end:
                    if t in have:
                        skipped += 1
                        t += timedelta(hours=1)
                        continue
                    url = hour_url(t)
                    r = await client.get(url)
                    if r.status_code != 200:
                        log.warning("%s -> HTTP %s; hour skipped (reported, not invented)", url, r.status_code)
                        missing += 1
                        t += timedelta(hours=1)
                        continue
                    fetched += 1
                    sha = hashlib.sha256(r.content).hexdigest()
                    lm = r.headers.get("last-modified")
                    original = parsedate_to_datetime(lm).astimezone(UTC).isoformat() if lm else None
                    field = parse_mrms_grib(r.content)
                    if masks is None:
                        masks = await _masks_for(session, field.grid, basins, GEO_DIR)
                    for basin in basins:
                        mask = masks.get(basin.id)
                        if mask is None:
                            continue
                        stats = _aggregate(mask, field.values)
                        session.add(
                            DerivedFeature(
                                feature=FEATURE_QPE,
                                scope_kind="basin",
                                scope_id=basin.id,
                                window="1h",
                                valid_time=t,
                                issued_at=None,
                                computed_at=retrieval,
                                available_at=retrieval,  # ADR-0010: we did not exist in 2025
                                method_id=METHOD_QPE,
                                product_id=PRODUCT_MRMS_QPE,
                                value=stats["mean"],
                                values_json={
                                    **stats,
                                    "grid_definition_hash": field.grid.definition_hash,
                                    "masked_area_km2": mask.masked_area_km2,
                                    "archive_source": "iem-mtarchive",
                                    "archive_url": url,
                                    "original_available_at": original,
                                },
                                unit="mm",
                                confidence_label="moderate" if stats["mean"] is not None else "unknown",
                                quality=[*_flags(stats), "backfilled", "gaugeinfl_unavailable_in_archive"],
                                inputs=[{"url": url, "sha256": sha}],
                                raw_inputs_hash=sha,
                                raw_artifact_id=None,
                            )
                        )
                        written += 1
                    await session.flush()
                    await asyncio.sleep(0.5)  # IEM asks for restraint
                    t += timedelta(hours=1)
            if args.dry_run:
                await session.rollback()
                print(f"DRY RUN rolled back: would write {written} rows "
                      f"({fetched} hours fetched, {skipped} already stored, {missing} absent upstream)")
            else:
                await session.commit()
                print(f"wrote {written} rows ({fetched} hours fetched, {skipped} already stored, "
                      f"{missing} absent upstream)")
    finally:
        await engine.dispose()
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(asyncio.run(main()))
