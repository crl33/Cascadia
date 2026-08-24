# Spike report — 2026-08-22

End-to-end verification of the Cascadia Papsukkal architecture spike: worker → raw archive →
SQLite → read-only API → contracts → web client (CesiumJS) → Playwright. Verified by the
spike-verification pass on 2026-08-22 (macOS, Python 3.14.6, Node 22.22.2). All automated
tests run offline against committed fixtures; the live runs below used the public USGS/NWPS APIs.

## 1. What was proven

| Claim | Evidence |
|---|---|
| The worker ingests real USGS IV and NWPS gauge/stageflow payloads, archives every payload content-addressed before parsing, and is idempotent | `run-once` (live): thresholds 0 new rows, forecast 0 new rows (unchanged upstream since the previous run), USGS 20 new 15-min values; 23 raw artifacts under `data/raw/<aa>/<bb>/<sha256>.json` |
| The API serves the whole SPIKE API SPEC read-only, with knowledge time on every read | 28 probes (below): all spec endpoints 200; `POST` → 405; `as_of=garbage` → 422; unknown basin → 404; `/docs` → 404 (CDN-free), `/openapi.json` 200 |
| Every ContractEnvelope / SceneSummary the API emits validates against `cascade_contracts` **and** the web client's zod schemas | 9 envelopes + 4 scene summaries validated with `ContractEnvelope.model_validate_json` / `SceneSummary.model_validate_json`; 7 live zod checks pass (`apps/web/src/contracts/live-api.test.ts`) |
| Thresholds are official NWPS with basis + datum; Green River categories are computed from FLOW in cfs | MVEW1: `basis=stage unit=ft datum=NGVD29 23.5/28/30/32`; AUBW1: `basis=flow unit=cfs datum=null 6000/9000/12000/14000`, observed 297 cfs → `observed_category=none` ("Observed flow 297 cfs is below action flow 6000 cfs (official NWPS)"), headroom basis flow 5703 cfs, forecast crest 310.83 cfs → none |
| UNKNOWN is a real output with a reason; replay before ingestion returns UNKNOWN/missing, never current data | `?as_of=2026-01-01T00:00:00Z`: MVEW1 `observed=null`, `observed_category=unknown` ("no official NWPS thresholds known for this point"), thresholds/forecast/trend/headroom null, provenance ref `source_kind=UNKNOWN freshness=missing`, `time.mode=past`; Skagit hazard `unknown` ("no official NWRFC forecast known at this knowledge time"); `/system/health` → `degraded`, all products `missing` |
| A displayed number is traceable to bytes in the archived payload | Observation row 3438 (`station:usgs:12200500`, stage 10.57 ft NGVD29, valid 2026-08-22 13:45Z, quality `["provisional"]`, qualifier_raw `P`, raw_artifact_id 26) → artifact sha256 `2f1db4ac8ad2639e2d2c914e4e045da67601de728c3784fedb1a67027078cfe9` (288,399 bytes, `waterservices.usgs.gov/nwis/iv/...period=PT72H`) → `{"value":"10.57","qualifiers":["P"],"dateTime":"2026-08-22T06:45:00.000-07:00"}` under site 12200500 / 00065 (`noDataValue` −999999) |
| The web client renders the real backend, not only the stub | Playwright suite passes 4/4 against the real API (`E2E_LIVE_API=1`) and 4/4 against the fixture stub; screenshots of the live run in `tests/e2e/__screenshots__/live-api/` |
| Web quality gates | `contracts:check` OK, `tsc` clean, eslint clean, vitest 27 passed (+7 live checks skipped offline), `vite build` OK, react-doctor **90 / 100** (1 warning: `deslop/unused-export` on the documented `registerBasemap` hook) |

## 2. Exact commands and outcomes

All from the repository root unless stated. Quote the path (it contains a space).

### 2.1 Backend offline tests

