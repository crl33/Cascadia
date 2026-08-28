/**
 * Pure chart math for the hydrograph panel: basis selection, nice ticks, domains, linear
 * scales, SVG path generation and the overlay-honesty rules (thresholds/forecast/crest are
 * drawn only on a matching basis, unit and datum — never converted, never mixed). No React,
 * no fetching, no science: every number positioned here arrived from a contract endpoint.
 */
import type { RiverVisualizationState } from '../contracts/schemas';

export type Basis = 'stage' | 'flow';

/* ---- basis selection ---- */

export interface BasisChoice {
  basis: Basis | null;
  /** which contract field declared the basis */
  source: 'thresholds' | 'headroom' | 'observed' | null;
  /** why the basis is unknown, when it is */
  reason: string | null;
}

/**
 * The variable this point charts. Declared by the backend: official thresholds first (the
 * NWPS basis), then headroom, then whichever observed quantity exists. Never guessed beyond
 * that — a point with no declaration renders the empty state, not a default line.
 */
export function resolveBasis(item: Pick<RiverVisualizationState, 'thresholds' | 'headroom' | 'observed'>): BasisChoice {
  if (item.thresholds) return { basis: item.thresholds.basis, source: 'thresholds', reason: null };
  if (item.headroom) return { basis: item.headroom.basis, source: 'headroom', reason: null };
  if (item.observed?.stage) return { basis: 'stage', source: 'observed', reason: null };
  if (item.observed?.flow) return { basis: 'flow', source: 'observed', reason: null };
  return {
    basis: null,
    source: null,
    reason: 'No thresholds, headroom or observation in this document declares a stage/flow basis for this point.',
  };
}

/* ---- domains and ticks ---- */

export interface Extent {
  min: number;
  max: number;
}

const PAD_FRACTION = 0.06;

/**
 * Value-axis domain: the union of series values and every official threshold present, so the
 * flood-stage range is always visible even when the river is far below action stage.
 */
export function valueDomain(seriesValues: readonly number[], thresholdValues: readonly number[]): Extent | null {
  const all = [...seriesValues, ...thresholdValues].filter((v) => Number.isFinite(v));
  if (all.length === 0) return null;
  let min = all[0]!;
  let max = all[0]!;
  for (const v of all) {
    if (v < min) min = v;
    if (v > max) max = v;
  }
  if (min === max) {
    const pad = Math.max(1, Math.abs(min) * 0.1);
    return { min: min - pad, max: max + pad };
  }
  const pad = (max - min) * PAD_FRACTION;
  return { min: min - pad, max: max + pad };
}

const HOUR_MS = 3_600_000;

/** Time-axis domain over every plotted instant (observed, forecast, crest). */
export function timeDomain(times: readonly number[]): Extent | null {
  const all = times.filter((t) => Number.isFinite(t));
  if (all.length === 0) return null;
  let min = all[0]!;
  let max = all[0]!;
  for (const t of all) {
    if (t < min) min = t;
    if (t > max) max = t;
  }
  if (min === max) return { min: min - HOUR_MS, max: max + HOUR_MS };
  return { min, max };
}

/** Smallest 1/2/5·10^n step at or above the raw step. */
export const niceStep = (rawStep: number): number => {
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const normalized = rawStep / magnitude;
  if (normalized <= 1) return magnitude;
  if (normalized <= 2) return 2 * magnitude;
  if (normalized <= 5) return 5 * magnitude;
  return 10 * magnitude;
};

const snap = (value: number, step: number): number => Number((Math.round(value / step) * step).toPrecision(12));

/** Ticks on the 1/2/5 ladder, inside [min, max]. */
export function niceTicks(min: number, max: number, targetCount = 5): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min || targetCount < 1) return [];
  const step = niceStep((max - min) / targetCount);
  const ticks: number[] = [];
  for (let v = Math.ceil(min / step - 1e-9) * step; v <= max + step * 1e-9; v += step) ticks.push(snap(v, step));
  return ticks;
}

