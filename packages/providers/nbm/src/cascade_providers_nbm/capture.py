"""Capture REAL NBM WA subsets into tests/fixtures/providers/nbm/ with a manifest.

Network; runs outside CI (docs/TESTING.md §3). Redacts nothing — these are public data.
Polite by construction: sequential requests, a pause between them, the project User-Agent.

    .venv/bin/python -m cascade_providers_nbm.capture [YYYYMMDD] [HH]

Defaults to the newest qmd cycle that should have landed (client.latest_qmd_cycle). NOMADS
keeps 1-2 days, so re-running this next week needs a cycle that still exists; the S3 PDS
archive (client.archive_url) is the only way back to an older one.
"""

from __future__ import annotations

import hashlib
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import yaml

from cascade_providers_nbm.client import (
    BASE_URL,
    WA_BASINS,
    Cycle,
    latest_qmd_cycle,
    subset_url_params,
)

ROOT = Path(__file__).resolve().parents[4].parent
OUT = ROOT / "tests" / "fixtures" / "providers" / "nbm"
UA = "CascadiaPapsukkal/0.1 (+https://cascadia.papsukkal.com; fixture capture)"
PAUSE_S = 1.5


def _entry(response: httpx.Response, out: Path, notes: str) -> dict:
    out.write_bytes(response.content)
    return {
        "file": out.name,
        "url": str(response.request.url),
        "captured_at": datetime.now(UTC).isoformat(),
        "http_status": response.status_code,
        "content_type": response.headers.get("content-type"),
        "bytes": len(response.content),
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "notes": notes,
    }


def capture(cycle: Cycle) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    wanted = [
        ("qmd", "APCP", 72, "qmd_f072_wa.grib2", "APCP, every window and percentile level, WA box. The 0-3 day cumulative window is the 72-h forcing horizon."),
        ("qmd", "APCP", 24, "qmd_f024_wa.grib2", "APCP for the 0-1 day cumulative window (the 24-h horizon), same box."),
        ("core", "SNOWLVL", 24, "core_f024_snowlvl_wa.grib2", "SNOWLVL deterministic + 15 percentiles at f024. core carries no QPF percentiles; qmd carries no SNOWLVL."),
    ]
    with httpx.Client(headers={"User-Agent": UA, "Accept": "application/octet-stream"}, timeout=120) as c:
        for i, (kind, var, fhour, name, notes) in enumerate(wanted):
            if i:
                time.sleep(PAUSE_S)
            params = subset_url_params(kind=kind, cycle=cycle, fhour=fhour, variable=var, region=WA_BASINS)
            r = c.get(BASE_URL, params=params)
            r.raise_for_status()
            if not r.content.startswith(b"GRIB"):
                raise SystemExit(f"{name}: not GRIB2 (first bytes {r.content[:16]!r}) — cycle probably rolled off NOMADS")
            entries.append(_entry(r, OUT / name, notes))

    full = (OUT / "qmd_f072_wa.grib2").read_bytes()
    derived = [
        _derive(OUT / "truncated.grib2", full[:65536], "qmd_f072_wa.grib2", "First 64 KB only: a truncated download must raise a typed parse error, never a short field."),
        _derive(OUT / "html_error.html", b"<html><head><title>404 Not Found</title></head><body>\n<h1>Not Found</h1>\n</body></html>\n", "-", "An HTML error page served with HTTP 200 must be refused before eccodes sees it."),
    ]
    manifest = {
        "provider": "nbm-v5",
        "cycle": str(cycle),
        "subregion": {"toplat": WA_BASINS.toplat, "bottomlat": WA_BASINS.bottomlat, "leftlon": WA_BASINS.leftlon, "rightlon": WA_BASINS.rightlon},
        "captured": entries,
        "derived": derived,
    }
    (OUT / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return manifest


def _derive(path: Path, data: bytes, source: str, notes: str) -> dict:
    path.write_bytes(data)
    return {"file": path.name, "derived_from": source, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "notes": notes}


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        d = sys.argv[1]
        cyc = Cycle(int(d[:4]), int(d[4:6]), int(d[6:8]), int(sys.argv[2]))
    else:
        cyc = latest_qmd_cycle(datetime.now(UTC))
    m = capture(cyc)
    total = sum(e["bytes"] for e in m["captured"])
    print(yaml.safe_dump(m, sort_keys=False))
    print(f"# cycle {m['cycle']}  captured bytes: {total} ({total / 1e6:.3f} MB)")
