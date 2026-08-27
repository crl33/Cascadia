"""The set-based `Knowledge` readers answer exactly what the singular ones answer.

`/viz/basins` issued 120 statements to ask twelve questions of six scopes. The fix is that each
question is now asked once, with `IN (…)` where it had `=`, and that the answers are memoised for
the life of one request. Both halves of that are only safe if one thing is true, and it is the
thing this module exists to check:

> for every reader, and for every input, **the batched answer is the singular answer**.

That is not a property that can be inspected by reading the SQL. `latest_forecast_run` is a
`LIMIT 1` over `(issued_at DESC, id DESC)` and its batched form is a `row_number()` window;
`latest_observation` takes the last row of a fourteen-day window while its batched form never
reads the window at all. Each pair is written differently on purpose — the whole point is to move
fewer rows — so each pair is *compared* here, against data built to make the two disagree if they
can: several revisions of one instant, several runs of two products at one point, several
recomputations of one feature, and rows on the wrong side of the knowledge clock.

The second half is the memo, and it gets the same treatment: it may not answer a question that
was not asked (a narrowed window must equal the narrow statement, not the wide one), it may not
survive a change of knowledge time, and what it hands out may not be corruptible by a caller.

Offline: SQLite, fixed clock, no network (docs/TESTING.md).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from cascade_core.db import create_schema, make_engine, make_session_factory
from cascade_core.knowledge import as_known_at
from cascade_core.models import (
    Basin,
    DerivedFeature,
    ForecastPoint,
    ForecastRun,
    ForecastValue,
    Observation,
    RawArtifact,
    Station,
    Threshold,
)
from cascade_core.registry import (
    PRODUCT_NWM_MR,
    PRODUCT_NWPS_FORECAST,
    PRODUCT_NWPS_THRESHOLDS,
    PRODUCT_USGS_IV,
    PRODUCT_USGS_OGC_DAILY,
)
from cascade_core.seed import seed_all
from cascade_core.settings import SEED_FILE
from tests.conftest import GEO

NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=3)

#: Two seeded points and two seeded stations, so every batch has more than one scope in it and a
#: reader that ignored its scope filter would be caught rather than accidentally right.
FP_A, FP_B = "fp:nwps:MVEW1", "fp:nwps:AUBW1"
ST_A, ST_B = "station:usgs:12200500", "station:usgs:12113000"


@pytest.fixture
async def sessions(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/batching.db")
    await create_schema(engine)
    factory = make_session_factory(engine)
    async with factory() as session:
        await seed_all(session, geo_dir=GEO, seed_file=SEED_FILE)
    yield factory
    await engine.dispose()


async def _artifact(session, product_id: str) -> RawArtifact:
    art = RawArtifact(
        sha256="b" * 64, object_key="test/batching", product_id=product_id, fetched_at=NOW,
        request_url="https://example.invalid/batching", bytes=1, http_status=200,
        content_type="application/json", retention_class=None,
    )
    session.add(art)
    await session.flush()
    return art


def _obs(art_id: int, **kw) -> Observation:
    base = dict(
        station_id=ST_A, product_id=PRODUCT_USGS_IV, variable="stage", value=1.0, unit="ft",
        datum="NAVD88", valid_time=NOW, retrieved_at=NOW, available_at=NOW, quality=[],
        qualifier_raw=None, revision_of=None, revision_seq=0, raw_artifact_id=art_id,
    )
    base.update(kw)
    return Observation(**base)


def _run(art_id: int, **kw) -> ForecastRun:
    base = dict(
        product_id=PRODUCT_NWPS_FORECAST, fp_id=FP_A, issued_at=NOW, retrieved_at=NOW,
        available_at=NOW, issuer="NWRFC", primary_variable="stage", unit="ft", stage_unit="ft",
        flow_unit="cfs", datum="NAVD88", raw_artifact_id=art_id, supersedes_run_id=None,
    )
    base.update(kw)
    return ForecastRun(**base)


def _threshold(art_id: int, **kw) -> Threshold:
    base = dict(
        fp_id=FP_A, product_id=PRODUCT_NWPS_THRESHOLDS, category="action", value=10.0, unit="ft",
        basis="stage", datum="NAVD88", source_kind="OFFICIAL_FORECAST", effective_from=NOW,
        retrieved_at=NOW, raw_artifact_id=art_id,
    )
    base.update(kw)
    return Threshold(**base)


def _feature(**kw) -> DerivedFeature:
    base = dict(
        feature="basin_swe_percent_of_median", scope_kind="basin", scope_id="basin:skagit",
        window=None, valid_time=NOW, issued_at=None, computed_at=NOW, available_at=NOW,
        method_id="method:snotel-basin-swe-context@1.0.0", product_id=None, value=1.0, unit="pct",
        percentile=None, climatology_ref=None, confidence_label="moderate", quality=[], inputs=[],
    )
    base.update(kw)
    return DerivedFeature(**base)


# --- stations / points ------------------------------------------------------------------


async def test_stations_and_points_batched_equal_singular(sessions) -> None:
    async with sessions() as s:
        k = as_known_at(s, NOW)
        batched = await k.stations_by_id([ST_A, ST_B, "station:usgs:nonexistent"])
        fresh = as_known_at(s, NOW)
        assert {sid: await fresh.station(sid) for sid in (ST_A, ST_B)} == batched
        # A miss is remembered as a miss, not re-asked and not turned into a row.
        assert await fresh.station("station:usgs:nonexistent") is None
        assert batched.keys() == {ST_A, ST_B}

        points = await k.forecast_points_by_lid(["MVEW1", "AUBW1", "ZZZZ9"])
        assert {p.id for p in points.values()} == {FP_A, FP_B}
        assert (await as_known_at(s, NOW).forecast_point_by_lid("MVEW1")).id == points["MVEW1"].id
        assert await as_known_at(s, NOW).forecast_point_by_lid("ZZZZ9") is None


# --- thresholds -------------------------------------------------------------------------


async def test_thresholds_batched_equal_singular_including_supersession(sessions) -> None:
    """Two points, several categories, and a later row for one category that must win."""
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_NWPS_THRESHOLDS)
        s.add_all([
            _threshold(art.id, fp_id=FP_A, category="action", value=10.0),
            _threshold(art.id, fp_id=FP_A, category="minor", value=20.0),
            _threshold(art.id, fp_id=FP_A, category="action", value=11.0, effective_from=NOW + timedelta(hours=1)),
            _threshold(art.id, fp_id=FP_B, category="action", value=5.0),
            # After T: invisible to both forms, or the knowledge filter is not being applied.
            _threshold(art.id, fp_id=FP_A, category="major", value=99.0, effective_from=LATER + timedelta(hours=1)),
        ])
        await s.flush()

        batched = await as_known_at(s, LATER).thresholds_for([FP_A, FP_B])
        singular = as_known_at(s, LATER)
        assert {fp: await singular.thresholds(fp) for fp in (FP_A, FP_B)} == batched
        assert batched[FP_A]["action"].value == 11.0  # the later row, not the first
        assert "major" not in batched[FP_A]  # effective_from > T
        assert batched[FP_B].keys() == {"action"}


# --- forecast runs and values -----------------------------------------------------------


async def test_latest_forecast_run_picks_the_newest_visible_run_of_the_asked_for_products(sessions) -> None:
    """Two products, two points, several cycles, and a run that is not yet knowledge-visible.

    Asserted against the run that *ought* to win rather than only against the other reader:
    `latest_forecast_run` now answers out of `latest_forecast_runs`, so comparing the two would
    agree with itself however the ordering were written. The expectation is spelled out.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_NWPS_FORECAST)
        old_a = _run(art.id, fp_id=FP_A, issued_at=NOW - timedelta(hours=6))
        new_a = _run(art.id, fp_id=FP_A, issued_at=NOW)
        model_a = _run(art.id, fp_id=FP_A, issued_at=NOW + timedelta(hours=2), product_id=PRODUCT_NWM_MR)
        only_b = _run(art.id, fp_id=FP_B, issued_at=NOW - timedelta(hours=1))
        # Issued before T but not retrieved until after it: invisible at T however it is read.
        unseen = _run(art.id, fp_id=FP_A, issued_at=NOW + timedelta(hours=1), available_at=LATER + timedelta(hours=1))
        s.add_all([old_a, new_a, model_a, only_b, unseen])
        await s.flush()

        expected = {
            None: {FP_A: model_a, FP_B: only_b},  # every product: the model run is newest
            frozenset({PRODUCT_NWPS_FORECAST}): {FP_A: new_a, FP_B: only_b},
            frozenset({PRODUCT_NWM_MR}): {FP_A: model_a},
        }
        for products, want in expected.items():
            batched = await as_known_at(s, LATER).latest_forecast_runs([FP_A, FP_B], product_ids=products)
            assert {fp: r.id for fp, r in batched.items()} == {fp: r.id for fp, r in want.items()}, products
            singular = as_known_at(s, LATER)
            for fp in (FP_A, FP_B):
                run = await singular.latest_forecast_run(fp, product_ids=products)
                assert (run.id if run else None) == (want[fp].id if fp in want else None), (products, fp)

        # The defect the product filter exists for: the DEFAULT must be the official forecast,
        # even on a cycle where the model run is the newest thing at the point.
        assert (await as_known_at(s, LATER).latest_forecast_runs([FP_A]))[FP_A].id == new_a.id


