"""Live canary (network; never in CI) for the HEFS ensemble path.

Three questions, in the order they would cost history:

1. Is the retention window still ~10 days, and is it still one cycle per day at 12Z? This is the
   only number that decides how long an outage may last before a cycle is unrecoverable. If it
   ever shrinks, the daily cron is no longer sufficient and the cadence must follow it down.
2. Does a cycle still carry 45 members on a 6 h grid, with weather-year indices? The provider says
   it may change without notice, and a quietly thinner ensemble is worse than a missing one.
3. Are the published exceedance quantiles still served, and still labelled? They are what Phase 5
   may show as OFFICIAL probability; Cascadia must never substitute its own.

Usage: .venv/bin/python -m cascade_providers_nwps.hefs_canary
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime

import httpx

from cascade_providers_nwps.hefs_client import BASE_URL, DISCHARGE_PARAMETER
from cascade_providers_nwps.hefs_parser import (
    parse_ensembles,
    parse_headers,
    parse_quantiles,
)

PROBE_LID = "MVEW1"  # the Skagit outlet: the longest record and the reference site everywhere else
GAUGES = ("RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1")


async def check(contact: str = "cascadia-papsukkal@example.invalid") -> dict:
    report: dict = {"checked_at": datetime.now(UTC).isoformat(), "base_url": BASE_URL}
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": f"CascadiaPapsukkal/0.1 (canary; {contact})"},
            timeout=180.0, follow_redirects=True,
        ) as c:
            coverage: dict = {}
            for lid in GAUGES:
                await asyncio.sleep(1.0)
                r = await c.get(f"{BASE_URL}headers/", params={"location_id": lid, "parameter_id": DISCHARGE_PARAMETER})
                heads = parse_headers(r.content) if r.status_code == 200 else ()
                cycles = sorted(h.forecast_datetime for h in heads)
                coverage[lid] = {
                    "http_status": r.status_code,
                    "retained_cycles": len(cycles),
                    "oldest": cycles[0].isoformat() if cycles else None,
                    "newest": cycles[-1].isoformat() if cycles else None,
                    # The number that decides how long an outage may last. If it drops, so must the cadence.
                    "window_days": round((cycles[-1] - cycles[0]).total_seconds() / 86400, 1) if len(cycles) > 1 else None,
                    "cycle_hours": sorted({t.hour for t in cycles}),
                }
            report["coverage"] = coverage
            report["locations_serving_nothing"] = [k for k, v in coverage.items() if not v["retained_cycles"]]

            newest = coverage[PROBE_LID]["newest"]
            if newest:
                await asyncio.sleep(1.0)
                r = await c.get(f"{BASE_URL}ensembles/", params={
                    "location_id": PROBE_LID, "parameter_id": DISCHARGE_PARAMETER,
                    "forecast_datetime": newest.replace("+00:00", "Z")})
                report["ensemble"] = {"http_status": r.status_code, "bytes": len(r.content)}
                if r.status_code == 200:
                    ens = parse_ensembles(r.content)
                    if ens:
                        e = ens[0]
                        steps = {
                            (b[0] - a[0]).total_seconds()
                            for m in e.members for a, b in zip(m.values, m.values[1:], strict=False)
                        }
                        report["ensemble"] |= {
                            "members": len(e.members),
                            "index_range": [min(m.index for m in e.members), max(m.index for m in e.members)],
                            "steps_per_member": sorted({len(m.values) for m in e.members}),
                            "distinct_step_seconds": sorted(steps)[:4],
                            "unit": e.header.units,
                            "publication_lag_h": round(
                                (e.header.creation_datetime - e.header.forecast_datetime).total_seconds() / 3600, 2
                            ),
                        }

            await asyncio.sleep(1.0)
            r = await c.get(f"{BASE_URL}hydrograph-quantiles/",
                            params={"location_id": PROBE_LID, "parameter_id": DISCHARGE_PARAMETER})
            report["quantiles"] = {"http_status": r.status_code, "bytes": len(r.content)}
            if r.status_code == 200:
                q = parse_quantiles(r.content)
                report["quantiles"] |= {"levels": list(q.levels), "rows": len(q.rows), "unit": q.units}
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