const TIME_STEPS_MS: readonly number[] = [
  15 * 60_000, 30 * 60_000, HOUR_MS, 3 * HOUR_MS, 6 * HOUR_MS, 12 * HOUR_MS,
  24 * HOUR_MS, 2 * 24 * HOUR_MS, 7 * 24 * HOUR_MS,
];

/** Time ticks aligned to UTC hour/day boundaries; returns the step so labels can adapt. */
export function timeTicks(domain: Extent, targetCount = 5): { ticks: number[]; stepMs: number } {
  const span = domain.max - domain.min;
  if (!Number.isFinite(span) || span <= 0) return { ticks: [], stepMs: 0 };
  const raw = span / targetCount;
  const stepMs = TIME_STEPS_MS.find((s) => s >= raw) ?? TIME_STEPS_MS[TIME_STEPS_MS.length - 1]!;
  const ticks: number[] = [];
  for (let t = Math.ceil(domain.min / stepMs) * stepMs; t <= domain.max; t += stepMs) ticks.push(t);
  return { ticks, stepMs };
}

/** UTC tick label: date for daily steps or UTC midnight, time of day otherwise. */
export function formatTickUtc(ms: number, stepMs: number): string {
  const iso = new Date(ms).toISOString();
  if (stepMs >= 24 * HOUR_MS || iso.slice(11, 16) === '00:00') return iso.slice(5, 10);
  return iso.slice(11, 16);
}

/* ---- scales and paths ---- */

export type Scale = (value: number) => number;

/** Plain linear map from a domain extent to a pixel range (r1 may be < r0 for the y axis). */
export const linearScale = (domain: Extent, r0: number, r1: number): Scale => {
  const span = domain.max - domain.min;
  return (value) => (span === 0 ? (r0 + r1) / 2 : r0 + ((value - domain.min) / span) * (r1 - r0));
};

export interface TimeValuePoint {
  t: number;
  v: number | null;
}

const round2 = (n: number): number => Math.round(n * 100) / 100;

/**
 * SVG path for a time/value series. A null or non-finite value breaks the line (a gap is a
 * gap — never bridged, never interpolated into a fake continuous line).
 */
export function seriesPath(points: readonly TimeValuePoint[], x: Scale, y: Scale): string {
  let path = '';
  let penDown = false;
  for (const p of points) {
    if (p.v == null || !Number.isFinite(p.v) || !Number.isFinite(p.t)) {
      penDown = false;
      continue;
    }
    path += `${path ? ' ' : ''}${penDown ? 'L' : 'M'}${round2(x(p.t))} ${round2(y(p.v))}`;
    penDown = true;
  }
  return path;
}

/* ---- overlay honesty ---- */

export const THRESHOLD_CATEGORIES = ['action', 'minor', 'moderate', 'major'] as const;
export type ThresholdCategory = (typeof THRESHOLD_CATEGORIES)[number];

export interface ThresholdLine {
  category: ThresholdCategory;
  value: number;
}

export interface ThresholdOverlay {
  lines: ThresholdLine[];
  /** backend-truthful refusal to mix bases/units/datums, shown verbatim */
  refusal: string | null;
}

/** Threshold lines drawn only on a matching basis, unit and (for stage) datum. */
export function thresholdOverlay(
  thresholds: RiverVisualizationState['thresholds'],
  basis: Basis,
  axisUnit: string | null,
  axisDatum: string | null,
): ThresholdOverlay {
  if (!thresholds) return { lines: [], refusal: null };
  if (thresholds.basis !== basis) {
    return { lines: [], refusal: `Official thresholds are on basis ${thresholds.basis}; this chart plots ${basis}. Not overlaid; values are never converted.` };
  }
  if (axisUnit != null && thresholds.unit !== axisUnit) {
    return { lines: [], refusal: `Official thresholds are in ${thresholds.unit}; the series is in ${axisUnit}. Not overlaid; values are never converted.` };
  }
  if (basis === 'stage' && axisDatum != null && thresholds.datum != null && thresholds.datum !== axisDatum) {
    return { lines: [], refusal: `Official thresholds use datum ${thresholds.datum}; the series uses ${axisDatum}. Not overlaid; datums are never compared.` };
  }
  const lines = THRESHOLD_CATEGORIES.flatMap((category) => {
    const value = thresholds[category];
    return value == null ? [] : [{ category, value }];
  });
  return { lines, refusal: null };
}