async def test_forecast_values_batched_equal_singular(sessions) -> None:
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_NWPS_FORECAST)
        runs = [_run(art.id, fp_id=FP_A, issued_at=NOW), _run(art.id, fp_id=FP_B, issued_at=NOW)]
        s.add_all(runs)
        await s.flush()
        for run in runs:
            s.add_all([
                ForecastValue(run_id=run.id, valid_time=NOW + timedelta(hours=h), stage=float(h), flow=None)
                for h in (3, 1, 2)  # inserted out of order: the reader owns the ordering
            ])
        await s.flush()

        ids = [r.id for r in runs]
        batched = await as_known_at(s, NOW).forecast_values_for([*ids, 999999])
        singular = as_known_at(s, NOW)
        assert {i: [v.id for v in await singular.forecast_values(i)] for i in ids} == {i: [v.id for v in batched[i]] for i in ids}
        assert [v.stage for v in batched[ids[0]]] == [1.0, 2.0, 3.0]
        assert batched[999999] == []


# --- observations -----------------------------------------------------------------------


async def test_latest_observation_batched_equals_singular_across_revisions(sessions) -> None:
    """Revisions, two variables, two stations, and a revision that arrived after T.

    **The revised row is inserted BEFORE the row it revises**, so it carries the LOWER `id`.
    That is the whole point of the arrangement: the two readers are written differently — the
    singular one takes the last row of an ascending `(valid_time, revision_seq, id)` ordering,
    the batched one the first row of that ordering reversed — and if either fell back on insert
    order it would now pick the superseded value. USGS backfills arrive out of order, so this is
    not a contrived shape.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([
            _obs(art.id, station_id=ST_A, variable="stage", valid_time=NOW, value=1.5, revision_seq=1),
            _obs(art.id, station_id=ST_A, variable="stage", valid_time=NOW, value=1.0, revision_seq=0),
            _obs(art.id, station_id=ST_A, variable="stage", valid_time=NOW - timedelta(hours=1), value=0.5),
            _obs(art.id, station_id=ST_A, variable="flow", valid_time=NOW, value=900.0, unit="cfs"),
            _obs(art.id, station_id=ST_B, variable="stage", valid_time=NOW - timedelta(minutes=30), value=2.0),
            # The highest revision of the newest instant, knowledge-visible only after T.
            _obs(art.id, station_id=ST_A, variable="stage", valid_time=NOW, value=9.9, revision_seq=2, available_at=LATER + timedelta(hours=1)),
        ])
        await s.flush()

        batched = await as_known_at(s, LATER).latest_observations([ST_A, ST_B], ("stage", "flow"))
        singular = as_known_at(s, LATER)
        expected = {}
        for st in (ST_A, ST_B):
            for var in ("stage", "flow"):
                row = await singular.latest_observation(st, var)
                if row is not None:
                    expected[(st, var)] = row
        assert {c: r.id for c, r in batched.items()} == {c: r.id for c, r in expected.items()}
        assert batched[(ST_A, "stage")].value == 1.5  # the highest revision KNOWN AT T, not 1.0 and not 9.9


async def test_the_two_observation_readers_break_a_revision_tie_the_same_way(sessions) -> None:
    """Two rows claiming the same revision of the same instant.

    The unique constraint permits it across products, and nothing in the revision rule says
    which wins. What matters is that the two readers do not disagree — a hazard category that
    depended on which reader had been called would be the worst kind of bug to find. Both order
    on `id` last, so both pick the same row; this pins that they do.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        other = await _artifact(s, PRODUCT_USGS_OGC_DAILY)
        s.add_all([
            _obs(art.id, valid_time=NOW, value=3.0, revision_seq=0),
            _obs(other.id, valid_time=NOW, value=4.0, revision_seq=0, product_id=PRODUCT_USGS_OGC_DAILY),
        ])
        await s.flush()
        batched = await as_known_at(s, NOW).latest_observations([ST_A], ("stage",))
        singular = await as_known_at(s, NOW).latest_observation(ST_A, "stage")
        assert batched[(ST_A, "stage")].id == singular.id
        window = await as_known_at(s, NOW).observations(ST_A, "stage", since=NOW - timedelta(hours=1))
        assert [o.id for o in window] == [singular.id]  # one row per valid_time, and the same one


