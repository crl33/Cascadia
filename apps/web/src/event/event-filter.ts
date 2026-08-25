/**
 * Pure EVENT-time filters (P2 Event Zero): the client fetches each archived window ONCE
 * (series by valid_time window, forecast runs by issued_at window) and the scrub cursor
 * filters CLIENT-SIDE — presentation-side windowing of complete, honest documents. No
 * science: values pass through untouched; selection compares instants that arrived in the
 * documents. The observed crest is the maximum of the fetched series — surfaced only once
 * the cursor has passed it (zero look-ahead in presentation).
 */
import type { RunListItem, StationSeries } from '../contracts/schemas';

const ms = (iso: string): number => Date.parse(iso);

/** The series as presented at event time `at`: points with valid_time ≤ at (boundary kept). */
export function filterSeriesAt(series: StationSeries | null, at: string | null): StationSeries | null {
  if (series === null || at === null) return series;
  const cutoff = ms(at);
  return { ...series, points: series.points.filter((p) => ms(p.t) <= cutoff) };
}

/**
 * A run may be presented AS the official forecast only when the API's own ProvenanceRef — built
 * from the run's SourceProduct and resolved through the registry — says OFFICIAL_FORECAST. The
 * kind is read, never inferred from a product-id list held here.
 */
const isOfficialForecastRun = (run: RunListItem): boolean => run.provenance.source_kind === 'OFFICIAL_FORECAST';

/**
 * Official runs whose issuance the cursor has crossed, ascending by issued_at (input order not
 * trusted).
 *
 * The product filter is load-bearing, not tidiness. `GET /forecast-points/{lid}/runs` is the
 * forecast-EVOLUTION read and deliberately returns every product side by side — from P3 the NWM
 * medium-range ensemble lands in `forecast_run` beside the NWRFC forecast. Both consumers of
 * this helper present what it returns as the official forecast: the hydrograph draws it in the
 * forecast colour, titles every point "· OFFICIAL FORECAST" and stamps truth
 * `authoritative_model`, and ForecastEvolution tables it under "Official forecast crests as
 * issued". Unfiltered, a model run issued later than the RFC's would take that place — the
 * frontend twin of the read-path defect the backend fixed in
 * docs/research/p3-surfaces-design-2026-08-24.md §3.4. A model run is shown as a model run or it
 * is not shown here at all.
 */
export function runsIssuedAtOrBefore(runs: readonly RunListItem[], at: string | null): RunListItem[] {
  if (at === null) return [];
  const cutoff = ms(at);
  return [...runs]
    .filter(isOfficialForecastRun)
    .sort((a, b) => ms(a.issued_at) - ms(b.issued_at))
    .filter((r) => ms(r.issued_at) <= cutoff);
}

/** The run the replay clock selects: the latest issuance at or before `at`, or null (UNKNOWN). */
export function currentRunAt(runs: readonly RunListItem[], at: string | null): RunListItem | null {
  const eligible = runsIssuedAtOrBefore(runs, at);
  return eligible.length > 0 ? eligible[eligible.length - 1]! : null;
}

export interface ObservedCrest {
  t: string;
  v: number;
}

/** First occurrence of the series maximum (flat peaks: EVENT_ZERO §3 note e — first max wins). */
export function observedCrest(series: StationSeries | null): ObservedCrest | null {
  if (series === null) return null;
  let best: ObservedCrest | null = null;
  for (const p of series.points) {
    if (p.v == null || !Number.isFinite(p.v)) continue;
    if (best === null || p.v > best.v) best = { t: p.t, v: p.v };
  }
  return best;
}

const BACKFILLED = 'backfilled';
const RECONSTRUCTED_PRODUCT = 'product:nws-fls-crest';
const WEEK_MS = 7 * 24 * 3_600_000;

/** A series is surfaced as backfilled when its provenance or any point says so. */
export function seriesIsBackfilled(series: StationSeries | null): boolean {
  if (series === null) return false;
  if (series.provenance.quality?.includes(BACKFILLED)) return true;
  return series.points.some((p) => p.quality?.includes(BACKFILLED));
}

/**
 * A run is surfaced as backfilled/reconstructed by (a) an explicit quality flag, (b) the
 * reconstructed-product identity, or (c) retrieval long after issuance (available_at ≫
 * issued_at — ADR-0010: a backfilled row's knowledge time is its retrieval time).
 */
export function runIsBackfilled(run: Pick<RunListItem, 'product_id' | 'issued_at' | 'provenance'>): boolean {
  if (run.provenance.quality?.includes(BACKFILLED)) return true;
  if (run.product_id === RECONSTRUCTED_PRODUCT) return true;
  const retrieved = run.provenance.retrieved_at;
  return retrieved != null && ms(retrieved) - ms(run.issued_at) > WEEK_MS;
}
