/**
 * Runtime (zod) schemas for the contract parts the client consumes: ContractEnvelope,
 * BasinVisualizationState, RiverVisualizationState, ProvenanceRef, Freshness, plus the small
 * spike endpoints. Unknown additive fields are stripped (minor-version tolerance); the inferred
 * types are asserted assignable to the generated JSON-Schema types so the two cannot drift.
 */
import { z } from 'zod';
import type * as Generated from './generated';

const iso = z.string();
const nullableIso = iso.nullable().optional();

export const SourceKindSchema = z.enum(['OBSERVED', 'OFFICIAL_FORECAST', 'MODELED', 'DERIVED', 'EXPERIMENTAL', 'CONFIGURED', 'UNKNOWN']);
export const TruthClassSchema = z.enum(['observation', 'authoritative_model', 'cascade_derived', 'cartographic', 'cinematic']);
export const FreshnessStateSchema = z.enum(['current', 'stale', 'degraded', 'missing', 'partial', 'unknown']);
export const FloodCategorySchema = z.enum(['none', 'action', 'minor', 'moderate', 'major', 'unknown']);
export const SurfaceLevelSchema = z.enum(['low', 'moderate', 'high', 'very_high', 'unknown']);
export const AgreementLevelSchema = z.enum(['high', 'moderate', 'low', 'unknown']);
export const ConfidenceLabelSchema = z.enum(['high', 'moderate', 'low', 'unknown']);

export const FreshnessSchema = z.object({
  state: FreshnessStateSchema,
  age_seconds: z.number().int().nonnegative().nullable().optional(),
  expected_cadence_seconds: z.number().int().nonnegative().nullable().optional(),
});

export const ProvenanceRefSchema = z.object({
  source_id: z.string(),
  source_kind: SourceKindSchema,
  product_id: z.string().nullable().optional(),
  method_id: z.string().nullable().optional(),
  issued_at: nullableIso,
  valid_time: nullableIso,
  retrieved_at: nullableIso,
  freshness: FreshnessSchema,
  quality: z.array(z.string()).optional(),
  label: z.string(),
  raw_artifact_id: z.string().nullable().optional(),
});

export const QuantitySchema = z.object({ value: z.number(), unit: z.string(), datum: z.string().nullable().optional() });

const SurfaceStateSchema = z.object({
  prov: z.string(),
  truth: TruthClassSchema,
  state: SurfaceLevelSchema,
  horizon_h: z.number().nullable().optional(),
  score: z.number().nullable().optional(),
  // contract 1.2.0: the headline quantity `state` was banded from, and the named spread points
  // that came with it. `spread` keys are left opaque on purpose — they are the method's own
  // statistic (`pointwise_p90` is a basin mean of a per-cell percentile, NOT a basin-scale
  // 90th percentile) and the client renders the key it is given rather than relabelling it.
  value: QuantitySchema.nullable().optional(),
  spread: z.record(z.string(), z.number()).nullable().optional(),
  confidence: ConfidenceLabelSchema.optional(),
  experimental: z.boolean().optional(),
  reason: z.string().nullable().optional(),
});

const HazardStateSchema = z.object({
  prov: z.string(),
  truth: TruthClassSchema,
  horizon_h: z.number(),
  official_category: FloodCategorySchema,
  official_prov: z.string().nullable().optional(),
  model_probability: z.record(z.string(), z.union([z.string(), z.number()])).nullable().optional(),
  cascade_index: z.number().nullable().optional(),
  reason: z.string().nullable().optional(),
});

const AgreementStateSchema = z.object({
  state: AgreementLevelSchema,
  // Present since contract 1.1.0 and previously stripped here, which is why the panel had
  // nothing to render: an UNKNOWN agreement without its reason is indistinguishable from
  // "the two forecasts agree" (docs/DATA_DOCTRINE.md §12).
  reason: z.string().nullable().optional(),
  explanation_ref: z.string().nullable().optional(),
  prov: z.array(z.string()).optional(),
});

const DriverSchema = z.object({
  feature: z.string(), value: z.number().nullable().optional(), unit: z.string().nullable().optional(),
  direction: z.string(), rank: z.number(), prov: z.string(),
});

