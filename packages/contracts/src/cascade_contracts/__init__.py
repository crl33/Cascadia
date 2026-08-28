"""Cascadia Papsukkal contracts.

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
    BandBoundary,
    BasinVisualizationState,
    ContractEnvelope,
    FieldGridSpec,
    FieldRasterState,
    FloodCategory,
    Headroom,
    HydrologicState,
    OfficialForecastSummary,
    RecordRank,
    ReferenceWindow,
    RiverVisualizationState,
    SceneSummary,
    SeasonalMultiple,
    StateChange,
    SurfaceState,
    Thresholds,
    TimeContext,
    Trend,
)

__all__ = [
    "CONTRACT_VERSION",
    "BandBoundary",
    "BasinVisualizationState",
    "ConfidenceLabel",
    "ContractEnvelope",
    "FieldGridSpec",
    "FieldRasterState",
    "DisplayRange",
    "FloodCategory",
    "Freshness",
    "FreshnessState",
    "Headroom",
    "HydrologicState",
    "OfficialForecastSummary",
    "ProvenanceRef",
    "Quantity",
    "RecordRank",
    "ReferenceWindow",
    "RiverVisualizationState",
    "SceneSummary",
    "SeasonalMultiple",
    "SourceKind",
    "StateChange",
    "SurfaceState",
    "Thresholds",
    "TimeContext",
    "Trend",
    "TruthClass",
]
