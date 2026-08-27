"""The high-tail selection, pinned so the research document cannot drift away from the code.

Deliberately offline and tiny: the ladders and window statistics below were computed once from the
USGS OGC `daily` record for the six susceptibility gauges (see
`docs/research/high-tail-selection-2026-08-27.md` §11 for the exact request), and are frozen here
as literals. What is being tested is the REPRESENTATION's properties — monotone, censored honestly,
velocity alive in the tail — not the provider.
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from cascade_hydrology.tail_candidates import (
    EXCEEDS_WINDOW_RECORD,
    FALLING,
    MIN_TAIL_YEARS,
    RISING,
    STEADY,
    UNKNOWN,
    WindowSample,
    candidate_a_ladder_percentile,
    candidate_a_prime_window_rank,
    candidate_b_seasonal_multiple,
    candidate_c_pot_gpd,
    growth_rank,
    state_change,
    supported_breakpoints,
    tail_state,
    water_year,
)

# The Sauk (12189500) 12-11 day-of-year window, approved daily means before WY2026:
# n = 490 over 98 water years, WY1912-WY2025. Ladder p05..p95 and the top of the sample.
SAUK_LADDER = {5: 1030.0, 10: 1240.0, 25: 1930.0, 50: 3170.0, 75: 5715.0, 90: 9282.0, 95: 12550.0}
SAUK_TOP = [
    (date(1946, 12, 11), 17300.0),
    (date(1977, 12, 11), 22300.0),
    (date(2004, 12, 10), 23700.0),
    (date(1956, 12, 10), 24000.0),
    (date(2010, 12, 12), 28700.0),
    (date(2015, 12, 9), 34100.0),
    (date(2004, 12, 11), 37400.0),
]
# Event Zero, as the production surface measured it (tier0-measured-basis-2026-08-26 §3).
SKAGIT_09, SKAGIT_11 = 24976.0, 72440.0


def sauk_sample(extra: list[tuple[date, float]] | None = None) -> WindowSample:
    """A stand-in window sample whose ORDER STATISTICS AT THE TOP are the Sauk's real ones.

    The 483 values below the top seven are filler at a level that cannot disturb any tail
    statement; every assertion in this file is about the top of the sample or about the p95
    reference, both of which are the measured values.
    """
    filler = [(date(1912 + i % 98, 12, 11 - i % 3), 500.0 + i) for i in range(483)]
    return WindowSample.from_pairs(filler + SAUK_TOP + (extra or []), key="12-11", window_days=2)


def test_water_year_boundary() -> None:
    assert water_year(date(2025, 9, 30)) == 2025
    assert water_year(date(2025, 10, 1)) == 2026
    assert water_year(date(2025, 12, 11)) == 2026


def test_the_shipped_ladder_clamps_both_event_zero_values_to_the_same_state() -> None:
    """The defect, restated as a test so a fix cannot be claimed without moving this number."""
    low = candidate_a_ladder_percentile(SKAGIT_09, SAUK_LADDER)
    high = candidate_a_ladder_percentile(SKAGIT_11, SAUK_LADDER)
    assert (low.percentile, high.percentile) == (95.0, 95.0)
    assert low.clamped and high.clamped
    assert high.percentile - low.percentile == 0.0  # the silenced derivative, exactly


def test_extending_the_ladder_moves_the_ceiling_but_not_the_derivative() -> None:
    """Candidate A: p98 discriminates 24,976 from p95 — and still says nothing across the crest."""
    sample = sauk_sample()
    extended = dict(SAUK_LADDER)
    extended[98] = sample.quantile(98)
    low = candidate_a_ladder_percentile(SKAGIT_09, extended)
    high = candidate_a_ladder_percentile(SKAGIT_11, extended)
    assert high.percentile == 98.0 and high.clamped
    assert high.percentile - low.percentile == 0.0
    assert EXCEEDS_WINDOW_RECORD not in low.quality  # the ladder cannot know it ran out


def test_the_support_rule_refuses_a_breakpoint_backed_by_too_few_water_years() -> None:
    sample = sauk_sample()
    published = supported_breakpoints(sample, (95.0, 98.0, 99.0, 99.5))
    assert 95.0 in published and 98.0 in published
    # p99 sits inside the top seven values, which come from fewer than MIN_TAIL_YEARS water years.
    assert sample.exceedance_years(sample.quantile(99)) < MIN_TAIL_YEARS
    assert 99.0 not in published and 99.5 not in published


def test_the_rank_is_exact_censored_at_one_and_names_the_record_it_beat() -> None:
    """Candidate A′: honest where the percentile is not — and just as silent across the crest."""
    sample = sauk_sample()
    low = candidate_a_prime_window_rank(SKAGIT_09, sample)
    high = candidate_a_prime_window_rank(SKAGIT_11, sample)
    assert (low.rank, low.of) == (3, 491) and not low.exceeds_record
    assert (high.rank, high.of) == (1, 491) and high.exceeds_record
    assert high.quality == (EXCEEDS_WINDOW_RECORD,)
    assert high.previous_max == 37400.0 and high.previous_max_day == date(2004, 12, 11)
    assert "previous maximum 37,400 on 2004-12-11" in high.label
    assert "3rd largest of 491" in low.label
    # Censored at 1: twice the flow is the same rank. This is why it cannot carry the velocity.
    assert candidate_a_prime_window_rank(SKAGIT_11 * 2, sample).rank == 1


def test_the_seasonal_multiple_is_unbounded_and_carries_the_crest() -> None:
    """Candidate B: the only representation whose Event Zero endpoints differ."""
    sample = sauk_sample()
    low = candidate_b_seasonal_multiple(SKAGIT_09, sample)
    high = candidate_b_seasonal_multiple(SKAGIT_11, sample)
    assert low.reference_flow == pytest.approx(12550.0, abs=1.0)
    assert low.multiple == pytest.approx(1.99, abs=0.01)
    assert high.multiple == pytest.approx(5.77, abs=0.01)
    assert high.multiple / low.multiple == pytest.approx(SKAGIT_11 / SKAGIT_09, rel=1e-9)
    assert EXCEEDS_WINDOW_RECORD in high.quality
    assert "±2-day window, WY1912–WY2025, n=490 over 98 water years" in high.label


def test_the_multiple_is_one_exactly_where_the_shipped_percentile_starts_clamping() -> None:
    """The two statements must not disagree about where discrimination stops."""
    sample = sauk_sample()
    reference = sample.quantile(95)
    assert candidate_b_seasonal_multiple(reference, sample).multiple == pytest.approx(1.0)
    assert candidate_a_ladder_percentile(reference * 0.999, SAUK_LADDER).clamped is False
    assert candidate_a_ladder_percentile(reference * 1.001, SAUK_LADDER).clamped is True


def test_the_representation_is_monotone_in_flow() -> None:
    sample = sauk_sample()
    ladder = dict(SAUK_LADDER)
    ladder[98] = sample.quantile(98)
    previous = None
    for value in (500.0, 1500.0, 5000.0, 12550.0, 20000.0, SKAGIT_09, 50000.0, SKAGIT_11):
        state = tail_state(value, sample, ladder)
        current = (state.percentile.percentile, -state.rank.rank, state.multiple.multiple)
        if previous is not None:
            assert current[0] >= previous[0]
            assert current[1] >= previous[1]
            assert current[2] > previous[2]  # strictly, always: the multiple never ties
        previous = current


def test_the_level_says_the_record_ran_out_without_claiming_extrapolation() -> None:
    sample = sauk_sample()
    state = tail_state(SKAGIT_11, sample, SAUK_LADDER)
    assert state.in_extrapolated_region is True
    assert EXCEEDS_WINDOW_RECORD in state.quality
    assert tail_state(SKAGIT_09, sample, SAUK_LADDER).in_extrapolated_region is False


def test_adding_one_more_water_year_moves_the_rank_by_one_and_nothing_else_breaks() -> None:
    """Stability under a reasonable record change: the ladder is rebuilt annually."""
    before = candidate_a_prime_window_rank(SKAGIT_09, sauk_sample())
    after = candidate_a_prime_window_rank(SKAGIT_09, sauk_sample(extra=[(date(2027, 12, 11), 60000.0)]))
    assert after.rank == before.rank + 1
    assert after.of == before.of + 1
    assert after.period_end == 2028


# --------------------------------------------------------------------------------------------
# STATE CHANGE
# --------------------------------------------------------------------------------------------

D9 = datetime(2025, 12, 9, 8, 0, tzinfo=UTC)
D10 = D9 + timedelta(hours=24)
D11 = D9 + timedelta(hours=48)


def test_the_velocity_survives_the_crest_where_every_percentile_derivative_dies() -> None:
    """The property the whole selection turns on, at the Sauk's real Event Zero pair."""
    points = [(D9, SKAGIT_09), (D11, SKAGIT_11)]
    change = state_change(points, end=D11, window_h=48)
    assert change.growth == pytest.approx(2.90, abs=0.01)
    assert change.direction == RISING
    assert change.percent_change == pytest.approx(190.0, abs=1.0)
    assert "×2.90 in 48 h" in change.label


