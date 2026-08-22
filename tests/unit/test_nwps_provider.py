"""NWPS fixture tests: flow-basis (AUBW1/WRAW1) vs stage-basis categories, datums, sentinels, missing forecast, malformed."""

from datetime import UTC, datetime

import pytest

from cascade_providers_nwps.normalize import forecast_from_stageflow, thresholds_from_gauge
from cascade_providers_nwps.parser import ParseError, parse_gauge, parse_stageflow

NOW = datetime(2026, 8, 22, 13, 30, tzinfo=UTC)
EXPECTED = {
    "RNTW1": ("stage", "NGVD29", {"action": 10.4, "minor": 13.0, "moderate": 14.5, "major": 16.0}),
    "CRNW1": ("stage", "NAVD88", {"action": 50.7, "minor": 54.0, "moderate": 56.0, "major": 58.0}),
    "MVEW1": ("stage", "NGVD29", {"action": 23.5, "minor": 28.0, "moderate": 30.0, "major": 32.0}),
    "NKSW1": ("stage", "NAVD88", {"action": 15.0, "minor": 18.0, "moderate": 20.5, "major": 23.0}),
    "AUBW1": ("flow", None, {"action": 6000.0, "minor": 9000.0, "moderate": 12000.0, "major": 14000.0}),
    "WRAW1": ("flow", None, {"action": 5500.0, "minor": 7500.0, "moderate": 10000.0, "major": 12000.0}),
}


@pytest.mark.parametrize("lid", sorted(EXPECTED))
def test_gauge_thresholds_basis_and_datum(fixtures, lid) -> None:
    g = parse_gauge((fixtures / f"nwps/gauge_{lid}.json").read_bytes())
    basis, datum, values = EXPECTED[lid]
    th = thresholds_from_gauge(g)
    assert {t.category: t.value for t in th} == values
    assert {t.basis for t in th} == {basis} and {t.datum for t in th} == {datum}
    assert {t.unit for t in th} == ({"ft"} if basis == "stage" else {"cfs"})
    assert g.rfc == "NWRFC" and g.wfo == "SEW" and g.reach_id and g.in_service


def test_gauge_metadata_mvew1(fixtures) -> None:
    g = parse_gauge((fixtures / "nwps/gauge_MVEW1.json").read_bytes())
    assert (g.usgs_id, g.reach_id, g.upstream_lid, g.downstream_lid) == ("12200500", "24270288", "CONW1", None)
    assert g.categories["major"].flow is None  # -9999 sentinel -> None, never a number
    assert g.crests_historic[0]["stage"] == 37.73 and g.crests_historic[0]["occurredTime"] == "2025-12-12T08:15:00Z"


def test_gauge_negative_fixtures(fixtures) -> None:
    with pytest.raises(ParseError, match="minor"):
        parse_gauge((fixtures / "nwps/gauge_missing_category.json").read_bytes())
    with pytest.raises(ParseError, match="expected number"):
        parse_gauge((fixtures / "nwps/gauge_string_number.json").read_bytes())
    with pytest.raises(ParseError, match="not JSON"):
        parse_gauge((fixtures / "nwps/malformed.json").read_bytes())
    assert thresholds_from_gauge(parse_gauge((fixtures / "nwps/gauge_all_sentinel.json").read_bytes())) == []


def test_stageflow_stage_primary_converts_kcfs(fixtures) -> None:
    sf = parse_stageflow((fixtures / "nwps/stageflow_MVEW1.json").read_bytes())
    assert sf.observed is not None and sf.observed.primary_units == "ft" and sf.observed.secondary_units == "kcfs"
    rec = forecast_from_stageflow(sf.forecast, retrieved_at=NOW, issuer="NWRFC", datum="NGVD29")
    assert rec is not None and rec.issued_at == datetime(2026, 8, 21, 15, 5, tzinfo=UTC)
    assert (rec.primary_variable, rec.unit, rec.stage_unit, rec.flow_unit, rec.datum) == ("stage", "ft", "ft", "cfs", "NGVD29")
    assert rec.values[0].stage == 10.53 and rec.values[0].flow == pytest.approx(6550.0)
    assert rec.available_at == NOW  # retrieved after issuance


def test_stageflow_flow_primary_aubw1(fixtures) -> None:
    sf = parse_stageflow((fixtures / "nwps/stageflow_AUBW1.json").read_bytes())
    assert sf.forecast is not None and sf.forecast.primary_name == "River Discharge" and sf.forecast.primary_units == "kcfs"
    rec = forecast_from_stageflow(sf.forecast, retrieved_at=NOW, issuer="NWRFC", datum="NGVD29")
    assert rec is not None and rec.primary_variable == "flow" and rec.unit == "cfs"
    assert rec.values[0].flow == pytest.approx(301.99) and rec.values[0].stage == 56.9


def test_stageflow_missing_forecast_and_sentinels(fixtures) -> None:
    sf = parse_stageflow((fixtures / "nwps/stageflow_no_forecast.json").read_bytes())
    assert sf.forecast is None and sf.observed is not None and len(sf.observed.points) == 4
    assert forecast_from_stageflow(sf.forecast, retrieved_at=NOW, issuer="NWRFC", datum="NGVD29") is None
    sf = parse_stageflow((fixtures / "nwps/stageflow_sentinel.json").read_bytes())
    pts = sf.forecast.points
    assert pts[2].primary is None and pts[3].secondary is None and pts[1].primary is not None
    with pytest.raises(ParseError):
        parse_stageflow(b"{not json")
