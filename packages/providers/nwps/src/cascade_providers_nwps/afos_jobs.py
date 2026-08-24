"""Event Zero T3 loader: archived FLW/FLS crest statements -> ForecastRun/ForecastValue.

One archived AFOS transmission (docs/EVENT_ZERO.md §7 "Reconstruct from products") becomes
at most one ForecastRun per (product:nws-fls-crest, forecast point, issued_at), carrying
exactly one ForecastValue: the segment's Forecast-bullet crest at the H-VTEC crest time.

Bitemporal honesty (ADR-0010, docs/DATA_DOCTRINE.md §11):

- ``issued_at`` is the product's transmission time — FACT, from the IEM AFOS listing
  ``entered`` (== the R2 ``_manifest/afos/{PIL}.json`` ``issued_at``), never the VTEC
  event-begin time (EVENT_ZERO look-ahead audit item 6).
- ``available_at`` = retrieval time. For a 2026 backfill of December 2025 products
  ``available_at`` >> ``issued_at``, and that gap IS the honest record: ``as_known_at(T)``
  with T in December 2025 correctly returns UNKNOWN — we did not exist then. The Event
  Zero replay therefore selects these runs by ``issued_at`` window with ``as_of`` omitted.
- The "backfilled" surface for forecast runs is the product identity itself
  (``product:nws-fls-crest``, whose label states the reconstruction) plus the visible
  ``available_at`` >> ``issued_at`` gap; ForecastRun has no quality column to flag.

UNKNOWN over fabrication: a segment whose Forecast bullet matches no crest phrase, or
whose H-VTEC crest time is the all-zero token, stores nothing and is counted in the
report. Idempotent: the unique (product_id, fp_id, issued_at) key makes re-runs no-ops.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.models import ForecastPoint, ForecastRun, ForecastValue
from cascade_core.registry import PRODUCT_NWS_FLS_CREST
from cascade_core.timeutils import available_at
from cascade_providers_nwps.afos import parse_afos

JOB_BACKFILL_FLS = "nws.backfill_event_zero_fls"
ISSUER = "NWRFC via KSEW"


@dataclass
class AfosLoadReport:
    """Counts for the honesty ledger: everything skipped is named, nothing silently lost."""

    products_parsed: int = 0
    segments_seen: int = 0  # segments carrying an H-VTEC LID
    runs_written: int = 0
    values_written: int = 0
    skipped_existing: int = 0
    unknown_lids: Counter[str] = field(default_factory=Counter)  # LID -> segment count
    no_forecast_crest: Counter[str] = field(default_factory=Counter)  # UNKNOWN, per LID
    missing_crest_time: list[tuple[str, str]] = field(default_factory=list)  # (lid, product)
    wmo_mismatches: list[tuple[str, str]] = field(default_factory=list)  # (pil, detail)

    def summary(self) -> str:
        lines = [
            f"products parsed: {self.products_parsed}; segments with LID: {self.segments_seen}",
            f"runs written: {self.runs_written} (+{self.values_written} values); "
            f"already stored: {self.skipped_existing}",
            f"segments for LIDs without a seeded forecast point: "
            f"{sum(self.unknown_lids.values())} across {len(self.unknown_lids)} LIDs",
            f"segments with no parseable Forecast crest (stored as nothing, UNKNOWN): "
            f"{sum(self.no_forecast_crest.values())} {dict(self.no_forecast_crest)}",
            f"segments with crest value but all-zero H-VTEC crest time (refused): "
            f"{len(self.missing_crest_time)} {self.missing_crest_time}",
        ]
        if self.wmo_mismatches:
            lines.append(f"WMO header vs archive issued_at mismatches: {self.wmo_mismatches}")
        return "\n".join(lines)


async def forecast_points_by_lid(session: AsyncSession) -> dict[str, ForecastPoint]:
    rows = (await session.execute(select(ForecastPoint).order_by(ForecastPoint.id))).scalars()
    return {fp.lid: fp for fp in rows}


async def load_crest_products(
    session: AsyncSession,
    *,
    content: bytes,
    issued_at: datetime,
    retrieved_at: datetime,
    raw_artifact_id: int,
    fp_by_lid: dict[str, ForecastPoint],
    report: AfosLoadReport,
) -> int:
    """Store crest runs for one archived transmission (may hold several SOH-joined products).

    Returns rows written (runs + values). ``issued_at`` is the archive's transmission time
    for the whole transmission; the WMO header day/hour/minute is cross-checked and any
    disagreement is reported, never silently repaired.
    """
    written = 0
    for product in parse_afos(content):
        report.products_parsed += 1
        if not product.wmo_matches(issued_at):
            report.wmo_mismatches.append(
                (product.pil, f"WMO {product.wmo_ddhhmm} != listed {issued_at:%d%H%M}")
            )
        for seg in product.segments:
            lid = seg.lid
            if lid is None:  # headline or areal segment without H-VTEC
                continue
            report.segments_seen += 1
            fp = fp_by_lid.get(lid)
            if fp is None:
                report.unknown_lids[lid] += 1
                continue
            crest = seg.crest
            if crest is None:  # no Forecast bullet, or bullet matched nothing
                report.no_forecast_crest[lid] += 1
                continue
            if seg.hvtec is None or seg.hvtec.crest is None:
                # A run with zero values is refusable: no crest time, no row.
                report.missing_crest_time.append((lid, f"{product.pil} {product.wmo_ddhhmm}"))
                continue
            exists = (
                await session.execute(
                    select(ForecastRun.id).where(
                        ForecastRun.product_id == PRODUCT_NWS_FLS_CREST,
                        ForecastRun.fp_id == fp.id,
                        ForecastRun.issued_at == issued_at,
                    )
                )
            ).scalar_one_or_none()
            if exists is not None:
                report.skipped_existing += 1
                continue
            prev = (
                await session.execute(
                    select(ForecastRun)
                    .where(
                        ForecastRun.product_id == PRODUCT_NWS_FLS_CREST,
                        ForecastRun.fp_id == fp.id,
                        ForecastRun.issued_at < issued_at,
                    )
                    .order_by(ForecastRun.issued_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            is_stage = crest.unit == "ft"
            run = ForecastRun(
                product_id=PRODUCT_NWS_FLS_CREST,
                fp_id=fp.id,
                issued_at=issued_at,
                retrieved_at=retrieved_at,
                available_at=available_at(
                    valid_time=issued_at, retrieved_at=retrieved_at, issued_at=issued_at
                ),
                issuer=ISSUER,
                primary_variable="stage" if is_stage else "flow",
                unit=crest.unit,
                stage_unit="ft" if is_stage else None,
                flow_unit=None if is_stage else "cfs",
                datum=(fp.datums[0] if fp.datums else None) if is_stage else None,
                raw_artifact_id=raw_artifact_id,
                supersedes_run_id=None if prev is None else prev.id,
            )
            session.add(run)
            await session.flush()
            session.add(
                ForecastValue(
                    run_id=run.id,
                    valid_time=seg.hvtec.crest,
                    stage=crest.value if is_stage else None,
                    flow=None if is_stage else crest.value,
                )
            )
            report.runs_written += 1
            report.values_written += 1
            written += 2
    await session.flush()
    return written
