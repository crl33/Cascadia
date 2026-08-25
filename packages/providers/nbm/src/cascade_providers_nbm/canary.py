"""Live canary (network; never in CI): is the NOMADS subset path still the shape we build on?

Canaries assert plumbing, never weather (docs/TESTING.md §8). This one asks the questions
that would silently break the forcing surface:

- does ``filter_blend.pl`` still answer, and with GRIB2 rather than an HTML error page?
- is the clip still the same grid — 99 x 142, same Section 3 hash — so stored masks still fit?
- are the ``0-N day`` cumulative APCP windows and the percentile ladder still present?
- is SNOWLVL still selectable by (discipline 0, category 19, number 236)?
- how many bytes does one cycle actually cost, against the 1.82 MB the design budgeted?

The CGI is not versioned in its URL and NBM v5.0 landed 2026-05-05, so a version change would
show up here as a changed message count or grid — which is exactly why those are asserted
rather than just HTTP 200 (design §7 item 2).
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import UTC, datetime

import httpx

from cascade_providers_nbm.client import (
    BASE_URL,
    CORE_HORIZONS_H,
    QMD_HORIZONS_H,
    WA_BASINS,
    Cycle,
    latest_qmd_cycle,
    subset_url_params,
)
from cascade_providers_nbm.parser import (
    APCP,
    SNOWLVL,
    decode,
    percentile_levels,
    windows,
)

#: What the design measured on 2026-08-24 for the WA box, for drift detection only.
EXPECTED = {
    ("qmd", 24): {"bytes": 214_318, "messages": 97},
    ("qmd", 48): {"bytes": 556_896, "messages": 129},
    ("qmd", 72): {"bytes": 1_045_326, "messages": 161},
    ("core", 24): {"bytes": 171_727, "messages": 16},
}
EXPECTED_GRID = (99, 142)
DESIGN_BYTES_PER_CYCLE = 1_816_540  # APCP at three horizons (design §1.7)
PAUSE_S = 1.5


async def check(contact: str = "cascadia-papsukkal@example.invalid", cycle: Cycle | None = None) -> dict:
    cyc = cycle or latest_qmd_cycle(datetime.now(UTC))
    report: dict = {
        "provider": "nbm-v5",
        "cycle": str(cyc),
        "checked_at": datetime.now(UTC).isoformat(),
        "subsets": {},
        "grid": None,
        "bytes_total": 0,
    }
    requests = [("qmd", "APCP", h) for h in QMD_HORIZONS_H] + [("core", "SNOWLVL", h) for h in CORE_HORIZONS_H[:1]]
    headers = {"User-Agent": f"CascadiaPapsukkal-canary/0.1 (+contact: {contact})", "Accept": "application/octet-stream"}
    async with httpx.AsyncClient(timeout=120, headers=headers) as client:
        for index, (kind, variable, fhour) in enumerate(requests):
            name = f"{kind}.f{fhour:03d}.{variable}"
            entry: dict = {}
            try:
                if index:
                    await asyncio.sleep(PAUSE_S)  # polite: sequential, spaced
                started = time.monotonic()
                params = subset_url_params(kind=kind, cycle=cyc, fhour=fhour, variable=variable, region=WA_BASINS)
                response = await client.get(BASE_URL, params=params)
                entry["http_status"] = response.status_code
                entry["seconds"] = round(time.monotonic() - started, 2)
                entry["bytes"] = len(response.content)
                report["bytes_total"] += len(response.content)
                fields = decode(response.content, with_values=False)
                keys = [f.key for f in fields]
                grid = fields[0].grid
                entry["messages"] = len(keys)
                entry["grid"] = {
                    "nx_ny": [grid.nx, grid.ny],
                    "definition_hash": grid.definition_hash,
                    "dx_m": grid.dx_m,
                    "la1_lo1": [grid.la1, grid.lo1],
                }
                parameter = APCP if variable == "APCP" else SNOWLVL
                entry["parameter_present"] = any(k.parameter == parameter for k in keys)
                if variable == "APCP":
                    entry["cumulative_window_present"] = (0, fhour) in windows(keys, parameter=APCP)
                    entry["percentile_levels"] = percentile_levels(keys, parameter=APCP, hours=fhour)
                else:
                    entry["percentile_levels"] = percentile_levels(keys, parameter=SNOWLVL)
                    entry["selected_by"] = "discipline=0, category=19, number=236 (never shortName)"
                expected = EXPECTED.get((kind, fhour))
                if expected:
                    entry["messages_expected"] = expected["messages"]
                    entry["messages_changed"] = len(keys) != expected["messages"]
                    entry["bytes_expected"] = expected["bytes"]
            except Exception as exc:  # canaries report, never raise
                entry["error"] = repr(exc)
            report["subsets"][name] = entry

    grids = {json.dumps(e["grid"], sort_keys=True) for e in report["subsets"].values() if "grid" in e}
    first = next((e["grid"] for e in report["subsets"].values() if "grid" in e), None)
    report["grid"] = first
    # Every subset of one cycle must land on the SAME grid: stored basin masks are keyed by
    # its Section 3 hash, so two different grids in one cycle would invalidate half of them.
    report["grid_consistent"] = len(grids) == 1
    report["bytes_per_cycle_qmd"] = sum(e.get("bytes", 0) for n, e in report["subsets"].items() if n.startswith("qmd"))
    report["bytes_per_cycle_design"] = DESIGN_BYTES_PER_CYCLE
    report["bytes_per_day"] = 4 * (report["bytes_per_cycle_qmd"] + sum(e.get("bytes", 0) for n, e in report["subsets"].items() if n.startswith("core")) * len(CORE_HORIZONS_H))
    report["ok"] = bool(
        first
        and first["nx_ny"] == list(EXPECTED_GRID)
        and report["grid_consistent"]
        and all(e.get("http_status") == 200 for e in report["subsets"].values())
        and all(e.get("parameter_present") for e in report["subsets"].values())
    )
    return report


def main() -> None:  # pragma: no cover - operational entry point
    print(json.dumps(asyncio.run(check()), indent=1, default=str))
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
