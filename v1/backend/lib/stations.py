"""Cascade Oracle — station configuration (Phase 1.5).

Authoritative initial config. Seeded into MongoDB so station IDs, LIDs, basin
groups, thresholds, notes, and active flags can be edited without a code change.

Threshold doctrine:
  - Risk state engine ONLY consumes thresholds when source.validated is True.
  - 'fallback_thresholds_ft' here is for resilience if NWPS is unreachable.
  - 'fallback_validated' is False unless an operator has manually verified the
    values against an authoritative source. Until then they are presented as
    'Pending validation' and risk remains 'unknown' if NWPS is down.
"""
from __future__ import annotations

from typing import List

from .types import StationConfig


# Basin group keys used for filtering in the UI.
BASIN_GROUPS: List[dict] = [
    {"key": "cedar-lk-washington", "label": "Cedar / Lake Washington"},
    {"key": "snoqualmie-snohomish", "label": "Snoqualmie / Snohomish"},
    {"key": "skagit", "label": "Skagit"},
    {"key": "nooksack", "label": "Nooksack"},
    {"key": "green-duwamish", "label": "Green-Duwamish"},
    {"key": "puyallup-white", "label": "Puyallup / White"},
]


DEFAULT_STATIONS: List[dict] = [
    {
        "id": "cedar-renton",
        "name": "Cedar River at Renton",
        "river": "Cedar River",
        "basin": "Lake Washington",
        "basin_group": "cedar-lk-washington",
        "usgs_site": "12119000",
        "nwps_lid": "RNTW1",
        "lat": 47.4825,
        "lon": -122.2025,
        "active": True,
        "notes": (
            "NWS forecast point with action/minor/moderate/major thresholds. "
            "Discharge typical baseline ~300-600 cfs."
        ),
        "fallback_thresholds_ft": {"action": 9.0, "minor": 11.0, "moderate": 13.0, "major": 15.0},
        "fallback_validated": False,
        "fallback_notes": "Resilience fallback only. Use NWPS values when reachable.",
    },
    {
        "id": "snoqualmie-carnation",
        "name": "Snoqualmie River near Carnation",
        "river": "Snoqualmie River",
        "basin": "Snohomish",
        "basin_group": "snoqualmie-snohomish",
        "usgs_site": "12149000",
        "nwps_lid": "CRNW1",
        "lat": 47.6656,
        "lon": -121.9242,
        "active": True,
        "notes": (
            "NWS forecast point. Snoqualmie can rise quickly during fall pineapple-express "
            "events; watch upstream rainfall."
        ),
        "fallback_thresholds_ft": {"action": 54.0, "minor": 56.0, "moderate": 58.0, "major": 60.0},
        "fallback_validated": False,
        "fallback_notes": "Resilience fallback only.",
    },
    {
        "id": "skagit-mt-vernon",
        "name": "Skagit River near Mount Vernon",
        "river": "Skagit River",
        "basin": "Skagit",
        "basin_group": "skagit",
        "usgs_site": "12200500",
        "nwps_lid": "MVEW1",
        "lat": 48.4453,
        "lon": -122.3342,
        "active": True,
        "notes": (
            "Major NWS forecast point on the lower Skagit. Snowmelt + fall storms drive "
            "the largest historic events."
        ),
        "fallback_thresholds_ft": {"action": 25.0, "minor": 28.0, "moderate": 32.0, "major": 35.0},
        "fallback_validated": False,
        "fallback_notes": "Resilience fallback only.",
    },
    {
        "id": "nooksack-ferndale",
        "name": "Nooksack River at Ferndale",
        "river": "Nooksack River",
        "basin": "Nooksack",
        "basin_group": "nooksack",
        "usgs_site": "12213100",
        "nwps_lid": "NKSW1",
        "lat": 48.8467,
        "lon": -122.5897,
        "active": True,
        "notes": (
            "Lower Nooksack near tidal influence. Combined freshet and storm surge can "
            "affect stage interpretation near tide."
        ),
        "fallback_thresholds_ft": {"action": 12.0, "minor": 14.0, "moderate": 16.0, "major": 18.0},
        "fallback_validated": False,
        "fallback_notes": "Resilience fallback only.",
    },
    {
        "id": "green-auburn",
        "name": "Green River near Auburn",
        "river": "Green River",
        "basin": "Green-Duwamish",
        "basin_group": "green-duwamish",
        "usgs_site": "12113000",
        "nwps_lid": "AUBW1",
        "lat": 47.3081,
        "lon": -122.2017,
        "active": True,
        "notes": (
            "Gauge datum for this site reads roughly 58 ft at typical flows; standard "
            "NWS flood-stage scales do NOT apply directly. NWPS gauge metadata exists "
            "but flood categories are not currently published. Risk reported as "
            "'unknown' until thresholds are validated for this datum."
        ),
        "fallback_thresholds_ft": None,  # No placeholder — honest unknown.
        "fallback_validated": False,
        "fallback_notes": "Awaiting calibrated thresholds for this gauge datum.",
    },
    {
        "id": "white-auburn",
        "name": "White River near Auburn",
        "river": "White River",
        "basin": "Puyallup",
        "basin_group": "puyallup-white",
        "usgs_site": "12100490",
        "lat": 47.2950,
        "lon": -122.2317,
        "nwps_lid": "WRAW1",
        "active": True,
        "notes": (
            "Gauge datum for this site reads roughly 110 ft at typical flows; "
            "standard NWS flood-stage scales do NOT apply directly. "
            "Risk reported as 'unknown' until thresholds are validated."
        ),
        "fallback_thresholds_ft": None,
        "fallback_validated": False,
        "fallback_notes": "Awaiting calibrated thresholds for this gauge datum.",
    },
]


def get_default_configs() -> List[StationConfig]:
    return [StationConfig(**s) for s in DEFAULT_STATIONS]
