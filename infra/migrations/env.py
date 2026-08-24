"""Alembic environment for Cascadia Papsukkal.

URL resolution: ``CASCADE_ALEMBIC_URL`` (override for scratch databases / CI), else
``CASCADE_DB_URL`` — the runtime URL works unchanged because the ``+psycopg`` driver is
sync/async dual; no async/sync URL swapping is needed. No URL is ever stored in a file.

Autogenerate hygiene: ``station.geom`` / ``forecast_point.geom`` are migration-owned and
deliberately absent from the ORM metadata (SQLite compatibility, see
``cascade_core.models.PG_ONLY_GEOMETRY_COLUMNS``), and PostGIS owns ``spatial_ref_sys``;
`include_object` keeps autogenerate from proposing to drop any of them.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from cascade_core.models import PG_ONLY_GEOMETRY_COLUMNS, Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    url = os.environ.get("CASCADE_ALEMBIC_URL") or os.environ.get("CASCADE_DB_URL")
    if not url:
        raise RuntimeError(
            "No database URL: set CASCADE_ALEMBIC_URL (preferred for migrations) or "
            "CASCADE_DB_URL, e.g. postgresql+psycopg://USER:PASS@HOST:PORT/DB "
            "(values from your environment/secret store; never from a file in this repo)."
        )
    return url


def include_object(object_, name, type_, reflected, compare_to) -> bool:
    if type_ == "table" and name == "spatial_ref_sys":
        return False  # PostGIS-owned catalog table
    if type_ == "column" and reflected and object_.table is not None:
        if name in PG_ONLY_GEOMETRY_COLUMNS.get(object_.table.name, ()):
            return False  # migration-owned geometry column, intentionally unmapped
    return True


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of executing (alembic upgrade head --sql)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url(), poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_object=include_object,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
