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
export type SurfaceLevel = 'low' | 'moderate' | 'high' | 'very_high' | 'unknown';
/**
 * the bands the reference distribution cannot separate here; empty when it can
 */
export type BandsWithinSamplingError = SurfaceLevel[];
/**
 * Whether the reference distribution can separate this value from a band edge.
 *
 * A **condition**, not a confidence: there is no number here and no coverage claim. The
 * day-of-year ladder's breakpoints are sample quantiles estimated from a finite number of
 * independent years, so a value sitting a point or two from a band edge is not distinguishable
 * from the other side of it by the record that drew the edge.
 *
 * - ``separated`` — no band edge lies inside the reported sampling error of the percentile.
 * - ``near_band_edge`` — one does; :attr:`HydrologicState.bands_within_sampling_error` names
 *   the bands the record cannot tell apart here.
 * - ``unquantified`` — the sample size behind the ladder is not known, so the question cannot
 *   be answered at all. This is the **fail-closed** state: it never means "separated".
 */
export type BandBoundary = 'separated' | 'near_band_edge' | 'unquantified';
/**
 * the station-local calendar day the daily mean covers
 */
export type Day = string;
export type Multiple = number;
export type Prov1 = string;
export type Datum = string | null;
export type Unit1 = string;
export type Value1 = number;
export type ReferencePercentile = number;
export type Percentile = number | null;
/**
 * the value fell outside the stored ladder, so the percentile is a bound, not an estimate
 */
export type PercentileClamped = boolean;
export type Prov2 = string;
export type ExceedsRecord = boolean;
/**
 * sample size including the value being ranked
 */
export type Of = number;
export type PreviousMaxDay = string | null;
export type Prov3 = string;
/**
 * 1 = largest; None when only a bound is known
 */
export type Rank1 = number | null;
export type Reason = string | null;
export type Reason1 = string | null;
/**
 * day-of-year key, "MM-DD"
 */
export type DoyKey = string;
/**
 * n deflated by the smoothing window; the honest denominator
 */
export type IndependentYears = number;
/**
 * the climatology method that built the sample, method:<name>@<semver>
 */
export type MethodId = string;
/**
 * values in the window sample
 */
export type N = number;
export type PeriodEnd = number | null;
/**
 * first calendar year of the record the reference was built from. A calendar SPAN, not a count of years with data: a gauge can reach back further than it observed
 */
export type PeriodStart = number | null;
/**
 * half-width of the smoothing window in days
 */
export type WindowDays = number;
/**
 * docs/VISUAL_TRUTH_DOCTRINE.md — what kind of thing a rendered element is.
 */
export type TruthClass =
  'observation' | 'authoritative_model' | 'cascade_derived' | 'cartographic' | 'cinematic';
export type Id = string;
export type LabelPriority = number;
export type Name = string;
export type Event = string;
export type Expires = string | null;
export type Id1 = string;
export type Issuer = string;
export type Onset = string | null;
export type Prov4 = string;
export type Severity = string | null;
export type OfficialAlerts = OfficialAlert[];
export type OutletForecastPointId = string | null;
export type RegulationClass = string;
export type Direction1 = string;
/**
 * Q(t) / Q(t − window_h); dimensionless
 */
export type Growth = number | null;
export type Prov5 = string;
/**
 * 1 = largest change in this gauge's record
 */
export type Rank2 = number | null;
export type RankOf = number | null;
/**
 * why the rank is absent or a bound
 */
export type RankReason = string | null;
/**
 * why growth is absent, when it is
 */
export type Reason2 = string | null;
/**
 * the span actually covered, which is what growth is over
 */
export type SpanH = number | null;
export type WindowH = number;
export type StateChange = StateChange1[];
export type ExplanationRef = string | null;
export type Prov6 = string[];
/**
 * why UNKNOWN/LOW, when it is
 */
export type Reason3 = string | null;
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
export type Prov7 = string;
/**
 * why UNKNOWN, when it is
 */
export type Reason4 = string | null;
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
export type Prov8 = string;
export type Reason5 = string | null;
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
export type Prov9 = string;
export type Reason6 = string | null;
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
export type Prov10 = string;
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
export type Prov11 = string;
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
export type Prov12 = string;
export type Unit2 = string;
export type Downstream = string[];
export type Upstream = string[];
export type Direction2 = string;
/**
 * key into ContractEnvelope.provenance_refs
 */
export type Prov13 = string;
export type WindowH1 = number;
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
export type MethodId1 = string | null;
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
  hydrologic_state?: HydrologicState | null;
  id: Id;
  label_priority?: LabelPriority;
  name: Name;
  official_alerts?: OfficialAlerts;
  outlet_forecast_point_id?: OutletForecastPointId;
  regulation_class: RegulationClass;
  state_change?: StateChange;
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
/**
 * Where the river is: one observation said three ways that are never combined.
 *
 * `percentile` is the shipped, still-clamped day-of-year percentile — unchanged, uncalibrated
 * and EXPERIMENTAL. `rank` says how unusual it is against a named record. `multiple` says how
 * big it is against a named reference. **There is no fourth field summarising the three, and
 * there must never be one**: a composite of these would be exactly the flood-risk score the
 * doctrine forbids. A client may not colour, size or order one of them by another.
 */
export interface HydrologicState {
  bands_within_sampling_error?: BandsWithinSamplingError;
  boundary?: BandBoundary;
  day: Day;
  multiple?: SeasonalMultiple | null;
  observed: Quantity1;
  percentile?: Percentile;
  percentile_clamped?: PercentileClamped;
  prov: Prov2;
  rank?: RecordRank | null;
  reason?: Reason1;
  reference?: ReferenceWindow | null;
  truth: TruthClass;
}
/**
 * `value ÷ the day-of-year reference flow`. Unbounded, and never a flood magnitude.
 *
 * The reference is the ladder's TOP stored breakpoint, so `multiple >= 1` is exactly the
 * condition under which the percentile clamps: this begins where the percentile stops
 * discriminating. It is a multiple of a *seasonal* reference — a late-summer flash flow on a
 * tiny denominator can exceed a winter flood's multiple — so the absolute flow always renders
 * beside it, and it is never banded on a year-round cutoff.
 */
