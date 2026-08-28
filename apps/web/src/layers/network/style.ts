/**
 * River-network styling: pure, total mapping from (mainstem, band, basin selection, flow
 * intensity) to line presentation.
 *
 * Two registers meet here WITHOUT blurring. The skeleton — where the rivers are, which is the
 * mainstem, one water-cyan hue — is CARTOGRAPHIC. On top of it, `intensity` carries the
 * contract's `flow_visual_intensity` (the sanctioned display hint: the station's day-of-year
 * flow percentile / 100, VISUALIZATION_CONTRACTS §3), and it modulates ONLY width and alpha —
 * presence, a non-colour carrier (§7.2). The hue never changes and no category is ever
 * encoded: a swollen river reads bigger, not redder. `intensity: null` is the honest absence
 * — the line falls back to the cartographic base, so a river nothing is known about looks
 * like a map, never like a calm river. The hint's provenance (gauge, record span, freshness)
 * renders in the basin panel beside the percentile itself.
 *
 * "Rivers as first-class visual objects" (design direction 2026-08-28): the hydrologic
 * network is the skeleton of Cascadia's world and draws from the overview down — mainstems
 * from orbit, the full network once a basin has the frame, and the rivers RESPOND where a
 * defensible percentile exists.
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { Band } from '../../scene/bands';

export interface RiverLineSemantic {
  mainstem: boolean;
  band: Band;
  /** The river's basin is the selected one. */
  inSelectedBasin: boolean;
  /** `flow_visual_intensity` for this river (0–1), or null when nothing is known. */
  intensity: number | null;
}

export interface RiverLineStyle {
  show: boolean;
  widthPx: number;
  color: Hsl;
  alpha: number;
}

/** Full-intensity width growth, in px: a p100 mainstem doubles its cartographic width. */
const STEM_SWELL_PX = 1.8;
const TRIB_SWELL_PX = 0.8;
/** Full-intensity alpha lift — small on purpose; presence is carried by width first. */
const ALPHA_LIFT = 0.15;

export function riverLine(s: RiverLineSemantic): RiverLineStyle {
  const overview = s.band === 'orbital';
  if (overview && !s.mainstem) {
    return { show: false, widthPx: 0, color: COLOR.cyan, alpha: 0 };
  }
  const lift = s.intensity == null ? 0 : Math.min(Math.max(s.intensity, 0), 1);
  const baseWidth = s.mainstem ? (overview ? 1.4 : 1.8) : 1.0;
  const width = baseWidth + (s.mainstem ? STEM_SWELL_PX : TRIB_SWELL_PX) * lift;
  const alpha = ((s.mainstem ? 0.8 : 0.4) + ALPHA_LIFT * lift) * (s.inSelectedBasin ? 1.15 : 1);
  return { show: true, widthPx: width, color: COLOR.cyan, alpha: Math.min(alpha, 0.95) };
}
