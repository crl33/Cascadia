"""Cascade Oracle — SNOTEL station config (Phase 2A).

Maps each river basin group to a representative upstream SNOTEL station for
snowpack precursor signals. Each mapping is config-driven; a basin can have
multiple alternates if the primary station goes offline.

DOCTRINE:
  - A single SNOTEL station is a *representative upstream signal* for a basin
    — NOT a basinwide snowpack assessment.
  - 'confidence' reflects mapping quality:
      high   : station HUC matches the basin's drainage AND elevation > 3500 ft
      medium : adjacent HUC, or sufficient elevation but partial drainage match
      low    : closest available, mapping is approximate
  - 'mapping_note' is human-readable disclosure of the basin→SNOTEL relationship.

All mappings here verified against NRCS metadata on initial Phase 2A build.
To add or replace a station, update the BASIN_SNOTEL list — no schema change.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SnotelStationConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    triplet: str  # e.g., '911:WA:SNTL'
    name: str
    basin_group: str
    elevation_ft: float
    lat: Optional[float] = None
    lon: Optional[float] = None
    huc: Optional[str] = None
    active: bool = True
    variables: List[str] = Field(default_factory=lambda: ["WTEQ"])
    confidence: str = "medium"  # high|medium|low
    mapping_note: str = ""
    notes: Optional[str] = None


# Primary SNOTEL station per basin (validated mapping).
BASIN_SNOTEL: List[dict] = [
    {
        "triplet": "911:WA:SNTL",
        "name": "Rex River",
        "basin_group": "cedar-lk-washington",
        "elevation_ft": 3810,
        "lat": None,
        "lon": None,
        "huc": "171100120102",
        "active": True,
        "confidence": "high",
        "mapping_note": (
            "Rex River SNOTEL sits in the Cedar River HUC (171100120102) above the "
            "Cedar at Renton gauge. Representative upstream signal only."
        ),
        "notes": "Primary upstream snowpack proxy for Cedar / Lake Washington basin.",
    },
    {
        "triplet": "908:WA:SNTL",
        "name": "Alpine Meadows",
        "basin_group": "snoqualmie-snohomish",
        "elevation_ft": 3500,
        "lat": 47.77957,
        "lon": -121.69847,
        "huc": "171100100501",
        "active": True,
        "confidence": "high",
        "mapping_note": (
            "Alpine Meadows sits in the Snoqualmie HUC (171100100501) upstream of "
            "the Snoqualmie at Carnation gauge. Representative upstream signal only."
        ),
        "notes": "Primary upstream snowpack proxy for Snoqualmie / Snohomish basin.",
    },
    {
        "triplet": "515:WA:SNTL",
        "name": "Harts Pass",
        "basin_group": "skagit",
        "elevation_ft": 6490,
        "lat": None,
        "lon": None,
        "huc": "171100050501",
        "active": True,
        "confidence": "high",
        "mapping_note": (
            "Harts Pass (6490 ft) is in the Upper Skagit HUC (171100050501). "
            "High-elevation site; representative of late-season snow reserves only."
        ),
        "notes": "High-elevation Upper Skagit signal. Persists later in season than basin average.",
    },
    {
        "triplet": "1011:WA:SNTL",
        "name": "MF Nooksack",
        "basin_group": "nooksack",
        "elevation_ft": 4940,
        "lat": None,
        "lon": None,
        "huc": "171100040303",
        "active": True,
        "confidence": "high",
        "mapping_note": (
            "MF Nooksack sits in the Middle Fork Nooksack HUC (171100040303). "
            "Representative upstream signal for the Nooksack at Ferndale gauge."
        ),
        "notes": "Primary upstream snowpack proxy for the Nooksack basin.",
    },
    {
        "triplet": "1068:WA:SNTL",
        "name": "Sawmill Ridge",
        "basin_group": "green-duwamish",
        "elevation_ft": 4640,
        "lat": None,
        "lon": None,
        "huc": "171100130104",
        "active": True,
        "confidence": "high",
        "mapping_note": (
            "Sawmill Ridge sits in the Green-Duwamish HUC (171100130104). "
            "Representative upstream signal for the Green at Auburn gauge."
        ),
        "notes": "Primary upstream snowpack proxy for the Green-Duwamish basin.",
    },
    {
        "triplet": "1085:WA:SNTL",
        "name": "Cayuse Pass",
        "basin_group": "puyallup-white",
        "elevation_ft": 5260,
        "lat": None,
        "lon": None,
        "huc": "171100140301",
        "active": True,
        "confidence": "high",
        "mapping_note": (
            "Cayuse Pass sits in the White River HUC (171100140301). "
            "Representative upstream signal for the White at Auburn gauge."
        ),
        "notes": "Primary upstream snowpack proxy for the Puyallup / White basin.",
    },
]


def get_snotel_configs() -> List[SnotelStationConfig]:
    return [SnotelStationConfig(**s) for s in BASIN_SNOTEL]


def get_snotel_for_basin(basin_group: str) -> Optional[SnotelStationConfig]:
    for s in BASIN_SNOTEL:
        if s["basin_group"] == basin_group and s.get("active", True):
            return SnotelStationConfig(**s)
    return None
