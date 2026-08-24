"""Event Zero USGS observation backfill (docs/NEXT_STEPS.md P2, docs/EVENT_ZERO.md T5).

One-off, network. Fetches December 2025 instantaneous stage (00065) + flow (00060) for the
seed stations from the USGS Water Data OGC API (`continuous` collection), archives every raw
page (content-addressed RawArtifact), and appends Observation rows through the idempotent
revision pattern of cascade_providers_usgs.backfill.

Doctrine (ADR-0010 bitemporal honesty, non-negotiable):
- available_at = retrieval time (2026-08-xx), NEVER the historical valid time. A replay at any
  December 2025 clock time correctly sees UNKNOWN for these rows: we did not exist then.
- every row's quality carries 'backfilled'; approval_status (A/P audit trail) is preserved
  verbatim in qualifier_raw.
- absent stations are skipped and reported, never invented (re-run after CONW1 seeding lands).

Auth: env CASCADE_USGS_API_KEY when present (X-Api-Key header, 4000/h); degrades politely to
anonymous (0.5 s min interval, sequential sites) otherwise. No secret is ever printed.

DB resolution: --db-url > env DATABASE_URL > env CASCADE_DB_URL > settings default.
--dry-run fetches and archives raw pages (content-addressed files persist; they are the same
bytes a real run would archive) but rolls back every database row.

Usage:
  python scripts/backfill_event_zero_usgs.py [--sites 12200500,12194000] \
      [--start 2025-12-01T00:00Z] [--end 2026-01-01T00:00Z] [--page-limit N] \
      [--db-url URL] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import logging
import os
import sys

from sqlalchemy import select

from cascade_core.models import JobRun, Station
from cascade_core.objectstore import store_from_settings
from cascade_core.settings import Settings
from cascade_core.timeutils import iso_z, parse_iso, utcnow
from cascade_providers_usgs.backfill import JOB_NAME, backfill_site
from cascade_providers_usgs.ogc_client import build_backfill_fetcher, close_fetcher
from cascade_worker.runtime import Runtime

# The six seed stations (tests/fixtures/geo + cascade_core/seed/stations.json).
DEFAULT_SITES = ["12100490", "12113000", "12119000", "12149000", "12200500", "12213100"]
DEFAULT_START = "2025-12-01T00:00:00Z"
DEFAULT_END = "2026-01-01T00:00:00Z"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="backfill_event_zero_usgs", description=__doc__.splitlines()[0])
    p.add_argument("--sites", default=",".join(DEFAULT_SITES), help="comma-separated USGS site numbers")
    p.add_argument("--start", default=DEFAULT_START, help="valid_time window start, ISO-8601 with offset")
    p.add_argument("--end", default=DEFAULT_END, help="valid_time window end (exclusive), ISO-8601 with offset")
    p.add_argument("--page-limit", type=int, default=10000, help="OGC page size (1..10000)")
    p.add_argument("--db-url", default=None, help="database URL (default: env DATABASE_URL, then CASCADE_DB_URL)")
    p.add_argument("--dry-run", action="store_true", help="fetch+archive+diff but write no database rows")
    return p.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if db_url:
        settings = dataclasses.replace(settings, db_url=db_url)
    rt = Runtime.build(settings)
    fetcher = build_backfill_fetcher(store_from_settings(settings), user_agent=settings.user_agent, api_key=settings.usgs_api_key)
    start, end = parse_iso(args.start), parse_iso(args.end)
    sites = [s.strip() for s in args.sites.split(",") if s.strip()]
    report: dict = {
        "job": JOB_NAME,
        "start": iso_z(start),
        "end": iso_z(end),
        "dry_run": args.dry_run,
        "keyed": settings.usgs_api_key is not None,  # never the key itself
        "sites": [],
        "skipped_absent": [],
        "errors": [],
        "rows_written": 0,
    }
    try:
        async with rt.sessions() as book:
            jr = JobRun(job=JOB_NAME, started_at=utcnow())
            book.add(jr)
            await book.commit()
            for site in sites:  # sequential: polite to the anonymous tier
                async with rt.sessions() as session:
                    station = (
                        await session.execute(select(Station).where(Station.agency == "usgs", Station.external_id == site))
                    ).scalar_one_or_none()
                    if station is None:
                        report["skipped_absent"].append(site)
                        continue
                    try:
                        site_report = await backfill_site(
                            session, fetcher, station=station, start=start, end=end,
                            page_limit=args.page_limit, dry_run=args.dry_run,
                        )
                    except Exception as e:  # keep going: each site commits independently
                        await session.rollback()
                        report["errors"].append({"site": site, "error": f"{type(e).__name__}: {e}"[:500]})
                        continue
                    if args.dry_run:
                        await session.rollback()
                    else:
                        await session.commit()
                    report["sites"].append(site_report.as_dict())
                    report["rows_written"] += site_report.written
            jr.ok = not report["errors"]
            jr.rows_written = 0 if args.dry_run else report["rows_written"]
            jr.error = ("; ".join(e["error"] for e in report["errors"])[:1000]) or None
            jr.finished_at = utcnow()
            await book.commit()
    finally:
        await close_fetcher(fetcher)
        await rt.engine.dispose()
    print(json.dumps(report, indent=1, default=str))
    return 0 if not report["errors"] else 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
