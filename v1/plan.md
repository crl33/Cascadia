# plan.md — Cascade Oracle (Phase 1 MVP)

## 1) Objectives
- Prove the **core real-data workflow** works end-to-end (USGS IV + 24h series + NWPS flood stages + risk computation + source labeling) via an isolated Python POC.
- Build a **cinematic command-center** React UI powered by a FastAPI data adapter, with trustworthy labeling (observed vs official vs fallback) and graceful failure modes.
- Establish an extensible architecture: config-driven stations, typed API responses, MongoDB cache/history for snapshots and time-series.

---

## 2) Implementation Steps

### Phase 1 — Core Data POC (Isolation; do not proceed until stable)
**Goal:** Validate external integrations + normalization logic for all 6 stations.

1. **Websearch (best practices / current endpoints):** confirm current USGS Water Services IV/JSON usage and NOAA NWPS endpoints/schema for flood categories (action/minor/moderate/major).
2. Create `poc_hydro.py` that:
   - Loads a local station config (6 stations: USGS site + NWPS LID + optional fallback thresholds).
   - Fetches USGS instantaneous values for `00065` (gage height) + `00060` (discharge).
   - Fetches USGS time-series for last 24h (for hydrograph) with consistent timestamp parsing.
   - Fetches NWPS flood stage thresholds by LID; extracts categories into a normalized structure.
   - Computes `risk_state` = `calm/watch/elevated/flood/unknown` using **observed stage** vs thresholds.
   - Emits a single JSON report per station including **source badges** for thresholds and data freshness.
3. Iterate until the POC passes for all stations:
   - Handle missing params (e.g., some stations lacking 00060/00065 at times).
   - Handle stale or empty series.
   - Handle NWPS failure/timeouts and correct fallbacks.
4. Define the **canonical normalized data contract** from the POC (fields + types) to be reused by FastAPI (Pydantic models).

**Phase 1 User Stories (POC):**
1. As a developer, I can run one script and see live readings + 24h series for all 6 stations.
2. As a developer, I can see which stations are missing USGS parameters and why.
3. As a developer, I can see NWPS stages when available and a clearly marked fallback when not.
4. As a developer, I can confirm risk-state outputs match thresholds.
5. As a developer, I can confirm “last updated” and stale detection logic using timestamps.

---

### Phase 2 — V1 App Development (Build around proven core)
**Backend (FastAPI + MongoDB)**
1. Implement project structure:
   - `server.py` (FastAPI app + routes)
   - `lib/types.py` (Pydantic response models from POC contract)
   - `lib/stations.py` (config loader; seeds Mongo `stations`)
   - `lib/usgs.py` (adapter)
   - `lib/nwps.py` (adapter)
   - `lib/risk.py` (risk computation + stale rules)
   - `lib/cache.py` (Mongo: stations/snapshots/history with TTL)
   - `lib/fallback_data.py` (explicit demo/fallback payloads)
2. MongoDB collections:
   - `stations` (config + LIDs + coords + basin labels + fallback thresholds)
   - `snapshots` (latest normalized reading per station)
   - `history` (time-series cache for 24h; TTL)
3. Endpoints (typed):
   - `GET /api/system/status` (health, adapter status, cache age)
   - `GET /api/stations` (all stations + latest snapshot + threshold source labels)
   - `GET /api/stations/{id}` (station detail + 24h hydrograph + thresholds)
   - `POST /api/stations/{id}/refresh` (force refetch + update cache)
4. Refresh logic:
   - Default: serve cache if fresh; refresh in background/forced on POST.
   - Stale rules: mark stale if snapshot older than a defined window (e.g., >30–45 min).

**Frontend (React + Tailwind + Framer Motion + Recharts)**
1. Build cinematic shell + routing:
   - `/` dashboard, `/roadmap` full phase vision.
