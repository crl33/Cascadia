/**
 * Camera-marker styling: pure, total mapping from (tier, band, pinned) to marker presentation.
 *
 * The semantic-zoom contract for the flood-observation network (mission §12, doctrine-tuned):
 *   orbital/state — hidden entirely (a camera is local evidence, not orientation);
 *   basin        — Tier A only, small and quiet;
 *   river        — Tiers A+B, legible markers;
 *   local        — every curated camera, full presence.
 * Pinned cameras are always shown at any band that shows the layer at all.
 *
 * Register: cameras are INSTRUMENTS (cartographic presence). Nothing here encodes hydrologic
 * state — the dynamic-attention treatment (official-warning emphasis) is a later, separately
 * truth-labeled pass; a camera never turns red because a model is worried.
 */
import type { Band } from '../../scene/bands';

export type CameraTier = 'A' | 'B' | 'C';

export interface CameraMarkerSemantic {
  tier: CameraTier;
  band: Band;
  pinned: boolean;
}

export interface CameraMarkerStyle {
  show: boolean;
  /** Marker square size in px (the billboard is a generated glyph). */
  sizePx: number;
  alpha: number;
}

const TIER_FLOOR_BAND: Record<CameraTier, Band[]> = {
  A: ['basin', 'river', 'local'],
  B: ['river', 'local'],
  C: ['local'],
};

export function cameraMarker(s: CameraMarkerSemantic): CameraMarkerStyle {
  const eligible = TIER_FLOOR_BAND[s.tier].includes(s.band);
  if (!eligible && !(s.pinned && s.band !== 'orbital' && s.band !== 'state')) {
    return { show: false, sizePx: 0, alpha: 0 };
  }
  const base = s.band === 'local' ? 22 : s.band === 'river' ? 18 : 14;
  return {
    show: true,
    sizePx: s.pinned ? base + 6 : base,
    alpha: s.pinned ? 1 : s.tier === 'A' ? 0.92 : 0.78,
  };
}
