/**
 * quality.ts — the renderer's quality vocabulary, pure and unit-testable (no Cesium types).
 *
 * Four internal tiers (docs/PERFORMANCE.md §3; budgets from
 * docs/research/cesium-cinematic-performance-2026-09-01.md §6) surface as TWO product
 * experiences (owner 2026-09-01: "the user chooses a stripped down version or full
 * version"): Essential = the BALANCED/LOW budgets, Cinematic = HIGH/ULTRA.
 *
 *   auto-detect  a measured render probe at Cinematic's real cost (native backing store,
 *                MSAA 4) classifies the machine once the ground has composed;
 *   the switch   Settings overrides the detection two ways, never four;
 *   the monitor  a gesture window that misses the tier's frame floor three times in a row
 *                steps one tier down — inside the user's chosen experience only. An
 *                explicit Cinematic never silently becomes Essential.
 *
 * No tier changes WHAT is true on the map; only how much rendering is spent depicting it.
 */
export type QualityTier = 'ultra' | 'high' | 'balanced' | 'low';
export type Experience = 'essential' | 'cinematic';
export type ExperienceChoice = 'auto' | Experience;

export interface TierBudget {
  /** Render at the device pixel ratio (Cinematic) or at CSS pixels (Essential). */
  nativeResolution: boolean;
  /** Backing-store area cap in megapixels for CSS-resolution tiers; Infinity for native tiers. */
  backingStoreCapMP: number;
  msaaSamples: number;
  tileCacheSize: number;
  /** Render-loop cap in frames per second; undefined = uncapped. */
  targetFrameRate: number | undefined;
  /** Gesture-window frame-time floor (p95, ms): 1.5× the tier's documented p95 budget. Beyond it the tier is over budget. */
  frameFloorMs: number;
}

export const TIER_BUDGET: Record<QualityTier, TierBudget> = {
  ultra: { nativeResolution: true, backingStoreCapMP: Infinity, msaaSamples: 4, tileCacheSize: 800, targetFrameRate: undefined, frameFloorMs: 25 },
  high: { nativeResolution: true, backingStoreCapMP: Infinity, msaaSamples: 4, tileCacheSize: 600, targetFrameRate: undefined, frameFloorMs: 25 },
  balanced: { nativeResolution: false, backingStoreCapMP: 2.1, msaaSamples: 1, tileCacheSize: 400, targetFrameRate: undefined, frameFloorMs: 50 },
  low: { nativeResolution: false, backingStoreCapMP: 1.2, msaaSamples: 1, tileCacheSize: 200, targetFrameRate: 30, frameFloorMs: Infinity },
};

export const TIER_LADDER: readonly QualityTier[] = ['ultra', 'high', 'balanced', 'low'];
/** Consecutive over-budget gesture windows before a tier steps down. */
export const DOWNGRADE_MISSES = 3;
export const EXPERIENCE_STORAGE_KEY = 'cascadia.experience';

const MIN_RESOLUTION_SCALE = 0.35;

export function stepDown(tier: QualityTier): QualityTier {
  const index = TIER_LADDER.indexOf(tier);
  return TIER_LADDER[Math.min(index + 1, TIER_LADDER.length - 1)] ?? tier;
}

export function experienceOf(tier: QualityTier): Experience {
  return tier === 'ultra' || tier === 'high' ? 'cinematic' : 'essential';
}

export const EXPERIENCE_LABEL: Record<Experience, string> = { essential: 'Essential', cinematic: 'Cinematic' };

/**
 * The effective tier: the detection decides inside the experience, the choice decides the
 * experience. Undetected auto is BALANCED — the measured-safe default, never a guess upward.
 */
export function resolveTier(choice: ExperienceChoice, detected: QualityTier | null): QualityTier {
  if (choice === 'essential') return detected === 'low' ? 'low' : 'balanced';
  if (choice === 'cinematic') return detected === 'ultra' ? 'ultra' : 'high';
  return detected ?? 'balanced';
}

/**
 * Cesium composes the backing store as css × (native ? devicePixelRatio : 1) × resolutionScale.
 * Native tiers render every device pixel. CSS-resolution tiers scale down only when the
 * CSS area itself exceeds the tier's megapixel cap (a 4K monitor at 1×), never below 0.35.
 */