def test_the_velocity_does_not_depend_on_the_ladder_at_all() -> None:
    """X8 disputes the ladder's vintage; it cannot move this number. (X8 is NOT resolved by that.)"""
    points = [(D9, SKAGIT_09), (D11, SKAGIT_11)]
    growth = state_change(points, end=D11, window_h=48).growth
    thin = WindowSample.from_pairs([(date(2000 + i, 12, 11), 100.0 * (i + 1)) for i in range(12)], key="12-11", window_days=2)
    fat = sauk_sample()
    assert thin.quantile(95) != fat.quantile(95)  # wildly different references
    for sample in (thin, fat):
        low = candidate_b_seasonal_multiple(SKAGIT_09, sample).multiple
        high = candidate_b_seasonal_multiple(SKAGIT_11, sample).multiple
        assert high / low == pytest.approx(growth, rel=1e-9)


def test_the_velocity_has_a_sign_and_detects_the_recession() -> None:
    falling = state_change([(D9, 62600.0), (D11, 21100.0)], end=D11, window_h=48)
    assert falling.direction == FALLING and falling.growth == pytest.approx(0.337, abs=0.001)
    steady = state_change([(D9, 5000.0), (D11, 5300.0)], end=D11, window_h=48)
    assert steady.direction == STEADY  # inside trend.py's 1 %/h band compounded over 48 h


