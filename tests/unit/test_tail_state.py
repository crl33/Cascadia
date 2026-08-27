"""The high-tail representation and its velocity, pinned so the code cannot drift from the evidence.

Deliberately offline and tiny: the window statistics below were computed once from the USGS OGC
`daily` record for the six susceptibility gauges (`docs/research/high-tail-selection-2026-08-27.md`
§11 gives the exact request) and are frozen here as literals. What is tested is the shipped
REPRESENTATION's properties — monotone, censored honestly, velocity alive in the tail — not the
provider, and not any candidate that was refused.

The record context is built by the real builder and read by the real reader, so this file also
checks the coupling the `lint-imports` contract forbids expressing as an import: `cascade_hydrology`
restates the feature and method vocabulary that `cascade_providers_usgs` writes.
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from cascade_hydrology import susceptibility as sus
from cascade_hydrology.trend import FALLING, RISING, STEADY, UNKNOWN
from cascade_providers_usgs import climatology as clim
from cascade_providers_usgs.stats_parser import DailyMean

SITE = "12189500"  # the Sauk — unregulated, and the Skagit's configured susceptibility gauge

# The Sauk's day-of-year key 12-11, approved daily means before WY2026: n = 490 over 98 water
# years, WY1912-WY2025, and the stored ladder that sample produces.
SAUK_LADDER = {5: 1508.0, 10: 1819.0, 25: 2480.0, 50: 3615.0, 75: 5677.5, 90: 8831.0, 95: 12550.0}
# The real top 30 order statistics of that sample with the days they fell on. Everything this
# file asserts about the tail — the p95 reference, the ranks, the water-year support counts, the
# record maximum — is decided inside these 30 values.
SAUK_TOP_30 = [
    (date(1990, 12, 10), 10900.0), (date(1993, 12, 10), 11000.0), (date(2014, 12, 10), 11200.0),
    (date(2014, 12, 11), 11200.0), (date(1956, 12, 9), 12000.0), (date(1956, 12, 11), 13000.0),
    (date(1995, 12, 12), 13300.0), (date(2004, 12, 12), 13600.0), (date(1988, 12, 13), 13600.0),
    (date(1987, 12, 10), 13700.0), (date(1933, 12, 10), 13800.0), (date(1955, 12, 12), 14200.0),
    (date(1933, 12, 13), 14300.0), (date(2015, 12, 10), 15500.0), (date(1995, 12, 13), 15900.0),
    (date(1977, 12, 13), 16200.0), (date(1933, 12, 11), 16600.0), (date(1995, 12, 11), 16900.0),
    (date(1946, 12, 11), 17300.0), (date(1977, 12, 12), 18100.0), (date(1933, 12, 12), 20500.0),
    (date(1966, 12, 13), 21100.0), (date(1998, 12, 13), 21200.0), (date(1977, 12, 11), 22300.0),
    (date(2004, 12, 10), 23700.0), (date(2010, 12, 13), 24000.0), (date(1956, 12, 10), 24000.0),
    (date(2010, 12, 12), 28700.0), (date(2015, 12, 9), 34100.0), (date(2004, 12, 11), 37400.0),
]
# Event Zero, as the production surface measured it (tier0-measured-basis-2026-08-26 §3).
SKAGIT_09, SKAGIT_11 = 24976.0, 72440.0


def _filler_water_years() -> list[int]:
    """The 98 water years the real window sample spans, WY1912-WY2025, top-30 years included."""
    top = {clim.water_year(d) for d, _ in SAUK_TOP_30}
    rest = [y for y in range(1912, 2026) if y not in top]
    return sorted(top | set(rest[: 98 - len(top) - 1]) | {2025})


def sauk_rows(extra: list[tuple[date, float]] | None = None) -> list[DailyMean]:
    """The Sauk's 12-11 window: the real top 30, plus 460 filler values below all of them.

    9-13 December of each of the 98 water years the real sample spans — exactly the 490 values
    the production ladder for that key was built from. The filler is a monotone ramp from 1,000
    to 10,776 cfs, strictly below the smallest measured value in the top 30, so it cannot touch
    any statement this file makes: every one of them is decided at or above the 460th order
    statistic, where the values are the measured ones.
    """
    top = dict(SAUK_TOP_30)
    slots = [date(y - 1, 12, 9 + off) for y in _filler_water_years() for off in range(5)]
    ramp = sorted(d for d in slots if d not in top)
    pairs = {**{d: 1000.0 + i * 21.3 for i, d in enumerate(ramp)}, **top, **dict(extra or [])}
    return [
        DailyMean(site=SITE, day=d, raw_value=f"{v}", approval_status="Approved", unit="ft^3/s")
        for d, v in sorted(pairs.items())
    ]


@pytest.fixture(scope="module")
def context() -> dict:
    """The stored `streamflow_record_context` blob, built by the real builder and serialised."""
    return clim.build_record_context(sauk_rows(), site=SITE).to_values_json()


@pytest.fixture
def growth_context() -> dict:
    """The stored `streamflow_growth_reference` blob — a SEPARATE row since 2026-08-27.

    Separate because the velocity reads it at every percentile while the window tail is read only
    at or above `RANK_READ_EDGE`; keeping them in one document made the growth rank inherit the
    tail's p90 gate.
    """
    return clim.build_record_context(sauk_rows(), site=SITE).growth_values_json()


# --- the defect, restated so a fix cannot be claimed without moving these numbers ------------


def test_the_shipped_ladder_clamps_both_event_zero_values_to_the_same_state() -> None:
    """`percentile_of` is UNCHANGED by this work, and this is what it does at the top."""
    ladder = clim.DoyLadder(key="12-11", values=SAUK_LADDER, sample_count=490)
    low = clim.percentile_of(SKAGIT_09, ladder)
    high = clim.percentile_of(SKAGIT_11, ladder)
    assert (low.percentile, high.percentile) == (95.0, 95.0)
    assert clim.OUTSIDE_RANGE in low.quality and clim.OUTSIDE_RANGE in high.quality
    assert high.percentile - low.percentile == 0.0  # the silenced derivative, exactly


def test_the_multiple_is_one_exactly_where_the_shipped_percentile_starts_clamping() -> None:
    """The two statements must not disagree about where discrimination stops."""
    ladder = clim.DoyLadder(key="12-11", values=SAUK_LADDER, sample_count=490)
    reference = SAUK_LADDER[sus.REFERENCE_PERCENTILE]
    assert sus.seasonal_multiple(reference, reference) == pytest.approx(1.0)
    assert clim.OUTSIDE_RANGE not in clim.percentile_of(reference * 0.999, ladder).quality
    assert clim.OUTSIDE_RANGE in clim.percentile_of(reference * 1.001, ladder).quality


# --- the level: rank and multiple -----------------------------------------------------------


def test_the_built_context_is_the_real_window_where_it_matters(context) -> None:
    support = context["keys"]["12-11"]
    assert (support["n"], support["water_years"]) == (490, 98)
    assert support["max"] == 37400.0 and support["max_day"] == "2004-12-11"
    # The floor is the sample's OWN p90 by the same R type-7 estimator the ladder uses — not a
    # separate constant that could drift away from it. (It is not the production 8,831 because
    # the 460 filler values below the measured top 30 are a ramp, not the real distribution.)
    sample = sorted(float(r.raw_value) for r in sauk_rows() if 12 == r.day.month and 9 <= r.day.day <= 13)
    assert support["tail_floor"] == pytest.approx(clim.percentile(sample, clim.TAIL_FLOOR_PERCENTILE))
    assert support["tail_floor"] < min(v for _, v in SAUK_TOP_30), "the measured tail is all stored"
    assert context["begin_water_year"] == 1912 and context["end_water_year"] == 2025
    # bounded by construction: only the tail is persisted, not the record
    assert 0 < len(context["tail"]) < 0.2 * context["used_rows"]


def test_water_year_boundary() -> None:
    assert clim.water_year(date(2025, 9, 30)) == 2025
    assert clim.water_year(date(2025, 10, 1)) == 2026
    assert clim.water_year(date(2025, 12, 11)) == 2026


def test_the_rank_is_exact_censored_at_one_and_names_the_record_it_beat(context) -> None:
    """Honest where the percentile is not — and just as silent across the crest."""
    low = sus.window_rank(SKAGIT_09, "12-09", context)
    high = sus.window_rank(SKAGIT_11, "12-11", context)
    # Each day is ranked against its OWN key: 12-09's window is 7-11 December, a different and
    # here smaller sample than 12-11's 9-13 December, and the two ranks are not interchangeable.
    assert low.rank == 3 and low.of < high.of and not low.exceeds_record
    assert (high.rank, high.of) == (1, 491) and high.exceeds_record
    assert sus.EXCEEDS_WINDOW_RECORD in high.quality
    assert high.previous_max == 37400.0 and high.previous_max_day == date(2004, 12, 11)
    # Censored at 1: twice the flow is the same rank. This is why it cannot carry the velocity.
    assert sus.window_rank(SKAGIT_11 * 2, "12-11", context).rank == 1


def test_the_rank_is_exact_inside_the_stored_tail(context) -> None:
    """Not an estimate: the count is over persisted order statistics, so it is checkable."""
    ranked = sus.window_rank(23700.0, "12-11", context)  # 2004-12-10, the 5th largest
    above = [v for _, v in SAUK_TOP_30 if v > 23700.0]
    assert ranked.rank == len(above) + 1
    assert not ranked.exceeds_record


def test_below_the_stored_tail_the_rank_refuses_instead_of_guessing(context) -> None:
    """Only the top decile is persisted; below it the percentile resolves and says so."""
    ranked = sus.window_rank(3000.0, "12-11", context)
    assert ranked.rank is None
    assert "tail floor" in ranked.reason and "percentile resolves" in ranked.reason


def test_the_seasonal_multiple_is_unbounded_and_carries_the_crest() -> None:
    """The only level statement whose Event Zero endpoints differ."""
    reference = SAUK_LADDER[sus.REFERENCE_PERCENTILE]
    low = sus.seasonal_multiple(SKAGIT_09, reference)
    high = sus.seasonal_multiple(SKAGIT_11, reference)
    assert low == pytest.approx(1.99, abs=0.01)
    assert high == pytest.approx(5.77, abs=0.01)
    assert high / low == pytest.approx(SKAGIT_11 / SKAGIT_09, rel=1e-9)


def test_the_multiple_refuses_a_reference_it_cannot_divide_by() -> None:
    assert sus.seasonal_multiple(1000.0, None) is None
    assert sus.seasonal_multiple(1000.0, 0.0) is None
    assert sus.seasonal_multiple(1000.0, float("nan")) is None


def test_the_level_is_monotone_in_flow(context) -> None:
    reference = SAUK_LADDER[sus.REFERENCE_PERCENTILE]
    ladder = clim.DoyLadder(key="12-11", values=SAUK_LADDER, sample_count=490)
    previous = None
    for value in (500.0, 1500.0, 5000.0, 12550.0, 20000.0, SKAGIT_09, 50000.0, SKAGIT_11):
        reading = sus.window_rank(value, "12-11", context)
        current = (
            clim.percentile_of(value, ladder).percentile,
            -(reading.rank if reading.rank is not None else 10**6),
            sus.seasonal_multiple(value, reference),
        )
        if previous is not None:
            assert current[0] >= previous[0]
            assert current[1] >= previous[1]
            assert current[2] > previous[2]  # strictly, always: the multiple never ties
        previous = current


def test_thin_tail_support_is_labelled_and_never_suppressed() -> None:
    """A tail backed by one water year is a description of one flood, and it says so.

    Twelve quiet years and one wet one: everything above p90 comes from December 2015, which is
    exactly cedar's measured situation (`high-tail-selection-2026-08-27.md` §4). The rank is
    still published — the rule LABELS, it never suppresses — and the label travels with it.
    """
    rows = [
        DailyMean(site=SITE, day=date(y, 12, 9 + off),
                  raw_value="30000" if y == 2015 else "1000",
                  approval_status="Approved", unit=None)
        for y in range(2005, 2017) for off in range(5)
    ]
    thin = clim.build_record_context(rows, site=SITE).to_values_json()
    assert thin["keys"]["12-11"]["tail_years"] == 1 < sus.MIN_TAIL_YEARS
    reading = sus.window_rank(40000.0, "12-11", thin)
    assert reading.rank == 1, "the statement is labelled, not withheld"
    assert sus.THIN_TAIL_SUPPORT in reading.quality


def test_adding_one_more_water_year_moves_the_rank_by_one_and_nothing_else_breaks() -> None:
    """Stability under a reasonable record change: the ladder is rebuilt annually."""
    before = clim.build_record_context(sauk_rows(), site=SITE).to_values_json()
    after = clim.build_record_context(
        sauk_rows(extra=[(date(2027, 12, 11), 60000.0)]), site=SITE
    ).to_values_json()
    a, b = sus.window_rank(SKAGIT_09, "12-11", before), sus.window_rank(SKAGIT_09, "12-11", after)
    assert b.rank == a.rank + 1
    assert b.of == a.of + 1
    assert after["end_water_year"] == 2028


def test_the_rank_is_absent_rather_than_wrong_when_no_context_is_stored() -> None:
    assert sus.window_rank(SKAGIT_11, "12-11", None) is None
    assert sus.window_rank(SKAGIT_11, "12-11", {}) is None
    assert sus.window_rank(SKAGIT_11, "07-04", {"keys": {}, "tail": []}) is None


# --- the boundary condition (brief §7 correction 4) ------------------------------------------


def test_the_sample_is_deflated_by_the_smoothing_window_before_any_error_is_quoted() -> None:
    """490 days are 98 independent years; quoting n would understate the error by sqrt(5)."""
    assert sus.independent_years(490) == 98
    assert sus.independent_years(490, window_days=0) == 490
    assert sus.independent_years(0) == 1  # never a zero denominator


def test_the_sampling_error_is_the_binomial_rank_error_at_the_independent_count() -> None:
    """The quantity register X8 already computes: +/-5.5 points at p90 with 30 years."""
    assert sus.rank_standard_error_points(90.0, 30) == pytest.approx(5.48, abs=0.01)
    assert sus.rank_standard_error_points(90.0, 98) == pytest.approx(3.03, abs=0.01)
    # more years, less error; and a degenerate count is refused rather than divided by
    assert sus.rank_standard_error_points(90.0, 98) < sus.rank_standard_error_points(90.0, 30)
    assert sus.rank_standard_error_points(90.0, 0) is None


def test_the_boundary_is_a_condition_and_it_fails_closed() -> None:
    """`unquantified` never means `separated`: a surface that could not check must not read
    like one that checked and was satisfied."""
    from cascade_contracts import BandBoundary
    from cascade_contracts.visualization import SurfaceLevel

    assert sus.band_boundary(50.0, None) == (BandBoundary.UNQUANTIFIED, ())
    near, bands = sus.band_boundary(89.5, sus.rank_standard_error_points(89.5, 98))
    assert near is BandBoundary.NEAR_BAND_EDGE
    assert bands == (SurfaceLevel.HIGH, SurfaceLevel.VERY_HIGH)
    far, none = sus.band_boundary(50.0, sus.rank_standard_error_points(50.0, 98))
    assert far is BandBoundary.SEPARATED and none == ()


def test_the_boundary_condition_adds_no_new_edge_of_its_own() -> None:
    """Only the existing band edges are compared against; nothing new is introduced."""
    edges = {edge for edge, _ in sus.BAND_EDGES}
    assert edges == {25.0, 75.0, 90.0}
    assert sus.METHOD_PARAMETERS["band_edges_percentile"] == [25, 75, 90]
    assert sus.METHOD_PARAMETERS["calibrated"] is False


# --- the velocity ----------------------------------------------------------------------------

D9 = datetime(2025, 12, 9, 8, 0, tzinfo=UTC)
D10 = D9 + timedelta(hours=24)
D11 = D9 + timedelta(hours=48)


def test_the_velocity_survives_the_crest_where_every_percentile_derivative_dies() -> None:
    """The property the whole selection turns on, at the Sauk's real Event Zero pair."""
    change = sus.state_change([(D9, SKAGIT_09), (D11, SKAGIT_11)], end=D11, window_h=48)
    assert change.growth == pytest.approx(2.90, abs=0.01)
    assert change.direction == RISING
    assert change.span_h == pytest.approx(48.0)


