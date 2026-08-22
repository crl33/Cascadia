# ADR-0005: Generic Observation / ForecastValue / DerivedFeature model; no per-variable schema

- Status: Accepted
- Date: 2026-08-22

## Context
V1 froze a contract with named slots (`snow_water_equivalent`, `precipitation_24h`, `soil_moisture`, `basin_tension_score`) before most existed (FACT, `v1/backend/lib/types.py`). Every new variable would have been a schema change across backend and frontend.

## Decision
Model values generically: `Observation(scope, product, variable, value, unit, valid_time, retrieved_at, available_at, quality, revision_of, raw_artifact)`, `ForecastRun`/`ForecastValue`, and `DerivedFeature(feature, scope, window, value, unit, method_id, inputs, percentile)`. Variables and features are registry rows. "States" (BasinState, SnowState, …) are API projections, not tables. See `docs/DOMAIN_MODEL.md`.

## Alternatives considered
- Wide tables per domain (one column per variable) — simple queries, but schema churn and sparse rows; rejected.
- Entity-attribute-value with untyped values — the generic model is EAV with typed units, registry-constrained variables and provenance; the discipline is in the registry and constraints.

## Consequences
Adding a variable or feature is data + a parser/method, not a migration. Queries pivot at read time; hot projections can be materialized later without changing the write model.
