# VISUALIZATION CONTRACTS — backend-facing semantic state for any renderer

These contracts are produced by `packages/visualization` from the domain model and consumed
by the web client (and, in principle, an Unreal client). They carry **stable ids, semantic
values, time, provenance references, confidence labels, and optional normalized display
ranges**. They never carry colours, materials, shader names, CSS classes, camera instructions
or renderer types. They are published as JSON Schema from Pydantic models in
`packages/contracts/visualization/` and generate the web client's TypeScript types.

## 1. Common envelope

```jsonc
{
  "contract": "BasinVisualizationState",   // contract name
  "version": "1.0.0",                      // semver; additive changes bump minor
  "generated_at": "2026-08-22T09:00:00Z",  // when the backend produced this document
  "as_of": "2026-08-22T09:00:00Z",         // knowledge time the document reflects (replay sets this)
  "time": { "valid": "…", "mode": "now|past|forecast" },
  "items": [ … ],                          // the typed entries
  "provenance_refs": { "<ref>": ProvenanceRef }   // deduplicated
}
```

```jsonc
ProvenanceRef {
  "source_id": "src:nwps-v1",
  "source_kind": "OBSERVED|OFFICIAL_FORECAST|MODELED|DERIVED|EXPERIMENTAL|CONFIGURED|UNKNOWN",
  "product_id": "product:nwps-stageflow",
  "method_id": "method:rain-exposed-fraction@1.0.0",   // DERIVED/EXPERIMENTAL only
  "issued_at": "…", "valid_time": "…", "retrieved_at": "…",
  "freshness": { "state": "current|stale|degraded|missing|unknown", "age_seconds": 1260 },
  "quality": ["provisional"],
  "label": "NWRFC official forecast"                   // human label supplied by backend
}
```

```jsonc
Freshness  { "state": "current|stale|degraded|missing|partial|unknown", "age_seconds": n|null, "expected_cadence_seconds": n }
ConfidenceLabel  "high|moderate|low|unknown"            // categorical; numeric only when calibrated
DisplayRange { "min": 0, "max": 1, "scale": "linear|log", "unit": "…" }   // optional hint, never a colour
VisualTruthClass "observation|authoritative_model|cascade_derived|cartographic|cinematic"
```

## 2. BasinVisualizationState

One item per basin (and optionally subbasin) in the requested band/extent.

```jsonc
{
  "id": "basin:skagit",
  "name": "Skagit",
  "regulation_class": "regulated_upper|natural|partially_regulated",
  "surfaces": {
    "susceptibility": { "state": "low|moderate|high|very_high|unknown", "score": 0.62|null, "value": {"value": 62.0, "unit": "pct"}|null, "confidence": ConfidenceLabel, "prov": "<ref>", "truth": "cascade_derived", "experimental": true },
    "forcing":        { "horizon_h": 72, "state": "low|moderate|high|very_high|unknown", "score": 0.71|null, "value": {"value": 142.0, "unit": "mm"}|null, "spread": {"p10": …, "p90": …}|null, "prov": "<ref>", "truth": "cascade_derived", "experimental": true },
    "hazard":         { "horizon_h": 72, "official_category": "none|action|minor|moderate|major|unknown", "official_prov": "<ref>", "model_probability": {"model": "nwm-mr-ens", "exceeds": "minor", "fraction": 0.43}|null, "cascade_index": null, "truth": "authoritative_model" },
    "agreement":      { "state": "high|moderate|low|unknown", "explanation_ref": "…", "prov": ["<ref>", …] }
  },
  "tension": 0.0–1.0|null,        // a single derived scalar for "wake-up" intensity; documented method; never a probability
  "delta": { "since": "…", "susceptibility": "+1|0|-1", "forcing": "+1", "hazard": "0" },
  "headline_drivers": [ { "feature": "soil_saturation_percentile", "value": 94, "unit": "pct", "direction": "increases_susceptibility", "rank": 1, "prov": "<ref>" } ],
  "official_alerts": [ { "id": "…", "event": "Flood Watch", "severity": "…", "onset": "…", "expires": "…", "issuer": "NWS Seattle", "prov": "<ref>" } ],
  "geometry_ref": { "lod": "regional|state|basin", "tile_url_template": "…", "feature_id": "basin:skagit" },
  "display": { "label_priority": 1–5 }
}
```

