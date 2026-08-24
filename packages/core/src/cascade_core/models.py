"""ORM models for docs/DOMAIN_MODEL.md §2 at spike scope.

Append-only value tables (observation, forecast_run, forecast_value, threshold): corrections are
new rows with revision/supersession links; nothing is updated or deleted by application code.
All timestamps are stored as UTC and returned aware (see `UTCDateTime`).

Geospatial (PostgreSQL/PostGIS only; the same models must keep working on SQLite):

- `basin_geometry` (below) carries ``info={"pg_only": True}`` on its table; `create_schema`
  skips such tables on SQLite, while the Alembic migration (infra/migrations) creates them on
  PostgreSQL.
- ``station.geom`` and ``forecast_point.geom`` (geometry(POINT, 4326), nullable) exist ONLY in
  the PostgreSQL database, owned by the Alembic migration and deliberately unmapped here so the
  SQLite tables — and every ORM SELECT/merge — stay geometry-free. They are populated from
  lon/lat by `cascade_core.seed` and read via SQL. `PG_ONLY_GEOMETRY_COLUMNS` is the registry
  Alembic's env.py uses to keep autogenerate from proposing their removal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

# Migration-owned geometry columns that intentionally do NOT appear on the ORM classes.
# table name -> column names. Read by infra/migrations/env.py (autogenerate include_object).
PG_ONLY_GEOMETRY_COLUMNS: dict[str, tuple[str, ...]] = {
    "station": ("geom",),
    "forecast_point": ("geom",),
}


class UTCDateTime(TypeDecorator[datetime]):
    """Aware-UTC in Python, naive-UTC in the database (portable across SQLite and PostgreSQL)."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetime rejected; all timestamps must be aware")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


class Basin(Base):
    __tablename__ = "basin"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    regulation_class: Mapped[str] = mapped_column(String)
    outlet_fp_id: Mapped[str | None] = mapped_column(String)
    huc8: Mapped[list[str]] = mapped_column(JSON, default=list)
    centroid: Mapped[list[float] | None] = mapped_column(JSON)
    bbox: Mapped[list[float] | None] = mapped_column(JSON)
    geometry_ref: Mapped[str | None] = mapped_column(String)
    regulated_by: Mapped[list[str]] = mapped_column(JSON, default=list)


class BasinGeometry(Base):
    """Basin polygons per display LOD (PostGIS MULTIPOLYGON, EPSG:4326). PostgreSQL-only:
    the ``pg_only`` info flag keeps `create_schema` from creating it on SQLite; the Alembic
    migration creates it on PostgreSQL. Regenerable from tests/fixtures/geo seed GeoJSON
    (docs/DOMAIN_MODEL.md §3: display geometries are materialized, regenerable)."""

    __tablename__ = "basin_geometry"
    __table_args__ = (
        CheckConstraint("lod IN ('state', 'basin')", name="ck_basin_geometry_lod"),
        Index("ix_basin_geometry_geom", "geom", postgresql_using="gist"),
        {"info": {"pg_only": True}},
    )
    basin_id: Mapped[str] = mapped_column(ForeignKey("basin.id"), primary_key=True)
    lod: Mapped[str] = mapped_column(String, primary_key=True)
    geom: Mapped[Any] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False), nullable=False
    )


class Station(Base):
    # PostgreSQL also carries `geom geometry(POINT, 4326)` (migration-owned, unmapped;
    # see PG_ONLY_GEOMETRY_COLUMNS above). lon/lat remain the authoritative seed values.
    __tablename__ = "station"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # station:usgs:12200500
    agency: Mapped[str] = mapped_column(String)
    external_id: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    basin_id: Mapped[str | None] = mapped_column(ForeignKey("basin.id"))
    lon: Mapped[float | None] = mapped_column(Float)
    lat: Mapped[float | None] = mapped_column(Float)
    vertical_datum: Mapped[str | None] = mapped_column(String)  # gauge-zero datum per NWPS
    time_zone: Mapped[str | None] = mapped_column(String)


class ForecastPoint(Base):
    # PostgreSQL also carries `geom geometry(POINT, 4326)` (migration-owned, unmapped;
    # see PG_ONLY_GEOMETRY_COLUMNS above). lon/lat remain the authoritative seed values.
    __tablename__ = "forecast_point"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # fp:nwps:MVEW1
    lid: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    station_id: Mapped[str | None] = mapped_column(ForeignKey("station.id"))
    basin_id: Mapped[str | None] = mapped_column(ForeignKey("basin.id"))
    upstream_lids: Mapped[list[str]] = mapped_column(JSON, default=list)
    downstream_lids: Mapped[list[str]] = mapped_column(JSON, default=list)
    reach_id: Mapped[str | None] = mapped_column(String)
    datums: Mapped[list[str]] = mapped_column(JSON, default=list)
    rfc: Mapped[str | None] = mapped_column(String)
    wfo: Mapped[str | None] = mapped_column(String)
    in_service: Mapped[bool] = mapped_column(Boolean, default=True)
    lon: Mapped[float | None] = mapped_column(Float)
    lat: Mapped[float | None] = mapped_column(Float)


