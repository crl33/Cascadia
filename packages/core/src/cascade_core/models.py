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
from sqlalchemy.dialects import postgresql
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


# JSON that becomes JSONB on PostgreSQL and stays plain JSON on SQLite. Used by the tables
# added in migration 0002 (docs/research/p3-surfaces-design-2026-08-24.md §1.6 specifies JSONB);
# the 0001 tables keep plain JSON — changing their column type is a schema change, not this one.
JSONVariant = JSON().with_variant(postgresql.JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class Basin(Base):
    """A basin plus the CONFIGURED operational metadata the seed owns.

    ``susceptibility_gauge_id`` names the station whose flow percentile stands in for basin
    wetness (p3-surfaces-design §2.3): on a regulated reach, flow is an operator decision and
    not a basin state, so the gauge is chosen per basin and is deliberately NOT always the
    outlet. ``susceptibility_confidence_ceiling`` is the highest ConfidenceLabel that gauge may
    ever justify, and ``susceptibility_note`` is the sentence that must be rendered with it.
    All three are CONFIGURED: they select and caveat an observation, they never become one.
    Like ``outlet_fp_id``, the gauge id carries no FK — station.basin_id already points the
    other way and a second FK would make the seed flush order circular.
    """

    __tablename__ = "basin"
    __table_args__ = (
        CheckConstraint(
            "susceptibility_confidence_ceiling IS NULL OR "
            "susceptibility_confidence_ceiling IN ('high', 'moderate', 'low', 'unknown')",
            name="ck_basin_susceptibility_ceiling",
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    regulation_class: Mapped[str] = mapped_column(String)
    outlet_fp_id: Mapped[str | None] = mapped_column(String)
    huc8: Mapped[list[str]] = mapped_column(JSON, default=list)
    centroid: Mapped[list[float] | None] = mapped_column(JSON)
    bbox: Mapped[list[float] | None] = mapped_column(JSON)
    geometry_ref: Mapped[str | None] = mapped_column(String)
    regulated_by: Mapped[list[str]] = mapped_column(JSON, default=list)
    susceptibility_gauge_id: Mapped[str | None] = mapped_column(String)  # station:usgs:12189500
    susceptibility_confidence_ceiling: Mapped[str | None] = mapped_column(String)
    susceptibility_note: Mapped[str | None] = mapped_column(String)


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
    # MEASURED tidal class: "FLUVIAL" | "TIDAL". NULL means nobody has measured this station's
    # semidiurnal amplitude, and rate of rise REFUSES rather than assuming it is fluvial — a
    # tide injects a false rate no estimator removes (research/trend-estimator-selection §5).
    # Set only from a measurement against a coastal reference with a non-tidal control
    # (research/tidal-gauge-verification-2026-08-26.md §3).
    tidal_class: Mapped[str | None] = mapped_column(String)


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
    # Object-store retention policy this artifact was written under (DATA_DOCTRINE §13):
    # NULL = keep indefinitely; "gridded-90d" = the R2 lifecycle rule may expire the bytes.
    # The row always survives, so a provenance popover can say the grid expired rather than 404.
    retention_class: Mapped[str | None] = mapped_column(String)


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


class DerivedFeature(Base):
    """A number Cascadia Papsukkal computed, with the chain back to what it was computed from
    (docs/DOMAIN_MODEL.md §2.3, p3-surfaces-design §1.6).

    Append-only, exactly like the observation/forecast value tables: a recomputation is a new
    row, never an update, and a method change is a new ``method_id`` and therefore a new
    identity (DATA_DOCTRINE §8). Nothing here is a probability; ``value``/``percentile`` are
    method outputs whose trustworthiness is carried by ``method_id`` + ``confidence_label``.

    Provenance columns, all of which the assembler needs to build a ProvenanceRef without
    hardcoding anything: ``method_id`` (what computed it), ``product_id`` (the upstream
    SourceProduct whose bytes it came from — NULL for a pure-Cascade derivation, and the only
    honest way to resolve ``source_kind`` from the registry rather than assuming it),
    ``raw_artifact_id`` / ``inputs`` / ``raw_inputs_hash`` (which bytes and rows), and the
    three times (``valid_time`` when it is true, ``issued_at`` for a model cycle,
    ``available_at`` when Cascadia first knew it — the knowledge-time filter reads this one).

    Not partitioned in v0: at the measured volumes (~73k rows/month, p3-surfaces-design §8) it
    does not need to be, and ADR-0013 says partition when measured, not before.
    """

    __tablename__ = "derived_feature"
    __table_args__ = (
        UniqueConstraint(
            "method_id", "feature", "scope_id", "window", "valid_time", "issued_at",
            name="uq_derived_feature_identity",
            # window and issued_at are legitimately NULL (a present-state feature has no
            # window; an observed-derived feature has no model cycle). Without this, PostgreSQL
            # treats NULLs as distinct and the identity constraint would not bite exactly where
            # it matters most. (SQLite has no equivalent; the offline suite is single-writer.)
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(
            "confidence_label IN ('high', 'moderate', 'low', 'unknown')",
            name="ck_derived_feature_confidence",
        ),
        Index("ix_derived_feature_scope_time", "scope_id", "feature", "valid_time"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature: Mapped[str] = mapped_column(String)  # basin_qpf_72h_p50 | streamflow_doy_percentile
    scope_kind: Mapped[str] = mapped_column(String)  # basin | forecast_point | station | reach
    scope_id: Mapped[str] = mapped_column(String)  # basin:skagit | fp:nwps:MVEW1
    window: Mapped[str | None] = mapped_column(String)  # 24h | 48h | 72h | 14d | None
    valid_time: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    issued_at: Mapped[datetime | None] = mapped_column(UTCDateTime)  # model cycle; None if observed-derived
    computed_at: Mapped[datetime] = mapped_column(UTCDateTime)
    available_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    method_id: Mapped[str] = mapped_column(String)  # method:basin-qpf@1.0.0
    product_id: Mapped[str | None] = mapped_column(ForeignKey("source_product.id"))
    value: Mapped[float | None] = mapped_column(Float)
    values_json: Mapped[dict[str, Any] | None] = mapped_column(JSONVariant)  # e.g. a percentile ladder
    unit: Mapped[str] = mapped_column(String)
    percentile: Mapped[float | None] = mapped_column(Float)
    climatology_ref: Mapped[str | None] = mapped_column(String)  # usgs-ogc-daily:12189500:1929-2026
    confidence_label: Mapped[str] = mapped_column(String, default="unknown", server_default="unknown")
    quality: Mapped[list[str]] = mapped_column(JSONVariant, default=list)
    inputs: Mapped[list[dict[str, Any]]] = mapped_column(JSONVariant, default=list)  # [{"table":..,"id":..}]
    raw_inputs_hash: Mapped[str | None] = mapped_column(String)
    raw_artifact_id: Mapped[int | None] = mapped_column(ForeignKey("raw_artifact.id"))


class GridMask(Base):
    """Basin x grid definition -> fractional cell weights (p3-surfaces-design §1.4).

    ``grid_definition_hash`` is a hash of the grid definition the mask was built against (for
    GRIB2, Section 3). It is part of the primary key on purpose: if the provider silently
    changes its grid, the lookup misses and the aggregation job must refuse and report UNKNOWN
    instead of area-weighting the wrong cells. Regenerable reference data, not a value row.
    """

    __tablename__ = "grid_mask"
    basin_id: Mapped[str] = mapped_column(ForeignKey("basin.id"), primary_key=True)
    grid_definition_hash: Mapped[str] = mapped_column(String, primary_key=True)
    method_id: Mapped[str] = mapped_column(String)  # method:basin-grid-mask@1.0.0
    cells: Mapped[list[list[float]]] = mapped_column(JSONVariant)  # [[flat_index, weight], ...]
    cell_count: Mapped[int] = mapped_column(Integer)
    masked_area_km2: Mapped[float] = mapped_column(Float)
    polygon_source: Mapped[str] = mapped_column(String)  # basins_seed_full.geojson.gz@<sha256>
    computed_at: Mapped[datetime] = mapped_column(UTCDateTime)


class JobRun(Base):
    __tablename__ = "job_run"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    ok: Mapped[bool | None] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(String)
    rows_written: Mapped[int] = mapped_column(Integer, default=0)
