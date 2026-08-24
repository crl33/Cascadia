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
  explanation_ref: z.string().nullable().optional(),
  prov: z.array(z.string()).optional(),
});

const DriverSchema = z.object({
  feature: z.string(), value: z.number().nullable().optional(), unit: z.string().nullable().optional(),
  direction: z.string(), rank: z.number(), prov: z.string(),
});

const OfficialAlertSchema = z.object({
  id: z.string(), event: z.string(), severity: z.string().nullable().optional(), onset: nullableIso, expires: nullableIso,
  issuer: z.string(), prov: z.string(),
});

export const BasinVisualizationStateSchema = z.object({
  id: z.string().regex(/^basin:[a-z0-9-]+$/),
  name: z.string(),
  regulation_class: z.string(),
  surfaces: z.object({ susceptibility: SurfaceStateSchema, forcing: SurfaceStateSchema, hazard: HazardStateSchema, agreement: AgreementStateSchema }),
  tension: z.number().nullable().optional(),
  headline_drivers: z.array(DriverSchema).optional(),
  official_alerts: z.array(OfficialAlertSchema).optional(),
  outlet_forecast_point_id: z.string().nullable().optional(),
  geometry_ref: z.object({ lod: z.string(), feature_id: z.string(), url: z.string().nullable().optional() }),
  label_priority: z.number().optional(),
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
  status: z.enum(['ok', 'degraded']),
  providers: z.record(z.string(), ProviderHealthSchema),
  freshness: z.record(z.string(), z.object({ age_seconds: z.number().nullable(), state: z.string() })),
});

export type SourceKind = z.infer<typeof SourceKindSchema>;
export type TruthClass = z.infer<typeof TruthClassSchema>;
export type FreshnessState = z.infer<typeof FreshnessStateSchema>;
export type FloodCategory = z.infer<typeof FloodCategorySchema>;
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
export const RunListItemSchema = ForecastRunSchema.omit({ provenance: true }).extend({
  product_id: z.string(),
  supersedes_run_id: z.string().nullable(),
  // Archived items carry product identity + the three timestamps instead of a full
  // ProvenanceRef (deployed API contract, 2026-08-24); provenance stays optional so the
  // stub/latest-run shape also validates. Backend per-item ProvenanceRef is a follow-up.
  provenance: ProvenanceRefSchema.optional(),
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

/* ---- compile-time drift check: zod-inferred types must be assignable to the generated ones ---- */
type Assignable<T extends U, U> = T;
export type _DriftEnvelope = Assignable<ContractEnvelope, Generated.ContractEnvelope>;
export type _DriftBasin = Assignable<BasinVisualizationState, Generated.BasinVisualizationState>;
export type _DriftRiver = Assignable<RiverVisualizationState, Generated.RiverVisualizationState>;
export type _DriftProv = Assignable<ProvenanceRef, Generated.ProvenanceRef>;
export type _DriftFreshness = Assignable<Freshness, Generated.Freshness>;
export type _DriftScene = Assignable<SceneSummary, Generated.SceneSummary>;
