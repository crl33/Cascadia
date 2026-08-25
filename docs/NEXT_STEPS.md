# NEXT STEPS — what is done, what is not, and the order of work (2026-08-24)

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
| Contracts | `packages/contracts` **1.2.0** (P3 added `SurfaceState.value` + `SurfaceState.spread`, additively) — Pydantic + JSON Schema + fixtures + generated TypeScript; contract tests green |
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
5. **HEFS, NWS alerts, SSE** adapters are not written (all researched, none coded). ~~AWDB/SNOTEL~~ landed with P3 (WTEQ + PREC as *unscored context*, HYDROLOGY §7); SNOTEL soil moisture was evaluated and REJECTED — no climatology, inconsistent depths, `no profile` flags (p3-surfaces-design §2.1), so soil stays UNKNOWN.
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

### P1 — Cinematic client C1/C2 on the live backend (M) — **DONE 2026-08-24, verified live**
- Hydrograph panel (observed + official forecast + thresholds with datum), layer inspector
  with per-value provenance, search, deep links; band boundaries fixed from telemetry;
  remove the Cesium ion logo credit (ion-free attribution).
- Timeline/replay controls driving `as_of` across every query (the API already honors it).
- Exit met (P1 scope): timeline/replay via as_of with honest AS-OF banner and URL round-trip,
  hydrograph with basis/unit/datum discipline, per-value provenance popover, keyboard
  search-to-flight, deep links (?sel=&as_of=&cam=), ion credit replaced with honest
  attribution. Verified in-browser against production 2026-08-24 (incl. the knowledge-time
  boundary: as_of before first ingestion correctly renders all-UNKNOWN). Deferred within C1/C2:
  camera-pose capture on settle, vendor imagery tier, reaches/reservoir layers, perf harness.

### P2 — Event Zero replay experience (M) — **CLOSED 2026-08-24, live and reconciled**
- Backfill Dec 2025 point truth into production: USGS IV Dec 1–31 for the seed stations via
  the OGC API (keyed, 4000/h), NWPS thresholds snapshot, AFOS text products (archiver built)
  parsed to `OfficialAlert`s — EVENT_ZERO T2/T4/T5 at seed-station scope.
- Frontend: an Event Zero mode — fly the Skagit, scrub Dec 3–22, watch observed stages,
  official forecast evolution (MVEW1 36.9→41.5→42.3→39.1→38.3→38.1 vs 37.73 observed) and
  alerts replay with knowledge-time honesty (`as_of` = the scrub position).
- Exit met: 34,940 December observations backfilled (all six §3 peaks exact; MVEW1
  37.73 ft @ 08:15Z, quality approved+backfilled); 123 FLS/FLW forecast runs parsed from
  the IEM byte record with supersedes chains; look-ahead audit zero violations; the client
  event mode (?event=event-zero-2025-12) replays the evolution. Byte verification CORRECTED
  the 2026-08-22 draft table (3 rows disproven, 3 issuances added — EVENT_ZERO.md §8, dated
  correction). Remaining for full T2–T9: other 21 §3 sites unseeded (scripts re-run cleanly
  after seeding), SNOTEL/USACE backfills, OfficialAlert parsing, hindcast harness.

> P2 close-out (2026-08-24): two follow-ups landed as one release — ADR-0014 (run bodies
> declare units/datum per column: `stage_unit`/`flow_unit`/`stage_datum`, no flat `datum`) and
> per-item `ProvenanceRef` on archived runs. A semantic review of the Event Zero freshness badge
> found it measuring present-day currency (`read clock − valid_time`) while sitting beside a
> December cursor; archived values now render `ARCHIVED · N before today` instead of `STALE`
> (VISUAL_TRUTH_DOCTRINE §5.6). `/system/version` plus a stamped `CASCADE_GIT_REVISION` make the
> deployed build checkable against the repository; HEAD and production were reconciled at close.

### P3 — Live intelligence surfaces v0 (M) — **LANDED 2026-08-25**