```
source .venv/bin/activate && python -m pytest -q
# 40 passed in 25.86s
```

### 2.2 Worker live, then API

```
python -m cascade_worker seed
# {"sources": 3, "products": 3, "basins": 6, "stations": 6, "forecast_points": 6}
python -m cascade_worker run-once        # network on; 33 s wall
# [{"job":"nwps.fetch_thresholds","ok":true,"rows_written":0},
#  {"job":"nwps.fetch_forecast","ok":true,"rows_written":0},
#  {"job":"usgs.fetch_iv","ok":true,"rows_written":20}]
find data/raw -type f | wc -l            # 23
.venv/bin/uvicorn cascade_api.main:app --host 127.0.0.1 --port 8000 &   # background
```

Probes (`curl -s -o <file> -w "%{http_code}" -H 'Origin: http://localhost:5173' http://localhost:8000<path>`):

| # | path | status | bytes |
|---|---|---|---|
| 01 | `/basins` | 200 | 2234 |
| 02 | `/basins/basin:skagit/geometry?lod=state` | 200 | 14673 |
| 03 | `/basins/basin:skagit/geometry?lod=basin` | 200 | 22308 |
| 04 | `/basins/basin:skagit/state` | 200 | 2572 |
| 05 | `/basins/basin:green-duwamish/state` | 200 | 2593 |
| 06 | `/viz/basins` (6 items) | 200 | 10590 |
| 07 | `/viz/rivers?basin=basin:skagit` | 200 | 3732 |
| 08 | `/viz/rivers?basin=basin:green-duwamish` | 200 | 3720 |
| 09 | `/forecast-points/MVEW1/state` | 200 | 3732 |
| 10 | `/forecast-points/AUBW1/state` | 200 | 3720 |
| 11 | `/forecast-points/MVEW1/runs/latest` (run:3, NWRFC, issued 2026-08-21T15:05Z, primary stage ft NGVD29, 32 points, crest 11.1 ft @ 2026-08-24T00Z) | 200 | 2368 |
| 12 | `/forecast-points/AUBW1/runs/latest` (primary flow cfs) | 200 | 2818 |
| 13 | `/stations/station:usgs:12200500/series?variable=stage&hours=72` (ft, NGVD29, quality `["provisional"]`) | 200 | 19066 |
| 14 | `/stations/station%3Ausgs%3A12113000/series?variable=flow&hours=72` (cfs, datum null; encoded colons accepted) | 200 | 19106 |
| 15–16 | `/scene/summary?band=orbital` / `band=state` (basins only, 6 items) | 200 | 10670 / 10668 |
| 17–18 | `/scene/summary?band=basin&basin=basin:skagit` / `band=river` (basins 1 + rivers 1) | 200 | 6378 |
| 19 | `/search?q=ska` (basin + forecast_point + station) | 200 | 412 |
| 20 | `/search?q=aub` (AUBW1, WRAW1 and both stations) | 200 | 607 |
| 21 | `/system/health` (`ok`; usgs/nwps healthy; usgs-iv age 1101 s current, nwps-forecast 82041 s current, nwps-thresholds 1708 s current) | 200 | 415 |
| 22 | `/openapi.json` | 200 | 9042 |
| 23 | `/basins/basin:skagit/state?as_of=2026-01-01T00:00:00Z` (mode past, hazard unknown) | 200 | 2462 |
| 24 | `/forecast-points/MVEW1/state?as_of=2026-01-01T00:00:00Z` (everything null/unknown with reason) | 200 | 1139 |
| 25 | `/system/health?as_of=2026-01-01T00:00:00Z` (`degraded`, providers unknown, products missing) | 200 | 370 |
| 26 | `/basins/basin:skagit/state?as_of=garbage` | 422 | — |
| 27 | `/basins/basin:nope/state` | 404 | — |
| 28 | `/docs` | 404 | — |
| — | `POST /basins` | 405 | — |