2. Core components:
   - `DashboardShell` (ambient gradients, glass panels)
   - `HeroStatusPanel` (system overview, last refresh, global state)
   - `RiverGaugeCard` (stage, flow, trend, risk badge, last updated, source badges)
   - `HydrographChart` (24h stage; optional flow overlay if present)
   - `RiskBadge`, `SourceBadge` (explicit labeling)
   - `PhaseRoadmap` (compact on dashboard; full page on /roadmap)
   - `SystemDisclaimer` (persistent: experimental, not official alerts)
3. Data flow:
   - `lib/api.js` client with polling (5 min) + manual refresh.
   - Loading/error/empty states; never disguise fallback as official.
4. UX behavior:
   - Calm (blue/cyan) by default; amber/red transitions only when risk changes.
   - Per-station stale indicator + global stale banner if many stations stale.

**Conclude Phase 2 with 1 full E2E test run** (testing agent): dashboard load, station detail, refresh, failure mode.

**Phase 2 User Stories (V1):**
1. As a user, I open the dashboard and immediately see a calm, cinematic command-center view.
2. As a user, I see 6 river stations with current stage/flow, risk state, and last-updated time.
3. As a user, I can open a station and view a 24h hydrograph.
4. As a user, I can manually refresh and also rely on 5-minute auto-refresh.
5. As a user, I can distinguish official NWPS thresholds vs configured fallback via source badges.
6. As a user, I see a clear disclaimer that this is not an official emergency alert system.

---

### Phase 3 — Testing, Hardening, Polish
1. Add backend unit tests for adapters (mock responses) + risk logic edge cases.
2. Add frontend state tests (loading/error/stale) and visual regression spot checks.
3. Performance + resilience:
   - Debounce refresh; timeouts; retries with backoff.
   - Ensure caching prevents aggressive polling.
4. UI polish pass:
   - Improve typography/spacing, motion restraint, and risk-state transitions.
5. Run testing agent E2E again; fix until stable.

**Phase 3 User Stories (Polish):**
1. As a user, if USGS or NWPS is down, I still see a graceful state with clear labeling.
2. As a user, I can tell when data is stale and when it last refreshed.
3. As a user, charts render reliably across desktop and mobile.
4. As a user, risk-state transitions feel subtle and credible, not alarming.
5. As a user, the system status page reflects partial outages without breaking the dashboard.

---

### Phase 4 — Feature Additions (Only after Phase 1–3 are stable; no fake foresight)
- Add Phase 2 “Precursor Intelligence” inputs (SNOTEL, precip, soil moisture) behind feature flags.
- Add Phase 3 simple outlook (rate-of-rise, threshold crossing ETA) with explicit “experimental” labeling.
- Expand station set and basin grouping; admin tooling for station config edits.

**Phase 4 User Stories (Expansion):**
1. As a user, I can see basin-level precursor context alongside each river.
2. As a user, I can view an experimental outlook with transparent methodology.
3. As a user, I can filter stations by basin and risk.
4. As a user, station thresholds can be updated without redeploying the UI.
5. As a user, historical snapshots enable basic trend comparisons across storms.

---

## 3) Status — Phase 1 + 1.5 + 2A COMPLETE ✅

### Phase 1 (delivered earlier)
- ✅ POC validated, FastAPI + React cinematic dashboard, 6 stations live, NWPS thresholds where mappable, doctrine for unknown stations enforced.
- ✅ E2E: backend 17/17, frontend 19/19.

### Phase 1.5 — Hardening Pass (delivered now)
- ✅ **Threshold taxonomy expanded to 4 explicit sources** with `validated` flag enforced end-to-end:
  - `official_nwps` → validated=True → used in risk calc
  - `configured_validated` → validated=True → used in risk calc
  - `configured_pending` → validated=False → NOT used; risk="unknown"
  - `thresholds_unavailable` → validated=False → NOT used
