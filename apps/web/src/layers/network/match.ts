/**
 * Joining the contract's per-station `flow_visual_intensity` onto the OSM river geometry.
 *
 * The two datasets share no key — forecast points carry NWPS lids and USGS station ids, the
 * network carries OSM river names — so the join is the one thing both actually state: the
 * river's name inside the station's name. "Skagit River near Mount Vernon" names the Skagit
 * River; a station that names no network river intensifies nothing, and a river no station
 * names stays at its cartographic base. That asymmetric honesty is the point: a failed match
 * degrades to "map", never to a wrong river swelling.
 *
 * Same-basin only, and the maximum across matching stations: a river with two gauges reads
 * as its busier reach, which errs toward visibility, never toward calm. Pure and total —
 * tested in match.test.ts; no Cesium, no React.
 */
import type { RiverNetwork } from '../../contracts/schemas';

/** The slice of `RiverVisualizationState` the join reads. */
export interface RiverStateForMatch {
  basin_id: string;
  name: string;
  flow_visual_intensity?: number | null;
}

export function riverIntensityKey(basinId: string, riverName: string): string {
  return `${basinId}|${riverName}`;
}

export function riverIntensities(
  network: RiverNetwork,
  states: readonly RiverStateForMatch[],
): Record<string, number> {
  const out: Record<string, number> = {};
  const known = states.filter((s) => s.flow_visual_intensity != null);
  if (known.length === 0) return out;
  for (const [basinId, basin] of Object.entries(network.basins)) {
    for (const river of basin.rivers) {
      const riverName = river.name.toLowerCase();
      if (riverName === '(unnamed)') continue;
      for (const state of known) {
        if (state.basin_id !== basinId) continue;
        if (!state.name.toLowerCase().includes(riverName)) continue;
        const key = riverIntensityKey(basinId, river.name);
        const intensity = state.flow_visual_intensity as number;
        out[key] = Math.max(out[key] ?? 0, intensity);
      }
    }
  }
  return out;
}
