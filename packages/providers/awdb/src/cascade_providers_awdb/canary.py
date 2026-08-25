"""Live canary (network; never in CI): AWDB reachable? schema parses? and does SMS still fail?

The third check is the unusual one and it is deliberate. `soil_saturation_percentile` ships as
UNKNOWN because SNOTEL soil moisture has no median, uneven depths and `no profile` flags
(p3-surfaces-design §2.1). That is a claim about live data, so the canary re-tests it: if AWDB
ever starts serving soil medians, `soil_median_present` flips to true and the UNKNOWN can be
revisited on evidence rather than on memory.
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta

import httpx

from cascade_providers_awdb.client import (
    CONTEXT_ELEMENTS,
    DATA_URL,
    SOIL_ELEMENT,
    STATIONS_URL,
    WA_SNOTEL_WILDCARD,
)
from cascade_providers_awdb.parser import parse_data, parse_stations

PUGET_HUC8 = {"17110004", "17110005", "17110006", "17110007", "17110009", "17110010", "17110011", "17110012", "17110013", "17110014"}


async def check(contact: str = "cascadia-papsukkal@example.invalid") -> dict:
    report: dict = {"provider": "nrcs-awdb", "reachable": False, "schema_ok": False}
    try:
        headers = {"User-Agent": f"CascadiaPapsukkal-canary (+contact: {contact})"}
        async with httpx.AsyncClient(timeout=60, follow_redirects=True, headers=headers) as c:
            r = await c.get(STATIONS_URL, params={"stationTriplets": WA_SNOTEL_WILDCARD, "activeOnly": "true"})
            report["reachable"] = r.status_code == 200
            report["http_status"] = r.status_code
            stations = parse_stations(r.content)
            puget = [s for s in stations if (s.huc8 or "") in PUGET_HUC8]
            report["wa_sntl_stations"] = len(stations)
            report["puget_basin_stations"] = len(puget)
            triplets = ",".join(sorted(s.triplet for s in puget))
            end = datetime.now(UTC).date()
            await asyncio.sleep(1.5)  # be polite: one host, no published rate limit
            r2 = await c.get(DATA_URL, params={
                "stationTriplets": triplets, "elements": ",".join(CONTEXT_ELEMENTS), "duration": "DAILY",
                "beginDate": (end - timedelta(days=21)).isoformat(), "endDate": end.isoformat(),
                "periodRef": "END", "centralTendencyType": "MEDIAN", "returnFlags": "true"})
            series = parse_data(r2.content)
            report["series"] = {code: sum(1 for s in series if s.element_code == code) for code in CONTEXT_ELEMENTS}
            report["values_with_median"] = sum(1 for s in series for v in s.values if v.median is not None)
            await asyncio.sleep(1.5)
            r3 = await c.get(DATA_URL, params={
                "stationTriplets": triplets, "elements": SOIL_ELEMENT, "duration": "DAILY",
                "beginDate": (end - timedelta(days=6)).isoformat(), "endDate": end.isoformat(),
                "periodRef": "END", "centralTendencyType": "MEDIAN", "returnFlags": "true"})
            soil = parse_data(r3.content)
            report["soil_series"] = len(soil)
            report["soil_median_present"] = any(v.median is not None for s in soil for v in s.values)
            report["soil_no_profile_flags"] = sum(1 for s in soil for v in s.values if v.qc_flag == "N")
            depths_by_site = {s.triplet: tuple(sorted(x.height_depth for x in soil if x.triplet == s.triplet and x.height_depth is not None)) for s in soil}
            report["soil_distinct_depth_sets"] = len(set(depths_by_site.values()))
            report["schema_ok"] = True
    except Exception as e:  # canaries report, never raise
        report["error"] = repr(e)
    return report


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1))
    sys.exit(0)
