# NEXT STEPS — what is done, what is not, and the order of work (2026-08-22)

A plan, not a roadmap: [ROADMAP.md](ROADMAP.md) and [CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md)
define the phases; this file says where we actually are and what to do next, in order. Update it
when a milestone closes; delete lines that stop being true.

## 1. Where we are

### Done (verified, in the repository)

| Area | State |
|---|---|
| Orientation | `V2_ASSESSMENT.md`, `V1_AUDIT.md` (V1 preserved read-only under `v1/`) |
| Doctrine & architecture | `HYDROLOGY`, `DATA_DOCTRINE`, `DOMAIN_MODEL`, `ARCHITECTURE`, `TESTING`, 7 cinematic docs, ADR-0001…0013 (all accepted) |
| Data inventory | `DATA_SOURCES.md` — 75 providers; `docs/research/` evidence for 9 categories (3 independently verified, 6 pending) |
| Event Zero | `EVENT_ZERO.md` — 25 verified crest rows, 115 timeline rows with issuance-time `available_at` |
| Contracts | `packages/contracts` 1.1.0 — Pydantic + JSON Schema + fixtures + generated TypeScript; contract tests green |
| Spike (verified end to end) | worker → raw archive → SQLite → read-only API → CesiumJS client; 40 backend tests, 27 web tests, Playwright 4/4 vs stub and vs real API, react-doctor 90/100 (`research/spike-report-2026-08-22.md`) |
| Geography seed | six WBD-derived basins at two display LODs; six stations / forecast points; SNOTEL mappings verified |
| Deployment (added 2026-08-22 by a second tool) | web client on Cloudflare Pages (`cascadia-c7y.pages.dev`) behind a Worker gateway at `cascadia.papsukkal.com`; production build points at a **same-origin API** |
| Working conventions | ICM routing (`CLAUDE.md`, `CONTEXT.md` per folder), skills `icm-architect`, `vibesec` (+ addendum), `react-quality` |

### Not done (gaps, ranked by how much they block)

1. ~~No deployed backend~~ **closed 2026-08-24** (Railway + Neon + R2 behind the Pages gateway). Was: The production client calls a same-origin `/basins`, `/viz/...` API that
   does not exist at `cascadia.papsukkal.com`; the deployed page can only show the non-WebGL /
   degraded states. The spike backend is SQLite + an in-process asyncio scheduler, not deployable
   as-is.
2. **Phase 0 infrastructure is unbuilt:** PostGIS + Alembic schema, Procrastinate worker/queue,
   object storage (SeaweedFS dev / R2 prod), observability, CI, `import-linter` boundaries.
3. **USGS ingestion is on the legacy IV endpoint** (decommission Q1 2027, possible degradation
   from August 2026); the OGC API adapter with a registered key is not written.
4. **No continuous history yet.** Nothing is ingesting around the clock; the 30-day freshness SLO
   and replay golden tests of Phase 1 cannot start until a worker runs somewhere.
5. **HEFS, NWS alerts, AWDB/SNOTEL, SSE** adapters are not written (all researched, none coded).
6. **Basin geometry is HUC8 unions**, not outlet-delineated (NLDI/StreamStats); no hypsometry; no
   reach topology in the store.
7. **Six research categories lack a second-agent verification pass** (hydrology, precipitation,
   snow/soil, reservoirs, static-geo, Event Zero).
8. **Client items from the spike:** CORS allowlist for the preview origin, Cesium ion logo credit
   rendered although ion is unused, band boundaries retuned pending telemetry, no hydrograph panel,
   no layer inspector for series, no timeline.
9. **Owner decisions pending:** commercial status (Cesium ion, Synoptic, Ecology GIS, DNR lidar
   terms), data agreements (King County HIC, SPU, FEMS), hosting for API/worker/DB, the second
   historical event for rain-on-snow.

## 2. Milestones, in order

> **Reprioritized 2026-08-24 (owner directive):** M1 is done and the Event Zero bulk copy is
> parked (long-term mirrors GCS+Azure verified byte-exact 2026-08-24, retrieval paths tested;
> extracted WA-specific analytical archive preferred later). Priority is now a substantially complete working product:
> the frontend/Cesium experience, live intelligence surfaces, the historical replay /
> Event Zero experience, and production robustness. No new recurring infrastructure cost
> unless required for functionality actively being built. Execution order: **P1 → P2 → P3**
> below, then the remaining M-milestones as originally sequenced.