async def test_observations_for_equals_the_singular_reads_it_replaces(sessions) -> None:
    """The mixed-window batch: a six-hour window on one variable and one instant on the other."""
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all(
            [_obs(art.id, station_id=ST_A, variable="stage", valid_time=NOW - timedelta(hours=h), value=float(h)) for h in range(0, 10)]
            + [_obs(art.id, station_id=ST_A, variable="flow", valid_time=NOW, value=900.0, unit="cfs")]
            + [_obs(art.id, station_id=ST_B, variable="stage", valid_time=NOW, value=7.0)]
        )
        await s.flush()

        # Inside every spec's window, but not yet known at T: no spec may return it.
        s.add(_obs(art.id, station_id=ST_A, variable="flow", valid_time=NOW, value=42.0, unit="cfs",
                   revision_seq=1, available_at=NOW + timedelta(hours=1)))
        s.add(_obs(art.id, station_id=ST_B, variable="stage", valid_time=NOW - timedelta(hours=2),
                   value=42.0, available_at=NOW + timedelta(hours=1)))
        await s.flush()

        specs = [
            (ST_A, "stage", NOW - timedelta(hours=6), NOW),
            (ST_A, "flow", NOW, NOW),
            (ST_B, "stage", NOW - timedelta(hours=6), NOW),
        ]
        batched = await as_known_at(s, NOW).observations_for(specs)
        singular = as_known_at(s, NOW)
        for st, var, lo, hi in specs:
            assert [o.id for o in batched[(st, var, lo, hi)]] == [
                o.id for o in await singular.observations(st, var, since=lo, until=hi)
            ], (st, var)
        assert len(batched[(ST_A, "stage", NOW - timedelta(hours=6), NOW)]) == 7  # 0..6 h inclusive
        assert [o.value for o in batched[(ST_A, "flow", NOW, NOW)]] == [900.0]  # not the unknown 42.0
        assert [o.value for o in batched[(ST_B, "stage", NOW - timedelta(hours=6), NOW)]] == [7.0]


