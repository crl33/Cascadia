# ADR-0004: S3-compatible object storage for raw payloads and gridded science products

- Status: Accepted
- Date: 2026-08-22

## Context
GRIB2/NetCDF/COG/LiDAR products are large, immutable, and read as whole files or byte ranges by scientific tooling. Raw provider payloads must be archived before parsing (provenance, re-parsing after bugs, hindcast reproducibility).

## Decision
All raw payloads and gridded/3D products go to S3-API object storage. Dev/CI: SeaweedFS `weed mini` (Apache-2.0) or Garage; production: Cloudflare R2 (zero egress) or AWS S3. **Not MinIO**: its repository was archived read-only on 2026-04-25 ("THIS REPOSITORY IS NO LONGER MAINTAINED"; community edition source-only; last binary 2025-10-15) — FACT, docs/research/backend-stack-and-scientific-tooling.json. Client: `obstore` (Rust object_store bindings; sync+async; S3-compatible endpoints) for the data path, boto3 for admin scripts. PostgreSQL holds an index (`RawArtifact`, `GridProduct`) with keys, hashes, times and bounding boxes. Raw payload keys are content-addressed (sha256); grid keys are deterministic by product/issued/valid/variable. Lifecycle rules: raw JSON forever (compressed); full-cycle grids for a rolling window plus event windows forever; basin aggregates forever in PostgreSQL; derivatives (tiles) regenerable.

## Alternatives considered
- PostGIS raster — possible but poor fit for multi-GB products and for xarray/GDAL tooling.
- Local disk — not durable or shareable across workers.

## Consequences
R2 lacks object versioning/tagging: compensate with immutable content-addressed keys and deterministic product paths (never overwrite). Cloud-agnostic; replays can re-read exactly what was fetched. Needs bucket versioning and an egress-aware tiling strategy (COG + range reads; CDN in front of derivatives).
