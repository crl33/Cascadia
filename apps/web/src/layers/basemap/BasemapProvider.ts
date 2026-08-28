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
  UrlTemplateImageryProvider,
  type TerrainProvider,
} from 'cesium';

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

export const usgsImagery: BasemapProvider = {
  id: 'usgs-imagery',
  kind: 'orthophoto',
  attribution: USGS_IMAGERY_ATTRIBUTION,
  // Content stops at the service's stated 1:9,028 scale; requesting deeper returns upsampled
  // or empty tiles, so the ceiling is declared rather than discovered per camera move.
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
        }),
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
