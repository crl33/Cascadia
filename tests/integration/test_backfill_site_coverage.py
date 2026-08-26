"""The Event Zero backfill must cover every gauge a susceptibility surface reads.

`scripts/backfill_event_zero_usgs.py` backfilled the six FORECAST-POINT gauges, but the Skagit's
configured SUSCEPTIBILITY gauge is the Sauk (12189500) — chosen because it is unregulated — and it
was not in the list. The basin of the event therefore had a climatology ladder and no December
observations to rank against it, so it was absent from every susceptibility reconstruction. That
was invisible precisely because the surface behaves correctly: it returned UNKNOWN with a reason
rather than a wrong number (docs/research/tier0-measured-basis-2026-08-26.md §4).

This test is the guard: the backfill list must remain a superset of the seeded susceptibility
gauges, so the two cannot drift apart again.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _default_sites() -> set[str]:
    """The site list the backfill script ships with, read from source, not imported.

    Importing the script would pull the whole provider stack into this test for one constant;
    reading the literal keeps the guard cheap and makes an accidental reformat visible.
    """
    src = (ROOT / "scripts" / "backfill_event_zero_usgs.py").read_text(encoding="utf-8")
    m = re.search(r"^DEFAULT_SITES\s*=\s*\[(.*?)\]", src, re.M | re.S)
    assert m, "DEFAULT_SITES literal not found in scripts/backfill_event_zero_usgs.py"
    return set(re.findall(r'"(\d+)"', m.group(1)))


def _seeded_susceptibility_gauges() -> set[str]:
    """Every basin's susceptibility gauge from the seed, as bare USGS site numbers.

    The seed spells this `basin_susceptibility_gauges: {basin_id: {gauge_station_id: ...}}`; the
    column it lands in is `basin.susceptibility_gauge_id`. Read the seed rather than the database
    so the guard runs offline in the default suite.
    """
    seed_dir = ROOT / "packages" / "core" / "src" / "cascade_core" / "seed"
    sites: set[str] = set()
    for path in seed_dir.glob("*.json"):
        blob = json.loads(path.read_text(encoding="utf-8"))
        for entry in (blob.get("basin_susceptibility_gauges") or {}).values():
            station = (entry or {}).get("gauge_station_id", "")
            m = re.fullmatch(r"station:usgs:(\d+)", station)
            if m:
                sites.add(m.group(1))
    return sites


def test_backfill_covers_every_seeded_susceptibility_gauge() -> None:
    seeded = _seeded_susceptibility_gauges()
    assert seeded, "no susceptibility gauges found in the seed — this guard would be vacuous"
    missing = seeded - _default_sites()
    assert not missing, (
        f"Event Zero backfill omits susceptibility gauge(s) {sorted(missing)}. A basin whose "
        f"susceptibility gauge is never backfilled reads UNKNOWN through the entire event and "
        f"drops out of the hindcast silently — add the site to DEFAULT_SITES."
    )


def test_the_sauk_is_covered_specifically() -> None:
    """The regression that motivated the guard: 12189500 is the Skagit's susceptibility gauge."""
    assert "12189500" in _default_sites()
