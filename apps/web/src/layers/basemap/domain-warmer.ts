/**
 * Domain warmer — the availability fix (owner 2026-09-01: "shift smoothly between those
 * terrain maps"). Rendering knobs cannot unify a view whose data is missing: Cesium always
 * draws the best it HAS, and never-visited regions only have the coarse base. So the whole
 * bounded PNW pyramid is made AVAILABLE up front:
 *
 *   boot   z5–z9 across HARD_DOMAIN (434 tiles, ~8–16 MB once) — a REAL loading-screen
 *          stage with real counts; tiles land in the browser HTTP cache (max-age 86400),
 *          so Cesium's own requests then resolve from disk in milliseconds and every
 *          state/basin-band zoom or pan renders from complete, uniform data;
 *   idle   z10 across the domain after reveal, small concurrency, quietly.
 *
 * Pure tile math is exported for tests; fetching is plain fetch() so the HTTP cache does
 * the work — no Cesium internals touched. The provider's usage terms record
 * prefetchAllowed: true (public-domain USGS/USDA).
 */
import { HARD_DOMAIN } from '../../camera/envelope';

const TILE_URL = (z: number, y: number, x: number): string =>
  `https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/${z}/${y}/${x}`;

export interface TileAddress {
  z: number;
  x: number;
  y: number;
}

const lonToX = (lon: number, z: number): number => Math.floor(((lon + 180) / 360) * 2 ** z);
const latToY = (lat: number, z: number): number => {
  const rad = (lat * Math.PI) / 180;
  return Math.floor(((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) * 2 ** z);
};

/** Every WebMercator tile intersecting the domain at one zoom. */
export function domainTiles(z: number, domain = HARD_DOMAIN): TileAddress[] {
  const x0 = Math.max(0, lonToX(domain.west, z));
  const x1 = Math.min(2 ** z - 1, lonToX(domain.east, z));
  const y0 = Math.max(0, latToY(domain.north, z)); // y grows southward
  const y1 = Math.min(2 ** z - 1, latToY(domain.south, z));
  const tiles: TileAddress[] = [];
  for (let y = y0; y <= y1; y += 1) for (let x = x0; x <= x1; x += 1) tiles.push({ z, x, y });
  return tiles;
}

/** The boot set: z5–z9 — complete regional availability for the analytical bands. */
export function bootTiles(domain = HARD_DOMAIN): TileAddress[] {
  const tiles: TileAddress[] = [];
  for (let z = 5; z <= 9; z += 1) tiles.push(...domainTiles(z, domain));
  return tiles;
}

async function fetchInto(tiles: TileAddress[], concurrency: number, onOne?: () => void, signal?: AbortSignal): Promise<void> {
  let index = 0;
  const worker = async (): Promise<void> => {
    while (index < tiles.length) {
      if (signal?.aborted) return;
      const t = tiles[index]!;
      index += 1;
      try {
        // default cache mode: a warm HTTP cache answers instantly on later visits
        await fetch(TILE_URL(t.z, t.y, t.x), { signal });
      } catch {
        // a failed tile warms nothing but must never stall the boot — the renderer's own
        // fallback chain (discard→parent→plate) still guarantees coverage
      }
      onOne?.();
    }
  };
  await Promise.all(Array.from({ length: concurrency }, () => worker()));
}

/** Boot warm: reports real progress for the manifest. VITE_DOMAIN_WARM=off (the e2e/CI
 * build) completes the stage instantly — every Playwright context is cache-fresh and 434
 * external fetches per spec would hammer the public service; the weighting itself stays
 * pinned by unit tests. */
export async function warmDomainForBoot(
  onProgress: (done: number, total: number) => void,
  signal?: AbortSignal,
): Promise<void> {
  if (import.meta.env.VITE_DOMAIN_WARM === 'off') {
    onProgress(1, 1);
    return;
  }
  const tiles = bootTiles();
  let done = 0;
  onProgress(0, tiles.length);
  await fetchInto(tiles, 12, () => {
    done += 1;
    onProgress(done, tiles.length);
  }, signal);
}

/** Post-reveal deep warm (z10), quiet and abortable. */
export async function warmDomainDeep(signal?: AbortSignal): Promise<void> {
  if (import.meta.env.VITE_DOMAIN_WARM === 'off') return;
  await fetchInto(domainTiles(10), 4, undefined, signal);
}
