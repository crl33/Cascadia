/**
 * BasemapProvider / terrain abstraction (docs/CINEMATIC_ARCHITECTURE.md §10). Providers
 * register here and are selected by id through VITE_BASEMAP — no code changes elsewhere.
 * Keys never live in the bundle: a `requiresKey` provider must receive its key at
 * createImagery time.
 *
 * DEFAULT (2026-08-28, satellite-first direction): `usgs-imagery` — USGS/USDA orthoimagery
 * from The National Map (`USGSImageryOnly`), probed live this date: keyless, public-domain
 * US-government imagery, `Access-Control-Allow-Origin: *`, WebMercator tiles with real
 * content to ~1:9,028 (≈ z16), refreshed June 2024 (service metadata). The EARTH is the
 * interface; a road-map raster is not. Evidence: docs/research/imagery-providers-2026-08-28.md.
 *
 * `osm-keyless` remains registered as the dev/failure fallback (ADR-0006) and is NOT the
 * intended production aesthetic.
 *
 * GRADES are per provider: the heavy mute that made road-map OSM speak quietly would kill
 * satellite imagery, whose whole point is that the world reads as real. Imagery gets a light
 * filmic grade (slight desaturation + gentle lift) so the hydrologic overlays — cyan water,
 * amber tension — stay the only saturated voices without the ground going grey.
 */
import {
  Credit,
  EllipsoidTerrainProvider,
  ImageryLayer,
  OpenStreetMapImageryProvider,
  Rectangle,
  UrlTemplateImageryProvider,
  type TerrainProvider,
} from 'cesium';
import { HARD_DOMAIN } from '../../camera/envelope';
import { WhiteTileDiscardPolicy } from './white-discard';

export interface BasemapGrade {
  saturation: number;
  brightness: number;
  contrast: number;
  gamma: number;
}

export interface BasemapProvider {
  id: string;
  kind: 'satellite' | 'aerial' | 'terrain' | 'orthophoto' | 'natural_colour' | 'low_light_analytical';
  attribution: string;
  usage: { maxZoom: number; prefetchAllowed: boolean };
  cspHosts: readonly string[];
  requiresKey: boolean;
  terrainLevel: 'ellipsoid' | 'global' | 'regional_dem';
  grade: BasemapGrade;
  createImagery(key?: string): ImageryLayer;
  /** Optional coarse ALWAYS-VALID plate rendered UNDER the main imagery: wherever a void
   * pixel goes transparent or a tile is discarded, real low-res earth shows through —
   * never the bare canvas (§5's "retain lower-resolution imagery", as a layer). */
  createBasePlate?(key?: string): ImageryLayer | null;
  createTerrain(key?: string): TerrainProvider;
}

export const OSM_ATTRIBUTION = '© OpenStreetMap contributors';
export const USGS_IMAGERY_ATTRIBUTION = 'USDA, USGS The National Map: Orthoimagery';

/** The road-map mute (design direction 2026-08-28): OSM's parks/highways/labels spoken quietly. */
export const OSM_GRADE: BasemapGrade = { saturation: 0.25, brightness: 0.82, contrast: 1.05, gamma: 1.08 };
/** The filmic grade for real orthoimagery: barely-touched earth tones under saturated overlays. */
export const IMAGERY_GRADE: BasemapGrade = { saturation: 0.88, brightness: 0.94, contrast: 1.04, gamma: 1.0 };

function graded(layer: ImageryLayer, grade: BasemapGrade): ImageryLayer {
  layer.saturation = grade.saturation;
  layer.brightness = grade.brightness;
  layer.contrast = grade.contrast;
  layer.gamma = grade.gamma;
  return layer;
}

/** LESSON (owner screenshots 2026-09-01): per-pixel white removal makes WHITE FRINGES —
 * JPEG ringing (240–249) around punched-out voids survives any tight threshold, outlining
 * every void. Per-pixel surgery is retired; the WhiteTileDiscardPolicy now discards ANY
 * tile with a substantial void region, so the parent's real imagery renders whole. */