### P1 — Cinematic client C1/C2 on the live backend (M)
- Hydrograph panel (observed + official forecast + thresholds with datum), layer inspector
  with per-value provenance, search, deep links; band boundaries fixed from telemetry;
  remove the Cesium ion logo credit (ion-free attribution).
- Timeline/replay controls driving `as_of` across every query (the API already honors it).
- Exit: CINEMATIC_ROADMAP C1+C2 exit criteria against cascadia.papsukkal.com.

### P2 — Event Zero replay experience (M)
- Backfill Dec 2025 point truth into production: USGS IV Dec 1–31 for the seed stations via
  the OGC API (keyed, 4000/h), NWPS thresholds snapshot, AFOS text products (archiver built)
  parsed to `OfficialAlert`s — EVENT_ZERO T2/T4/T5 at seed-station scope.
- Frontend: an Event Zero mode — fly the Skagit, scrub Dec 3–22, watch observed stages,
  official forecast evolution (MVEW1 36.9→41.5→42.3→39.1→38.3→38.1 vs 37.73 observed) and
  alerts replay with knowledge-time honesty (`as_of` = the scrub position).
- Exit: the MVEW1 forecast-evolution table reproduces on screen from stored rows with zero
  look-ahead violations.

### P3 — Live intelligence surfaces v0 (M)
- Forcing v0 from NBM QPF percentiles at basin scale (EXPERIMENTAL badge, documented method);
  susceptibility v0 from streamflow percentile + (when SNOTEL adapter lands) SWE context;
  agreement v0 from NWM blend-vs-NWRFC crest comparison at forecast points. All labeled,
  all provenance-carrying, UNKNOWN where inputs are missing.
- Exit: no surface shows UNKNOWN for reasons that are now implemented; every value traces.


Each milestone has an exit test. Sizes are relative. Dependencies point at earlier milestones.

### M1 — A real backend behind the deployed client (M) — **DONE 2026-08-24** (see infra/CONTEXT.md; smoke-tested through cascadia.papsukkal.com)

Goal: `cascadia.papsukkal.com` shows live Skagit data with provenance, continuously refreshed.

- Choose the backend host (a small VM or container service with persistent disk; Cloudflare
  Pages cannot run the Python API/worker). Decide PostgreSQL hosting (managed Postgres with
  PostGIS; no TimescaleDB needed — ADR-0013).
- Route `/api/*` (or the spec paths) from the Worker gateway to the backend; keep the client
  same-origin; add the preview origin to `CASCADE_CORS_ORIGINS` for E2E.
- Run the spike worker on a schedule (temporary: the asyncio `run` loop under a process
  supervisor) until M2 replaces it.
- Exit: `/system/health` public and `ok`; `/basins/basin:skagit/state` validates against the
  1.1.0 contracts; the Playwright live-API suite passes against the deployed origin.

### M2 — Phase 0 infrastructure (L)

- Alembic migrations implementing `DOMAIN_MODEL.md` on PostGIS: geography, sources, values
  (monthly partitions via `pg_partman`), intelligence, history; roles `ingest_writer` /
  `api_reader` / `migrator`; append-only grants.
- Procrastinate app: job modules per provider, idempotency keys, per-host rate limits, circuit
  breakers, stalled-job retry task, finished-job pruning (ADR-0003).
- Object store via `obstore` against SeaweedFS (dev) / R2 (prod): raw payloads content-addressed.
- Observability: structured logs, `/metrics`, freshness per product, provider health board.
- CI: ruff, mypy (contracts, hydrology), pytest offline, contracts:check, vitest, Playwright vs
  stub, react-doctor score gate, gitleaks; canaries on a schedule, non-blocking.
- Exit: ROADMAP Phase 0 exit criteria; the spike's SQLite path deleted.

### M3 — Phase 1 observational truth (M)

- USGS **OGC API** adapter (key, `latest-continuous` polling, `continuous` backfill ≤ 3 years,
  `approval_status`, revisions); retire the legacy IV adapter.