async def test_a_window_closed_early_is_not_reopened_by_the_memo(sessions) -> None:
    """A read bounded ABOVE — `assess_point` asks for one instant of the secondary variable —
    must not later stand in for a read that runs up to the knowledge time.

    Same failure as widening the lower bound, at the other end: the trend window would come back
    holding only what a single-instant read had already fetched.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([_obs(art.id, valid_time=NOW - timedelta(hours=h), value=float(h)) for h in (0, 2, 4)])
        await s.flush()

        k = as_known_at(s, NOW)
        closed = await k.observations(ST_A, "stage", since=NOW - timedelta(hours=6), until=NOW - timedelta(hours=3))
        assert [o.value for o in closed] == [4.0]
        reopened = await k.observations(ST_A, "stage", since=NOW - timedelta(hours=6))
        assert [o.value for o in reopened] == [4.0, 2.0, 0.0]


async def test_a_narrowed_window_equals_the_narrow_statement(sessions) -> None:
    """A window read out of a wider one already in the memo must equal what the narrow statement
    returns — not the wider rows, and not a re-query.

    This is what collapses `assess_point`'s six-hour trend read into the fourteen-day read it
    sits inside, and it is the one place a memo could quietly answer a question nobody asked.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([
            _obs(art.id, station_id=ST_A, valid_time=NOW - timedelta(hours=h), value=float(h))
            for h in (0, 1, 5, 7, 30, 200)
        ])
        await s.flush()

        wide = as_known_at(s, NOW)
        await wide.observations(ST_A, "stage", since=NOW - timedelta(days=14))  # fills the memo
        narrowed = await wide.observations(ST_A, "stage", since=NOW - timedelta(hours=6))
        direct = await as_known_at(s, NOW).observations(ST_A, "stage", since=NOW - timedelta(hours=6))
        assert [o.id for o in narrowed] == [o.id for o in direct]
        assert [o.value for o in narrowed] == [5.0, 1.0, 0.0]


