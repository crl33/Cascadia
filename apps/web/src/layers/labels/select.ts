/**
 * Label selection: pure, deterministic mapping from (label set, band, selection, projection)
 * to the labels a frame may show — SEMANTIC_ZOOM §6 with the semantic corrections of the
 * visual-continuity pass (2026-08-29).
 *
 * CLASS SEMANTICS (the conceptual fix): a basin is NOT a place. Each class carries its own
 * band window, priority and collision standing:
 *   basin — analytical region context: orbital/state/basin ONLY, always hidden at river/
 *           local (the river wins its own valley), and it LOSES every collision (mission
 *           §14: city beats basin, river beats basin);
 *   city  — stable orientation anchors, state and deeper;
 *   town  — flood-corridor communities by editorial tier (2=basin.., 3=river.., 4=local);
 *   river — anchored to its own geometry, basin and deeper;
 *   water — lakes/reservoirs on their feature, river and deeper;
 *   peak  — the hydrologic skyline, state/basin only.
 *
 * COLLISION: when a projection is supplied (the live camera), spacing is true screen pixels;
 * without one (tests, determinism), a per-band ground-distance approximation stands in. Off-
 * viewport anchors and the chrome exclusion bands drop candidates outright. Budgets cap the
 * total; the lowest-standing class drops whole first.
 */
import type { Band } from '../../scene/bands';

export type LabelKind = 'city' | 'town' | 'river' | 'basin' | 'peak' | 'water';

export interface LabelEntry {
  name: string;
  kind: LabelKind;
  /** 1 = state band and down … 4 = local only (editorial, from the build script). */
  tier: number;
  lon: number;
  lat: number;
  basin_id?: string;
}

export interface ScreenProjection {
  /** Window coords for an anchor, or null when off-globe/behind. */
  project(lon: number, lat: number): { x: number; y: number } | null;
  width: number;
  height: number;
}

export const BAND_BUDGET: Record<Band, number> = { orbital: 8, state: 14, basin: 18, river: 22, local: 16 };
/** Class band windows — the semantic core. */
const CLASS_BANDS: Record<LabelKind, readonly Band[]> = {
  basin: ['orbital', 'state', 'basin'],
  city: ['orbital', 'state', 'basin', 'river', 'local'],
  town: ['basin', 'river', 'local'],
  river: ['basin', 'river', 'local'],
  water: ['river', 'local'],
  peak: ['state', 'basin'],
};
/** Collision standing, strongest first — basin loses to everything (mission §14). */
const CLASS_PRIORITY: readonly LabelKind[] = ['city', 'river', 'town', 'water', 'peak', 'basin'];
/** Screen-space padding between accepted label RECTS, px (anchor distance alone let long
 * uppercase basin names overlap city names whose anchors were far enough apart). */
const RECT_PADDING_PX = 14;
const LABEL_HEIGHT_PX = 18;
/** Rough glyph advance for collision purposes only (SANS ~0.58 em, spaced classes wider). */
export function estimatedWidthPx(entry: LabelEntry): number {
  const spaced = entry.kind === 'basin';
  const suffix = entry.kind === 'basin' ? 6 : 0; // " BASIN"
  const px = spaced ? 11.5 : entry.kind === 'city' ? 9 : 7.5;
  return (entry.name.length + suffix) * px;
}
/** Chrome exclusion bands (top strip / timeline+credits), px. */
const EXCLUDE_TOP_PX = 64;
const EXCLUDE_BOTTOM_PX = 96;
/** Ground-distance stand-in per band when no projection is available (approximation). */
const BAND_MIN_SEPARATION_DEG: Record<Band, number> = { orbital: 0.5, state: 0.24, basin: 0.1, river: 0.035, local: 0.012 };

function separationDeg(a: LabelEntry, b: LabelEntry): number {
  const latScale = Math.cos(((a.lat + b.lat) / 2) * (Math.PI / 180));
  return Math.hypot((a.lon - b.lon) * latScale, a.lat - b.lat);
}

export function selectLabels(
  labels: readonly LabelEntry[],
  band: Band,
  selectedBasinId: string | null,
  projection?: ScreenProjection,
): LabelEntry[] {
  const eligible = labels.filter((entry) => {
    if (!CLASS_BANDS[entry.kind].includes(band)) return false;
    // the opening scene must still orient by its major cities (mission §27) — but only
    // the tier-1 anchors join the basin frame at orbital
    if (entry.kind === 'city' && band === 'orbital' && entry.tier > 1) return false;
    // towns/rivers keep their editorial depth tiers inside their class window
    if ((entry.kind === 'town' || entry.kind === 'river') && band === 'basin' && entry.tier > 2) return false;
    if (entry.kind === 'town' && band === 'river' && entry.tier > 3) return false;
    return true;
  });

  const rank = (entry: LabelEntry): number => CLASS_PRIORITY.indexOf(entry.kind);
  const sorted = [...eligible].sort((a, b) => {
    const classOrder = rank(a) - rank(b);
    if (classOrder !== 0) return classOrder;
    const aSelected = selectedBasinId !== null && a.basin_id === selectedBasinId ? 0 : 1;
    const bSelected = selectedBasinId !== null && b.basin_id === selectedBasinId ? 0 : 1;
    if (aSelected !== bSelected) return aSelected - bSelected;
    if (a.tier !== b.tier) return a.tier - b.tier;
    return a.name.localeCompare(b.name);
  });

  const accepted: LabelEntry[] = [];
  if (projection) {
    const placed: { x: number; y: number; halfW: number }[] = [];
    for (const candidate of sorted) {
      const p = projection.project(candidate.lon, candidate.lat);
      if (!p) continue;
      if (p.x < 0 || p.x > projection.width || p.y < EXCLUDE_TOP_PX || p.y > projection.height - EXCLUDE_BOTTOM_PX) continue;
      const halfW = estimatedWidthPx(candidate) / 2;
      const clear = placed.every((q) =>
        Math.abs(p.x - q.x) >= halfW + q.halfW + RECT_PADDING_PX ||
        Math.abs(p.y - q.y) >= LABEL_HEIGHT_PX + RECT_PADDING_PX,
      );
      if (clear) {
        accepted.push(candidate);
        placed.push({ x: p.x, y: p.y, halfW });
      }
    }
  } else {
    const minSep = BAND_MIN_SEPARATION_DEG[band];
    for (const candidate of sorted) {
      if (accepted.every((placed) => separationDeg(candidate, placed) >= minSep)) accepted.push(candidate);
    }
  }

  const budget = BAND_BUDGET[band];
  if (accepted.length <= budget) return accepted;
  let trimmed = accepted;
  for (let classIndex = CLASS_PRIORITY.length - 1; classIndex >= 0 && trimmed.length > budget; classIndex -= 1) {
    const without = trimmed.filter((entry) => rank(entry) !== classIndex);
    if (without.length > 0 && without.length < trimmed.length) trimmed = without;
  }
  return trimmed.slice(0, budget);
}
