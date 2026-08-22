"""Hand-computed hydrology cases: categories, refusals, equality, headroom, trend across gaps, hazard crest."""

from datetime import UTC, datetime, timedelta

import pytest

from cascade_contracts import FloodCategory
from cascade_hydrology.category import Measure, ThresholdSet, categorize
from cascade_hydrology.headroom import headroom
from cascade_hydrology.surfaces import forecast_crest, hazard_category
from cascade_hydrology.trend import FALLING, RISING, STEADY, UNKNOWN, rate_of_rise

MVEW1 = ThresholdSet(basis="stage", unit="ft", datum="NGVD29", action=23.5, minor=28.0, moderate=30.0, major=32.0)
AUBW1 = ThresholdSet(basis="flow", unit="cfs", datum=None, action=6000.0, minor=9000.0, moderate=12000.0, major=14000.0)
T0 = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)


def test_stage_categories_and_equality_at_threshold() -> None:
    assert categorize(Measure("stage", 10.59, "ft", "NGVD29"), MVEW1).category == FloodCategory.NONE
    assert categorize(Measure("stage", 23.5, "ft", "NGVD29"), MVEW1).category == FloodCategory.ACTION  # >= at equality
    assert categorize(Measure("stage", 29.99, "ft", "NGVD29"), MVEW1).category == FloodCategory.MINOR
    assert categorize(Measure("stage", 37.73, "ft", "NGVD29"), MVEW1).category == FloodCategory.MAJOR
    r = categorize(Measure("stage", 10.59, "ft", "NGVD29"), MVEW1, label="Observed stage")
    assert "below action stage 23.5 ft, NGVD29" in r.reason


def test_flow_categories_from_cfs_only() -> None:
    assert categorize(Measure("flow", 297.0, "cfs"), AUBW1).category == FloodCategory.NONE
    assert categorize(Measure("flow", 9000.0, "cfs"), AUBW1).category == FloodCategory.MINOR
    kcfs = categorize(Measure("flow", 9.0, "kcfs"), AUBW1)
    assert kcfs.category == FloodCategory.UNKNOWN and "unit mismatch" in kcfs.reason


def test_refusals_are_unknown_with_reasons() -> None:
    r = categorize(Measure("flow", 6660.0, "cfs"), MVEW1)
    assert r.category == FloodCategory.UNKNOWN and "basis mismatch" in r.reason
    r = categorize(Measure("stage", 44.47, "ft", "NAVD88"), MVEW1)
    assert r.category == FloodCategory.UNKNOWN and "datum mismatch" in r.reason
    r = categorize(Measure("stage", 44.47, "ft", None), MVEW1)
    assert r.category == FloodCategory.UNKNOWN and "datum" in r.reason
    assert categorize(Measure("stage", 1.0, "ft", "NGVD29"), None).category == FloodCategory.UNKNOWN
    assert categorize(None, MVEW1).category == FloodCategory.UNKNOWN
    assert categorize(Measure("stage", 1.0, "ft", "NGVD29"), ThresholdSet("stage", "ft", "NGVD29")).category == FloodCategory.UNKNOWN


def test_headroom_and_time_to_threshold() -> None:
    h = headroom(Measure("stage", 10.59, "ft", "NGVD29"), MVEW1, rate_per_h=0.01, direction=STEADY)
    assert h.to_category == FloodCategory.ACTION and h.value == pytest.approx(12.91) and h.time_to_threshold_h is None and "rising" in h.reason
    h = headroom(Measure("stage", 20.5, "ft", "NGVD29"), MVEW1, rate_per_h=0.5, direction=RISING)
    assert h.value == pytest.approx(3.0) and h.time_to_threshold_h == pytest.approx(6.0)
    h = headroom(Measure("stage", 32.0, "ft", "NGVD29"), MVEW1, rate_per_h=0.5, direction=RISING)
    assert h.value is None and h.to_category == FloodCategory.MAJOR
    h = headroom(Measure("flow", 6660.0, "cfs"), MVEW1, rate_per_h=None, direction=UNKNOWN)
    assert h.to_category == FloodCategory.UNKNOWN and "basis mismatch" in h.reason
    assert headroom(None, MVEW1, rate_per_h=None, direction=UNKNOWN) is None


def test_trend_rates_directions_and_gaps() -> None:
    pts = [(T0 - timedelta(hours=6) + timedelta(minutes=15 * i), 10.0 + 0.05 * i) for i in range(25)]
    t = rate_of_rise(pts, basis="stage", unit="ft", end=T0)
    assert t.direction == RISING and t.rate == pytest.approx(0.2) and t.unit == "ft/h"
    t = rate_of_rise([(p, 12.0 - (v - 10.0)) for p, v in pts], basis="stage", unit="ft", end=T0)
    assert t.direction == FALLING and t.rate == pytest.approx(-0.2)
    t = rate_of_rise([(p, 10.0 + 0.001 * i) for i, (p, _) in enumerate(pts)], basis="stage", unit="ft", end=T0)
    assert t.direction == STEADY
    gappy = [pts[0], pts[-1]]  # one 6 h gap
    t = rate_of_rise(gappy, basis="stage", unit="ft", end=T0)
    assert t.direction == UNKNOWN and "gap" in t.reason
    t = rate_of_rise(pts[-3:], basis="stage", unit="ft", end=T0)  # 30 min span in a 6 h window
    assert t.direction == UNKNOWN and "span" in t.reason
    tolerated = [p for i, p in enumerate(pts) if i % 4 == 0]  # hourly, within the 2 h tolerance
    assert rate_of_rise(tolerated, basis="stage", unit="ft", end=T0).direction == RISING
    assert rate_of_rise([pts[-1]], basis="stage", unit="ft", end=T0).direction == UNKNOWN
    flow = [(p, 6000.0 + 10.0 * i) for i, (p, _) in enumerate(pts)]  # 40 cfs/h on 6240 cfs -> under 1 %/h
    assert rate_of_rise(flow, basis="flow", unit="cfs", end=T0).direction == STEADY


def test_forecast_crest_and_hazard() -> None:
    series = [(T0 + timedelta(hours=6 * i), 10.5 + (i if i < 5 else 9 - i)) for i in range(10)]
    crest = forecast_crest(series, as_of=T0)
    assert crest.value == 14.5 and crest.valid_time == T0 + timedelta(hours=24)
    assert forecast_crest(series, as_of=T0 - timedelta(days=10)) is None
    h = hazard_category(crest, basis="stage", unit="ft", datum="NGVD29", thresholds=MVEW1)
    assert h.category == FloodCategory.NONE and "Official forecast crest 14.5 ft" in h.reason
    big = forecast_crest([(T0 + timedelta(hours=12), 28.0)], as_of=T0)
    assert hazard_category(big, basis="stage", unit="ft", datum="NGVD29", thresholds=MVEW1).category == FloodCategory.MINOR
    assert hazard_category(None, basis="stage", unit="ft", datum="NGVD29", thresholds=MVEW1).category == FloodCategory.UNKNOWN
    assert hazard_category(big, basis="stage", unit="ft", datum="NAVD88", thresholds=MVEW1).category == FloodCategory.UNKNOWN