## 3. RiverVisualizationState (reach / station / forecast point)

```jsonc
{
  "id": "fp:nwps:MVEW1",
  "station_id": "station:usgs:12200500",
  "reach_id": "reach:nwm:24270288",
  "basin_id": "basin:skagit",
  "observed": { "stage": {"value": 10.6, "unit": "ft", "datum": "NGVD29"}, "flow": {"value": 6670, "unit": "cfs"}, "valid_time": "…", "prov": "<ref>", "truth": "observation" },
  "observed_category": "none|action|minor|moderate|major|unknown",
  "trend": { "window_h": 6, "rate": {"value": 0.12, "unit": "ft/h"}, "direction": "rising|falling|steady|unknown", "prov": "<ref>", "truth": "cascade_derived" },
  "headroom": { "basis": "stage|flow", "to_category": "minor", "value": 17.4, "unit": "ft", "time_to_threshold_h": null, "prov": "<ref>" },
  "official_forecast": { "issued_at": "…", "crest": {"value": 11.1, "unit": "ft", "valid_time": "…"}, "category": "none", "prov": "<ref>", "truth": "authoritative_model" },
  "model_forecasts": [ { "model": "nwm-short-range", "crest": {…}, "prov": "<ref>" } ],
  "agreement": { "state": "high|moderate|low|unknown" },
  "thresholds": { "basis": "stage|flow", "unit": "ft", "datum": "NGVD29", "action": 23.5, "minor": 28, "moderate": 30, "major": 32, "prov": "<ref>" },
  "topology": { "upstream": ["fp:nwps:CONW1"], "downstream": [] },
  "regulation": { "class": "regulated", "regulated_by": ["reservoir:ross-lake", "reservoir:baker"] },
  "flow_visual_intensity": 0.0–1.0|null   // normalized display hint from percentile, documented; not a depth
}
```

## 4. ReservoirVisualizationState

```jsonc
{
  "id": "reservoir:howard-hanson",
  "dam_id": "dam:nid:…", "basin_id": "basin:green-duwamish", "operator": "USACE Seattle District",
  "pool": { "elevation": {"value": 1141.2, "unit": "ft", "datum": "…"}, "storage": {"value": …, "unit": "acre-ft"}, "valid_time": "…", "prov": "<ref>", "truth": "observation" },
  "flood_control": { "rule_curve_max_storage": {…}, "available_buffer": {"value": …, "unit": "acre-ft", "fraction": 0.71}, "prov": "<ref>", "truth": "cascade_derived" },
  "flows": { "inflow": {…}, "outflow": {…}, "net": {…}, "trend": "filling|drawing_down|steady|unknown" },
  "forecast_inflow": null | { "issued_at": "…", "peak": {…}, "prov": "<ref>" },
  "regulates": ["reach:…"],
  "freshness": Freshness
}
```

## 5. SnowVisualizationState

```jsonc
{
  "scope": "basin:skagit",
  "swe": { "basin_mean": {"value": 312, "unit": "mm"}, "anomaly_pct_of_median": 118, "by_band": [ {"band_m": [1000,1500], "swe_mm": 140, "sca_fraction": 0.62} ], "prov": "<ref>", "truth": "authoritative_model" },
  "points": [ { "station_id": "station:snotel:515:WA:SNTL", "swe": {…}, "elevation_m": 1978, "prov": "<ref>", "truth": "observation" } ],
  "snow_level": { "valid_time": "…", "elevation": {"value": 2100, "unit": "m"}, "prov": "<ref>", "truth": "authoritative_model", "offset_from_freezing_level_m": 300 },
  "rain_exposed_fraction": { "value": 0.58, "prov": "<ref>", "truth": "cascade_derived" },
  "rain_on_snow_exposed_fraction": { "value": 0.42, "prov": "<ref>", "truth": "cascade_derived" },
  "sca_raster_ref": { "tile_url_template": "…", "valid_time": "…", "prov": "<ref>" }
}
```

