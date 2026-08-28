"""Common contract primitives: source kinds, truth classes, freshness, provenance, quantities."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "1.4.0"  # 1.4.0 (2026-08-28): +BasinVisualizationState.antecedent_precip
# (observed MRMS basin-mean windows; additive, so 1.3.0 readers keep validating).
# 1.3.0 (2026-08-26): +BasinVisualizationState.hydrologic_state and
# .state_change — the Tier 0 high-tail representation and its velocity (ReferenceWindow,
# SeasonalMultiple, RecordRank, BandBoundary, HydrologicState, StateChange). Additive only: both
# new fields default to absent, so 1.2.0 consumers keep validating.
# 1.2.0 (2026-08-24): +SurfaceState.value, +SurfaceState.spread — additive only,
# so 1.1.0 consumers keep validating (docs/VISUALIZATION_CONTRACTS.md §10 rule 4).
# 1.1.0 (2026-08-22): +ground band, +AgreementState.reason, Regulation.class accepts regulated_upper


class SourceKind(StrEnum):
    """docs/DATA_DOCTRINE.md §2 — closed, ordered taxonomy."""

    OBSERVED = "OBSERVED"
    OFFICIAL_FORECAST = "OFFICIAL_FORECAST"
    MODELED = "MODELED"
    DERIVED = "DERIVED"
    EXPERIMENTAL = "EXPERIMENTAL"
    CONFIGURED = "CONFIGURED"
    UNKNOWN = "UNKNOWN"


class TruthClass(StrEnum):
    """docs/VISUAL_TRUTH_DOCTRINE.md — what kind of thing a rendered element is."""

    OBSERVATION = "observation"
    AUTHORITATIVE_MODEL = "authoritative_model"
    CASCADE_DERIVED = "cascade_derived"
    CARTOGRAPHIC = "cartographic"
    CINEMATIC = "cinematic"


class FreshnessState(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    DEGRADED = "degraded"
    MISSING = "missing"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ConfidenceLabel(StrEnum):
    """Categorical by doctrine; numeric confidence is reserved for calibrated quantities."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Freshness(StrictModel):
    state: FreshnessState
    age_seconds: int | None = Field(default=None, ge=0)
    expected_cadence_seconds: int | None = Field(default=None, ge=0)


class ProvenanceRef(StrictModel):
    """docs/VISUALIZATION_CONTRACTS.md §1. Every scientific value points at one of these."""

    source_id: str = Field(description="DataSource id, e.g. src:nwps-v1")
    source_kind: SourceKind
    product_id: str | None = Field(default=None, description="SourceProduct id, e.g. product:nwps-stageflow")
    method_id: str | None = Field(default=None, description="method:<name>@<semver> for DERIVED/EXPERIMENTAL")
    issued_at: datetime | None = None
    valid_time: datetime | None = None
    retrieved_at: datetime | None = None
    freshness: Freshness
    quality: tuple[str, ...] = ()
    label: str = Field(description="Human label supplied by the backend, e.g. 'NWRFC official forecast'")
    raw_artifact_id: str | None = None


class Quantity(StrictModel):
    """A number with its unit; `datum` is required for stage-like quantities."""

    value: float
    unit: str
    datum: str | None = None


class DisplayRange(StrictModel):
    """Optional presentation hint. Never a colour."""

    min: float
    max: float
    scale: str = Field(default="linear", pattern="^(linear|log)$")
    unit: str | None = None
