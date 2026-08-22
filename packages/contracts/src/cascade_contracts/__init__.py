"""Cascade Oracle contracts.

Every value that leaves the backend is typed here. There is no constructor for a bare number:
a scientific quantity always travels with its unit and a provenance reference
(docs/DATA_DOCTRINE.md §1, docs/VISUALIZATION_CONTRACTS.md §1).
"""

from cascade_contracts.common import (
    CONTRACT_VERSION,
    ConfidenceLabel,
    DisplayRange,
    Freshness,
    FreshnessState,
    ProvenanceRef,
    Quantity,
    SourceKind,
    TruthClass,
)
from cascade_contracts.visualization import (
    BasinVisualizationState,
    ContractEnvelope,
    FloodCategory,
    Headroom,
    OfficialForecastSummary,
    RiverVisualizationState,
    SceneSummary,
    SurfaceState,
    Thresholds,
    TimeContext,
    Trend,
)

__all__ = [
    "CONTRACT_VERSION",
    "BasinVisualizationState",
    "ConfidenceLabel",
    "ContractEnvelope",
    "DisplayRange",
    "FloodCategory",
    "Freshness",
    "FreshnessState",
    "Headroom",
    "OfficialForecastSummary",
    "ProvenanceRef",
    "Quantity",
    "RiverVisualizationState",
    "SceneSummary",
    "SourceKind",
    "SurfaceState",
    "Thresholds",
    "TimeContext",
    "Trend",
    "TruthClass",
]
