"""Backfill Event Zero T3: December 2025 KSEW FLW/FLS crest statements -> ForecastRun rows.

Fetches every FLWSEW/FLSSEW issuance in the window from the IEM AFOS archive exactly as
scripts/archive_afos_event_zero.py does (day-granular list.json per PIL — that is the
pagination — then /api/1/nwstext/{product_id}, with ?nolimit=1 whenever the listing
reports >1 product stored at the id). Every listing page and every product text goes
through ArchivingFetcher, so the bytes land in the object store with a RawArtifact row
BEFORE any parsing (archive-before-parse); rows are written by
cascade_providers_nwps.afos_jobs.load_crest_products.

Bitemporal honesty (ADR-0010): issued_at = the IEM listing 'entered' transmission time
(FACT; equals the R2 manifest issued_at); available_at = retrieval time, NEVER the
historical issuance time — a replay at T in December 2025 correctly sees UNKNOWN for
these reconstructed runs. supersedes_run_id chains per forecast point by issuance order.
Idempotent: re-runs skip stored (product, fp, issued_at) rows. One JobRun row
(job='nws.backfill_event_zero_fls') records each invocation.

Usage:
    python scripts/backfill_event_zero_fls.py [--start 2025-12-01T00:00Z]
        [--end 2025-12-23T00:00Z] [--pils FLWSEW,FLSSEW] [--dry-run]

--dry-run touches no database and no object store: it fetches the same listings and
texts politely via urllib, parses them, and prints the report plus the MVEW1 chain.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from sqlalchemy import select

from cascade_core.models import DataSource, ForecastRun, ForecastValue, SourceProduct
from cascade_core.registry import PRODUCT_NWS_FLS_CREST, PRODUCTS, SOURCES, SRC_NWS_AFOS
from cascade_core.settings import Settings
from cascade_core.timeutils import iso_z, parse_iso
from cascade_providers_nwps.afos import parse_afos
from cascade_providers_nwps.afos_jobs import (
    JOB_BACKFILL_FLS,
    AfosLoadReport,
    forecast_points_by_lid,
    load_crest_products,
)
from cascade_worker.runtime import Runtime, run_job

IEM_HOST = "mesonet.agron.iastate.edu"
API = f"https://{IEM_HOST}/api/1"
ALLOWED_HOSTS = frozenset({IEM_HOST})
UA = {"User-Agent": "CascadiaPapsukkal/0.1 (event-zero FLW/FLS backfill)"}
PAUSE_S = 0.3

# docs/EVENT_ZERO.md §8 forecast-evolution table for MVEW1 (corrected 2026-08-24 to the
# byte record; see tests/unit/test_nws_afos.py and the §8 correction note), printed
# beside the stored chain.
DOC_GOLDEN = (
    ("2025-12-09T17:01Z", 36.9),
    ("2025-12-10T01:24Z", 41.5),
    ("2025-12-10T08:54Z", 41.5),
    ("2025-12-10T16:47Z", 41.5),
    ("2025-12-10T19:01Z", 41.5),
    ("2025-12-10T23:14Z", 42.3),
    ("2025-12-11T02:21Z", 42.1),
    ("2025-12-11T06:47Z", 41.3),
    ("2025-12-11T10:04Z", 39.7),
    ("2025-12-11T18:17Z", 39.1),
    ("2025-12-12T01:12Z", 38.3),
    ("2025-12-12T08:50Z", 38.1),
)


def _days(start: datetime, end: datetime):
    d = start.date()
    last = (end - timedelta(microseconds=1)).date()
    while d <= last:
        yield d
        d += timedelta(days=1)


def _listing_rows(payload: bytes, *, pil: str, start: datetime, end: datetime) -> list[dict]:
    rows = []
    for row in json.loads(payload).get("data") or []:
        entered = parse_iso(row["entered"])
        if not (start <= entered < end):
            continue
        url = row["text_link"]
        if int(row.get("count") or 1) > 1:
            url += "?nolimit=1"  # capture every product stored at this id
        rows.append({"pil": pil, "product_id": row["product_id"], "entered": entered, "url": url})
    return rows


def _print_doc_table() -> None:
    print("\ndocs/EVENT_ZERO.md §8 golden table (MVEW1):")
    for issued, crest in DOC_GOLDEN:
        print(f"  {issued}  {crest} ft")


async def _print_chain(rt: Runtime) -> None:
    async with rt.sessions() as session:
        rows = (
            await session.execute(
                select(ForecastRun, ForecastValue)
                .join(ForecastValue, ForecastValue.run_id == ForecastRun.id)
                .where(
                    ForecastRun.product_id == PRODUCT_NWS_FLS_CREST,
                    ForecastRun.fp_id == "fp:nwps:MVEW1",
                )
                .order_by(ForecastRun.issued_at)
            )
        ).all()
    print(f"\nStored MVEW1 chain ({len(rows)} runs, product {PRODUCT_NWS_FLS_CREST}):")
    for run, value in rows:
        crest = value.stage if value.stage is not None else value.flow
        print(
            f"  issued {iso_z(run.issued_at)}  crest {crest} {run.unit}"
            f"  crest_time {iso_z(value.valid_time)}  available {iso_z(run.available_at)}"
            f"  supersedes {run.supersedes_run_id}  artifact {run.raw_artifact_id}"
        )
    _print_doc_table()


def _fetch_polite(url: str) -> bytes:
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            data = urllib.request.urlopen(req, timeout=120).read()
            time.sleep(PAUSE_S)
            return data
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _dry_run(pils: list[str], start: datetime, end: datetime) -> None:
    rows: list[dict] = []
    seen: set[str] = set()
    for pil in pils:
        for day in _days(start, end):
            q = urllib.parse.urlencode({"pil": pil, "date": day.isoformat()})
            for r in _listing_rows(_fetch_polite(f"{API}/nws/afos/list.json?{q}"), pil=pil, start=start, end=end):
                if r["product_id"] not in seen:
                    seen.add(r["product_id"])
                    rows.append(r)
    rows.sort(key=lambda r: (r["entered"], r["product_id"]))
    chain: list[tuple[datetime, float, str]] = []
    n_segments = n_crests = 0
    for r in rows:
        for product in parse_afos(_fetch_polite(r["url"])):
            for seg in product.segments:
                if seg.lid is None:
                    continue
                n_segments += 1
                crest = seg.crest
                if crest is None or seg.hvtec is None or seg.hvtec.crest is None:
                    continue
                n_crests += 1
                if seg.lid == "MVEW1":
                    chain.append((r["entered"], crest.value, crest.unit))
    print(f"DRY RUN: {len(rows)} products, {n_segments} LID segments, {n_crests} storable crests; nothing written")
    print(f"\nMVEW1 chain from product text ({len(chain)} issuances):")
    for entered, value, unit in chain:
        print(f"  issued {iso_z(entered)}  crest {value} {unit}")
    _print_doc_table()


async def _run(pils: list[str], start: datetime, end: datetime) -> int:
    settings = Settings.from_env()
    rt = Runtime.build(settings)
    try:
        async with rt.sessions() as session:  # registry rows may predate this product
            for src in SOURCES:
                if src["id"] == SRC_NWS_AFOS:
                    await session.merge(DataSource(**src))
            for prod in PRODUCTS:
                if prod["id"] == PRODUCT_NWS_FLS_CREST:
                    await session.merge(SourceProduct(**prod))  # type: ignore[arg-type]
            await session.commit()

        report = AfosLoadReport()

        async def fn(session, fetcher) -> int:
            fp_by_lid = await forecast_points_by_lid(session)
            print(f"seeded forecast points: {sorted(fp_by_lid)}", flush=True)
            rows: list[dict] = []
            seen: set[str] = set()
            for pil in pils:
                for day in _days(start, end):
                    res = await fetcher.fetch(
                        session,
                        url=f"{API}/nws/afos/list.json",
                        params={"pil": pil, "date": day.isoformat()},
                        allowed_hosts=ALLOWED_HOSTS,
                        product_id=PRODUCT_NWS_FLS_CREST,
                        suffix=".json",
                    )
                    for r in _listing_rows(res.content, pil=pil, start=start, end=end):
                        if r["product_id"] not in seen:
                            seen.add(r["product_id"])
                            rows.append(r)
            rows.sort(key=lambda r: (r["entered"], r["product_id"]))
            print(f"{len(rows)} products listed in window", flush=True)
            total = 0
            for i, r in enumerate(rows, 1):
                res = await fetcher.fetch(
                    session,
                    url=r["url"],
                    params=None,
                    allowed_hosts=ALLOWED_HOSTS,
                    product_id=PRODUCT_NWS_FLS_CREST,
                    suffix=".txt",
                )
                total += await load_crest_products(
                    session,
                    content=res.content,
                    issued_at=r["entered"],
                    retrieved_at=res.fetched_at,
                    raw_artifact_id=res.artifact_id,
                    fp_by_lid=fp_by_lid,
                    report=report,
                )
                await session.commit()  # idempotent re-runs resume cheaply
                if i % 50 == 0:
                    print(f"  {i}/{len(rows)} products processed", flush=True)
            return total

        jr = await run_job(rt, JOB_BACKFILL_FLS, fn)
        print(f"\njob {jr.job}: ok={jr.ok} rows_written={jr.rows_written} error={jr.error}")
        print(report.summary())
        await _print_chain(rt)
        return 0 if jr.ok else 1
    finally:
        await rt.engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", default="2025-12-01T00:00Z", help="window start, ISO-8601 UTC (inclusive)")
    ap.add_argument("--end", default="2025-12-23T00:00Z", help="window end, ISO-8601 UTC (exclusive)")
    ap.add_argument("--pils", default="FLWSEW,FLSSEW", help="comma-separated AFOS PILs")
    ap.add_argument("--dry-run", action="store_true", help="fetch+parse only; no DB, no object store")
    args = ap.parse_args()
    start, end = parse_iso(args.start), parse_iso(args.end)
    pils = [p.strip().upper() for p in args.pils.split(",") if p.strip()]
    if args.dry_run:
        _dry_run(pils, start, end)
        return
    sys.exit(asyncio.run(_run(pils, start, end)))


if __name__ == "__main__":
    main()