async def test_a_wider_window_is_not_answered_out_of_a_narrower_one(sessions) -> None:
    """The direction that matters. Narrowing is safe because the rows are already in hand;
    WIDENING is not, and a containment test that let it through would drop rows silently — the
    fourteen-day read would come back holding only the six hours somebody happened to ask for
    first, and the latest observation would be whatever was inside that.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([_obs(art.id, valid_time=NOW - timedelta(hours=h), value=float(h)) for h in (1, 5, 30, 200)])
        await s.flush()

        k = as_known_at(s, NOW)
        assert len(await k.observations(ST_A, "stage", since=NOW - timedelta(hours=6))) == 2
        widened = await k.observations(ST_A, "stage", since=NOW - timedelta(days=14))
        assert [o.value for o in widened] == [200.0, 30.0, 5.0, 1.0]
        assert (await k.latest_observation(ST_A, "stage")).value == 1.0


# --- derived features -------------------------------------------------------------------


async def test_derived_features_batched_equal_singular(sessions) -> None:
    """Two features under two methods, three scopes, several recomputations, one row after T."""
    async with sessions() as s:
        s.add_all([
            _feature(scope_id="basin:skagit", value=1.0),
            _feature(scope_id="basin:skagit", value=2.0, available_at=NOW + timedelta(minutes=1)),  # recomputed
            _feature(scope_id="basin:nooksack", value=3.0),
            _feature(scope_id="basin:skagit", feature="snotel_precip_14d_percent_of_median",
                     method_id="method:snotel-precip-14d-context@1.0.0", value=4.0),
            # Same feature, a DIFFERENT method: must not be returned under the spec's method.
            _feature(scope_id="basin:skagit", method_id="method:other@9.9.9", value=99.0),
            _feature(scope_id="basin:skagit", value=88.0, available_at=LATER + timedelta(hours=1)),
        ])
        await s.flush()

        specs = [
            ("basin_swe_percent_of_median", "method:snotel-basin-swe-context@1.0.0", None),
            ("snotel_precip_14d_percent_of_median", "method:snotel-precip-14d-context@1.0.0", None),
        ]
        scopes = ["basin:skagit", "basin:nooksack", "basin:cedar"]
        batched = await as_known_at(s, LATER).derived_features_for(specs, scopes)
        singular = as_known_at(s, LATER)
        for feature, method, window in specs:
            for scope in scopes:
                assert [r.id for r in batched[(feature, scope)]] == [
                    r.id for r in await singular.derived_features(feature, scope, method_id=method, window=window)
                ], (feature, scope)
        assert [r.value for r in batched[("basin_swe_percent_of_median", "basin:skagit")]] == [1.0, 2.0]
        assert batched[("basin_swe_percent_of_median", "basin:cedar")] == []

        latest = await as_known_at(s, LATER).latest_derived_features(specs, scopes)
        one = as_known_at(s, LATER)
        assert latest[("basin_swe_percent_of_median", "basin:skagit")].value == 2.0
        assert latest[("basin_swe_percent_of_median", "basin:skagit")].id == (
            await one.latest_derived_feature("basin_swe_percent_of_median", "basin:skagit", method_id=specs[0][1])
        ).id


async def test_window_is_part_of_a_features_identity_in_a_batch(sessions) -> None:
    """A spec's `window` filters exactly as the singular reader's does — `None` is "do not
    filter", never "match NULL"."""
    async with sessions() as s:
        s.add_all([
            _feature(feature="basin_qpf_72h_pointwise_p50", method_id="method:basin-qpf@1.0.0", window="72h", value=1.0),
            _feature(feature="basin_qpf_72h_pointwise_p50", method_id="method:basin-qpf@1.0.0", window="24h", value=2.0),
        ])
        await s.flush()
        k = as_known_at(s, NOW)
        windowed = await k.derived_features_for([("basin_qpf_72h_pointwise_p50", "method:basin-qpf@1.0.0", "72h")], ["basin:skagit"])
        assert [r.value for r in windowed[("basin_qpf_72h_pointwise_p50", "basin:skagit")]] == [1.0]
        unfiltered = await as_known_at(s, NOW).derived_features_for(
            [("basin_qpf_72h_pointwise_p50", "method:basin-qpf@1.0.0", None)], ["basin:skagit"]
        )
        assert sorted(r.value for r in unfiltered[("basin_qpf_72h_pointwise_p50", "basin:skagit")]) == [1.0, 2.0]