- ✅ **Station config schema hardened**: `basin_group`, `active`, `notes` (uncertainty narrative per station), `fallback_validated`, `fallback_notes`. Schema auto-upgrades existing Mongo docs on backend startup.
- ✅ **Risk doctrine**: risk engine ONLY computes non-unknown when `thresholds.validated=True`. Verified by tests.
- ✅ **Refresh attempt tracking**: `last_attempt {attempted_at, succeeded_at, ok, errors, stations_attempted, stations_succeeded}` persisted in Mongo `co_meta`, surfaced in `SystemStatus` and HeroStatusPanel ("refresh OK / degraded" pill).
- ✅ **Basin + Risk FilterBar**: 6 basin chips (live counts) + 5 risk chips, mobile-scrollable, Clear button, empty-state when filters yield nothing.
- ✅ **StationDetailDialog rebuilt** with sectioned panels:
  - "Why this status?" panel — state + reason + description + validation warning when applicable
  - Observed data section (USGS source pill)
  - Flood thresholds section (source-pill matched to actual source)
  - Data provenance section
  - Station notes section
  - Phase 2 Precursor Intelligence placeholder (empty, dashed border, "Phase 2 • Planned")
- ✅ **Phase 2 attachment points**: `lib/precursors.py` (stub) + `BasinPrecursors` / `PrecursorSignal` Pydantic models + `StationSnapshot.precursors` field. Always `available=False` in 1.5; ready for SNOTEL/QPE/soil adapters in Phase 2.
- ✅ E2E: backend 24/24 (100%), frontend 13/13 user stories (100%). Zero bugs.

### Threshold matrix (live truth, Phase 1.5)
| Station | NWPS LID | Source | Validated | Risk |
|---|---|---|---|---|
| Cedar River at Renton | RNTW1 | official_nwps | ✅ | calm |
| Snoqualmie River near Carnation | CRNW1 | official_nwps | ✅ | calm |
| Skagit River near Mount Vernon | MVEW1 | official_nwps | ✅ | calm |
| Nooksack River at Ferndale | NKSW1 | official_nwps | ✅ | calm |
| Green River near Auburn | AUBW1 | thresholds_unavailable | ❌ | unknown (honest) |
| White River near Auburn | WRAW1 | thresholds_unavailable | ❌ | unknown (honest) |

## 4) What remains before Phase 2 can begin
1. Validate / configure Green & White river thresholds (gauge datums are non-standard) OR document permanently as observation-only.
2. Optionally promote select fallbacks to `configured_validated` once cross-checked with NWS sources, so the system stays informative if NWPS is briefly down.
3. Decide Phase 2 data providers + obtain access:
   - **Snowpack** → NRCS AWDB / SNOTEL (no auth; add adapter)
   - **Precipitation 24/72h** → NWS QPE / MRMS (decide source)
   - **Soil moisture proxy** → NLDAS-2 or RAWS sample
4. Define basin-tension scoring formula + confidence weighting.
5. Frontend slot for precursor section already wired (StationDetailDialog → station-section-precursors); turn on rendering when adapter returns `available=True`.

---

### Phase 2A — Snowpack Precursor Intelligence (DELIVERED)
- ✅ **NRCS AWDB / SNOTEL adapter** (`lib/snotel.py`, `lib/snotel_stations.py`) — public REST API at `wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data`. Single batched fetch returns SWE for all 6 basins.
- ✅ **6 basins mapped to validated upstream SNOTEL stations** (HUC-aligned, all `confidence=high`):
  | Basin | SNOTEL Station | Triplet | Elevation | HUC |
  |---|---|---|---|---|
  | Cedar / Lake Washington | Rex River | 911:WA:SNTL | 3,810 ft | 171100120102 |
  | Snoqualmie / Snohomish | Alpine Meadows | 908:WA:SNTL | 3,500 ft | 171100100501 |
  | Skagit | Harts Pass | 515:WA:SNTL | 6,490 ft | 171100050501 |
  | Nooksack | MF Nooksack | 1011:WA:SNTL | 4,940 ft | 171100040303 |
  | Green-Duwamish | Sawmill Ridge | 1068:WA:SNTL | 4,640 ft | 171100130104 |
  | Puyallup / White | Cayuse Pass | 1085:WA:SNTL | 5,260 ft | 171100140301 |