## 6. WeatherVisualizationState

```jsonc
{
  "scope": "region:cascadia|basin:…",
  "time": { "valid": "…", "issued_at": "…", "model": "nbm|hrrr|gefs|mrms" },
  "fields": [
    { "variable": "qpf_6h|qpe_1h|ivt|freezing_level|temperature_2m", "kind": "observed|forecast", "raster_ref": {"tile_url_template": "…", "cog_url": "…"}, "display_range": DisplayRange, "prov": "<ref>", "truth": "observation|authoritative_model" }
  ],
  "basin_aggregates": [ { "basin_id": "…", "qpf_mm_by_window": {"6": 18, "24": 61, "72": 142}, "spread": {…}, "prov": "<ref>" } ],
  "ar": { "present": true, "scale": 3, "ivt_max": 850, "orientation_deg": 230, "duration_h": 36, "prov": "<ref>", "truth": "authoritative_model" } | null
}
```

## 7. HazardVisualizationState (cross-basin summary for orbital/state bands)

```jsonc
{
  "horizon_h": 72,
  "items": [ { "basin_id": "…", "official_category": "…", "forcing_state": "…", "susceptibility_state": "…", "agreement_state": "…", "tension": 0.3, "alerts_count": 1 } ],
  "counts": { "basins_elevated": 3, "basins_watch": 1 },
  "as_of": "…"
}
```

## 8. SceneSummary (what the client asks for per camera band)

Request: `bbox`, `band` (orbital/state/basin/river/local/ground — `ground` added 2026-08-22 as an additive 1.1.0 change; the API serves `local` content for it until ground-band products exist), `t` (valid time), `as_of` (replay),
`layers[]`. Response: the subset of the contracts above appropriate to the band (e.g. orbital
→ HazardVisualizationState + weather region fields; basin → Basin/River/Snow/Reservoir states
for the selected basin only), each with its own `provenance_refs`. Never one monolithic scene
object for the whole world.

## 9. Explanation payload

```jsonc
{
  "scope": "basin:skagit", "surface": "hazard", "horizon_h": 72,
  "from": { "assessment_id": "…", "at": "…", "state": "moderate" },
  "to":   { "assessment_id": "…", "at": "…", "state": "high" },
  "drivers": [ { "feature": "basin_qpf_72h", "from": 98, "to": 142, "unit": "mm", "direction": "increases_hazard", "rank": 1, "prov": "<ref>" } ],
  "mitigating": [ { "feature": "reservoir_buffer_fraction", "value": 0.71, "direction": "decreases_hazard", "prov": "<ref>" } ],
  "model_agreement": { "state": "moderate", "detail": [ { "model": "nwps", "category": "minor" }, { "model": "nwm-mr-ens", "exceeds_minor_fraction": 0.6 } ] },
  "confidence": ConfidenceLabel,
  "rendering_note": "text is rendered from this structure; no free-form narrative"
}
```

## 10. Rules

1. Every item with a scientific value has `prov` and a `truth` class. Missing provenance is a
   schema violation, not a default.
2. No field may be named for a renderer concept (`color`, `material`, `opacity`, `camera`).
   `display_range`, `label_priority`, `tension` and `flow_visual_intensity` are the only
   presentation hints, each with a documented derivation.
3. Replay: the same request with `as_of=T` must return a document that is a pure function of
   the database as of T (DATA_DOCTRINE §11).
