/**
 * BasemapProvider / terrain abstraction (docs/CINEMATIC_ARCHITECTURE.md §10). The keyless OSM
 * provider with ellipsoid terrain is the default (ADR-0006). Other providers register here and
 * are selected by id through VITE_BASEMAP (or later /config/public) — no code changes elsewhere.
 * Keys never live in the bundle: a `requiresKey` provider must receive its key at createImagery time.
 */
import { Credit, EllipsoidTerrainProvider, ImageryLayer, OpenStreetMapImageryProvider, type TerrainProvider } from 'cesium';

export interface BasemapProvider {
  id: string;
  kind: 'satellite' | 'aerial' | 'terrain' | 'orthophoto' | 'natural_colour' | 'low_light_analytical';
  attribution: string;
  usage: { maxZoom: number; prefetchAllowed: boolean };
  cspHosts: readonly string[];
  requiresKey: boolean;
  terrainLevel: 'ellipsoid' | 'global' | 'regional_dem';
  createImagery(key?: string): ImageryLayer;
  createTerrain(key?: string): TerrainProvider;
}

export const OSM_ATTRIBUTION = '© OpenStreetMap contributors';

/**
 * The muted ground (design direction 2026-08-28): raw OSM's green parks, red highways and
 * label clutter were the loudest visual language on screen — an engineering-GIS look, not
 * Cascadia's world. These are Cesium ImageryLayer colour adjustments applied at the LAYER, so
 * the tiles, attribution and usage policy are untouched: the same cartography, spoken quietly,
 * under which cyan water and amber tension are the only saturated things.
 */
export const BASEMAP_SATURATION = 0.25;
export const BASEMAP_BRIGHTNESS = 0.82;
export const BASEMAP_CONTRAST = 1.05;
export const BASEMAP_GAMMA = 1.08;

function muted(layer: ImageryLayer): ImageryLayer {
  layer.saturation = BASEMAP_SATURATION;
  layer.brightness = BASEMAP_BRIGHTNESS;
  layer.contrast = BASEMAP_CONTRAST;
  layer.gamma = BASEMAP_GAMMA;
  return layer;
}

export const osmKeyless: BasemapProvider = {
  id: 'osm-keyless',
  kind: 'natural_colour',
  attribution: OSM_ATTRIBUTION,
  usage: { maxZoom: 18, prefetchAllowed: false },
  cspHosts: ['https://tile.openstreetmap.org'],
  requiresKey: false,
  terrainLevel: 'ellipsoid',
  createImagery: () =>
    muted(new ImageryLayer(
      new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/', maximumLevel: 18, credit: new Credit(OSM_ATTRIBUTION, true) }),
    )),
  createTerrain: () => new EllipsoidTerrainProvider(),
};

const registry = new Map<string, BasemapProvider>([[osmKeyless.id, osmKeyless]]);

/** Config hook: register an ion/vendor provider at startup; select it with VITE_BASEMAP=<id>. */
export function registerBasemap(provider: BasemapProvider): void {
  registry.set(provider.id, provider);
}

export function resolveBasemap(id: string | undefined = import.meta.env.VITE_BASEMAP as string | undefined): BasemapProvider {
  const provider = registry.get(id ?? osmKeyless.id);
  if (!provider) {
    console.warn(`basemap "${id}" is not registered; falling back to ${osmKeyless.id}`);
    return osmKeyless;
  }
  return provider;
}