def test_the_velocity_does_not_depend_on_the_ladder_at_all() -> None:
    """X8 disputes the ladder's vintage; it cannot move this number. (X8 is NOT resolved by that.)"""
    growth = sus.state_change([(D9, SKAGIT_09), (D11, SKAGIT_11)], end=D11, window_h=48).growth
    for reference in (12550.0, 1.0, 999999.0):  # wildly different ladders
        low = sus.seasonal_multiple(SKAGIT_09, reference)
        high = sus.seasonal_multiple(SKAGIT_11, reference)
        assert high / low == pytest.approx(growth, rel=1e-9)


def test_the_velocity_has_a_sign_and_detects_the_recession() -> None:
    falling = sus.state_change([(D9, 62600.0), (D11, 21100.0)], end=D11, window_h=48)
    assert falling.direction == FALLING and falling.growth == pytest.approx(0.337, abs=0.001)
    steady = sus.state_change([(D9, 5000.0), (D11, 5300.0)], end=D11, window_h=48)
    assert steady.direction == STEADY  # inside trend.py's 1 %/h band compounded over 48 h


def test_the_velocity_refuses_rather_than_interpolates() -> None:
    gap = sus.state_change([(D9, 1000.0), (D11, 4000.0)], end=D11, window_h=24)
    assert gap.growth is None and gap.direction == UNKNOWN and "within 6 h" in gap.reason
    empty = sus.state_change([], end=D11, window_h=24)
    assert empty.growth is None and "at or before" in empty.reason
    zero = sus.state_change([(D10, 0.0), (D11, 4000.0)], end=D11, window_h=24)
    assert zero.growth is None and "multiplicative rate" in zero.reason
    # A "24 h growth" measured over 14 h is a different number wearing the same label: the far
    # endpoint is 10 h from where a 24 h window puts it, so the window is refused, not shortened.
    short = sus.state_change([(D10, 4000.0), (D10 - timedelta(hours=14), 1000.0)], end=D10, window_h=24)
    assert short.growth is None and "within 6 h of" in short.reason


