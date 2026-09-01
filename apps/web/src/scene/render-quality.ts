/**
 * render-quality.ts — the Cesium-facing half of the quality system (quality.ts is the pure
 * half). Three things, each a plain function over a Scene/Viewer:
 *
 *   applyTierBudget   the five viewer knobs a tier owns: backing-store resolution, MSAA,
 *                     tile cache, render-loop cap (PERFORMANCE.md §3);
 *   probeRenderCost   the auto-detect measurement — forced frames at Cinematic's real cost
 *                     with a GPU timer query where the browser offers one, CPU render time
 *                     and frame arrival everywhere. Frames with tiles still uploading are
 *                     not counted (uploads are not steady-state cost). Under explicit
 *                     rendering the probe requests its own frames;
 *   watchGestureFrames the runtime monitor: rendered-frame deltas across one wheel/drag
 *                     window. Cesium's FrameRateMonitor is deliberately NOT used — under
 *                     requestRenderMode an idle scene renders nothing, which it would read
 *                     as 0 fps and downgrade a perfectly healthy machine.
 */
import type { Scene, Viewer } from 'cesium';
import { TIER_BUDGET, percentile, resolutionScaleFor, type GestureWindow, type ProbeSample, type QualityTier } from './quality';

/** Frames discarded after the resolution switch while framebuffers and tiles re-settle. */
const PROBE_WARMUP_FRAMES = 8;
/** Counted frames for a full verdict. Fewer than the perf doc's 90 on purpose: the probe
 * runs at native resolution under the veil, and on a weak machine 90 slow frames would
 * add seconds to the boot; 45 frames plus the early exit below classify just as well. */
const PROBE_FRAMES = 45;
/** After this many counted frames a clearly slow machine is classified without waiting. */
const PROBE_EARLY_EXIT_FRAMES = 20;
const PROBE_EARLY_EXIT_P50_MS = 34;
const PROBE_TIMEOUT_MS = 6_000;
/** How long to wait for the last GPU timer results after the final counted frame. */
const TIMER_HARVEST_MS = 400;

/** A gesture window closes this long after the last wheel/drag activity. */
const GESTURE_WINDOW_IDLE_MS = 400;
const MIN_WINDOW_FRAMES = 12;
/** A delta longer than this is a pause between renders, not a slow frame (explicit rendering). */
const RENDER_GAP_MS = 150;

interface DisjointTimerQueryExt {
  TIME_ELAPSED_EXT: number;
  GPU_DISJOINT_EXT: number;
}

interface GpuTimer {
  begin(): void;
  end(): void;
  /** Move every finished query into `into` (ms); disjoint frames are dropped. */
  harvest(into: number[]): void;
  dispose(): void;
}

function createGpuTimer(canvas: HTMLCanvasElement): GpuTimer | null {
  // The canvas already holds Cesium's WebGL2 context; getContext returns that same object.
  const gl = canvas.getContext('webgl2');
  if (!gl) return null;
  const ext: DisjointTimerQueryExt | null = gl.getExtension('EXT_disjoint_timer_query_webgl2');
  if (!ext) return null;
  let active: WebGLQuery | null = null;
  let pending: WebGLQuery[] = [];
  let broken = false;
  return {
    begin() {
      if (broken || active) return;
      const query = gl.createQuery();
      if (!query) return;
      try {
        gl.beginQuery(ext.TIME_ELAPSED_EXT, query);
        active = query;
      } catch {
        gl.deleteQuery(query);
        broken = true; // another query was already active: the timer path is not ours to use
      }
    },
    end() {
      if (!active) return;
      try {
        gl.endQuery(ext.TIME_ELAPSED_EXT);
        pending.push(active);
      } catch {
        gl.deleteQuery(active);
      }
      active = null;
    },
    harvest(into) {
      const disjoint = Boolean(gl.getParameter(ext.GPU_DISJOINT_EXT));
      const remaining: WebGLQuery[] = [];
      for (const query of pending) {
        const available = Boolean(gl.getQueryParameter(query, gl.QUERY_RESULT_AVAILABLE));
        if (!available) {
          remaining.push(query);
          continue;
        }
        const nanoseconds = Number(gl.getQueryParameter(query, gl.QUERY_RESULT));
        if (!disjoint && Number.isFinite(nanoseconds)) into.push(nanoseconds / 1e6);
        gl.deleteQuery(query);
      }
      pending = remaining;
    },
    dispose() {
      if (active) {
        try { gl.endQuery(ext.TIME_ELAPSED_EXT); } catch { /* nothing to end */ }
        gl.deleteQuery(active);
        active = null;
      }
      pending.forEach((query) => gl.deleteQuery(query));
      pending = [];
    },
  };
}

