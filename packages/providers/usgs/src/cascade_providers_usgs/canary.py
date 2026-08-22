"""Live canary (network; never in CI): reachable? schema parses? values flowing for the seed sites?"""

from __future__ import annotations

import asyncio
import json
import sys

import httpx

from cascade_providers_usgs.client import BASE_URL, PARAMETER_CODES
from cascade_providers_usgs.parser import parse_iv

SITES = ["12119000", "12149000", "12200500", "12213100", "12113000", "12100490"]


async def check(contact: str = "cascade-oracle@example.invalid") -> dict:
    report: dict = {"provider": "usgs-nwis-iv", "reachable": False, "schema_ok": False, "series": {}}
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers={"User-Agent": f"CascadeOracle-canary (+contact: {contact})"}) as c:
            r = await c.get(BASE_URL, params={"format": "json", "sites": ",".join(SITES), "parameterCd": PARAMETER_CODES, "period": "PT2H", "siteStatus": "all"})
            report["reachable"] = r.status_code == 200
            report["http_status"] = r.status_code
            for s in parse_iv(r.content):
                report["series"][f"{s.site}:{s.variable}"] = {"n": len(s.values), "last": s.values[-1].time.isoformat() if s.values else None}
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