def test_the_velocity_is_computable_when_the_level_is_not() -> None:
    """No climatology, no reference, no rank — and the state change is still exact."""
    assert sus.window_rank(SKAGIT_09, "12-11", None) is None
    assert sus.seasonal_multiple(SKAGIT_09, None) is None
    assert sus.state_change([(D9, SKAGIT_09), (D11, SKAGIT_11)], end=D11, window_h=48).growth is not None


def test_growth_rank_describes_speed_without_drawing_a_band(growth_context) -> None:
    reference = growth_context["growth"]["24"]
    assert reference["n"] > 0 and reference["span_days"] == 1
    biggest = max(reference["top"])
    rank, n, reason = sus.growth_rank(biggest + 1.0, reference)
    assert (rank, n, reason) == (1, reference["n"], None)
    # below the stored decile the answer is a BOUND with its reason, never a fabricated rank
    rank, n, reason = sus.growth_rank(1.0, reference)
    assert rank is None and n == reference["n"] and "only part stored" in reason
    assert sus.growth_rank(2.0, None) == (None, None, "no growth reference stored for this gauge")


def test_the_growth_reference_matches_the_calendar_and_not_the_row_order() -> None:
    """A gap in the record must not become a '24 h change' measured over three years."""
    rows = [
        DailyMean(site=SITE, day=date(2000, 12, 1), raw_value="100", approval_status="Approved", unit=None),
        DailyMean(site=SITE, day=date(2000, 12, 2), raw_value="200", approval_status="Approved", unit=None),
        DailyMean(site=SITE, day=date(2003, 12, 2), raw_value="900", approval_status="Approved", unit=None),
    ]
    daily = clim._approved_daily_means(rows, site=SITE)
    reference = clim.build_growth_reference(daily, window_h=24, tail_fraction=1.0)
    assert reference.n == 1 and reference.top == (2.0,)  # the 2003 value has no neighbour


