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

export const osmKeyless: BasemapProvider = {
  id: 'osm-keyless',
  kind: 'natural_colour',
  attribution: OSM_ATTRIBUTION,
  usage: { maxZoom: 18, prefetchAllowed: false },
  cspHosts: ['https://tile.openstreetmap.org'],
  requiresKey: false,
  terrainLevel: 'ellipsoid',
  createImagery: () =>
    new ImageryLayer(
      new OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/', maximumLevel: 18, credit: new Credit(OSM_ATTRIBUTION, true) }),
    ),
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
