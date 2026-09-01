/**
 * TransitionPlate — tiles appear ALL AT ONCE, smoothly (owner 2026-09-01; mission §2–3's
 * composition layer, implemented within the renderer's real limits).
 *
 * Cesium refines tile-by-tile and cannot fade tiles (verified: no such API in 1.144).
 * So the COMPOSITION layer lives above it: the moment a zoom gesture or flight ends with
 * tiles left to load, the CURRENT frame is copied onto a 2D overlay canvas — pixel-equal
 * to what the user already sees, so the hold is invisible. The real scene refines
 * UNDERNEATH the plate; when the tile queue stays empty for a beat, the plate fades out
 * in one crossfade and the crisp scene appears as a single event. A new gesture drops the
 * plate instantly — the live world always wins under the user's hand.
 *
 * Requires preserveDrawingBuffer (already set for deep-link captures). One canvas copy
 * per transition, no per-frame cost while idle. React never touches this class.
 */
import type { Viewer } from 'cesium';

const GESTURE_IDLE_MS = 220;
const PENDING_WORTH_HOLDING = 4;
const SETTLE_SUSTAIN_MS = 250;
const FADE_MS = 320;
const MAX_HOLD_MS = 8_000; // honesty valve: never hold a stale frame forever

export class TransitionPlate {
  private readonly plate: HTMLCanvasElement;
  private readonly viewer: Viewer;
  private pending = 0;
  private idleTimer: number | null = null;
  private settleTimer: number | null = null;
  private holdTimer: number | null = null;
  private holding = false;
  private lastGestureAt = 0;
  private readonly disposers: (() => void)[] = [];

  constructor(viewer: Viewer, container: HTMLElement) {
    this.viewer = viewer;
    this.plate = document.createElement('canvas');
    this.plate.className = 'transition-plate';
    this.plate.setAttribute('aria-hidden', 'true');
    container.appendChild(this.plate);

    const onProgress = (pending: number) => {
      this.pending = pending;
      // Loads ramp up a few frames AFTER a gesture ends — the hold arms on the RISE,
      // whenever the user's hand is off (the captured frame is whatever is on screen at
      // that instant, so the hold is seamless by construction).
      if (!this.holding && pending >= PENDING_WORTH_HOLDING && performance.now() - this.lastGestureAt > GESTURE_IDLE_MS) {
        this.maybeHold();
      }
      if (this.holding && pending === 0 && this.settleTimer === null) {
        this.settleTimer = window.setTimeout(() => {
          this.settleTimer = null;
          if (this.pending === 0) this.release();
        }, SETTLE_SUSTAIN_MS);
      }
      if (this.holding && pending > 0 && this.settleTimer !== null) {
        window.clearTimeout(this.settleTimer);
        this.settleTimer = null;
      }
    };
    viewer.scene.globe.tileLoadProgressEvent.addEventListener(onProgress);
    this.disposers.push(() => viewer.scene.globe.tileLoadProgressEvent.removeEventListener(onProgress));

    // A gesture in progress = live world, never a plate. On gesture end, arm the hold.
    const canvas = viewer.scene.canvas;
    const onGestureActivity = () => {
      this.lastGestureAt = performance.now();
      this.drop();
      if (this.idleTimer !== null) window.clearTimeout(this.idleTimer);
      this.idleTimer = window.setTimeout(() => {
        this.idleTimer = null;
        this.maybeHold();
      }, GESTURE_IDLE_MS);
    };
    canvas.addEventListener('wheel', onGestureActivity, { passive: true });
    canvas.addEventListener('pointerdown', onGestureActivity);
    canvas.addEventListener('pointerup', onGestureActivity);
    this.disposers.push(() => {
      canvas.removeEventListener('wheel', onGestureActivity);
      canvas.removeEventListener('pointerdown', onGestureActivity);
      canvas.removeEventListener('pointerup', onGestureActivity);
    });
  }

  /** Programmatic flights call this on settle (SceneController wires it). */
  onFlightSettled(): void {
    this.maybeHold();
  }

  /** Capture and hold the CURRENT frame unconditionally — used at gesture-end BEFORE the
   * detail threshold restores, so the coarse→sharp reload happens entirely under the
   * plate and reveals as one crossfade. If nothing ends up loading, the settle path
   * releases within a beat. */
  holdNow(): void {
    this.capture(true);
  }

  dispose(): void {
    this.drop();
    this.disposers.forEach((d) => d());
    this.plate.remove();
  }

  private maybeHold(): void {
    this.capture(false);
  }

  private capture(force: boolean): void {
    if (this.holding) return;
    if (!force && this.pending < PENDING_WORTH_HOLDING) return; // nearly loaded: nothing worth hiding
    const source = this.viewer.scene.canvas;
    if (source.width === 0 || source.height === 0) return;
    this.plate.width = source.width;
    this.plate.height = source.height;
    const ctx = this.plate.getContext('2d');
    if (!ctx) return;
    try {
      ctx.drawImage(source, 0, 0);
    } catch {
      return; // a failed copy must never freeze a wrong frame
    }
    this.plate.style.transition = 'none';
    this.plate.style.opacity = '1';
    this.plate.style.display = 'block';
    this.holding = true;
    this.holdTimer = window.setTimeout(() => this.release(), MAX_HOLD_MS);
    // a forced hold with an empty queue must still release promptly if nothing loads
    if (this.pending === 0 && this.settleTimer === null) {
      this.settleTimer = window.setTimeout(() => {
        this.settleTimer = null;
        if (this.pending === 0) this.release();
      }, SETTLE_SUSTAIN_MS * 2);
    }
  }

  /** One crossfade: the crisp scene appears as a single event. */
  private release(): void {
    if (!this.holding) return;
    this.holding = false;
    if (this.holdTimer !== null) { window.clearTimeout(this.holdTimer); this.holdTimer = null; }
    this.plate.style.transition = `opacity ${FADE_MS}ms ease`;
    this.plate.style.opacity = '0';
    window.setTimeout(() => {
      if (!this.holding) this.plate.style.display = 'none';
    }, FADE_MS + 40);
  }

  /** Instant removal — the live world always wins under the user's hand. */
  private drop(): void {
    if (this.settleTimer !== null) { window.clearTimeout(this.settleTimer); this.settleTimer = null; }
    if (this.holdTimer !== null) { window.clearTimeout(this.holdTimer); this.holdTimer = null; }
    this.holding = false;
    this.plate.style.transition = 'none';
    this.plate.style.opacity = '0';
    this.plate.style.display = 'none';
  }
}
