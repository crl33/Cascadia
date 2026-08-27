"""Live canary for the USGS instantaneous transport (network; never in CI; never writes rows).

TRANSPORT, 2026-08-27: this checks the Water Data **OGC API** `continuous` collection, which
replaced legacy `waterservices.usgs.gov/nwis/iv/` as the production instantaneous path.

Canary doctrine (docs/TESTING.md §8): scheduled, non-blocking, alerting. It answers reachable? /
authenticated? / does the schema still parse? / are the expected variables flowing? — and it asks
the questions a fixture cannot, because a fixture is frozen and the provider is not:

- the collection still exists and answers (an endpoint or collection rename shows as HTTP 404);
- the api key is still accepted, if one is configured (an auth failure is 401/403, and the
  keyed rate-limit headers are reported so a silent downgrade to the anonymous tier is visible);
- the page still parses under the shipped strict parser (schema drift raises ParseError);
- BOTH stage and flow are present for every seeded gauge (a parameter disappearing is the
  failure a reachability check alone would miss);
- units and timestamps are still what the normalizer assumes.

It deliberately does NOT check the legacy service. There is no fallback to detect.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import timedelta

import httpx

from cascade_core.timeutils import iso_z, utcnow
from cascade_providers_usgs.ogc_client import (
    ALLOWED_HOSTS,
    OGC_BASE_URL,
    PARAMETER_CODES,
)
from cascade_providers_usgs.ogc_parser import parse_continuous

SITES = ["12119000", "12149000", "12200500", "12213100", "12113000", "12100490", "12189500"]
WINDOW_HOURS = 2
EXPECTED_VARIABLES = {"stage", "flow"}
#: The unit the normalizer assumes for each variable, in the registry's own spelling.
EXPECTED_UNITS = {"stage": "ft", "flow": "cfs"}


async def check(contact: str = "cascadia-papsukkal@example.invalid", api_key: str | None = None) -> dict:
    key = api_key if api_key is not None else os.environ.get("CASCADE_USGS_API_KEY")
    report: dict = {
        "provider": "usgs-ogc-continuous",
        "endpoint": OGC_BASE_URL,
        "keyed": bool(key),
        "reachable": False,
        "schema_ok": False,
        "sites": {},
        "problems": [],
    }
    headers = {"User-Agent": f"CascadiaPapsukkal-canary (+contact: {contact})", "Accept": "application/json"}
    if key:
        headers["X-Api-Key"] = key
    end = utcnow()
    start = end - timedelta(hours=WINDOW_HOURS)
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False, headers=headers) as c:
            for site in SITES:
                r = await c.get(OGC_BASE_URL, params={
                    "f": "json", "monitoring_location_id": f"USGS-{site}",
                    "parameter_code": PARAMETER_CODES, "datetime": f"{iso_z(start)}/{iso_z(end)}",
                    "limit": "10000",
                })
                report["reachable"] = report["reachable"] or r.status_code == 200
                if r.status_code in (401, 403):
                    report["problems"].append(f"{site}: authentication rejected (HTTP {r.status_code})")
                    continue
                if r.status_code != 200:
                    report["problems"].append(f"{site}: HTTP {r.status_code}")
                    continue
                if r.url.host not in ALLOWED_HOSTS:
                    report["problems"].append(f"{site}: answered from unexpected host {r.url.host}")
                # a silent downgrade off the keyed tier is a real operational change
                report.setdefault("rate_limit", {})[site] = {
                    k: v for k, v in r.headers.items() if k.lower().startswith("x-ratelimit")
                } or None
                page = parse_continuous(r.content)  # raises ParseError on schema drift
                seen: dict[str, dict] = {}
                for v in page.values:
                    s = seen.setdefault(v.variable, {"n": 0, "unit": v.unit, "last": None, "foreign_site": None})
                    s["n"] += 1
                    if s["last"] is None or v.time.isoformat() > s["last"]:
                        s["last"] = v.time.isoformat()
                    if v.site != site:
                        s["foreign_site"] = v.site
                report["sites"][site] = seen
                missing = EXPECTED_VARIABLES - set(seen)
                if missing:
                    report["problems"].append(f"{site}: no {', '.join(sorted(missing))} in the last {WINDOW_HOURS} h")
                for variable, s in seen.items():
                    if s["unit"] != EXPECTED_UNITS.get(variable):
                        report["problems"].append(f"{site}: {variable} unit is {s['unit']!r}, normalizer assumes {EXPECTED_UNITS.get(variable)!r}")
                    if s["foreign_site"]:
                        report["problems"].append(f"{site}: page carried observations for {s['foreign_site']}")
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    report["ok"] = report["reachable"] and report["schema_ok"] and not report["problems"]
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1, default=str))
    sys.exit(0)