export const usgsImagery: BasemapProvider = {
  id: 'usgs-imagery',
  kind: 'orthophoto',
  attribution: USGS_IMAGERY_ATTRIBUTION,
  // Content stops at the service's stated 1:9,028 scale; requesting deeper returns upsampled
  // or empty tiles, so the ceiling is declared rather than discovered per camera move.
  // Known data characteristics, verified against source tiles 2026-08-29: (1) collection
  // seams — adjacent NAIP campaigns differ in tone, so straight-edged brightness steps are
  // in the JPEGs themselves (e.g. the bright urban rectangle over Seattle at basin band);
  // (2) offshore voids — where no ortho collection exists at a mid LOD the service bakes
  // OPAQUE WHITE into the tile. (1) is out of scope (recolouring another agency's imagery
  // per-tile); (2) is HANDLED below by WhiteTileDiscardPolicy, which inspects each DECODED
  // tile (3×3 downsample, all regions ≥250) — the single-reference byte-length policy
  // missed differently-encoded whites at z11–z12 (owner screenshot, 2026-08-31) — so white
  // tiles at ANY zoom go INVALID and the quadtree renders the PARENT's real imagery.
  usage: { maxZoom: 16, prefetchAllowed: true },
  cspHosts: ['https://basemap.nationalmap.gov'],
  requiresKey: false,
  terrainLevel: 'regional_dem', // SceneController upgrades to the ADR-0021 pyramid post-construction
  grade: IMAGERY_GRADE,
  createImagery: () =>
    graded(
      new ImageryLayer(
        new UrlTemplateImageryProvider({
          url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}',
          maximumLevel: 16,
          credit: new Credit(USGS_IMAGERY_ATTRIBUTION, true),
          tileDiscardPolicy: new WhiteTileDiscardPolicy(),
        }),
        // The operating envelope is an imagery fact too: nothing outside the PNW domain is
        // ever requested or drawn (mission §2 — the planet is not the product).
        { rectangle: Rectangle.fromDegrees(HARD_DOMAIN.west, HARD_DOMAIN.south, HARD_DOMAIN.east, HARD_DOMAIN.north) },
      ),
      IMAGERY_GRADE,
    ),
  // The under-plate: same public-domain product, capped at z7 (a handful of tiles for the
  // whole domain, cached forever). Discard still applies (a coarse baked-white would
  // otherwise resurface); no colorToAlpha — this IS the bottom of the fallback chain.
  createBasePlate: () =>
    graded(
      new ImageryLayer(
        new UrlTemplateImageryProvider({
          url: 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}',
          maximumLevel: 7,
          credit: new Credit(USGS_IMAGERY_ATTRIBUTION, false),
          tileDiscardPolicy: new WhiteTileDiscardPolicy(),
        }),
        { rectangle: Rectangle.fromDegrees(HARD_DOMAIN.west, HARD_DOMAIN.south, HARD_DOMAIN.east, HARD_DOMAIN.north) },
      ),
      IMAGERY_GRADE,
    ),
  createTerrain: () => new EllipsoidTerrainProvider(),
};

export const osmKeyless: BasemapProvider = {
  id: 'osm-keyless',
  kind: 'natural_colour',
  attribution: OSM_ATTRIBUTION,
  usage: { maxZoom: 18, prefetchAllowed: false },
  cspHosts: ['https://tile.openstreetmap.org'],
  requiresKey: false,
  terrainLevel: 'ellipsoid',
  grade: OSM_GRADE,
  createImagery: () =>
    graded(
      new ImageryLayer(
        new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/', maximumLevel: 18, credit: new Credit(OSM_ATTRIBUTION, true) }),
      ),
      OSM_GRADE,
    ),
  createTerrain: () => new EllipsoidTerrainProvider(),
};

const registry = new Map<string, BasemapProvider>([
  [usgsImagery.id, usgsImagery],
  [osmKeyless.id, osmKeyless],
]);

/** Config hook: register an ion/vendor provider at startup; select it with VITE_BASEMAP=<id>. */
export function registerBasemap(provider: BasemapProvider): void {
  registry.set(provider.id, provider);
}

export function resolveBasemap(id: string | undefined = import.meta.env.VITE_BASEMAP as string | undefined): BasemapProvider {
  const provider = registry.get(id ?? usgsImagery.id);
  if (!provider) {
    console.warn(`basemap "${id}" is not registered; falling back to ${usgsImagery.id}`);
    return usgsImagery;
  }
  return provider;
}
