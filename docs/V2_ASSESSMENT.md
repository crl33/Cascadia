# V2 ASSESSMENT — architecture and science orientation (2026-08-22)

The first-assignment deliverable: what Cascade Oracle is, what V1 is worth, where the founding
brief's assumptions need correction, and the V2 system at a systems level. Everything here is
expanded in the sibling documents; this file is the index and the judgment calls.

## 1. Cascade Oracle in my own words

Cascade Oracle is a **state estimator with a conscience**. It continuously ingests the
observations, official forecasts and authoritative models that describe a Washington
watershed — gauges, snow pillows, radar rainfall, reservoir pools, NWRFC river forecasts,
National Water Model output, atmospheric-river diagnostics — and maintains, per basin, an
explicit estimate of three different things that people habitually conflate:

1. how primed the basin is to react (**susceptibility**: soil storage, snow state, baseflow,
   reservoir buffer, river percentile);
2. how much hydrologically significant water is coming and in what phase (**forcing**: basin
   QPF and its spread, intensity and duration, snow level, rain-exposed fraction, IVT);
3. what official and authoritative models say about threshold crossings and how much they
   agree (**hazard** and **model agreement**).

It then explains every change in those estimates from named features with provenance, replays
any past moment using only what was knowable then, and presents all of it through a
planetary-scale geographic interface where the world itself is the navigation. It never
issues warnings; it makes the reasoning of an expert observer continuous, inspectable and
honest about uncertainty.

## 2. V1 verdict: preserve / rewrite / discard / migrate

Full audit: [V1_AUDIT.md](V1_AUDIT.md). The short form:

| Preserve | Migrate (the idea, not the code) | Discard |
|---|---|---|
| station ↔ USGS ↔ NWPS ↔ SNOTEL mappings (live-verified) | threshold-source taxonomy → `source_kind` + official-only thresholds | request-driven ingestion |
| "UNKNOWN is legitimate" and per-value error disclosure | precursor ≠ risk → the three surfaces + agreement | Mongo latest-only cache |
| design tokens, calm→amber→red ladder, motion timings, source badges, `data-testid` discipline | sentinel handling → quality flags from `noDataValue` | process-local caches |
| the phased "earn your claims" product narrative | batched provider requests → rate-aware adapters | frozen per-variable contract |
| | | CRA/CRACO/Emergent tooling, 35 unused packages |
| | | TimesFM/ML forecasting plan, theater/TTS mode |
| | | live-endpoint "tests", agent self-reports |

Two findings the brief did not anticipate: V1's "honest unknown" for the Green and White
Rivers was a **parser bug** (NWS defines those flood categories in flow, not stage), and V1
shipped **third-party session recording** and an unauthenticated endpoint that makes the
server hammer NOAA/USGS on demand.

## 3. Corrections to the brief's assumptions

Ranked by consequence. Each has evidence in `research/` or `V1_AUDIT.md`.

1. **Official probabilistic river forecasts already exist for these basins.** NWPS exposes an
   experimental HEFS API (MEFP-forced ensembles, 45 members, 6-hourly to 30 days, daily 12Z,
   137 WA locations incl. MVEW1/CONW1/CRNW1/AUBW1) with exceedance quantiles (FACT,
   `research/hydrology-observations-and-official-forecasts.json`). The brief treated ensembles
   as "where available" and placed probabilities in Phase 7. Official probabilities belong in
   Phase 5 as *official* outputs; Cascade-derived probabilities stay gated behind hindcasting.
2. **Hydraulic headroom cannot be "threshold − stage".** Two of six seed points are
   flow-defined (AUBW1, WRAW1); NWPS reports their observations in kcfs; four points carry
   NGVD29 datums and two NAVD88, and the NGVD29→NAVD88 offset across Puget Sound gauges is
   3.50–3.93 ft — larger than the gap between some NWS categories. Headroom is basis-aware
   (stage or flow), datum-checked, and expressed additionally as time-to-threshold
   ([HYDROLOGY.md](HYDROLOGY.md) §9, ADR-0009).
