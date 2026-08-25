"""Idempotent NWM medium-range job (design §3.4).

Every 6 h, for each forecast point that carries a `reach_id`: fetch the reach's medium-range
ensemble, store the provider mean truncated to the 72-hour hazard window as ONE `ForecastRun`,
and store the per-member crest summary as `derived_feature` rows. The full 240-hour, 7-series
payload stays in the object store as the RawArtifact and everything else is re-derivable from it.

Idempotency is the same rule the official-forecast job uses: one run per
(product, forecast point, issued_at); an already-stored cycle is a no-op, and because the
derived rows are written in the same branch they cannot be duplicated either.

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
    EnsembleCrestSummary,
    crest_summary,
    model_run_from_ensemble,
)
from cascade_providers_nwps.reaches_parser import parse_medium_range

log = logging.getLogger("cascade.providers.nwps.reaches")


class EmptyCycleError(RuntimeError):
    """Every reach answered 200 with an empty series — a retryable provider condition."""

JOB_NAME = "nwm.fetch_reach_medium_range"
CADENCE_SECONDS = 6 * 3600  # NWM medium range runs 00/06/12/18Z (DATA_SOURCES H6)

#: The method that reads a crest out of a model member's hydrograph. Version it, not the code:
#: a change to the window or to the median rule is a new method id and therefore new rows.
METHOD_MEMBER_CREST = "method:nwm-member-crest@1.0.0"
FEATURE_MEMBER_CREST = "nwm_mr_crest_flow"  # + "_member3" per member
FEATURE_CREST_SUMMARY = "nwm_mr_crest_flow_members"


def _summary_values(summary: EnsembleCrestSummary) -> dict[str, object]:
    """The whole member ladder in one JSON column, so the read path needs exactly one row.

    `median_rule` and `member_count` are recorded with the values because a member fraction
    whose denominator is not stated is not a number anyone can check (design §7 item 4)."""
    return {
        "window_h": summary.window_h,
        "unit": summary.unit,
        "member_count": summary.member_count,
        "median_rule": "lower_median_member",
        "median_member": None if summary.median_member is None else summary.median_member.member,
        "members": {
            c.member: {"crest": c.value, "valid_time": c.valid_time.isoformat()} for c in summary.members
        },
        "provider_mean_crest": (
            None
            if summary.provider_mean_crest is None
            else {
                "crest": summary.provider_mean_crest.value,
                "valid_time": summary.provider_mean_crest.valid_time.isoformat(),
                "note": "NWPS-computed mean of its own members; not a member and never blended with an official forecast",
            }
        ),
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

        summary = crest_summary(ensemble)
        if summary is None:
            continue
        common = {
            "scope_kind": "forecast_point",
            "scope_id": fp.id,
            "window": f"{summary.window_h}h",
            "issued_at": summary.issued_at,
            "computed_at": result.fetched_at,
            "available_at": rec.available_at,
            "method_id": METHOD_MEMBER_CREST,
            "product_id": PRODUCT_NWM_MR,
            "unit": summary.unit,
            "confidence_label": "unknown",  # a faithful readout of an uncalibrated model
            "inputs": [{"table": "raw_artifact", "id": result.artifact_id}],
            "raw_inputs_hash": result.sha256,
            "raw_artifact_id": result.artifact_id,
        }
        for crest in summary.members:
            session.add(
                DerivedFeature(
                    feature=f"{FEATURE_MEMBER_CREST}_{crest.member}",
                    valid_time=crest.valid_time,
                    value=crest.value,
                    **common,
                )
            )
            written += 1
        median = summary.median_member
        session.add(
            DerivedFeature(
                feature=FEATURE_CREST_SUMMARY,
                valid_time=median.valid_time if median is not None else summary.issued_at,
                value=None if median is None else median.value,
                values_json=_summary_values(summary),
                **common,
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