4. Versioning: additive changes bump minor; removals bump major; the client checks
   `version` and degrades gracefully. **1.2.0** (2026-08-24) added the optional
   `SurfaceState.value` (the quantity the state was banded from, with its unit) and
   `SurfaceState.spread` (named spread points in that same unit) — additive, so 1.1.0
   consumers keep validating. Neither is ever a probability, and where the surface is a
   Cascade derivation both are EXPERIMENTAL; `headline_drivers` remain the explanation.
   **1.3.0** (2026-08-26) added the optional `BasinVisualizationState.hydrologic_state` and
   `.state_change` (with `ReferenceWindow`, `SeasonalMultiple`, `RecordRank`, `BandBoundary`,
   `HydrologicState`, `StateChange`) — the Tier 0 high-tail level and its velocity. They sit
   **beside** `surfaces`, never inside `SurfaceState`, and that placement is the contract:
   `SurfaceState.score` is still the day-of-year percentile and nothing else, so no client can
   fuse a level with a velocity into one symbol. `HydrologicState.boundary` is a *condition*
   with three values, one of which is `unquantified` — the fail-closed state, which never means
   "separated". None of these fields is ever a probability, a return period or an AEP.
   **1.4.0** (2026-08-28) added the optional `BasinVisualizationState.antecedent_precip`
   (`AntecedentPrecip`): observed MRMS basin-mean precipitation summed over trailing 6/24/72 h
   windows, each entry carrying `window_end` (the newest observed hour, which anchors the
   window — never the wall clock), `hours_present`/`hours_expected`, and a `reason` whenever
   the sum covers fewer hours than the window. A partial total is a KNOWN UNDERESTIMATE and is
   never scaled up; truth class `observation`; a driver beside the surfaces, fused with
   nothing. Additive, so 1.3.0 consumers keep validating.
5. Contract tests: each schema has fixture documents; the web client's generated types are
   checked against them in CI; the API's responses are validated against the schema in
   integration tests.

## 11. Series and forecast-run bodies (not envelopes)

Three P1/P2 endpoints return raw series rather than visualization state. They are **not** part of
the versioned envelope above: they carry no `version`, they are not modelled in
`packages/contracts`, and their client types are hand-written zod in
`apps/web/src/contracts/schemas.ts` rather than generated. Promoting them is a follow-up
(ADR-0014); until then a change here is a coordinated API + client deploy.

`GET /stations/{station_id}/series?variable=stage|flow` — one variable, so one `unit` and one
`datum` describe the whole body. `datum` is null for flow.

`GET /forecast-points/{lid}/runs/latest` and `GET /forecast-points/{lid}/runs?start=&end=` — a run
is **two-column**: NWPS issues a primary and a secondary series together, and every point carries
both.

```jsonc
{
  "run_id": "run:130", "issued_at": "…", "issuer": "NWRFC",
  "primary": "flow",        // the variable this run is ISSUED on
  "unit": "cfs",            // the unit of the PRIMARY variable
  "stage_unit": "ft",       // unit of points[].stage, null when there is no stage column
  "flow_unit": "cfs",       // unit of points[].flow, null when there is no flow column
  "stage_datum": "NGVD29",  // gauge-zero datum of the STAGE column only; null with no stage column
  "points": [ { "t": "…", "stage": 56.8, "flow": 293.34 } ],
  "provenance": ProvenanceRef
}
```

Rules specific to these bodies:

1. **Units and datum are declared per column, never per run.** A flow-primary run may carry a
   fully populated stage column (AUBW1 does); that column's datum is real and is named for it.
   There is no field that means "the run's datum" — flow values never have one (ADR-0009,
   ADR-0014).
2. `stage_datum` non-null **implies** a stage column exists. Ingestion enforces the converse: a
   run with no stage column stores no datum, so the two are never out of step.
3. Values are returned as issued. Nothing is converted between units or datums at read time; a
   consumer that cannot match basis, unit and datum refuses to draw and says why, exactly as
   §10 rule 1 requires for envelope values.