- ✅ **Live precursor fields**: SWE value/unit/timestamp, confidence (numeric+bucketed), mapping_confidence, station meta, plain-English interpretation, is_stale, mapping_note.
- ✅ **Doctrine enforced (verified by tests)**: SNOTEL signals NEVER affect `risk_state`. River risk and precursor are independent surfaces.
- ✅ **Frontend cinematic precursor UI**: PrecursorPanel with subtle snowpack glow, snowflake icon, source/confidence/mapping pills, "not a flood forecast" caption. HeroStatusPanel snowpack pill ("Snowpack • 6/6 basins"). Phase label updates to "Phase 2A • Snowpack Precursor Active". Detail dialog "Why this status?" panel explicitly notes precursors are context-only.
- ✅ **Phase 2 attachment slots remain open**: precipitation_24h / soil_moisture / basin_tension_score still None; PrecursorLayerStatus tracks each phase's active flag.
- ✅ **New endpoints**: `GET /api/system/snotel-stations`, `GET /api/system/precursors`, `POST /api/system/precursors/refresh`.
- ✅ E2E: backend 34/34 (100%), frontend 22/22 (100%). Zero bugs.

### Threshold + Precursor matrix (live truth, Phase 2A)
| Station | Threshold Source | River Risk | Snowpack Precursor | SWE |
|---|---|---|---|---|
| Cedar @ Renton | official_nwps | calm | Rex River (3,810 ft) | ~6.8 in |
| Snoqualmie @ Carnation | official_nwps | calm | Alpine Meadows (3,500 ft) | ~30.4 in |
| Skagit @ Mt Vernon | official_nwps | calm | Harts Pass (6,490 ft) | ~54.5 in |
| Nooksack @ Ferndale | official_nwps | calm | MF Nooksack (4,940 ft) | ~27.9 in |
| Green @ Auburn | thresholds_unavailable | unknown (honest) | Sawmill Ridge (4,640 ft) | ~0.2 in (melted) |
| White @ Auburn | thresholds_unavailable | unknown (honest) | Cayuse Pass (5,260 ft) | ~19.4 in |

### Uncertain mappings / API limitations
- **Single-station-per-basin** is a representative upstream signal, not a basinwide assessment (mapping_note discloses this).
- **Percent-of-normal not yet available**: AWDB centralTendency response shape needs more research; deferred to Phase 2B.
- **Lat/lon missing** for some SNOTEL stations (kept None rather than guessing).
- **3-day stale window**: SNOTEL publishes daily; UI auto-degrades confidence on stale data.

## 5) What remains for Phase 2B (Precipitation Accumulation)
1. Decide provider: NWS QPE vs MRMS vs NCEP/NLDAS-2.
2. Implement `lib/precip.py` adapter — basin-level 24h and 72h totals.
3. Decide aggregation: point sample at outlet vs basin-mean over HUC polygon.
4. Wire into `BasinPrecursors.precipitation_24h` (slot already exists).
5. Frontend: extend `PrecursorPanel` to render precipitation block.
6. Update HeroStatusPanel pill to surface combined "Snowpack + Precip" status.

## 6) What remains for Phase 2C / 2D
- **Phase 2C**: NLDAS-2 / RAWS soil moisture proxy → `BasinPrecursors.soil_moisture`.
- **Phase 2D**: weighted basin-tension formula (SWE melt risk × precip × soil × seasonality) → `basin_tension_score` with explicit confidence + explainability. Still NOT a flood prediction.

---

## 4) Success Criteria
- POC returns valid normalized JSON for **all 6 stations** with:
  - latest stage + flow (when available)
  - 24h series (or explicit empty with reason)
  - NWPS thresholds when available, otherwise explicit fallback threshold source
  - computed risk_state + stale indicator
- V1 dashboard:
  - loads reliably, auto-refreshes every 5 minutes, manual refresh works
  - shows per-station last-updated + stale warnings
  - hydrograph renders for each station
  - threshold/data sources are unambiguous (no fake officialness)
- Resilience:
  - partial API failures do not blank the app; errors are contained per station
  - caching reduces upstream calls and avoids aggressive polling
- UX:
  - cinematic calm-first aesthetic with restrained transitions for watch/flood states
  - roadmap + disclaimer present without cluttering the command-center focus
