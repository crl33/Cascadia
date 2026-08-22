# ARCHITECTURE — components, data flow, boundaries, deployment

A modular monolith in Python with independent workers, PostgreSQL/PostGIS for structured and
geospatial state, object storage for raw and gridded science products, and a separate
TypeScript web client that consumes semantic contracts. No Kubernetes, no microservices, no
message broker until a measured need appears.

## 1. System shape

```
                          EXTERNAL SOURCES
   USGS (OGC API) · NWPS + HEFS · NWRFC · NWM · NWS api · NBM/HRRR/GFS/GEFS · MRMS · AWDB/SNOTEL · SNODAS
   SMAP · USACE CWMS · operators (SCL/PSE/SPU) · WBD/NHDPlus/3DEP/NLD/NFHL · alerts
                                 │
                                 ▼
 ┌──────────────────────── apps/worker ────────────────────────┐
 │ scheduler ─► jobs (idempotent, retried, rate-aware)          │
 │   fetch ──► archive raw ──► parse/normalize ──► quality ──► write (append-only)
 │   aggregate grids → basin features    compute derived features
 │   assess surfaces  ▸  explain deltas  ▸  build visualization derivatives (tiles, LOD geom)
 └──────────────┬───────────────────────────────┬──────────────┘
                │                               │
                ▼                               ▼
        PostgreSQL + PostGIS              Object storage (S3 API)
   geography · observations · forecasts   raw payloads · GRIB2/NetCDF · COG/Zarr
   thresholds · features · assessments    tile pyramids · hindcast outputs
   events · provenance · sources          (content-addressed, lifecycle rules)
                │                               │
                └──────────────┬────────────────┘
                               ▼
                          apps/api  (FastAPI, read-mostly)
        REST/JSON (entities, state, assessments, provenance, alerts)
        time-series endpoints · replay (`as_known_at`) · tile proxy/redirects
        SSE for lightweight "new run / state changed" notifications
                               │
                               ▼
                          apps/web  (React + TypeScript + CesiumJS)
        scene · camera · layers · timeline · panels — renders semantic contracts
```

Invariants:

- **Acquisition never depends on a request.** The API has no code path that calls a provider.
- **Science lives in `packages/`**, imported by workers; the API only reads and projects.
- **Renderer-agnostic contracts.** `packages/visualization` emits semantic state; no colour,
  material or camera instruction leaves the backend.
- **One database, two roles.** Workers write (append-only); the API reads.

## 2. Repository layout

```
cascade-oracle/
├─ CLAUDE.md · CONTEXT.md · AGENTS.md           ICM routing
├─ docs/                                       doctrine, architecture, ADRs, research
├─ v1/                                         prototype, read-only
├─ apps/
│  ├─ api/        FastAPI app: routers, projections, auth (admin only), SSE
│  ├─ worker/     scheduler + job modules; one process type, N replicas
│  └─ web/        Vite + React + TS + CesiumJS (own AGENTS.md per subsystem when needed)
├─ packages/                                   Python, installed as one workspace (uv)
│  ├─ contracts/  Pydantic models + JSON Schema export (API + visualization contracts)
│  ├─ core/       config, logging/tracing, db session, object store, time utils, units
│  ├─ geo/        basins, hypsometry, topology, zonal aggregation, LOD geometry
│  ├─ hydrology/  features, surfaces, headroom, snow/soil/river/reservoir logic, explanation
│  ├─ providers/  one subpackage per source: client, parser, fixtures, canary
│  │   usgs/ nwps/ nwrfc/ nwm/ nws/ nbm/ hrrr/ gfs/ mrms/ snotel/ snodas/ smap/ usace/ …
│  ├─ history/    events, timelines, hindcast harness, `as_known_at`
│  └─ visualization/  scene contracts, tile/derivative generation (no science)
├─ migrations/    Alembic; schema is reviewed against docs/DOMAIN_MODEL.md
├─ tests/         fixtures/ unit/ integration/ e2e/ canaries/
└─ infra/         compose for dev (postgis, seaweedfs), Dockerfiles, env examples, runbooks
```

Python packages are not mirrored in TypeScript for symmetry. The web app depends on the
contracts only through generated types (`apps/web/src/contracts/` from JSON Schema).

## 3. Ingestion workers

- **Scheduler**: cron-like definitions per product (`every 15m`, `at cycle + latency`),
  plus event-triggered jobs (a new forecast run ⇒ aggregation ⇒ assessment ⇒ derivatives).
- **Jobs** are pure functions of `(product, window)` with an **idempotency key**
  `(product_id, scope, issued_at|valid_time)`; re-running is safe by construction (append
  with unique constraints; conflicts are no-ops).
- **Rate awareness**: per-host token buckets and concurrency caps declared by each provider
  adapter; User-Agent with contact; backoff with jitter; circuit breaker per host.
- **Pipeline per payload**: fetch → archive raw (object store, sha256) → parse (strict) →
  normalize (units, times, sentinels → quality) → write. A parse failure never loses the raw
  payload and raises a provider-health event.
- **Gridded products**: download → archive → extract needed variables → reproject/clip to
  the Washington extent → basin aggregation via precomputed masks → write basin features →
  emit visualization derivatives (COG/tiles) asynchronously.
- **Queue/scheduler technology**: PostgreSQL-backed (ADR-0003) so that dev and prod share one
  dependency; no Redis/RabbitMQ until needed.
- **Health**: every job records start/finish/outcome; freshness per product is a metric; a
  provider is `healthy / degraded / down` by rule, exposed on `/system/health`.

## 4. Persistence

- PostgreSQL 18.x with PostGIS 3.6.x (ADR-0001; version evidence in ADR-0013). Observation/forecast tables partitioned monthly
  (native partitioning via `pg_partman`; TimescaleDB deferred — ADR-0013).