export function resolutionScaleFor(tier: QualityTier, cssWidth: number, cssHeight: number): number {
  const budget = TIER_BUDGET[tier];
  if (budget.nativeResolution) return 1;
  const areaMP = (Math.max(1, cssWidth) * Math.max(1, cssHeight)) / 1e6;
  if (areaMP <= budget.backingStoreCapMP) return 1;
  const scale = Math.sqrt(budget.backingStoreCapMP / areaMP);
  return Math.max(MIN_RESOLUTION_SCALE, Math.round(scale * 100) / 100);
}

export interface ProbeSample {
  /** GPU time per frame (timer query), p50 ms; null where the extension is unavailable. */
  gpuMsP50: number | null;
  /** CPU time spent inside the renderer's frame (preRender → postRender), p50 ms. */
  cpuMsP50: number;
  /** Wall time between rendered frames, p95 ms. */
  frameDeltaP95Ms: number;
  frames: number;
}

/** Fewer counted frames than this and the probe is inconclusive — auto stays BALANCED. */
export const PROBE_MIN_FRAMES = 20;

/**
 * Classification (perf research §6): GPU p50 ≤ 5 ms → ULTRA-capable, ≤ 9 → HIGH, ≤ 16 →
 * BALANCED, else LOW. The frame-delta p95 measured in the same window caps the answer —
 * a machine whose frames arrive late is not Cinematic whatever its GPU timer says — and is
 * the whole answer where no timer query exists (≤ 17 → HIGH, ≤ 34 → BALANCED, else LOW).
 */
export function classifyProbe(sample: ProbeSample): QualityTier | null {
  if (sample.frames < PROBE_MIN_FRAMES) return null;
  const byDelta: QualityTier = sample.frameDeltaP95Ms <= 17 ? 'high' : sample.frameDeltaP95Ms <= 34 ? 'balanced' : 'low';
  if (sample.gpuMsP50 === null) return byDelta;
  const byGpu: QualityTier = sample.gpuMsP50 <= 5 ? 'ultra' : sample.gpuMsP50 <= 9 ? 'high' : sample.gpuMsP50 <= 16 ? 'balanced' : 'low';
  // a timer that says ULTRA is believed only when frames also arrive on time
  if (byGpu === 'ultra') return sample.frameDeltaP95Ms <= 17 ? 'ultra' : byDelta;
  return lowerOf(byGpu, byDelta);
}

export function lowerOf(a: QualityTier, b: QualityTier): QualityTier {
  return TIER_LADDER.indexOf(a) >= TIER_LADDER.indexOf(b) ? a : b;
}

/** Nearest-rank percentile on a copy; 0 for an empty list. */
export function percentile(values: readonly number[], p: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((x, y) => x - y);
  const rank = Math.min(sorted.length - 1, Math.max(0, Math.ceil(p * sorted.length) - 1));
  return sorted[rank] ?? 0;
}

export interface GestureWindow {
  p95Ms: number;
  frames: number;
}

/**
 * The monitor's ladder step: after DOWNGRADE_MISSES consecutive over-floor windows the
 * detection steps down one tier — but only if that changes what the user's choice
 * resolves to. Returns the new detection, or null when nothing should change.
 */
export function downgradeAfterWindow(
  window: GestureWindow,
  missStreak: number,
  choice: ExperienceChoice,
  detected: QualityTier | null,
  effective: QualityTier,
): { detected: QualityTier; missStreak: number } | { detected: null; missStreak: number } {
  const overBudget = window.p95Ms > TIER_BUDGET[effective].frameFloorMs;
  const streak = overBudget ? missStreak + 1 : 0;
  if (streak < DOWNGRADE_MISSES) return { detected: null, missStreak: streak };
  const next = stepDown(detected ?? effective);
  if (resolveTier(choice, next) === effective) return { detected: null, missStreak: 0 }; // the ladder is exhausted inside this choice
  return { detected: next, missStreak: 0 };
}

export function parseExperienceChoice(raw: unknown): ExperienceChoice {
  return raw === 'essential' || raw === 'cinematic' ? raw : 'auto';
}
