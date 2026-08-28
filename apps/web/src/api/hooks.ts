/**
 * The query layer: TanStack Query hooks over api/client.ts. Components and the scene bridge use
 * these and never fetch directly. Every time-dependent hook reads the knowledge time from the
 * store, keys on it and forwards it — replay is a cache dimension, not a refetch. staleTime
 * follows product cadence (observations 15 min, geography effectively static); a replayed
 * (as_of) document is a pure function of the database at that instant, so it never goes stale.
 */
import { QueryClient, useQueries, useQuery, type UseQueryResult } from '@tanstack/react-query';
import type { GeoFeature, SeriesVariable } from '../contracts/schemas';
import { useSceneStore } from '../state/store';
import { api } from './client';
import { keys } from './keys';

const MINUTE_MS = 60_000;

export const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 5 * MINUTE_MS } },
});

/** The knowledge time every time-dependent query is keyed by (null while live). */
const useAsOf = (): string | null => useSceneStore((s) => s.timeline.asOf);

const timeDependentStale = (asOf: string | null): number => (asOf === null ? 15 * MINUTE_MS : Infinity);

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

export const useHefsLatest = (forecastPointId: string | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.hefsLatest(forecastPointId ?? '', asOf),
    queryFn: ({ signal }) => api.hefsLatest(forecastPointId!, asOf, signal),
    enabled: forecastPointId !== null,
    retry: false, // a 404 is an answer (no ladder known at this knowledge time), not a flake
    staleTime: timeDependentStale(asOf),
  });
};

export const useRiverNetwork = () =>
  useQuery({
    queryKey: keys.riverNetwork(),
    queryFn: ({ signal }) => api.riverNetwork(signal),
    staleTime: Infinity, // cartographic and static: rivers do not move between deploys
    retry: false, // a 404 means no network was derived in this deployment — an answer
  });

export const useBasinReservoirs = (basinId: string | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.basinReservoirs(basinId ?? '', asOf),
    queryFn: ({ signal }) => api.basinReservoirs(basinId!, asOf, signal),
    enabled: basinId !== null,
    staleTime: timeDependentStale(asOf),
  });
};

export const useBasinState = (basinId: string | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.basinState(basinId ?? '', asOf),
    queryFn: ({ signal }) => api.basinState(basinId!, asOf, signal),
    enabled: basinId !== null,
    staleTime: timeDependentStale(asOf),
  });
};

export const useVizBasins = () => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.vizBasins(asOf),
    queryFn: ({ signal }) => api.vizBasins(asOf, signal),
    staleTime: timeDependentStale(asOf),
  });
};

export const useVizField = (layer: string) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.vizField(layer, asOf),
    queryFn: ({ signal }) => api.vizField(layer, asOf, signal),
    staleTime: timeDependentStale(asOf),
    retry: false, // a 404 is an answer ("nothing current to draw"), rendered as absence
  });
};

export const useVizRivers = (basinId: string | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.vizRivers(basinId ?? '', asOf),
    queryFn: ({ signal }) => api.vizRivers(basinId!, asOf, signal),
    enabled: basinId !== null,
    staleTime: timeDependentStale(asOf),
  });
};

export const useRiverState = (forecastPointId: string | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.riverState(forecastPointId ?? '', asOf),
    queryFn: ({ signal }) => api.riverState(forecastPointId!, asOf, signal),
    enabled: forecastPointId !== null,
    staleTime: timeDependentStale(asOf),
  });
};

/** Observed series for a station on the charted basis; disabled until both are known. */
export const useStationSeries = (stationId: string | null, variable: SeriesVariable | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.stationSeries(stationId ?? '', variable ?? 'stage', asOf),
    queryFn: ({ signal }) => api.stationSeries(stationId!, variable!, asOf, signal),
    enabled: stationId !== null && variable !== null,
    staleTime: timeDependentStale(asOf),
  });
};

/** Latest official forecast run for a forecast point — 'latest' is relative to the knowledge time. */
export const useLatestRun = (forecastPointId: string | null) => {
  const asOf = useAsOf();
  return useQuery({
    queryKey: keys.latestRun(forecastPointId ?? '', asOf),
    queryFn: ({ signal }) => api.latestRun(forecastPointId!, asOf, signal),
    enabled: forecastPointId !== null,
    staleTime: timeDependentStale(asOf),
  });
};

/** Archived observed series over an absolute event window; fetched once (an archive never goes stale). */
export const useSeriesWindow = (stationId: string | null, variable: SeriesVariable | null, window: readonly [string, string] | null) =>
  useQuery({
    queryKey: keys.seriesWindow(stationId ?? '', variable ?? 'stage', window?.[0] ?? '', window?.[1] ?? ''),
    queryFn: ({ signal }) => api.seriesWindow(stationId!, variable!, window![0], window![1], signal),
    enabled: stationId !== null && variable !== null && window !== null,
    staleTime: Infinity,
  });

/** Every forecast run issued inside the event window (superseded included); fetched once. */
export const useRunsList = (forecastPointId: string | null, window: readonly [string, string] | null) =>
  useQuery({
    queryKey: keys.runs(forecastPointId ?? '', window?.[0] ?? '', window?.[1] ?? ''),
    queryFn: ({ signal }) => api.runs(forecastPointId!, window![0], window![1], signal),
    enabled: forecastPointId !== null && window !== null,
    staleTime: Infinity,
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
