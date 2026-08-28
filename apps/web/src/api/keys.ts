/**
 * Query keys, keyed by entity id (and LOD/variable where relevant). Every time-dependent key
 * ends with an { asOf } segment ('now' when live) so replay never reads a live cache entry and
 * a scrub can abort superseded in-flight requests by key. One place, no ad-hoc keys.
 */
export interface AsOfSegment { readonly asOf: string }

export const asOfSegment = (asOf: string | null): AsOfSegment => ({ asOf: asOf ?? 'now' });

/** The asOf of a query key ('now' or an ISO instant), or null when the key is not time-dependent. */
export const asOfOfKey = (queryKey: readonly unknown[]): string | null => {
  const last = queryKey[queryKey.length - 1];
  if (typeof last === 'object' && last !== null && 'asOf' in last) {
    const value = (last as { asOf: unknown }).asOf;
    if (typeof value === 'string') return value;
  }
  return null;
};

export const keys = {
  basins: () => ['basins'] as const,
  geometry: (basinId: string, lod: 'state' | 'basin') => ['geo', 'basin', basinId, lod] as const,
  basinState: (basinId: string, asOf: string | null) => ['basin-state', basinId, asOfSegment(asOf)] as const,
  basinReservoirs: (basinId: string, asOf: string | null) => ['basin-reservoirs', basinId, asOfSegment(asOf)] as const,
  vizBasins: (asOf: string | null) => ['viz', 'basins', asOfSegment(asOf)] as const,
  vizRivers: (basinId: string, asOf: string | null) => ['viz', 'rivers', basinId, asOfSegment(asOf)] as const,
  vizField: (layer: string, asOf: string | null) => ['viz', 'fields', layer, asOfSegment(asOf)] as const,
  riverState: (forecastPointId: string, asOf: string | null) => ['river-state', forecastPointId, asOfSegment(asOf)] as const,
  search: (q: string) => ['search', q] as const,
  stationSeries: (stationId: string, variable: 'stage' | 'flow', asOf: string | null) => ['series', stationId, variable, asOfSegment(asOf)] as const,
  latestRun: (forecastPointId: string, asOf: string | null) => ['run', forecastPointId, 'latest', asOfSegment(asOf)] as const,
  hefsLatest: (forecastPointId: string, asOf: string | null) => ['hefs', forecastPointId, 'latest', asOfSegment(asOf)] as const,
  // Archived event-window queries (P2 Event Zero): keyed by the whole window; no asOf segment —
  // event mode carries no knowledge time, so knowledge-time scrubs never abort these.
  seriesWindow: (stationId: string, variable: 'stage' | 'flow', start: string, end: string) => ['series-window', stationId, variable, { start, end }] as const,
  runs: (forecastPointId: string, start: string, end: string) => ['runs', forecastPointId, { start, end }] as const,
  riverNetwork: () => ['geo', 'rivers'] as const,
  labels: () => ['geo', 'labels'] as const,
  health: () => ['system', 'health'] as const,
};
