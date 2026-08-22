# ADR-0013: Time-series storage — native partitioning first, TimescaleDB deferred

- Status: Accepted (2026-08-22; evidence in docs/research/backend-stack-and-scientific-tooling.json)
- Date: 2026-08-22

## Context
Expected volume: six to a few hundred stations × 2–5 variables × 96 values/day, plus forecast runs (dozens of points × 40 values × several runs/day), plus basin features (hundreds/day), plus ensemble members later. Tens of millions of rows/year at full Washington coverage — comfortably within PostgreSQL with monthly partitions and BRIN/B-tree indexes.

## Decision
Use native declarative partitioning (by month on `valid_time` / `issued_at`) managed by `pg_partman`, with BRIN indexes on time and B-tree on `(scope, variable, valid_time)`. Defer TimescaleDB; revisit when ensemble/gridded-derived row counts exceed ~1e9 or when continuous aggregates/compression would remove meaningful operational work. TimescaleDB's licensing (Apache core vs Timescale License features) must be reviewed before adoption.

## Evidence (retrieved 2026-08-22)
- PostgreSQL 18.6 is current stable (PG 19 at Beta 3); PostGIS 3.6.1 supports PG 12–18 (PG 19 only in 3.7.0 betas). Adopt PG 18.x + PostGIS 3.6.x; do not plan on PG 19 until PostGIS 3.7.0 final.
- PostgreSQL docs: the planner handles "up to a few thousand partitions fairly well" with pruning; monthly partitions give 12–36 per year-span. pg_partman 5.5.0 (2026-07-22) manages native partitioning with a background worker (note: BGW role now defaults to `partman_maintainer`).
- TimescaleDB 2.29.2 supports PG 16–18, but compression/columnstore, continuous aggregates, retention policies and background jobs are Community-edition (Tiger Data License) only; the Apache-2 edition is essentially hypertable chunking. TSL permits self-hosting for our own product but constrains managed hosting options.

## Consequences
No extension dependency beyond PostGIS; fewer operational surprises; a clear trigger for revisiting.
