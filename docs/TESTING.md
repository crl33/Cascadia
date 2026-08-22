# TESTING — deterministic tests, provider fixtures, canaries, integration, E2E, hindcasting

V1 claimed "100% tested" with zero committed tests and a live script whose assertions
depended on the current snowpack (`V1_AUDIT.md` §6). V2's rule: **no claim without a
committed, deterministic test; live checks are canaries, never tests.**

## 1. Hierarchy

| Level | Runs on | Network | Data | Gate |
|---|---|---|---|---|
| Unit | every commit | none | in-memory | blocking |
| Adapter fixture | every commit | none | saved payloads in `tests/fixtures/<provider>/` | blocking |
| Contract | every commit | none | JSON Schema + fixture documents | blocking |
| Integration | every PR | none (containers) | PostGIS + SeaweedFS via testcontainers; fixtures | blocking |
| E2E (web) | every PR | none | API stub or seeded DB with fixed clock | blocking |
| Visual regression | every PR touching `apps/web` | none | fixture contracts, fixed clock/camera | blocking with review override |
| Performance regression | nightly + on demand | none | representative scenes | advisory → blocking once calibrated |
| Live canaries | scheduled (hourly/daily) | **yes** | real providers | never blocks CI; alerts on failure |
| Scientific evaluation (hindcast) | on method change + scheduled | none (archived data) | event datasets | blocks promotion of a method version |

## 2. Unit tests (packages/*)

Targets, each with edge cases listed in the test module docstring:

- category computation from official thresholds (stage basis, flow basis, kcfs↔cfs, missing
  categories, equality at threshold, datum mismatch ⇒ refusal);
- staleness/degraded computation from cadence + grace (boundaries, missing timestamps);
- timestamp handling (offsets across the November DST change, daily values with provider
  day boundaries, lexicographic-vs-chronological regression from V1);
- unit normalization (`pint` registry pins; round-trip; kcfs, acre-ft, in↔mm);
- quality flags (sentinels from `noDataValue`, provisional/approved, out-of-range);
- feature calculations (rate of rise with gaps, headroom, time-to-threshold, API with
  missing days, rain-exposed fraction from hypsometry with band edges, SWE anomaly);
- routing/topology (upstream/downstream recursion, cycles rejected);
- assessment logic (surface states, driver ranking, delta explanation);
- `as_known_at(T)` selection rules (revisions, superseded runs, backfilled flags);
- property tests (Hypothesis): a CONFIGURED threshold can never produce a category; a fallback
  can never carry `OFFICIAL_FORECAST`; staleness is monotone in time.

Scientific logic is tested with small hand-computable cases plus at least one literature or
published-data cross-check where available (e.g. NWPS category for a known historic crest).

## 3. Adapter fixture tests (packages/providers/*)

For every provider, fixtures are real captured payloads (redacted of nothing — they are
public data) stored with a `manifest.yaml` (URL pattern, captured at, notes). Required cases:

1. valid response (happy path; values, units, times, qualifiers parsed);
2. missing field (optional field absent; required field absent ⇒ typed parse error, raw
   archived, health event);
3. malformed response (truncated JSON, HTML error page, wrong content-type);
4. timeout / connection error (client raises provider error; retry policy exercised);
5. API outage (5xx; circuit breaker opens; no partial writes);
6. sentinel values (`−999999`, `−9999`, `−9000`, empty strings ⇒ `quality=sentinel`);
7. schema evolution (extra fields ignored; renamed field detected by canary, not test);
8. provider-specific: NWPS flow-defined categories; USGS DST offsets; AWDB daily day
   boundary and `median`; GRIB variable missing from a cycle.

Fixture capture is a tool (`tests/fixtures/capture.py`) that records and redacts nothing,
runs outside CI, and writes the manifest — so fixtures are refreshable and reviewable.

## 4. Contract tests (packages/contracts ↔ apps/web)

- JSON Schema is exported from Pydantic; fixture documents for every contract live in
  `packages/contracts/fixtures/`; schema validation of fixtures runs in Python and TypeScript.
