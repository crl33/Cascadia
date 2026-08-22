"""Async SQLAlchemy 2 engine/session factory. One engine per process; sessions are short-lived.

SQLite (aiosqlite) in the spike, PostgreSQL later: nothing here is dialect-specific except the
`create_schema` convenience used instead of migrations at spike scope.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from cascade_core.models import Base


def make_engine(db_url: str) -> AsyncEngine:
    if db_url.startswith("sqlite+aiosqlite:///") and not db_url.endswith(":memory:"):
        Path(db_url.removeprefix("sqlite+aiosqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(db_url, future=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_schema(engine: AsyncEngine) -> None:
    """Spike-scope schema creation (Alembic arrives with PostGIS, docs/ARCHITECTURE.md §4)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
