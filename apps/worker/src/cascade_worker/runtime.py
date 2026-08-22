"""Worker runtime: settings -> engine/session factory/object store/fetcher, and `run_job`, which
records every job start/finish/outcome in job_run (docs/ARCHITECTURE.md §3 "Health")."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from cascade_core.db import make_engine, make_session_factory
from cascade_core.fetch import ArchivingFetcher, HostRateLimiter
from cascade_core.models import JobRun
from cascade_core.objectstore import LocalFilesystemStore
from cascade_core.settings import Settings
from cascade_core.timeutils import utcnow

JobFn = Callable[[AsyncSession, ArchivingFetcher], Awaitable[int]]


@dataclass
class Runtime:
    settings: Settings
    engine: AsyncEngine
    sessions: async_sessionmaker[AsyncSession]
    fetcher: ArchivingFetcher
    clock: Callable[[], datetime] = utcnow

    @classmethod
    def build(cls, settings: Settings, *, engine: AsyncEngine | None = None, fetcher: ArchivingFetcher | None = None, clock: Callable[[], datetime] = utcnow) -> Runtime:
        engine = engine or make_engine(settings.db_url)
        fetcher = fetcher or ArchivingFetcher(
            store=LocalFilesystemStore(settings.raw_dir),
            user_agent=settings.user_agent,
            limiter=HostRateLimiter(min_interval_s=0.5, max_concurrency=2),
            clock=clock,
        )
        return cls(settings=settings, engine=engine, sessions=make_session_factory(engine), fetcher=fetcher, clock=clock)


async def run_job(rt: Runtime, name: str, fn: JobFn) -> JobRun:
    async with rt.sessions() as book:
        jr = JobRun(job=name, started_at=rt.clock())
        book.add(jr)
        await book.commit()
        try:
            async with rt.sessions() as session:
                rows = await fn(session, rt.fetcher)
                await session.commit()
            jr.ok, jr.rows_written = True, rows
        except Exception as e:  # the failure is the record; never re-raise out of the scheduler
            jr.ok, jr.error = False, f"{type(e).__name__}: {e}"[:1000]
        jr.finished_at = rt.clock()
        await book.commit()
        return jr