- `apps/web` types are generated from the schema in CI; a diff between committed and
  generated types fails the build.
- API integration tests validate real responses against the schema.

## 5. Integration tests (apps/api, apps/worker, database)

- Fresh PostGIS container: migrations apply; roles/grants enforce append-only.
- Worker job against fixtures writes Observation/ForecastRun/Threshold rows with full
  provenance; re-running the job is a no-op (idempotency).
- Revision flow: a changed value for the same key produces a revision row; "current" view
  picks the latest; `as_known_at(T)` picks the one that existed at T.
- Zonal aggregation against a small synthetic raster and basin polygon with a known answer.
- API: state projections, series pagination, `as_of`, bbox/time limits enforced, SSE emits on
  new rows.
- Golden replay: seed the database from an event fixture; assert the assessment at several
  clock times equals stored golden outputs (updated only with an explicit review).

## 6. E2E and visual tests (apps/web)

- Playwright against the API with a seeded database and a **fixed clock** (no "now").
- Scenarios: search Skagit → camera flies (or cuts under reduced motion) → basin selected →
  panel shows OBSERVED/OFFICIAL badges and freshness → gauge selectable → timeline scrub
  changes state → layer inspector shows provenance → degraded source shows STALE, not calm.
- Visual regression scenes (fixed camera, fixed data): Cascadia overview, Skagit basin, river
  selection, snow layer, storm layer, event mode, night mode, degraded data.
- Accessibility checks: keyboard path through search → selection → panel; contrast on
  dark glass; reduced-motion path.

## 7. Scientific evaluation and hindcasting

- **Harness** (`packages/history`): given an event dataset and a method version, replay at
  clock times T₁…Tₙ with `as_known_at(Tᵢ)` only; record every assessment; compare against
  outcomes (official crests/categories, observed exceedance times).
- **Look-ahead audit**: the harness logs the `available_at` of every input; any input with
  `available_at > Tᵢ` is a harness failure (test), not a warning.
- **Metrics**: for categorical states — timeliness (lead time at which the state first
  reached the outcome category), hit/miss/false-alarm by basin; for indices — rank
  correlation with outcome severity across events; for probabilities (Phase 7) — reliability
  diagram, Brier score, skill versus official forecast and versus climatology, stratified by
  basin and regime.
- **Promotion rule**: a method version moves from EXPERIMENTAL to DERIVED (or may display
  probabilities) only when its evaluation report is committed, reviewed, and linked from the
  `Method` row.
- **Event Zero first**; additional events (November 2021 Skagit/Nooksack; November 2006;
  others) as the archive grows.

## 8. Live canaries (tests/canaries)

Scheduled, non-blocking, alerting. Each provider has one canary that asks: reachable?
expected schema present (fields we parse)? data flowing (latest valid time within cadence)?
thresholds unchanged (NWPS categories diff)? Rate limits respected (no 429s). Canary results
feed `/system/health`; `tests/canaries/v1_mapping_canary.py` is the first (verifies the seed
mappings and crests).

Canaries never assert on weather (no "SWE > 0"); they assert on *plumbing*.

## 9. Tooling

- Python: `pytest`, `pytest-asyncio`, `hypothesis`, `respx` (httpx mocking) or recorded
  fixtures, `testcontainers` (PostGIS, SeaweedFS), `schemathesis` for OpenAPI conformance, `ruff`,
  `mypy --strict` on `packages/contracts` and `packages/hydrology`.
- Web: `vitest`, Playwright (E2E + screenshots), `react-doctor` score gate, bundle-size check.
- CI layout: `unit` → `fixtures+contracts` → `integration` → `e2e` → `visual` (parallel
  where independent); `canaries` and `perf` on schedules.

## 10. Definition of "tested"

A feature is tested when: unit tests cover its logic and edge cases; any provider it touches
has fixtures for the eight cases in §3; its contract has a fixture; an integration test
exercises the write path and the `as_of` read path; and, if user-visible, an E2E scenario
covers the happy path and one degraded path. Agent-reported click-throughs do not count.