- NWPS: gauge metadata versioning, thresholds (stage and flow), `stageflow` forecasts,
  crests/impacts; **HEFS API** archived daily (official probabilities for Phase 5).
- NWS API alerts (county/zone) → `OfficialAlert`; SSE notify-then-fetch.
- Basin refinement: NLDI/StreamStats outlet delineation, NHDPlus HR reaches + NWM `feature_id`
  crosswalk, 3DEP hypsometry per basin.
- Derived: observed category, rate of rise (1/3/6 h), stage/flow headroom, time-to-threshold,
  streamflow percentile (labeled period).
- Exit: 30 days of continuous ingestion within freshness SLOs; replay golden test; Green/White
  categories from flow; `as_of` on every endpoint.

### M4 — Client C1/C2 promotion (M)

- Production basemap decision (self-hosted PMTiles via Martin, or Esri Static Basemap Tiles) and
  ion-free terrain (MapTiler quantized-mesh or self-tiled 3DEP); remove the ion logo credit.
- Hydrograph panel (observed + official forecast + thresholds with datum), layer inspector on
  series, search, bookmarks, deep links; band boundaries fixed from telemetry.
- Exit: CINEMATIC_ROADMAP C1 and C2 exit criteria; visual regression scenes recorded.

### M5 — Forcing and snow/soil (Phases 2–3, L, parallelizable after M2)

- Grid pipeline: NBM v5.0 (QPF percentiles, `SNOWLVL`), HRRR, GEFS (pgrb2b for IVT), MRMS
  Pass2 with RQI/gauge-influence covariates; basin masks; COG derivatives.
- AWDB/SNOTEL (`periodRef` explicit, `returnFlags`, medians), SNODAS (mask unbounded-SWE cells),
  VIIRS (NOAA-20/21), SMAP L4, NWM land; rain-exposed and rain-on-snow fractions; susceptibility
  index badged EXPERIMENTAL.

### M6 — Reservoirs, fusion, Event Zero (Phases 4–6, XL)

- USACE CWMS under office `NWDP` (HAH, MMD, ROS, UBK, LWSC), A2W levels, NID, NLD; regulated-reach
  awareness.
- NWM reach forecasts + HEFS → model agreement; forecast evolution.
- Event Zero reconstruction per `EVENT_ZERO.md` §8 (copy the NWM Dec-2025 outputs **now** — the
  bucket's documented retention has not been enforced and may be); hindcast harness with the
  look-ahead audit; pick the rain-on-snow analog event.

## 3. Immediate next actions (this week)

1. Decide backend hosting and PostgreSQL hosting (owner decision; unblocks M1/M2).
2. Register a USGS Water Data API key and an NWS API contact; put both in the worker environment.
3. ~~Inventory the surviving NWM Dec-2025 outputs~~ **done 2026-08-24**: all 22 days survive
   (25.44 TB total; scoped archive tiers FULL 2.30 TB / LEAN 1.10 TB) — see
   `research/nwm-survival-inventory-2026-08-24.md`. Copy now blocked ONLY on an explicit owner cost approval (R2 free tier is 10 GB; LEAN ~$16.5/mo,
   FULL ~$34/mo; owner directed free-tier mindfulness 2026-08-24). Mechanism when approved:
   Cloudflare Worker copy pump (Super Slurper cannot read anonymous public buckets; local
   relay measured at 1.5 MB/s). IEM AFOS product dumps still to archive (small, T2).
4. Stand up PostGIS locally (Docker) and write the first Alembic migration from `DOMAIN_MODEL.md`.
5. Port the spike's providers onto Procrastinate jobs; write the USGS OGC adapter with fixtures.
6. Deploy the API + worker; wire the gateway; run the live Playwright suite against the domain.
7. Re-run the pending research verifications (six categories) as a scheduled, low-concurrency job.
8. Fix the client's ion credit and CORS preview origin; record the band decision in
   `SEMANTIC_ZOOM.md` §1 once measured.

## 4. What would change this plan

- A hosting choice that cannot run long-lived workers (then: scheduled serverless ingestion with
  the same job modules and an external Postgres).
- NWS/USGS endpoint changes (the legacy IV degradation window has started; the OGC API is v0).
- HEFS API withdrawal (experimental) — Phase 5 would fall back to NWM ensembles only.