def test_provisional_values_never_reach_the_record_context() -> None:
    """Same filter as the ladder: a provisional value can be revised under the platform's feet."""
    rows = [*sauk_rows(), DailyMean(site=SITE, day=date(2026, 12, 11), raw_value="999999",
                                    approval_status="Provisional", unit=None)]
    built = clim.build_record_context(rows, site=SITE)
    assert built.keys["12-11"].maximum == 37400.0


# --- the vocabulary the surface and the builder must agree on --------------------------------


def test_the_surface_and_the_builder_agree_on_the_record_context_vocabulary() -> None:
    """cascade_hydrology must not import a provider package, so the coupling is TESTED."""
    assert sus.RECORD_CONTEXT_METHOD_ID == clim.RECORD_CONTEXT_METHOD_ID
    assert sus.DOY_WINDOW_DAYS == clim.WINDOW_DAYS
    assert sus.MIN_TAIL_YEARS == clim.MIN_TAIL_YEARS
    assert sus.REFERENCE_PERCENTILE in clim.PERCENTILES
    assert sus.REFERENCE_PERCENTILE == max(clim.PERCENTILES), "the multiple references the TOP breakpoint"
    assert sus.RANK_READ_EDGE == float(clim.TAIL_FLOOR_PERCENTILE), (
        "the surface must only ask for a rank where the builder actually stored one"
    )
    assert tuple(sus.STATE_CHANGE_WINDOWS_H) == clim.GROWTH_WINDOWS_H
    assert sus.OUTSIDE_CLIMATOLOGY_RANGE == clim.OUTSIDE_RANGE
    # the +/-window arithmetic wraps the year identically on both sides of the boundary
    assert sus.DOY_KEYS == clim.DOY_KEYS
    for key in ("01-01", "12-31", "02-29", "07-04"):
        assert sus._window_keys(key, clim.WINDOW_DAYS) == set(clim.window_keys(key))


