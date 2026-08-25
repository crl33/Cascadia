"""Live canary (network; never in CI) for the susceptibility data path.

Four questions, in the order they would break the surface:

1. Does OGC ``daily`` still return a whole period of record in one request? That single fact is
   what makes the platform's own climatology possible (design §2.1).
2. Does ``latest-daily`` still carry a complete daily mean, and how old is it? The surface goes
   UNKNOWN past 48 h, so the canary reports the age rather than a bare "ok".
3. Is the legacy ``nwis/stat`` cross-check still alive? It decommissions in Q1 2027 and this is
   how the platform finds out — a failure here is expected eventually and is NOT an outage.
4. Has the modern statistics API started serving discharge normals yet? Verified absent
   2026-08-24. If ``discharge_normals`` ever goes non-zero, design §2.1's OPEN QUESTION is
   answered and the cross-check gains a second, supported source.
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
    NWIS_STAT_URL,
    OBSERVATION_NORMALS_URL,
)
from cascade_providers_usgs.stats_parser import (
    parse_daily_csv,
    parse_latest_daily_json,
    parse_nwis_stat_rdb,
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

            await asyncio.sleep(1.0)
            r3 = await c.get(NWIS_STAT_URL, params={
                "format": "rdb", "sites": PROBE_SITE, "statReportType": "daily",
                "statTypeCd": "all", "parameterCd": DISCHARGE_CODE})
            report["nwis_stat"] = {"http_status": r3.status_code, "alive": r3.status_code == 200}
            if r3.status_code == 200:
                published = parse_nwis_stat_rdb(r3.content)
                report["nwis_stat"]["rows"] = len(published)
                key = doy_key(today)
                ladder = climatology.ladders.get(key)
                match = next((s for s in published if f"{s.month:02d}-{s.day:02d}" == key), None)
                if ladder and match and 50 in match.percentiles and match.percentiles[50]:
                    report["nwis_stat"]["p50_disagreement_today"] = round(
                        (ladder.values[50] - match.percentiles[50]) / match.percentiles[50], 4)
                mine = next((v for v in latest if v.site == PROBE_SITE), None)
                if ladder and mine and mine.raw_value:
                    ranked = percentile_of(float(mine.raw_value), ladder)
                    report["percentile_today"] = {"site": PROBE_SITE, "percentile": round(ranked.percentile, 1),
                                                  "quality": list(ranked.quality), "n": ranked.sample_count}

            # Probe TWO sites: coverage is per-site and inconsistent (2026-08-24: the Sauk has a
            # full 366-day percentile ladder, the Skagit outlet has nothing), and a one-site
            # probe would report whichever answer it happened to hit as the state of the API.
            report["statistics_v0"] = {
                "note": "per-site coverage; 12189500 had 366 percentile days and 12200500 had none on 2026-08-24",
            }
            for site in (PROBE_SITE, "12200500"):
                await asyncio.sleep(1.0)
                r4 = await c.get(OBSERVATION_NORMALS_URL, params={
                    "monitoring_location_id": f"USGS-{site}", "normal_type": "DOY",
                    "parameter_code": DISCHARGE_CODE})
                doc = r4.json() if r4.status_code == 200 else {}
                blocks = [b for f in (doc.get("features") or []) for b in f["properties"].get("data", [])]
                percentile_days = sum(1 for b in blocks for v in b.get("values", []) if v.get("computation") == "percentile")
                report["statistics_v0"][site] = {
                    "http_status": r4.status_code,
                    "features": len(doc.get("features") or []),
                    "percentile_days": percentile_days,
                }
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