> P3 close-out (2026-08-25): all three surfaces compute live. Adversarial verification found
> seven places where a surface claimed more than its inputs supported; all were fixed or
> disclosed. Open, deliberately: (a) the agreement bands (25 %/60 % magnitude, 6 h/18 h timing,
> 5 % crest prominence) are **uncalibrated assumptions** — they belong to the hindcast
> calibration work (ADR-0008), and a dry-summer sample has never once exercised the timing
> bands because nothing crests; (b) `RiverVisualizationState.agreement` is still null at river
> items though design §3.3 gives the per-point state one; (c) `high` is reachable at a 29 %
> crest difference because the denominator is floored by the action flow threshold — defensible
> (both models say "nowhere near flooding") and the sentence names the denominator, but it is a
> calibration question a hindcast should settle.
 — **BUILT 2026-08-24**, design and verification in `research/p3-surfaces-design-2026-08-24.md`
- Forcing v0 from NBM QPF percentiles at basin scale (EXPERIMENTAL badge, documented method);
  susceptibility v0 from streamflow percentile + (when SNOTEL adapter lands) SWE context;
  agreement v0 from NWM blend-vs-NWRFC crest comparison at forecast points. All labeled,
  all provenance-carrying, UNKNOWN where inputs are missing.
- Exit: no surface shows UNKNOWN for reasons that are now implemented; every value traces.

**What shipped.** Three surfaces, one foundation, one integration seam.

| Piece | What it is | Where |
|---|---|---|
| Foundation | `derived_feature` + `grid_mask` tables (migration `0002`), NBM/NWM/USGS-statistics/AWDB registry ids, per-call `Accept` + host allowlist + object-key prefix on `ArchivingFetcher`, contract **1.2.0** (`SurfaceState.value`, `SurfaceState.spread`), `eccodes` in the worker extra only | `infra/migrations/`, `packages/core/`, `packages/contracts/` |
| Forcing v0 | NOMADS `filter_blend.pl` WA subset (1.05 MB against a 785 MB source file), `eccodes` decode, area-weighted basin means over full-resolution polygons, banded by an **uncalibrated** table carried as a parameter block | `packages/providers/nbm/`, `packages/geo/`, `hydrology/forcing.py` |
| Susceptibility v0 | The platform's own day-of-year flow climatology from USGS OGC `daily` (decommission-proof), today's rank inside it, SNOTEL SWE/precipitation as **unscored context** | `packages/providers/{usgs,awdb}/`, `hydrology/susceptibility.py` |
| Agreement v0 | NWM v3.1 medium-range **ensemble** per reach from NWPS JSON, compared with the NWRFC run on flow — magnitude, timing, and category only where official flow thresholds exist | `packages/providers/nwps/reaches_*`, `hydrology/agreement.py` |
| Integration | reason **vocabularies** replace the three "not implemented in the spike" constants; `basin_envelope` calls all three methods and merges their drivers into one ranked list; six ingest jobs + the mask build registered on the queue; the panel renders values, units, spread, confidence, agreement's reason and every driver's provenance | `hydrology/{surfaces,assemble}.py`, `apps/worker/{scheduler,queue}.py`, `apps/web/src/panels/BasinPanel.tsx` |

**Two read-path defects were fixed first, and they were the real risk.** `forecast_run` now holds
two forecast products, so `latest_forecast_run` takes a product filter (defaulting to the
registry-resolved OFFICIAL set) and `forecast_run_ref` resolves `source_kind` from the registry
instead of spelling `OFFICIAL_FORECAST` beside every run. Without both, an NWM cycle issued later
than the NWRFC run would have been rendered as the National Weather Service's forecast.

**Measured cost** (design §8, unchanged by the build): ~13.2 MB/day ingest, ~400 MB/month R2
before the 90-day `nbm/` lifecycle rule and ~1.2 GB steady state after it, ~73 k Neon
rows/month (~14 MB), ~20 s worker CPU/day, 24 NOMADS + 24 NWPS-reach requests/day. No new
service and no new recurring charge.

