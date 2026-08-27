# NEXT STEPS — what is done, what is not, and the order of work (2026-08-27, second pass)

A plan, not a roadmap: [ROADMAP.md](ROADMAP.md) and [CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md)
define the phases; this file says where we actually are and what to do next, in order. Update it
when a milestone closes; delete lines that stop being true.

## 1. Where we are

### Done (verified, in the repository)

| Area | State |
|---|---|
| Orientation | `V2_ASSESSMENT.md`, `V1_AUDIT.md` (V1 preserved read-only under `v1/`) |
| Doctrine & architecture | `HYDROLOGY`, `DATA_DOCTRINE`, `DOMAIN_MODEL`, `ARCHITECTURE`, `TESTING`, 7 cinematic docs, ADR-0001…0014 (all accepted; 0014 added 2026-08-24, per-column units/datum on forecast runs) |
| Data inventory | `DATA_SOURCES.md` — 75 providers; `docs/research/` evidence for 9 categories (3 independently verified, 6 pending) |
| Event Zero | `EVENT_ZERO.md` — 25 verified crest rows, 115 timeline rows with issuance-time `available_at` |
| Contracts | `packages/contracts` **1.3.0** (P3 added `SurfaceState.value` + `SurfaceState.spread`; Tier 0 added `HydrologicState`, `SeasonalMultiple`, `StateChange` and `BandBoundary`, all additively and all OUTSIDE `SurfaceState` so no client can fuse them into a score) — Pydantic + JSON Schema + fixtures + generated TypeScript; contract tests green |
| Spike (verified end to end) | worker → raw archive → SQLite → read-only API → CesiumJS client; 40 backend tests, 27 web tests, Playwright 4/4 vs stub and vs real API, react-doctor 90/100 (`research/spike-report-2026-08-22.md`) |
| Geography seed | six WBD-derived basins at two display LODs; six stations / forecast points; SNOTEL mappings verified |
| Deployment (added 2026-08-22 by a second tool) | web client on Cloudflare Pages (`cascadia-c7y.pages.dev`) behind a Worker gateway at `cascadia.papsukkal.com`; production build points at a **same-origin API** |
| Working conventions | ICM routing (`CLAUDE.md`, `CONTEXT.md` per folder), skills `icm-architect`, `vibesec` (+ addendum), `react-quality` |
| Production (2026-08-24 →) | Railway backend + Neon PostgreSQL 18/PostGIS + Cloudflare R2 behind the Pages gateway at `cascadia.papsukkal.com`; `/system/version` stamps the deployed revision; Alembic at `0003` |
| Live intelligence (P3, 2026-08-25) | forcing (NBM v5), susceptibility (platform-built USGS day-of-year climatology), agreement (NWM medium-range ensemble via NWPS `/reaches`) |
| Tier 0 (2026-08-27) | `rate-of-rise@2.0.0` (Siegel repeated median + fail-closed `station.tidal_class`), `streamflow-tail-state@0.1.0`, `streamflow-state-change@0.1.0`, `streamflow-record-context@2.0.0` + `streamflow-growth-reference@1.0.0` (split so the growth rank is read at every percentile, not only at or above p90), boundary condition; Event Zero A/B in `research/event-zero-ab-2026-08-27.md`, re-run after the split: first escalations carrying a growth rank 1 of 6 → 6 of 6, lead times unchanged |
| Tier 0 in the client (2026-08-27) | runtime zod schemas for `hydrologic_state` / `state_change` with a `NoMissingKeys` drift check; BasinPanel renders level, change and historical context as separate statements, each with its own provenance; refusals keep the backend's own reason |

### Not done (gaps, ranked by how much they block)

1. ~~No deployed backend~~ **closed 2026-08-24** (Railway + Neon + R2 behind the Pages gateway). Was: The production client calls a same-origin `/basins`, `/viz/...` API that
   does not exist at `cascadia.papsukkal.com`; the deployed page can only show the non-WebGL /
   degraded states. The spike backend is SQLite + an in-process asyncio scheduler, not deployable
   as-is.
2. ~~Phase 0 infrastructure is unbuilt~~ **largely closed 2026-08-24/27** — PostGIS + Alembic
   (3 revisions), Procrastinate worker/queue, R2 via `obstore`, CI (5 jobs incl. a
   PostgreSQL-marked suite), `import-linter` (5 contracts) all exist. **Still genuinely missing,
   verified 2026-08-27:** no `/metrics` endpoint, no `ingest_writer` / `api_reader` / `migrator`
   database roles, and no mypy in CI. Freshness-per-product and a provider health board DO exist,
   in `/system/health`.
