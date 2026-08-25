"""Live canary for the NWM-via-NWPS reach path (network; never in CI, never blocking).

Usage: `.venv/bin/python -m cascade_providers_nwps.reaches_canary` -> JSON on stdout, exit 0.

What it is for: NWPS states the API "is not supported 24/7 and may be modified without advance
notice", and the NWM member count is a version-dependent fact (design §7 items 3–4). So the
canary asserts *shape*, not just HTTP 200: the series exists, the member list is read from the
payload, the units are a spelling this codebase accepts, and the reference time parses. A drop
from six members to five is exactly the change that would silently turn a "3 of 6 members"
statement into a wrong one, so it is reported explicitly.

Polite by construction: one request per reach, sequentially, with a pause between them.
"""

from __future__ import annotations

import asyncio
import json
import sys

import httpx

from cascade_core.timeutils import utcnow
from cascade_providers_nwps.client import BASE_URL
from cascade_providers_nwps.reaches_normalize import (
    crest_summary,
    model_run_from_ensemble,
)
from cascade_providers_nwps.reaches_parser import SERIES_NAME, parse_medium_range

#: The seed forecast points and their NWPS-published reach ids (design §3.1). The crosswalk is
#: NWPS's own (`/gauges/{lid}.reachId`); it is never inferred here.
REACHES = {
    "RNTW1": "24537890",
    "CRNW1": "23970199",
    "MVEW1": "24270288",
    "NKSW1": "23955772",
    "AUBW1": "23977634",
    "WRAW1": "23981235",
}
PAUSE_S = 1.5
EXPECTED_MEMBERS = 6  # observed 2026-08-24; a change is reported, never assumed away


async def check(contact: str = "cascadia-papsukkal@example.invalid") -> dict:
    now = utcnow()
    report: dict = {"provider": "nwm-via-nwps", "checked_at": now.isoformat(), "reaches": {}}
    headers = {"User-Agent": f"CascadiaPapsukkal-canary (+contact: {contact})", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=60, headers=headers) as c:
        for i, (lid, reach) in enumerate(REACHES.items()):
            if i:
                await asyncio.sleep(PAUSE_S)
            entry: dict = {"reach_id": reach}
            try:
                response = await c.get(f"{BASE_URL}reaches/{reach}/streamflow", params={"series": SERIES_NAME})
                entry["http_status"] = response.status_code
                entry["bytes"] = len(response.content)
                ensemble = parse_medium_range(response.content)
                entry["reach_name"] = ensemble.reach.name
                entry["members"] = ensemble.member_count
                entry["member_count_changed"] = ensemble.member_count != EXPECTED_MEMBERS
                entry["reference_time"] = None if ensemble.reference_time is None else ensemble.reference_time.isoformat()
                entry["units"] = None if ensemble.mean is None else ensemble.mean.unit
                run = model_run_from_ensemble(ensemble, retrieved_at=now)
                entry["stored_points"] = 0 if run is None else len(run.values)
                summary = crest_summary(ensemble)
                entry["median_member"] = None if summary is None or summary.median_member is None else summary.median_member.member
                entry["crest_cfs"] = None if summary is None or summary.median_member is None else round(summary.median_member.value, 1)
            except Exception as e:  # a canary reports, it never raises
                entry["error"] = repr(e)
            report["reaches"][lid] = entry
    report["ok"] = all("error" not in e and not e.get("member_count_changed") for e in report["reaches"].values())
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
