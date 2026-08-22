"""Idempotent NWPS jobs.

thresholds (every 6 h): gauge -> refresh forecast-point metadata (datums, topology, reach, in
service) and append Threshold rows ONLY when a category's (value, unit, basis, datum) differs
from the latest stored row (new values are new rows; unchanged values write nothing).
forecast (every 30 min): stageflow -> one ForecastRun per (product, fp, issued_at); an already
stored issuance is a no-op; a newer issuance records `supersedes_run_id`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.models import ForecastPoint, ForecastRun, ForecastValue, Station, Threshold
from cascade_core.registry import PRODUCT_NWPS_FORECAST, PRODUCT_NWPS_THRESHOLDS
from cascade_providers_nwps.client import fetch_gauge, fetch_stageflow
from cascade_providers_nwps.normalize import forecast_from_stageflow, thresholds_from_gauge
from cascade_providers_nwps.parser import parse_gauge, parse_stageflow

JOB_THRESHOLDS = "nwps.fetch_thresholds"
JOB_FORECAST = "nwps.fetch_forecast"
CADENCE_THRESHOLDS_SECONDS = 6 * 3600
CADENCE_FORECAST_SECONDS = 30 * 60


async def _points(session: AsyncSession) -> list[ForecastPoint]:
    return list((await session.execute(select(ForecastPoint).order_by(ForecastPoint.id))).scalars().all())


async def run_fetch_thresholds(session: AsyncSession, fetcher: ArchivingFetcher) -> int:
    written = 0
    for fp in await _points(session):
        result = await fetch_gauge(fetcher, session, fp.lid)
        g = parse_gauge(result.content)
        fp.reach_id = f"reach:nwm:{g.reach_id}" if g.reach_id else fp.reach_id
        fp.upstream_lids = [g.upstream_lid] if g.upstream_lid else []
        fp.downstream_lids = [g.downstream_lid] if g.downstream_lid else []
        fp.datums = list(g.datums) or fp.datums
        fp.rfc, fp.wfo, fp.in_service = g.rfc or fp.rfc, g.wfo or fp.wfo, g.in_service
        if fp.station_id and g.datum:
            station = await session.get(Station, fp.station_id)
            if station is not None and station.vertical_datum != g.datum:
                station.vertical_datum = g.datum
        latest: dict[str, Threshold] = {}
        q = select(Threshold).where(Threshold.fp_id == fp.id).order_by(Threshold.effective_from, Threshold.id)
        for row in (await session.execute(q)).scalars():
            latest[row.category] = row
        for rec in thresholds_from_gauge(g):
            prev = latest.get(rec.category)
            if prev is not None and (prev.value, prev.unit, prev.basis, prev.datum) == (rec.value, rec.unit, rec.basis, rec.datum):
                continue
            session.add(
                Threshold(
                    fp_id=fp.id,
                    product_id=PRODUCT_NWPS_THRESHOLDS,
                    category=rec.category,
                    value=rec.value,
                    unit=rec.unit,
                    basis=rec.basis,
                    datum=rec.datum,
                    source_kind="OFFICIAL_FORECAST",
                    effective_from=result.fetched_at,
                    retrieved_at=result.fetched_at,
                    raw_artifact_id=result.artifact_id,
                )
            )
            written += 1
    await session.flush()
    return written


async def run_fetch_forecast(session: AsyncSession, fetcher: ArchivingFetcher) -> int:
    written = 0
    for fp in await _points(session):
        result = await fetch_stageflow(fetcher, session, fp.lid)
        sf = parse_stageflow(result.content)
        datum = fp.datums[0] if fp.datums else None
        rec = forecast_from_stageflow(sf.forecast, retrieved_at=result.fetched_at, issuer=fp.rfc or "NWRFC", datum=datum)
        if rec is None:
            continue
        exists = (
            await session.execute(
                select(ForecastRun.id).where(ForecastRun.product_id == PRODUCT_NWPS_FORECAST, ForecastRun.fp_id == fp.id, ForecastRun.issued_at == rec.issued_at)
            )
        ).scalar_one_or_none()
        if exists is not None:
            continue
        prev = (
            await session.execute(
                select(ForecastRun).where(ForecastRun.fp_id == fp.id, ForecastRun.product_id == PRODUCT_NWPS_FORECAST).order_by(ForecastRun.issued_at.desc()).limit(1)
            )
        ).scalar_one_or_none()
        run = ForecastRun(
            product_id=PRODUCT_NWPS_FORECAST,
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
            session.add(ForecastValue(run_id=run.id, valid_time=v.valid_time, stage=v.stage, flow=v.flow))
        written += 1 + len(rec.values)
    await session.flush()
    return written
