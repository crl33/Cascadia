"""Contract invariants that encode the data doctrine (docs/DATA_DOCTRINE.md §14)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cascade_contracts import (
    BasinVisualizationState,
    ContractEnvelope,
    Freshness,
    FreshnessState,
    ProvenanceRef,
    SourceKind,
    Thresholds,
    TimeContext,
    TruthClass,
)
from cascade_contracts.visualization import (
    AgreementLevel,
    AgreementState,
    BasinSurfaces,
    FloodCategory,
    GeometryRef,
    HazardState,
    SurfaceLevel,
    SurfaceState,
)

NOW = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)


def prov(kind: SourceKind = SourceKind.OBSERVED) -> ProvenanceRef:
    return ProvenanceRef(
        source_id="src:test",
        source_kind=kind,
        freshness=Freshness(state=FreshnessState.CURRENT, age_seconds=60),
        label="test",
    )


def basin(prov_key: str = "p1") -> BasinVisualizationState:
    s = SurfaceState(state=SurfaceLevel.UNKNOWN, prov=prov_key, truth=TruthClass.CASCADE_DERIVED, experimental=True)
    return BasinVisualizationState(
        id="basin:skagit",
        name="Skagit",
        regulation_class="regulated_upper",
        surfaces=BasinSurfaces(
            susceptibility=s,
            forcing=s,
            hazard=HazardState(horizon_h=72, official_category=FloodCategory.NONE, prov=prov_key, truth=TruthClass.AUTHORITATIVE_MODEL),
            agreement=AgreementState(state=AgreementLevel.UNKNOWN),
        ),
        geometry_ref=GeometryRef(lod="basin", feature_id="basin:skagit"),
    )


def test_envelope_rejects_unresolved_provenance() -> None:
    with pytest.raises(ValidationError, match="unresolved provenance refs"):
        ContractEnvelope(
            contract="BasinVisualizationState",
            generated_at=NOW,
            as_of=NOW,
            time=TimeContext(valid=NOW, mode="now"),
            items=(basin("missing"),),
            provenance_refs={"p1": prov()},
        )


def test_envelope_accepts_resolved_provenance() -> None:
    env = ContractEnvelope(
        contract="BasinVisualizationState",
        generated_at=NOW,
        as_of=NOW,
        time=TimeContext(valid=NOW, mode="now"),
        items=(basin("p1"),),
        provenance_refs={"p1": prov()},
    )
    assert env.items[0].id == "basin:skagit"


def test_stage_thresholds_require_datum() -> None:
    with pytest.raises(ValidationError, match="vertical datum"):
        Thresholds(basis="stage", unit="ft", action=23.5, prov="p1")
    ok = Thresholds(basis="stage", unit="ft", datum="NGVD29", action=23.5, prov="p1")
    assert ok.datum == "NGVD29"
    flow = Thresholds(basis="flow", unit="cfs", action=6000, prov="p1")
    assert flow.datum is None


def test_no_renderer_fields_in_contracts() -> None:
    forbidden = {"color", "colour", "material", "opacity", "camera", "shader", "css", "rgb"}
    for model in (BasinVisualizationState, ContractEnvelope):
        schema_text = str(model.model_json_schema()).lower()
        for word in forbidden:
            assert f"'{word}'" not in schema_text, f"renderer concept {word!r} leaked into {model.__name__}"


def test_contracts_are_frozen_and_strict() -> None:
    b = basin("p1")
    with pytest.raises(ValidationError):
        BasinVisualizationState(**{**b.model_dump(), "cesiumColor": "#f00"})  # type: ignore[arg-type]
