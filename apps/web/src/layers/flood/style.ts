/**
 * Static flood-hazard styling: pure, total mapping from (hazard class, band, availability) to
 * presentation. STATIC HAZARD is its own register — regulatory map geometry of a specific
 * study vintage — and must never read as current water, forecast concern, or Cascade
 * derivation. So: a desaturated slate family (never the water cyan, never the derived amber,
 * never any official warning colour), fills quieter than every live overlay, and the 0.2%
 * zone is outline-only — the faintest voice for the faintest statement.
 *
 * A basin whose availability is not 'covered' draws NOTHING from FEMA here — and the absence
 * itself is stated in the panel (FloodMappingNote): absence of shading is absence of DATA.
 * Levees: NLD centerlines, bronze dashes — infrastructure presence, never "protection"
 * (VTD §3.5).
 */
import type { Band } from '../../scene/bands';

export type HazardClass = 'floodway' | 'sfha' | 'pct02';
export type FloodAvailability = 'covered' | 'partial_edges_only' | 'no_digital_data';

export interface HazardZoneStyle {
  show: boolean;
  fill: { h: number; s: number; l: number };
  fillAlpha: number;
  outlineAlpha: number;
  dashed: boolean;
}

/** Slate — the register's one hue family; class separates by weight, never by hue. */
const SLATE = { h: 214, s: 32, l: 62 };

export function hazardZone(cls: HazardClass, band: Band, availability: FloodAvailability): HazardZoneStyle {
  const none = { show: false, fill: SLATE, fillAlpha: 0, outlineAlpha: 0, dashed: false };
  if (availability !== 'covered' && availability !== 'partial_edges_only') return none;
  const bandShows = cls === 'pct02' ? band === 'local' : band === 'river' || band === 'local';
  if (!bandShows) return none;
  switch (cls) {
    case 'floodway':
      return { show: true, fill: SLATE, fillAlpha: 0.16, outlineAlpha: 0.5, dashed: false };
    case 'sfha':
      return { show: true, fill: SLATE, fillAlpha: 0.09, outlineAlpha: 0.22, dashed: false };
    case 'pct02':
      return { show: true, fill: SLATE, fillAlpha: 0, outlineAlpha: 0.3, dashed: true };
  }
}

export interface LeveeStyle {
  show: boolean;
  color: { h: number; s: number; l: number };
  alpha: number;
  widthPx: number;
}

/** Bronze: earthwork infrastructure, unmistakably not water and not hazard shading. */
const BRONZE = { h: 38, s: 34, l: 58 };

export function leveeLine(band: Band): LeveeStyle {
  const shows = band === 'river' || band === 'local';
  return { show: shows, color: BRONZE, alpha: shows ? 0.85 : 0, widthPx: 1.6 };
}
