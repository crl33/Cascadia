"""Capture REAL provider payloads into tests/fixtures/providers/<provider>/ with a manifest.

Runs outside CI (network). Redacts nothing: these are public data. Writes the payload bytes
verbatim plus manifest.yaml entries (url, captured_at, sha256, bytes, notes). Re-run to
refresh. Usage: .venv/bin/python scripts/capture_fixtures.py [usgs|nwps|all]
"""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "providers"
UA = "CascadeOracle/0.1 (fixture capture; contact: cascade-oracle@example.invalid)"
SITES = ["12119000", "12149000", "12200500", "12213100", "12113000", "12100490"]
LIDS = ["RNTW1", "CRNW1", "MVEW1", "NKSW1", "AUBW1", "WRAW1"]
USGS_IV = "https://waterservices.usgs.gov/nwis/iv/"
NWPS = "https://api.water.noaa.gov/nwps/v1/"


def capture(client: httpx.Client, url: str, params: dict[str, str] | None, out: Path, notes: str) -> dict:
    r = client.get(url, params=params)
    r.raise_for_status()
    out.write_bytes(r.content)
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


def main(which: str) -> None:
    with httpx.Client(headers={"User-Agent": UA, "Accept": "application/json"}, timeout=60) as c:
        if which in ("usgs", "all"):
            d = FIX / "usgs"
            d.mkdir(parents=True, exist_ok=True)
            entries = [
                capture(
                    c,
                    USGS_IV,
                    {"format": "json", "sites": ",".join(SITES), "parameterCd": "00065,00060", "period": "PT12H", "siteStatus": "all"},
                    d / "valid.json",
                    "All six seed sites, stage (00065) + discharge (00060), 12 h window. Provisional (P) qualifiers expected.",
                )
            ]
            (d / "manifest.yaml").write_text(yaml.safe_dump({"provider": "usgs-nwis-iv", "captured": entries}, sort_keys=False))
        if which in ("nwps", "all"):
            d = FIX / "nwps"
            d.mkdir(parents=True, exist_ok=True)
            entries = []
            for lid in LIDS:
                entries.append(capture(c, f"{NWPS}gauges/{lid}", None, d / f"gauge_{lid}.json", f"Gauge metadata + flood categories + datums for {lid}."))
                entries.append(capture(c, f"{NWPS}gauges/{lid}/stageflow", None, d / f"stageflow_{lid}.json", f"Observed + official forecast series for {lid}."))
            (d / "manifest.yaml").write_text(yaml.safe_dump({"provider": "nwps-v1", "captured": entries}, sort_keys=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "all")