async def test_a_narrower_lookback_reads_out_of_a_wider_batch(sessions) -> None:
    """`[T − 48 h, T]` inside `[T − 7 d, T]` must equal the 48-hour statement.

    The susceptibility surface batches its family at the wider of two lookbacks and then reads
    at its own; if narrowing were approximate, a row two days stale would present as current.
    """
    async with sessions() as s:
        s.add_all([
            _feature(scope_id="basin:skagit", value=1.0, valid_time=NOW - timedelta(days=5)),
            _feature(scope_id="basin:skagit", value=2.0, valid_time=NOW - timedelta(hours=70)),
        ])
        await s.flush()
        spec = [("basin_swe_percent_of_median", "method:snotel-basin-swe-context@1.0.0", None)]

        wide = as_known_at(s, NOW)
        await wide.latest_derived_features(spec, ["basin:skagit"], lookback=timedelta(days=7))
        narrowed = await wide.latest_derived_feature(
            "basin_swe_percent_of_median", "basin:skagit", method_id=spec[0][1], lookback=timedelta(hours=48)
        )
        direct = await as_known_at(s, NOW).latest_derived_feature(
            "basin_swe_percent_of_median", "basin:skagit", method_id=spec[0][1], lookback=timedelta(hours=48)
        )
        assert narrowed is None and direct is None  # both rows are older than 48 h


async def test_a_batch_refuses_two_shapes_for_one_feature(sessions) -> None:
    """Results are grouped by `(feature, scope)`, so two methods computing one feature could not
    be told apart. Refused loudly rather than silently returning one of them."""
    async with sessions() as s:
        with pytest.raises(ValueError, match="two shapes"):
            await as_known_at(s, NOW).derived_features_for(
                [("f", "method:a@1", None), ("f", "method:b@1", None)], ["basin:skagit"]
            )


# --- the memo itself --------------------------------------------------------------------


async def test_the_memo_does_not_survive_a_change_of_knowledge_time(sessions) -> None:
    """`as_of` is not in any memo key because it cannot vary within one `Knowledge`. That is only
    safe if a different knowledge time is a different object — checked here rather than assumed,
    because it is the whole basis on which memoising a knowledge-filtered read is legitimate."""
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([
            _obs(art.id, valid_time=NOW - timedelta(hours=1), value=1.0),
            _obs(art.id, valid_time=NOW + timedelta(hours=1), value=2.0, available_at=NOW + timedelta(hours=1)),
        ])
        await s.flush()

        before = as_known_at(s, NOW)
        after = as_known_at(s, NOW + timedelta(hours=2))
        assert (await before.latest_observation(ST_A, "stage")).value == 1.0
        assert (await after.latest_observation(ST_A, "stage")).value == 2.0
        # ... and asking the earlier one again still gets the earlier answer.
        assert (await before.latest_observation(ST_A, "stage")).value == 1.0
        assert before._memo is not after._memo

        # `dataclasses.replace` is the one way a memo could follow an object onto a new clock.
        # It cannot: the field is `init=False`, so a replaced Knowledge starts empty.
        moved = replace(before, as_of=NOW + timedelta(hours=2))
        assert moved._memo == {}
        assert (await moved.latest_observation(ST_A, "stage")).value == 2.0


