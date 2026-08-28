/**
 * Label selection: pure, deterministic mapping from (label set, band, selection) to the
 * labels a frame may show — SEMANTIC_ZOOM §6 made computable. No Cesium, no React.
 *
 * The doctrine's mandatory rules, implemented:
 * - band eligibility: a class outside its band is not a candidate regardless of budget
 *   (orbital shows BASIN names only — "Cascadia orientation", nothing else);
 * - per-band budgets 8/14/18/22/16 (orbital..local);
 * - priority: P2 basin > P3 river > P4 city > P4 town > P5 water > P6 peak, with the
 *   selected basin's own labels first within each class;
 * - spacing: greedy accept with a minimum GROUND separation per band. The doctrine asks for
 *   28 projected pixels; this uses the ground-distance equivalent of ~28 px at each band's
 *   typical camera height (APPROXIMATION, deterministic and camera-free — measured against
 *   real scenes before any tightening);
 * - over budget, the lowest-priority CLASS drops whole, never a random subset.
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

export const BAND_BUDGET: Record<Band, number> = { orbital: 8, state: 14, basin: 18, river: 22, local: 16 };
const BAND_MAX_TIER: Record<Band, number> = { orbital: 0, state: 1, basin: 2, river: 3, local: 4 };
/** ~28 px of ground at each band's typical effective height, in degrees (documented approximation). */
const BAND_MIN_SEPARATION_DEG: Record<Band, number> = { orbital: 0.5, state: 0.22, basin: 0.09, river: 0.03, local: 0.01 };
const CLASS_PRIORITY: readonly LabelKind[] = ['basin', 'river', 'city', 'town', 'water', 'peak'];

function separationDeg(a: LabelEntry, b: LabelEntry): number {
  const latScale = Math.cos(((a.lat + b.lat) / 2) * (Math.PI / 180));
  const dx = (a.lon - b.lon) * latScale;
  const dy = a.lat - b.lat;
  return Math.hypot(dx, dy);
}

export function selectLabels(
  labels: readonly LabelEntry[],
  band: Band,
  selectedBasinId: string | null,
): LabelEntry[] {
  const eligible = labels.filter((entry) =>
    band === 'orbital' ? entry.kind === 'basin' : entry.tier <= BAND_MAX_TIER[band],
  );
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
  const minSep = BAND_MIN_SEPARATION_DEG[band];
  for (const candidate of sorted) {
    if (accepted.every((placed) => separationDeg(candidate, placed) >= minSep)) {
      accepted.push(candidate);
    }
  }

  const budget = BAND_BUDGET[band];
  if (accepted.length <= budget) return accepted;
  // Drop the lowest-priority class whole until inside budget; if one class alone still
  // overflows, truncate within it by the sort order (deterministic, never random).
  let trimmed = accepted;
  for (let classIndex = CLASS_PRIORITY.length - 1; classIndex >= 0 && trimmed.length > budget; classIndex -= 1) {
    const without = trimmed.filter((entry) => rank(entry) !== classIndex);
    if (without.length > 0) trimmed = without.length >= trimmed.length ? trimmed : without;
  }
  return trimmed.slice(0, budget);
}
