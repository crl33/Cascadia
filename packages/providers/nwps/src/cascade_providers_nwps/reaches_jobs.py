"""Idempotent NWM medium-range job (design §3.4).

Every 6 h, for each forecast point that carries a `reach_id`: fetch the reach's medium-range
ensemble, store the provider mean truncated to the 72-hour hazard window as ONE `ForecastRun`,
and store the member hydrographs over `(cycle, cycle + 96 h]` as ONE `derived_feature` row. The
full 240-hour, 7-series payload stays in the object store as the RawArtifact and everything else
is re-derivable from it.

**No crest is computed here** (verification finding B, 2026-08-24). A crest is a maximum over a
window, the comparison window is only known at `as_of`, and the previous version's frozen
cycle-anchored crests were compared against an `as_of`-anchored official crest — two different
windows, offset by the cycle age. `reaches_normalize` carries the full argument; the consequence
for this job is that it stores series and lets `cascade_hydrology.agreement` take every crest at
read time over one shared window.

**Measured cost of storing series instead of crests** (live 12Z cycle, six seed reaches, two
otherwise-identical PostgreSQL 18 databases, 2026-08-24). Raw `values_json` text per cycle grew
4,932 B -> 69,611 B, but PostgreSQL TOAST-compresses flow arrays about 6.6:1, so what lands on
disk is 5,612 B -> 10,603 B. Against that, six frozen per-member crest rows per reach stopped
being written, at ~344 B of row overhead each. Net `derived_feature` bytes per cycle:
**20,056 B -> 12,632 B, a 37 % reduction**, and rows per cycle 42 -> 6. Monthly, at four cycles a
day: 2.41 MB -> 1.52 MB and 5,040 -> 720 rows. `forecast_value` is untouched (432 rows/cycle, the
mean series). The correctness fix therefore *lowers* the free-tier footprint rather than spending
against it; design §3.5's ~57 k rows/month becomes ~52.6 k.

Idempotency is the same rule the official-forecast job uses: one run per
(product, forecast point, issued_at); an already-stored cycle is a no-op, and because the
derived row is written in the same branch it cannot be duplicated either.

This job writes a MODELED product into the same table as the official forecast. That is safe
only because the read path filters by product (`Knowledge.latest_forecast_run`) and resolves
`source_kind` from the registry (`assemble.forecast_run_ref`) — the two defects design §3.4
required to be fixed *before* this job could exist.

**Measured provider behaviour, 2026-08-24 (this is why `EmptyCycleError` exists).** NWPS answers
`/reaches/{id}/streamflow?series=medium_range` with **HTTP 200 and `"mediumRange": {}`** a large
fraction of the time, while `reach.streamflow` still advertises `medium_range`. At 22:05Z all six
seed reaches returned the full 157–161 KB ensemble; at 22:21Z and 22:23Z only one of six did, and
which one changed between the two runs. So an empty series is a transient per-request condition,
not a statement that the cycle does not exist. The job therefore treats "not one point yielded a
cycle" as a failed attempt and lets the queue retry it with backoff, rather than recording a
silent success that wrote nothing. A partial run is not an error: the next cycle catches up, and
until then the surface says UNKNOWN with a reason, which is the correct answer.

One consequence, stated rather than hidden: `run_job` discards the session when a job raises, so
the `RawArtifact` rows for those empty responses are rolled back while the bytes stay in the
object store. Keys are content-addressed, so this is bounded at one ~700-byte object per reach
for all time (identical bytes rewrite the same key), and nothing scientific is lost — an empty
series carries no values. The alternative, committing rows for payloads that contain nothing and
reporting success, would hide a provider outage inside a green job.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import (
    DerivedFeature,
    ForecastPoint,
    ForecastRun,
    ForecastValue,
)
from cascade_core.registry import PRODUCT_NWM_MR
from cascade_providers_nwps.reaches_client import fetch_medium_range
from cascade_providers_nwps.reaches_normalize import (
    SERIES_SCHEMA,
    EnsembleWindow,
    encode_series,
    member_window,
    model_run_from_ensemble,
)
from cascade_providers_nwps.reaches_parser import parse_medium_range

log = logging.getLogger("cascade.providers.nwps.reaches")


class EmptyCycleError(RuntimeError):
    """Every reach answered 200 with an empty series — a retryable provider condition."""

JOB_NAME = "nwm.fetch_reach_medium_range"
CADENCE_SECONDS = 6 * 3600  # NWM medium range runs 00/06/12/18Z (DATA_SOURCES H6)

#: The method that clips the member hydrographs to the stored coverage window. Version it, not
#: the code: a change to the coverage, the encoding or what is stored is a new method id and
#: therefore new rows. `@2.0.0` is the series form — `@1.0.0` froze a cycle-anchored crest per
#: member, which is the bug this replaced, so the two must never be read as the same quantity.
METHOD_MEMBER_SERIES = "method:nwm-member-series@2.0.0"
FEATURE_MEMBER_SERIES = "nwm_mr_member_flow_series"

#: What this row is not: it carries no crest, no median and no central value. Recorded in the
#: row itself so anyone reading the table sees the reason without reading this file.
SERIES_NOTE = (
    "Member hydrographs as published, clipped to the cycle's coverage window. No crest is frozen "
    "here: a crest is a maximum over a window, and the comparison window is only known at read "
    "time (cascade_hydrology.agreement). The NWPS-computed mean is not a member and is not here."
)


def _series_values(window: EnsembleWindow) -> dict[str, object]:
    """The whole member ensemble in one JSON column, so the read path needs exactly one row.

    `member_count` is recorded with the values because a member fraction whose denominator is not
    stated is not a number anyone can check (design §7 item 4), and `coverage_h` is recorded
    because the read path must know how far past the cycle the series actually reaches before it
    decides which window the two forecasts can share."""
    return {
        "schema": SERIES_SCHEMA,
        "cycle": window.issued_at.isoformat(),
        "coverage_h": window.coverage_h,
        "hazard_window_h": window.hazard_window_h,
        "unit": window.unit,
        "member_count": window.member_count,
        "series": {m.member: encode_series(m.points) for m in window.members},
        "note": SERIES_NOTE,
    }


async def _points(session: AsyncSession) -> list[ForecastPoint]:
    q = select(ForecastPoint).where(ForecastPoint.reach_id.is_not(None)).order_by(ForecastPoint.id)
    return list((await session.execute(q)).scalars().all())


async def run_fetch_medium_range(session: AsyncSession, fetcher: ArchivingFetcher) -> int:
    written = 0
    points = await _points(session)
    empty: list[str] = []
    for fp in points:
        assert fp.reach_id is not None
        result = await fetch_medium_range(fetcher, session, fp.reach_id)
        ensemble = parse_medium_range(result.content)
        rec = model_run_from_ensemble(ensemble, retrieved_at=result.fetched_at)
        if rec is None:
            # HTTP 200 with an advertised-but-empty series; see the module docstring.
            log.info("%s: no usable NWM medium-range mean series at reach %s", fp.id, fp.reach_id)
            empty.append(fp.id)
            continue
        exists = (
            await session.execute(
                select(ForecastRun.id).where(
                    ForecastRun.product_id == PRODUCT_NWM_MR,
                    ForecastRun.fp_id == fp.id,
                    ForecastRun.issued_at == rec.issued_at,
                )
            )
        ).scalar_one_or_none()
        if exists is not None:
            continue
        prev = (
            await session.execute(
                select(ForecastRun)
                .where(ForecastRun.fp_id == fp.id, ForecastRun.product_id == PRODUCT_NWM_MR)
                .order_by(ForecastRun.issued_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        run = ForecastRun(
            product_id=PRODUCT_NWM_MR,
            fp_id=fp.id,
            issued_at=rec.issued_at,
            retrieved_at=rec.retrieved_at,
            available_at=rec.available_at,
            issuer=rec.issuer,
            primary_variable=rec.primary_variable,
            unit=rec.unit,
            stage_unit=rec.stage_unit,
            flow_unit=rec.flow_unit,
            datum=rec.datum,
            raw_artifact_id=result.artifact_id,
            supersedes_run_id=None if prev is None or prev.issued_at >= rec.issued_at else prev.id,
        )
        session.add(run)
        await session.flush()
        for v in rec.values:
            session.add(ForecastValue(run_id=run.id, valid_time=v.valid_time, stage=None, flow=v.flow))
        written += 1 + len(rec.values)

        window = member_window(ensemble)
        if window is None:
            continue
        session.add(
            DerivedFeature(
                feature=FEATURE_MEMBER_SERIES,
                # The row is about a cycle, not about an instant, so `valid_time` is the cycle.
                # Anything else would be a crest time, and this row deliberately has no crest.
                valid_time=window.issued_at,
                value=None,
                values_json=_series_values(window),
                scope_kind="forecast_point",
                scope_id=fp.id,
                window=f"{window.coverage_h}h",
                issued_at=window.issued_at,
                computed_at=result.fetched_at,
                available_at=rec.available_at,
                method_id=METHOD_MEMBER_SERIES,
                product_id=PRODUCT_NWM_MR,
                unit=window.unit,
                confidence_label="unknown",  # a faithful readout of an uncalibrated model
                inputs=[{"table": "raw_artifact", "id": result.artifact_id}],
                raw_inputs_hash=result.sha256,
                raw_artifact_id=result.artifact_id,
            )
        )
        written += 1
    await session.flush()
    if points and len(empty) == len(points):
        raise EmptyCycleError(
            f"every reach ({len(points)}) returned HTTP 200 with an empty medium_range series; "
            "the raw responses are archived. This is a transient NWPS condition — retry rather "
            "than recording a successful run that stored nothing."
        )
    return written