Response headers on every probe: `access-control-allow-origin: http://localhost:5173` (only for
allowlisted origins; an `Origin: http://evil.example` request gets no ACAO header),
`x-content-type-options: nosniff`, `referrer-policy: strict-origin-when-cross-origin`.

Validation (python, venv): `ContractEnvelope.model_validate_json` on probes 04–10, 23, 24 and
`SceneSummary.model_validate_json` on 15–18 — all OK. Checked values quoted in §1.

### 2.3 Web

```
cd apps/web
npm install                      # 0 vulnerabilities
npm run contracts:check          # contracts:check OK
npm run build                    # tsc --noEmit + vite build: dist/assets/index-*.js 4,467 kB (gzip 1,210 kB), 389 Cesium static files copied
npm test                         # vitest: 8 passed | 1 skipped (9 files); 27 passed | 7 skipped (34 tests)
npm run lint && npm run typecheck  # clean
```

Live zod check of the real API (new, env-gated, offline-skipped by default):

```
CASCADE_LIVE_API_BASE=http://localhost:8000 npx vitest run src/contracts/live-api.test.ts
# 7 passed
```

Playwright against the **real API** (the API must allow the `vite preview` origin; the spec
default allowlist is `http://localhost:5173` only):

```
CASCADE_CORS_ORIGINS=http://localhost:4173 .venv/bin/uvicorn cascade_api.main:app --host 127.0.0.1 --port 8000 &
cd apps/web && E2E_LIVE_API=1 npx playwright test -c ../../tests/e2e/playwright.config.ts
# 4 passed (36.5s)
```

Playwright against the **fixture stub** (canonical, offline with respect to science data):

```
cd apps/web && npm run e2e       # builds, starts dev/stub-api.mjs on :8000 and vite preview on :4173
# 4 passed (43.5s)
```

react-doctor:

```
cd apps/web && npx react-doctor@latest --verbose
# Score: 90 / 100 Great — 1 issue: deslop/unused-export src/layers/basemap/BasemapProvider.ts:41
```

### 2.4 Servers stopped

`pkill -f "uvicorn cascade_api.main:app"`; Playwright stops the stub and preview it started.
Verified: `pgrep -fl "uvicorn|stub-api.mjs|vite preview"` → none; `:8000` and `:4173` free.
(Port 5173 is held by an unrelated process on this machine and was not touched.)

## 3. Screenshots

- `tests/e2e/__screenshots__/live-api/skagit-basin-scene.png` and `mvew1-river-scene.png` — the
  web client over the **real API** (live NWPS/USGS data: crest 11.1 ft below action 23.5 ft NGVD29,
  forecast age 23.1 h, UNKNOWN susceptibility/forcing/agreement with reasons).
- `tests/e2e/__screenshots__/skagit-basin-scene.png` and `mvew1-river-scene.png` — the same
  scenes over the fixture stub (last writer: `npm run e2e`).

Screenshots are evidence, not visual-regression baselines (no pixel comparison is made).

## 4. Doctrine invariants checked

