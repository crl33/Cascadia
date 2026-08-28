# ADR-0019: The worker runs as `ingest_writer`; partition DDL goes through one definer function

- Status: Accepted
- Date: 2026-08-28
- Completes: the role separation `scripts/sql/roles.sql` drafted in P0 (api_reader landed
  2026-08-28 the same way; this closes the writer half).

## Context

Append-only is doctrine (DATA_DOCTRINE §13-14), but until now only convention enforced it: the
worker connected as the database owner, so any bug could UPDATE history. The one genuine
blocker to a least-privilege writer was the monthly partition-maintenance job:
`CREATE TABLE ... PARTITION OF observation` requires ownership of the parent table, which an
append-only role must never have.

Two designs were considered:

- **Migrator-run partitioning**: move the monthly job out of the worker into an operator-run
  or platform-cron alembic step running as owner. Rejected: it removes the job from the
  `job_run` health machinery — the exact "hand-kept list" failure /system/health was built to
  end — and adds an operational step someone must remember on the 1st of the month.
- **SECURITY DEFINER on the existing function**: `cascade_ensure_month_partitions` is already
  the ONLY partition-DDL path, already parameterized (`format %I/%L`, bound dates, no string
  interpolation), and already idempotent. Making it `SECURITY DEFINER` (owner: the migrator)
  with a pinned `search_path` lets `ingest_writer` execute exactly this one DDL capability and
  nothing else, while the job stays in the worker, in `job_run`, in health.

## Decision

1. Migration 0006 recreates `cascade_ensure_month_partitions` with `SECURITY DEFINER` and
   `SET search_path = public, pg_temp` (the standard definer hardening: no schema-shadowing of
   `observation` or `to_regclass`). The function body is byte-identical.
2. `ingest_writer` is a LOGIN role: SELECT+INSERT on all tables; USAGE+SELECT on sequences;
   UPDATE only on the seed-merged reference tables and `job_run` (the drafted roles.sql list);
   full DML on the `procrastinate_*` queue tables (the queue's own bookkeeping legitimately
   updates and deletes); EXECUTE on the partition function. DELETE nowhere else. No DDL.
3. The worker's `CASCADE_DB_URL` and `CASCADE_QUEUE_DB_URL` point at `ingest_writer`
   (`postgresql+psycopg://…?sslmode=require` — the driver-scheme rule from the runbook).
   Migrations and `apply-queue-schema` remain owner-run operations with explicitly passed
   URLs; the seed keeps working through the writer because reference-table UPDATE is granted.

## Consequences

- A worker bug that tries to UPDATE an observation, a forecast value, a derived feature or an
  alert now fails at the database, loudly, instead of silently editing history.
- The definer function is the single point where writer privilege exceeds its grants; its
  safety rests on the properties it already had (fixed statement shape, `%I/%L` quoting,
  bound arguments) plus the pinned search_path. Any future partition-shape change edits this
  one function through a migration, as before.
- Grants for tables created by FUTURE migrations arrive via `ALTER DEFAULT PRIVILEGES ...
  FOR ROLE neondb_owner`, run once with the grants; a migration that adds a table needs no
  grant step of its own.
- Rollback is two Railway variables (point the worker back at the owner URL).