3. **The snow-level offset is a parameter, not a constant.** The "~1,000 ft below freezing
   level" rule is a broadcast rule of thumb; NWS research cited in the literature gives
   ~700 ft with a 500–1,500 ft range, and NBM v5.0 now publishes `SNOWLVL` (wet-bulb 0.5 °C
   height) with fifteen percentiles directly. Use the published snow level where it exists;
   derive with a stored, sensitivity-tested offset only where it does not.
4. **Event Zero is a rain-on-saturated-soil event, not a rain-on-snow event.** December 2025
   had near record-low snowpack; snow levels ran 6,000–9,000 ft; snowmelt was negligible
   (FACT, CW3E/UW OWSC). It is the right first hindcast — forecast evolution, regulation,
   levee behaviour, warning lead time are all richly documented — but it will barely exercise
   the snow logic. A rain-on-snow analog (e.g. November 2021 Nooksack/Skagit; February 1996)
   is needed as the second event before snow features are trusted.
5. **Regulation dominated three of the six outcomes in Event Zero.** Ross held ~99 % of
   inflow under USACE Section 7 control; Howard Hanson set a record pool; Mud Mountain used
   ~70 % of its flood pool. Reservoirs are not a Phase 4 nicety; the explanation layer is
   wrong without them for the Skagit, Green and White. Machine-readable operator data does
   exist — under USACE office code `NWDP` in the CWMS Data API, not where the brief assumed.
6. **Build USGS ingestion on the new OGC API.** The legacy `waterservices.usgs.gov/nwis/iv`
   service is scheduled for decommission in Q1 2027 with possible degradation from August
   2026; the replacement needs an API key (50/h anonymous vs 1,000/h keyed) and returns UTC
   timestamps, nulls instead of sentinels and `approval_status`.
7. **"Hazard" is not "risk".** The brief's three surfaces are right, but keep exposure and
   consequence (who is downstream) out of the hazard surface; hazard × exposure is a later,
   separately labeled product. Model agreement is promoted to an explicit fourth surface.
8. **Floodplain and frequency data have gaps in the flagship basin.** Skagit County has zero
   FEMA NFHL polygons (paper FIRMs), and Washington has no NOAA Atlas 14 volume (Atlas 2 from
   1973 until Atlas 15 in 2027). Floodplain layers and return-period labels must be sourced
   per basin and labeled accordingly.
9. **Western Washington radar QPE is structurally weak.** MRMS fills Olympic/Cascade gaps with
   gauge/PRISM and HRRR; Stage IV is not real-time over NWRFC (back-filled days later). Observed
   precipitation must carry quality covariates (RQI, gauge-influence) and never be shown as
   radar truth in the mountains.
