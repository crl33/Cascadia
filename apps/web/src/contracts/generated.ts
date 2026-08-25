/* eslint-disable */
/**
 * GENERATED — do not edit. Source: packages/contracts/schema/*.json (BasinVisualizationState.json, ContractEnvelope.json, ProvenanceRef.json, RiverVisualizationState.json, SceneSummary.json).
 * Regenerate with `npm run contracts:gen`; `npm run contracts:check` fails on drift.
 */

export type AsOf = string;
/**
 * ground is served with local content until ground-band products exist
 */
export type Band = string;
export type AsOf1 = string;
export type Contract = string;
export type GeneratedAt = string;
export type FeatureId = string;
export type Lod = string;
/**
 * GeoJSON or tile URL template; cartographic truth class
 */
export type Url = string | null;
export type Direction = string;
export type Feature = string;
export type Prov = string;
export type Rank = number;
export type Unit = string | null;
export type Value = number | null;
export type HeadlineDrivers = Driver[];
export type Id = string;
export type LabelPriority = number;
export type Name = string;
export type Event = string;
export type Expires = string | null;
export type Id1 = string;
export type Issuer = string;
export type Onset = string | null;
export type Prov1 = string;
export type Severity = string | null;
export type OfficialAlerts = OfficialAlert[];
export type OutletForecastPointId = string | null;
export type RegulationClass = string;
export type ExplanationRef = string | null;
export type Prov2 = string[];
/**
 * why UNKNOWN/LOW, when it is
 */
export type Reason = string | null;
export type AgreementLevel = 'high' | 'moderate' | 'low' | 'unknown';
/**
 * Categorical by doctrine; numeric confidence is reserved for calibrated quantities.
 */
export type ConfidenceLabel = 'high' | 'moderate' | 'low' | 'unknown';
export type Experimental = boolean;
export type HorizonH = number | null;
/**
 * key into ContractEnvelope.provenance_refs
 */
export type Prov3 = string;
/**
 * why UNKNOWN, when it is
 */
export type Reason1 = string | null;
/**
 * EXPERIMENTAL index in [0,1] from the surface's own band table; never a probability
 */
export type Score = number | null;
/**
 * named spread points for `value`, in the SAME unit, e.g. {'p10': 88.0, 'p90': 211.0}. Keys name the method's own statistic and nothing more: a model's pointwise percentile is not a basin-scale percentile and must be labeled as what it is. Never a probability
 */
export type Spread = {
  [k: string]: number | undefined;
} | null;
export type SurfaceLevel = 'low' | 'moderate' | 'high' | 'very_high' | 'unknown';
/**
 * docs/VISUAL_TRUTH_DOCTRINE.md — what kind of thing a rendered element is.
 */
export type TruthClass =
  'observation' | 'authoritative_model' | 'cascade_derived' | 'cartographic' | 'cinematic';
export type Datum = string | null;
export type Unit1 = string;
export type Value1 = number;
/**
 * only after hindcast evaluation (ADR-0008)
 */
export type CascadeIndex = number | null;
export type HorizonH1 = number;
/**
 * e.g. {"model": "nwm-mr-ens", "exceeds": "minor", "fraction": 0.43}
 */
export type ModelProbability = {
  [k: string]: (string | number) | undefined;
} | null;
export type FloodCategory = 'none' | 'action' | 'minor' | 'moderate' | 'major' | 'unknown';
export type OfficialProv = string | null;
/**
 * key into ContractEnvelope.provenance_refs
 */
export type Prov4 = string;
export type Reason2 = string | null;
/**
 * wake-up intensity hint; documented method; not a probability
 */
export type Tension = number | null;
export type BasinId = string;
/**
 * display hint from percentile; not depth
 */
export type FlowVisualIntensity = number | null;
export type Basis = string;
export type Prov5 = string;
export type Reason3 = string | null;
export type TimeToThresholdH = number | null;
export type Id2 = string;
/**
 * [lon, lat] WGS84; cartographic
 */
export type Location = [unknown, unknown] | null;
export type Name1 = string;
/**
 * key into ContractEnvelope.provenance_refs
 */