def test_a_growth_rank_is_never_absent_merely_because_the_percentile_is_low() -> None:
    """The decoupling, asserted as the ABSENCE of a state rather than the presence of a message.

    There used to be two reasons a growth rank could be missing: nobody had built the reference,
    or the surface had declined to read it below p90. The second was the defect — `RANK_READ_EDGE`
    is the same constant as the top band edge, so the rank arrived only once the band already read
    VERY_HIGH, and the velocity fires below that. The reference is now read at every percentile,
    so "not read" is not a state the surface can be in, and the only remaining reason must be the
    one somebody can act on.
    """
    assert not hasattr(sus, "NO_GROWTH_REFERENCE_READ_REASON"), (
        "the p90-gated refusal is the defect; its reintroduction is a regression"
    )
    only_reason = sus.NO_GROWTH_REFERENCE_BUILT_REASON
    assert "build_climatology" in only_reason, "the remaining reason must name what closes it"
    assert f"p{int(sus.RANK_READ_EDGE)}" not in only_reason, (
        "the reason must not cite the percentile edge — the read no longer depends on it"
    )
    # and the reference is fetched under its OWN identity, not the tail's
    assert sus.GROWTH_REFERENCE_METHOD_ID != sus.RECORD_CONTEXT_METHOD_ID
    assert sus.GROWTH_REFERENCE_FEATURE != sus.RECORD_CONTEXT_FEATURE

