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
from datetime import UTC, datetime
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