/** Observed trailing-window precipitation (1.4.0). A partial window is a KNOWN UNDERESTIMATE
 * whose `reason` says how many hours are missing — render the caveat, never scale the number. */
const AntecedentPrecipSchema = z.object({
  window_h: z.number(),
  window_end: nullableIso,
  total: QuantitySchema.nullable().optional(),
  hours_present: z.number(),
  hours_expected: z.number(),
  truth: TruthClassSchema,
  prov: z.string(),
  reason: z.string().nullable().optional(),
});

const OfficialAlertSchema = z.object({
  id: z.string(), event: z.string(), severity: z.string().nullable().optional(), onset: nullableIso, expires: nullableIso,
  issuer: z.string(), prov: z.string(),
});

/* ---- Tier 0 (contract 1.3.0): level, velocity and the record they are read against --------
 *
 * These existed in `generated.ts` from the day the contract was bumped and were absent HERE, so
 * `z.object`'s minor-version tolerance stripped every one of them before the UI could see it:
 * the exact rank, the seasonal multiple, the state change and the boundary condition were
 * fetched, parsed away, and never rendered. Minor-version tolerance is still what we want for
 * genuinely unknown future fields — the fix is that a field the contract ALREADY declares must
 * not be unknown here, which the key check at the bottom of this file now enforces.
 *
 * `direction` is `z.string()` and not an enum on purpose: the generated contract types it as a
 * string, and a stricter runtime schema would drop an entire basin over a direction word this
 * build has not seen. The panel renders the word it is given.
 */

export const BandBoundarySchema = z.enum(['separated', 'near_band_edge', 'unquantified']);

export const SeasonalMultipleSchema = z.object({
  multiple: z.number(),
  reference: QuantitySchema,
  reference_percentile: z.number(),
  prov: z.string(),
});

export const RecordRankSchema = z.object({
  rank: z.number().nullable().optional(),
  of: z.number(),
  exceeds_record: z.boolean().optional(),
  previous_max: QuantitySchema.nullable().optional(),
  previous_max_day: z.string().nullable().optional(),
  reason: z.string().nullable().optional(),
  prov: z.string(),
});

export const ReferenceWindowSchema = z.object({
  doy_key: z.string(),
  window_days: z.number(),
  n: z.number(),
  independent_years: z.number(),
  period_start: z.number().nullable().optional(),
  period_end: z.number().nullable().optional(),
  method_id: z.string(),
});

export const HydrologicStateSchema = z.object({
  prov: z.string(),
  truth: TruthClassSchema,
  observed: QuantitySchema,
  day: z.string(),
  percentile: z.number().nullable().optional(),
  percentile_clamped: z.boolean().optional(),
  reference: ReferenceWindowSchema.nullable().optional(),
  rank: RecordRankSchema.nullable().optional(),
  multiple: SeasonalMultipleSchema.nullable().optional(),
  boundary: BandBoundarySchema.optional(),
  bands_within_sampling_error: z.array(SurfaceLevelSchema).optional(),
  reason: z.string().nullable().optional(),
});

export const StateChangeEntrySchema = z.object({
  window_h: z.number(),
  growth: z.number().nullable().optional(),
  direction: z.string(),
  from_value: QuantitySchema.nullable().optional(),
  to_value: QuantitySchema.nullable().optional(),
  span_h: z.number().nullable().optional(),
  rank: z.number().nullable().optional(),
  rank_of: z.number().nullable().optional(),
  rank_reason: z.string().nullable().optional(),
  reason: z.string().nullable().optional(),
  prov: z.string(),
});

