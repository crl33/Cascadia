"""Rebuild the DERIVED fixtures in this directory from the captured ones (no network).

Run: `.venv/bin/python tests/fixtures/providers/nwm-via-nwps/derive.py`

Captured fixtures are provider bytes and are never edited. Derived fixtures exercise the paths
the live payloads happen not to contain — in late August every NWM member is identical inside
the first 72 hours, so a real payload cannot test member spread, the median-member rule or the
member fraction. Each derivation is one small, stated change, recorded in manifest.yaml.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
SERIES_TRUNCATION = 80  # points kept per series: past the 72-hour window, so truncation is testable

#: member -> (crest flow cfs, index of the point the crest lands on)
#: Chosen against the AUBW1 official flow thresholds (action 6000, minor 9000, moderate 12000,
#: major 14000 cfs) so every band boundary is crossed by some member: the lower-median member of
#: six is the third smallest (9500, member3) and exactly one member reaches major.
DIVERGED = {
    "member1": (5000.0, 30),
    "member2": (8000.0, 32),
    "member3": (9500.0, 34),
    "member4": (11000.0, 36),
    "member5": (13000.0, 38),
    "member6": (15000.0, 40),
    "mean": (10250.0, 35),  # the provider's own mean; never a member, never the comparison value
}
BASELINE = 300.0


def _truncate(doc: dict, n: int = SERIES_TRUNCATION) -> dict:
    for name, series in doc["mediumRange"].items():
        series["data"] = series["data"][:n]
    return doc


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text())


def _write(name: str, doc: dict) -> None:
    (HERE / name).write_text(json.dumps(doc, indent=1) + "\n")
    print(f"{name}: {(HERE / name).stat().st_size} bytes")


def main() -> None:
    diverged = _truncate(_load("medium_range_AUBW1.json"))
    for name, series in diverged["mediumRange"].items():
        crest, at = DIVERGED[name]
        for i, point in enumerate(series["data"]):
            point["flow"] = crest if i == at else BASELINE
    _write("medium_range_AUBW1_diverged.json", diverged)

    small = _truncate(_load("medium_range_MVEW1.json"))
    _write("medium_range_MVEW1_short.json", json.loads(json.dumps(small)))

    empty = json.loads(json.dumps(small))
    empty["mediumRange"] = {}
    _write("medium_range_MVEW1_no_series.json", empty)

    mixed = json.loads(json.dumps(small))
    mixed["mediumRange"]["member3"]["referenceTime"] = "2026-08-24T18:00:00Z"
    _write("medium_range_MVEW1_mixed_cycle.json", mixed)

    units = json.loads(json.dumps(small))
    units["mediumRange"]["member2"]["units"] = "m³/s"
    _write("medium_range_MVEW1_bad_units.json", units)

    sentinel = json.loads(json.dumps(small))
    for i in (0, 1, 2):
        sentinel["mediumRange"]["mean"]["data"][i]["flow"] = -9999
    sentinel["mediumRange"]["member1"]["data"][5]["flow"] = -9999
    _write("medium_range_MVEW1_sentinel.json", sentinel)

    (HERE / "malformed.json").write_text(json.dumps(small)[:2048])
    print(f"malformed.json: {(HERE / 'malformed.json').stat().st_size} bytes")


if __name__ == "__main__":
    main()