async def test_a_caller_cannot_corrupt_what_the_next_caller_reads(sessions) -> None:
    """Readers hand back fresh containers. A caller that sorts, clears or pops what it got must
    not change the answer the next caller gets out of the same memo entry."""
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([_obs(art.id, valid_time=NOW - timedelta(hours=h), value=float(h)) for h in (0, 1, 2)])
        s.add_all([_threshold(art.id, category=c, value=float(i)) for i, c in enumerate(("action", "minor"))])
        s.add_all([_feature(scope_id="basin:skagit", value=1.0)])
        run = _run(art.id, fp_id=FP_A, issued_at=NOW)
        s.add(run)
        await s.flush()
        s.add(ForecastValue(run_id=run.id, valid_time=NOW, stage=1.0, flow=None))
        await s.flush()

        k = as_known_at(s, NOW)
        for read in (
            lambda: k.observations(ST_A, "stage", since=NOW - timedelta(days=1)),
            lambda: k.derived_features("basin_swe_percent_of_median", "basin:skagit"),
            lambda: k.forecast_values(run.id),
        ):
            first = await read()
            assert first, read
            first.clear()
            assert await read(), f"{read} returned the container a previous caller emptied"

        first_thresholds = await k.thresholds(FP_A)
        first_thresholds.clear()
        assert await k.thresholds(FP_A)

        first_products = await k.products()
        first_products.clear()
        assert await k.products()

        first_basins = await k.basins()
        first_basins.clear()
        assert await k.basins()


async def test_the_memo_answers_the_singular_reader_after_a_batch(sessions) -> None:
    """The mechanism the prefetches rely on: after a set-based read, the per-scope reader returns
    the same rows without a statement of its own. Asserted on the *answer*; the query COUNT is
    pinned separately in tests/perf/test_query_budget.py."""
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_NWPS_THRESHOLDS)
        s.add_all([_threshold(art.id, fp_id=FP_A, category="action"), _threshold(art.id, fp_id=FP_B, category="action", value=5.0)])
        await s.flush()

        k = as_known_at(s, NOW)
        batched = await k.thresholds_for([FP_A, FP_B])
        assert {fp: await k.thresholds(fp) for fp in (FP_A, FP_B)} == batched


async def test_seeded_reference_reads_do_not_change_what_is_returned(sessions) -> None:
    """`basins()` and `forecast_points()` seed the by-id memos they imply. A seeded entry must be
    the row the singular reader would have fetched, or a later `basin(id)` answers from a list
    that was never meant to define it."""
    async with sessions() as s:
        k = as_known_at(s, NOW)
        listed = {b.id: b for b in await k.basins()}
        assert listed
        for basin_id, basin in listed.items():
            assert (await k.basin(basin_id)) is basin
        points = await k.forecast_points()
        for fp in points:
            assert (await k.forecast_point_by_lid(fp.lid)) is fp
        assert isinstance(listed[next(iter(listed))], Basin)
        assert isinstance(points[0], ForecastPoint)
        assert isinstance(await k.station(ST_A), Station)


# --- what the batched readers' ORDER BY decides ------------------------------------------
#
# Everything below was written after a mutation round on 2026-08-26 (docs/research/
# pg-migration-verification-2026-08-24.md, "Phase B read path"). Deleting `available_at <=
# as_of` from any of the five batched readers already failed a test here. Deleting the *rest*
# of what their ORDER BY decides did not: `revision_seq` could come out of `observations_for`,
# `available_at` out of `derived_features_for`, and each spec's own window out of the way
# `observations_for` partitions its union, and all 331 tests still passed.
#
# Those are the same class of rule as the knowledge filter — which row of several a reader is
# allowed to call the answer — so they get the same treatment. Each test below is written to
# fail on exactly one such deletion, and each one pins the ABSOLUTE expected row as well as
# batched-equals-singular: an equality alone would be satisfied by both readers being wrong.


