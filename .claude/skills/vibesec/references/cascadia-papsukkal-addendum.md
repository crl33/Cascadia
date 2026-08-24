# VibeSec addendum — Cascadia Papsukkal threat model

Read after `SKILL.md`. This file covers what a generic web-app checklist misses for a
scientific ingestion platform: the attack surface is mostly *upstream providers, expensive
geospatial compute, and trust labeling*, not user accounts.

## 1. Provider adapters are SSRF-shaped by construction

Every adapter (`packages/providers/*`) makes outbound HTTP to NOAA/USGS/NRCS/USACE/AWS hosts.

- Base URLs are **compile-time constants**, never request parameters, never config read from
  the database, never derived from provider responses (a `next` link in a payload must be
  validated against the adapter's allowlisted host before it is followed).
- Adapters follow at most N redirects and re-validate the host on every hop.
- Adapters set a hard timeout, a max response size, and a `User-Agent` that identifies
  Cascadia Papsukkal with a contact address (NWS API requires one; others rate-limit by it).
- Raw payloads are archived to object storage **before** parsing; parsing bugs must not lose
  data, and a malicious payload must not be able to reach the database unparsed.
- Parsers are fixture-tested for malformed/oversized/sentinel inputs. A provider returning
  `-999999`, `-9999`, `NaN`, `null`, or a string where a number is expected must produce a
  quality flag, never a crash and never a silently-wrong number.

## 2. Scientific file parsers are untrusted-input parsers

GRIB2, NetCDF/HDF5, GeoTIFF, shapefiles, LAS/LAZ and KML/GPX are all parsed by native
libraries (eccodes, netCDF-C/HDF5, GDAL, PDAL, libxml2).

- Parse only files that Cascadia Papsukkal fetched itself from allowlisted hosts; never parse
  user uploads in the API process.
- Run heavy parsers in worker processes with memory/CPU limits, not in the API process.
- Pin and track CVEs for GDAL, HDF5, eccodes, PROJ, and libxml2. Disable external entity
  resolution in any XML path (SAML/WMS capabilities/KML).
- Treat NetCDF/HDF5 from third parties as hostile: known decompression and heap bugs exist.

## 3. Geospatial query endpoints are denial-of-service magnets

Endpoints that accept geometry, bounding boxes, time ranges, or tile coordinates can be made
arbitrarily expensive.

- Validate bbox area, polygon vertex count, and time-range length server-side; reject
  rather than clamp silently (document the limits in the API).
- `ST_Intersects`/`ST_Union` on user geometry runs only against pre-simplified geometry with
  spatial indexes; never allow user geometry into raster zonal statistics at request time
  (precompute per basin in workers).
- Tile endpoints are cached at the edge/CDN and rate-limited per IP; dynamic raster tiling
  (TiTiler-style) must have a max zoom and max request size.
- `POST /refresh`-style endpoints that trigger upstream fetches (V1 had these, unauthenticated)
  are **removed** in V2. Ingestion is scheduled by workers, never by HTTP callers. If an
  operator "refresh now" is needed, it is an authenticated admin action with a rate limit and
  an audit log entry.

## 4. Secrets and keys

- Provider keys (NWS API contact, Synoptic tokens, Earthdata credentials, Cesium ion, map
  imagery keys) live in the worker/API environment only. The web app receives only
  **browser-scoped, domain-restricted** keys (imagery tokens) and only through a
  `/config/public` endpoint that is explicitly reviewed; never in the bundle.
- No `REACT_APP_*`/`VITE_*` variable may hold a secret; the build fails a CI grep for
  key-shaped strings in `dist/`.
- `.env*` files are gitignored; a pre-commit secret scanner (gitleaks) runs in CI.
- V1 shipped a third-party analytics key and session recording in `index.html`; V2 ships
  **no third-party scripts** by default. Any analytics is first-party, opt-in, and documented.

## 5. Database

- Parameterized SQL only; PostGIS functions receive geometry via bound parameters
  (`ST_GeomFromGeoJSON($1)`), never string-built WKT.
- Separate roles: `ingest_writer` (workers), `api_reader` (API, read-only), `migrator`.
  The API role cannot write observations.
- Row-level immutability for `observation`/`forecast_value` tables (append-only; corrections
  are new rows with revision lineage), so a compromised API key cannot rewrite history.

## 6. CORS, headers, and transport

- V1 used `allow_origins="*"` **with** `allow_credentials=True`. Never do this. V2: explicit
  origin allowlist from config, credentials only if cookies are ever introduced.
- Security headers on every response (HSTS, `X-Content-Type-Options: nosniff`,
  `Content-Security-Policy` with an allowlist for tile/imagery hosts, `Referrer-Policy`).
- CSP for the web app must enumerate imagery/terrain/3D-tile hosts explicitly; `connect-src`
  and `img-src` allowlists are part of the BasemapProvider configuration, not ad hoc.

## 7. Trust labeling is a security property

A value shown as OFFICIAL that is not official is an integrity failure, not a UX bug.

- Provenance fields (`source_kind`, `issued_at`, `retrieved_at`, `model_version`) are set by
  the adapter that produced the value and are not editable by later stages.
- Any code path that substitutes one source for another (fallback) must change
  `source_kind` and must be visible in the API response. Tests assert that a fallback can never
  carry the `official` label.
- Configured/hand-entered thresholds are never used for risk computation (V1 had fallback
  values that were all wrong versus NWPS; see `docs/V1_AUDIT.md`).

## 8. Supply chain

- No dependencies fetched from non-registry URLs (V1 pulled a tarball from `assets.emergent.sh`).
- Lockfiles committed; `pip-audit`/`npm audit` in CI; Dependabot or Renovate enabled.
- Container images pinned by digest; non-root users; read-only filesystems for API containers.

## 9. Review checklist for a Cascadia Papsukkal PR

- [ ] New outbound HTTP? Host allowlisted, timeout, size cap, UA, raw archive before parse.
- [ ] New endpoint? Input limits documented; no upstream fetch on request path; rate limit.
- [ ] New parser? Fixture tests for malformed, sentinel, oversized, schema-drift inputs.
- [ ] New config/secret? Worker/API only; not in web bundle; documented in `infra/`.
- [ ] New displayed value? `source_kind` + timestamps present; UNKNOWN path exists.
- [ ] New third-party script or CDN? Rejected unless justified in an ADR.