| Invariant | How checked | Result |
|---|---|---|
| The API never calls a provider (ARCHITECTURE §1) | `grep -rnE "^\s*(import|from)\s+(httpx|requests|aiohttp|urllib)" apps/api/src` | no matches; `ArchivingFetcher` lives in `packages/core/fetch.py` and is constructed only by the worker |
| Raw archived before parse (DATA_DOCTRINE §13, addendum §1) | `cascade_core/fetch.py`: bytes are sha256-hashed and written to the object store inside `fetch()` before `FetchResult` is returned to any parser; traceability row→artifact→bytes in §1 | holds |
| Provenance on every value (§1) | contract validators (`prov` keys must resolve; `Thresholds` with `basis=stage` must carry a datum) applied to every live envelope; each ref carries `source_kind`, `retrieved_at` (observations/forecasts/thresholds), `freshness`, `quality` | holds; EXPERIMENTAL "not yet computed" refs legitimately carry `freshness=missing` and no `retrieved_at` |
| Freshness computed at read time from cadence (§5) | `grep -rniE "stale\s*(=|:)\s*(bool|Column|mapped)" packages/core/src/cascade_core/models.py` → none; `compute_freshness()` in `freshness.py` derives current/stale/degraded from `valid_time`/`retrieved_at` vs cadence + grace (`DEGRADED_MULTIPLIER = 4`) | holds; ages in `/system/health` change between probes |
| Knowledge-time filtering (§11) | `routes.py` imports `as_known_at` and every read handler (9 call sites) goes through it; `as_of=2026-01-01` probes return UNKNOWN/missing | holds |
| Thresholds: official only, basis stage **or** flow, datum on stage, kcfs→cfs explicit (§6–§7, ADR-0009/0011) | `nwps/normalize.py` refuses stage thresholds without a datum (`NormalizeError`), flow thresholds in cfs; AUBW1/MVEW1 live values in §1; category reasons name basis, unit and datum | holds |
| Sentinels and qualifiers (§4) | USGS: provider-declared `noDataValue` → `quality=["sentinel"]`, `P` → `provisional` (row 3438); NWPS: `-9999`/NaN → `None` in `parser.py` | holds |
| Append-only (§8, §14) | `grep -rniE "\.(update|delete)\(|session\.delete|UPDATE |DELETE " packages/core/src packages/providers/*/src apps/worker/src` → none; second live `run-once` wrote 0 forecast/threshold rows | holds by code, not by DB roles (SQLite spike) |
| No Cesium types in application state (ADR-0007) | `grep -rni cesium apps/web/src/state` → none | holds |
| No secrets / no third-party scripts / CDN-free (addendum §4, §8) | `index.html` has a single `<script type="module" src="/src/main.tsx">`; hosts in the bundle are Cesium's embedded attribution/provider strings; only `tile.openstreetmap.org` (keyless) is requested at runtime; Swagger UI disabled | holds, with one note: the bundle contains Cesium's **library default** ion token constant (`eyJhbGciOi…`, public, shipped by `cesium` itself, unused because ion is never constructed) — a CI "key-shaped string" grep on `dist/` will flag it and needs an allowlist for that constant |
| CORS allowlist without credentials (addendum §6) | `allow_credentials=False`, methods GET/OPTIONS, origins from settings; evil origin gets no ACAO | holds |
| UNKNOWN never rendered as calm (§12) | live screenshot: susceptibility/forcing/agreement show `UNKNOWN` + reason + EXPERIMENTAL/MISSING badges; hazard `NONE` only where an official forecast exists | holds |

## 5. Fixes applied during verification

1. **E2E against the real API** (`tests/e2e/web/skagit-flight.spec.ts`): with `E2E_LIVE_API=1`
   the three fixture-value assertions (`10.59 ft (NGVD29)`, `6,660 cfs`, `11.10 ft (NGVD29)`)
   become shape assertions (`/^\d+\.\d{2} ft \(NGVD29\)$/`, `/^[\d,]+ cfs$/`); official thresholds
   (`23.5`, `NGVD29`) are asserted identically in both modes. Default (stub) behaviour unchanged.
2. **Live zod contract check** (`apps/web/src/contracts/live-api.test.ts`): validates every spec
   endpoint of a running API against the client schemas; skipped unless `CASCADE_LIVE_API_BASE`
   is set, so the offline suite stays offline.
3. **`tests/e2e/tsconfig.json`** now resolves Node types from `apps/web/node_modules` (lib
   `ESNext.Disposable`, `skipLibCheck`), so `apps/web/node_modules/.bin/tsc -p tests/e2e/tsconfig.json`
   typechecks the Playwright files (it failed on `node:path`/`__dirname` before).
