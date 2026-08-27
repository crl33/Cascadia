"""Semantic parity between the legacy NWIS IV path and the OGC `continuous` path.

Evidence behind `docs/research/usgs-ogc-instantaneous-parity-2026-08-27.md`. Fetches BOTH
endpoints for the same seeded gauges over the same window, runs each through its OWN shipped
parser and normalizer, and compares the resulting semantic rows — station, variable, valid time,
value, unit, quality — rather than raw JSON. Raw JSON differences are expected and uninteresting;
a difference in what lands in `observation` is the whole question.

Run:  python scripts/compare_usgs_iv_ogc.py [--hours 3] [--out report.json]

Anonymous by default. The registered key lives only in the Railway environment (owner directive
2026-08-24) and is not needed for six sites over a few hours; `--api-key-env NAME` exists for a
keyed run somewhere that legitimately holds it.

Writes nothing to any database. The archive store is a temporary directory, discarded on exit.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for pkg in ("core", "providers/usgs"):
    sys.path.insert(0, str(ROOT / "packages" / pkg / "src"))

import httpx  # noqa: E402

from cascade_core.fetch import ArchivingFetcher, HostRateLimiter  # noqa: E402
from cascade_core.objectstore import LocalFilesystemStore  # noqa: E402
from cascade_providers_usgs import client as iv_client  # noqa: E402
from cascade_providers_usgs import ogc_client  # noqa: E402
from cascade_providers_usgs.normalize import to_observations  # noqa: E402
from cascade_providers_usgs.ogc_normalize import BACKFILLED_FLAG, to_observation_records  # noqa: E402
from cascade_providers_usgs.ogc_parser import parse_continuous  # noqa: E402
from cascade_providers_usgs.parser import parse_iv  # noqa: E402

SITES = ["12100490", "12113000", "12119000", "12149000", "12189500", "12200500", "12213100"]
STATION = {s: f"station:usgs:{s}" for s in SITES}
DATUM = "NGVD29"  # only affects the stage rows' datum field; identical on both sides by construction


class _NullSession:
    """The fetcher wants a session to append a RawArtifact row; this run persists nothing."""

    def add(self, _obj) -> None: ...
    async def flush(self) -> None: ...


async def _fetch_iv(fetcher, session, hours: int):
    result = await iv_client.fetch_iv(fetcher, session, sites=SITES, hours=hours)
    rows = []
    for series in parse_iv(result.content):
        station = STATION.get(series.site)
        if station is None:
            continue
        rows.extend(to_observations(series, retrieved_at=result.fetched_at, station_id=station, datum=DATUM))
    return rows, len(result.content), 1


async def _fetch_ogc(fetcher, session, hours: int):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    rows, total_bytes, requests = [], 0, 0
    for site in SITES:
        result = await ogc_client.fetch_continuous_first_page(
            fetcher, session, site=site, start=start, end=end, limit=10000,
        )
        requests += 1
        total_bytes += len(result.content)
        page = parse_continuous(result.content)
        pages = [page]
        while page.next_url:
            result = await ogc_client.fetch_continuous_next_page(fetcher, session, next_url=page.next_url)
            requests += 1
            total_bytes += len(result.content)
            page = parse_continuous(result.content)
            pages.append(page)
        for p in pages:
            recs, _ = to_observation_records(
                p.values, retrieved_at=result.fetched_at, station_id=STATION[site], datum=DATUM,
            )
            rows.extend(recs)
    return rows, total_bytes, requests


def _key(r):
    return (r.station_id, r.variable, r.valid_time.astimezone(timezone.utc).isoformat())


def compare(iv_rows, ogc_rows) -> dict:
    """Semantic row comparison. `backfilled` is stripped from the OGC side and reported: it is a
    property of the BACKFILL adapter, not of the transport, and a live adapter must not set it."""
    iv = {_key(r): r for r in iv_rows}
    ogc = {}
    stripped_backfilled = 0
    for r in ogc_rows:
        q = tuple(x for x in r.quality if x != BACKFILLED_FLAG)
        if len(q) != len(r.quality):
            stripped_backfilled += 1
        ogc[_key(r)] = (r, q)

    only_iv = sorted(set(iv) - set(ogc))
    only_ogc = sorted(set(ogc) - set(iv))
    both = sorted(set(iv) & set(ogc))

    diffs = defaultdict(list)
    for k in both:
        a, (b, bq) = iv[k], ogc[k]
        if a.value != b.value:
            if a.value is not None and b.value is not None and abs(a.value - b.value) < 1e-9:
                pass
            else:
                diffs["value"].append({"key": k, "iv": a.value, "ogc": b.value})
        if a.unit != b.unit:
            diffs["unit"].append({"key": k, "iv": a.unit, "ogc": b.unit})
        if a.datum != b.datum:
            diffs["datum"].append({"key": k, "iv": a.datum, "ogc": b.datum})
        if set(a.quality) != set(bq):
            diffs["quality"].append({"key": k, "iv": sorted(a.quality), "ogc": sorted(bq)})
        if a.qualifier_raw != b.qualifier_raw:
            diffs["qualifier_raw"].append({"key": k, "iv": a.qualifier_raw, "ogc": b.qualifier_raw})

    # Publication latency: the newest valid_time each transport was willing to serve, per gauge
    # and variable. A transport that publishes the same measurement sooner is the operationally
    # interesting difference, and it does not show up in a row-by-row value comparison.
    newest = defaultdict(lambda: {"iv": None, "ogc": None})
    for (st, var, t) in iv:
        k = f"{st}:{var}"
        if newest[k]["iv"] is None or t > newest[k]["iv"]:
            newest[k]["iv"] = t
    for (st, var, t) in ogc:
        k = f"{st}:{var}"
        if newest[k]["ogc"] is None or t > newest[k]["ogc"]:
            newest[k]["ogc"] = t
    from datetime import datetime as _dt
    lead = {}
    for k, v in newest.items():
        if v["iv"] and v["ogc"]:
            a = _dt.fromisoformat(v["iv"]); b = _dt.fromisoformat(v["ogc"])
            lead[k] = {"iv_newest": v["iv"], "ogc_newest": v["ogc"],
                       "ogc_lead_minutes": round((b - a).total_seconds() / 60, 1)}

    per_gauge = defaultdict(lambda: defaultdict(lambda: {"iv": 0, "ogc": 0, "both": 0}))
    for (st, var, _t) in iv:
        per_gauge[st][var]["iv"] += 1
    for (st, var, _t) in ogc:
        per_gauge[st][var]["ogc"] += 1
    for (st, var, _t) in both:
        per_gauge[st][var]["both"] += 1

    return {
        "counts": {"iv": len(iv), "ogc": len(ogc), "matched": len(both),
                   "only_iv": len(only_iv), "only_ogc": len(only_ogc),
                   "ogc_rows_carrying_backfilled": stripped_backfilled},
        "per_gauge": {k: dict(v) for k, v in sorted(per_gauge.items())},
        "differences": {k: v for k, v in diffs.items()},
        "difference_counts": {k: len(v) for k, v in diffs.items()},
        "publication_lead": dict(sorted(lead.items())),
        "only_iv_sample": only_iv[:10],
        "only_ogc_sample": only_ogc[:10],
    }


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=3)
    ap.add_argument("--out", default="")
    ap.add_argument("--api-key-env", default="CASCADE_USGS_API_KEY")
    args = ap.parse_args()

    api_key = os.environ.get(args.api_key_env) or None
    session = _NullSession()
    with tempfile.TemporaryDirectory() as tmp:
        store = LocalFilesystemStore(Path(tmp))
        ua = "CascadiaPapsukkal/0.1 (IV-vs-OGC parity comparator)"
        iv_fetcher = ArchivingFetcher(store=store, user_agent=ua, timeout_s=60.0,
                                      limiter=HostRateLimiter(min_interval_s=0.5, max_concurrency=2))
        headers = {"User-Agent": ua, "Accept": "application/json"}
        if api_key:
            headers["X-Api-Key"] = api_key
        ogc_http = httpx.AsyncClient(timeout=60.0, follow_redirects=False, headers=headers)
        ogc_fetcher = ArchivingFetcher(store=store, user_agent=ua, timeout_s=60.0,
                                       limiter=HostRateLimiter(min_interval_s=0.5, max_concurrency=2),
                                       client=ogc_http)
        t0 = datetime.now(timezone.utc)
        iv_rows, iv_bytes, iv_reqs = await _fetch_iv(iv_fetcher, session, args.hours)
        t1 = datetime.now(timezone.utc)
        ogc_rows, ogc_bytes, ogc_reqs = await _fetch_ogc(ogc_fetcher, session, args.hours)
        t2 = datetime.now(timezone.utc)
        await ogc_http.aclose()

    report = {
        "window_hours": args.hours,
        "keyed": bool(api_key),
        "transport": {
            "iv": {"requests": iv_reqs, "bytes": iv_bytes, "seconds": round((t1 - t0).total_seconds(), 2)},
            "ogc": {"requests": ogc_reqs, "bytes": ogc_bytes, "seconds": round((t2 - t1).total_seconds(), 2)},
        },
        **compare(iv_rows, ogc_rows),
    }
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    if args.out:
        Path(args.out).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
