# packages/core — the spine

One job: give every other package the same settings, database session, object store, clock
rules, freshness arithmetic and the single knowledge-time read path. No science, no HTTP
endpoints, no provider-specific parsing.

## Inputs
- Environment: `CASCADE_DB_URL`, `CASCADE_RAW_DIR`, `CASCADE_CONTACT`, `CASCADE_CORS_ORIGINS`,
  `CASCADE_GEO_DIR` (`settings.py`).
- Reference data: `seed/stations.json` (verified seed stations/forecast points) plus the named
  addenda beside it (`seed/p3_surfaces.json`: NWM reach ids, the unregulated Sauk gauge, the
  per-basin susceptibility gauge + confidence ceiling + caveat), and the geo fixtures under
  `tests/fixtures/geo/` (basins). Each addendum carries its own `_provenance` verification date;
  `seed.py` merges them and raises on a key that names no seeded basin/point/station.

## Outputs
- `models.py` ORM tables for `docs/DOMAIN_MODEL.md` §2 at spike scope (append-only value tables).
- `models.py` also carries `derived_feature` (every number Cascadia computed, with `method_id`,
  the upstream `product_id`, `raw_artifact_id`/`inputs` and the three times — append-only) and
  `grid_mask` (basin x grid definition -> fractional weights, keyed by the grid hash so a
  changed provider grid MISSES instead of mis-aggregating).
- `fetch.py` `ArchivingFetcher`: allowlisted host, timeout, byte cap, UA, rate limit, per-call
  `Accept` (JSON, GRIB2 and RDB share this path), and the raw payload archived
  (`objectstore.py`, sha256 keys) with a `RawArtifact` row BEFORE parsing. `PROVIDER_HOSTS` is
  the ceiling — every host any adapter may contact, in one reviewable place; each adapter still
  passes its own narrow `allowed_hosts`. `retention_class` records the object-store lifecycle
  policy a payload was written under, so the row can outlive expired bytes.
- `freshness.py` computed at read time from `SourceProduct` cadence/grace; never stored.
- `knowledge.py` `as_known_at(session, T)`: the only read path for values (`available_at <= T`),
  including `derived_features()` / `latest_derived_feature()` — knowledge-filtered on
  `available_at` only, because a derived forecast feature is legitimately valid in the future.
- `timeutils.py` aware-UTC parsing with offsets; `units.py` explicit pint conversions.

## Human check
Pick one observation row: its `raw_artifact_id` resolves to a file under `data/raw/` whose bytes
contain the value string, the dateTime with offset, and the qualifier you see on the row.
`available_at` equals `max(valid_time, retrieved_at)`. Datum on a stage row equals the NWPS
gauge-zero datum for that LID in `seed/stations.json`.