class DataSource(Base):
    __tablename__ = "data_source"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # src:usgs-nwis-iv
    authority: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String)  # SourceKind value
    base_url: Mapped[str] = mapped_column(String)
    docs_url: Mapped[str | None] = mapped_column(String)


class SourceProduct(Base):
    __tablename__ = "source_product"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # product:usgs-iv
    source_id: Mapped[str] = mapped_column(ForeignKey("data_source.id"))
    label: Mapped[str] = mapped_column(String)
    variables: Mapped[list[str]] = mapped_column(JSON, default=list)
    expected_cadence_seconds: Mapped[int] = mapped_column(Integer)
    grace_seconds: Mapped[int] = mapped_column(Integer)


class RawArtifact(Base):
    __tablename__ = "raw_artifact"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha256: Mapped[str] = mapped_column(String, index=True)
    object_key: Mapped[str] = mapped_column(String)
    product_id: Mapped[str] = mapped_column(ForeignKey("source_product.id"))
    fetched_at: Mapped[datetime] = mapped_column(UTCDateTime)
    request_url: Mapped[str] = mapped_column(String)
    bytes: Mapped[int] = mapped_column(Integer)
    http_status: Mapped[int] = mapped_column(Integer)
    content_type: Mapped[str | None] = mapped_column(String)


class Observation(Base):
    """On PostgreSQL this table is partitioned by RANGE (valid_time), monthly, with the
    composite primary key (id, valid_time) — the partition key must be in the PK — while
    ``id`` keeps identity semantics, and ``revision_of`` carries no FK (a FK cannot target
    the non-unique ``id`` alone on a partitioned table). The ORM mapping below (single-column
    PK, plain FK on SQLite) is compatible with both shapes for append-only writes."""

    __tablename__ = "observation"
    __table_args__ = (UniqueConstraint("product_id", "station_id", "variable", "valid_time", "revision_seq"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("station.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("source_product.id"))
    variable: Mapped[str] = mapped_column(String)  # stage | flow
    value: Mapped[float | None] = mapped_column(Float)  # None when quality says sentinel/unparseable
    unit: Mapped[str] = mapped_column(String)
    datum: Mapped[str | None] = mapped_column(String)
    valid_time: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime)
    available_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    quality: Mapped[list[str]] = mapped_column(JSON, default=list)
    qualifier_raw: Mapped[str | None] = mapped_column(String)
    revision_of: Mapped[int | None] = mapped_column(ForeignKey("observation.id"))
    revision_seq: Mapped[int] = mapped_column(Integer, default=0)
    raw_artifact_id: Mapped[int] = mapped_column(ForeignKey("raw_artifact.id"))


class ForecastRun(Base):
    __tablename__ = "forecast_run"
    __table_args__ = (UniqueConstraint("product_id", "fp_id", "issued_at"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("source_product.id"))
    fp_id: Mapped[str] = mapped_column(ForeignKey("forecast_point.id"), index=True)
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime)
    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime)
    available_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    issuer: Mapped[str] = mapped_column(String)
    primary_variable: Mapped[str] = mapped_column(String)  # stage | flow
    unit: Mapped[str] = mapped_column(String)  # unit of the primary variable as stored
    stage_unit: Mapped[str | None] = mapped_column(String)
    flow_unit: Mapped[str | None] = mapped_column(String)  # always cfs after normalization
    datum: Mapped[str | None] = mapped_column(String)
    raw_artifact_id: Mapped[int] = mapped_column(ForeignKey("raw_artifact.id"))
    supersedes_run_id: Mapped[int | None] = mapped_column(ForeignKey("forecast_run.id"))


class ForecastValue(Base):
    __tablename__ = "forecast_value"
    __table_args__ = (UniqueConstraint("run_id", "valid_time"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("forecast_run.id"), index=True)
    valid_time: Mapped[datetime] = mapped_column(UTCDateTime)
    stage: Mapped[float | None] = mapped_column(Float)
    flow: Mapped[float | None] = mapped_column(Float)


class Threshold(Base):
    __tablename__ = "threshold"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fp_id: Mapped[str] = mapped_column(ForeignKey("forecast_point.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("source_product.id"))
    category: Mapped[str] = mapped_column(String)  # action | minor | moderate | major
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    basis: Mapped[str] = mapped_column(String)  # stage | flow
    datum: Mapped[str | None] = mapped_column(String)
    source_kind: Mapped[str] = mapped_column(String)  # OFFICIAL_FORECAST only; CONFIGURED never reaches hazard
    effective_from: Mapped[datetime] = mapped_column(UTCDateTime, index=True)  # = knowledge time of this row
    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime)
    raw_artifact_id: Mapped[int] = mapped_column(ForeignKey("raw_artifact.id"))


class JobRun(Base):
    __tablename__ = "job_run"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    ok: Mapped[bool | None] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(String)
    rows_written: Mapped[int] = mapped_column(Integer, default=0)