def test_the_velocity_refuses_rather_than_interpolates() -> None:
    gap = state_change([(D9, 1000.0), (D11, 4000.0)], end=D11, window_h=24)
    assert gap.growth is None and gap.direction == UNKNOWN and "within 6 h" in gap.reason
    empty = state_change([], end=D11, window_h=24)
    assert empty.growth is None and "no observation at or before" in empty.reason
    zero = state_change([(D10, 0.0), (D11, 4000.0)], end=D11, window_h=24)
    assert zero.growth is None and "multiplicative rate" in zero.reason


def test_the_velocity_is_computable_when_the_level_is_not() -> None:
    """No climatology, no reference, no rank — and the state change is still exact."""
    thin = WindowSample.from_pairs([(date(2024, 12, 11), 100.0)], key="12-11", window_days=2)
    assert candidate_b_seasonal_multiple(SKAGIT_09, thin).quality  # thin support is flagged
    assert state_change([(D9, SKAGIT_09), (D11, SKAGIT_11)], end=D11, window_h=48).growth is not None


def test_growth_rank_describes_speed_without_drawing_a_band() -> None:
    history = [1.0 + i / 100 for i in range(100)]
    rank, n = growth_rank(1.90, history)
    assert (rank, n) == (10, 100)
    assert growth_rank(99.0, history) == (1, 100)


# --------------------------------------------------------------------------------------------
# Candidate C
# --------------------------------------------------------------------------------------------


def test_peaks_over_threshold_is_refused_with_its_diagnostics_attached() -> None:
    pairs = [(date(1930 + i // 4, 12, 1 + (i % 4) * 7), 10000.0 + 500.0 * (i % 11)) for i in range(240)]
    diag = candidate_c_pot_gpd(pairs, 11000.0)
    assert diag.refused is True
    assert diag.n_independent <= diag.n_exceedances  # declustering never invents events
    assert diag.reason and "return period" in diag.reason


def test_peaks_over_threshold_refuses_a_short_record_on_count_alone() -> None:
    pairs = [(date(2010 + i, 12, 11), 5000.0 + 100.0 * i) for i in range(12)]
    diag = candidate_c_pot_gpd(pairs, 5300.0)
    assert diag.refused and "below the 30-event floor" in diag.reason
