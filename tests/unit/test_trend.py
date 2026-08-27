"""`method:rate-of-rise@2.0.0` — the estimator swap, and the properties that make it safe.

The selection is evidence, not preference: `docs/research/trend-estimator-selection-2026-08-26.md`
measured four estimators over 14,700 real 6-hour windows and a second, independently-sampled
measurement (`...-2026-08-27.md`) reached the same conclusion. These tests pin the two claims a
future edit could silently undo — that the SHIPPED estimator is the robust one, and that the
tidal guard fails CLOSED — plus the arithmetic that makes the first claim matter, plus the
§22 requirement that `method:rate-of-rise@1.0.0` stays callable so the A/B has something real to
compare against.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from cascade_hydrology.trend import (
    METHOD_ID,
    METHOD_ID_V1,
    REASON_TIDAL_CLASS_UNVERIFIED,
    REASON_TIDAL_CONTAMINATION,
    SHIPPED_ESTIMATOR,
    STAGE_STEADY_EPS_FT_PER_H,
    TidalClass,
    endpoint_slope,
    estimate_trend,
    ols_slope,
    rate_of_rise,
    repeated_median_slope,
    steady_epsilon,
    theil_sen_slope,
    tidal_refusal,
)

T0 = datetime(2025, 12, 10, 6, 0, tzinfo=timezone.utc)


@pytest.fixture
async def sessions(tmp_path):
    """A seeded SQLite database — the same shape `test_p3_foundation.py` uses."""
    from cascade_core.db import create_schema, make_engine, make_session_factory
    from cascade_core.seed import seed_all
    from cascade_core.settings import SEED_FILE
    from tests.conftest import GEO

    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/trend.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


def series(values: list[float], *, minutes: int = 15) -> list[tuple[datetime, float]]:
    return [(T0 + timedelta(minutes=minutes * i), v) for i, v in enumerate(values)]


def test_the_shipped_estimator_is_the_one_the_measurement_chose() -> None:
    """A rename or a 'tidy-up' that reverts this to theil_sen or endpoint is a regression."""
    assert SHIPPED_ESTIMATOR == "repeated_median"
    assert METHOD_ID == "method:rate-of-rise@2.0.0"


def test_the_replaced_method_is_still_callable_under_its_own_id() -> None:
    """§22: the OLD method stays reproducible, and the two ids are never the same object.

    An A/B that could only call the new code would be comparing the new code against a
    reconstruction of the old one. `rate_of_rise` is the deployed v1 verbatim; nothing on the
    live read path calls it, and this test is what keeps it from being tidied away.
    """
    assert METHOD_ID_V1 == "method:rate-of-rise@1.0.0" != METHOD_ID
    clean = series([10.0 + 0.05 * i for i in range(25)])
    v1 = rate_of_rise([(t, v) for t, v in clean], basis="stage", unit="ft", end=T0 + timedelta(hours=6))
    assert v1.rate == pytest.approx(0.20, abs=1e-9)  # (last - first) / span, exactly as deployed
    assert v1.direction == "rising"

    # Both versions decide STEADY against the SAME epsilon: this change replaced an estimator,
    # it did not recalibrate a band, and an A/B fitted to Event Zero would prove nothing.
    v2 = estimate_trend(clean, station_id="s", basis="stage", unit="ft",
                        end=T0 + timedelta(hours=6), tidal_class=TidalClass.FLUVIAL)
    assert v2.steady_eps == steady_epsilon("stage", 10.0 + 0.05 * 24) == STAGE_STEADY_EPS_FT_PER_H


def test_a_corrupted_final_reading_moves_the_endpoint_difference_and_not_the_shipped_one() -> None:
    """The decisive measured case (selection note §3), reproduced as arithmetic.

    A clean 0.20 ft/h rise with one bad FINAL sample. The endpoint difference cannot see past
    the two values it uses; every robust estimator can.
    """
    clean = [10.0 + 0.05 * i for i in range(25)]  # +0.05 ft per 15 min = 0.20 ft/h
    dirty = list(clean)
    dirty[-1] = clean[-1] * 1.5 + 1.0

    xs = [0.25 * i for i in range(25)]
    assert endpoint_slope(xs, clean) == pytest.approx(0.20, abs=1e-9)

    eps = steady_epsilon("stage", clean[-1])
    err = {
        "endpoint": abs(endpoint_slope(xs, dirty) - endpoint_slope(xs, clean)) / eps,
        "ols": abs(ols_slope(xs, dirty) - ols_slope(xs, clean)) / eps,
        "theil_sen": abs(theil_sen_slope(xs, dirty) - theil_sen_slope(xs, clean)) / eps,
        "repeated_median": abs(repeated_median_slope(xs, dirty) - repeated_median_slope(xs, clean)) / eps,
    }
    # the shipped estimator does not move at all; the one it replaces moves by many epsilons
    assert err["repeated_median"] == pytest.approx(0.0, abs=1e-9)
    assert err["endpoint"] > 20.0
    assert err["endpoint"] > err["ols"] > err["repeated_median"]
    assert err["theil_sen"] < 1.0


def test_the_rate_survives_a_bad_final_reading_end_to_end() -> None:
    """Not just the slope function: the whole assembly still reports the true direction."""
    clean = [10.0 + 0.05 * i for i in range(25)]
    dirty = list(clean)
    dirty[-1] = 2.0  # a dropout to a sentinel-ish low value

    got = estimate_trend(series(dirty), station_id="s", basis="stage", unit="ft",
                         end=T0 + timedelta(hours=6), tidal_class=TidalClass.FLUVIAL)
    assert got.refusal is None
    assert got.direction == "rising"
    assert got.slope == pytest.approx(0.20, abs=0.02)


@pytest.mark.parametrize("marker", [None, TidalClass.UNVERIFIED])
def test_the_tidal_guard_fails_closed(marker) -> None:
    """An unmarked station gets no rate. There is no path where 'unknown' means 'fluvial'."""
    refusal = tidal_refusal(marker)
    assert refusal is not None and refusal.reason == REASON_TIDAL_CLASS_UNVERIFIED

    got = estimate_trend(series([10.0 + 0.05 * i for i in range(25)]), station_id="s",
                         basis="stage", unit="ft", end=T0 + timedelta(hours=6), tidal_class=marker)
    assert got.slope is None and got.direction == "unknown"
    assert got.refusal.reason == REASON_TIDAL_CLASS_UNVERIFIED


def test_a_tidal_station_is_refused_even_though_the_data_looks_fine() -> None:
    """The guard runs BEFORE the data, so a clean-looking tide cannot talk its way past it."""
    got = estimate_trend(series([10.0 + 0.05 * i for i in range(25)]), station_id="s",
                         basis="stage", unit="ft", end=T0 + timedelta(hours=6),
                         tidal_class=TidalClass.TIDAL)
    assert got.slope is None
    assert got.refusal.reason == REASON_TIDAL_CONTAMINATION


def test_no_estimator_removes_a_tide_which_is_why_the_guard_exists() -> None:
    """Selection note §5: robustness is the wrong tool for a coherent signal.

    A pure M2 sinusoid with no river motion at all. The window PHASE is swept, because a 6 h
    window is roughly half a tidal cycle: one starting at the crest sees the rise and the fall
    cancel, while one on the rising limb sees the full false rate. It is the worst phase the
    guard exists for, so that is what is asserted -- and at that phase the MOST robust estimator
    is the worst of the four, so a future edit must not delete the guard on the grounds that the
    estimator got better.
    """
    period_h, amp = 12.42, 1.0
    xs = [0.25 * i for i in range(25)]
    fns = {"endpoint": endpoint_slope, "ols": ols_slope,
           "theil_sen": theil_sen_slope, "repeated_median": repeated_median_slope}
    worst = {name: 0.0 for name in fns}
    for step in range(50):  # one full cycle of window start phases
        phase = step * period_h / 50
        ys = [10.0 + amp * math.sin(2 * math.pi * (x + phase) / period_h) for x in xs]
        for name, fn in fns.items():
            worst[name] = max(worst[name], abs(fn(xs, ys)))

    assert all(r > 4 * STAGE_STEADY_EPS_FT_PER_H for r in worst.values()), worst
    assert worst["repeated_median"] > worst["endpoint"]


def test_two_points_are_refused_because_every_estimator_collapses_there() -> None:
    """With n=2 the repeated median IS the endpoint difference. Refuse rather than pretend."""
    got = estimate_trend(series([10.0, 10.5]), station_id="s", basis="stage", unit="ft",
                         end=T0 + timedelta(hours=6), tidal_class=TidalClass.FLUVIAL)
    assert got.slope is None
    assert got.refusal.reason == "INSUFFICIENT_OBSERVATIONS"


# --- the wiring, not just the method ------------------------------------------------------
#
# Mutation-driven: hardcoding `tidal = TidalClass.FLUVIAL` at the call site in `assemble.py`
# passed the entire suite before these two tests existed. A guard nothing reads is not a guard.


async def _assess(sessions, tidal_class: str | None):
    """`assess_point` for one seeded forecast point with the station's marker set as given."""
    from sqlalchemy import select

    from cascade_core.knowledge import as_known_at
    from cascade_core.models import ForecastPoint, Observation, RawArtifact, SourceProduct, Station
    from cascade_core.registry import PRODUCT_USGS_IV
    from cascade_hydrology.assemble import assess_point

    now = datetime(2025, 12, 10, 12, 0, tzinfo=timezone.utc)
    async with sessions() as s:
        fp = (await s.execute(select(ForecastPoint).where(ForecastPoint.lid == "RNTW1"))).scalar_one()
        station = await s.get(Station, fp.station_id)
        station.tidal_class = tidal_class
        # every observation carries provenance; the schema will not let one exist without it
        art = RawArtifact(
            sha256="d" * 64, object_key="test/trend", product_id=PRODUCT_USGS_IV,
            fetched_at=now, request_url="test://trend", bytes=1, http_status=200,
            content_type="application/json", retention_class=None,
        )
        s.add(art)
        await s.flush()
        # a clean, unambiguous 6 h rise so the only thing under test is the guard
        for i in range(25):
            s.add(Observation(
                station_id=fp.station_id, product_id=PRODUCT_USGS_IV, variable="stage",
                value=10.0 + 0.05 * i, unit="ft", datum="NGVD29",
                valid_time=now - timedelta(hours=6) + timedelta(minutes=15 * i),
                retrieved_at=now, available_at=now, revision_seq=0, quality=[],
                raw_artifact_id=art.id,
            ))
        await s.commit()
    async with sessions() as s:
        products = {p.id: p for p in (await s.execute(select(SourceProduct))).scalars()}
        fp = (await s.execute(select(ForecastPoint).where(ForecastPoint.lid == "RNTW1"))).scalar_one()
        return await assess_point(as_known_at(s, now), fp, None, products)


