# ADR-0002: Python modular monolith + independent worker processes

- Status: Accepted
- Date: 2026-08-22

## Context
Ingestion must run continuously and independently of UI traffic (the V1 request-driven model is rejected). The science is Python-native (xarray, rasterio, cfgrib, shapely, pint). The team is small; operational weight must stay low.

## Decision
One Python workspace (`packages/*`) with two process types: `apps/api` (FastAPI, Pydantic v2, SQLAlchemy 2 async, read-mostly) and `apps/worker` (scheduler + jobs). No microservices; package boundaries are the architecture. Workers and API share `packages/` but the API never imports provider clients.

## Alternatives considered
- Separate services per provider — premature; deployment and observability cost without benefit at this scale.
- Ingestion inside the API process (background tasks) — couples availability of the UI to ingestion and breaks under multiple API replicas.
- A workflow platform (Airflow/Prefect/Dagster) as the core — useful later for batch reprocessing; too heavy as the primary runtime.

## Consequences
Simple deployment (two containers + DB + object store). Clear rule: science in packages, IO at the edges. The package layout must be protected by import-linting (e.g. `import-linter`) so boundaries do not erode.
