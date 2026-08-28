/**
 * Basin edge styling: pure, total mapping from semantic state to presentation (widths, tokens,
 * alpha). No renderer calls. Boundaries are embedded in the landscape (LAYER_SYSTEM §9.3): faint
 * hairline at orbital/state, a gentle stronger edge for the selected basin, amber/red only from
 * official categories.
 */
import { COLOR, type Hsl } from '../../design-system/tokens';
import type { FloodCategory } from '../../contracts/schemas';
import type { Band } from '../../scene/bands';

export interface BasinEdgeSemantic {
  lod: 'state' | 'basin';
  band: Band;
  selected: boolean;
  hovered: boolean;
  /** Official hazard category of the basin outlet, or 'unknown'. */
  category: FloodCategory;
  /** At least one active NWS alert routed to this basin (any event type). */
  alerted: boolean;
  /** Whether a basin-LOD outline exists for this basin (then the state-LOD one yields to it). */
  hasBasinLod: boolean;
}

export interface EdgeStyle { show: boolean; widthPx: number; color: Hsl; alpha: number; fadeIn: boolean; dashed: boolean }

const categoryColor = (category: FloodCategory): Hsl => {
  switch (category) {
    case 'none': return COLOR.cyan;
    case 'action': return COLOR.amberWatch;
    case 'minor': return COLOR.amberElevated;
    case 'moderate':
    case 'major': return COLOR.floodRed;
    case 'unknown': return COLOR.neutralUnknown;
  }
};

export function basinEdge(s: BasinEdgeSemantic): EdgeStyle {
  const color = categoryColor(s.category);
  const overview = s.band === 'orbital' || s.band === 'state';
  // An active NWS alert is carried by the DASH — a non-colour channel, the stripe principle
  // (VISUAL_TRUTH_DOCTRINE): colour stays the outlet category, because an Air Quality Alert
  // must not paint a basin flood-amber, and a dash says "an official advisory names this
  // basin — open it" without asserting severity the edge does not know.
  const dashed = s.alerted;
  if (s.lod === 'basin') {
    // Only the selected basin carries a basin-LOD outline; it is the stronger edge at every band.
    return { show: s.selected, widthPx: 2.2, color, alpha: 0.9, fadeIn: true, dashed };
  }
  if (s.selected && s.hasBasinLod) return { show: false, widthPx: 0, color, alpha: 0, fadeIn: false, dashed };
  if (s.selected) return { show: true, widthPx: 2, color, alpha: 0.85, fadeIn: true, dashed };
  if (!overview) return { show: false, widthPx: 0, color, alpha: 0, fadeIn: false, dashed };
  if (s.hovered) return { show: true, widthPx: 1.6, color, alpha: 0.6, fadeIn: false, dashed };
  // an alerted basin keeps a slightly firmer resting edge, so the dash is findable from orbit
  if (s.alerted) return { show: true, widthPx: 1.4, color, alpha: 0.5, fadeIn: false, dashed: true };
  return { show: true, widthPx: 1, color, alpha: 0.32, fadeIn: false, dashed: false };
}
