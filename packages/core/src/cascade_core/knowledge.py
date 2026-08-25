"""`as_known_at(session, T)` — the only knowledge-time read path (ADR-0010, DATA_DOCTRINE §11).

Every read returns only rows with `available_at <= T` (thresholds: `effective_from <= T`) and,
for observations, the highest revision that existed at T. API projections and hydrology assembly
go through this object; direct table access in a replay path is a review failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.models import (
    Basin,
    DerivedFeature,
    ForecastPoint,
    ForecastRun,
    ForecastValue,
    JobRun,
    Observation,
    RawArtifact,
    SourceProduct,
    Station,
    Threshold,
)
from cascade_core.registry import METADATA_ONLY_PRODUCTS, PRODUCTS, SOURCES
from cascade_core.timeutils import to_utc

# Which products are an OFFICIAL forecast, resolved from the registry rather than listed here
# (cascade_core.registry is the only place a source's SourceKind is declared). P3 puts a second
# forecast product — the NWM medium-range ensemble — into `forecast_run`, so "the latest run at
# this point" stopped being a synonym for "the official forecast at this point"
# (docs/research/p3-surfaces-design-2026-08-24.md §3.4 defect 1).
_SOURCE_KIND: dict[str, str] = {str(s["id"]): str(s["kind"]) for s in SOURCES}
OFFICIAL_FORECAST_PRODUCTS: frozenset[str] = frozenset(
    str(p["id"]) for p in PRODUCTS if _SOURCE_KIND.get(str(p["source_id"])) == "OFFICIAL_FORECAST"
)


@dataclass(frozen=True)
class FreshnessAnchor:
    """The timestamps `/system/health` computes a product's freshness from, plus which table they
    came from. `kind` is part of the answer, not decoration: "current because values landed" and
    "current because bytes were fetched" are different claims about the same product."""

    kind: str
    valid_time: datetime | None
    retrieved_at: datetime | None


@dataclass(frozen=True)
class Knowledge:
    session: AsyncSession
    as_of: datetime

    async def products(self) -> dict[str, SourceProduct]:
        rows = (await self.session.execute(select(SourceProduct))).scalars().all()
        return {p.id: p for p in rows}

    async def basins(self) -> list[Basin]:
        return list((await self.session.execute(select(Basin).order_by(Basin.id))).scalars().all())

    async def basin(self, basin_id: str) -> Basin | None:
        return await self.session.get(Basin, basin_id)

    async def forecast_points(self, basin_id: str | None = None) -> list[ForecastPoint]:
        q = select(ForecastPoint).order_by(ForecastPoint.id)
        if basin_id is not None:
            q = q.where(ForecastPoint.basin_id == basin_id)
        return list((await self.session.execute(q)).scalars().all())

    async def forecast_point_by_lid(self, lid: str) -> ForecastPoint | None:
        return (await self.session.execute(select(ForecastPoint).where(ForecastPoint.lid == lid))).scalar_one_or_none()

    async def station(self, station_id: str) -> Station | None:
        return await self.session.get(Station, station_id)

    async def stations(self) -> list[Station]:
        return list((await self.session.execute(select(Station).order_by(Station.id))).scalars().all())

    async def observations(self, station_id: str, variable: str, since: datetime, until: datetime | None = None) -> list[Observation]:
        """Known-at-T observations in [since, until], one row per valid_time (highest known revision)."""
        until = self.as_of if until is None else min(to_utc(until), self.as_of)
        q = (
            select(Observation)
            .where(Observation.station_id == station_id, Observation.variable == variable)
            .where(Observation.available_at <= self.as_of)
            .where(Observation.valid_time >= to_utc(since), Observation.valid_time <= until)
            .order_by(Observation.valid_time, Observation.revision_seq)
        )
        best: dict[datetime, Observation] = {}
        for row in (await self.session.execute(q)).scalars():
            best[row.valid_time] = row  # later revision_seq overwrites earlier within the ordering
        return [best[k] for k in sorted(best)]

    async def latest_observation(self, station_id: str, variable: str, lookback: timedelta = timedelta(days=14)) -> Observation | None:
        rows = await self.observations(station_id, variable, since=self.as_of - lookback)
        return rows[-1] if rows else None

    async def latest_forecast_run(
        self, fp_id: str, *, product_ids: frozenset[str] | None = OFFICIAL_FORECAST_PRODUCTS
    ) -> ForecastRun | None:
        """The latest run known at T at this point, restricted to ``product_ids``.

        ``forecast_run`` holds more than one forecast product: from P3 the NWM medium-range
        ensemble lands in the same table as the NWRFC official forecast. Ordering by issued_at
        across every product would hand back whichever run happens to be newest, so on any cycle
        where the model beat the RFC the caller displaying "the official forecast" would be
        showing a model run (design §3.4 defect 1 — the fix is the filter, not a convention).

        The default is therefore the registry-resolved OFFICIAL set, not "everything": a caller
        that says nothing gets the official forecast, which is what every existing caller means.
        Pass an explicit set to read another product, or ``product_ids=None`` to deliberately
        ask for the latest run of ANY product (the caller then owns badging it correctly)."""
        q = select(ForecastRun).where(ForecastRun.fp_id == fp_id, ForecastRun.available_at <= self.as_of)
        if product_ids is not None:
            q = q.where(ForecastRun.product_id.in_(sorted(product_ids)))
        q = q.order_by(ForecastRun.issued_at.desc(), ForecastRun.id.desc()).limit(1)
        return (await self.session.execute(q)).scalar_one_or_none()

    async def forecast_runs(
        self,
        fp_id: str,
        issued_from: datetime,
        issued_until: datetime,
        *,
        product_ids: frozenset[str] | None = None,
    ) -> list[ForecastRun]:
        """Known-at-T forecast runs with issued_at inside [issued_from, issued_until], ascending.

        The Event Zero forecast-evolution read: select by ISSUED time, knowledge-filter by
        available_at — a backfilled run (available_at ≫ issued_at) stays invisible at any T
        before its retrieval (ADR-0010).

        ``product_ids`` defaults to None = every product, because this is the *evolution* read:
        it returns runs of every kind side by side and each item carries its own product id and
        ProvenanceRef, so a model run shows up as a model run instead of being hidden. Pass a
        set when a caller needs one product's history only."""
        q = (
            select(ForecastRun)
            .where(ForecastRun.fp_id == fp_id, ForecastRun.available_at <= self.as_of)
            .where(ForecastRun.issued_at >= to_utc(issued_from), ForecastRun.issued_at <= to_utc(issued_until))
        )
        if product_ids is not None:
            q = q.where(ForecastRun.product_id.in_(sorted(product_ids)))
        q = q.order_by(ForecastRun.issued_at, ForecastRun.id)
        return list((await self.session.execute(q)).scalars().all())

    async def forecast_values(self, run_id: int) -> list[ForecastValue]:
        q = select(ForecastValue).where(ForecastValue.run_id == run_id).order_by(ForecastValue.valid_time)
        return list((await self.session.execute(q)).scalars().all())

    async def derived_features(
        self,
        feature: str,
        scope_id: str,
        *,
        method_id: str | None = None,
        window: str | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        latest_per_valid_time: bool = False,
    ) -> list[DerivedFeature]:
        """Known-at-T derived features, ascending by (valid_time, available_at, id).

        Knowledge filtering is on ``available_at`` only. ``valid_time`` is deliberately NOT
        clamped to ``as_of``: a derived forecast feature (72-hour basin QPF) is legitimately
        valid in the future, and clamping it would silently hide the forecast half of the
        surface. Pass ``valid_until`` when a caller genuinely wants present-or-past rows.

        ``method_id`` and ``window`` filter only when given (``None`` means "do not filter",
        not "match NULL"). Recomputation is append-only — a new run under the same method is a
        new row — so ``latest_per_valid_time=True`` keeps the last-known row per valid_time,
        the same rule ``observations`` uses for revisions.
        """
        q = (
            select(DerivedFeature)
            .where(DerivedFeature.feature == feature, DerivedFeature.scope_id == scope_id)
            .where(DerivedFeature.available_at <= self.as_of)
            .order_by(DerivedFeature.valid_time, DerivedFeature.available_at, DerivedFeature.id)
        )
        if method_id is not None:
            q = q.where(DerivedFeature.method_id == method_id)
        if window is not None:
            q = q.where(DerivedFeature.window == window)
        if valid_from is not None:
            q = q.where(DerivedFeature.valid_time >= to_utc(valid_from))
        if valid_until is not None:
            q = q.where(DerivedFeature.valid_time <= to_utc(valid_until))
        rows = list((await self.session.execute(q)).scalars().all())
        if not latest_per_valid_time:
            return rows
        best: dict[datetime, DerivedFeature] = {}
        for row in rows:  # ordering means the last write for a valid_time wins
            best[row.valid_time] = row
        return [best[k] for k in sorted(best)]

    async def latest_derived_feature(
        self,
        feature: str,
        scope_id: str,
        *,
        method_id: str | None = None,
        window: str | None = None,
        lookback: timedelta = timedelta(days=30),
    ) -> DerivedFeature | None:
        """The most recent known-at-T row for a feature/scope with valid_time <= T.

        Bounded by ``lookback`` so a surface reading a stale table gets None (and says why)
        instead of quietly presenting a value from an arbitrary distance in the past.
        """
        rows = await self.derived_features(
            feature,
            scope_id,
            method_id=method_id,
            window=window,
            valid_from=self.as_of - lookback,
            valid_until=self.as_of,
            latest_per_valid_time=True,
        )
        return rows[-1] if rows else None

    async def thresholds(self, fp_id: str) -> dict[str, Threshold]:
        """Latest known-at-T official threshold row per category."""
        q = (
            select(Threshold)
            .where(Threshold.fp_id == fp_id, Threshold.effective_from <= self.as_of)
            .order_by(Threshold.effective_from, Threshold.id)
        )
        out: dict[str, Threshold] = {}
        for row in (await self.session.execute(q)).scalars():
            out[row.category] = row
        return out

    async def latest_job_runs(self) -> dict[str, tuple[JobRun | None, JobRun | None]]:
        """Per job name: (last run, last successful run), restricted to runs started at or before T."""
        q = select(JobRun).where(JobRun.started_at <= self.as_of).order_by(JobRun.started_at, JobRun.id)
        out: dict[str, tuple[JobRun | None, JobRun | None]] = {}
        for row in (await self.session.execute(q)).scalars():
            last, last_ok = out.get(row.job, (None, None))
            out[row.job] = (row, row if row.ok else last_ok)
        return out

    async def product_freshness_anchors(self) -> dict[str, FreshnessAnchor]:
        """Per product id: the freshness anchor known at T, for /system/health.

        Table-agnostic on purpose. A product's values land in whichever table suits them —
        `observation`, `forecast_run`, `threshold` or `derived_feature` — and the old
        product-id-by-product-id branch covered exactly three ids, so every product added after
        the spike silently anchored on the threshold table and read `missing` forever. One
        grouped query per table, unioned, means a newly registered product is anchored the
        moment its first row lands (pg-migration-verification-2026-08-24 §P3.6 finding C).

        The value anchor is the time the SOURCE says the information is about, which for anything
        issued in cycles is the issue time, not the valid time: a forecast valid 72 h from now is
        not fresh because its valid_time is in the future. Hence `issued_at` where there is one
        and `valid_time` otherwise.

        `raw_artifact` is a fallback for the registry's `METADATA_ONLY_PRODUCTS` and nothing else,
        and `kind` says which was used. Those products store no value rows at all (station
        metadata) and would otherwise read `missing` while being fetched every day. Every other
        product is judged on its rows, because bytes can keep arriving while the step that turns
        them into values fails — and `nbm.build_grid_masks` fetches a `product:nbm-v5-core` file
        of its own, so an unrestricted fallback answered `current` for a product whose own job had
        never once succeeded (measured 2026-08-25, §P3.9 of the pg-migration verification).
        """
        anchors: dict[str, FreshnessAnchor] = {}
        fix = lambda x: None if x is None else (x if x.tzinfo else x.replace(tzinfo=self.as_of.tzinfo))  # noqa: E731

        def newer(a: datetime | None, b: datetime | None) -> datetime | None:
            return b if a is None else (a if b is None else max(a, b))

        async def collect(kind: str, value_col, retrieved_col, table, knowledge_col) -> None:
            q = select(table.product_id, func.max(value_col), func.max(retrieved_col)).where(knowledge_col <= self.as_of).group_by(table.product_id)
            for pid, v, r in (await self.session.execute(q)).all():
                if pid is None:
                    continue
                have = anchors.get(pid)
                if kind == "raw_artifact" and (have is not None or pid not in METADATA_ONLY_PRODUCTS):
                    # Value rows win, and for a product that is SUPPOSED to yield values, having
                    # none is `missing` — not `current` on the strength of bytes that never
                    # parsed. Only the registry's metadata-only products anchor on bytes.
                    continue
                if have is None:
                    anchors[pid] = FreshnessAnchor(kind=kind, valid_time=fix(v), retrieved_at=fix(r))
                else:  # the same product writes into more than one table: latest of both
                    anchors[pid] = FreshnessAnchor(
                        kind=f"{have.kind}+{kind}",
                        valid_time=newer(have.valid_time, fix(v)),
                        retrieved_at=newer(have.retrieved_at, fix(r)),
                    )

        await collect("observation", Observation.valid_time, Observation.retrieved_at, Observation, Observation.available_at)
        await collect("forecast_run", ForecastRun.issued_at, ForecastRun.retrieved_at, ForecastRun, ForecastRun.available_at)
        await collect("threshold", Threshold.retrieved_at, Threshold.retrieved_at, Threshold, Threshold.effective_from)
        await collect("derived_feature", func.coalesce(DerivedFeature.issued_at, DerivedFeature.valid_time), DerivedFeature.computed_at, DerivedFeature, DerivedFeature.available_at)
        await collect("raw_artifact", RawArtifact.fetched_at, RawArtifact.fetched_at, RawArtifact, RawArtifact.fetched_at)
        return anchors


def as_known_at(session: AsyncSession, as_of: datetime) -> Knowledge:
    return Knowledge(session=session, as_of=to_utc(as_of))