export interface SeasonalMultiple {
  multiple: Multiple;
  prov: Prov1;
  reference: Quantity;
  reference_percentile: ReferencePercentile;
}
/**
 * A number with its unit; `datum` is required for stage-like quantities.
 */
export interface Quantity {
  datum?: Datum;
  unit: Unit1;
  value: Value1;
}
/**
 * A number with its unit; `datum` is required for stage-like quantities.
 */
export interface Quantity1 {
  datum?: Datum;
  unit: Unit1;
  value: Value1;
}
/**
 * Where the value sits among the reference window sample, as a count and nothing more.
 *
 * Deliberately not a plotting position: "3rd largest of 491 daily means" says its own sample
 * size, where "p99.48" advertises resolution the sample does not have. Censored at 1 — a value
 * above the record maximum is "the largest", and so is one twice as big — but it censors
 * HONESTLY, naming the record it beat. `rank` is None where only a bound is available, and
 * `reason` then says why.
 */
export interface RecordRank {
  exceeds_record?: ExceedsRecord;
  of: Of;
  previous_max?: Quantity2 | null;
  previous_max_day?: PreviousMaxDay;
  prov: Prov3;
  rank?: Rank1;
  reason?: Reason;
}
/**
 * A number with its unit; `datum` is required for stage-like quantities.
 */
export interface Quantity2 {
  datum?: Datum;
  unit: Unit1;
  value: Value1;
}
/**
 * The empirical day-of-year sample a level statement is ranked against.
 *
 * Printed beside every number derived from it, because a rank means nothing without the
 * sample it is a rank in. `independent_years` is the sample count deflated by the smoothing
 * window (a ±2-day window pools 5 consecutive days of each year, so `n` days are not `n`
 * independent draws); it is the denominator any statement about sampling error must use.
 */
export interface ReferenceWindow {
  doy_key: DoyKey;
  independent_years: IndependentYears;
  method_id: MethodId;
  n: N;
  period_end?: PeriodEnd;
  period_start?: PeriodStart;
  window_days: WindowDays;
}
export interface OfficialAlert {
  event: Event;
  expires?: Expires;
  id: Id1;
  issuer: Issuer;
  onset?: Onset;
  prov: Prov4;
  severity?: Severity;
}
/**
 * How fast the river is moving, as a multiplicative growth of the daily mean over a window.
 *
 * `growth = Q(t) / Q(t − window_h)`. Computed on the observation, never on the percentile: the
 * ladder clamps, so a percentile derivative reads +0 through a crest. Three properties follow
 * and all three are load-bearing — it does not depend on any ladder or its vintage, it has no
 * extrapolated region (it is arithmetic on two observations), and it stays exact while the
 * level is censored.
 *
 * It is a **driver, not a score**: nothing here is weighted against the level, and no band edge
 * is drawn on it. `rank` answers "is that fast?" descriptively, against this gauge's own past
 * changes over the same window, because no evidence yet exists for a cutoff.
 */
export interface StateChange1 {
  direction: Direction1;
  from_value?: Quantity2 | null;
  growth?: Growth;
  prov: Prov5;
  rank?: Rank2;
  rank_of?: RankOf;
  rank_reason?: RankReason;
  reason?: Reason2;
  span_h?: SpanH;
  to_value?: Quantity2 | null;
  window_h: WindowH;
}
export interface BasinSurfaces {
  agreement: AgreementState;
  forcing: SurfaceState;
  hazard: HazardState;
  susceptibility: SurfaceState;
}
export interface AgreementState {
  explanation_ref?: ExplanationRef;
  prov?: Prov6;
  reason?: Reason3;
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
  prov: Prov7;
  reason?: Reason4;
  score?: Score;
  spread?: Spread;
  state: SurfaceLevel;
  truth: TruthClass;
  /**
   * the headline quantity `state` was banded from, in its own unit (e.g. 72-h basin-mean QPF in mm, or a day-of-year flow percentile in pct). EXPERIMENTAL whenever `experimental` is true; never a probability
   */
  value?: Quantity2 | null;
}
export interface HazardState {
  cascade_index?: CascadeIndex;
  horizon_h: HorizonH1;
  model_probability?: ModelProbability;
  official_category: FloodCategory;
  official_prov?: OfficialProv;
  prov: Prov8;
  reason?: Reason5;
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
  prov: Prov9;
  reason?: Reason6;
  time_to_threshold_h?: TimeToThresholdH;
  to_category: FloodCategory;
  value?: Quantity2 | null;
}
export interface ObservedRiverState {
  flow?: Quantity2 | null;
  prov: Prov10;
  stage?: Quantity2 | null;
  truth: TruthClass;
  valid_time: ValidTime;
}
export interface OfficialForecastSummary {
  category: FloodCategory;
  crest?: Quantity2 | null;
  crest_valid_time?: CrestValidTime;
  issued_at: IssuedAt;
  issuer: Issuer1;
  points: Points;
  prov: Prov11;
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
  prov: Prov12;
  unit: Unit2;
}
export interface Topology {
  downstream?: Downstream;
  upstream?: Upstream;
}
export interface Trend {
  direction: Direction2;
  prov: Prov13;
  rate?: Quantity2 | null;
  truth: TruthClass;
  window_h: WindowH1;
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
  method_id?: MethodId1;
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