async def test_the_assembler_publishes_a_rate_for_a_measured_fluvial_station(sessions) -> None:
    got = await _assess(sessions, "FLUVIAL")
    assert got.item.trend is not None
    assert got.item.trend.direction == "rising"
    assert got.item.trend.rate.value == pytest.approx(0.20, abs=0.02)


@pytest.mark.parametrize("marker", [None, "TIDAL", "not-a-class"])
async def test_the_assembler_refuses_a_rate_when_the_station_is_not_measured_fluvial(sessions, marker) -> None:
    """NULL, TIDAL and an unrecognised marker all refuse. Only a measured FLUVIAL publishes."""
    got = await _assess(sessions, marker)
    assert got.item.trend is not None, "the refusal must be rendered, not dropped"
    assert got.item.trend.rate is None
    assert got.item.trend.direction == "unknown"


# --- the tide the guard exists for, driven end to end --------------------------------------


def m2_tide(amplitude_ft: float, *, phase_h: float = 0.0, n: int = 25, minutes: int = 15,
            base: float = 10.0) -> list[tuple[datetime, float]]:
    """A pure semidiurnal (M2) stage series with no river motion in it at all."""
    period_h = 12.42
    return [
        (T0 + timedelta(minutes=minutes * i),
         base + amplitude_ft * math.sin(2 * math.pi * ((minutes * i) / 60.0 + phase_h) / period_h))
        for i in range(n)
    ]