export const BasinVisualizationStateSchema = z.object({
  id: z.string().regex(/^basin:[a-z0-9-]+$/),
  name: z.string(),
  regulation_class: z.string(),
  surfaces: z.object({ susceptibility: SurfaceStateSchema, forcing: SurfaceStateSchema, hazard: HazardStateSchema, agreement: AgreementStateSchema }),
  tension: z.number().nullable().optional(),
  headline_drivers: z.array(DriverSchema).optional(),
  official_alerts: z.array(OfficialAlertSchema).optional(),
  antecedent_precip: z.array(AntecedentPrecipSchema).optional(),
  outlet_forecast_point_id: z.string().nullable().optional(),
  geometry_ref: z.object({ lod: z.string(), feature_id: z.string(), url: z.string().nullable().optional() }),
  label_priority: z.number().optional(),
  // Tier 0. Both are OUTSIDE `surfaces` in the contract and stay outside here, because a client
  // that nested them under the susceptibility surface would be one step from fusing them into
  // its state — which is the composite the doctrine forbids.
  hydrologic_state: HydrologicStateSchema.nullable().optional(),
  state_change: z.array(StateChangeEntrySchema).optional(),
});

const ObservedRiverStateSchema = z.object({
  prov: z.string(), truth: TruthClassSchema,
  stage: QuantitySchema.nullable().optional(), flow: QuantitySchema.nullable().optional(), valid_time: iso,
});
const TrendSchema = z.object({
  prov: z.string(), truth: TruthClassSchema, window_h: z.number(), rate: QuantitySchema.nullable().optional(),
  direction: z.enum(['rising', 'falling', 'steady', 'unknown']),
});
const HeadroomSchema = z.object({
  basis: z.enum(['stage', 'flow']), to_category: FloodCategorySchema, value: QuantitySchema.nullable().optional(),
  time_to_threshold_h: z.number().nullable().optional(), prov: z.string(), reason: z.string().nullable().optional(),
});
const OfficialForecastSummarySchema = z.object({
  prov: z.string(), truth: TruthClassSchema, issued_at: iso, issuer: z.string(), crest: QuantitySchema.nullable().optional(),
  crest_valid_time: nullableIso, category: FloodCategorySchema, points: z.number(),
});
const ThresholdsSchema = z.object({
  basis: z.enum(['stage', 'flow']), unit: z.string(), datum: z.string().nullable().optional(),
  action: z.number().nullable().optional(), minor: z.number().nullable().optional(),
  moderate: z.number().nullable().optional(), major: z.number().nullable().optional(), prov: z.string(),
}).refine((t) => t.basis !== 'stage' || (t.datum != null && t.datum !== ''), { message: 'stage thresholds must carry a datum (ADR-0009)' });

export const RiverVisualizationStateSchema = z.object({
  id: z.string(),
  name: z.string(),
  station_id: z.string().nullable().optional(),
  reach_id: z.string().nullable().optional(),
  basin_id: z.string(),
  observed: ObservedRiverStateSchema.nullable().optional(),
  observed_category: FloodCategorySchema.optional(),
  observed_category_reason: z.string().nullable().optional(),
  trend: TrendSchema.nullable().optional(),
  headroom: HeadroomSchema.nullable().optional(),
  official_forecast: OfficialForecastSummarySchema.nullable().optional(),
  thresholds: ThresholdsSchema.nullable().optional(),
  topology: z.object({ upstream: z.array(z.string()).optional(), downstream: z.array(z.string()).optional() }).optional(),
  regulation: z.object({ class: z.string(), regulated_by: z.array(z.string()).optional() }).optional(),
  location: z.tuple([z.number(), z.number()]).nullable().optional(),
  flow_visual_intensity: z.number().nullable().optional(),
});

const envelopeBase = {
  contract: z.string(),
  version: z.string().optional(),
  generated_at: iso,
  as_of: iso,
  time: z.object({ valid: iso, mode: z.string() }),
  provenance_refs: z.record(z.string(), ProvenanceRefSchema),
};

