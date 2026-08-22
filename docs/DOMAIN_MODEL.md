# DOMAIN MODEL — entities, identifiers, relationships, storage shape

Basin-centric, generic over variables, bitemporal, geospatial. This is the conceptual model
and the intended PostgreSQL/PostGIS shape; exact DDL lives in `migrations/` once Phase 0
implementation begins and must match this document or change it.

## 1. Identifier doctrine

Stable, human-readable, namespaced string ids used identically in the database, API, URLs,
replay, tiles and analytics. Display labels are never identity.

| Entity | Id pattern | Example |
|---|---|---|
| Basin / subbasin | `basin:<slug>` (slug from HUC or local name; HUC kept as attribute) | `basin:skagit`, `basin:skagit-sauk` |
| River reach | `reach:nhdplushr:<comid>` · `reach:nwm:<feature_id>` | `reach:nwm:24270288` |
| Gauge station | `station:usgs:<site_no>` · `station:snotel:<triplet>` · `station:<agency>:<id>` | `station:usgs:12200500`, `station:snotel:515:WA:SNTL` |
| Forecast point | `fp:nwps:<LID>` | `fp:nwps:MVEW1` |
| Reservoir / lake | `reservoir:<slug>` · `lake:<slug>` | `reservoir:ross-lake`, `reservoir:howard-hanson` |
| Dam | `dam:nid:<nid_id>` | `dam:nid:WA00089` (example shape) |
| Flood defense | `levee:nld:<system_id>` | |
| Community / exposure area | `place:census:<geoid>` · `area:<slug>` | |
| Data source / product | `src:<slug>` / `product:<slug>` | `src:usgs-nwis-iv`, `product:nwm-v3-medium-range` |
| Historical event | `event:<yyyy-mm>-<slug>` | `event:2025-12-western-wa-ar` |
| Method / model version | `method:<name>@<semver>` | `method:rain-exposed-fraction@1.0.0` |

Geometry-bearing entities also carry `geom` (PostGIS, EPSG:4326 storage; analysis in an
equal-area projection, e.g. EPSG:5070 or a UTM zone 10N variant) and a simplified display
geometry per zoom band (materialized, regenerable).

## 2. Entity catalogue

### 2.1 Geography (static-ish; versioned by dataset release)

- **Basin** — a watershed polygon with `huc` (when HUC-aligned), `outlet_station_id`,
  `regulation_class`, `area_km2`, `hypsometry` (area by elevation band; JSONB or child table),
  `parent_basin_id` (subbasins nest), `display_geom_lod[]`.
- **RiverReach** — flowline segment with `from_node`/`to_node`, `downstream_reach_id`,
  `nhdplus_comid`, `nwm_feature_id`, `stream_order`, `length_km`, `basin_id`.
- **Station** — observation site: `agency`, `external_id`, `geom`, `elevation_m`,
  `vertical_datum`, `station_type` (stream / snow / met / reservoir / soil),
  `basin_id`, `reach_id` (nullable), `drainage_area_km2`, `time_zone`.
- **ForecastPoint** — NWS forecast location: `lid`, `station_id` (USGS), `reach_id`,
  `upstream_fp_id`, `downstream_fp_id`, `rfc`, `wfo`, `datums[]`, `forecast_reliability`,
  `in_service`.
- **Reservoir / Lake** — `dam_id`, `operator`, `purpose[]`, `flood_control_rule_curve`
  (seasonal table with provenance), `capacity_m3`, `geom` (pool polygon), `basin_id`,
  `regulates_reach_ids[]`.
- **Dam** — `nid_id`, `owner`, `height_m`, `hazard_class`, `geom`.
- **FloodDefense** — levee/dike/floodwall/channel: `kind`, `nld_system_id`, `design_height`,
  `geom` (line/polygon), `protects_area_id`, attributes verbatim from source.
- **ExposureArea / Community** — `place_id`, population and asset attributes (later phases),
  `geom`, `downstream_of_reach_ids[]`.

