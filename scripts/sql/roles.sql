-- Application roles for the Cascadia Papsukkal PostgreSQL database.
--
-- Run MANUALLY by an operator, after scripts/migrate.sh, against the target database:
--   psql "$SOME_ADMIN_URL" -f scripts/sql/roles.sql
-- Neon manages login roles its own way (console/API-created roles, neon_superuser):
-- these are NOLOGIN grant-holder roles only — on Neon (or anywhere), attach them to the
-- platform's login roles with e.g.  GRANT ingest_writer TO <worker login role>;
-- Idempotent: safe to re-run at any time. No credentials appear in this file.
--
-- Doctrine (docs/DATA_DOCTRINE.md §13–14, ADR-0001): value tables are append-only.
-- ingest_writer gets INSERT+SELECT everywhere, UPDATE only on reference/operational
-- tables, and DELETE nowhere. api_reader is read-only ("one database, two roles",
-- docs/ARCHITECTURE.md §1).
--
-- APPLIED STATE (2026-08-28): `api_reader` exists in production Neon as a LOGIN role
-- (created directly — Neon accepts SQL CREATE ROLE ... LOGIN from neondb_owner, so the
-- NOLOGIN-plus-attach indirection above is unnecessary for it; the IF NOT EXISTS guard
-- makes this file safe to re-run over that). Grants + ALTER DEFAULT PRIVILEGES (for
-- neondb_owner) are live and PROVEN: SELECT answers, INSERT is refused
-- (InsufficientPrivilege). The API prefers CASCADE_API_DB_URL (Settings.effective_api_db_url).
-- `ingest_writer` remains grants-on-paper: the monthly partition-maintenance job issues DDL
-- (CREATE TABLE ... PARTITION OF), which no non-owner can run against the parent — adopting
-- it needs a migrator-run partition path or a SECURITY DEFINER helper (ADR to write).

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ingest_writer') THEN
        CREATE ROLE ingest_writer NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_reader') THEN
        CREATE ROLE api_reader NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO ingest_writer, api_reader;

-- Read side: the API only reads and projects.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO api_reader;

-- Write side: append-only by default...
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO ingest_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ingest_writer;

-- ...with UPDATE only where the worker maintains rows in place: seed-merged reference
-- tables, job bookkeeping, and regenerable display geometry. Never on value tables
-- (observation, forecast_run, forecast_value, threshold, raw_artifact).
GRANT UPDATE ON basin, station, forecast_point, data_source, source_product,
                basin_geometry, job_run
TO ingest_writer;

-- Objects created later by the role running migrations inherit the same shape.
-- (ALTER DEFAULT PRIVILEGES applies to objects created by the role executing this
-- statement — run this file as the same role that runs scripts/migrate.sh.)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO api_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT ON TABLES TO ingest_writer;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ingest_writer;
