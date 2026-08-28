/**
 * Typed fetchers for the SPIKE API SPEC. Every response is parsed with its zod schema before it
 * reaches the app; an AbortSignal is passed through so TanStack Query can cancel stale requests.
 * Every time-dependent endpoint forwards the knowledge time as `?as_of=` — the backend is a pure
 * function of as_of; the client never recomputes science. VITE_API_BASE overrides the backend
 * origin. Unset: localhost:8000 in `vite`/`vitest`, same-origin (`''`) in `vite build` so
 * Cloudflare Pages can serve the stub API next to the app. No other module calls fetch.
 */
import type { ZodType } from 'zod';
import {
  FieldRasterStateSchema,
  type FieldRasterState,
  BasinEnvelopeSchema, BasinListSchema, BasinReservoirsSchema, ForecastRunSchema, HefsLatestSchema, RiverNetworkSchema, GeoFeatureSchema, HealthSchema, RiverEnvelopeSchema,
  RunsListSchema, SearchResultsSchema, StationSeriesSchema,
  type BasinEnvelope, type BasinList, type BasinReservoirs, type ForecastRun, type HefsLatest, type RiverNetwork, type GeoFeature, type Health, type RiverEnvelope,
  type RunsList, type SearchResults, type SeriesVariable, type StationSeries,
} from '../contracts/schemas';
import { lidOf } from '../app/deep-link';

const rawBase = import.meta.env.VITE_API_BASE as string | undefined;
export const API_BASE: string = rawBase !== undefined && rawBase !== ''
  ? rawBase.replace(/\/$/, '')
  : (import.meta.env.PROD ? '' : 'http://localhost:8000');

export class ApiError extends Error {
  constructor(readonly status: number, readonly path: string, detail: string) {
    super(`${status} ${path}: ${detail}`);
  }
}

async function getJson<T>(path: string, schema: ZodType<T>, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { signal, headers: { Accept: 'application/json' } });
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = String((await response.json() as { detail?: string }).detail ?? detail); } catch { /* keep statusText */ }
    throw new ApiError(response.status, path, detail);
  }
  return schema.parse(await response.json());
}

const enc = encodeURIComponent;

/** Appends the knowledge time to a time-dependent path; live ('now') requests carry no as_of. */
const withAsOf = (path: string, asOf: string | null): string =>
  asOf === null ? path : `${path}${path.includes('?') ? '&' : '?'}as_of=${enc(asOf)}`;

export const api = {
  basins: (signal?: AbortSignal): Promise<BasinList> => getJson('/basins', BasinListSchema, signal),
  geometry: (basinId: string, lod: 'state' | 'basin', signal?: AbortSignal): Promise<GeoFeature> =>
    getJson(`/basins/${enc(basinId)}/geometry?lod=${lod}`, GeoFeatureSchema, signal),
  basinState: (basinId: string, asOf: string | null, signal?: AbortSignal): Promise<BasinEnvelope> =>
    getJson(withAsOf(`/basins/${enc(basinId)}/state`, asOf), BasinEnvelopeSchema, signal),
  vizBasins: (asOf: string | null, signal?: AbortSignal): Promise<BasinEnvelope> =>
    getJson(withAsOf('/viz/basins', asOf), BasinEnvelopeSchema, signal),
  /** One observed weather field (404 = nothing current to draw — an answer, not an error). */
  vizField: (layer: string, asOf: string | null, signal?: AbortSignal): Promise<FieldRasterState> =>
    getJson(withAsOf(`/viz/fields/${enc(layer)}`, asOf), FieldRasterStateSchema, signal),
  vizRivers: (basinId: string, asOf: string | null, signal?: AbortSignal): Promise<RiverEnvelope> =>
    getJson(withAsOf(`/viz/rivers?basin=${enc(basinId)}`, asOf), RiverEnvelopeSchema, signal),
  riverState: (forecastPointId: string, asOf: string | null, signal?: AbortSignal): Promise<RiverEnvelope> =>
    getJson(withAsOf(`/forecast-points/${enc(lidOf(forecastPointId))}/state`, asOf), RiverEnvelopeSchema, signal),
  stationSeries: (stationId: string, variable: SeriesVariable, asOf: string | null, signal?: AbortSignal): Promise<StationSeries> =>
    getJson(withAsOf(`/stations/${enc(stationId)}/series?variable=${variable}`, asOf), StationSeriesSchema, signal),
  /** The provider's own HEFS exceedance ladder, verbatim, known at as_of (404 = none known). */
  hefsLatest: (forecastPointId: string, asOf: string | null, signal?: AbortSignal): Promise<HefsLatest> =>
    getJson(withAsOf(`/forecast-points/${enc(lidOf(forecastPointId))}/hefs/latest`, asOf), HefsLatestSchema, signal),
  latestRun: (forecastPointId: string, asOf: string | null, signal?: AbortSignal): Promise<ForecastRun> =>
    getJson(withAsOf(`/forecast-points/${enc(lidOf(forecastPointId))}/runs/latest`, asOf), ForecastRunSchema, signal),
  /** Observed series over an absolute valid-time window (event replay; no as_of — see event/registry). */
  seriesWindow: (stationId: string, variable: SeriesVariable, start: string, end: string, signal?: AbortSignal): Promise<StationSeries> =>
    getJson(`/stations/${enc(stationId)}/series?variable=${variable}&start=${enc(start)}&end=${enc(end)}`, StationSeriesSchema, signal),
  /** Every forecast run issued inside the window, ascending; superseded runs included. */
  runs: (forecastPointId: string, start: string, end: string, signal?: AbortSignal): Promise<RunsList> =>
    getJson(`/forecast-points/${enc(lidOf(forecastPointId))}/runs?start=${enc(start)}&end=${enc(end)}`, RunsListSchema, signal),
  /** Latest reservoir state per dam in the basin; empty for an unregulated basin (the truth). */
  basinReservoirs: (basinId: string, asOf: string | null, signal?: AbortSignal): Promise<BasinReservoirs> =>
    getJson(withAsOf(`/basins/${enc(basinId)}/reservoirs`, asOf), BasinReservoirsSchema, signal),
  /** The derived river network — cartographic, static; cached for the app's lifetime. */
  riverNetwork: (signal?: AbortSignal): Promise<RiverNetwork> =>
    getJson('/geo/rivers', RiverNetworkSchema, signal),
  search: (q: string, signal?: AbortSignal): Promise<SearchResults> => getJson(`/search?q=${enc(q)}`, SearchResultsSchema, signal),
  health: (signal?: AbortSignal): Promise<Health> => getJson('/system/health', HealthSchema, signal),
};