Relationships: Basin ⟶ contains Reaches, Stations, Reservoirs; Reach ⟶ downstream Reach
(graph); Station ⟶ observes Reach/Basin; ForecastPoint ⟶ Station; Reservoir ⟶ regulates
Reaches; FloodDefense ⟶ protects Area; Area ⟶ downstream of Reaches.

### 2.2 Sources (reference data)

- **DataSource** — `authority`, `kind` (observed/official_forecast/modeled/derived/static),
  `access` (mechanism, base URL, auth, rate limit), `license`, `docs_url`.
- **SourceProduct** — a specific feed of a source: `variables[]`, `spatial_scope`
  (point/grid/reach/polygon), `expected_cadence`, `grace`, `history_depth`,
  `missing_semantics`, `quality_flag_schema`, `unit_by_variable`.
- **Variable** registry — `id`, `canonical_unit`, `dimension`, `description`, `valid_range`.
- **Method** — `name`, `version`, `inputs[]` (variables/features), `description`, `code_ref`,
  `evaluation_status` (unevaluated / hindcast-evaluated), `evaluation_report_url`.

### 2.3 Values (append-only, bitemporal)

- **RawArtifact** — `product_id`, `fetched_at`, `request` (URL/params, redacted), `sha256`,
  `object_key`, `bytes`, `content_type`, `http_status`. Everything parsed points here.
- **Observation** — `station_id | reach_id | basin_id | grid_cell_ref` (exactly one scope),
  `product_id`, `variable`, `value` (double), `unit`, `valid_time`, `retrieved_at`,
  `available_at`, `quality[]`, `qualifier_raw`, `revision_of` (nullable), `raw_artifact_id`.
  Partitioned by month on `valid_time`; unique on `(product_id, scope, variable, valid_time, revision_seq)`.
- **ForecastRun** — `product_id`, `model_version`, `issued_at`, `retrieved_at`,
  `available_at`, `horizon_hours`, `member` (nullable; `mean`/`p10`… for percentiles),
  `scope`, `raw_artifact_id`, `supersedes_run_id` (nullable).
- **ForecastValue** — `run_id`, `variable`, `valid_time`, `value`, `unit`. Partitioned by
  `issued_at` month.
- **Threshold** — `fp_id | station_id | reach_id`, `category` (action/minor/moderate/major
  and low-water if needed), `value`, `unit`, `basis` (stage/flow), `vertical_datum`,
  `source_kind` (OFFICIAL from NWPS or CONFIGURED), `effective_from`, `retrieved_at`,
  `raw_artifact_id`. New values are new rows.
- **GridProduct** — index of archived gridded files: `product_id`, `issued_at`, `valid_time`,
  `variable[]`, `object_key`, `crs`, `bbox`, `resolution`, `format` (GRIB2/NetCDF/COG/Zarr),
  `bytes`. Values are not stored in PostgreSQL; basin aggregates are.
- **DerivedFeature** — `feature` (registry id), `scope` (basin/reach/station), `window`
  (e.g. `24h`, `7d`, null), `valid_time`, `computed_at`, `available_at`, `method_id`,
  `value`, `unit`, `percentile` (nullable), `climatology_ref`, `confidence_label`,
  `inputs` (array of `{table, id}`), `raw_inputs_hash`. Append-only.

### 2.4 Intelligence

- **Assessment** — one row per (`scope`, `surface`, `horizon`, `computed_at`):
  `surface` ∈ {susceptibility, forcing, hazard, model_agreement}, `state` (categorical),
  `score` (nullable, experimental), `probability` (nullable; only when permitted by
  `DATA_DOCTRINE.md` §9), `method_id`, `drivers` (structured list — feature, value, delta,
  direction, rank, source, as_of), `mitigating_factors`, `confidence_label`, `available_at`.
- **ExplanationDelta** — materialized diff between two Assessments of the same scope/surface:
  `from_id`, `to_id`, `state_change`, `driver_deltas`.
