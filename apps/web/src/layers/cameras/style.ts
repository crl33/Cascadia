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
  /** OFFICIAL evidence names this camera's basin (attention.ts) — never derived, never a score. */
  attention: boolean;
}

export interface CameraMarkerStyle {
  show: boolean;
  /** Marker square size in px (the billboard is a generated glyph). */
  sizePx: number;
  alpha: number;
  /** The attention treatment is a RING variant of the glyph — a non-colour carrier. */
  ring: boolean;
}

const TIER_FLOOR_BAND: Record<CameraTier, Band[]> = {
  A: ['basin', 'river', 'local'],
  B: ['river', 'local'],
  C: ['local'],
};
/** Under official attention every tier surfaces one band earlier (mission §14) — official
 * evidence, and only official evidence, promotes the corridor's cameras. */
const ATTENTION_FLOOR_BAND: Record<CameraTier, Band[]> = {
  A: ['basin', 'river', 'local'],
  B: ['basin', 'river', 'local'],
  C: ['river', 'local'],
};

export function cameraMarker(s: CameraMarkerSemantic): CameraMarkerStyle {
  const floors = s.attention ? ATTENTION_FLOOR_BAND : TIER_FLOOR_BAND;
  const eligible = floors[s.tier].includes(s.band);
  if (!eligible && !(s.pinned && s.band !== 'orbital' && s.band !== 'state')) {
    return { show: false, sizePx: 0, alpha: 0, ring: false };
  }
  const base = s.band === 'local' ? 22 : s.band === 'river' ? 18 : 14;
  const emphasized = s.pinned || s.attention;
  return {
    show: true,
    sizePx: emphasized ? base + 6 : base,
    alpha: emphasized ? 1 : s.tier === 'A' ? 0.92 : 0.78,
    ring: s.attention,
  };
}
