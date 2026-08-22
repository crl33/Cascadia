"""Visualization contracts (docs/VISUALIZATION_CONTRACTS.md §2–§3, §7–§8).

Rules enforced here by type:
- every scientific value carries `prov` (a key into the envelope's provenance_refs) and a
  `truth` class;
- no field names a renderer concept (no colour, material, opacity, camera);
- thresholds carry `basis` (stage|flow), unit and datum so the client can never compare the
  wrong things.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from cascade_contracts.common import (
    CONTRACT_VERSION,
    ConfidenceLabel,
    ProvenanceRef,
    Quantity,
    StrictModel,
    TruthClass,
)


class FloodCategory(StrEnum):
    NONE = "none"
    ACTION = "action"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    UNKNOWN = "unknown"


class SurfaceLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class AgreementLevel(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class TimeContext(StrictModel):
    valid: datetime
    mode: str = Field(pattern="^(now|past|forecast)$")


class Provenanced(StrictModel):
    prov: str = Field(description="key into ContractEnvelope.provenance_refs")
    truth: TruthClass


class SurfaceState(Provenanced):
    """One of the risk surfaces (docs/HYDROLOGY.md §3–§6)."""

    state: SurfaceLevel
    horizon_h: int | None = Field(default=None, ge=0)
    score: float | None = Field(default=None, ge=0, le=1, description="experimental index, never a probability")
    confidence: ConfidenceLabel = ConfidenceLabel.UNKNOWN
    experimental: bool = False
    reason: str | None = Field(default=None, description="why UNKNOWN, when it is")


class HazardState(Provenanced):
    horizon_h: int = Field(ge=0)
    official_category: FloodCategory
    official_prov: str | None = None
    model_probability: dict[str, str | float] | None = Field(
        default=None, description='e.g. {"model": "nwm-mr-ens", "exceeds": "minor", "fraction": 0.43}'
    )
    cascade_index: float | None = Field(default=None, description="only after hindcast evaluation (ADR-0008)")
    reason: str | None = None


class AgreementState(StrictModel):
    state: AgreementLevel
    reason: str | None = Field(default=None, description="why UNKNOWN/LOW, when it is")
    explanation_ref: str | None = None
    prov: tuple[str, ...] = ()


class Driver(StrictModel):
    feature: str
    value: float | None = None
    unit: str | None = None
    direction: str
    rank: int = Field(ge=1)
    prov: str


class OfficialAlert(StrictModel):
    id: str
    event: str
    severity: str | None = None
    onset: datetime | None = None
    expires: datetime | None = None
    issuer: str
    prov: str


class GeometryRef(StrictModel):
    lod: str = Field(pattern="^(orbital|state|basin|river|local|ground)$")
    feature_id: str
    url: str | None = Field(default=None, description="GeoJSON or tile URL template; cartographic truth class")


class BasinSurfaces(StrictModel):
    susceptibility: SurfaceState
    forcing: SurfaceState
    hazard: HazardState
    agreement: AgreementState


class BasinVisualizationState(StrictModel):
    id: str = Field(pattern=r"^basin:[a-z0-9-]+$")
    name: str
    regulation_class: str = Field(pattern="^(natural|partially_regulated|regulated|regulated_upper|unknown)$")
    surfaces: BasinSurfaces
    tension: float | None = Field(default=None, ge=0, le=1, description="wake-up intensity hint; documented method; not a probability")
    headline_drivers: tuple[Driver, ...] = ()
    official_alerts: tuple[OfficialAlert, ...] = ()
    outlet_forecast_point_id: str | None = None
    geometry_ref: GeometryRef
    label_priority: int = Field(default=3, ge=1, le=5)


class ObservedRiverState(Provenanced):
    stage: Quantity | None = None
    flow: Quantity | None = None
    valid_time: datetime


class Trend(Provenanced):
    window_h: int = Field(ge=1)
    rate: Quantity | None = None
    direction: str = Field(pattern="^(rising|falling|steady|unknown)$")


class Headroom(StrictModel):
    basis: str = Field(pattern="^(stage|flow)$")
    to_category: FloodCategory
    value: Quantity | None = None
    time_to_threshold_h: float | None = None
    prov: str
    reason: str | None = None


class OfficialForecastSummary(Provenanced):
    issued_at: datetime
    issuer: str
    crest: Quantity | None = None
    crest_valid_time: datetime | None = None
    category: FloodCategory
    points: int = Field(ge=0)


class Thresholds(StrictModel):
    basis: str = Field(pattern="^(stage|flow)$")
    unit: str
    datum: str | None = None
    action: float | None = None
    minor: float | None = None
    moderate: float | None = None
    major: float | None = None
    prov: str

    @model_validator(mode="after")
    def _stage_requires_datum(self) -> Thresholds:
        if self.basis == "stage" and self.datum is None:
            raise ValueError("stage thresholds must carry a vertical datum (ADR-0009)")
        return self


class Topology(StrictModel):
    upstream: tuple[str, ...] = ()
    downstream: tuple[str, ...] = ()


class Regulation(StrictModel):
    class_: str = Field(alias="class", pattern="^(natural|partially_regulated|regulated|regulated_upper|unknown)$")
    regulated_by: tuple[str, ...] = ()

    model_config = {"populate_by_name": True, "extra": "forbid", "frozen": True}


class RiverVisualizationState(StrictModel):
    id: str = Field(pattern=r"^fp:nwps:[A-Z0-9]+$|^station:[a-z]+:[A-Za-z0-9:._-]+$")
    name: str
    station_id: str | None = None
    reach_id: str | None = None
    basin_id: str
    observed: ObservedRiverState | None = None
    observed_category: FloodCategory = FloodCategory.UNKNOWN
    observed_category_reason: str | None = None
    trend: Trend | None = None
    headroom: Headroom | None = None
    official_forecast: OfficialForecastSummary | None = None
    thresholds: Thresholds | None = None
    topology: Topology = Topology()
    regulation: Regulation = Regulation(class_="unknown")
    location: tuple[float, float] | None = Field(default=None, description="[lon, lat] WGS84; cartographic")
    flow_visual_intensity: float | None = Field(default=None, ge=0, le=1, description="display hint from percentile; not depth")


class ContractEnvelope(StrictModel):
    contract: str
    version: str = CONTRACT_VERSION
    generated_at: datetime
    as_of: datetime
    time: TimeContext
    items: tuple[BasinVisualizationState | RiverVisualizationState, ...]
    provenance_refs: dict[str, ProvenanceRef]

    @model_validator(mode="after")
    def _all_prov_keys_resolve(self) -> ContractEnvelope:
        missing: set[str] = set()

        def visit(obj: object) -> None:
            if isinstance(obj, StrictModel):
                for name in type(obj).model_fields:
                    val = getattr(obj, name)
                    if name == "prov" and isinstance(val, str) and val not in self.provenance_refs:
                        missing.add(val)
                    elif name == "prov" and isinstance(val, tuple):
                        missing.update(v for v in val if v not in self.provenance_refs)
                    elif name in ("official_prov",) and isinstance(val, str) and val not in self.provenance_refs:
                        missing.add(val)
                    else:
                        visit(val)
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    visit(v)
            elif isinstance(obj, dict):
                for v in obj.values():
                    visit(v)

        visit(self.items)
        if missing:
            raise ValueError(f"unresolved provenance refs: {sorted(missing)}")
        return self


class SceneSummary(StrictModel):
    """docs/VISUALIZATION_CONTRACTS.md §8 — the band-appropriate subset for a request."""

    band: str = Field(pattern="^(orbital|state|basin|river|local|ground)$", description="ground is served with local content until ground-band products exist")
    as_of: datetime
    basins: ContractEnvelope | None = None
    rivers: ContractEnvelope | None = None
