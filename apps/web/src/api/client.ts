/**
 * Typed fetchers for the SPIKE API SPEC. Every response is parsed with its zod schema before it
 * reaches the app; an AbortSignal is passed through so TanStack Query can cancel stale requests.
 * VITE_API_BASE overrides the backend origin. Unset: localhost:8000 in `vite`/`vitest`,
 * same-origin (`''`) in `vite build` so Cloudflare Pages can serve the stub API next to the app.
 * No other module calls fetch.
 */
import type { ZodType } from 'zod';
import {
  BasinEnvelopeSchema, BasinListSchema, GeoFeatureSchema, HealthSchema, RiverEnvelopeSchema, SearchResultsSchema,
  type BasinEnvelope, type BasinList, type GeoFeature, type Health, type RiverEnvelope, type SearchResults,
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

export const api = {
  basins: (signal?: AbortSignal): Promise<BasinList> => getJson('/basins', BasinListSchema, signal),
  geometry: (basinId: string, lod: 'state' | 'basin', signal?: AbortSignal): Promise<GeoFeature> =>
    getJson(`/basins/${enc(basinId)}/geometry?lod=${lod}`, GeoFeatureSchema, signal),
  basinState: (basinId: string, signal?: AbortSignal): Promise<BasinEnvelope> =>
    getJson(`/basins/${enc(basinId)}/state`, BasinEnvelopeSchema, signal),
  vizBasins: (signal?: AbortSignal): Promise<BasinEnvelope> => getJson('/viz/basins', BasinEnvelopeSchema, signal),
  vizRivers: (basinId: string, signal?: AbortSignal): Promise<RiverEnvelope> =>
    getJson(`/viz/rivers?basin=${enc(basinId)}`, RiverEnvelopeSchema, signal),
  riverState: (forecastPointId: string, signal?: AbortSignal): Promise<RiverEnvelope> =>
    getJson(`/forecast-points/${enc(lidOf(forecastPointId))}/state`, RiverEnvelopeSchema, signal),
  search: (q: string, signal?: AbortSignal): Promise<SearchResults> => getJson(`/search?q=${enc(q)}`, SearchResultsSchema, signal),
  health: (signal?: AbortSignal): Promise<Health> => getJson('/system/health', HealthSchema, signal),
};