export type Prov6 = string;
export type ValidTime = string;
export type FloodCategory1 = 'none' | 'action' | 'minor' | 'moderate' | 'major' | 'unknown';
export type ObservedCategoryReason = string | null;
export type CrestValidTime = string | null;
export type IssuedAt = string;
export type Issuer1 = string;
export type Points = number;
/**
 * key into ContractEnvelope.provenance_refs
 */
export type Prov7 = string;
export type ReachId = string | null;
export type Class = string;
export type RegulatedBy = string[];
export type StationId = string | null;
export type Action = number | null;
export type Basis1 = string;
export type Datum1 = string | null;
export type Major = number | null;
export type Minor = number | null;
export type Moderate = number | null;
export type Prov8 = string;
export type Unit2 = string;
export type Downstream = string[];
export type Upstream = string[];
export type Direction1 = string;
/**
 * key into ContractEnvelope.provenance_refs
 */
export type Prov9 = string;
export type WindowH = number;
export type Items = (BasinVisualizationState | RiverVisualizationState)[];
export type AgeSeconds = number | null;
export type ExpectedCadenceSeconds = number | null;
export type FreshnessState = 'current' | 'stale' | 'degraded' | 'missing' | 'partial' | 'unknown';
export type IssuedAt1 = string | null;
/**
 * Human label supplied by the backend, e.g. 'NWRFC official forecast'
 */
export type Label = string;
/**
 * method:<name>@<semver> for DERIVED/EXPERIMENTAL
 */
export type MethodId = string | null;
/**
 * SourceProduct id, e.g. product:nwps-stageflow
 */
export type ProductId = string | null;
export type Quality = string[];
export type RawArtifactId = string | null;
export type RetrievedAt = string | null;
/**
 * DataSource id, e.g. src:nwps-v1
 */
export type SourceId = string;
/**
 * docs/DATA_DOCTRINE.md §2 — closed, ordered taxonomy.
 */
export type SourceKind =
  'OBSERVED' | 'OFFICIAL_FORECAST' | 'MODELED' | 'DERIVED' | 'EXPERIMENTAL' | 'CONFIGURED' | 'UNKNOWN';
export type ValidTime1 = string | null;
export type Mode = string;
export type Valid = string;
export type Version = string;

/**
 * docs/VISUALIZATION_CONTRACTS.md §8 — the band-appropriate subset for a request.
 */
export interface SceneSummary {
  as_of: AsOf;
  band: Band;
  basins?: ContractEnvelope | null;
  rivers?: ContractEnvelope | null;
}
export interface ContractEnvelope {
  as_of: AsOf1;
  contract: Contract;
  generated_at: GeneratedAt;
  items: Items;
  provenance_refs: ProvenanceRefs;
  time: TimeContext;
  version?: Version;
}
export interface BasinVisualizationState {
  geometry_ref: GeometryRef;
  headline_drivers?: HeadlineDrivers;
  id: Id;
  label_priority?: LabelPriority;
  name: Name;
  official_alerts?: OfficialAlerts;
  outlet_forecast_point_id?: OutletForecastPointId;
  regulation_class: RegulationClass;
  surfaces: BasinSurfaces;
  tension?: Tension;
}
export interface GeometryRef {
  feature_id: FeatureId;
  lod: Lod;
  url?: Url;
}
export interface Driver {
  direction: Direction;
  feature: Feature;
  prov: Prov;
  rank: Rank;
  unit?: Unit;
  value?: Value;
}
export interface OfficialAlert {
  event: Event;
  expires?: Expires;
  id: Id1;
  issuer: Issuer;
  onset?: Onset;
  prov: Prov1;
  severity?: Severity;
}
export interface BasinSurfaces {
  agreement: AgreementState;
  forcing: SurfaceState;
  hazard: HazardState;
  susceptibility: SurfaceState;
}
export interface AgreementState {
  explanation_ref?: ExplanationRef;
  prov?: Prov2;
  reason?: Reason;
  state: AgreementLevel;
}
/**
 * One of the risk surfaces (docs/HYDROLOGY.md §3–§6).
 *
 * `state` is the banded answer, `value` is the quantity it was banded from, and `spread`
 * names the uncertainty points that came with that quantity. **None of `score`, `value` or
 * `spread` is ever a probability.** Where `experimental` is true the surface is a Cascadia
 * Papsukkal derivation whose method has not passed hindcast evaluation, so its number is
 * EXPERIMENTAL by definition: it carries a `method_id` through `prov`, it is uncalibrated,
 * and no client may render it as a chance of anything (ADR-0008, docs/DATA_DOCTRINE.md §9).
 * A threshold-crossing probability may only ever come from counted model members, never
 * from here. `state = unknown` with a specific `reason` is a legitimate, correct answer;
 * a fabricated value is not.
 */