- **ModelAgreement** (Assessment subtype) — `sources[]`, `crest_magnitude_spread`,
  `crest_timing_spread_h`, `category_disagreement`, `explanation`.
- **OfficialAlert** — NWS alerts/products verbatim: `id`, `event`, `severity`, `areas`,
  `onset`, `expires`, `issued_at`, `headline`, `raw`.

### 2.5 History

- **HistoricalEvent** — `id`, `name`, `start`, `end`, `basins[]`, `summary`, `sources[]`.
- **EventTimelineEntry** — `event_id`, `at`, `kind` (forecast_issued, warning_issued,
  crest_observed, reservoir_action, levee_incident, evacuation, declaration, note),
  `scope`, `ref` (pointer to the row that is the evidence), `text`, `source_url`.
- **HindcastRun** — `event_id`, `method_id`, `clock_times[]`, `results` (object key),
  `metrics` (JSONB), `created_at`.

## 3. What is a table, what is not

| Concept | Shape | Reason |
|---|---|---|
| Observation, ForecastValue, DerivedFeature, Assessment | tables, append-only, partitioned | volume, time queries, immutability |
| "Current state" per station/basin | **views** (latest non-superseded row per key) | never store a cache that can drift |
| Staleness | computed in queries/API | doctrine §5 |
| BasinState / SnowState / SoilState / HydraulicState / ReservoirState | **API projections** over DerivedFeature + Observation, not tables | avoids hard-coding variable sets (the V1 mistake) |
| Hypsometry, rule curves, drivers | JSONB on the owning row | small, read-whole, versioned with the row |
| Gridded products | object storage + index table | never rasters inside PostgreSQL |
| Display geometries per LOD | materialized columns/tables, regenerable | renderer needs them; science does not |

## 4. Spatial operations the model must support

- basin-average of a grid for a valid time (mask precomputed per basin per grid definition);
- fraction of basin area below an elevation (hypsometry lookup, no raster at request time);
- intersection of snow-covered area with below-snow-level area;
- reaches upstream/downstream of a station (recursive CTE on `RiverReach`);
- reservoirs regulating a reach; communities downstream of a reach;
- nearest stations to a basin by type and elevation band.

## 5. Extensibility contract

Adding a variable = one row in the Variable registry + one parser. Adding a feature = one
Method row + one function. Adding a source = DataSource + SourceProduct rows + an adapter +
fixtures. None of these require schema migration. Adding a new *entity type* (e.g. tide
station) is a migration and an ADR.

## 6. Seed set (Phase 1)

| Basin | Outlet forecast point | USGS | Regulation class | Notes |
|---|---|---|---|---|
| `basin:skagit` | `fp:nwps:MVEW1` (upstream `CONW1`) | 12200500 | regulated upper; natural Sauk | NGVD29 datum at fp; flow-defined? no, stage |
| `basin:nooksack` | `fp:nwps:NKSW1` | 12213100 | natural; tidal at outlet | NAVD88 |
| `basin:snohomish-snoqualmie` | `fp:nwps:CRNW1` | 12149000 | natural (Tolt minor) | NAVD88 |
| `basin:cedar` | `fp:nwps:RNTW1` | 12119000 | partially regulated (Chester Morse) | NGVD29 |
| `basin:green-duwamish` | `fp:nwps:AUBW1` | 12113000 | regulated (Howard Hanson) | **flow-defined categories** |
| `basin:puyallup-white` | `fp:nwps:WRAW1` | 12100490 | regulated (Mud Mountain) | **flow-defined categories** |

SNOTEL seeds: 911 Rex River (Cedar), 908 Alpine Meadows (Snoqualmie), 515 Harts Pass (upper
Skagit, regulated headwater), 1011 MF Nooksack, 1068 Sawmill Ridge (Green), 1085 Cayuse Pass
(White). Basin polygons come from WBD HUC8/HUC10 unions, refined to the outlet station with
NLDI basin delineation (Phase 0 task).
