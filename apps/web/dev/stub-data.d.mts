// Type surface of dev/stub-data.mjs used by the vitest schema check; the runtime is plain JS.
export interface StubFixtures { basinLod: unknown; stateLod: unknown; basinEnvelope: unknown; riverEnvelope: unknown; samples: unknown; tier0?: unknown }
export const SEED_POINTS: readonly { id: string; lid: string; name: string; station_id: string; basin_id: string; location: [number, number] }[];
export function buildVizBasins(fx: StubFixtures, asOf?: string | null): unknown;
export function buildBasinState(fx: StubFixtures, id: string, asOf?: string | null): unknown;
export function buildRiverState(fx: StubFixtures, lid: string, asOf?: string | null): unknown;
export function buildVizRivers(fx: StubFixtures, basinId: string, asOf?: string | null): unknown;
export function buildSceneSummary(fx: StubFixtures, band: string, basinId: string | null, asOf?: string | null): unknown;
export function buildSearch(fx: StubFixtures, q: string): { items: unknown[] };
export function buildHealth(fx: StubFixtures, now?: Date): unknown;
export function buildRunsLatest(fx: StubFixtures, lid: string): unknown;
export function buildSeries(fx: StubFixtures, stationId: string, variable: string): unknown;