3. ~~USGS instantaneous values are still on the legacy IV endpoint~~ **closed 2026-08-27**: the
   instantaneous path is the OGC `continuous` collection ([ADR-0015](adr/ADR-0015-usgs-instantaneous-transport.md)).
   ~~`nwis/stat` remains on the same Q1 2027 deadline~~ **also closed 2026-08-27**: the published
   day-of-year cross-check now reads the OGC statistics API's `observationNormals`
   ([ADR-0016](adr/ADR-0016-usgs-published-statistics-successor.md)). **Cascadia has no production
   call site for `waterservices.usgs.gov`.** Both hosts stay in the fetch ceiling for the retired
   instantaneous comparator alone, pinned by a test.
4. ~~No continuous history yet~~ **closed 2026-08-24**: the Railway worker runs the registered
   crons continuously and `/system/health` reports freshness per product. The 30-day freshness
   SLO can now be measured; it has not been.
5. **HEFS, NWS alerts, SSE** adapters are not written (all researched, none coded). ~~AWDB/SNOTEL~~ landed with P3 (WTEQ + PREC as *unscored context*, HYDROLOGY §7); SNOTEL soil moisture was evaluated and REJECTED — no climatology, inconsistent depths, `no profile` flags (p3-surfaces-design §2.1), so soil stays UNKNOWN.
6. **Basin geometry is HUC8 unions**, not outlet-delineated (NLDI/StreamStats); no hypsometry; no
   reach topology in the store.
7. **Six research categories lack a second-agent verification pass** (hydrology, precipitation,
   snow/soil, reservoirs, static-geo, Event Zero).
8. **Client items.** Closed with P1 (2026-08-24): hydrograph panel, timeline/replay, provenance
   popover, search-to-flight, deep links. ~~The client cannot see Tier 0~~ **closed 2026-08-27**
   (`3b880bf`): runtime zod schemas added with a missing-key drift check, and BasinPanel renders
   the level, the change and the historical context of that change as separate statements.
   Still open: Cesium ion logo credit rendered although ion is unused, CORS allowlist for the
   preview origin, band boundaries pending telemetry, no layer inspector for series.
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

### M2 — Phase 0 infrastructure (L) — **LARGELY DONE 2026-08-24/27; three items remain**

Verified 2026-08-27 against the repository: Alembic revisions `0001`–`0003` on PostGIS,
Procrastinate queue + worker, `obstore` against R2, 5 CI jobs (`gitleaks`, `e2e-stub`, `backend`,
`backend-pg`, `web`), `import-linter` 5 contracts, 4 provider canaries, `pg_partman`. **Not done:**
`/metrics`, the `ingest_writer` / `api_reader` / `migrator` roles with append-only grants, and
mypy in CI. The exit line "the spike's SQLite path deleted" is **withdrawn**: `docs/TESTING.md`
requires a deterministic offline suite and SQLite is how it runs, so deleting it would remove the
property the exit criterion was protecting.

- Alembic migrations implementing `DOMAIN_MODEL.md` on PostGIS: geography, sources, values
  (monthly partitions via `pg_partman`), intelligence, history; roles `ingest_writer` /
  `api_reader` / `migrator`; append-only grants.
- Procrastinate app: job modules per provider, idempotency keys, per-host rate limits, circuit
  breakers, stalled-job retry task, finished-job pruning (ADR-0003).
- Object store via `obstore` against SeaweedFS (dev) / R2 (prod): raw payloads content-addressed.
- Observability: structured logs, `/metrics`, freshness per product, provider health board.
- CI: ruff, mypy (contracts, hydrology), pytest offline, contracts:check, vitest, Playwright vs
  stub, react-doctor score gate, gitleaks; canaries on a schedule, non-blocking.
- Exit: ROADMAP Phase 0 exit criteria, minus the withdrawn SQLite line (see above).

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

## 3. Immediate next actions

Items 1–6 of the previous list (hosting decisions, the USGS key, PostGIS + the first migration,
Procrastinate, the OGC adapter, deploying API + worker + gateway) all **closed 2026-08-24**;
they are recorded in §1 rather than repeated here.

~~1. Decouple the growth rank from `RANK_READ_EDGE`~~ **DONE 2026-08-27** (`595fc92`). The growth
   reference is its own row, `method:streamflow-growth-reference@1.0.0`, read at every percentile;
   the record context went to `@2.0.0` with `growth` removed, so storage is unchanged and the read
   is 247 KiB instead of 952. Mutation-proved three ways.
~~2. Surface Tier 0 in the client~~ **DONE 2026-08-27** (`3b880bf`, `1856fe1`). The runtime zod
   schemas were the gap — `generated.ts` had the types and minor-version tolerance stripped them.
   Added, plus a `NoMissingKeys` check that fails typecheck naming an omitted field, because the
   existing `Assignable` guard is one-directional and structurally cannot catch an omission.
   BasinPanel renders level / change / historical context as separate statements, each with its
   own provenance. `1856fe1` corrected a clamp renderer that named the wrong END of the ladder.
