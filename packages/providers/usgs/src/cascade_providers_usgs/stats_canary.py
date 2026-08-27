"""Live canary (network; never in CI) for the susceptibility data path.

Three questions, in the order they would break the surface:

1. Does OGC ``daily`` still return a whole period of record in one request? That single fact is
   what makes the platform's own climatology possible (design §2.1).
2. Does ``latest-daily`` still carry a complete daily mean, and how old is it? The surface goes
   UNKNOWN past 48 h, so the canary reports the age rather than a bare "ok".
3. Does the published cross-check still answer, and by how much does it disagree with the
   ladder Cascadia built itself? A failure here is NOT an outage — the surface keeps its value
   and loses a confidence input. Coverage is probed at TWO sites because it is per-site and
   inconsistent: on 2026-08-27 the Sauk had a full 366-day ladder and the Skagit outlet had
   nothing, from either published source.

The ``nwis/stat`` question this canary used to ask was retired on 2026-08-27 along with the last
call to ``waterservices.usgs.gov`` (docs/research/nwis-stat-successor-2026-08-27.md).
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime

import httpx

from cascade_providers_usgs.climatology import (
    build_doy_climatology,
    doy_key,
    percentile_of,
)
from cascade_providers_usgs.stats_client import (
    DAILY_MEAN_STATISTIC,
    DAILY_PROPERTIES,
    DAILY_URL,
    DISCHARGE_CODE,
    LATEST_DAILY_URL,
    OBSERVATION_NORMALS_URL,
)
from cascade_providers_usgs.stats_parser import (
    parse_daily_csv,
    parse_latest_daily_json,
    parse_ogc_normals_json,
)

# The six basin susceptibility gauges (seed/p3_surfaces.json). The Skagit's is the Sauk.
GAUGES = ["12213100", "12149000", "12119000", "12189500", "12113000", "12100490"]
PROBE_SITE = "12189500"  # the Sauk: unregulated, 98-year record


async def check(contact: str = "cascadia-papsukkal@example.invalid") -> dict:
    report: dict = {"provider": "usgs-statistics-and-daily", "reachable": False, "schema_ok": False}
    try:
        headers = {"User-Agent": f"CascadiaPapsukkal-canary (+contact: {contact})"}
        async with httpx.AsyncClient(timeout=180, follow_redirects=True, headers=headers) as c:
            r = await c.get(DAILY_URL, params={
                "monitoring_location_id": f"USGS-{PROBE_SITE}", "parameter_code": DISCHARGE_CODE,
                "statistic_id": DAILY_MEAN_STATISTIC, "f": "csv", "skipGeometry": "true",
                "limit": "50000", "properties": DAILY_PROPERTIES})
            report["reachable"] = r.status_code == 200
            report["http_status"] = r.status_code
            rows = parse_daily_csv(r.content, site=PROBE_SITE)
            climatology = build_doy_climatology(rows, site=PROBE_SITE)
            report["daily_record"] = {
                "site": PROBE_SITE, "bytes": len(r.content), "rows": len(rows),
                "first_day": rows[0].day.isoformat() if rows else None,
                "last_day": rows[-1].day.isoformat() if rows else None,
                "ladder_days": len(climatology.ladders), "ref": climatology.climatology_ref,
            }

            await asyncio.sleep(1.0)
            r2 = await c.get(LATEST_DAILY_URL, params={
                "monitoring_location_id": ",".join(f"USGS-{s}" for s in GAUGES),
                "parameter_code": DISCHARGE_CODE, "f": "json", "skipGeometry": "true", "limit": "50"})
            latest = parse_latest_daily_json(r2.content)
            today = datetime.now(UTC).date()
            report["latest_daily"] = {
                v.site: {"day": v.day.isoformat(), "age_days": (today - v.day).days,
                         "value": v.raw_value, "approval": v.approval_status}
                for v in latest
            }
            report["gauges_missing_a_daily_mean"] = sorted(set(GAUGES) - {v.site for v in latest})

            # Probe TWO sites: coverage is per-site and inconsistent, and a one-site probe would
            # report whichever answer it happened to hit as the state of the API.
            report["doy_normals"] = {
                "note": "per-site coverage; on 2026-08-27 12189500 had 366 percentile days and 12200500 had none",
            }
            for site in (PROBE_SITE, "12200500"):
                await asyncio.sleep(1.0)
                r3 = await c.get(OBSERVATION_NORMALS_URL, params={
                    "monitoring_location_id": f"USGS-{site}", "normal_type": "DOY",
                    "parameter_code": DISCHARGE_CODE})
                published = parse_ogc_normals_json(r3.content) if r3.status_code == 200 else ()
                entry: dict = {
                    "http_status": r3.status_code,
                    "percentile_days": len(published),
                    # Reported, not asserted: this API serves the literal string "nan" for
                    # percentiles it cannot compute, so a level going missing is a real signal.
                    "levels": sorted({p for stat in published for p in stat.percentiles}),
                }
                if site == PROBE_SITE and published:
                    key = doy_key(today)
                    ladder = climatology.ladders.get(key)
                    match = next((stat for stat in published if f"{stat.month:02d}-{stat.day:02d}" == key), None)
                    if ladder and match and match.percentiles.get(50):
                        entry["p50_disagreement_today"] = round(
                            (ladder.values[50] - match.percentiles[50]) / match.percentiles[50], 4)
                    mine = next((v for v in latest if v.site == PROBE_SITE), None)
                    if ladder and mine and mine.raw_value:
                        ranked = percentile_of(float(mine.raw_value), ladder)
                        report["percentile_today"] = {"site": PROBE_SITE, "percentile": round(ranked.percentile, 1),
                                                      "quality": list(ranked.quality), "n": ranked.sample_count}
                report["doy_normals"][site] = entry
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