export interface ForecastRunLike {
  primary: string;
  unit: string;
  /** Gauge-zero datum of the `stage` column only; null when the run carries no stage column. */
  stage_datum?: string | null;
  points: readonly { t: string; stage?: number | null; flow?: number | null }[];
}

export interface ForecastChoice {
  points: TimeValuePoint[] | null;
  reason: string | null;
}

/**
 * The official-forecast series for the charted basis. Drawn only when the run's declared
 * primary variable, unit and (for stage) datum match the axis. The run's secondary column is
 * never charted as the official forecast — the run is issued on its primary, and the companion
 * column is not what NWRFC issued. On a stage axis the run's `stage_datum` must be known and
 * equal: a datum is never assumed, so an undeclared one refuses like a mismatched one (ADR-0009).
 */
export function forecastSeriesFor(
  run: ForecastRunLike | null | undefined,
  basis: Basis,
  axisUnit: string | null,
  axisDatum: string | null,
): ForecastChoice {
  if (!run) return { points: null, reason: null };
  if (run.primary !== basis) {
    return { points: null, reason: `The official forecast run is issued on ${run.primary}; this chart plots ${basis}. The run is not overlaid; values are never converted.` };
  }
  if (axisUnit != null && run.unit !== axisUnit) {
    return { points: null, reason: `The official forecast run is in ${run.unit}; the series is in ${axisUnit}. Not overlaid; values are never converted.` };
  }
  if (basis === 'stage' && axisDatum != null) {
    if (run.stage_datum == null) {
      return { points: null, reason: `The official forecast run declares no vertical datum for its stage values; the series uses ${axisDatum}. Not overlaid; a datum is never assumed.` };
    }
    if (run.stage_datum !== axisDatum) {
      return { points: null, reason: `The official forecast run uses datum ${run.stage_datum}; the series uses ${axisDatum}. Not overlaid; datums are never compared.` };
    }
  }
  const points = run.points.map((p) => ({ t: Date.parse(p.t), v: (basis === 'stage' ? p.stage : p.flow) ?? null }));
  return { points, reason: null };
}

export interface CrestChoice {
  marker: { t: number; v: number } | null;
  reason: string | null;
}

/** The official crest marker, only on a matching unit and (for stage) datum. */
export function crestMarker(
  forecast: RiverVisualizationState['official_forecast'],
  basis: Basis,
  axisUnit: string | null,
  axisDatum: string | null,
): CrestChoice {
  if (!forecast) return { marker: null, reason: null };
  if (!forecast.crest || !forecast.crest_valid_time) {
    return { marker: null, reason: 'The official forecast summary carries no crest value/time.' };
  }
  if (axisUnit != null && forecast.crest.unit !== axisUnit) {
    return { marker: null, reason: `The official crest is in ${forecast.crest.unit}; the series is in ${axisUnit}. Not marked; values are never converted.` };
  }
  if (basis === 'stage' && axisDatum != null && forecast.crest.datum != null && forecast.crest.datum !== axisDatum) {
    return { marker: null, reason: `The official crest uses datum ${forecast.crest.datum}; the series uses ${axisDatum}. Not marked; datums are never compared.` };
  }
  const t = Date.parse(forecast.crest_valid_time);
  if (!Number.isFinite(t)) return { marker: null, reason: 'The official crest valid time is not parseable.' };
  return { marker: { t, v: forecast.crest.value }, reason: null };
}

/* ---- HEFS exceedance band (P5: the provider's own probabilities, §9(a)) ---- */

export interface HefsLadderLike {
  unit: string;
  parameter_id: string | null;
  exceedance_levels: readonly number[];
  rows: readonly { valid_time: string; values: readonly (number | null)[] }[];
}

