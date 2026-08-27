"""Measure what the p95 clamp destroys, and which tail representation gets it back.

Evidence behind `docs/research/tail-representation-2026-08-26.md`. Reads the SAME archived
daily-values CSVs the deployed ladders were built from (content-addressed in R2, retention
NULL), so the analysis is bit-consistent with what production actually ranks against — no
re-fetch, no drift, and no USGS API calls.

Run:  CASCADE_DB_URL=... CASCADE_S3_* ... AWS_* ... python scripts/measure_tail_representation.py

Four questions:

  A. RESOLVABLE  how far into the tail does each gauge's own sample reach? A breakpoint with
                 too few observations above it is extrapolation wearing a percentile's clothes.
  B. LOST        how much of December 2025 fell inside the clamped region, and where would the
                 extra breakpoints have placed it?
  C. RANK        above the top breakpoint, can the value be stated as an empirical rank in the
                 ladder's own sample -- a fact, needing no interpolation at all?
  D. DERIVATIVE  does each candidate representation still move through the crest, where the
                 clamped percentile reads identically +0?
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for pkg in ("core", "hydrology", "providers/usgs"):
    sys.path.insert(0, str(ROOT / "packages" / pkg / "src"))

from cascade_core.objectstore import store_from_settings  # noqa: E402
from cascade_core.settings import Settings  # noqa: E402
from cascade_providers_usgs.climatology import (  # noqa: E402
    WINDOW_DAYS,
    doy_key,
    percentile,
    window_keys,
)
from cascade_providers_usgs.stats_parser import parse_daily_csv  # noqa: E402

#: Candidate breakpoints beyond the shipped ladder's p95 ceiling.
CANDIDATE_TAIL = (96, 97, 98, 99, 99.5)
#: How many observed values must lie STRICTLY ABOVE a breakpoint for it to be interpolated from
#: data rather than extrapolated past the end of the sample. Five is the smallest count for
#: which the R-7 rank falls between two real observations with room to spare at every gauge; it
#: is a stated admissibility rule, not a tuned parameter.
TAIL_MIN_EXCEEDANCES = 5
EVENT_DAYS = [date(2025, 12, d) for d in range(1, 23)]


async def load() -> dict[str, dict]:
    """The archived CSV bytes per gauge, addressed through the derived_feature that used them."""
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine

    url = os.environ["CASCADE_DB_URL"].replace("postgresql://", "postgresql+psycopg://")
    engine = create_async_engine(url)
    store = store_from_settings(Settings.from_env(os.environ))
    out: dict[str, dict] = {}
    async with engine.connect() as conn:
        rows = (await conn.execute(sa.text("""
            SELECT DISTINCT ON (d.scope_id) d.scope_id, a.object_key, a.sha256
              FROM derived_feature d JOIN raw_artifact a ON a.id = d.raw_artifact_id
             WHERE d.method_id='method:streamflow-doy-climatology@1.0.0'
               AND d.feature='streamflow_doy_climatology'
             ORDER BY d.scope_id, d.id DESC"""))).all()
        for scope, key, sha in rows:
            site = scope.split(":")[-1]
            out[site] = {"scope": scope, "csv": store.get(key), "sha256": sha}
        # the December daily means the surface actually ranked
        for site, blob in out.items():
            obs = (await conn.execute(sa.text("""
                SELECT date_trunc('day', valid_time)::date d, avg(value) v
                  FROM observation
                 WHERE station_id=:s AND variable='flow'
                   AND valid_time >= '2025-12-01' AND valid_time < '2025-12-23'
                 GROUP BY 1 ORDER BY 1"""), {"s": blob["scope"]})).all()
            blob["december"] = {str(r[0]): float(r[1]) for r in obs}
    await engine.dispose()
    return out


def sample_for(rows, key: str) -> list[float]:
    """The exact sample `build_doy_climatology` would use for one day-of-year key."""
    by_key = defaultdict(list)
    for r in rows:
        if r.approval_status != "Approved" or r.raw_value is None:
            continue
        try:
            v = float(r.raw_value)
        except ValueError:
            continue
        if v < 0:
            continue
        by_key[doy_key(r.day)].append(v)
    out: list[float] = []
    for nb in window_keys(key, window_days=WINDOW_DAYS):
        out.extend(by_key[nb])
    out.sort()
    return out


def years_for(rows, key: str) -> list[tuple[float, int]]:
    """(value, year) pairs in the same window, so a rank can name the year it beat."""
    keys = set(window_keys(key, window_days=WINDOW_DAYS))
    out = []
    for r in rows:
        if r.approval_status != "Approved" or r.raw_value is None or doy_key(r.day) not in keys:
            continue
        try:
            v = float(r.raw_value)
        except ValueError:
            continue
        if v >= 0:
            out.append((v, r.day.year))
    out.sort()
    return out


def main() -> int:
    blobs = asyncio.run(load())
    report: dict = {"generated": datetime.now(timezone.utc).isoformat(), "gauges": {}}

    for site, blob in sorted(blobs.items()):
        rows = parse_daily_csv(blob["csv"], site=site)
        g: dict = {"sha256": blob["sha256"], "days": {}}

        for day_s, flow in sorted(blob["december"].items()):
            key = doy_key(date.fromisoformat(day_s))
            sample = sample_for(rows, key)
            if len(sample) < 10:
                continue
            n = len(sample)
            p95 = percentile(sample, 95)

            # A. which extra breakpoints the sample can actually support
            supported = {}
            for p in CANDIDATE_TAIL:
                v = percentile(sample, p)
                above = sum(1 for x in sample if x > v)
                supported[str(p)] = {"value": v, "exceedances": above,
                                     "resolvable": above >= TAIL_MIN_EXCEEDANCES}

            # C. the empirical rank -- how many of this window's observations it exceeds
            strictly_above = sum(1 for x in sample if x > flow)
            g["days"][day_s] = {
                "flow": flow, "n": n, "p95": p95,
                "clamped": flow >= p95,
                "ratio_to_p95": flow / p95 if p95 else None,
                "rank_from_top": strictly_above + 1,
                "exceeded_by_n_observations": strictly_above,
                "tail": supported,
            }

        # B/D: the clamped stretch and whether each representation still moves through it
        clamped = [(d, v) for d, v in sorted(g["days"].items()) if v["clamped"]]
        if clamped:
            flows = [v["flow"] for _, v in clamped]
            g["clamped_stretch"] = {
                "days": [d for d, _ in clamped],
                "min_flow": min(flows), "max_flow": max(flows),
                "flow_ratio_across_the_clamp": max(flows) / min(flows),
                "distinct_percentiles_reported": 1,
                "distinct_ranks_available": len({v["rank_from_top"] for _, v in clamped}),
                "distinct_ratios_available": len({round(v["ratio_to_p95"], 4) for _, v in clamped}),
                "highest_resolvable_breakpoint": max(
                    [float(p) for p, s in clamped[0][1]["tail"].items() if s["resolvable"]] or [95.0]
                ),
            }
            # D: the day-over-day change each representation produces inside the clamp
            def deltas(fn):
                seq = [fn(v) for _, v in clamped]
                return [round(b - a, 4) for a, b in zip(seq, seq[1:])]
            g["clamped_stretch"]["delta_percentile"] = deltas(lambda v: 95.0)
            g["clamped_stretch"]["delta_ratio"] = deltas(lambda v: v["ratio_to_p95"])
            g["clamped_stretch"]["delta_rank"] = deltas(lambda v: float(v["rank_from_top"]))
        report["gauges"][site] = g

    # storage cost of carrying the top-K sample with the ladder
    sizes = []
    for site, blob in sorted(blobs.items()):
        rows = parse_daily_csv(blob["csv"], site=site)
        key = "12-09"
        top = years_for(rows, key)[-20:]
        sizes.append(len(json.dumps([[round(v, 1), y] for v, y in top])))
    report["storage"] = {
        "bytes_per_day_key_for_top20": statistics.mean(sizes),
        "bytes_per_gauge_366_keys": statistics.mean(sizes) * 366,
        "bytes_for_six_gauges": statistics.mean(sizes) * 366 * 6,
    }
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
