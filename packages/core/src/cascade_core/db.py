"""Async SQLAlchemy 2 engine/session factory. One engine per process; sessions are short-lived.

SQLite (aiosqlite) for offline tests and local spikes; PostgreSQL via the dual sync/async
``+psycopg`` driver for real deployments. The PostgreSQL schema is owned by Alembic
(``infra/migrations``, applied by ``scripts/migrate.sh``); `create_schema` remains the
SQLite/dev convenience and skips tables flagged ``info={"pg_only": True}`` (PostGIS geometry
tables plain SQLite cannot hold). Called against an already-migrated PostgreSQL database it is
a checkfirst no-op.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cascade_core.models import Base


def make_engine(db_url: str) -> AsyncEngine:
    if db_url.startswith("sqlite+aiosqlite:///") and not db_url.endswith(":memory:"):
        Path(db_url.removeprefix("sqlite+aiosqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    if db_url.startswith("postgresql"):
        # Small-service sizing: a few persistent connections per process with modest burst
        # headroom; pre-ping + recycle so idle-dropped connections (managed Postgres,
        # PgBouncer idle timeouts) heal instead of surfacing as request errors.
        return create_async_engine(
            db_url,
            future=True,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_recycle=1800,
        )
    return create_async_engine(db_url, future=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_schema(engine: AsyncEngine) -> None:
    """Dev/test schema creation (SQLite). PostgreSQL schema is Alembic-owned; here this is a
    checkfirst no-op for existing tables and never creates ``pg_only`` (PostGIS) tables."""
    tables = [t for t in Base.metadata.sorted_tables if not t.info.get("pg_only")]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