/** Every `prov` / `official_prov` key in the items must resolve (mirrors the pydantic validator). */
function collectProvKeys(value: unknown, out: Set<string>): void {
  if (Array.isArray(value)) { value.forEach((v) => collectProvKeys(v, out)); return; }
  if (value && typeof value === 'object') {
    for (const [key, v] of Object.entries(value as Record<string, unknown>)) {
      if ((key === 'prov' || key === 'official_prov') && typeof v === 'string') out.add(v);
      else if (key === 'prov' && Array.isArray(v)) v.forEach((x) => typeof x === 'string' && out.add(x));
      else collectProvKeys(v, out);
    }
  }
}
const provResolves = <T extends { items: unknown[]; provenance_refs: Record<string, unknown> }>(env: T, ctx: z.RefinementCtx) => {
  const keys = new Set<string>();
  collectProvKeys(env.items, keys);
  const missing = [...keys].filter((k) => !(k in env.provenance_refs));
  if (missing.length) ctx.addIssue({ code: 'custom', message: `unresolved provenance refs: ${missing.join(', ')}` });
};

export const BasinEnvelopeSchema = z.object({ ...envelopeBase, items: z.array(BasinVisualizationStateSchema) }).superRefine(provResolves);
export const RiverEnvelopeSchema = z.object({ ...envelopeBase, items: z.array(RiverVisualizationStateSchema) }).superRefine(provResolves);
export const ContractEnvelopeSchema = z.object({
  ...envelopeBase,
  items: z.array(z.union([BasinVisualizationStateSchema, RiverVisualizationStateSchema])),
}).superRefine(provResolves);

export const SceneSummarySchema = z.object({
  band: z.string(), as_of: iso,
  basins: BasinEnvelopeSchema.nullable().optional(), rivers: RiverEnvelopeSchema.nullable().optional(),
});

/* ---- spike endpoints outside the visualization contracts ---- */
export const BasinListSchema = z.object({
  items: z.array(z.object({
    id: z.string(), name: z.string(), regulation_class: z.string(), outlet_forecast_point_id: z.string().nullable(),
    centroid: z.tuple([z.number(), z.number()]), bbox: z.tuple([z.number(), z.number(), z.number(), z.number()]),
    area_km2_wbd_sum: z.number(), huc8: z.array(z.string()),
  })),
  provenance: z.record(z.string(), z.unknown()),
});
export const GeoFeatureSchema = z.object({
  type: z.literal('Feature'),
  id: z.string().optional(),
  properties: z.record(z.string(), z.unknown()).nullable(),
  geometry: z.looseObject({ type: z.string() }),
});
export const SearchResultsSchema = z.object({
  items: z.array(z.object({
    id: z.string(), kind: z.enum(['basin', 'forecast_point', 'station']), name: z.string(), basin_id: z.string(),
    location: z.tuple([z.number(), z.number()]).nullable(),
  })),
});
const ProviderHealthSchema = z.object({ state: z.enum(['healthy', 'degraded', 'down', 'unknown']), last_success_at: iso.nullable(), last_error: z.string().nullable() });
export const HealthSchema = z.object({
  // Three-valued since the finding-C fix: `unknown` is "no evidence yet" — a fresh deployment
  // whose jobs have not run, or a knowledge time before ingestion — as distinct from `degraded`,
  // which is evidence that something failed or went stale. TopStrip already renders an unknown
  // health state with the neutral dot; parsing it as an error would paint that red instead.
  status: z.enum(['ok', 'degraded', 'unknown']),
  providers: z.record(z.string(), ProviderHealthSchema),
  freshness: z.record(z.string(), z.object({ age_seconds: z.number().nullable(), state: z.string() })),
});

export type SourceKind = z.infer<typeof SourceKindSchema>;
export type TruthClass = z.infer<typeof TruthClassSchema>;
export type FreshnessState = z.infer<typeof FreshnessStateSchema>;
export type FloodCategory = z.infer<typeof FloodCategorySchema>;
export type SurfaceLevel = z.infer<typeof SurfaceLevelSchema>;
export type ConfidenceLabel = z.infer<typeof ConfidenceLabelSchema>;
export type Freshness = z.infer<typeof FreshnessSchema>;
export type ProvenanceRef = z.infer<typeof ProvenanceRefSchema>;
export type Quantity = z.infer<typeof QuantitySchema>;
export type BasinVisualizationState = z.infer<typeof BasinVisualizationStateSchema>;
export type RiverVisualizationState = z.infer<typeof RiverVisualizationStateSchema>;
export type BasinEnvelope = z.infer<typeof BasinEnvelopeSchema>;
export type RiverEnvelope = z.infer<typeof RiverEnvelopeSchema>;
export type ContractEnvelope = z.infer<typeof ContractEnvelopeSchema>;
export type SceneSummary = z.infer<typeof SceneSummarySchema>;
export type BasinList = z.infer<typeof BasinListSchema>;
export type BasinListItem = BasinList['items'][number];
export type GeoFeature = z.infer<typeof GeoFeatureSchema>;
export type SearchResults = z.infer<typeof SearchResultsSchema>;
export type SearchResult = SearchResults['items'][number];
export type Health = z.infer<typeof HealthSchema>;