**Exit status.** `GET /viz/basins` returns computed `forcing` and `susceptibility` for all six
basins and a computed `agreement` at five of six, end to end from checked-in provider payloads
(`tests/integration/test_p3_surfaces_api.py`). What is still UNKNOWN is UNKNOWN *on purpose* and
now says which input is missing:

- **soil** — no basin soil-moisture product exists; SNOTEL SMS returns no climatology,
  inconsistent depths and `no profile` flags. Waits for SMAP L4 or NWM `land`.
- **agreement at CRNW1** — the NWRFC run carries no flow column (every secondary value is the
  −9999 sentinel). Waits for a flow column or `method:nwps-rating-conversion`.
- **category agreement at MVEW1/NKSW1/RNTW1** — official categories there are in stage, and
  ADR-0011 forbids inventing the flow equivalent. `model_probability` is therefore emitted only
  at AUBW1 and WRAW1, as a counted member fraction.
- **rain-exposed / rain-on-snow fractions** — need hypsometry (gap 6) and snow-covered area.

**Carried forward out of P3** (each is a decision or a build, not a bug):
1. **Band edges are uncalibrated assumptions** — 25/75/150 mm per 72 h (forcing), 25/75/90
   (susceptibility), 0.25/0.60 and 6 h/18 h (agreement). Stored as parameter blocks with that
   sentence attached; calibration is hindcast work (ADR-0008, Phase 7).
2. **The annual climatology job fires on 1 January only** — cron cannot express "every 365 days"
   from an arbitrary start. Until then the ladder must be built once by hand
   (`python -m cascade_worker run-once`, or defer `usgs.build_climatology`); a fresh deployment
   otherwise shows susceptibility UNKNOWN with the "no day-of-year climatology" reason.
3. **No S3 `.idx` + ranged-GET backfill for NBM** — NOMADS keeps 1–2 days, so a worker outage
   longer than that loses those cycles until the byte-range path (verified working, §1.2) is
   built. The surface reports no cycle; nothing is substituted.
4. **The dev stub and the Cloudflare Pages fallback still serve the pre-P3 envelope**, including
   the now-false "not implemented in the spike" sentences
   (`packages/contracts/fixtures/basin_skagit_envelope.json` → `scripts/sync-pages-fixtures.sh`).
   Recapturing that fixture from a real `/viz/basins` response is a small, separate change.
5. **The three new canaries** (`nbm`, `nwm-via-nwps`, `awdb`/susceptibility) are not folded into
   the scheduled canary run. (`/system/health` itself now reports every registered job and every
   expected product — verification finding C, fixed 2026-08-24: the job catalogue is
   `cascade_core.registry.JOBS`, health is derived from it, and `tests/unit/test_job_registry.py`
   fails if a job registered on the worker is missing from it. `status` gained a third value,
   `unknown`, for "no evidence yet" — a fresh deployment reads `unknown` with the pending jobs
   named, not `degraded`, and not `ok`.)
6. **Open provider questions the canaries now watch**: whether `filter_blend.pl` survives an NBM
   version change, whether NWM `medium_range` stays at 6 members, NWPS `/reaches` rate limits,
   and the intermittent empty `mediumRange` responses (6/6 reaches answered at 22:05Z, 1/6
   twenty minutes later).


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

> **Top P4 item — `/viz/basins` latency (measured 2026-08-25).** The endpoint computes three
> surfaces for six basins and takes **21.8 s** in production (a single basin's state: 4.6 s;
> `/system/health`: 1.9 s). It exceeded the gateway's 20 s abort the moment P3 landed and
> returned 503; the gateway backstop was raised to 60 s, which unblocks the page without
> addressing the cause. The cost is per basin and linear, so it is round trips, not compute:
> each basin re-reads thresholds, runs, the climatology ladder and the member series
> individually. Fix in the API (batch the per-basin reads into set-based queries, and cache the
> assembled envelope until the next ingest — the inputs only change every 6–12 h), not by
> raising timeouts again.
