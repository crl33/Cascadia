"""Archive every HEFS cycle before the provider drops it, and store what Phase 5 will read.

The job is a backfill that happens to run daily. HEFS keeps ~10 cycles; this walks the header list
at each seed forecast point, collects every cycle not already stored, and archives the bytes. On a
first run against a fresh database it therefore recovers up to ten days of history in one pass —
which is the only recovery this data has, because a cycle that ages out is gone.

**Why the loop is per (location, cycle).** Any HEFS query matching more than 100 objects fails
HTTP 400, and one cycle is already 45 members (FACT, DATA_SOURCES H4). There is no bulk form.

**Why one row per cycle, not 5,445.** 45 members x 121 six-hourly steps is 5,445 numbers per
location-cycle; as `ForecastValue` rows that is ~32,700 inserts a day for six points, for a
product nothing reads pointwise yet. This follows the precedent `nwm.fetch_reach_medium_range`
already set for member ensembles: one `DerivedFeature` per cycle whose `values_json` carries the
whole ensemble on the uniform grid it arrived on. The raw payload is archived either way, so the
irreplaceable part is safe regardless of how the normalized form later evolves.

**Two knowledge times, kept apart** (ADR-0010): `issued_at` is the cycle (`forecast_datetime`),
`available_at` is publication (`creation_datetime`), and they differ by 3-4 h. `valid_time` is the
cycle instant, not a crest time — these rows carry no crest, no mean and no central value, exactly
like the NWM member-series row.

**What these rows are NOT.** They are MODELED members badged EXPERIMENTAL, not official
probabilities. ROADMAP Phase 5 decides that promotion, and DATA_DOCTRINE §9(a) is the rule. The
published quantiles are stored separately and are the provider's own numbers; nothing here
computes a quantile from the members, because a Cascade-computed quantile is not official guidance
however closely it matches.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchError
from cascade_core.models import DerivedFeature, ForecastPoint
from cascade_core.registry import PRODUCT_HEFS_ENSEMBLE, PRODUCT_HEFS_QUANTILES
from cascade_providers_nwps.hefs_client import (
    fetch_ensemble,
    fetch_headers,
    fetch_quantiles,
)
from cascade_providers_nwps.hefs_parser import (
    parse_ensembles,
    parse_headers,
    parse_quantiles,
)

log = logging.getLogger("cascade.providers.nwps.hefs")

JOB_NAME = "nwps.fetch_hefs"
#: Daily. The cycle is 12Z and NWS publishes it ~15:06-15:49Z, so the cron sits at 16:30Z —
#: comfortably after the observed latency, and far enough before the next cycle that a missed run
#: still has the whole retention window to catch up in.
CADENCE_SECONDS = 86400
CRON = "30 16 * * *"

#: One row carries a whole cycle's members. Version the METHOD, not the code: a change to the
#: encoding or to which members are kept is a new method id and therefore new rows.
METHOD_MEMBERS = "method:nwps-hefs-members@1.0.0"
FEATURE_MEMBERS = "hefs_ensemble_flow_series"
METHOD_QUANTILES = "method:nwps-hefs-quantiles@1.0.0"
FEATURE_QUANTILES = "hefs_exceedance_quantiles"

SERIES_SCHEMA = "hefs-member-series@1"

#: Said in the row itself, so anyone reading the table sees it without finding this file.
MEMBERS_NOTE = (
    "NWRFC HEFS (MEFP) ensemble traces, EXPERIMENTAL. Member indices are historical WEATHER YEARS "
    "(1981-2025), not member numbers or probabilities: trace 1981 is 'what this basin would do "
    "under 1981's weather', so ordering or averaging them is meaningless. This row carries no "
    "crest, no mean and no central value. The provider's own exceedance quantiles are stored "
    "separately under method:nwps-hefs-quantiles; anything computed from these members by Cascadia "
    "is Cascade-derived and must not be shown as official probability (DATA_DOCTRINE §9(a))."
)
QUANTILES_NOTE = (
    "NWRFC HEFS published exceedance quantiles — the provider's OWN numbers, fetched rather than "
    "computed from the members so they remain official guidance rather than a Cascade derivation."
)


class NoHefsCyclesError(RuntimeError):
    """Not one location served a cycle — retryable, and a real signal for an unsupported API."""


async def _points(session: AsyncSession) -> list[ForecastPoint]:
    q = select(ForecastPoint).where(ForecastPoint.lid.is_not(None)).order_by(ForecastPoint.id)
    return list((await session.execute(q)).scalars().all())


async def _stored_cycles(session: AsyncSession, fp_id: str) -> set[datetime]:
    q = select(DerivedFeature.issued_at).where(
        DerivedFeature.feature == FEATURE_MEMBERS,
        DerivedFeature.method_id == METHOD_MEMBERS,
        DerivedFeature.scope_kind == "forecast_point",
        DerivedFeature.scope_id == fp_id,
    )
    return {d for (d,) in (await session.execute(q)).all() if d is not None}


def _member_values(ensemble) -> dict:
    """The whole cycle on the grid it arrived on. Faithful first, compact second."""
    step_h = ensemble.header.step_seconds / 3600.0
    times = [t for t, _ in ensemble.members[0].values] if ensemble.members else []
    uniform = all(
        len(m.values) == len(times) and [t for t, _ in m.values] == times for m in ensemble.members
    )
    common = {
        "schema": SERIES_SCHEMA,
        "location_id": ensemble.header.location_id,
        "ensemble_id": ensemble.header.ensemble_id,
        "parameter_id": ensemble.header.parameter_id,
        "unit": ensemble.header.units,
        "member_count": len(ensemble.members),
        "member_index_meaning": "historical weather year",
        "note": MEMBERS_NOTE,
    }
    if uniform and times:
        return common | {
            "encoding": "grid",
            "t0": times[0].isoformat(),
            "step_h": step_h,
            "members": {str(m.index): [v for _, v in m.values] for m in ensemble.members},
        }
    # Not one grid: write the timestamps out rather than implying times the model never gave.
    return common | {
        "encoding": "points",
        "members": {
            str(m.index): [[t.isoformat(), v] for t, v in m.values] for m in ensemble.members
        },
    }


def _quantile_values(q) -> dict:
    return {
        "schema": "hefs-exceedance-quantiles@1",
        "location_id": q.location_id,
        "parameter_id": q.parameter_id,
        "unit": q.units,
        "exceedance_levels": list(q.levels),
        "rows": [
            {"valid_time": t.isoformat(), "values": list(v), "max": mx, "min": mn}
            for t, v, mx, mn in q.rows
        ],
        "note": QUANTILES_NOTE,
    }


async def run_fetch_hefs(session: AsyncSession, fetcher: ArchivingFetcher) -> int:
    """Archive and store every retained cycle not already held, at every seed forecast point."""
    written = 0
    points = await _points(session)
    served: list[str] = []
    unreachable: list[str] = []

    for fp in points:
        lid = fp.lid
        assert lid is not None
        try:
            head_result = await fetch_headers(fetcher, session, location_id=lid)
        except FetchError as e:
            # Per point, for the same reason the NWM reach job isolates per reach: one slow or
            # unhappy location must not discard the cycles another location just yielded.
            log.warning("hefs: %s headers did not answer (%s)", lid, e)
            unreachable.append(lid)
            continue
        headers = parse_headers(head_result.content)
        if not headers:
            log.info("hefs: %s serves no cycles", lid)
            continue
        served.append(lid)
        have = await _stored_cycles(session, fp.id)
        missing = sorted({h.forecast_datetime for h in headers} - have)
        if not missing:
            continue
        log.info("hefs: %s has %d retained cycle(s), %d not stored", lid, len(headers), len(missing))
        by_cycle = {h.forecast_datetime: h for h in headers}
        for cycle in missing:
            head = by_cycle[cycle]
            try:
                ens_result = await fetch_ensemble(fetcher, session, location_id=lid, forecast_datetime=cycle)
            except FetchError as e:
                log.warning("hefs: %s cycle %s did not answer (%s)", lid, cycle.isoformat(), e)
                continue
            ensembles = parse_ensembles(ens_result.content)
            for ensemble in ensembles:
                if ensemble.header.forecast_datetime != cycle:
                    # The API answered with a cycle other than the one asked for. Refused rather
                    # than stored: silently accepting it would file one cycle's members under
                    # another cycle's issued_at, and every replay after that would be wrong.
                    raise ValueError(
                        f"hefs: asked {lid} for {cycle.isoformat()} and got "
                        f"{ensemble.header.forecast_datetime.isoformat()}"
                    )
                session.add(
                    DerivedFeature(
                        feature=FEATURE_MEMBERS,
                        valid_time=cycle,  # the row is about a cycle, not an instant
                        value=None,
                        values_json=_member_values(ensemble),
                        scope_kind="forecast_point",
                        scope_id=fp.id,
                        window=f"{_horizon_h(ensemble)}h",
                        issued_at=cycle,
                        computed_at=ens_result.fetched_at,
                        available_at=head.creation_datetime,
                        method_id=METHOD_MEMBERS,
                        product_id=PRODUCT_HEFS_ENSEMBLE,
                        unit=ensemble.header.units,
                        confidence_label="unknown",  # a faithful readout of an uncalibrated model
                        inputs=[{"table": "raw_artifact", "id": ens_result.artifact_id}],
                        raw_inputs_hash=ens_result.sha256,
                        raw_artifact_id=ens_result.artifact_id,
                    )
                )
                written += 1

        # The published quantiles are only served for the latest cycle, so they are collected once
        # per location per run rather than per cycle. An older cycle's quantiles are not
        # recoverable; the members are, and those are the irreplaceable part.
        try:
            q_result = await fetch_quantiles(fetcher, session, location_id=lid)
        except FetchError as e:
            log.warning("hefs: %s quantiles did not answer (%s)", lid, e)
            continue
        quantiles = parse_quantiles(q_result.content)
        cycle = quantiles.forecast_datetime or max(by_cycle)
        exists = (
            await session.execute(
                select(DerivedFeature.id).where(
                    DerivedFeature.feature == FEATURE_QUANTILES,
                    DerivedFeature.method_id == METHOD_QUANTILES,
                    DerivedFeature.scope_id == fp.id,
                    DerivedFeature.issued_at == cycle,
                )
            )
        ).scalar_one_or_none()
        if exists is not None:
            continue
        session.add(
            DerivedFeature(
                feature=FEATURE_QUANTILES,
                valid_time=cycle,
                value=None,
                values_json=_quantile_values(quantiles),
                scope_kind="forecast_point",
                scope_id=fp.id,
                issued_at=cycle,
                computed_at=q_result.fetched_at,
                available_at=quantiles.creation_datetime or by_cycle[cycle].creation_datetime
                if cycle in by_cycle
                else quantiles.creation_datetime,
                method_id=METHOD_QUANTILES,
                product_id=PRODUCT_HEFS_QUANTILES,
                unit=quantiles.units,
                confidence_label="unknown",
                inputs=[{"table": "raw_artifact", "id": q_result.artifact_id}],
                raw_inputs_hash=q_result.sha256,
                raw_artifact_id=q_result.artifact_id,
            )
        )
        written += 1

    await session.flush()
    if points and not served:
        raise NoHefsCyclesError(
            f"no HEFS location served a cycle: {len(unreachable)} of {len(points)} did not answer. "
            "Retry rather than recording a successful run that archived nothing — this provider is "
            "explicitly experimental, and a silent zero here means history is being lost."
        )
    if unreachable:
        log.warning("hefs: %d location(s) did not answer (%s)", len(unreachable), ", ".join(unreachable))
    return written


def _horizon_h(ensemble) -> int:
    if not ensemble.members or not ensemble.members[0].values:
        return 0
    times = [t for t, _ in ensemble.members[0].values]
    return int((times[-1] - times[0]).total_seconds() // 3600)