export interface SurfaceState {
  confidence?: ConfidenceLabel;
  experimental?: Experimental;
  horizon_h?: HorizonH;
  prov: Prov3;
  reason?: Reason1;
  score?: Score;
  spread?: Spread;
  state: SurfaceLevel;
  truth: TruthClass;
  /**
   * the headline quantity `state` was banded from, in its own unit (e.g. 72-h basin-mean QPF in mm, or a day-of-year flow percentile in pct). EXPERIMENTAL whenever `experimental` is true; never a probability
   */
  value?: Quantity | null;
}
/**
 * A number with its unit; `datum` is required for stage-like quantities.
 */
export interface Quantity {
  datum?: Datum;
  unit: Unit1;
  value: Value1;
}
export interface HazardState {
  cascade_index?: CascadeIndex;
  horizon_h: HorizonH1;
  model_probability?: ModelProbability;
  official_category: FloodCategory;
  official_prov?: OfficialProv;
  prov: Prov4;
  reason?: Reason2;
  truth: TruthClass;
}
export interface RiverVisualizationState {
  basin_id: BasinId;
  flow_visual_intensity?: FlowVisualIntensity;
  headroom?: Headroom | null;
  id: Id2;
  location?: Location;
  name: Name1;
  observed?: ObservedRiverState | null;
  observed_category?: FloodCategory1;
  observed_category_reason?: ObservedCategoryReason;
  official_forecast?: OfficialForecastSummary | null;
  reach_id?: ReachId;
  regulation?: Regulation;
  station_id?: StationId;
  thresholds?: Thresholds | null;
  topology?: Topology;
  trend?: Trend | null;
}
export interface Headroom {
  basis: Basis;
  prov: Prov5;
  reason?: Reason3;
  time_to_threshold_h?: TimeToThresholdH;
  to_category: FloodCategory;
  value?: Quantity | null;
}
export interface ObservedRiverState {
  flow?: Quantity | null;
  prov: Prov6;
  stage?: Quantity | null;
  truth: TruthClass;
  valid_time: ValidTime;
}
export interface OfficialForecastSummary {
  category: FloodCategory;
  crest?: Quantity | null;
  crest_valid_time?: CrestValidTime;
  issued_at: IssuedAt;
  issuer: Issuer1;
  points: Points;
  prov: Prov7;
  truth: TruthClass;
}
export interface Regulation {
  class: Class;
  regulated_by?: RegulatedBy;
}
export interface Thresholds {
  action?: Action;
  basis: Basis1;
  datum?: Datum1;
  major?: Major;
  minor?: Minor;
  moderate?: Moderate;
  prov: Prov8;
  unit: Unit2;
}
export interface Topology {
  downstream?: Downstream;
  upstream?: Upstream;
}
export interface Trend {
  direction: Direction1;
  prov: Prov9;
  rate?: Quantity | null;
  truth: TruthClass;
  window_h: WindowH;
}
export interface ProvenanceRefs {
  [k: string]: ProvenanceRef | undefined;
}
/**
 * docs/VISUALIZATION_CONTRACTS.md §1. Every scientific value points at one of these.
 */
export interface ProvenanceRef {
  freshness: Freshness;
  issued_at?: IssuedAt1;
  label: Label;
  method_id?: MethodId;
  product_id?: ProductId;
  quality?: Quality;
  raw_artifact_id?: RawArtifactId;
  retrieved_at?: RetrievedAt;
  source_id: SourceId;
  source_kind: SourceKind;
  valid_time?: ValidTime1;
}
export interface Freshness {
  age_seconds?: AgeSeconds;
  expected_cadence_seconds?: ExpectedCadenceSeconds;
  state: FreshnessState;
}
export interface TimeContext {
  mode: Mode;
  valid: Valid;
}
