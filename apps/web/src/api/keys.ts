/** Query keys, keyed by entity id (and LOD/variable where relevant). One place, no ad-hoc keys. */
export const keys = {
  basins: () => ['basins'] as const,
  geometry: (basinId: string, lod: 'state' | 'basin') => ['geo', 'basin', basinId, lod] as const,
  basinState: (basinId: string) => ['basin-state', basinId] as const,
  vizBasins: () => ['viz', 'basins'] as const,
  vizRivers: (basinId: string) => ['viz', 'rivers', basinId] as const,
  riverState: (forecastPointId: string) => ['river-state', forecastPointId] as const,
  search: (q: string) => ['search', q] as const,
  health: () => ['system', 'health'] as const,
};
