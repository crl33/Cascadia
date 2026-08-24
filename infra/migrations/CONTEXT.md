# infra/migrations — the PostgreSQL schema, versioned

Alembic owns the PostgreSQL/PostGIS schema. `cascade_core.db.create_schema` is only the
SQLite/dev shortcut; every real database goes through here.

## Run

```
alembic -c infra/migrations/alembic.ini upgrade head     # or: scripts/migrate.sh
```

URL from the environment, never from a file: `CASCADE_ALEMBIC_URL` (preferred for
migrations/CI scratch databases), else `CASCADE_DB_URL`. The runtime `+psycopg` URL works
unchanged — psycopg 3 is sync/async dual, so no driver swapping.

## Shape (revision 0001)

- Everything `cascade_core.models.Base.metadata` defines, plus `CREATE EXTENSION postgis`.
- `basin_geometry(basin_id, lod)` MULTIPOLYGON/4326 + GiST; `station.geom` /
  `forecast_point.geom` POINT/4326 nullable + GiST. The two point columns are
  **migration-owned and unmapped** in the ORM (SQLite compatibility); the registry is
  `cascade_core.models.PG_ONLY_GEOMETRY_COLUMNS`, honored by env.py's `include_object`.
- `observation` is partitioned by RANGE(valid_time), monthly: composite PK
  `(id, valid_time)`, identity `id`, partition-local unique natural key, no FK on
  `revision_of` (see the revision's docstring). Partitions 2025-11..2027-01 premade +
  `observation_default`.

## Partitions going forward

`pg_partman` is the intended manager on Neon (ADR-0013). Where the extension is absent
(local docker PostGIS, CI), call the fallback shipped in revision 0001:

```
SELECT cascade_ensure_month_partitions(DATE '2027-02-01', DATE '2027-06-01');
```

Keep premaking ahead of ingestion — with `observation_default` in place, a new partition can
only be created while the default holds no rows in its range.

## Roles

`scripts/sql/roles.sql` (run manually, idempotent): NOLOGIN `ingest_writer` / `api_reader`
with append-only grants per DATA_DOCTRINE §14. Neon manages login roles its own way; grant
these roles to its login roles there.

## Testing

`tests/integration/test_pg_migration.py` (marker `pg`, skipped unless `CASCADE_TEST_PG_URL`
is set) migrates a scratch database via the CLI, seeds it, and asserts geometry counts,
partition count, and partition routing.
