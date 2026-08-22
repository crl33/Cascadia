# ADR-0001: PostgreSQL + PostGIS as the primary database (replacing MongoDB)

- Status: Accepted
- Date: 2026-08-22

## Context
V1 used MongoDB/Motor purely as a key-value cache of the latest snapshot per station (FACT, `v1/backend/lib/cache.py`). The platform's data is relational (basins ⟶ reaches ⟶ stations ⟶ forecast points), temporal (append-only observations, superseded forecast runs, revisions), and geospatial (polygons, flowlines, zonal statistics, upstream/downstream navigation). Hindcasting needs bitemporal queries (`as_known_at`). Nothing in the requirements benefits from schemaless documents.

## Decision
Use PostgreSQL (16 or newer) with PostGIS as the single system of record for structured and geospatial data. Use native declarative partitioning for high-volume time tables. Use JSONB only for small, read-whole attributes (hypsometry, rule curves, drivers).

## Alternatives considered
- Keep MongoDB — no spatial joins/zonal ops, weak time-series semantics, no constraints to enforce doctrine.
- A dedicated time-series DB (InfluxDB) beside a relational DB — two systems of record; provenance joins become application code.
- DuckDB/Parquet only — excellent for analysis, not for a concurrently written operational store; used later for analytics exports instead.

## Consequences
One dependency for dev and prod; constraints enforce the data doctrine; PostGIS answers the basin-centric questions in SQL. Requires migrations discipline (Alembic) and partition management (`pg_partman`). Rasters stay out of the database (ADR-0004).