4. Live-run screenshots preserved under `tests/e2e/__screenshots__/live-api/`.

No Python source, docs, `v1/` or `packages/contracts/` were modified.

## 6. Known gaps (unresolved; with reproduction)

1. **Real-API E2E needs an extra CORS origin.** The spec fixes the API default allowlist to
   `http://localhost:5173`, but `vite preview` (the Playwright origin) runs on :4173, so the first
   live E2E attempt failed on every test (requests returned 200 but the browser dropped them).
   Repro: start uvicorn without `CASCADE_CORS_ORIGINS`, run `E2E_LIVE_API=1 npx playwright test …`
   → `search-result` never appears. Workaround documented in §2.3; a decision is needed on whether
   :4173 joins the spec default (the stub already allows it).
2. **Cesium default ion token in the bundle** (see §4). Not a Cascade secret; needs an allowlist
   entry in the future CI secret grep, or a build-time replacement of `Ion.defaultAccessToken`.
3. **`/forecast-points/{LID}/runs/latest` returns `datum` for flow-primary points** (AUBW1:
   `primary: "flow", unit: "cfs", datum: "NGVD29"`). The datum applies to the `stage` values that
   also ride along in `points`, which is defensible, but the spec's flat `datum` field is ambiguous
   for flow-primary runs. Contract clarification, not a bug.
   *Resolved 2026-08-24 (ADR-0014): the field is now `stage_datum`, declared per column alongside
   `stage_unit`/`flow_unit`. This reading was right — the live AUBW1 stage column is populated.*
4. **Contract gaps carried from the implementers** (packages/contracts is read-only):
   `AgreementState` has no `reason` field (the UNKNOWN reason is rendered from client copy, not the
   envelope); `Regulation.class` does not allow `regulated_upper` (basins use it; the river item says
   `regulated`); the exported `location` tuple schema has untyped items; product ids follow the
   `/system/health` vocabulary (`product:usgs-iv`, `product:nwps-forecast`, `product:nwps-thresholds`)
   rather than the canonical fixture ids.
5. **Spike substitutions** (by design, listed for completeness): SQLite + `create_all` instead of
   PostGIS + Alembic (append-only by code, not roles); susceptibility, forcing and agreement are
   UNKNOWN with reasons; no NWS alerts, no SSE, no hydrograph in the UI; NWPS observed series parsed
   but not stored; CRNW1 forecast flow is null (no usable secondary series upstream); semantic-zoom
   band boundaries retuned to 900/450/90/8 km (documented in `apps/web/src/scene/bands.ts`);
   observation stage datum attributed from the NWPS gauge datum (V1_AUDIT §4.5); rate limiting is a
   per-host interval + concurrency cap without a circuit breaker; `DEGRADED_MULTIPLIER = 4` chosen
   where the doctrine leaves k open.
6. **Environment**: port 5173 is held by another process on this machine; dev against the real
   API needs `npx vite --port 5174` plus `CASCADE_CORS_ORIGINS=http://localhost:5174`.
   `npx react-doctor` sends telemetry by default (`--no-telemetry` suppresses the score).
7. **Cesium's default "ion" logo credit is rendered** (visible bottom-left in both live screenshots)
   although the Viewer is constructed ion-free. The Cesium attribution itself is welcome; the ion
   logo is misleading for an app that never calls ion. Decide the attribution treatment in
   `layers/basemap/` (keep the Cesium credit, drop the ion mark) during C1.

## 7. Post-verification contract bump (architect, 2026-08-22)

`packages/contracts` moved to **1.1.0** (additive): `SceneSummary.band` and `GeometryRef.lod`
accept `ground`; `Regulation.class` accepts `regulated_upper`; `AgreementState.reason` added.
Re-verified after the bump: backend `pytest -q` 40 passed; contract tests 7 passed; web
`contracts:gen` + `contracts:check` OK; vitest 27 passed / 7 skipped (live checks, env-gated).
