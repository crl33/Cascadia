# ADR-0020: Observed weather fields are stored as quantized window rasters in Postgres

- Status: Accepted
- Date: 2026-08-28
- Serves: CINEMATIC_ROADMAP C3b (`precip_observed` as a rendered field, "the map absorbing
  what the panel carries" — design direction 2026-08-28).

## Context

C3b needs the MRMS QPE hour rendered as a spatial field, not a basin mean. The worker already
decodes the full CONUS grid every hour (`mrms.fetch_qpe`) and then keeps only six basin-mean
rows; the spatial plane it computed them from is thrown away, and the archived grib in the
object store is unreachable from the API by design (the API reads the database and the geo
fixtures, nothing else — the read path has no eccodes, no numpy, and no business acquiring
them per request).

The rendered field only needs the seeded world: the basin-union bbox padded to a fixed window
(W−122.87 S46.63 E−120.50 N49.46, 236×283 = 66,788 cells at MRMS's own 0.01°). Quantized to
0.1 mm in uint16 and gzip-compressed, a typical hour is 1–40 KB (dry hours are almost all
zeros); 72 h of retention is at most ~3 MB — noise against the deployment's storage
arithmetic.

Alternatives considered:

- **Tile pipeline to the object store (COG/PNG pyramid).** The roadmap's eventual shape for
  multi-field weather cinema (C4), but it adds a serving surface (bucket auth or public
  bucket), a raster toolchain, and cache invalidation — for a single-window field whose whole
  document is smaller than one PNG tile. Rejected for C3b; nothing below forecloses it.
- **Decode the archived grib on API request.** Puts eccodes+numpy and a 7000×3500 decode in
  the read path for a document the worker already held in memory at ingest. Rejected.
- **values_json on `derived_feature`.** The row shape (one scalar + covariates per scope) is
  wrong for a 67k-cell plane, JSONB doubles the bytes, and the budget-guarded readers that
  scan `derived_feature` must never risk pulling a raster by accident. Rejected.

## Decision

1. A dedicated `field_raster` table (migration 0007): `(product_id, field, valid_time)`
   unique; `available_at` for knowledge-time reads; grid spec columns (`lo1`, `la1`, `dlon`,
   `dlat`, `nx`, `ny` — the window's own georeferencing, never assumed from a constant);
   `scale` (quantization step, 0.1 mm); `cells` BYTEA = gzip of little-endian uint16,
   row-major from the NW corner (MRMS's own order); `max_value` for `display_range`;
   `raw_artifact_id` back to the archived grib.
2. `mrms.fetch_qpe` cuts the window from the plane it already decoded, quantizes (missing and
   no-coverage sentinels → 0xFFFF, distinct from any real value), and INSERTs alongside the
   basin means — same idempotency key, same knowledge times. No second fetch, no second decode.
3. `ingest_writer` gets INSERT+SELECT and — uniquely among data tables — DELETE on
   `field_raster` only, so the same job can prune beyond retention (72 h). The append-only
   doctrine protects *observations of record*; a display raster whose source grib stays
   archived is a derived convenience, and re-deriving it is `scripts/` work, not history loss.
4. The API serves the newest row at or before `as_of` as
   `GET /viz/fields/precip_observed?as_of=` — spec + base64(gzip(uint16)) + scale + unit +
   `display_range` + provenance ref, truth `observation`. UNKNOWN is a 404 with a reason,
   never an empty raster.

## Consequences

- The web renders real weather geometry for the first time; the renderer draws one
  `SingleTileImageryProvider` per refresh, no tile tree.
- A new table means roles.sql, the migration chain, and the pg suite all move together; the
  DELETE grant is the first non-queue DELETE `ingest_writer` holds and is documented inline in
  roles.sql with this ADR as the reason.
- Retention is a worker concern (the same job that writes prunes); a longer archive remains
  possible later from the raw gribs without schema change.
- C4's multi-field/tile future supersedes this shape when it arrives; the contract document
  deliberately carries its own grid spec so clients never bake the window in.