@pytest.mark.parametrize("marker", [TidalClass.TIDAL, TidalClass.UNVERIFIED, None])
def test_a_tide_dominated_stage_series_never_becomes_a_flood_trend(marker) -> None:
    """The physical case, through the whole assembly rather than through the bare estimators.

    A 2.0 ft M2 tide and nothing else, swept over a full tidal cycle of window phases, is
    refused at every phase — and the second half of the loop shows what the refusal is standing
    in front of: mark the identical series FLUVIAL and the surface publishes an ordinary rise of
    many STEADY epsilons. That is why this is a refusal keyed on a per-station MEASUREMENT and
    not a quality flag on a number: the number looks exactly like a flood.

    `test_no_estimator_removes_a_tide_which_is_why_the_guard_exists` makes the estimator-level
    case; this one pins that `estimate_trend` actually consults the guard before it computes.
    """
    expected = REASON_TIDAL_CONTAMINATION if marker is TidalClass.TIDAL else REASON_TIDAL_CLASS_UNVERIFIED
    end = T0 + timedelta(hours=6)
    worst_suppressed = 0.0
    for step in range(24):  # one full cycle of window start phases
        points = m2_tide(2.0, phase_h=step * 12.42 / 24)
        got = estimate_trend(points, station_id="station:usgs:12155500", basis="stage", unit="ft",
                             end=end, tidal_class=marker)
        assert got.refusal is not None and got.refusal.reason == expected
        assert got.slope is None and got.direction == "unknown" and got.steady_eps is None
        unguarded = estimate_trend(points, station_id="station:usgs:12155500", basis="stage",
                                   unit="ft", end=end, tidal_class=TidalClass.FLUVIAL)
        assert unguarded.refusal is None and unguarded.slope is not None
        worst_suppressed = max(worst_suppressed, abs(unguarded.slope))
    assert worst_suppressed > 10 * STAGE_STEADY_EPS_FT_PER_H, worst_suppressed


async def test_the_guard_does_not_fire_for_any_station_the_platform_serves(sessions) -> None:
    """The other half of a guard: it must not be an outage for everything the platform serves.

    Every seeded station carries a MEASURED fluvial marker
    (`research/tidal-gauge-verification-2026-08-26.md` §3: M2 <= 0.008 ft against a coastal
    reference with a non-tidal control). Seeding a seventh station without that measurement
    fails here, which is the intended price of seeding one.
    """
    from sqlalchemy import select

    from cascade_core.models import ForecastPoint, Station

    async with sessions() as s:
        stations = list((await s.execute(select(Station))).scalars())
        points = list((await s.execute(select(ForecastPoint))).scalars())

    assert len(points) == 6, "the six seeded forecast points"
    assert len(stations) == 7, "six forecast-point stations plus the Sauk susceptibility proxy"
    assert {st.tidal_class for st in stations} == {"FLUVIAL"}
    for st in stations:
        assert tidal_refusal(TidalClass(st.tidal_class)) is None, st.id
    by_id = {st.id: st for st in stations}
    for fp in points:
        assert tidal_refusal(TidalClass(by_id[fp.station_id].tidal_class)) is None, fp.lid