async def test_observations_for_breaks_a_revision_tie_by_revision_not_by_row_id(sessions) -> None:
    """`revision_seq` has to stay ahead of `id` in the batched reader's ORDER BY.

    Both readers take the LAST row per valid_time, so the ORDER BY *is* the revision rule. `id`
    normally agrees with `revision_seq` — a later write gets a later id — which is exactly why
    this builds the case where it does not: the higher revision written first, the lower one
    arriving afterwards, which is what a backfill pass over a corrected instant looks like.
    Ordering on `(valid_time, id)` picks revision 0 and says nothing about it.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add(_obs(art.id, valid_time=NOW, value=2.0, revision_seq=1))
        await s.flush()  # the CORRECTED value lands first, so it holds the LOWER id
        s.add(_obs(art.id, valid_time=NOW, value=1.0, revision_seq=0))
        await s.flush()

        spec = (ST_A, "stage", NOW, NOW)
        batched = await as_known_at(s, NOW).observations_for([spec])
        singular = await as_known_at(s, NOW).observations(ST_A, "stage", since=NOW, until=NOW)
        assert [o.id for o in batched[spec]] == [o.id for o in singular]
        assert [o.value for o in batched[spec]] == [2.0]  # revision 1, not the later-written revision 0
        assert (await as_known_at(s, NOW).latest_observation(ST_A, "stage")).value == 2.0


async def test_observations_for_gives_each_spec_its_own_window(sessions) -> None:
    """Two specs on the SAME station and variable, over different windows.

    One statement covers both — its valid_time bounds are the union of every spec's — so each
    spec has to be cut back out of that union by its own predicate. Without that step the
    single-instant read comes back holding the whole six-hour window, and it is memoised under
    the narrow key, so every later narrowing of it is wrong too. `assess_point` asks for exactly
    this pair (one instant of the secondary variable, six hours of the primary) and reaches it
    with the same station whenever two points share a gauge.
    """
    async with sessions() as s:
        art = await _artifact(s, PRODUCT_USGS_IV)
        s.add_all([_obs(art.id, valid_time=NOW - timedelta(hours=h), value=float(h)) for h in range(0, 8)])
        await s.flush()

        wide = (ST_A, "stage", NOW - timedelta(hours=6), NOW)
        instant = (ST_A, "stage", NOW, NOW)
        batched = await as_known_at(s, NOW).observations_for([wide, instant])
        for spec in (wide, instant):
            expected = await as_known_at(s, NOW).observations(spec[0], spec[1], since=spec[2], until=spec[3])
            assert [o.id for o in batched[spec]] == [o.id for o in expected], spec
        assert [o.value for o in batched[instant]] == [0.0]  # the instant, not the window it shared a statement with
        assert [o.value for o in batched[wide]] == [6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.0]


async def test_derived_features_for_orders_recomputations_by_when_they_became_known(sessions) -> None:
    """`available_at` has to stay ahead of `id` in the batched reader's ORDER BY.

    `latest_per_valid_time` keeps the LAST row for a valid_time, and "last" means last KNOWN —
    the recomputation with the greatest `available_at`, which is the same rule `observations`
    applies to revisions. Row id is insertion order, and insertion order is not knowledge order:
    a cycle whose values were computed later can be written first. Ordering on `(valid_time,
    id)` hands back the earlier-known row and no body on the read path moves.
    """
    feature, method = "basin_swe_percent_of_median", "method:snotel-basin-swe-context@1.0.0"
    async with sessions() as s:
        s.add(_feature(value=1.0, issued_at=NOW - timedelta(hours=2), available_at=NOW))
        await s.flush()  # known LAST, written FIRST: the lower id is the one that must win
        s.add(_feature(value=2.0, issued_at=NOW - timedelta(hours=1), available_at=NOW - timedelta(minutes=30)))
        await s.flush()

        cell = (feature, "basin:skagit")
        batched = await as_known_at(s, NOW).derived_features_for([(feature, method, None)], ["basin:skagit"])
        singular = await as_known_at(s, NOW).derived_features(feature, "basin:skagit", method_id=method)
        assert [r.id for r in batched[cell]] == [r.id for r in singular]

        latest = await as_known_at(s, NOW).latest_derived_features([(feature, method, None)], ["basin:skagit"])
        alone = await as_known_at(s, NOW).latest_derived_feature(feature, "basin:skagit", method_id=method)
        assert latest[cell].value == 1.0, "the last-KNOWN recomputation, not the last-written row"
        assert alone.id == latest[cell].id


async def test_an_empty_scope_id_answers_as_it_did(sessions) -> None:
    """A reader handed an empty scope id answers "nothing known", as its single-scope statement
    did — it does not raise.

    Four readers now delegate to their own set-based form for one scope, and every set-based
    reader drops a falsy scope id before building its `IN (…)`, which leaves no memo entry for
    the singular reader to read back. Indexing that memo turned four `None`/empty answers into
    `KeyError`, i.e. a 500 where the endpoint used to 404 (found 2026-08-26). Nothing on
    `/viz/basins` passes an empty id today; this is here so nothing has to.
    """
    async with sessions() as s:
        k = as_known_at(s, NOW)
        assert await k.forecast_point_by_lid("") is None
        assert await k.thresholds("") == {}
        assert await k.latest_forecast_run("") is None
        assert await k.forecast_values(None) == []
        assert await k.station("") is None
