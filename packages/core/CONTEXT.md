# packages/core — the spine

One job: give every other package the same settings, database session, object store, clock
rules, freshness arithmetic and the single knowledge-time read path. No science, no HTTP
endpoints, no provider-specific parsing.

## Inputs
- Environment: `CASCADE_DB_URL`, `CASCADE_RAW_DIR`, `CASCADE_CONTACT`, `CASCADE_CORS_ORIGINS`,
  `CASCADE_GEO_DIR` (`settings.py`).
- Reference data: `seed/stations.json` (verified seed stations/forecast points) and the geo
  fixtures under `tests/fixtures/geo/` (basins).

## Outputs
- `models.py` ORM tables for `docs/DOMAIN_MODEL.md` §2 at spike scope (append-only value tables).
- `fetch.py` `ArchivingFetcher`: allowlisted host, timeout, byte cap, UA, rate limit, and the
  raw payload archived (`objectstore.py`, sha256 keys) with a `RawArtifact` row BEFORE parsing.
- `freshness.py` computed at read time from `SourceProduct` cadence/grace; never stored.
- `knowledge.py` `as_known_at(session, T)`: the only read path for values (`available_at <= T`).
- `timeutils.py` aware-UTC parsing with offsets; `units.py` explicit pint conversions.

## Human check
Pick one observation row: its `raw_artifact_id` resolves to a file under `data/raw/` whose bytes
contain the value string, the dateTime with offset, and the qualifier you see on the row.
`available_at` equals `max(valid_time, retrieved_at)`. Datum on a stage row equals the NWPS
gauge-zero datum for that LID in `seed/stations.json`.
