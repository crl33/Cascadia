"""Antecedent QPE windows: honest sums of the hours that exist, anchored to the data.

The names in `cascade_hydrology.antecedent` are shared DATA, not imports (the import contract
keeps hydrology provider-agnostic), so the first test pins them to the constants the MRMS job
actually writes — a drift would otherwise read nothing, forever, silently.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cascade_core.models import DerivedFeature
from cascade_hydrology import antecedent
from cascade_hydrology.antecedent import assess_antecedent

T_END = datetime(2026, 8, 28, 4, 0, tzinfo=UTC)


def _row(hours_before_end: int, value: float | None) -> DerivedFeature:
    vt = T_END - timedelta(hours=hours_before_end)
    return DerivedFeature(
        feature=antecedent.FEATURE_QPE_01H, scope_kind="basin", scope_id="basin:skagit",
        window="1h", valid_time=vt, issued_at=None, computed_at=vt + timedelta(minutes=57),
        available_at=vt + timedelta(minutes=57), method_id=antecedent.METHOD_QPE,
        product_id="product:mrms-qpe-01h-pass2", value=value, unit="mm",
        confidence_label="moderate" if value is not None else "unknown",
        quality=[] if value is not None else ["coverage_refused"],
    )


def _rows(n_hours: int, value: float = 1.0) -> list[DerivedFeature]:
    return [_row(h, value) for h in range(n_hours - 1, -1, -1)]  # ascending valid_time


def test_the_names_are_pinned_to_what_the_mrms_job_writes() -> None:
    from cascade_providers_mrms import jobs

    assert antecedent.FEATURE_QPE_01H == jobs.FEATURE_QPE
    assert antecedent.METHOD_QPE == jobs.METHOD_QPE


def test_a_full_window_sums_exactly_and_carries_no_reason() -> None:
    a = assess_antecedent(_rows(72, 0.5), ref_key="k")
    by_w = {e.window_h: e for e in a.entries}
    assert set(by_w) == {6, 24, 72}
    assert by_w[6].total.value == 3.0 and by_w[24].total.value == 12.0 and by_w[72].total.value == 36.0
    for e in by_w.values():
        assert e.hours_present == e.hours_expected == e.window_h
        assert e.reason is None and e.window_end == T_END and e.prov == "k"
    assert a.newest.valid_time == T_END


def test_the_window_ends_at_the_newest_hour_not_the_wall_clock() -> None:
    # Only 3 hours exist, the newest ending at T_END: the 6 h window is anchored THERE, so it
    # holds all 3 — a wall-clock anchor would call recent hours missing on a healthy lagged feed.
    a = assess_antecedent(_rows(3, 2.0), ref_key="k")
    six = next(e for e in a.entries if e.window_h == 6)
    assert six.window_end == T_END
    assert six.hours_present == 3 and six.total.value == 6.0
    assert "3 of 6 hours missing" in six.reason and "only the hours that exist" in six.reason


def test_a_partial_window_is_an_underestimate_that_says_so_and_never_scales() -> None:
    rows = _rows(72, 1.0)
    del rows[10:34]  # a 24-hour hole
    a = assess_antecedent(rows, ref_key="k")
    seventy2 = next(e for e in a.entries if e.window_h == 72)
    assert seventy2.total.value == 48.0, "the sum of the 48 hours that exist — never scaled to 72"
    assert seventy2.hours_present == 48 and "24 of 72 hours missing" in seventy2.reason


def test_a_coverage_refused_hour_is_an_absent_hour_and_is_named() -> None:
    rows = _rows(6, 1.0)
    rows[-2] = _row(1, None)  # one hour looked at, refused
    a = assess_antecedent(rows, ref_key="k")
    six = next(e for e in a.entries if e.window_h == 6)
    assert six.total.value == 5.0 and six.hours_present == 5
    assert "1 of them looked at but refused for coverage" in six.reason


def test_all_hours_refused_is_total_none_with_the_refusal_named() -> None:
    a = assess_antecedent([_row(h, None) for h in (2, 1, 0)], ref_key="k")
    six = next(e for e in a.entries if e.window_h == 6)
    assert six.total is None and six.hours_present == 0
    assert "looked at and refused" in six.reason
    assert a.newest is not None, "refused rows still anchor provenance: the hour WAS examined"


def test_no_rows_is_unknown_with_reason_never_zero() -> None:
    a = assess_antecedent([], ref_key="k")
    assert a.newest is None
    for e in a.entries:
        assert e.total is None and e.window_end is None and e.hours_present == 0
        assert "no observed QPE hour is known" in e.reason


async def test_the_envelope_carries_the_windows_with_resolving_provenance(tmp_path) -> None:
    """Rows in -> entries out, prov resolves, and a basin with no rows is UNKNOWN with reason."""
    from cascade_core.db import create_schema, make_engine, make_session_factory
    from cascade_core.knowledge import as_known_at
    from cascade_core.seed import seed_all
    from cascade_core.settings import SEED_FILE
    from cascade_hydrology.assemble import basin_envelope
    from tests.conftest import GEO

    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/a.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as s:
        await seed_all(s, geo_dir=GEO, seed_file=SEED_FILE)
        for r in _rows(6, 1.5):
            s.add(r)  # skagit only; every other basin has nothing
        await s.commit()
    as_of = T_END + timedelta(hours=1)
    async with factory() as s:
        k = as_known_at(s, as_of)
        env = await basin_envelope(k, await k.basins(), generated_at=as_of)
    await engine.dispose()

    by_id = {i.id: i for i in env.items}
    skagit = by_id["basin:skagit"].antecedent_precip
    assert [e.window_h for e in skagit] == [6, 24, 72]
    assert skagit[0].total.value == 9.0 and skagit[0].hours_present == 6 and skagit[0].reason is None
    assert skagit[2].total.value == 9.0 and "66 of 72 hours missing" in skagit[2].reason
    ref = env.provenance_refs[skagit[0].prov]
    assert ref.source_kind.value == "OBSERVED" and ref.product_id == "product:mrms-qpe-01h-pass2"
    assert ref.valid_time == T_END

    nook = by_id["basin:nooksack"].antecedent_precip
    assert all(e.total is None and "no observed QPE hour" in e.reason for e in nook)
    unk = env.provenance_refs[nook[0].prov]
    assert unk.source_kind.value == "UNKNOWN" and unk.freshness.state.value == "missing"
