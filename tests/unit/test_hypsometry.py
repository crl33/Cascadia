"""Hypsometry: the elevation-area curve, and the rain-exposed fraction it enables.

Two layers under test, deliberately together in one file because their honesty constraints are
one story:

1. `cascade_geo.hypsometry` — the stdlib loader over the checked-in 3DEP-derived curves. Its
   numbers are validated against physical reality (Rainier, Baker, WBD areas), because a curve
   that loads cleanly but describes the wrong mountains would pass any shape test.
2. `cascade_hydrology.forcing` — the fraction driver. Its constraints: context and never scored,
   the spread comes from the snow level's OWN p10-p90 (never invented), the HUC8-union caveat is
   printed, and an absent input produces an absent driver rather than a guess.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from cascade_core.models import DerivedFeature, SourceProduct
from cascade_geo.hypsometry import BasinHypsometry, HypsometryError, load_hypsometry
from cascade_hydrology import forcing
from cascade_hydrology.forcing import (
    METHOD_RAIN_EXPOSED,
    RAIN_EXPOSED_FEATURE,
    assess_from_rows,
    rain_exposed_ref_key,
)

GEO = Path(__file__).resolve().parents[1] / "fixtures" / "geo"
NOW = datetime(2026, 8, 28, 3, 0, tzinfo=UTC)
CYCLE = datetime(2026, 8, 28, 0, 0, tzinfo=UTC)
VALID = datetime(2026, 8, 29, 0, 0, tzinfo=UTC)


# --- the checked-in curves describe the real mountains -----------------------------------


def test_the_checked_in_curves_match_the_physical_basins() -> None:
    hyps = load_hypsometry(GEO / "basin_hypsometry.json")
    assert set(hyps.basins) == {
        "basin:cedar", "basin:green-duwamish", "basin:nooksack",
        "basin:puyallup-white", "basin:skagit", "basin:snohomish-snoqualmie",
    }
    # Rainier (4,392 m) crowns the Puyallup-White; a pixel centre sits just below the summit.
    assert 4350 <= hyps.basins["basin:puyallup-white"].max_m <= 4392
    # Mount Baker (3,286 m) crowns the Nooksack.
    assert 3250 <= hyps.basins["basin:nooksack"].max_m <= 3286
    # The Cedar tops out low — the reason DATA_SOURCES says it cannot stratify SWE by elevation.
    assert hyps.basins["basin:cedar"].max_m < 1700
    # The Skagit pixel sum agrees with the WBD area the masks reproduce (8,275 km2, ±1 %).
    assert abs(hyps.basins["basin:skagit"].total_km2 - 8275) / 8275 < 0.01
    assert "HUC8-union" in hyps.geometry_caveat
    assert hyps.method_id == "method:basin-hypsometry@1.0.0"


def test_fraction_below_is_monotone_and_clamped() -> None:
    hyps = load_hypsometry(GEO / "basin_hypsometry.json")
    skagit = hyps.basins["basin:skagit"]
    values = [skagit.fraction_below(e) for e in range(-100, 4500, 50)]
    assert values == sorted(values), "an elevation-area cumulative curve must be monotone"
    assert skagit.fraction_below(-100) == 0.0
    assert skagit.fraction_below(5000) == 1.0
    # mid-elevation sanity: the Skagit is mountainous — most of its surface is above 300 m
    assert skagit.fraction_below(300) < 0.5
    # and essentially everything is below 3,000 m
    assert skagit.fraction_below(3000) > 0.99


def test_a_curve_that_cannot_account_for_its_own_area_is_refused(tmp_path) -> None:
    doc = json.loads((GEO / "basin_hypsometry.json").read_text())
    doc["basins"]["basin:skagit"]["total_km2"] = 99999.0
    bad = tmp_path / "hyps.json"
    bad.write_text(json.dumps(doc))
    with pytest.raises(HypsometryError, match="does not account"):
        load_hypsometry(bad)


def test_a_missing_file_raises_rather_than_returning_empty(tmp_path) -> None:
    with pytest.raises(HypsometryError, match="no hypsometry file"):
        load_hypsometry(tmp_path / "absent.json")


# --- the fraction driver ------------------------------------------------------------------


def _hyps() -> BasinHypsometry:
    """A synthetic wedge basin: area uniform from 0 to 2,000 m, so fraction_below(x) = x/2000."""
    return BasinHypsometry(
        basin_id="basin:test", origin_m=0.0, bin_m=20.0,
        counts_km2=tuple([1.0] * 100), under_km2=0.0, over_km2=0.0,
        total_km2=100.0, min_m=0.0, max_m=2000.0,
    )


def _row(feature: str, value: float | None, *, valid: datetime = VALID) -> DerivedFeature:
    return DerivedFeature(
        feature=feature, scope_kind="basin", scope_id="basin:test", window="72h",
        valid_time=valid, issued_at=CYCLE, computed_at=NOW, available_at=NOW,
        method_id=forcing.METHOD_BASIN_SNOW_LEVEL if "snow" in feature else forcing.METHOD_BASIN_QPF,
        product_id="product:nbm-v5-core" if "snow" in feature else "product:nbm-v5-qmd",
        value=value, values_json={}, unit="m" if "snow" in feature else "mm",
    )


def _qpf_rows() -> list[DerivedFeature]:
    return [_row(forcing.qpf_feature(forcing.FORCING_HORIZON_H, p), v)
            for p, v in ((50, 12.0), (90, 30.0), (10, 2.0))]


def _products() -> dict[str, SourceProduct]:
    return {}


def _snow(p50: float, p10: float | None = None, p90: float | None = None) -> list[DerivedFeature]:
    rows = [_row(forcing.snow_level_feature(50), p50)]
    if p10 is not None:
        rows.append(_row(forcing.snow_level_feature(10), p10))
    if p90 is not None:
        rows.append(_row(forcing.snow_level_feature(90), p90))
    return rows


def test_the_fraction_is_the_snow_level_through_the_curve_with_the_snow_levels_own_spread() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=_snow(1000.0, p10=800.0, p90=1400.0),
        products=_products(), now=NOW, hypsometry=_hyps(),
    )
    driver = next(d for d in result.drivers if d.feature == RAIN_EXPOSED_FEATURE)
    assert driver.value == 50.0  # 1,000 m through the wedge = half the surface
    assert driver.unit == "pct"
    assert driver.direction == "context_not_scored"
    ref = result.refs[rain_exposed_ref_key("basin:test")]
    assert ref.method_id == METHOD_RAIN_EXPOSED
    # the spread is the snow level's own p10/p90 pushed through the same curve — 40 % and 70 %
    assert "p10 snow level -> 40 %" in ref.label
    assert "p90 -> 70 %" in ref.label
    # and the caveats are printed, not implied
    assert "HUC8-union" in ref.label
    assert "not scored" in ref.label.lower()


def test_no_hypsometry_means_no_driver_not_a_guess() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=_snow(1000.0),
        products=_products(), now=NOW, hypsometry=None,
    )
    assert not [d for d in result.drivers if d.feature == RAIN_EXPOSED_FEATURE]
    assert rain_exposed_ref_key("basin:test") not in result.refs


def test_no_snow_level_means_no_fraction_even_with_a_curve() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=(),
        products=_products(), now=NOW, hypsometry=_hyps(),
    )
    assert not [d for d in result.drivers if d.feature == RAIN_EXPOSED_FEATURE]


def test_missing_spread_rows_drop_the_bracket_never_invent_one() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=_snow(1000.0),  # p50 only
        products=_products(), now=NOW, hypsometry=_hyps(),
    )
    ref = result.refs[rain_exposed_ref_key("basin:test")]
    assert "p10 snow level" not in ref.label, "no p10/p90 rows -> no bracket, not a fabricated one"
    driver = next(d for d in result.drivers if d.feature == RAIN_EXPOSED_FEATURE)
    assert driver.value == 50.0


def test_spread_rows_from_a_different_forecast_are_not_mixed_in() -> None:
    """A p10 from another valid time is a different forecast; mixing would fabricate a spread.

    The poison case pairs a SAME-forecast p90 with an OTHER-forecast p10: dropping the
    forecast-identity filter then has both ends available and prints a bracket built from two
    different forecasts — which is exactly the fabrication this test exists to catch. (A stray
    p10 alone would be masked by the lo-and-hi guard and the mutation would pass unnoticed.)
    """
    other_valid = datetime(2026, 8, 30, 0, 0, tzinfo=UTC)
    rows = _snow(1000.0, p90=1400.0) + [_row(forcing.snow_level_feature(10), 100.0, valid=other_valid)]
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=rows,
        products=_products(), now=NOW, hypsometry=_hyps(),
    )
    ref = result.refs[rain_exposed_ref_key("basin:test")]
    assert "p10 snow level" not in ref.label, "a bracket needs both ends from the SAME forecast"


def test_a_snow_level_above_the_whole_basin_reads_one_hundred_percent() -> None:
    """The normal late-summer state on a low basin: everything is below the snow level."""
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=_snow(3500.0, p10=3200.0, p90=3800.0),
        products=_products(), now=NOW, hypsometry=_hyps(),
    )
    driver = next(d for d in result.drivers if d.feature == RAIN_EXPOSED_FEATURE)
    assert driver.value == 100.0


def test_the_existing_snow_driver_still_uses_only_p50_rows() -> None:
    """Regression guard for the split: p10/p90 rows must not leak into the p50 context driver."""
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), snow_rows=_snow(1000.0, p10=800.0, p90=1400.0),
        products=_products(), now=NOW, hypsometry=None,
    )
    snow_driver = next(d for d in result.drivers if d.feature == forcing.snow_level_feature(50))
    assert snow_driver.value == 1000.0


# --- the official WPC QPF beside the blend ------------------------------------------------


def _wpc_row(day: int, value: float | None, *, cycle: datetime = CYCLE) -> DerivedFeature:
    return DerivedFeature(
        feature=forcing.WPC_QPF_FEATURE, scope_kind="basin", scope_id="basin:test", window="24h",
        valid_time=cycle + timedelta(hours=24 * day), issued_at=cycle, computed_at=NOW,
        available_at=cycle - timedelta(minutes=72),  # WPC publishes ahead; carried verbatim
        method_id=forcing.METHOD_QPF_WPC, product_id="product:wpc-qpf-5km-grib",
        value=value, values_json={}, unit="mm",
    )


def test_the_names_are_pinned_to_what_the_wpc_job_writes() -> None:
    from cascade_providers_wpc import jobs as wpc_jobs

    assert forcing.WPC_QPF_FEATURE == wpc_jobs.FEATURE_QPF
    assert forcing.METHOD_QPF_WPC == wpc_jobs.METHOD_QPF


def test_a_complete_wpc_cycle_becomes_one_official_context_driver() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), products=_products(), now=NOW,
        official_qpf_rows=[_wpc_row(1, 1.2), _wpc_row(2, 4.2), _wpc_row(3, 0.4)],
    )
    driver = next(d for d in result.drivers if d.feature == forcing.WPC_QPF_TOTAL_FEATURE)
    assert driver.value == pytest.approx(5.8) and driver.unit == "mm"
    assert driver.direction == forcing.DIRECTION_CONTEXT, "context, never scored"
    ref = result.refs[driver.prov]
    assert "Never averaged" in ref.label and "Day 1+2+3" in ref.label
    # the NBM banding is untouched by the official number standing beside it
    bare = assess_from_rows("basin:test", qpf_rows=_qpf_rows(), products=_products(), now=NOW)
    assert result.surface.state == bare.surface.state
    assert result.surface.score == bare.surface.score
    assert result.surface.value == bare.surface.value


def test_a_partial_cycle_yields_no_total_and_no_silent_fallback_to_an_older_one() -> None:
    older = CYCLE - timedelta(hours=12)
    rows = [
        # the OLDER cycle is complete...
        _wpc_row(1, 9.0, cycle=older), _wpc_row(2, 9.0, cycle=older), _wpc_row(3, 9.0, cycle=older),
        # ...but the NEWEST is not (a half-published or coverage-refused window)
        _wpc_row(1, 1.2), _wpc_row(2, None),
    ]
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), products=_products(), now=NOW, official_qpf_rows=rows
    )
    assert not any(d.feature == forcing.WPC_QPF_TOTAL_FEATURE for d in result.drivers), (
        "a 72-h total from two windows would read as a small forecast; and quietly showing "
        "yesterday's cycle instead would claim the newest official word is older than it is"
    )


# --- forecaster vs blend (design note 2026-08-28; each rule is a pinned obligation) --------


def _blend_rows_for_agreement() -> list[DerivedFeature]:
    return _qpf_rows() + [
        _row(forcing.qpf_feature(24, 50), 4.0),
        _row(forcing.qpf_feature(24, None), 3.5),
        _row(forcing.qpf_feature(72, None), 11.0),
    ]


def test_matching_cycles_yield_two_deltas_and_the_whole_story_in_one_label() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_blend_rows_for_agreement(), products=_products(), now=NOW,
        official_qpf_rows=[_wpc_row(1, 1.2), _wpc_row(2, 4.2), _wpc_row(3, 0.4)],
    )
    by = {d.feature: d for d in result.drivers}
    d24 = by[forcing.AGREEMENT_24H_FEATURE]
    d72 = by[forcing.AGREEMENT_72H_FEATURE]
    assert d24.value == pytest.approx(-2.8)  # official Day-1 1.2 vs blend 24h p50 4.0
    assert d72.value == pytest.approx(-6.2)  # official total 5.8 vs blend 72h p50 12.0
    assert d24.direction == d72.direction == forcing.DIRECTION_CONTEXT, "context, never scored"
    assert d24.prov == d72.prov
    label = result.refs[d24.prov].label
    assert "Day 1 (0-24 h)" in label and "-2.8 mm" in label and "0.3x the blend median" in label
    assert "-2.3 mm against the deterministic member" in label  # 1.2 - 3.5
    assert "inside the blend's pointwise p10-p90 (2.0-30.0 mm)" in label  # 5.8 in [2, 30]
    assert forcing.POINTWISE_CAVEAT in label, "the caveat travels verbatim (design §obligations)"
    assert "never averaged" in label
    assert result.refs[d24.prov].source_kind.value == "DERIVED"
    assert result.refs[d24.prov].method_id == "method:qpf-agreement@1.0.0"


def test_offset_cycles_refuse_and_name_both_cycles_instead_of_comparing_stale_to_fresh() -> None:
    older = CYCLE - timedelta(hours=12)
    result = assess_from_rows(
        "basin:test", qpf_rows=_blend_rows_for_agreement(), products=_products(), now=NOW,
        official_qpf_rows=[_wpc_row(1, 9.0, cycle=older), _wpc_row(2, 9.0, cycle=older), _wpc_row(3, 9.0, cycle=older)],
    )
    by = {d.feature: d for d in result.drivers}
    assert by[forcing.AGREEMENT_24H_FEATURE].value is None
    assert by[forcing.AGREEMENT_72H_FEATURE].value is None
    label = result.refs[by[forcing.AGREEMENT_24H_FEATURE].prov].label
    assert "No comparison" in label
    assert f"{older:%Y-%m-%d %H}Z" in label and f"{CYCLE:%Y-%m-%d %H}Z" in label


def test_trace_amounts_carry_a_delta_but_never_a_ratio() -> None:
    rows = _qpf_rows() + [_row(forcing.qpf_feature(24, 50), 0.4)]
    result = assess_from_rows(
        "basin:test", qpf_rows=rows, products=_products(), now=NOW,
        official_qpf_rows=[_wpc_row(1, 1.2), _wpc_row(2, 4.2), _wpc_row(3, 0.4)],
    )
    by = {d.feature: d for d in result.drivers}
    label = result.refs[by[forcing.AGREEMENT_24H_FEATURE].prov].label
    day1 = label.split("72-h total")[0]
    assert "+0.8 mm" in day1 and "x the blend median" not in day1, (
        "a 3x about 0.4 mm reads as violent disagreement about nothing (design §2)"
    )


def test_only_the_two_declared_windows_are_ever_compared() -> None:
    """The no-percentile-differencing pin: Day-2/Day-3 windows must not appear as agreement
    features — the blend stores CUMULATIVE percentiles and percentiles do not subtract."""
    result = assess_from_rows(
        "basin:test", qpf_rows=_blend_rows_for_agreement(), products=_products(), now=NOW,
        official_qpf_rows=[_wpc_row(1, 1.2), _wpc_row(2, 4.2), _wpc_row(3, 0.4)],
    )
    agreement_features = {d.feature for d in result.drivers if "vs_blend" in d.feature}
    assert agreement_features == {forcing.AGREEMENT_24H_FEATURE, forcing.AGREEMENT_72H_FEATURE}


def test_a_missing_blend_window_says_so_instead_of_skipping_quietly() -> None:
    result = assess_from_rows(
        "basin:test", qpf_rows=_qpf_rows(), products=_products(), now=NOW,  # no 24h p50 stored
        official_qpf_rows=[_wpc_row(1, 1.2), _wpc_row(2, 4.2), _wpc_row(3, 0.4)],
    )
    by = {d.feature: d for d in result.drivers}
    assert by[forcing.AGREEMENT_24H_FEATURE].value is None
    assert by[forcing.AGREEMENT_72H_FEATURE].value == pytest.approx(-6.2), "the 72-h half still compares"
    label = result.refs[by[forcing.AGREEMENT_24H_FEATURE].prov].label
    assert "not stored for this cycle; no comparison" in label