def test_the_tail_and_the_velocity_have_to_be_checked_together(context) -> None:
    """The coupling, in one test, because shipping half of this change is the failure mode.

    tier0 §3: the ladder clamps at p95, so a derivative taken in PERCENTILE space reads `+0`
    through the crest. That makes the high-tail representation and the velocity one decision and
    not two — it is not enough that the level discriminates, and not enough that the growth is
    non-trivial. The same two Event Zero flows, 2.9x apart and identical to the shipped
    percentile, must move BOTH.

    A collapse of either half fails here: clamping the multiple or refusing the tail rank fails
    (2), and re-pointing the state change at the percentile series (whose ratio is exactly 1.0
    on these two days) fails (3).
    """
    ladder = clim.DoyLadder(key="12-11", values=SAUK_LADDER, sample_count=490)
    reference = SAUK_LADDER[sus.REFERENCE_PERCENTILE]

    # 1. the shipped percentile cannot tell the two flows apart, and its derivative is +0
    p_low = clim.percentile_of(SKAGIT_09, ladder).percentile
    p_high = clim.percentile_of(SKAGIT_11, ladder).percentile
    assert p_high - p_low == 0.0 and p_high / p_low == 1.0

    # 2. the LEVEL discriminates anyway: the multiple strictly up, the rank strictly better
    m_low = sus.seasonal_multiple(SKAGIT_09, reference)
    m_high = sus.seasonal_multiple(SKAGIT_11, reference)
    assert m_high > m_low > 1.0
    assert m_high / m_low == pytest.approx(SKAGIT_11 / SKAGIT_09, rel=1e-9)
    mid = sus.window_rank(15000.0, "12-11", context)
    top = sus.window_rank(SKAGIT_11, "12-11", context)
    assert top.rank is not None and mid.rank is not None and top.rank < mid.rank

    # 3. the VELOCITY discriminates too, and it is the FLOW ratio — not the percentile ratio,
    #    which is the number a representation-space derivative would have published
    change = sus.state_change([(D9, SKAGIT_09), (D11, SKAGIT_11)], end=D11, window_h=48)
    assert change.growth == pytest.approx(SKAGIT_11 / SKAGIT_09, rel=1e-9)
    assert change.direction == RISING
    assert change.growth != pytest.approx(p_high / p_low, rel=1e-3), (
        "the state change is reading the clamped percentile, which is what tier0 §3 measured as +0"
    )


