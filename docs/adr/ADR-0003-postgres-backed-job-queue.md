# ADR-0003: PostgreSQL-backed job queue and scheduler for ingestion

- Status: Accepted (2026-08-22; evidence in docs/research/backend-stack-and-scientific-tooling.json)
- Date: 2026-08-22

## Context
Jobs must be idempotent, retried with backoff, rate-aware per provider, schedulable (cron and event-triggered), safe across multiple worker processes, and observable. Introducing Redis/RabbitMQ adds an operational dependency only for queuing.

## Decision
Use a PostgreSQL-backed task queue with built-in periodic scheduling and retries (leading candidate: Procrastinate; alternative: PgQueuer), running inside `apps/worker`. Job identity = idempotency key `(product_id, scope, issued_at|valid_time)`; duplicate enqueues are deduplicated by a unique constraint. Per-host rate limits are enforced in the provider adapters (token buckets stored in PostgreSQL advisory-locked rows), not in the queue.

## Alternatives considered
- Celery + Redis — mature but adds a broker and is weak on idempotency semantics.
- APScheduler in-process — no durable queue, no multi-process safety.
- Dramatiq/arq — require Redis.
- Prefect/Dagster — orchestration platforms; reconsider for batch reprocessing and hindcast runs in Phase 6.

## Evidence (retrieved 2026-08-22)
- Procrastinate 3.9.0 (2026-06-20, MIT): psycopg3 async connector, LISTEN/NOTIFY + polling, retry strategies, DB-coordinated periodic tasks ("deferring only happens once per period, even with multiple workers"), `queueing_lock` for enqueue-time dedupe and `lock` for per-resource serialization; stalled-job recovery and finished-job cleanup are periodic tasks we must write (docs). PgQueuer 1.3.2 is the runner-up (built-in Prometheus/dashboard, automatic stalled re-pickup, `dedupe_key`) but younger with a single primary maintainer. Celery has no PostgreSQL broker; Dramatiq/arq need Redis; APScheduler 4 is pre-release ("do NOT use in production"); Prefect/Dagster are orchestration products, not job engines (Dagster OSS remains a credible later layer for asset lineage/backfills).
- Operational rules adopted: keep task bodies as plain functions (cheap to switch queues); run the stalled-job retry task every 10 minutes; partition or prune `procrastinate_jobs` on a schedule.

## Consequences
Single infrastructure dependency; jobs are rows a human can inspect. Throughput ceiling of a Postgres queue is far above needs (hundreds of jobs/hour). Revisit if job volume exceeds ~10k/hour or if sub-second latency is required.
