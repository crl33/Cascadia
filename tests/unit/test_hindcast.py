"""The Event Zero A/B, pinned to the values a real replay actually produced.

`tests/fixtures/hindcast/event_zero_ab.json` is a slice of an actual retrospective replay
(`scripts/hindcast_event_zero.py`), not a transcription of the report's prose. Three things are
checked, and only the first is a test of this fixture:

1. **Shape and honesty.** Every evaluation carries its replay mode; nothing labelled
   RETROSPECTIVE is presentable as knowledge-time; every UNKNOWN carries a reason.
2. **The methods still produce these numbers.** `band`, `seasonal_multiple`,
   `independent_years`, `rank_standard_error_points`, `band_boundary` and `state_change` are
   re-run on the fixture's own recorded INPUTS and compared with its recorded outputs. A change
   to any of those functions fails here with the basin and the day that moved. Offline: no
   database, no network, no clock.
3. **The A/B verdicts are reproducible.** The escalation rules and `compare_arms` are re-run
   over the rehydrated evaluations and must reach the verdicts the run recorded — including the
   ones that say the corrected method bought nothing.

`docs/TESTING.md`: deterministic, no live weather dependence, no network.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _pkg in ("contracts", "core", "geo", "hydrology"):
    sys.path.insert(0, str(ROOT / "packages" / _pkg / "src"))

from cascade_contracts.visualization import SurfaceLevel  # noqa: E402
from cascade_hydrology import hindcast, susceptibility  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "hindcast" / "event_zero_ab.json"


@pytest.fixture(scope="module")
def run_doc() -> dict:
    return json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def evaluations(run_doc: dict) -> list[hindcast.Evaluation]:
    return hindcast.evaluations_from_document(run_doc)


# ---------------------------------------------------------------------------------------------
# 1. shape and honesty
# ---------------------------------------------------------------------------------------------


def test_every_evaluation_declares_its_replay_mode(evaluations: list[hindcast.Evaluation]) -> None:
    assert evaluations, "fixture is empty"
    assert {e.mode for e in evaluations} == {hindcast.ReplayMode.RETROSPECTIVE}


def test_the_disclosure_says_this_is_not_what_the_platform_knew(run_doc: dict) -> None:
    """The one sentence that must never be lost between the harness and a published figure."""
    disclosure = run_doc["_provenance"]["disclosure"]
    assert "RECONSTRUCTABLE" in disclosure
    assert "NOT what this deployed system knew" in disclosure
    assert "did not exist during the event" in disclosure


def test_both_arms_evaluated_the_same_basins_at_the_same_instants(evaluations: list[hindcast.Evaluation]) -> None:
    """An A/B in which one arm saw more evaluation instants than the other is not an A/B."""
    keyed = {a: {(e.basin_id, e.clocks.as_of) for e in evaluations if e.arm_id == a} for a in ("old", "new")}
    assert keyed["old"] == keyed["new"]
    assert keyed["old"], "no paired evaluations in the fixture"


def test_an_unknown_surface_always_carries_a_reason(evaluations: list[hindcast.Evaluation]) -> None:
    for e in evaluations:
        if e.surface_state == "unknown":
            assert e.surface_reason, f"{e.basin_id} at {e.clocks.as_of} is UNKNOWN with no reason"


def test_the_old_arm_publishes_no_tail_and_no_velocity(evaluations: list[hindcast.Evaluation]) -> None:
    """`@0.1.0` had a percentile and a band and nothing else; the fixture must still show that.

    This is the property that makes `rising_24h` unanswerable rather than false under the old
    arm, and `compare_arms` depends on it to refuse the phrase "lead time" there.
    """
    for e in (e for e in evaluations if e.arm_id == "old"):
        assert e.level.rank is None and e.level.multiple is None
        assert all(v.growth is None for v in e.velocity)
        assert e.level.percentile is not None or e.surface_state == "unknown"


def test_the_new_arm_never_moved_the_band(evaluations: list[hindcast.Evaluation]) -> None:
    """The Tier 0 change recalibrated nothing, and the A/B must be able to show it.

    If this ever fails, either a band edge moved or the two arms stopped reading the same ladder
    — and in both cases every lead-time number in `docs/research/event-zero-ab-2026-08-27.md`
    stops meaning what it says.
    """
    by_key = {(e.arm_id, e.basin_id, e.clocks.as_of): e for e in evaluations}
    for (arm, basin, as_of), old in by_key.items():
        if arm != "old":
            continue
        new = by_key[("new", basin, as_of)]
        assert old.level.percentile == new.level.percentile
        assert old.level.band == new.level.band


# ---------------------------------------------------------------------------------------------
# 2. the shipped methods still produce these numbers
# ---------------------------------------------------------------------------------------------


def test_band_is_reproducible_from_the_recorded_percentile(evaluations: list[hindcast.Evaluation]) -> None:
    checked = 0
    for e in evaluations:
        if e.level.percentile is None:
            continue
        assert susceptibility.band(e.level.percentile).value == e.level.band, f"{e.basin_id} {e.clocks.as_of}"
        checked += 1
    assert checked > 100


def test_seasonal_multiple_is_reproducible_from_the_recorded_flow_and_reference(
    evaluations: list[hindcast.Evaluation],
) -> None:
    checked = 0
    for e in evaluations:
        if e.level.multiple is None or e.flow is None or e.level.reference_flow is None:
            continue
        recomputed = susceptibility.seasonal_multiple(e.flow, e.level.reference_flow)
        assert recomputed is not None
        assert round(recomputed, 3) == e.level.multiple, f"{e.basin_id} {e.daily_mean_day}"
        checked += 1
    assert checked > 50


def test_the_boundary_condition_is_reproducible_from_the_recorded_sample(
    evaluations: list[hindcast.Evaluation],
) -> None:
    """The rank-space dispersion and the three-valued condition, recomputed end to end."""
    checked = 0
    for e in evaluations:
        if e.reference is None or e.level.percentile is None or not e.reference.n:
            continue
        m = susceptibility.independent_years(e.reference.n)
        assert m == e.reference.independent_years
        se = susceptibility.rank_standard_error_points(e.level.percentile, m)
        boundary, bands = susceptibility.band_boundary(e.level.percentile, se)
        assert boundary.value == e.level.boundary, f"{e.basin_id} {e.daily_mean_day}"
        assert tuple(b.value for b in bands) == e.level.bands_within_sampling_error
        checked += 1
    assert checked > 20


def test_state_change_is_reproducible_from_the_ranked_daily_means(
    run_doc: dict, evaluations: list[hindcast.Evaluation]
) -> None:
    """Re-run the shipped velocity over the fixture's own series and match every published number.

    This is the real regression test of the Tier 0 velocity: the inputs are the ranked daily
    means the replay read, the function is the shipped one, and the expected values are what the
    replay published.
    """
    series = {
        gauge: [(datetime.fromisoformat(t), float(v)) for t, v, _p in rows]
        for gauge, rows in run_doc["ranked_daily_means"].items()
    }
    checked = 0
    for e in evaluations:
        if e.arm_id != "new" or e.gauge_id not in series or e.clocks.valid_at is None:
            continue
        points = [p for p in series[e.gauge_id] if p[0] <= e.clocks.as_of]
        for v in e.velocity:
            reading = susceptibility.state_change(points, end=e.clocks.valid_at, window_h=v.window_h)
            expected = None if reading.growth is None else round(reading.growth, 4)
            assert expected == v.growth, f"{e.basin_id} {e.daily_mean_day} {v.window_h}h"
            assert reading.direction == v.growth_direction
            assert (None if reading.span_h is None else round(reading.span_h, 2)) == v.span_h
            checked += 1
    assert checked > 100


def test_the_percentile_derivative_diagnostic_matches_the_recorded_series(
    run_doc: dict, evaluations: list[hindcast.Evaluation]
) -> None:
    """The `+0 through the crest` diagnostic, recomputed from the stored percentiles.

    Pinned because it is the measured defect the whole change exists for: if this number ever
    stops being +0 on a clamped day, either the ladder gained resolution above p95 or the
    diagnostic stopped measuring what tier0 §3 measured.
    """
    series = {
        gauge: [(datetime.fromisoformat(t), p) for t, _v, p in rows if p is not None]
        for gauge, rows in run_doc["ranked_daily_means"].items()
    }
    for e in evaluations:
        if e.arm_id != "new" or e.gauge_id not in series or e.clocks.valid_at is None:
            continue
        for v in e.velocity:
            prior = [
                p
                for t, p in series[e.gauge_id]
                if abs((t - e.clocks.valid_at).total_seconds() / 3600 + v.window_h) <= susceptibility.STATE_CHANGE_TOLERANCE_H
            ]
            now = [p for t, p in series[e.gauge_id] if t == e.clocks.valid_at]
            if not prior or not now:
                assert v.percentile_delta is None
                continue
            assert v.percentile_delta == round(now[-1] - prior[0], 2), f"{e.basin_id} {e.daily_mean_day}"


# ---------------------------------------------------------------------------------------------
# 3. the measured defect, and the measured fix
# ---------------------------------------------------------------------------------------------


def test_the_clamp_silences_the_percentile_derivative_and_not_the_growth(
    evaluations: list[hindcast.Evaluation],
) -> None:
    """`tier0-measured-basis-2026-08-26.md` §3, reproduced as an assertion.

    On a clamped day the percentile-space 24 h change is identically +0, and on almost every one
    of those days the multiplicative growth is not 1 — which is the entire argument for computing
    the velocity on flow. The counts are pinned so a regression cannot quietly shrink the fix.
    """
    clamped = [e for e in evaluations if e.arm_id == "new" and e.level.clamped and not e.is_control]
    silenced = [e for e in clamped if (w := e.window(24)) is not None and w.percentile_delta == 0.0]
    alive = [e for e in silenced if (w := e.window(24)) is not None and w.growth not in (None, 1.0)]
    assert len(clamped) >= 15
    assert len(silenced) >= 12
    # every day on which the percentile went blind, the growth was still saying something
    assert len(alive) >= len(silenced) - 1
    for e in clamped:
        assert e.level.rank is not None or e.level.rank_reason, "a clamped level with neither a rank nor a reason"


def test_a_clamped_percentile_spans_a_flow_ratio_the_band_cannot_see(
    evaluations: list[hindcast.Evaluation],
) -> None:
    by_basin: dict[str, list[float]] = {}
    for e in evaluations:
        if e.arm_id == "new" and e.level.clamped and not e.is_control and e.flow is not None:
            by_basin.setdefault(e.basin_id, []).append(e.flow)
    assert by_basin
    worst = max(max(f) / min(f) for f in by_basin.values())
    assert worst > 3.0, "the fixture no longer contains the clamp defect it was cut to contain"
    for e in evaluations:
        if e.arm_id == "new" and e.level.clamped:
            assert e.level.band == SurfaceLevel.VERY_HIGH.value


# ---------------------------------------------------------------------------------------------
# 4. the A/B verdicts are reproducible from the stored run
# ---------------------------------------------------------------------------------------------


RULES = {
    r.id: r
    for r in (
        hindcast.ANY_ESCALATION,
        hindcast.BAND_HIGH_ESCALATION,
        hindcast.BAND_ESCALATION,
        hindcast.TREND_RISING,
        hindcast.RISING_24H,
        hindcast.RISING_48H,
        hindcast.growth_rank_rules(0.05),
        hindcast.growth_rank_rules(0.01),
    )
}


def test_every_recorded_comparison_recomputes_to_the_same_verdict(
    run_doc: dict, evaluations: list[hindcast.Evaluation]
) -> None:
    basins = {e.basin_id for e in evaluations}
    checked = 0
    for recorded in run_doc["comparisons"]:
        if recorded["basin_id"] not in basins:
            continue
        rule = RULES[recorded["rule_id"]]
        again = hindcast.compare_arms(evaluations, rule, basin_id=recorded["basin_id"])
        assert again.verdict == recorded["verdict"], f"{rule.id} {recorded['basin_id']}"
        assert again.legitimate_lead_time == recorded["legitimate_lead_time"]
        assert again.difference_h == recorded["difference_h"]
        assert again.old.control_firings == recorded["old"]["control_firings"]
        assert again.new.control_firings == recorded["new"]["control_firings"]
        checked += 1
    assert checked >= 12


def test_the_headline_lead_times_survive_the_12z_slice(
    run_doc: dict, evaluations: list[hindcast.Evaluation]
) -> None:
    """The report's headline rule fires only at 12:00Z, so the slice must reproduce the full run.

    A daily mean is complete at the station's local midnight (08:00Z in PST), so the first
    evaluation of the 6-hourly grid that can see a new one is 12:00Z. Anything level-driven
    therefore escalates at 12:00Z or not at all — and if that ever stops being true, the fixture
    is silently answering a different question from the run it was cut from.
    """
    basins = {e.basin_id for e in evaluations}
    checked = 0
    for recorded in run_doc["comparisons_over_the_full_run"]:
        if recorded["rule_id"] != hindcast.ANY_ESCALATION.id or recorded["basin_id"] not in basins:
            continue
        again = hindcast.compare_arms(evaluations, hindcast.ANY_ESCALATION, basin_id=recorded["basin_id"])
        assert again.verdict == recorded["verdict"], recorded["basin_id"]
        assert again.difference_h == recorded["difference_h"], recorded["basin_id"]
        checked += 1
    assert checked == len(basins)


def test_the_band_rules_show_no_difference_between_the_arms(
    run_doc: dict, evaluations: list[hindcast.Evaluation]
) -> None:
    """The honest headline: the corrected method did NOT change the level, so it cannot have
    bought a single hour on any rule that reads only the level."""
    for basin_id in {e.basin_id for e in evaluations}:
        for rule in (hindcast.BAND_ESCALATION, hindcast.BAND_HIGH_ESCALATION):
            c = hindcast.compare_arms(evaluations, rule, basin_id=basin_id)
            assert c.verdict == "no_difference"
            assert c.difference_h == 0.0
            assert c.legitimate_lead_time is False


def test_a_rule_the_old_arm_cannot_answer_is_never_called_a_lead_time(
    evaluations: list[hindcast.Evaluation],
) -> None:
    for basin_id in {e.basin_id for e in evaluations}:
        c = hindcast.compare_arms(evaluations, hindcast.RISING_24H, basin_id=basin_id)
        assert c.legitimate_lead_time is False
        assert c.caveat and "unanswerable" in c.caveat


def test_a_rule_whose_constant_was_chosen_after_the_fact_is_never_called_a_lead_time() -> None:
    rule = hindcast.growth_rank_rules(0.05)
    assert rule.fixed_independently_of_outcome is False
    assert "validated nowhere" in rule.constant_provenance


#: What each lead-time rule's predicate actually READS. Every one of these must be named in that
#: rule's `constant_provenance`. `any` was not enough: the old assertion accepted a single name
#: out of three, so `rising_24h` and `any_escalation` claimed independence while the window
#: constant that generates the headline lead time went unnamed in both.
CONSTANTS_EACH_RULE_READS: dict[str, tuple[str, ...]] = {
    "any_escalation": ("BAND_EDGES", "FLOW_STEADY_FRACTION_PER_H", "STATE_CHANGE_WINDOWS_H"),
    "band_very_high": ("BAND_EDGES",),
    "rising_24h": ("FLOW_STEADY_FRACTION_PER_H", "STATE_CHANGE_WINDOWS_H"),
    "trend_rising_6h": ("steady_epsilon",),
}


def test_the_rules_that_do_claim_a_lead_time_name_where_their_constants_came_from() -> None:
    for rule in (hindcast.ANY_ESCALATION, hindcast.BAND_ESCALATION, hindcast.RISING_24H, hindcast.TREND_RISING):
        assert rule.fixed_independently_of_outcome is True
        assert len(rule.constant_provenance) > 80, rule.id
        # EVERY constant the predicate reads must be named — not merely one of them
        required = CONSTANTS_EACH_RULE_READS[rule.id]
        missing = [n for n in required if n not in rule.constant_provenance]
        assert not missing, f"{rule.id} claims independence without naming {missing}"


def test_the_constant_inventory_is_not_vacuous() -> None:
    """The table above is only a guard if it covers the rules and names real constants."""
    from cascade_hydrology import susceptibility, trend

    assert set(CONSTANTS_EACH_RULE_READS) == {
        r.id for r in (hindcast.ANY_ESCALATION, hindcast.BAND_ESCALATION, hindcast.RISING_24H, hindcast.TREND_RISING)
    }
    for names in CONSTANTS_EACH_RULE_READS.values():
        assert names, "a rule with no required constants would pass vacuously"
        for n in names:
            assert hasattr(susceptibility, n) or hasattr(trend, n), n


def test_the_escalation_it_did_buy_is_paid_for_in_the_control_window(
    evaluations: list[hindcast.Evaluation],
) -> None:
    """Both halves of the governing question, asserted together so neither can be quoted alone.

    Where the new arm escalates earlier under `any_escalation`, it also speaks on quiet control
    days the old arm was silent on. That is the trade, it is not free, and a test that only
    pinned the lead time would let the cost drift.
    """
    earlier = 0
    extra_control = 0
    for basin_id in {e.basin_id for e in evaluations}:
        c = hindcast.compare_arms(evaluations, hindcast.ANY_ESCALATION, basin_id=basin_id)
        if c.difference_h and c.difference_h > 0:
            earlier += 1
        extra_control += c.new.control_firings - c.old.control_firings
    assert earlier >= 1, "the fixture no longer shows any earlier escalation"
    assert extra_control >= 0, "the new arm cannot be quieter than the old on the control window"