~~3. Re-run the strict knowledge-time replay~~ **DONE 2026-08-27** (`a024c7f`). `unproject` must
   run BEFORE the strict replay; with it, 792 evaluations and zero computed surfaces, pinned by
   `tests/fixtures/hindcast/event_zero_knowledge_time.json` and a test.
~~4. Migrate USGS instantaneous values off the legacy IV endpoint~~ **DONE 2026-08-27**. The live
   path is the Water Data OGC API `continuous` collection; parity was measured over 1,100 semantic
   rows with zero one-sided rows and zero value/unit/datum/quality differences
   (`research/usgs-ogc-instantaneous-parity-2026-08-27.md`, [ADR-0015](adr/ADR-0015-usgs-instantaneous-transport.md)).
   The legacy adapter is retired to comparator-only and there is no fallback. **The published
   day-of-year cross-check followed the same day**: `observationNormals` under a NEW source,
   product and method id, because parity there was measured ABSENT — p50 equal on 1,213 of 2,196
   day pairs, no period of record published at all, and a 25 % maximum p50 difference at 12113000
   from 6–26 extra years of record
   (`research/nwis-stat-successor-2026-08-27.md`, [ADR-0016](adr/ADR-0016-usgs-published-statistics-successor.md)).
~~5. Fix the seeded time zone that was killing `state_change` in production~~ **DONE 2026-08-27**.
   Stations were seeded `PST8PDT`; `python:3.14-slim` ships `tzdata` without `tzdata-legacy` and
   cannot resolve the alias, so every container-written daily percentile row was stamped at UTC
   midnight with `day_boundary_assumed_utc` — 7 h from the local boundary, more than the 6 h
   pairing tolerance, so every basin's 24 h `state_change` published `growth: null` (and no `rank`)
   with a refusal reason instead of a rate. The seed now
   carries `America/Los_Angeles` and refuses any zone outside `SEEDABLE_TIME_ZONES` or
   unresolvable in the running image, so it fails at seed time instead of degrading per row
   ([ADR-0017](adr/ADR-0017-canonical-iana-time-zones-in-the-seed.md)). The flagged historical rows
   are left as they are and nothing is backfilled: the 24 h `growth` returns on its own once two
   correctly stamped daily rows exist. **Production still needs the re-seed and one re-run** —
   `infra/RUNBOOK-deploy.md` §"Re-seed after a seed-data change".
6. **Close the three remaining M2 items**: `/metrics`, database roles with append-only grants,
   mypy in CI.
7. Re-run the pending research verifications (six categories) as a scheduled, low-concurrency job.
8. Fix the client's ion credit and CORS preview origin; record the band decision in
   `SEMANTIC_ZOOM.md` §1 once measured.

**Explicitly NOT next** (owner direction, 2026-08-27): multi-event calibration / the POD-FAR
curve of brief §18. Nothing may draw a band or cutoff on the Tier 0 statements until it exists,
and it is not being started yet.

## 4. What would change this plan

- A hosting choice that cannot run long-lived workers (then: scheduled serverless ingestion with
  the same job modules and an external Postgres).
- NWS/USGS endpoint changes (the legacy IV degradation window has started; the OGC API is v0).
- HEFS API withdrawal (experimental) — Phase 5 would fall back to NWM ensembles only.

> **RESOLVED 2026-08-26 — `/viz/basins` read-path amplification.** Attacked in the brief's order
> and stopped before caching, which was not needed.
>
> | | statements | production p50 |
> |---|---:|---:|
> | before | 120 (17 exact repeats) | 21.8 s |
> | after | **13** (0 repeats) | **~2.6 s** direct, **~2.75 s** through the domain |
>
> The count is now **independent of basin count** (six basins and one basin both issue 13) and
> rows returned fell 58 %, so round trips were not bought with bytes. Proved by 74 body
> comparisons at 12 knowledge times — including both sides of every `available_at` instant in the
> data — with zero differences, and by mutation tests in which deleting the `available_at <= as_of`
> filter from a batched reader is caught 5 times out of 5. No cache, no Redis, no new recurring
> cost. The gateway abort is back to a 30 s backstop from the emergency 60 s.
>
> **What remains is distance, not amplification.** Measured in production: `/basins` (1 query)
> 0.41 s, `/system/health` (7) 1.59 s, `/viz/basins` (13) 2.75 s — a consistent **~195 ms per
> query** on a 0.41 s network baseline. The <2 s stretch target needs ~8 queries or a shorter hop,
> and the honest lever is **co-locating Railway with Neon (`us-west-2`)**: `serviceInstanceUpdate`
> accepts a `region`, returns `true`, and leaves the instance at `region: null`, so it must be set
> in the Railway dashboard by hand. At ~15 ms per query the present 13 statements would cost well
> under a second.
