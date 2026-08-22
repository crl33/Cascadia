/**
 * The query layer: TanStack Query hooks over api/client.ts. Components and the scene bridge use
 * these and never fetch directly. staleTime follows product cadence (observations 15 min,
 * geography effectively static).
 */
import { QueryClient, useQueries, useQuery, type UseQueryResult } from '@tanstack/react-query';
import type { GeoFeature } from '../contracts/schemas';
import { api } from './client';
import { keys } from './keys';

const MINUTE_MS = 60_000;

export const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 5 * MINUTE_MS } },
});

export const useBasins = () =>
  useQuery({ queryKey: keys.basins(), queryFn: ({ signal }) => api.basins(signal), staleTime: Infinity });

export const useBasinGeometry = (basinId: string | null, lod: 'state' | 'basin') =>
  useQuery({
    queryKey: keys.geometry(basinId ?? '', lod),
    queryFn: ({ signal }) => api.geometry(basinId!, lod, signal),
    enabled: basinId !== null,
    staleTime: Infinity,
  });

/** Stable combine (structurally shared by TanStack) so callers can depend on the result array. */
const combineFeatures = (results: UseQueryResult<GeoFeature>[]): (GeoFeature | null)[] => results.map((r) => r.data ?? null);

export const useBasinGeometries = (basinIds: readonly string[], lod: 'state' | 'basin') =>
  useQueries({
    queries: basinIds.map((id) => ({
      queryKey: keys.geometry(id, lod),
      queryFn: ({ signal }: { signal: AbortSignal }) => api.geometry(id, lod, signal),
      staleTime: Infinity,
    })),
    combine: combineFeatures,
  });

export const useBasinState = (basinId: string | null) =>
  useQuery({
    queryKey: keys.basinState(basinId ?? ''),
    queryFn: ({ signal }) => api.basinState(basinId!, signal),
    enabled: basinId !== null,
    staleTime: 15 * MINUTE_MS,
  });

export const useVizBasins = () =>
  useQuery({ queryKey: keys.vizBasins(), queryFn: ({ signal }) => api.vizBasins(signal), staleTime: 15 * MINUTE_MS });

export const useVizRivers = (basinId: string | null) =>
  useQuery({
    queryKey: keys.vizRivers(basinId ?? ''),
    queryFn: ({ signal }) => api.vizRivers(basinId!, signal),
    enabled: basinId !== null,
    staleTime: 15 * MINUTE_MS,
  });

export const useRiverState = (forecastPointId: string | null) =>
  useQuery({
    queryKey: keys.riverState(forecastPointId ?? ''),
    queryFn: ({ signal }) => api.riverState(forecastPointId!, signal),
    enabled: forecastPointId !== null,
    staleTime: 15 * MINUTE_MS,
  });

export const useSearch = (q: string) =>
  useQuery({
    queryKey: keys.search(q),
    queryFn: ({ signal }) => api.search(q, signal),
    enabled: q.trim().length >= 2,
    staleTime: 5 * MINUTE_MS,
  });

export const useHealth = () =>
  useQuery({ queryKey: keys.health(), queryFn: ({ signal }) => api.health(signal), refetchInterval: MINUTE_MS, staleTime: MINUTE_MS });