export interface HefsBandPoint {
  t: number;
  lo: number;
  hi: number;
}

export interface HefsBandChoice {
  band: HefsBandPoint[] | null;
  median: TimeValuePoint[] | null;
  /** the exceedance levels actually drawn, for the legend: [hi-flow level, median, lo-flow level] */
  levels: readonly [number, number, number] | null;
  /** rows dropped because they lie beyond the charted window (said, not silent) */
  clipped: number;
  reason: string | null;
}

/**
 * The HEFS exceedance band for the charted basis: the provider's own 0.05/0.50/0.95 quantile
 * traces, drawn ONLY when they exist at exactly those levels — a ladder serving different
 * levels is not interpolated into these (DATA_DOCTRINE §9: percentiles stay percentiles).
 * HEFS quantiles are flow (QINE), so a stage axis refuses. Unit comparison is
 * case-insensitive on purpose: the provider serves "CFS" where the series says "cfs", and
 * case is orthography, not conversion. Rows beyond `untilMs` are clipped and COUNTED — a
 * 30-day ladder must not stretch a 72-hour chart, and the legend says how much was cut.
 */
export function hefsBand(
  ladder: HefsLadderLike | null | undefined,
  basis: Basis,
  axisUnit: string | null,
  untilMs: number,
): HefsBandChoice {
  const none = { band: null, median: null, levels: null, clipped: 0 };
  if (!ladder) return { ...none, reason: null };
  if (basis !== 'flow') {
    return { ...none, reason: `HEFS exceedance quantiles are flow (${ladder.parameter_id ?? 'QINE'}); this chart plots ${basis}. Not banded; values are never converted.` };
  }
  if (axisUnit != null && ladder.unit.toLowerCase() !== axisUnit.toLowerCase()) {
    return { ...none, reason: `HEFS quantiles are in ${ladder.unit}; the series is in ${axisUnit}. Not banded; values are never converted.` };
  }
  const iHi = ladder.exceedance_levels.indexOf(0.05); // exceeded 5 % of the time = the HIGH bound
  const iMid = ladder.exceedance_levels.indexOf(0.5);
  const iLo = ladder.exceedance_levels.indexOf(0.95); // exceeded 95 % of the time = the LOW bound
  if (iHi < 0 || iMid < 0 || iLo < 0) {
    return { ...none, reason: `The served ladder (${ladder.exceedance_levels.join(', ')}) does not carry the 0.05/0.50/0.95 levels. Not banded; levels are never interpolated.` };
  }
  const band: HefsBandPoint[] = [];
  const median: TimeValuePoint[] = [];
  let clipped = 0;
  for (const row of ladder.rows) {
    const t = Date.parse(row.valid_time);
    if (!Number.isFinite(t)) continue;
    if (t > untilMs) {
      clipped += 1;
      continue;
    }
    const hi = row.values[iHi];
    const lo = row.values[iLo];
    const mid = row.values[iMid];
    if (hi != null && lo != null && Number.isFinite(hi) && Number.isFinite(lo)) {
      band.push({ t, lo, hi });
    }
    median.push({ t, v: mid ?? null });
  }
  if (band.length === 0 && clipped === 0) {
    return { ...none, reason: 'The HEFS ladder carries no drawable rows.' };
  }
  if (band.length === 0) {
    return { ...none, clipped, reason: 'Every HEFS row lies beyond the charted window.' };
  }
  return { band, median, levels: [0.05, 0.5, 0.95], clipped, reason: null };
}

/** Closed SVG polygon for a band: along the high bound, back along the low bound. */
export function bandPath(points: readonly HefsBandPoint[], x: Scale, y: Scale): string {
  if (points.length === 0) return '';
  const forward = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${round2(x(p.t))} ${round2(y(p.hi))}`);
  const backward = [...points].reverse().map((p) => `L${round2(x(p.t))} ${round2(y(p.lo))}`);
  return `${forward.join(' ')} ${backward.join(' ')} Z`;
}
