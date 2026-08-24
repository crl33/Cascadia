"""Partition-horizon maintenance: keep `observation`'s premade monthly partitions ahead of
ingestion.

Migration 0001 premakes partitions 2025-11 .. 2027-01 plus a DEFAULT partition. Rows past
the premade horizon would silently land in the DEFAULT partition — and once the DEFAULT
holds rows for a month, creating that month's real partition fails. This module keeps the
horizon rolling: from the current month through :data:`MONTHS_AHEAD` months ahead, by
calling the SQL function ``cascade_ensure_month_partitions(from_month, to_month)`` that the
migration installed (idempotent; returns the number of partitions created).

``run_ensure_partitions`` is JobFn-shaped ``(session, fetcher) -> rows`` so the queue task
wraps it with ``run_job`` exactly like the provider jobs: every monthly run leaves a
job_run row (health surface), and both date arguments are bound parameters — no SQL string
interpolation anywhere.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher
from cascade_core.timeutils import utcnow

JOB_NAME = "maintenance.ensure_observation_partitions"
#: 00:03 UTC on the 1st of every month — off the top-of-hour/minute stampede.
CRON = "3 0 1 * *"
#: Keep partitions premade through this many months past the current one.
MONTHS_AHEAD = 13


def month_window(today: date, months_ahead: int = MONTHS_AHEAD) -> tuple[date, date]:
    """(first day of ``today``'s month, first day of the month ``months_ahead`` later)."""
    start = today.replace(day=1)
    total = start.month - 1 + months_ahead
    return start, date(start.year + total // 12, total % 12 + 1, 1)


async def run_ensure_partitions(session: AsyncSession, fetcher: ArchivingFetcher) -> int:
    """Extend the observation partition horizon; returns partitions created (0 = all present).

    ``fetcher`` is unused (no network) — the signature matches JobFn so ``run_job`` records
    the outcome like any other job. The caller (run_job / the test) commits the session;
    partition DDL in PostgreSQL is transactional.
    """
    from_month, to_month = month_window(utcnow().date())
    result = await session.execute(
        text("SELECT cascade_ensure_month_partitions(:from_month, :to_month)"),
        {"from_month": from_month, "to_month": to_month},
    )
    return int(result.scalar_one())
