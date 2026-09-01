/**
 * Boot manifest → one real percentage (UX reconstruction 2026-08-31, mission §7–8).
 *
 * Every point of the number corresponds to measured work; nothing advances on a timer.
 * The weights are documented product decisions, not physics:
 *
 *   renderer   5 %  — the Cesium viewer exists (one discrete task; cheap but blocking)
 *   ground    40 %  — the imagery/terrain tile queue's drain against its high-water mark
 *   regional  15 %  — the WHOLE PNW pyramid z5–z9 fetched into the HTTP cache (domain-
 *                     warmer; tiles done / total — the availability guarantee behind
 *                     "no patchwork while scrolling"; near-instant on a warm cache)
 *   data      25 %  — the discrete boot queries, tasks complete / total
 *   live      10 %  — the first hydrologic envelope (optional: an error DEGRADES and
 *                     completes the slice — the world says UNKNOWN elsewhere; the bar must
 *                     never sit at 94 % because one provider is down)
 *   device     5 %  — the renderer's quality measurement (scene/render-quality.ts): ≈45
 *                     forced frames at Cinematic's real cost, run LAST so nothing else
 *                     contends for the frame; instant when a detection from the last day
 *                     is persisted, or when the build pins the probe off
 *
 * 100 % ⇔ SCENE_VISUAL_READY: renderer up, ground composed (sustained-empty queue, not a
 * transient zero), all data tasks settled, live settled-or-degraded, device measured. The
 * veil reveals only at 100 % (plus a brief settle); a hard timeout elsewhere remains the
 * honesty valve.
 *
 * Monotonicity is enforced here: the tile queue legitimately grows (progress would dip as
 * the high-water rises), so the published percentage is clamped to never decrease.
 */

export interface BootState {
  /** The Cesium viewer/controller exists. */
  renderer: boolean;
  /** Tile-queue drain in [0,1] (1 - pending/highWater). May regress at the source. */
  groundProgress: number;
  /** The queue stayed empty for the sustained beat — the opening frame is composed. */
  groundComposed: boolean;
  /** Discrete boot queries settled (success or error), out of dataTasksTotal. */
  dataTasksDone: number;
  dataTasksTotal: number;
  /** The live envelope settled (success) or degraded (error) — both complete the slice. */
  liveSettled: boolean;
  /** Regional-map warm progress: tiles fetched / total (domain-warmer). */
  regionalDone: number;
  regionalTotal: number;
  /** The quality probe resolved (or was skipped: persisted detection / probe pinned off). */
  deviceMeasured: boolean;
}

const WEIGHT_RENDERER = 0.05;
const WEIGHT_GROUND = 0.4;
const WEIGHT_REGIONAL = 0.15;
const WEIGHT_DATA = 0.25;
const WEIGHT_LIVE = 0.1;
const WEIGHT_DEVICE = 0.05;

const clamp01 = (n: number): number => Math.max(0, Math.min(1, n));

/** Raw weighted aggregate in [0,100]. Pure; may regress if groundProgress regresses. */
export function bootPercent(s: BootState): number {
  const renderer = s.renderer ? 1 : 0;
  // Ground counts fully only once COMPOSED — a momentarily-empty queue is not a composed
  // frame, so its slice caps at 96 % until the sustained-zero confirms.
  const ground = s.groundComposed ? 1 : Math.min(clamp01(s.groundProgress), 0.96);
  const data = s.dataTasksTotal > 0 ? clamp01(s.dataTasksDone / s.dataTasksTotal) : 1;
  const live = s.liveSettled ? 1 : 0;
  const regional = s.regionalTotal > 0 ? clamp01(s.regionalDone / s.regionalTotal) : 0;
  const device = s.deviceMeasured ? 1 : 0;
  return (
    100 *
    (WEIGHT_RENDERER * renderer + WEIGHT_GROUND * ground + WEIGHT_REGIONAL * regional + WEIGHT_DATA * data + WEIGHT_LIVE * live + WEIGHT_DEVICE * device)
  );
}

/** SCENE_VISUAL_READY — the definition of done for the opening frame. */
export function sceneVisualReady(s: BootState): boolean {
  return (
    s.renderer &&
    s.groundComposed &&
    s.dataTasksTotal > 0 &&
    s.dataTasksDone >= s.dataTasksTotal &&
    s.regionalTotal > 0 &&
    s.regionalDone >= s.regionalTotal &&
    s.liveSettled &&
    s.deviceMeasured
  );
}

/** Stateful monotonic wrapper: the published percentage never decreases, and only
 * SCENE_VISUAL_READY can publish 100. */
export function createBootProgress() {
  let published = 0;
  return (s: BootState): { percent: number; ready: boolean } => {
    const ready = sceneVisualReady(s);
    const raw = ready ? 100 : Math.min(bootPercent(s), 99);
    published = Math.max(published, raw);
    return { percent: Math.round(published), ready };
  };
}
