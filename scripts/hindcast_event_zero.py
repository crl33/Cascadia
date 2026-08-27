"""Event Zero old-vs-new A/B (brief §13), driven by the reusable harness (brief §21).

Runs `cascade_hydrology.hindcast` over the December 2025 Western Washington floods for every
seeded basin, under both `method:susceptibility-index@0.1.0` + `method:rate-of-rise@1.0.0` (the
surface as it shipped until 2026-08-26) and `@0.2.0` + `@2.0.0` (the Tier 0 correction), and
writes the evidence behind `docs/research/event-zero-ab-2026-08-27.md`.

This script is the PROVIDER-SPECIFIC half of the harness and lives outside the packages for
that reason: `cascade_hydrology` may not import a provider adapter (import-linter contract), and
reconstructing a USGS daily-mean ranking needs `cascade_providers_usgs`. The harness owns the
shape of a replay; this owns what Event Zero's rows are made of.

The two knowledge times (brief §20), which this script implements rather than assumes
-------------------------------------------------------------------------------------
`--mode knowledge-time` reads the archive untouched: `available_at <= T`. Every December-2025
row in it was backfilled in 2026, so a replay at 2025-12-06 correctly finds nothing, and the
run records that as the result rather than treating it as a failure. Run it — it is the control
that proves the projection below is doing something, and it is the honest answer to "what would
this platform have shown".

`--mode retrospective` first REWRITES the visibility clocks of a scratch database so that each
row becomes visible at the instant its own evidence existed, then runs the identical code path
through the identical `as_known_at`. The rewrite is the projection, every rule of it is recorded
in the output, and `Projection.disclosure()` travels with every number. It is destructive and
refuses to run against a database whose name does not look like a scratch database.

Usage, in order (S=scripts/hindcast_event_zero.py):
    python $S reference   --db-url ...   # rebuild the pre-event ladders + record context
    python $S reconstruct --db-url ...   # rank the December daily means as the job would have
    python $S run  --db-url ... --mode knowledge-time --out kt.json   # the §20 control: nothing
    python $S project     --db-url ...   # move the visibility clocks (destructive, scratch only)
    python $S run  --db-url ... --mode retrospective  --out ab.json   # the A/B
    python $S unproject   --db-url ...   # put the archive clocks back
    python $S vintage     --db-url ... --out vintage.json   # what the ladder vintage is worth
    python $S base-rate   --db-url ... --out base.json      # how often each rule ever fires
    python $S fixture --db-url ... --run ab.json --out tests/fixtures/hindcast/event_zero_ab.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
for _pkg in ("contracts", "core", "geo", "hydrology", "providers/usgs"):
    sys.path.insert(0, str(ROOT / "packages" / _pkg / "src"))

import sqlalchemy as sa  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from cascade_contracts import FloodCategory  # noqa: E402
from cascade_hydrology.susceptibility import BAND_TOP  # noqa: E402
from cascade_core.db import make_engine, make_session_factory  # noqa: E402
from cascade_core.knowledge import as_known_at  # noqa: E402
from cascade_core.models import Basin, DerivedFeature, Station  # noqa: E402
from cascade_core.objectstore import store_from_settings  # noqa: E402
from cascade_core.registry import PRODUCT_USGS_OGC_DAILY  # noqa: E402
from cascade_core.settings import Settings  # noqa: E402
from cascade_core.timeutils import utcnow  # noqa: E402
from cascade_hydrology import hindcast, susceptibility  # noqa: E402
from cascade_providers_usgs.climatology import (  # noqa: E402
    METHOD_ID as CLIMATOLOGY_METHOD_ID,
)
from cascade_providers_usgs.climatology import (  # noqa: E402
    PUBLISHED_METHOD_ID,
    build_doy_climatology,
    build_record_context,
    daily_mean_valid_time,
    doy_key,
    from_values_json,
    p50_disagreement,
    percentile_of,
)
from cascade_providers_usgs.stats_jobs import (  # noqa: E402
    CLIMATOLOGY_FEATURE,
    DISAGREEMENT_FRACTION,
    PERCENTILE_FEATURE,
    PERCENTILE_METHOD_ID,
    GROWTH_REFERENCE_FEATURE,
    RECORD_CONTEXT_FEATURE,
    _climatology_row,
    _growth_reference_row,
    _record_context_row,
)
from cascade_providers_usgs.stats_parser import parse_daily_csv  # noqa: E402

# =============================================================================================
# The event, its clocks and its outcome
# =============================================================================================
#
# EVERY constant in this block predates the run and none of it is a tuning parameter. The
# evaluation grid is the brief's list widened to a regular cadence; the outcomes are read from
# `docs/EVENT_ZERO.md` §3 and are never consulted while a signal is computed.

#: The event window the A/B reports over.
EVENT_START = date(2025, 12, 1)
EVENT_END = date(2025, 12, 14)

#: The quiet control window: the eleven days immediately before the event, same gauges, same
#: season, same instruments. Half the governing question is "did it stay quiet when nothing was
#: happening", and that half cannot be answered without one.
CONTROL_START = date(2025, 11, 21)
#: Ends the day before the event window opens, so no instant is evaluated as both a control and
#: an event day. An overlap would double-count a knowledge time and let a control firing and an
#: escalation be the same row.
CONTROL_END = date(2025, 11, 30)

#: Reconstruct the ranked daily means from here, so the 48 h state change at the first control
#: evaluation has both its endpoints.
RECONSTRUCT_START = date(2025, 11, 1)
RECONSTRUCT_END = date(2025, 12, 22)

#: The day the pre-event reference distribution is built up to. The end of October, not the
#: end of November, so the ladder is visible for the whole CONTROL window too and one reference
#: covers every evaluation in the run. A ladder built that morning is what the annual job would
#: have produced had it run on 2025-11-01, and it removes both the valid_time anachronism and
#: register X8's claim D — no WY2026 day is in it.
PRE_EVENT_CUTOFF = date(2025, 10, 31)

#: The instant every retrospective reference row is made visible from. Before the first
#: evaluation, because a reference distribution is not an observation with a moment of arrival —
#: it is the anachronism the projection declares.
PROJECTION_EPOCH = datetime(2025, 1, 1, tzinfo=UTC)

#: Sub-daily evaluation hours. 12:00Z and 18:00Z see the daily mean labelled "yesterday";
#: 00:00Z and 06:00Z still see the day before that, because a station-local daily mean is only
#: complete at local midnight. A daily-only grid hides exactly that half-day of lag.
EVENT_HOURS = (0, 6, 12, 18)
CONTROL_HOURS = (12,)

#: `docs/EVENT_ZERO.md` §3, verbatim. Recorded for the report; read by nothing that computes.
OUTCOMES = (
    hindcast.BasinOutcome(
        basin_id="basin:skagit", crest_valid_time=datetime(2025, 12, 12, 8, 15, tzinfo=UTC),
        crest_value=133000.0, crest_unit="cfs", category_reached=FloodCategory.MAJOR,
        record_status="record stage 37.73 ft at Mount Vernon; previous 37.37 ft 1990-11-25",
        source="docs/EVENT_ZERO.md §3 (MVEW1)",
    ),
    hindcast.BasinOutcome(
        basin_id="basin:snohomish-snoqualmie", crest_valid_time=datetime(2025, 12, 11, 12, 0, tzinfo=UTC),
        crest_value=89700.0, crest_unit="cfs", category_reached=FloodCategory.MAJOR,
        record_status="2nd by stage at Carnation; Snohomish at Snohomish set a record",
        source="docs/EVENT_ZERO.md §3 (CRNW1, SNAW1)",
    ),
    hindcast.BasinOutcome(
        basin_id="basin:cedar", crest_valid_time=datetime(2025, 12, 11, 23, 0, tzinfo=UTC),
        crest_value=12400.0, crest_unit="cfs", category_reached=FloodCategory.MAJOR,
        record_status="record stage and flow at Renton; previous 17.13 ft / 10,600 cfs 1990-11-24",
        source="docs/EVENT_ZERO.md §3 (RNTW1)",
    ),
    hindcast.BasinOutcome(
        basin_id="basin:nooksack", crest_valid_time=datetime(2025, 12, 12, 6, 15, tzinfo=UTC),
        crest_value=44300.0, crest_unit="cfs", category_reached=FloodCategory.MODERATE,
        record_status="not a record at Ferndale; N Cedarville reached major",
        source="docs/EVENT_ZERO.md §3 (NKSW1, NRKW1)",
    ),
    hindcast.BasinOutcome(
        basin_id="basin:green-duwamish", crest_valid_time=datetime(2025, 12, 13, 15, 15, tzinfo=UTC),
        crest_value=12100.0, crest_unit="cfs", category_reached=FloodCategory.MODERATE,
        record_status="2nd-highest stage at Auburn; regulated by Howard Hanson",
        source="docs/EVENT_ZERO.md §3 (AUBW1)",
    ),
    hindcast.BasinOutcome(
        basin_id="basin:puyallup-white", crest_valid_time=datetime(2025, 12, 15, 17, 15, tzinfo=UTC),
        crest_value=12000.0, crest_unit="cfs", category_reached=FloodCategory.MAJOR,
        record_status="record at White R St; dam-release driven, crest on 12-15 outside the A/B window",
        source="docs/EVENT_ZERO.md §3 (WRAW1)",
    ),
)


def _grid(start: date, end: date, hours: tuple[int, ...]) -> tuple[datetime, ...]:
    out: list[datetime] = []
    day = start
    while day <= end:
        out.extend(datetime(day.year, day.month, day.day, h, tzinfo=UTC) for h in hours)
        day += timedelta(days=1)
    return tuple(out)


def event_zero(basin_ids: tuple[str, ...]) -> hindcast.HindcastEvent:
    return hindcast.HindcastEvent(
        id="event-zero-2025-12",
        label="December 2025 Western Washington floods",
        basin_ids=basin_ids,
        evaluation_times=_grid(EVENT_START, EVENT_END, EVENT_HOURS),
        control_times=_grid(CONTROL_START, CONTROL_END, CONTROL_HOURS),
        outcomes=OUTCOMES,
        source="docs/EVENT_ZERO.md",
    )


# =============================================================================================
# The projection (brief §20) — stated as data, applied as SQL, recorded in the output
# =============================================================================================

PROJECTION = hindcast.Projection(
    name="event-zero-retrospective",
    mode=hindcast.ReplayMode.RETROSPECTIVE,
    note=(
        "Applied to a scratch database only. Every rule below moves a VISIBILITY clock; not one "
        "of them changes a value, a valid_time or an issued_at, so no number in the run is "
        "altered by the projection — only the instant at which the replay is allowed to see it."
    ),
    rules=(
        hindcast.ProjectionRule(
            row_family="observation (USGS instantaneous stage and flow)",
            visibility_clock="valid_time",
            rule="available_at := valid_time",
            optimism=(
                "Optimistic by the USGS publication latency, of the order of 5-15 minutes for the "
                "instantaneous service. The 6 h trend window therefore sees its own trailing edge "
                "slightly sooner than any real retrieval could have delivered it."
            ),
        ),
        hindcast.ProjectionRule(
            row_family="derived_feature streamflow_doy_percentile (reconstructed daily-mean ranking)",
            visibility_clock="valid_time (station-local midnight ending the day)",
            rule="available_at := valid_time",
            optimism=(
                "Optimistic twice. First by the USGS daily-value publication lag, which is hours "
                "to a day. Second and more seriously: these daily means carry approval_status "
                "'Approved' because they were fetched in 2026: in December 2025 the same values "
                "would have been PROVISIONAL and some of them numerically different. A replay "
                "using approved values is reading a cleaner record than the one that existed."
            ),
        ),
        hindcast.ProjectionRule(
            row_family="derived_feature streamflow_doy_climatology and streamflow_record_context",
            visibility_clock="available_at := valid_time (REWRITTEN; valid_time itself unmodified)",
            rule=(
                "REBUILT, NOT PROJECTED — but the visibility clock IS rewritten, and the previous "
                "wording of this rule hid that. The reference a replay reads is rebuilt by the "
                "shipped builders from the same archived record truncated at "
                f"{PRE_EVENT_CUTOFF.isoformat()}. The builders stamp `available_at = max(valid_time, "
                "retrieved_at)`, which is the 2026 fetch time, and `build_reference` then sets it "
                "to `valid_time` — a movement of roughly 300 DAYS. The argument for that is the "
                "reconstruction itself: the row is what the annual job WOULD have written on "
                "2025-11-01, so it is stamped with the clock that job would have used. The "
                "2026-vintage rows stay in the database and stay invisible, because their "
                "valid_time is in the replay's future and `valid_time <= as_of` is not a rule "
                "this script is willing to bend."
            ),
            optimism=(
                "ABOUT 300 DAYS on the visibility clock — the largest single clock movement in "
                "this run, and it was previously disclosed here as 'None on the clock', which was "
                "false. What is true is narrower and is the actual argument: the rewrite does not "
                "make a row visible EARLIER THAN THE ROW IT RECONSTRUCTS would have been, because "
                "the annual job would have written it on 2025-11-01. The residual nobody can "
                "remove is that this platform did not exist in November 2025, so the ladder was "
                "RECONSTRUCTABLE then, never KNOWN then — which is exactly why every figure built "
                "on it is labelled RETROSPECTIVE. Register X8 claim D is REMOVED rather than "
                "declared: no "
                "WY2026 day is in the rebuilt reference, so the event is not ranked against a "
                "distribution it helped make. What remains is that the rebuild happened in 2026: "
                "the bytes are the 2026 fetch of the record, so any day whose approval status or "
                "value was revised after December 2025 enters the reference with its revised "
                "value. That is unavoidable without a 2025 vintage of the record, which does not "
                "exist in any archive available here."
            ),
        ),
        hindcast.ProjectionRule(
            row_family="threshold (NWPS official flood categories)",
            visibility_clock="none — made visible from a declared epoch",
            rule=f"effective_from := {PROJECTION_EPOCH.isoformat()}",
            optimism=(
                "NWPS publishes no historical vintage for a threshold set, so whether these were "
                "the categories in force in December 2025 is unverified. `docs/EVENT_ZERO.md` §3 "
                "already makes this same assumption when it derives the categories the event "
                "reached; this run inherits it rather than inventing a second one."
            ),
            anachronism=True,
        ),
        hindcast.ProjectionRule(
            row_family="forecast_run (KSEW FLW/FLS crest statements)",
            visibility_clock="issued_at",
            rule="available_at := issued_at",
            optimism=(
                "The least optimistic rule here, and the only one resting on a genuine historical "
                "clock: issued_at is the AFOS transmission time of the actual product. A replay "
                "sees an official crest statement at the minute it was transmitted."
            ),
        ),
    ),
)

SCRATCH_MARKERS = ("hindcast", "scratch", "tmp", "test")


def _guard_scratch(db_url: str) -> None:
    """Refuse to project onto anything that does not announce itself as a scratch database.

    The projection rewrites visibility clocks in place. Doing that to an archive would destroy
    the one property the archive exists to have.
    """
    name = db_url.rsplit("/", 1)[-1].split("?")[0].lower()
    if not any(m in name for m in SCRATCH_MARKERS):
        raise SystemExit(
            f"refusing to apply a retrospective projection to database {name!r}: the name carries "
            f"none of {SCRATCH_MARKERS}. Create a scratch database and point --db-url at it."
        )


# =============================================================================================
# Reconstruction: the December daily-mean ranking that never existed
# =============================================================================================
#
# `usgs.fetch_daily_percentile` ranks only the LATEST daily mean, once a day, and this platform
# has been running since 2026-08. So there is no stored `streamflow_doy_percentile` row for any
# day of Event Zero, in production or anywhere else — the surface's whole input is missing.
#
# It is reconstructable exactly, because the ladder's own archived source CSV is the period of
# record and contains those days. This function re-runs the SHIPPED ranking (`percentile_of`,
# `doy_key`, `daily_mean_valid_time`, `p50_disagreement`) over them and writes rows in the same
# shape the job writes, linked to the same raw artifact. Nothing is interpolated or invented: a
# day the record does not carry produces no row.


# =============================================================================================
# The pre-event reference distribution — the honest fix for two problems at once
# =============================================================================================
#
# TWO problems, and one build answers both.
#
# 1. A reference row's `valid_time` is the last day of the record it was built from. The stored
#    ladders and record contexts were built on 2026-08-26, so their valid_time is 2026-08-26 and
#    `Knowledge.latest_derived_feature` — which asks for `valid_time <= as_of` — CORRECTLY
#    refuses to hand a December-2025 replay a reference from its own future. Projecting
#    `available_at` does not and must not change that: moving a valid_time would be falsifying
#    content, not adjusting visibility.
# 2. Register X8 claim D: those same records run THROUGH the event, so the level would be ranked
#    against a distribution the event helped make. Measured here (`approval_census`): four of the
#    six gauges carry the whole of approved December 2025, cedar carries 12-01..12-04, and
#    Snoqualmie's approved record stops on 2024-11-14.
#
# Re-running the SHIPPED builders over the same archived record truncated at a cutoff day
# produces exactly the row `usgs.build_climatology` would have written had it run that morning:
# same method id, same code, same bytes, fewer rows. It is not a new method and not a
# recalibration — `build_doy_climatology` and `build_record_context` are called unmodified — and
# it removes the anachronism instead of declaring it.


async def build_reference(
    session: AsyncSession,
    settings: Settings,
    *,
    cutoff: date,
) -> dict[str, Any]:
    """Rebuild each gauge's ladder and record context from the record up to ``cutoff``.

    The rows are written with `valid_time` = the cutoff day's own daily-mean completion instant,
    which is what the annual job would have stamped, so a replay after the cutoff sees them
    exactly as it would have seen the real thing.
    """
    store = store_from_settings(settings)
    out: dict[str, Any] = {"cutoff": cutoff.isoformat(), "gauges": {}}
    for basin, station in await _susceptibility_gauges(session):
        source = await _latest_row(session, scope_id=station.id, method_id=CLIMATOLOGY_METHOD_ID)
        if source is None:
            continue
        raw = (
            await session.execute(
                sa.text("SELECT object_key, fetched_at FROM raw_artifact WHERE id = :i"),
                {"i": source.raw_artifact_id},
            )
        ).first()
        if raw is None:
            continue
        object_key, fetched_at = raw
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        rows = [r for r in parse_daily_csv(store.get(object_key), site=station.external_id) if r.day <= cutoff]
        climatology = build_doy_climatology(rows, site=station.external_id, unit="cfs")
        context = build_record_context(rows, site=station.external_id, unit="cfs")
        if not climatology.ladders:
            out["gauges"][station.id] = {"basin": basin.id, "error": "no approved record before the cutoff"}
            continue
        valid_time, flags = daily_mean_valid_time(cutoff, time_zone=station.time_zone)
        made = 0
        for feature, method_id, row in (
            (CLIMATOLOGY_FEATURE, CLIMATOLOGY_METHOD_ID, _climatology_row(
                climatology, station_id=station.id, valid_time=valid_time, retrieved_at=fetched_at,
                product_id=PRODUCT_USGS_OGC_DAILY, artifact_id=source.raw_artifact_id,
                quality=[*flags, PRE_EVENT_QUALITY_FLAG],
            )),
            (RECORD_CONTEXT_FEATURE, susceptibility.RECORD_CONTEXT_METHOD_ID, _record_context_row(
                context, station_id=station.id, valid_time=valid_time, retrieved_at=fetched_at,
                artifact_id=source.raw_artifact_id, quality=[*flags, PRE_EVENT_QUALITY_FLAG],
            )),
            # The growth reference moved out of the record context on 2026-08-27 and must be
            # rebuilt here too, or the velocity's rank is unavailable for the whole replay — which
            # is exactly the defect the split closed, reappearing in the harness instead of the
            # surface. Same builder, same cutoff, same artifact, same pre-event quality flag.
            (GROWTH_REFERENCE_FEATURE, susceptibility.GROWTH_REFERENCE_METHOD_ID, _growth_reference_row(
                context, station_id=station.id, valid_time=valid_time, retrieved_at=fetched_at,
                artifact_id=source.raw_artifact_id, quality=[*flags, PRE_EVENT_QUALITY_FLAG],
            )),
        ):
            found = await session.execute(
                sa.select(DerivedFeature.id).where(
                    DerivedFeature.method_id == method_id,
                    DerivedFeature.feature == feature,
                    DerivedFeature.scope_id == station.id,
                    DerivedFeature.valid_time == valid_time,
                )
            )
            if found.first() is not None:
                continue
            # Visible from its own valid_time: the annual job would have written it that morning.
            row.available_at = valid_time
            session.add(row)
            made += 1
        out["gauges"][station.id] = {
            "basin": basin.id,
            "site": station.external_id,
            "rows": made,
            "valid_time": valid_time.isoformat(),
            "period_of_record": [climatology.begin_year, climatology.end_year],
            "days_used": len(rows),
            "ladder_keys": len(climatology.ladders),
            "context_keys": len(context.keys),
        }
    await session.flush()
    return out


#: Stamped on every pre-event reference row so it can never be mistaken for a job's output.
PRE_EVENT_QUALITY_FLAG = "pre_event_reference_rebuild"


@dataclass
class ReconstructionReport:
    rows_written: int
    gauges: dict[str, dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {"rows_written": self.rows_written, "gauges": self.gauges}


def _numeric(record: Any) -> float | None:
    """The daily mean as a number, or None.

    PERMISSIVE about approval status, and that is a deliberate match to the deployed job:
    `run_fetch_daily_percentile` ranks whatever `fetch_latest_daily` returns and records the
    approval status in `quality`, so a provisional value ranked inside an approved-built ladder
    is the SHIPPED behaviour, not an artefact of this reconstruction. It is also the more
    faithful replay — in December 2025 every one of these values was provisional.

    Which days are approved and which are not is measured and reported per gauge
    (:func:`approval_census`) instead of being silently decided here, because the answer turns
    out to differ sharply between the six seeded gauges and it bears directly on register X8.
    """
    if record is None or record.raw_value is None:
        return None
    try:
        value = float(record.raw_value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def approval_census(by_day: dict[date, Any], *, start: date, end: date) -> dict[str, Any]:
    """How much of `[start, end]` this gauge's published daily record has APPROVED, and to when.

    Register X8 asks which record a ladder should be built from; claim D asserts that seeded
    gauges carry approved WY2026 data inside the December ranking window. This counts it, per
    gauge, from the same archived CSV the ladder was built from — so the assertion becomes a
    measurement, and a reader can see that the answer is not uniform across the six.
    """
    days = [d for d in by_day if start <= d <= end]
    approved = [d for d in days if by_day[d].approval_status == "Approved"]
    all_approved = [d for d, r in by_day.items() if r.approval_status == "Approved"]
    return {
        "window": [start.isoformat(), end.isoformat()],
        "days_present": len(days),
        "days_approved": len(approved),
        "last_approved_day_in_record": max(all_approved).isoformat() if all_approved else None,
    }


async def _susceptibility_gauges(session: AsyncSession) -> list[tuple[Basin, Station]]:
    basins = (await session.execute(sa.select(Basin).order_by(Basin.id))).scalars().all()
    out = []
    for basin in basins:
        if not basin.susceptibility_gauge_id:
            continue
        station = await session.get(Station, basin.susceptibility_gauge_id)
        if station is not None:
            out.append((basin, station))
    return out


async def _latest_row(
    session: AsyncSession, *, scope_id: str, method_id: str, valid_until: datetime | None = None
) -> DerivedFeature | None:
    """The newest row of a method for a scope, optionally the newest one valid by an instant.

    ``valid_until`` matters once a pre-event reference exists beside the 2026 one: the
    reconstruction must rank each day in the ladder a replay at that day would actually read,
    which is `Knowledge`'s own `valid_time <= as_of` rule restated for a setup step that runs
    outside a `Knowledge`.
    """
    stmt = sa.select(DerivedFeature).where(
        DerivedFeature.scope_id == scope_id, DerivedFeature.method_id == method_id
    )
    if valid_until is not None:
        stmt = stmt.where(DerivedFeature.valid_time <= valid_until)
    return (await session.execute(stmt.order_by(DerivedFeature.valid_time.desc(), DerivedFeature.id.desc()).limit(1))).scalars().first()


async def reconstruct(
    session: AsyncSession,
    settings: Settings,
    *,
    start: date,
    end: date,
) -> ReconstructionReport:
    """Rank every daily mean in `[start, end]` in the ladder a replay AT THAT DAY would read.

    Which ladder that is matters once a pre-event reference exists beside the 2026 one, so the
    ladder is resolved per day under `valid_time <= that day's daily-mean instant` — `Knowledge`'s
    own rule, restated for a setup step that runs outside a `Knowledge`. Ranking December in a
    ladder built in August 2026 and then replaying it as if the platform had held that ladder in
    December would be exactly the confusion this whole script exists to prevent.
    """
    store = store_from_settings(settings)
    written = 0
    gauges: dict[str, dict[str, Any]] = {}
    for basin, station in await _susceptibility_gauges(session):
        row = await _latest_row(session, scope_id=station.id, method_id=CLIMATOLOGY_METHOD_ID)
        if row is None:
            gauges[station.id] = {"basin": basin.id, "error": "no stored climatology ladder"}
            continue
        published_row = await _latest_row(session, scope_id=station.id, method_id=PUBLISHED_METHOD_ID)
        published = (
            from_values_json(published_row.values_json or {}, method_id=PUBLISHED_METHOD_ID)
            if published_row is not None
            else None
        )
        raw = await session.execute(
            sa.text("SELECT object_key, fetched_at FROM raw_artifact WHERE id = :i"),
            {"i": row.raw_artifact_id},
        )
        got = raw.first()
        if got is None:
            gauges[station.id] = {"basin": basin.id, "error": "ladder row has no archived source CSV"}
            continue
        object_key, fetched_at = got
        # The raw SELECT bypasses the ORM's aware-datetime type, and every timestamp in this
        # project is aware (`cascade_core.models`). Restore that here rather than at the INSERT.
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        # Same filter the ladder and the record context apply — approved, parseable, finite,
        # last value per day wins — so a reconstructed ranking cannot be a statement about a
        # different sample from the ladder it is ranked in.
        by_day = {r.day: r for r in parse_daily_csv(store.get(object_key), site=station.external_id)}
        made = 0
        days: list[dict[str, Any]] = []
        day = start
        while day <= end:
            record = by_day.get(day)
            observed = _numeric(record)
            if observed is None:
                day += timedelta(days=1)
                continue
            key = doy_key(day)
            valid_time, flags = daily_mean_valid_time(day, time_zone=station.time_zone)
            ladder_row = await _latest_row(
                session, scope_id=station.id, method_id=CLIMATOLOGY_METHOD_ID, valid_until=valid_time
            )
            if ladder_row is None:
                day += timedelta(days=1)
                continue
            climatology = from_values_json(ladder_row.values_json or {}, method_id=CLIMATOLOGY_METHOD_ID)
            ladder = climatology.ladders.get(key)
            if ladder is None:
                day += timedelta(days=1)
                continue
            ranked = percentile_of(observed, ladder)
            exists = await session.execute(
                sa.select(DerivedFeature.id).where(
                    DerivedFeature.method_id == PERCENTILE_METHOD_ID,
                    DerivedFeature.feature == PERCENTILE_FEATURE,
                    DerivedFeature.scope_id == station.id,
                    DerivedFeature.valid_time == valid_time,
                )
            )
            if exists.first() is not None:
                day += timedelta(days=1)
                continue
            quality = list(flags) + list(ranked.quality)
            if record.approval_status:
                quality.append(record.approval_status.lower())
            values_json: dict[str, Any] = {
                "day": day.isoformat(),
                "doy_key": key,
                "sample_count": ranked.sample_count,
                "ladder": {f"p{p:02d}": ladder.values[p] for p in sorted(ladder.values)},
                "climatology": {
                    "method_id": climatology.method_id,
                    "ref": climatology.climatology_ref,
                    "begin_year": climatology.begin_year,
                    "end_year": climatology.end_year,
                },
                "approval_status": record.approval_status,
                # The reconstruction says so IN THE ROW, not only in the run document: anyone who
                # finds this row later must be able to see that no job wrote it.
                "reconstructed": {
                    "by": "scripts/hindcast_event_zero.py",
                    "from_artifact": row.raw_artifact_id,
                    "note": (
                        "retrospective reconstruction of a ranking the deployed job never "
                        "performed; available_at is the daily mean's own completion instant, "
                        "not a retrieval time"
                    ),
                },
            }
            if published is not None:
                disagreement = p50_disagreement(climatology, published, key)
                values_json["cross_check"] = {
                    "method_id": PUBLISHED_METHOD_ID,
                    "ref": published.climatology_ref,
                    "cascade_p50": ladder.values.get(50),
                    "published_p50": published.ladders[key].values.get(50) if key in published.ladders else None,
                    "disagreement_fraction": None if disagreement is None else round(disagreement, 4),
                    "threshold": DISAGREEMENT_FRACTION,
                }
                if disagreement is not None and abs(disagreement) > DISAGREEMENT_FRACTION:
                    quality.append("climatology_disagreement")
            else:
                values_json["cross_check"] = None
                quality.append("no_published_cross_check")
            session.add(
                DerivedFeature(
                    feature=PERCENTILE_FEATURE,
                    scope_kind="station",
                    scope_id=station.id,
                    window=None,
                    valid_time=valid_time,
                    issued_at=None,
                    computed_at=fetched_at,
                    # THE PROJECTION RULE, applied at write time for this family: the earliest
                    # instant the value was complete. `available_at()` would take the max with
                    # the 2026 retrieval time and make the row invisible to the replay, which is
                    # the correct KNOWLEDGE_TIME answer and the wrong RETROSPECTIVE one.
                    available_at=valid_time,
                    method_id=PERCENTILE_METHOD_ID,
                    product_id=PRODUCT_USGS_OGC_DAILY,
                    value=observed,
                    values_json=values_json,
                    unit="cfs",
                    percentile=round(ranked.percentile, 2),
                    climatology_ref=climatology.climatology_ref,
                    confidence_label="unknown",
                    quality=list(dict.fromkeys(quality)),
                    inputs=[{"table": "raw_artifact", "id": row.raw_artifact_id}],
                    raw_artifact_id=row.raw_artifact_id,
                )
            )
            made += 1
            days.append({"day": day.isoformat(), "flow": observed, "percentile": round(ranked.percentile, 2)})
            day += timedelta(days=1)
        written += made
        gauges[station.id] = {
            "basin": basin.id,
            "site": station.external_id,
            "rows": made,
            "period_of_record": [climatology.begin_year, climatology.end_year],
            "ladder_valid_time": ladder_row.valid_time.isoformat() if made else None,
            "source_artifact": row.raw_artifact_id,
            "approval": approval_census(by_day, start=start, end=end),
            "days": days,
        }
    await session.flush()
    return ReconstructionReport(rows_written=written, gauges=gauges)


async def restore_archive_clocks(session: AsyncSession) -> dict[str, int]:
    """Put every visibility clock back to what the archive says, so KNOWLEDGE_TIME means it.

    The inverse of :func:`apply_projection`, and it is a real inverse rather than a saved copy:
    `cascade_core.timeutils.available_at` DEFINES the archive clock as
    `max(issued_at or valid_time, retrieved_at)`, and every one of those three columns is
    untouched by the projection. So the archive value is recomputable exactly, and a
    knowledge-time replay run after this is reading the same clocks production reads.

    Without this the two modes cannot both be demonstrated on one scratch database, and a
    KNOWLEDGE_TIME run on a projected database would be a lie wearing the stricter label —
    which is precisely the confusion brief §20 exists to prevent.
    """
    counts: dict[str, int] = {}
    r = await session.execute(
        sa.text("UPDATE observation SET available_at = GREATEST(valid_time, retrieved_at) "
                "WHERE available_at <> GREATEST(valid_time, retrieved_at)")
    )
    counts["observation"] = r.rowcount or 0
    r = await session.execute(
        sa.text("UPDATE derived_feature SET available_at = GREATEST(COALESCE(issued_at, valid_time), computed_at) "
                "WHERE available_at <> GREATEST(COALESCE(issued_at, valid_time), computed_at)")
    )
    counts["derived_feature"] = r.rowcount or 0
    r = await session.execute(sa.text("UPDATE threshold SET effective_from = retrieved_at WHERE effective_from <> retrieved_at"))
    counts["threshold"] = r.rowcount or 0
    r = await session.execute(
        sa.text("UPDATE forecast_run SET available_at = GREATEST(issued_at, retrieved_at) "
                "WHERE available_at <> GREATEST(issued_at, retrieved_at)")
    )
    counts["forecast_run"] = r.rowcount or 0
    await session.commit()
    return counts


async def projection_state(session: AsyncSession) -> dict[str, Any]:
    """Whether this database is currently projected, measured rather than remembered.

    `run` records it in the output so a run document can never claim a mode the database it read
    was not in.
    """
    row = (
        await session.execute(
            sa.text(
                "SELECT (SELECT count(*) FROM observation WHERE available_at = valid_time), "
                "       (SELECT count(*) FROM observation), "
                "       (SELECT count(*) FROM forecast_run WHERE available_at = issued_at), "
                "       (SELECT count(*) FROM forecast_run), "
                "       (SELECT count(*) FROM derived_feature WHERE method_id = :pct AND available_at = valid_time), "
                "       (SELECT count(*) FROM derived_feature WHERE method_id = :pct), "
                "       (SELECT count(*) FROM derived_feature WHERE quality::jsonb ? :flag AND available_at = valid_time), "
                "       (SELECT count(*) FROM derived_feature WHERE quality::jsonb ? :flag)"
            ),
            {"pct": PERCENTILE_METHOD_ID, "flag": PRE_EVENT_QUALITY_FLAG},
        )
    ).first()
    obs_projected, obs_total, run_projected, run_total, pct_projected, pct_total, ref_projected, ref_total = row
    return {
        "observations_visible_at_valid_time": f"{obs_projected}/{obs_total}",
        "forecast_runs_visible_at_issued_at": f"{run_projected}/{run_total}",
        "reconstructed_rankings_visible_at_valid_time": f"{pct_projected}/{pct_total}",
        "pre_event_reference_visible_at_valid_time": f"{ref_projected}/{ref_total}",
        "projected": bool(
            obs_total
            and obs_projected == obs_total
            and pct_total
            and pct_projected == pct_total
            and ref_total
            and ref_projected == ref_total
        ),
    }


async def apply_projection(session: AsyncSession) -> dict[str, int]:
    """Move the visibility clocks. Values, valid times and issue times are never touched."""
    counts: dict[str, int] = {}
    r = await session.execute(sa.text("UPDATE observation SET available_at = valid_time WHERE available_at > valid_time"))
    counts["observation"] = r.rowcount or 0
    # The 2026-vintage reference rows are NOT projected and do not need to be: their valid_time
    # is 2026-08-26, and `Knowledge` asks for `valid_time <= as_of`, so a December-2025 replay
    # cannot see them however their available_at is set. The reference a replay actually reads is
    # the pre-event rebuild, which carries its own honest valid_time and available_at and is left
    # untouched here. Moving a valid_time would be falsifying content rather than adjusting
    # visibility, and this script does not do that.
    # The pre-event rebuild is restored to its own honest clock — the instant the annual job
    # would have written it — because `unproject` recomputes every derived_feature's archive
    # clock from `computed_at`, which for these rows is the 2026 fetch of the source bytes.
    r = await session.execute(
        sa.text(
            "UPDATE derived_feature SET available_at = valid_time "
            "WHERE quality::jsonb ? :flag AND available_at <> valid_time"
        ),
        {"flag": PRE_EVENT_QUALITY_FLAG},
    )
    counts["derived_feature:pre_event_reference"] = r.rowcount or 0
    # The reconstructed ranking: visible from the instant the daily mean it ranks was complete.
    # Written that way too, but restated here so `project` is idempotent after an `unproject`.
    r = await session.execute(
        sa.text(
            "UPDATE derived_feature SET available_at = valid_time "
            "WHERE method_id = :pct AND feature = :feat AND available_at <> valid_time"
        ),
        {"pct": PERCENTILE_METHOD_ID, "feat": PERCENTILE_FEATURE},
    )
    counts["derived_feature:reconstructed_percentile"] = r.rowcount or 0
    r = await session.execute(
        sa.text("UPDATE threshold SET effective_from = :epoch WHERE effective_from > :epoch"),
        {"epoch": PROJECTION_EPOCH},
    )
    counts["threshold"] = r.rowcount or 0
    r = await session.execute(
        sa.text("UPDATE forecast_run SET available_at = issued_at WHERE available_at > issued_at")
    )
    counts["forecast_run"] = r.rowcount or 0
    await session.commit()
    return counts


async def ladder_vintage(session: AsyncSession, settings: Settings, *, start: date, end: date) -> dict[str, Any]:
    """Rank the same daily means in EVERY stored ladder vintage, and report where they differ.

    Register X8 asks which record a day-of-year ladder should be built from and is deliberately
    left open by this change. This does not answer it — it MEASURES what it is worth, on the one
    quantity the old method escalates on: the first day a gauge's daily mean reaches p90.

    Nothing varies here but the ladder. Same days, same values, same `percentile_of`, same
    `band`. Any difference in the answer is the vintage and nothing else.
    """
    store = store_from_settings(settings)
    out: dict[str, Any] = {"window": [start.isoformat(), end.isoformat()], "gauges": {}}
    for basin, station in await _susceptibility_gauges(session):
        rows = (
            await session.execute(
                sa.select(DerivedFeature)
                .where(
                    DerivedFeature.scope_id == station.id,
                    DerivedFeature.method_id == CLIMATOLOGY_METHOD_ID,
                )
                .order_by(DerivedFeature.valid_time)
            )
        ).scalars().all()
        if not rows:
            continue
        source = rows[-1]
        raw = (
            await session.execute(
                sa.text("SELECT object_key FROM raw_artifact WHERE id = :i"), {"i": source.raw_artifact_id}
            )
        ).first()
        if raw is None:
            continue
        by_day = {r.day: r for r in parse_daily_csv(store.get(raw[0]), site=station.external_id)}
        vintages: dict[str, Any] = {}
        for row in rows:
            climatology = from_values_json(row.values_json or {}, method_id=CLIMATOLOGY_METHOD_ID)
            first_p90: str | None = None
            series: list[list[Any]] = []
            day = start
            while day <= end:
                observed = _numeric(by_day.get(day))
                ladder = climatology.ladders.get(doy_key(day))
                if observed is not None and ladder is not None:
                    pct = round(percentile_of(observed, ladder).percentile, 2)
                    series.append([day.isoformat(), observed, pct])
                    if first_p90 is None and susceptibility.band(round(pct, 1)) is BAND_TOP:
                        first_p90 = day.isoformat()
                day += timedelta(days=1)
            vintages[row.valid_time.isoformat()] = {
                "period_of_record": [climatology.begin_year, climatology.end_year],
                "quality": list(row.quality or ()),
                "first_day_at_or_above_p90": first_p90,
                "series": series,
            }
        firsts = {v["first_day_at_or_above_p90"] for v in vintages.values()}
        out["gauges"][station.id] = {
            "basin": basin.id,
            "site": station.external_id,
            "vintages": vintages,
            "first_p90_day_moves_with_vintage": len(firsts) > 1,
        }
    return out


# =============================================================================================
# The run
# =============================================================================================


async def run(
    session: AsyncSession,
    *,
    mode: hindcast.ReplayMode,
    limit_times: int | None = None,
) -> hindcast.HindcastRun:
    basins = (await session.execute(sa.select(Basin).order_by(Basin.id))).scalars().all()
    event = event_zero(tuple(b.id for b in basins))
    times = list(event.all_times())
    if limit_times:
        times = times[:limit_times]
    projection = (
        PROJECTION
        if mode is hindcast.ReplayMode.RETROSPECTIVE
        else hindcast.Projection(name="none", mode=hindcast.ReplayMode.KNOWLEDGE_TIME)
    )
    arms = (hindcast.ARM_OLD, hindcast.ARM_NEW)
    rules = (
        hindcast.ANY_ESCALATION,
        hindcast.BAND_HIGH_ESCALATION,
        hindcast.BAND_ESCALATION,
        hindcast.TREND_RISING,
        hindcast.RISING_24H,
        hindcast.RISING_48H,
        hindcast.growth_rank_rules(0.05),
        hindcast.growth_rank_rules(0.01),
    )
    out = hindcast.HindcastRun(
        event=event, projection=projection, arms=arms, rules=rules, generated_at=utcnow(),
        notes=(
            "Reference distributions were REBUILT for this run by re-running the shipped "
            "builders over the same archived record truncated at 2025-10-31, so no water-year "
            "2026 day is inside the distribution that ranks the event (register X8 claim D is "
            "removed from this run rather than declared). Both arms read the identical ladder. "
            "Verify per row, never from this sentence: `reference.contains_event` is False and "
            "`reference.truncated_at` is 2025-10-31, both derived from the cutoff.",
            "Forcing (NBM QPF) and model agreement (NWM) have no December 2025 rows in any "
            "archive available to this platform, so both surfaces are UNKNOWN throughout and "
            "the A/B is confined to the susceptibility level, the state change and the trend.",
        ),
    )
    state = await projection_state(session)
    out.notes = (*out.notes, f"database projection state at run time: {json.dumps(state)}")
    if state["projected"] != (mode is hindcast.ReplayMode.RETROSPECTIVE):
        raise SystemExit(
            f"refusing to label this run {mode.value}: the database is "
            f"{'projected' if state['projected'] else 'unprojected'}. Run `project` or "
            f"`unproject` first. A run document must not claim a mode its database was not in."
        )
    now = utcnow()
    for as_of, is_control in times:
        k = as_known_at(session, as_of)
        products = await k.products()
        await susceptibility.prefetch(k, basins)
        for basin in basins:
            outlet = (
                await k.forecast_point_by_lid(basin.outlet_fp_id.split(":")[-1])
                if basin.outlet_fp_id
                else None
            )
            for arm in arms:
                out.evaluations.append(
                    await hindcast.evaluate(
                        k, event=event, arm=arm, basin=basin, products=products, mode=mode,
                        cursor=as_of.date(), is_control=is_control, outlet=outlet, system_now=now,
                        # DERIVED from the cutoff, not asserted: the reference is rebuilt from
                        # the record up to PRE_EVENT_CUTOFF, and every evaluation instant in this
                        # event is strictly after it, so no day of the event can be inside its
                        # own reference distribution. Register X8 claim D does not apply to this
                        # run — `vintage` measures separately what it would have been worth.
                        reference_contains_event=False,
                        reference_truncated_at=PRE_EVENT_CUTOFF,
                    )
                )
    return out


# =============================================================================================
# The false-warning base rate — the other half of the governing question
# =============================================================================================
#
# "Remaining quiet when no meaningful deterioration existed" cannot be answered from an event
# window and eleven control days: that is a sample of one flood. What CAN be answered, exactly
# and offline, is how often each candidate escalation rule would have fired across every day of
# each gauge's own record. That is a base rate, not a false-alarm ratio — no day here is labelled
# "flood" or "not flood" — and it is reported as one.


async def base_rate(session: AsyncSession, settings: Settings) -> dict[str, Any]:
    store = store_from_settings(settings)
    out: dict[str, Any] = {
        "method": (
            "susceptibility.state_change applied to every consecutive pair of approved daily "
            "means in each gauge's own archived record, and susceptibility.band applied to every "
            "daily mean ranked in its own day-of-year ladder. Counts days on which each rule "
            "would have held. NOT a false-alarm ratio: no day is labelled."
        ),
        "gauges": {},
    }
    for basin, station in await _susceptibility_gauges(session):
        # The SAME pre-event ladder the A/B ranks against, so a base rate and an event-window
        # count are statements about one reference distribution and can be read side by side.
        reference_at, _ = daily_mean_valid_time(PRE_EVENT_CUTOFF, time_zone=station.time_zone)
        row = await _latest_row(
            session, scope_id=station.id, method_id=CLIMATOLOGY_METHOD_ID, valid_until=reference_at
        )
        if row is None:
            continue
        climatology = from_values_json(row.values_json or {}, method_id=CLIMATOLOGY_METHOD_ID)
        raw = (
            await session.execute(
                sa.text("SELECT object_key FROM raw_artifact WHERE id = :i"), {"i": row.raw_artifact_id}
            )
        ).first()
        if raw is None:
            continue
        by_day = {r.day: r for r in parse_daily_csv(store.get(raw[0]), site=station.external_id)}
        points: list[tuple[datetime, float]] = []
        for day in sorted(by_day):
            observed = _numeric(by_day[day])
            if observed is None:
                continue
            valid_time, _flags = daily_mean_valid_time(day, time_zone=station.time_zone)
            points.append((valid_time, observed))
        counters: dict[str, int] = defaultdict(int)
        considered = 0
        winter = 0
        for i, (t, _v) in enumerate(points):
            if i < 3:
                continue
            considered += 1
            is_winter = t.month in (11, 12, 1, 2)
            winter += 1 if is_winter else 0

            def bump(name: str, *, w: bool = False) -> None:
                counters[name] += 1
                if w:
                    counters[f"{name}_winter"] += 1

            rising24 = False
            for window_h in susceptibility.STATE_CHANGE_WINDOWS_H:
                reading = susceptibility.state_change(points[max(0, i - 6): i + 1], end=t, window_h=window_h)
                if reading.direction == "rising":
                    bump(f"rising_{window_h}h", w=is_winter)
                    rising24 = rising24 or window_h == 24
            key = doy_key(t.date() - timedelta(days=1))
            ladder = climatology.ladders.get(key)
            very_high = False
            if ladder is not None:
                ranked = percentile_of(points[i][1], ladder)
                level = susceptibility.band(round(ranked.percentile, 1))
                very_high = level.value == "very_high"
                if level.value in ("high", "very_high"):
                    bump("band_high", w=is_winter)
                if very_high:
                    bump("band_very_high", w=is_winter)
            # The rule the A/B actually compares arms on, and the two halves of what adding it
            # costs: how often the union speaks at all, and how often the VELOCITY is the only
            # reason it speaks. The second is the marginal false-warning surface of this change.
            if very_high or rising24:
                bump("any_escalation", w=is_winter)
            if rising24 and not very_high:
                bump("rising_24h_below_p90", w=is_winter)
        out["gauges"][station.id] = {
            "basin": basin.id,
            "site": station.external_id,
            "days_considered": considered,
            "winter_days_considered": winter,
            "period_of_record": [climatology.begin_year, climatology.end_year],
            "firings": dict(sorted(counters.items())),
            "days_per_year": {
                name: round(count / max(1e-9, considered / 365.25), 1)
                for name, count in sorted(counters.items())
                if not name.endswith("_winter")
            },
        }
    return out


# =============================================================================================
# The regression fixture
# =============================================================================================


def build_fixture(run_doc: dict[str, Any], points: dict[str, list[list[Any]]]) -> dict[str, Any]:
    """The pinned, offline, deterministic slice of an actual run.

    Two things are pinned, and the second is what makes it a regression test of the METHODS
    rather than of this script:

    1. the harness's own verdicts, so `compare_arms` and the escalation rules can be recomputed
       from the recorded evaluations and checked against what this run produced;
    2. the INPUTS every published number was computed from — the ranked daily-mean series with
       its valid times, the ladder's p95 reference flow, the window sample size — beside the
       outputs, so `tests/unit/test_hindcast.py` can re-run `susceptibility.state_change`,
       `seasonal_multiple`, `band`, `independent_years`, `rank_standard_error_points` and
       `band_boundary` and assert the shipped code still produces exactly these numbers, with no
       database, no network and no fixture of prose.

    The exact rank is pinned as a value only: reproducing it offline would mean shipping a
    62 KiB record-context blob per gauge into the test fixture, which is a copy of source data
    and the one thing this harness is not allowed to store.
    """
    keep = {"basin:skagit", "basin:snohomish-snoqualmie", "basin:cedar"}
    evaluations = [
        e
        for e in run_doc["evaluations"]
        if e["basin_id"] in keep and e["clocks"]["as_of"].endswith("12:00:00+00:00")
    ]
    gauges = {e["gauge_id"] for e in evaluations}
    rehydrated = [hindcast.evaluation_from_dict(e) for e in evaluations]
    return {
        "_provenance": {
            "generated_by": "scripts/hindcast_event_zero.py fixture",
            "generated_at": run_doc["generated_at"],
            "event": run_doc["event"]["id"],
            "mode": run_doc["projection"]["mode"],
            "disclosure": run_doc["projection"]["disclosure"],
            "note": (
                "Actual reconstructed values from a retrospective replay of Event Zero — never "
                "transcribed from prose. Three basins at the 12:00Z evaluations, which is the "
                "smallest slice that still contains a clamped percentile whose derivative reads "
                "+0, a flow above the whole window record, and a quiet control day."
            ),
        },
        "ranked_daily_means": {g: v for g, v in sorted(points.items()) if g in gauges},
        "evaluations": evaluations,
        # Recomputed over THIS SLICE so the fixture is internally consistent: a test that
        # recomputes the verdicts from the evaluations it holds must be able to reach the
        # verdicts it holds. Where the slice is missing an hour at which something escalated,
        # the two lists below differ, and that difference is information rather than a defect —
        # `trend_rising_6h` moves within a day on the 6-hourly grid and the 12:00Z slice cannot
        # see it, which is exactly why the run evaluates four times a day.
        "comparisons": [
            hindcast.compare_arms(rehydrated, rule, basin_id=basin_id).as_dict()
            for rule in _FIXTURE_RULES
            for basin_id in sorted(keep)
        ],
        "comparisons_over_the_full_run": run_doc["comparisons"],
        "rules": run_doc["rules"],
    }


#: The rules the fixture recomputes. Same objects the run uses, listed once so the fixture and
#: the run cannot end up describing different rules by the same id.
_FIXTURE_RULES = (
    hindcast.ANY_ESCALATION,
    hindcast.BAND_HIGH_ESCALATION,
    hindcast.BAND_ESCALATION,
    hindcast.TREND_RISING,
    hindcast.RISING_24H,
    hindcast.RISING_48H,
    hindcast.growth_rank_rules(0.05),
    hindcast.growth_rank_rules(0.01),
)


async def ranked_daily_means(session: AsyncSession) -> dict[str, list[list[Any]]]:
    """`[valid_time, flow, percentile]` per gauge — the series the velocity is computed over.

    Small on purpose: 52 rows per gauge, which is the window the run evaluates, not the 36,000
    of the record.
    """
    rows = (
        await session.execute(
            sa.select(DerivedFeature)
            .where(
                DerivedFeature.method_id == PERCENTILE_METHOD_ID,
                DerivedFeature.feature == PERCENTILE_FEATURE,
            )
            .order_by(DerivedFeature.scope_id, DerivedFeature.valid_time)
        )
    ).scalars().all()
    out: dict[str, list[list[Any]]] = {}
    for row in rows:
        if row.value is None:
            continue
        out.setdefault(row.scope_id, []).append(
            [row.valid_time.isoformat(), float(row.value), None if row.percentile is None else float(row.percentile)]
        )
    return out


# =============================================================================================
# CLI
# =============================================================================================


def _sessions(db_url: str):  # noqa: ANN202
    return make_session_factory(make_engine(db_url))


async def _main(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    db_url = args.db_url or settings.db_url
    sessions = _sessions(db_url)
    if args.command == "fixture":
        run_doc = json.loads(Path(args.run).read_text())
        async with sessions() as session:
            points = await ranked_daily_means(session)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(build_fixture(run_doc, points), indent=1) + "\n")
        print(json.dumps({"fixture": args.out, "evaluations": len(build_fixture(run_doc, points)["evaluations"])}))
        return 0
    if args.command == "reconstruct":
        _guard_scratch(db_url)
        async with sessions() as session:
            report = await reconstruct(session, settings, start=RECONSTRUCT_START, end=RECONSTRUCT_END)
            await session.commit()
        print(json.dumps({"reconstruction": report.as_dict()}, indent=1))
        return 0
    if args.command == "reference":
        _guard_scratch(db_url)
        async with sessions() as session:
            doc = await build_reference(session, settings, cutoff=date.fromisoformat(args.cutoff))
            await session.commit()
        print(json.dumps(doc, indent=1))
        return 0
    if args.command in ("project", "unproject"):
        _guard_scratch(db_url)
        async with sessions() as session:
            counts = await (apply_projection if args.command == "project" else restore_archive_clocks)(session)
            state = await projection_state(session)
        print(json.dumps({args.command: counts, "state": state}, indent=1))
        return 0
    if args.command == "vintage":
        async with sessions() as session:
            doc = await ladder_vintage(session, settings, start=EVENT_START, end=EVENT_END)
        Path(args.out).write_text(json.dumps(doc, indent=1) + "\n")
        moved = [g for g, v in doc["gauges"].items() if v["first_p90_day_moves_with_vintage"]]
        print(json.dumps({"out": args.out, "gauges": len(doc["gauges"]), "first_p90_day_moves": moved}, indent=1))
        return 0
    if args.command == "base-rate":
        async with sessions() as session:
            doc = await base_rate(session, settings)
        Path(args.out).write_text(json.dumps(doc, indent=1) + "\n")
        print(json.dumps({"out": args.out, "gauges": len(doc["gauges"])}))
        return 0
    if args.command == "run":
        mode = (
            hindcast.ReplayMode.RETROSPECTIVE
            if args.mode == "retrospective"
            else hindcast.ReplayMode.KNOWLEDGE_TIME
        )
        async with sessions() as session:
            doc = (await run(session, mode=mode, limit_times=args.limit_times)).as_dict()
        Path(args.out).write_text(json.dumps(doc, indent=1) + "\n")
        known = sum(1 for e in doc["evaluations"] if e["surface_state"] != "unknown")
        print(json.dumps({
            "out": args.out,
            "mode": mode.value,
            "evaluations": len(doc["evaluations"]),
            "with_a_computed_surface": known,
            "disclosure": doc["projection"]["disclosure"],
        }, indent=1))
        return 0
    raise SystemExit(f"unknown command {args.command}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="hindcast_event_zero")
    p.add_argument("command", choices=["reference", "reconstruct", "project", "unproject", "run", "vintage", "base-rate", "fixture"])
    p.add_argument("--db-url", default=None)
    p.add_argument("--mode", choices=["retrospective", "knowledge-time"], default="retrospective")
    p.add_argument("--out", default="hindcast-run.json")
    p.add_argument("--run", default="hindcast-run.json")
    p.add_argument("--limit-times", type=int, default=None)
    p.add_argument("--cutoff", default=PRE_EVENT_CUTOFF.isoformat())
    return asyncio.run(_main(p.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
