"""Capture REAL provider payloads for SUSCEPTIBILITY v0 into tests/fixtures/providers/.

Runs outside CI (network); redacts nothing (public data); writes payload bytes verbatim plus a
manifest.yaml with url, captured_at, sha256, bytes and notes, exactly like
scripts/capture_fixtures.py. Separate file so the P3 surface builders do not collide in the
shared capture script and so each capture carries its own design reference.

Politeness (docs/DATA_SOURCES.md §5.5, vibesec addendum §1): one request at a time, a pause
between requests, one contact-bearing User-Agent.

Two of these captures exist to record a NEGATIVE result and must not be deleted as "empty":
`observation_normals_12200500_00060.json` (the modern USGS statistics API serves no discharge
normals at our sites) and `data_sms_puget.json` (SNOTEL soil moisture has no median, uneven
depths and `no profile` flags — p3-surfaces-design §2.1, which is why soil stays UNKNOWN).

Usage: .venv/bin/python scripts/capture_p3_susceptibility_fixtures.py [usgs-stats|awdb|all]
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "providers"
UA = "CascadiaPapsukkal/0.1 (fixture capture; +https://cascadia.papsukkal.com)"
PAUSE_S = 1.5

OGC = "https://api.waterdata.usgs.gov/ogcapi/v0/collections"
STATS_V0 = "https://api.waterdata.usgs.gov/statistics/v0"
NWIS_STAT = "https://waterservices.usgs.gov/nwis/stat/"
AWDB = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"

# The six basin susceptibility gauges (seed/p3_surfaces.json, design §2.3). The Skagit's is the
# unregulated Sauk (12189500), NOT the Mount Vernon outlet.
GAUGES = ["12213100", "12149000", "12119000", "12189500", "12113000", "12100490"]
# The six seed basins' HUC8s (tests/fixtures/geo/basins_seed_full.geojson.gz properties.huc8).
PUGET_HUC8 = {"17110004", "17110005", "17110006", "17110007", "17110009", "17110010", "17110011", "17110012", "17110013", "17110014"}


def capture(client: httpx.Client, url: str, params: dict[str, str] | None, out: Path, notes: str) -> dict:
    r = client.get(url, params=params)
    r.raise_for_status()
    out.write_bytes(r.content)
    time.sleep(PAUSE_S)
    return {
        "file": out.name,
        "url": str(r.request.url),
        "captured_at": datetime.now(UTC).isoformat(),
        "http_status": r.status_code,
        "content_type": r.headers.get("content-type"),
        "bytes": len(r.content),
        "sha256": hashlib.sha256(r.content).hexdigest(),
        "notes": notes,
    }


def derived(out: Path, content: bytes, source: str, notes: str) -> dict:
    out.write_bytes(content)
    return {"file": out.name, "derived_from": source, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content), "notes": notes}


def capture_usgs_stats(c: httpx.Client) -> None:
    d = FIX / "usgs_stats"
    d.mkdir(parents=True, exist_ok=True)
    entries = [
        capture(
            c,
            f"{OGC}/daily/items",
            {"monitoring_location_id": "USGS-12200500", "parameter_code": "00060", "statistic_id": "00003",
             "f": "csv", "skipGeometry": "true", "limit": "50000", "properties": "time,value,approval_status"},
            d / "daily_12200500.csv",
            "REAL capture: the ENTIRE daily-mean discharge record for the Skagit at Mount Vernon "
            "in one request (design §2.1). Rows are NOT time-ordered — the parser sorts. This is "
            "the golden climatology input: method:streamflow-doy-climatology@1.0.0 is reproduced "
            "from these bytes offline.",
        ),
        capture(
            c,
            f"{OGC}/daily/items",
            {"monitoring_location_id": "USGS-12189500", "parameter_code": "00060", "statistic_id": "00003",
             "f": "csv", "skipGeometry": "true", "limit": "50000", "datetime": "2000-01-01/2026-08-24",
             "properties": "time,value,approval_status"},
            d / "daily_12189500_2000.csv",
            "REAL capture: the Sauk (unregulated Skagit tributary, the Skagit basin's "
            "susceptibility gauge) from 2000-01-01. Deliberately a bounded window, not the full "
            "98-year record: the full record is a second megabyte of fixture for no extra "
            "coverage.",
        ),
    ]
    for site in ("12200500", "12189500"):
        entries.append(
            capture(
                c,
                NWIS_STAT,
                {"format": "rdb", "sites": site, "statReportType": "daily", "statTypeCd": "all", "parameterCd": "00060"},
                d / f"stat_{site}.rdb",
                f"REAL capture: the LEGACY USGS published day-of-year statistics for {site}. This is "
                "the CROSS-CHECK, never a dependency — WaterServices decommissions Q1 2027 (design "
                "§2.1/§2.2 step 2). USGS states these statistics may not match official USGS "
                "publications; that sentence is reproduced in the method row.",
            )
        )
    entries.append(
        capture(
            c,
            f"{OGC}/latest-daily/items",
            {"monitoring_location_id": ",".join(f"USGS-{s}" for s in GAUGES), "parameter_code": "00060",
             "f": "json", "skipGeometry": "true", "limit": "50"},
            d / "latest_daily_gauges.json",
            "REAL capture: the previous complete daily mean at all six basin susceptibility gauges "
            "in one request, each with its approval_status.",
        )
    )
    entries.append(
        capture(
            c,
            f"{STATS_V0}/observationNormals",
            {"monitoring_location_id": "USGS-12200500", "normal_type": "DOY", "parameter_code": "00060"},
            d / "observation_normals_12200500_00060.json",
            "NEGATIVE RESULT, captured on purpose: the modern USGS statistics API (BETA) serves NO "
            "discharge (00060) day-of-year normals at 12200500. This is why the platform builds its "
            "own climatology instead of depending on a published one (design §2.1). Re-probe "
            "quarterly; if this file ever stops being empty, the cross-check gains a second source "
            "— it still never becomes the dependency.",
        )
    )
    head = (d / "daily_12200500.csv").read_bytes().split(b"\n")
    entries.append(derived(d / "daily_malformed.csv", b"\n".join(head[:1] + [b",,2020-13-99,notanumber,Approved"]) + b"\n",
                           "daily_12200500.csv", "Real header, one row with an impossible date and an unparseable value -> ParseError."))
    entries.append(derived(d / "daily_missing_column.csv", b"x,y,time,value\n,,2020-01-01,1000\n",
                           "daily_12200500.csv", "approval_status column absent -> ParseError (the approval filter must not silently pass)."))
    (d / "manifest.yaml").write_text(yaml.safe_dump({"provider": "usgs-statistics-and-daily", "design_ref": "docs/research/p3-surfaces-design-2026-08-24.md §2", "captured": [e for e in entries if "url" in e], "derived": [e for e in entries if "url" not in e]}, sort_keys=False))


def capture_awdb(c: httpx.Client) -> None:
    d = FIX / "awdb"
    d.mkdir(parents=True, exist_ok=True)
    entries = [
        capture(c, f"{AWDB}/stations", {"stationTriplets": "*:WA:SNTL", "activeOnly": "true"}, d / "stations_wa_sntl.json",
                "REAL capture: every active Washington SNOTEL station with its HUC12, elevation and "
                "coordinates. The basin mapping is derived from huc[:8] against the seeded basin "
                "huc8 lists — never a hardcoded site list."),
    ]
    stations = json.loads((d / "stations_wa_sntl.json").read_bytes())
    puget = sorted(s["stationTriplet"] for s in stations if str(s.get("huc", ""))[:8] in PUGET_HUC8)
    end = date(2026, 8, 24)
    begin = end - timedelta(days=20)
    entries.append(
        capture(c, f"{AWDB}/data",
                {"stationTriplets": ",".join(puget), "elements": "WTEQ,PREC", "duration": "DAILY",
                 "beginDate": begin.isoformat(), "endDate": end.isoformat(), "periodRef": "END",
                 "centralTendencyType": "MEDIAN", "returnFlags": "true"},
                d / "data_wteq_prec_puget.json",
                f"REAL capture: WTEQ (snow water equivalent) and PREC (water-year ACCUMULATED "
                f"precipitation) for the {len(puget)} Puget-basin SNOTEL sites, 21 days, periodRef=END "
                "(the DAILY value dated D is the 00:00 PST reading of D+1 — DATA_SOURCES S1), with "
                "per-value median. Captured in late August: SWE and its median are 0.0 at nearly "
                "every site, which is exactly the divide-by-zero case the normalizer must refuse "
                "rather than fabricate a percent-of-median."),
    )
    entries.append(
        capture(c, f"{AWDB}/data",
                {"stationTriplets": ",".join(puget), "elements": "SMS:*", "duration": "DAILY",
                 "beginDate": (end - timedelta(days=6)).isoformat(), "endDate": end.isoformat(),
                 "periodRef": "END", "centralTendencyType": "MEDIAN", "returnFlags": "true"},
                d / "data_sms_puget.json",
                "NEGATIVE RESULT, captured on purpose (design §2.1, §2.6, §7): SNOTEL soil moisture "
                "for the same sites. No `median` key at all even with centralTendencyType=MEDIAN, "
                "inconsistent depth sets per site, qcFlag 'N' (no profile) at most sites, and "
                "physically incoherent profiles. There is no honest way to turn this into a basin "
                "soil-saturation percentile, so soil_saturation_percentile ships with value null and "
                "an unavailability provenance. tests/unit/test_susceptibility.py asserts against "
                "THESE bytes, so a future 'let us just use SMS' change has to argue with the data."),
    )
    raw = json.loads((d / "data_wteq_prec_puget.json").read_bytes())
    broken = json.loads(json.dumps(raw[:1]))
    del broken[0]["data"][0]["stationElement"]["elementCode"]
    entries.append(derived(d / "data_missing_field.json", json.dumps(broken, indent=1).encode(), "data_wteq_prec_puget.json",
                           "elementCode removed from the first stationElement -> ParseError."))
    (d / "manifest.yaml").write_text(yaml.safe_dump({"provider": "nrcs-awdb", "design_ref": "docs/research/p3-surfaces-design-2026-08-24.md §2.1", "captured": [e for e in entries if "url" in e], "derived": [e for e in entries if "url" not in e]}, sort_keys=False))


def main(which: str) -> None:
    with httpx.Client(headers={"User-Agent": UA}, timeout=180, follow_redirects=True) as c:
        if which in ("usgs-stats", "all"):
            capture_usgs_stats(c)
        if which in ("awdb", "all"):
            capture_awdb(c)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
