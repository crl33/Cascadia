"""Cascade Oracle — typed data contract (Phase 1.5 + Phase 2A).

FROZEN normalized contract.
FastAPI endpoints, Mongo cache, and React frontend all share this schema.
"""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


RiskState = Literal["calm", "watch", "elevated", "flood", "unknown"]

ThresholdSource = Literal[
    "official_nwps",
    "configured_validated",
    "configured_pending",
    "thresholds_unavailable",
]


class TimePoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    t: str
    v: float


class ParameterSeries(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    label: str
    unit: str
    latest: Optional[float] = None
    latest_at: Optional[str] = None
    series: List[TimePoint] = Field(default_factory=list)
    available: bool = False
    note: Optional[str] = None


class FloodThresholds(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action: Optional[float] = None
    minor: Optional[float] = None
    moderate: Optional[float] = None
    major: Optional[float] = None
    unit: str = "ft"
    source: ThresholdSource = "thresholds_unavailable"
    source_label: str = "Thresholds unavailable"
    validated: bool = False
    notes: Optional[str] = None


class StationConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    river: str
    basin: str
    basin_group: str
    usgs_site: str
    nwps_lid: Optional[str] = None
    lat: float
    lon: float
    active: bool = True
    notes: Optional[str] = None
    fallback_thresholds_ft: Optional[dict] = None
    fallback_validated: bool = False
    fallback_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 2 precursor models.
# Phase 2A: PrecursorSignal + BasinPrecursors are LIVE for SNOTEL/SWE only.
# Phase 2B will populate precipitation_24h; Phase 2C will populate soil_moisture
# and basin_tension_score. Schema is frozen.
# ---------------------------------------------------------------------------
PrecursorKind = Literal[
    "snow_water_equivalent",
    "precipitation_24h",
    "precipitation_72h",
    "soil_moisture",
    "basin_tension_score",
]


class PrecursorSignal(BaseModel):
    """A single precursor measurement contributing to basin tension."""
    model_config = ConfigDict(extra="ignore")
    kind: PrecursorKind
    source: str  # short key: 'nrcs_snotel', 'nws_qpe', etc.
    source_label: str  # human label
    value: Optional[float] = None
    unit: str = ""
    timestamp: Optional[str] = None
    confidence: Optional[float] = None  # 0..1 numeric
    validated: bool = False
    notes: Optional[str] = None
    # Phase 2A SNOTEL extras (also useful generically).
    station_name: Optional[str] = None
    station_id: Optional[str] = None
    station_elevation_ft: Optional[float] = None
    mapping_confidence: Optional[str] = None  # 'high'|'medium'|'low'
    mapping_note: Optional[str] = None
    is_stale: Optional[bool] = None


class BasinPrecursors(BaseModel):
    """Aggregated precursor context for a basin.

    Phase 2A: snow_water_equivalent populated; others remain None.
    """
    model_config = ConfigDict(extra="ignore")
    basin_group: str
    snow_water_equivalent: Optional[PrecursorSignal] = None
    precipitation_24h: Optional[PrecursorSignal] = None
    soil_moisture: Optional[PrecursorSignal] = None
    basin_tension_score: Optional[PrecursorSignal] = None
    computed_at: Optional[str] = None
    available: bool = False
    note: Optional[str] = None


class StationSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    river: str
    basin: str
    basin_group: str = ""
    usgs_site: str
    nwps_lid: Optional[str] = None
    lat: float
    lon: float
    active: bool = True
    notes: Optional[str] = None
    gage_height: ParameterSeries
    discharge: ParameterSeries
    thresholds: FloodThresholds
    risk_state: RiskState
    risk_reason: str
    is_stale: bool
    fetched_at: str
    errors: List[str] = Field(default_factory=list)
    # Phase 2 attachment point.
    precursors: Optional[BasinPrecursors] = None


class RefreshAttempt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    attempted_at: Optional[str] = None
    succeeded_at: Optional[str] = None
    ok: bool = False
    errors: List[str] = Field(default_factory=list)
    stations_attempted: int = 0
    stations_succeeded: int = 0


class PrecursorLayerStatus(BaseModel):
    """Phase 2 precursor layer status, surfaced on the dashboard."""
    model_config = ConfigDict(extra="ignore")
    snowpack_active: bool = False
    snowpack_basins_with_data: int = 0
    snowpack_basins_total: int = 0
    snowpack_last_attempt_at: Optional[str] = None
    snowpack_last_attempt_ok: bool = False
    snowpack_errors: List[str] = Field(default_factory=list)
    precipitation_active: bool = False  # Phase 2B placeholder
    soil_moisture_active: bool = False  # Phase 2C placeholder
    basin_tension_active: bool = False  # Phase 2D placeholder
    note: Optional[str] = None


class SystemStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ok: bool
    stations_total: int
    stations_active: int = 0
    stations_with_data: int
    last_global_refresh_at: Optional[str] = None
    cache_seconds_remaining: int = 0
    last_attempt: RefreshAttempt = Field(default_factory=RefreshAttempt)
    notes: List[str] = Field(default_factory=list)
    phase: int = 1
    phase_label: str = "Phase 1 • Real-Data MVP (1.5 hardening)"
    precursors: PrecursorLayerStatus = Field(default_factory=PrecursorLayerStatus)


class StationsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    fetched_at: str
    stations: List[StationSnapshot]
    system: SystemStatus