def test_each_new_statement_publishes_its_own_method_identity() -> None:
    """Four claims, four identities, pinned to their literals.

    DATA_DOCTRINE §8 makes a method change a new identity, so these strings are a contract a
    consumer switches on and not an implementation detail. Mutating the id a statement is
    STAMPED with was caught only by the perf semantic body baseline, which is evidence rather
    than a contract — it is regenerated on purpose whenever the endpoint's answer legitimately
    changes, and the provenance guard would be regenerated away with it.
    """
    assert sus.TAIL_STATE_METHOD_ID == "method:streamflow-tail-state@0.1.0"
    assert sus.STATE_CHANGE_METHOD_ID == "method:streamflow-state-change@0.1.0"
    # @2.0.0: the growth reference moved out of this document, so what is stored changed
    assert sus.RECORD_CONTEXT_METHOD_ID == "method:streamflow-record-context@2.0.0"
    assert sus.GROWTH_REFERENCE_METHOD_ID == "method:streamflow-growth-reference@1.0.0"
    # an exact rank, a ratio of two daily means, the ladder they are read beside, the published
    # cross-check and the banded index are five different claims and never interchangeable
    assert len({
        sus.TAIL_STATE_METHOD_ID, sus.STATE_CHANGE_METHOD_ID, sus.CLIMATOLOGY_METHOD_ID,
        sus.PUBLISHED_CLIMATOLOGY_METHOD_ID, sus.SURFACE_METHOD_V2,
        sus.RECORD_CONTEXT_METHOD_ID, sus.GROWTH_REFERENCE_METHOD_ID,
    }) == 7