/** Sets the viewer to the tier's budget. Idempotent; safe to call on every resize. */
export function applyTierBudget(viewer: Viewer, tier: QualityTier): void {
  const budget = TIER_BUDGET[tier];
  const canvas = viewer.scene.canvas;
  viewer.useBrowserRecommendedResolution = !budget.nativeResolution;
  viewer.resolutionScale = resolutionScaleFor(tier, canvas.clientWidth, canvas.clientHeight);
  viewer.scene.msaaSamples = budget.msaaSamples;
  viewer.scene.globe.tileCacheSize = budget.tileCacheSize;
  // Cesium clears the cap with undefined (its setter says so); the typing omits that, so the
  // assignment goes through the widget's real contract rather than a cast to a number.
  const loop: { targetFrameRate: number | undefined } = viewer;
  loop.targetFrameRate = budget.targetFrameRate;
  viewer.scene.requestRender();
}

/**
 * Measures the renderer at its CURRENT settings (the caller sets Cinematic's budget first).
 * Resolves null when too few frames could be counted (hidden tab, dead renderer).
 */
export function probeRenderCost(scene: Scene): Promise<ProbeSample | null> {
  return new Promise((resolve) => {
    const timer = createGpuTimer(scene.canvas);
    const cpu: number[] = [];
    const deltas: number[] = [];
    const gpu: number[] = [];
    let preAt = Number.NaN;
    let lastPost = Number.NaN;
    let seen = 0;
    let done = false;
    let raf = 0;
    let timeout = 0;

    const finish = () => {
      if (done) return;
      done = true;
      scene.preRender.removeEventListener(onPre);
      scene.postRender.removeEventListener(onPost);
      window.cancelAnimationFrame(raf);
      window.clearTimeout(timeout);
      const settle = () => {
        timer?.harvest(gpu);
        timer?.dispose();
        const frames = deltas.length;
        resolve(frames === 0 ? null : {
          gpuMsP50: gpu.length >= Math.min(PROBE_EARLY_EXIT_FRAMES, frames) ? percentile(gpu, 0.5) : null,
          cpuMsP50: percentile(cpu, 0.5),
          frameDeltaP95Ms: percentile(deltas, 0.95),
          frames,
        });
      };
      window.setTimeout(settle, timer ? TIMER_HARVEST_MS : 0);
    };
    const onPre = () => {
      preAt = performance.now();
      timer?.begin();
    };
    const onPost = () => {
      const now = performance.now();
      timer?.end();
      timer?.harvest(gpu);
      const uploading = scene.globe ? !scene.globe.tilesLoaded : false;
      if (uploading || seen < PROBE_WARMUP_FRAMES) {
        if (!uploading) seen += 1;
        lastPost = now;
        preAt = Number.NaN;
        return;
      }
      if (!Number.isNaN(preAt)) cpu.push(now - preAt);
      if (!Number.isNaN(lastPost)) deltas.push(now - lastPost);
      lastPost = now;
      preAt = Number.NaN;
      seen += 1;
      const counted = deltas.length;
      if (counted >= PROBE_FRAMES) finish();
      else if (counted >= PROBE_EARLY_EXIT_FRAMES && percentile(deltas, 0.5) > PROBE_EARLY_EXIT_P50_MS) finish();
    };
    const pump = () => {
      if (done) return;
      scene.requestRender();
      raf = window.requestAnimationFrame(pump);
    };
    scene.preRender.addEventListener(onPre);
    scene.postRender.addEventListener(onPost);
    timeout = window.setTimeout(finish, PROBE_TIMEOUT_MS);
    pump();
  });
}

/**
 * Reports one GestureWindow per wheel/drag gesture (deltas between RENDERED frames while the
 * hand is on the map). Returns a disposer.
 */
export function watchGestureFrames(scene: Scene, canvas: HTMLElement, onWindow: (window: GestureWindow) => void): () => void {
  let deltas: number[] = [];
  let last = Number.NaN;
  let active = false;
  let idle: number | null = null;
  const onPost = () => {
    if (!active) return;
    const now = performance.now();
    if (!Number.isNaN(last)) {
      const delta = now - last;
      if (delta <= RENDER_GAP_MS) deltas.push(delta);
    }
    last = now;
  };
  const close = () => {
    idle = null;
    active = false;
    if (deltas.length >= MIN_WINDOW_FRAMES) onWindow({ p95Ms: percentile(deltas, 0.95), frames: deltas.length });
    deltas = [];
    last = Number.NaN;
  };
  const activity = () => {
    if (!active) {
      active = true;
      deltas = [];
      last = Number.NaN;
    }
    if (idle !== null) window.clearTimeout(idle);
    idle = window.setTimeout(close, GESTURE_WINDOW_IDLE_MS);
  };
  const onPointerMove = (event: PointerEvent) => {
    if (event.buttons > 0) activity();
  };
  scene.postRender.addEventListener(onPost);
  canvas.addEventListener('wheel', activity, { passive: true });
  canvas.addEventListener('pointerdown', activity);
  canvas.addEventListener('pointermove', onPointerMove);
  return () => {
    scene.postRender.removeEventListener(onPost);
    canvas.removeEventListener('wheel', activity);
    canvas.removeEventListener('pointerdown', activity);
    canvas.removeEventListener('pointermove', onPointerMove);
    if (idle !== null) window.clearTimeout(idle);
  };
}