/* ---- station series and forecast runs (P1 endpoints; parsed like the other spike endpoints —
        no generated JSON Schema exists for them yet) ---- */
export const SeriesVariableSchema = z.enum(['stage', 'flow']);
export const SeriesPointSchema = z.object({ t: iso, v: z.number().nullable(), quality: z.array(z.string()).optional() });
export const StationSeriesSchema = z.object({
  station_id: z.string(),
  variable: SeriesVariableSchema,
  unit: z.string(),
  datum: z.string().nullable().optional(),
  points: z.array(SeriesPointSchema),
  provenance: ProvenanceRefSchema,
});
export const ForecastRunPointSchema = z.object({ t: iso, stage: z.number().nullable().optional(), flow: z.number().nullable().optional() });
/**
 * GET /forecast-points/{lid}/runs/latest. `primary`/`unit` name the variable the run is ISSUED
 * on; every point carries both columns because NWPS publishes a primary and a secondary series
 * together. The columns are therefore declared per column, never per run: `stage_unit` and
 * `flow_unit` are the units of `points[].stage` / `points[].flow`, and `stage_datum` is the
 * gauge-zero vertical datum of the STAGE column only — null when the run has no stage column,
 * and never the datum of a flow value (ADR-0009, ADR-0014).
 */
/**
 * Reservoir state: GET /basins/{id}/reservoirs — the latest observation per (dam, variable)
 * known at as_of. Units are VERBATIM long-form ("k-acre-feet", "cubic feet per second");
 * forebay elevations carry no vertical datum because the provider states none (the quality
 * list says so). An empty `reservoirs` list is the truth for an unregulated basin.
 */
export const ReservoirVariableSchema = z.object({
  value: z.number().nullable(),
  unit: z.string(),
  valid_time: iso,
  quality: z.array(z.string()),
  qualifier: z.string().nullable().optional(),
});
export const BasinReservoirsSchema = z.object({
  basin_id: z.string(),
  as_of: iso,
  reservoirs: z.array(z.object({
    station_id: z.string(),
    lid: z.string(),
    name: z.string(),
    variables: z.record(z.string(), ReservoirVariableSchema),
    prov: z.string().nullable(),
  })),
  provenance_refs: z.record(z.string(), ProvenanceRefSchema),
});
export type BasinReservoirs = z.infer<typeof BasinReservoirsSchema>;

export const ForecastRunSchema = z.object({
  run_id: z.string(),
  issued_at: iso,
  issuer: z.string(),
  primary: SeriesVariableSchema,
  unit: z.string(),
  stage_unit: z.string().nullable().optional(),
  flow_unit: z.string().nullable().optional(),
  stage_datum: z.string().nullable().optional(),
  points: z.array(ForecastRunPointSchema),
  provenance: ProvenanceRefSchema,
});
/**
 * Archived forecast-run list (P2 Event Zero): GET /forecast-points/{lid}/runs?start=&end= —
 * every run issued inside the window, ascending, superseded runs included. Each item is the
 * /runs/latest body plus product identity and the supersedes chain.
 */
