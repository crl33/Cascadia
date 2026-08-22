"""Live canary (network; never in CI): each seed LID resolves, parses, has categories and a forecast."""

from __future__ import annotations

import asyncio
import json
import sys

import httpx

from cascade_providers_nwps.client import BASE_URL
from cascade_providers_nwps.normalize import thresholds_from_gauge
from cascade_providers_nwps.parser import parse_gauge, parse_stageflow

LIDS = ["RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1"]


async def check(contact: str = "cascade-oracle@example.invalid") -> dict:
    report: dict = {"provider": "nwps-v1", "lids": {}}
    async with httpx.AsyncClient(timeout=60, headers={"User-Agent": f"CascadeOracle-canary (+contact: {contact})"}) as c:
        for lid in LIDS:
            entry: dict = {}
            try:
                g = parse_gauge((await c.get(f"{BASE_URL}gauges/{lid}")).content)
                th = thresholds_from_gauge(g)
                entry["basis"] = th[0].basis if th else None
                entry["datum"] = g.datum
                sf = parse_stageflow((await c.get(f"{BASE_URL}gauges/{lid}/stageflow")).content)
                entry["forecast_issued"] = sf.forecast.issued_time.isoformat() if sf.forecast and sf.forecast.issued_time else None
                entry["forecast_points"] = len(sf.forecast.points) if sf.forecast else 0
            except Exception as e:
                entry["error"] = repr(e)
            report["lids"][lid] = entry
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
