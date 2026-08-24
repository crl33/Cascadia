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
    ForecastPoint,
    ForecastRun,
    ForecastValue,
    JobRun,
    Observation,
    SourceProduct,
    Station,
    Threshold,
)
from cascade_core.timeutils import to_utc


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

    async def latest_forecast_run(self, fp_id: str) -> ForecastRun | None:
        q = (
            select(ForecastRun)
            .where(ForecastRun.fp_id == fp_id, ForecastRun.available_at <= self.as_of)
            .order_by(ForecastRun.issued_at.desc(), ForecastRun.id.desc())
            .limit(1)
        )
        return (await self.session.execute(q)).scalar_one_or_none()

    async def forecast_runs(self, fp_id: str, issued_from: datetime, issued_until: datetime) -> list[ForecastRun]:
        """Known-at-T forecast runs with issued_at inside [issued_from, issued_until], ascending.

        The Event Zero forecast-evolution read: select by ISSUED time, knowledge-filter by
        available_at — a backfilled run (available_at ≫ issued_at) stays invisible at any T
        before its retrieval (ADR-0010)."""
        q = (
            select(ForecastRun)
            .where(ForecastRun.fp_id == fp_id, ForecastRun.available_at <= self.as_of)
            .where(ForecastRun.issued_at >= to_utc(issued_from), ForecastRun.issued_at <= to_utc(issued_until))
            .order_by(ForecastRun.issued_at, ForecastRun.id)
        )
        return list((await self.session.execute(q)).scalars().all())

    async def forecast_values(self, run_id: int) -> list[ForecastValue]:
        q = select(ForecastValue).where(ForecastValue.run_id == run_id).order_by(ForecastValue.valid_time)
        return list((await self.session.execute(q)).scalars().all())

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

    async def product_freshness_anchor(self, product_id: str) -> tuple[datetime | None, datetime | None]:
        """(latest valid/issued time, latest retrieved_at) known at T for a product, for /system/health."""
        if product_id == "product:usgs-iv":
            q = select(func.max(Observation.valid_time), func.max(Observation.retrieved_at)).where(
                Observation.product_id == product_id, Observation.available_at <= self.as_of
            )
        elif product_id == "product:nwps-forecast":
            q = select(func.max(ForecastRun.issued_at), func.max(ForecastRun.retrieved_at)).where(
                ForecastRun.product_id == product_id, ForecastRun.available_at <= self.as_of
            )
        else:
            q = select(func.max(Threshold.retrieved_at), func.max(Threshold.retrieved_at)).where(
                Threshold.product_id == product_id, Threshold.effective_from <= self.as_of
            )
        v, r = (await self.session.execute(q)).one()
        fix = lambda x: None if x is None else (x if x.tzinfo else x.replace(tzinfo=self.as_of.tzinfo))  # noqa: E731
        return fix(v), fix(r)


def as_known_at(session: AsyncSession, as_of: datetime) -> Knowledge:
    return Knowledge(session=session, as_of=to_utc(as_of))