export const RunListItemSchema = ForecastRunSchema.extend({
  product_id: z.string(),
  supersedes_run_id: z.string().nullable(),
  // `provenance` is REQUIRED: every archived run answers where it came from on its own
  // (docs/DATA_DOCTRINE.md). The API builds it per item from the run's SourceProduct
  // (assemble.forecast_run_ref); the three item-level timestamps are the backfilled surface
  // and stay optional because the stub fixtures state them inside the ref instead.
  product_label: z.string().nullable().optional(),
  available_at: iso.optional(),
  retrieved_at: iso.optional(),
});
export const RunsListSchema = z.object({
  lid: z.string(),
  fp_id: z.string().optional(),
  start: iso.optional(),
  end: iso.optional(),
  items: z.array(RunListItemSchema),
});
export type SeriesVariable = z.infer<typeof SeriesVariableSchema>;
export type SeriesPoint = z.infer<typeof SeriesPointSchema>;
export type StationSeries = z.infer<typeof StationSeriesSchema>;
export type ForecastRun = z.infer<typeof ForecastRunSchema>;
export type RunListItem = z.infer<typeof RunListItemSchema>;
export type RunsList = z.infer<typeof RunsListSchema>;

/* ---- compile-time drift check ------------------------------------------------------------
 *
 * TWO checks, because one of them cannot see the failure that actually happened.
 *
 * `Assignable` proves the runtime schema does not INVENT or mistype anything: whatever zod
 * infers has to fit the generated contract. It is one-directional by construction, and every
 * generated Tier 0 field is optional, so a schema that simply OMITS `hydrologic_state` is still
 * perfectly assignable. That is exactly what shipped: the fields were in `generated.ts`, absent
 * here, and silently stripped at parse time with a green CI.
 *
 * `NoMissingKeys` is the other direction and the one that would have caught it: every key the
 * generated contract declares must EXIST in the runtime schema. It reports the missing names in
 * the type error rather than a bare `false`, so the failure says what to add. It deliberately
 * compares keys and not full types — the value types are already covered by `Assignable`, and a
 * whole-type bidirectional check would fail on legitimate narrowing (zod enums where the
 * generator emits `string`).
 *
 * Minor-version tolerance is unaffected: a field the contract has NOT yet declared is still
 * unknown to both sides and still stripped. What is forbidden is a field the contract already
 * declares being unknown to the parser.
 */
type Assignable<T extends U, U> = T;
type MissingKeys<Contract, Runtime> = Exclude<keyof Contract, keyof Runtime>;
type NoMissingKeys<Contract, Runtime> =
  MissingKeys<Contract, Runtime> extends never ? true : MissingKeys<Contract, Runtime>;

export const _noMissingBasinKeys: NoMissingKeys<Generated.BasinVisualizationState, BasinVisualizationState> = true;
export const _noMissingRiverKeys: NoMissingKeys<Generated.RiverVisualizationState, RiverVisualizationState> = true;
export const _noMissingHydrologicStateKeys: NoMissingKeys<Generated.HydrologicState, z.infer<typeof HydrologicStateSchema>> = true;
export const _noMissingStateChangeKeys: NoMissingKeys<Generated.StateChange1, z.infer<typeof StateChangeEntrySchema>> = true;
export const _noMissingSeasonalMultipleKeys: NoMissingKeys<Generated.SeasonalMultiple, z.infer<typeof SeasonalMultipleSchema>> = true;
export const _noMissingRecordRankKeys: NoMissingKeys<Generated.RecordRank, z.infer<typeof RecordRankSchema>> = true;
export const _noMissingReferenceWindowKeys: NoMissingKeys<Generated.ReferenceWindow, z.infer<typeof ReferenceWindowSchema>> = true;
export type _DriftEnvelope = Assignable<ContractEnvelope, Generated.ContractEnvelope>;
export type _DriftBasin = Assignable<BasinVisualizationState, Generated.BasinVisualizationState>;
export type _DriftRiver = Assignable<RiverVisualizationState, Generated.RiverVisualizationState>;
export type _DriftProv = Assignable<ProvenanceRef, Generated.ProvenanceRef>;
export type _DriftFreshness = Assignable<Freshness, Generated.Freshness>;
export type _DriftScene = Assignable<SceneSummary, Generated.SceneSummary>;
export type _DriftHydrologicState = Assignable<z.infer<typeof HydrologicStateSchema>, Generated.HydrologicState>;
export type _DriftStateChange = Assignable<z.infer<typeof StateChangeEntrySchema>, Generated.StateChange1>;
