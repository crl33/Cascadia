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
  /** Some OTHER camera is the open preview — this marker steps back so the spatial
   * correspondence between marker and card is unmistakable (mission §18). */
  otherPinned?: boolean;
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
  B: ['basin', 'river', 'local'], // promoted 2026-08-29: most curated flood cameras are B, and
  C: ['local'],                   // a basin view with two visible cameras read as "no network"
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
  // Legibility pass 2026-08-29: the previous 14-22 px marks sank into arbitrary satellite
  // imagery. Sizes up, and the glyph itself gained a dark disc + white halo (CameraLayer).
  const base = s.band === 'local' ? 30 : s.band === 'river' ? 26 : 20;
  const emphasized = s.pinned || s.attention;
  const quieted = s.otherPinned === true && !s.pinned;
  return {
    show: true,
    sizePx: emphasized ? base + 6 : base,
    alpha: quieted ? 0.45 : emphasized ? 1 : s.tier === 'A' ? 1 : 0.9,
    // the OPEN camera earns the ring too — the marker↔card correspondence (§18)
    ring: s.attention || s.pinned,
  };
}