10. **Infrastructure facts that changed the stack:** MinIO's repository is archived (use
    SeaweedFS/Garage in dev, R2/S3 in prod); `vite-plugin-cesium` is unmaintained (use
    Cesium's own static-copy pattern); Cesium ion's free plan is non-commercial with a
    mandatory logo (design for keyless/self-hosted terrain); CesiumJS 1.142+ has native vector
    tiles; PostgreSQL 18 + PostGIS 3.6 are current; TimescaleDB's useful features are
    TSL-licensed (native partitioning first).

Assumptions I kept: forcing-driven flooding with state as modulator; official models first; no
probability without hindcast evaluation; modular monolith + workers; PostGIS; no Kubernetes;
Cesium as renderer only; no audio.

## 4. V2 architecture at a systems level

[ARCHITECTURE.md](ARCHITECTURE.md). Workers ingest on schedules (never on request), archive
raw payloads, normalize into an append-only bitemporal PostgreSQL/PostGIS store, aggregate grids
to basins, compute versioned features and the four surfaces, and emit semantic visualization
contracts. A read-only FastAPI serves geography, state, series, assessments, explanation,
replay (`as_of`) and SceneSummary, with SSE notify-then-fetch. A Vite/React/TypeScript/CesiumJS
client renders contracts; it computes no hydrology and holds no Cesium types in application
state. Object storage holds raw and gridded products; PostgreSQL holds everything relational,
temporal and geospatial.

## 5. Canonical domain model

[DOMAIN_MODEL.md](DOMAIN_MODEL.md). Geography (Basin, RiverReach, Station, ForecastPoint,
Reservoir, Dam, FloodDefense, ExposureArea) with stable namespaced ids; sources (DataSource,
SourceProduct, Variable registry, Method); values (RawArtifact, Observation, ForecastRun/
ForecastValue, Threshold, GridProduct, DerivedFeature) — generic over variables, append-only,
with `valid_time`/`issued_at`/`retrieved_at`/`available_at`; intelligence (Assessment with
structured drivers, ExplanationDelta, ModelAgreement, OfficialAlert); history (HistoricalEvent,
EventTimelineEntry, HindcastRun). "States" are API projections, not tables.

## 6. Ingestion and persistence

ADR-0001/0002/0003/0004/0005/0013. PostgreSQL-backed job queue (Procrastinate) with
idempotency keys, per-host rate limits and circuit breakers; raw-before-parse archival;
typed parsers with fixture suites; freshness computed from per-product cadence and grace;
monthly partitioning managed by pg_partman; S3-API object storage with content-addressed keys.

## 7. Historical / hindcast architecture

[HYDROLOGY.md](HYDROLOGY.md) §12, [DATA_DOCTRINE.md](DATA_DOCTRINE.md) §11, ADR-0010,
[EVENT_ZERO.md](EVENT_ZERO.md). Knowledge time on every row; revisions and superseded runs
kept; a single `as_known_at(T)` helper as the only replay path; a harness that logs every input's
`available_at` and fails on look-ahead; metrics per basin and regime; a promotion rule from
EXPERIMENTAL to DERIVED. Event Zero is seeded from NWPS crests, USGS peaks, the IEM AFOS
archive of NWS Seattle products (exact issuance times), CW3E outlooks, USACE operations and
declarations.

## 8. Decisions settled before coding

ADR-0001 PostGIS · 0002 modular monolith + workers · 0003 Postgres-backed queue · 0004 object
storage · 0005 generic value model · 0006 web stack · 0007 renderer boundary · 0008 official
models first · 0009 units and datums · 0010 knowledge time · 0011 official-only thresholds ·
0012 repository strategy · 0013 partitioning first. All accepted on 2026-08-22 with evidence.

## 9. Documentation and implementation sequence

Delivered today: this doc set (core 8 + cinematic 7 + EVENT_ZERO + V1_AUDIT + 13 ADRs), the
ICM routing files, three project skills, the contracts package (Pydantic models, JSON Schema,
validated fixtures, tests), WBD basin geometry at two display LODs, and the architecture spike
(see `research/spike-report-2026-08-22.md`).

Next, in order ([ROADMAP.md](ROADMAP.md), [CINEMATIC_ROADMAP.md](CINEMATIC_ROADMAP.md)):

1. Phase 0 completion: Alembic schema on PostGIS, Procrastinate worker, provider protocol with
   fixtures and canaries for USGS (OGC API), NWPS (gauges, stageflow, HEFS), AWDB; NLDI/WBD
   basin refinement and 3DEP hypsometry; observability.
2. Phase 1: thirty days of continuous river truth with replay golden tests; the spike client
   promoted to C1/C2.
3. Phase 2 and 3 in parallel: NBM/HRRR/GEFS/MRMS grid pipeline with basin aggregation;
   SNOTEL/SNODAS/VIIRS/SMAP/NWM-land fusion and the two snow fractions.
4. Phase 4: USACE CWMS (`NWDP`), A2W, NID, NLD; regulated-reach awareness.
5. Phase 5: NWM and HEFS fusion, model agreement, forecast evolution.
6. Phase 6: Event Zero reconstruction and the hindcast harness; then a rain-on-snow analog.
7. Phase 7 only after 6 publishes reliability.

## 10. Open questions that need the owner, not the engineer

- Commercial status of the product (Cesium ion Community terms, Synoptic licensing, Ecology
  GIS non-commercial clause, WA DNR lidar redistribution).
- Whether to pursue data agreements (King County HIC, SPU gauges, FEMS RAWS API role).
- Which second historical event to reconstruct for snow behaviour.
- Hosting: managed PostgreSQL without TimescaleDB is fine; S3 vs R2 decides egress costs.