- Append-only application roles; corrections as revision rows (DATA_DOCTRINE §8).
- Object storage through the S3 API (SeaweedFS or Garage locally — MinIO is archived and
  unmaintained as of 2026-04-25; Cloudflare R2 or S3 in production — ADR-0004). Keys are content-addressed for raw payloads and deterministic
  `product/issued/valid/variable` paths for grids.
- Large science products are indexed in PostgreSQL (`GridProduct`) but never stored in it.

## 5. State, feature, intelligence engines (packages/hydrology)

- **State engine**: projects the latest valid observations/model outputs into per-basin and
  per-reach state views with freshness; no computation beyond unit normalization and
  percentiles against stored climatology.
- **Feature engine**: versioned `Method`s computing `DerivedFeature`s (API, rate of rise,
  headroom, rain-exposed fraction, basin QPF, SWE anomaly, reservoir buffer…). Each method
  declares inputs and emits lineage.
- **Assessment engine**: computes the four surfaces (`HYDROLOGY.md` §3–6) from features,
  official forecasts and model outputs; emits structured drivers and mitigating factors;
  computes deltas versus the previous assessment for the explanation layer.
- **History engine** (`packages/history`): event timelines, `as_known_at(T)`, hindcast
  harness that replays assessments over an event with only knowledge-time-eligible data and
  writes evaluation metrics.

## 6. API (apps/api)

Read-mostly FastAPI. Resource families:

| Family | Examples |
|---|---|
| geography | `/basins`, `/basins/{id}`, `/basins/{id}/reaches`, `/stations/{id}`, `/reservoirs/{id}`, `/search?q=` |
| state | `/basins/{id}/state`, `/stations/{id}/state`, `/reservoirs/{id}/state` (projections with provenance + freshness) |
| assessments | `/basins/{id}/assessments?surface=&horizon=`, `/assessments/latest`, `/basins/{id}/explanation` |
| series | `/stations/{id}/series?variable=&from=&to=`, `/forecast-points/{lid}/runs`, `/forecast-points/{lid}/runs/{run}/values` |
| thresholds & alerts | `/forecast-points/{lid}/thresholds`, `/alerts?basin=` |
| replay | any read endpoint with `?as_of=<T>` → served via `as_known_at(T)` |
| visualization | `/scene/summary?bbox=&band=&t=`, `/viz/basins?t=`, `/viz/rivers?t=`, tile redirects |
| system | `/system/health`, `/system/sources`, `/system/freshness` |
| events | `/events`, `/events/{id}/timeline`, `/events/{id}/hindcasts` |

Conventions: cursor pagination on series; ETags on static geography; explicit limits on bbox
area, polygon vertices and time ranges (vibesec addendum §3); OpenAPI exported and used to
generate web types. Admin endpoints (re-run job, re-fetch) are authenticated and rate-limited;
there are no anonymous mutating endpoints.

Live updates: SSE topic per basin emitting `{kind: observation|forecast_run|assessment|alert, scope, at}`;
clients refetch. No data payloads over the stream.

## 7. Web client boundary (summary; details in CINEMATIC_ARCHITECTURE.md)

The client consumes `packages/contracts` visualization types, static geography (vector tiles
or simplified GeoJSON by LOD), and raster/3D tiles from object storage/CDN. It computes
nothing hydrologic. Camera, layers and time are client state; science is server state.

## 8. Observability

- Structured logs (JSON) with `job_id`, `product_id`, `scope`, `run_id` fields.
- Metrics: ingestion success/failure per product, freshness seconds per product, rows written,
  provider latency, queue depth, assessment latency, API latency, tile cache hit rate.
- Tracing (OpenTelemetry) across job → DB → object store; sampled in production.
- Dashboards: provider health board, freshness board, assessment timeline.

## 9. Deployment

- Containers: `api`, `worker` (same image, different entrypoint), `web` (static build behind a
  CDN/edge), `postgis`, `seaweedfs` (dev) — composed with `docker compose` for dev; the same
  images run on any VM/PaaS in production. Cloud-agnostic: S3 API + PostgreSQL are the only
  service contracts.
- Configuration via environment (12-factor); secrets in the platform's secret store; the web
  build contains only public, domain-restricted keys.
- Migrations run as a job before `api`/`worker` roll.
- Backups: PostgreSQL base + WAL; object storage versioning on raw buckets.

## 10. Technology decisions (see docs/adr/)

| ADR | Decision |
|---|---|
| 0001 | PostgreSQL + PostGIS replaces MongoDB |
| 0002 | Python modular monolith + worker processes; FastAPI/Pydantic v2/SQLAlchemy 2 async |
| 0003 | PostgreSQL-backed job queue and scheduler |
| 0004 | S3-compatible object storage for raw and gridded products |
| 0005 | Generic Observation / DerivedFeature model; no per-variable schema |
| 0006 | Web: Vite + React + TypeScript + CesiumJS; no CRA |
| 0007 | Renderer boundary: semantic visualization contracts only |
| 0008 | Official models first; no Cascade probabilities before hindcast evaluation |
| 0009 | Units and datums policy |
| 0010 | Bitemporal knowledge time (`available_at`) for all values |
| 0011 | Thresholds: official only in hazard computation |
| 0012 | Repository strategy: V1 preserved under `v1/`, V2 at root, single repo |
| 0013 | Time-series storage: native partitioning first; TimescaleDB deferred |

## 11. Non-goals for Phase 0–2

Kubernetes, service mesh, Kafka, a custom ML model, GraphQL, multi-tenant auth, mobile-first
layouts, audio. Each is a later ADR if and when needed.
