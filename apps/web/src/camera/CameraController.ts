/**
 * CameraController: owns every programmatic camera move. Initial view over Cascadia, basin
 * framing from a bbox, forecast-point framing, distance-based durations (flight-math.ts) with
 * the minimum-jerk profile, interruption on user input, and the reduced-motion path (veil →
 * instant setView → veil out, opacity only). Emits started/settled/interrupted; publishes
 * throttled CameraSamples for the SemanticZoomController. React never touches this class.
 */
import { BoundingSphere, Cartesian3, Cartographic, HeadingPitchRange, Math as CesiumMath, Matrix4, PerspectiveFrustum, Rectangle, type Viewer } from 'cesium';
import { MOTION, minimumJerk, type MotionPreference } from '../design-system/motion';
import type { CameraSample } from '../scene/SemanticZoomController';
import { ZOOM_CEILING_M } from './envelope';
import { cappedArcApexM, computeFlightDuration, defaultArcApexM, framingRange } from './flight-math';
import type { Bbox, CameraEvents, FlightHandle, FlightOptions, FlightResult, InterruptReason } from './types';

// Top-down intelligence camera (owner 2026-09-01: "just make it a top down view, no
// angles"): every framing is pure nadir; the tilt gesture is disabled outright.
export const CASCADIA_VIEW = { lon: -122.3, lat: 47.6, rangeM: 1_150_000, pitchDeg: -90, headingDeg: 0 } as const;
export const BASIN_FRAMING = { pitchDeg: -90, paddingFactor: 1.1 } as const;
export const FORECAST_POINT_FRAMING = { rangeM: 12_000, pitchDeg: -90 } as const; // owner 2026-09-01: top down, no angles — anywhere
const SAMPLE_MIN_INTERVAL_MS = 100;

type Listener<E extends keyof CameraEvents> = (event: CameraEvents[E]) => void;

export class CameraController {
  private motion: MotionPreference;
  private flightSeq = 0;
  private active: { id: string; cancel: () => void } | null = null;
  private readonly listeners: { [E in keyof CameraEvents]: Set<Listener<E>> } = { started: new Set(), settled: new Set(), interrupted: new Set() };
  private readonly sampleListeners = new Set<(sample: CameraSample) => void>();
  private lastSampleAt = 0;
  private readonly veil: HTMLDivElement;
  /** The scene container (the same element SceneController stamps data-tiles-pending on):
   * flights write `data-flight-max-height` here so a spec can log the apex — imperative DOM,
   * written only when the running maximum rises, never per frame into React. */
  private readonly container: HTMLElement;
  private readonly removeDomListeners: () => void;
  private readonly removeCameraListeners: () => void;

  constructor(private readonly viewer: Viewer, container: HTMLElement, motion: MotionPreference) {
    this.motion = motion;
    this.container = container;
    this.veil = document.createElement('div');
    this.veil.className = 'scene-veil';
    this.veil.setAttribute('aria-hidden', 'true');
    container.appendChild(this.veil);

    const onUserInput = () => { if (this.active) this.interrupt('user-input'); };
    const canvas = viewer.scene.canvas;
    canvas.addEventListener('pointerdown', onUserInput);
    canvas.addEventListener('wheel', onUserInput, { passive: true });
    canvas.addEventListener('keydown', onUserInput);
    this.removeDomListeners = () => {
      canvas.removeEventListener('pointerdown', onUserInput);
      canvas.removeEventListener('wheel', onUserInput);
      canvas.removeEventListener('keydown', onUserInput);
      this.veil.remove();
    };

    viewer.camera.percentageChanged = 0.05;
    const onChanged = () => this.publishSample(false);
    const onMoveEnd = () => this.publishSample(true);
    viewer.camera.changed.addEventListener(onChanged);
    viewer.camera.moveEnd.addEventListener(onMoveEnd);
    this.removeCameraListeners = () => {
      viewer.camera.changed.removeEventListener(onChanged);
      viewer.camera.moveEnd.removeEventListener(onMoveEnd);
    };
  }

  on<E extends keyof CameraEvents>(event: E, handler: Listener<E>): () => void {
    this.listeners[event].add(handler);
    return () => this.listeners[event].delete(handler);
  }

  onSample(handler: (sample: CameraSample) => void): () => void {
    this.sampleListeners.add(handler);
    return () => this.sampleListeners.delete(handler);
  }

  setMotionPreference(motion: MotionPreference): void {
    if (motion === this.motion) return;
    this.motion = motion;
    if (this.active) this.interrupt('reduced-motion-change');
  }

  get motionPreference(): MotionPreference { return this.motion; }

  /** True while a programmatic flight is in progress — the envelope must not spring back
   * against a flight that is already going somewhere deliberate. */
  get flightActive(): boolean { return this.active !== null; }

  /** Initial view: Cascadia near-nadir at ~1,150 km — the domain fills the frame. Always a cut (first frame is the final frame). */
  setInitialView(): void {
    this.cutTo(Cartesian3.fromDegrees(CASCADIA_VIEW.lon, CASCADIA_VIEW.lat), new HeadingPitchRange(CesiumMath.toRadians(CASCADIA_VIEW.headingDeg), CesiumMath.toRadians(CASCADIA_VIEW.pitchDeg), CASCADIA_VIEW.rangeM));
    this.publishSample(true, true);
  }

  flyToBasin(bbox: Bbox, options: FlightOptions): FlightHandle {
    const [west, south, east, north] = bbox;
    const sphere = BoundingSphere.fromRectangle3D(Rectangle.fromDegrees(west, south, east, north));
    const pitch = options.pitchDeg ?? BASIN_FRAMING.pitchDeg;
    const range = framingRange(sphere.radius, this.narrowestHalfAngle(), BASIN_FRAMING.paddingFactor);
    return this.fly(sphere, new HeadingPitchRange(CesiumMath.toRadians(options.headingDeg ?? 0), CesiumMath.toRadians(pitch), range), options);
  }

  frameForecastPoint(lon: number, lat: number, options: FlightOptions): FlightHandle {
    const sphere = new BoundingSphere(Cartesian3.fromDegrees(lon, lat), 1);
    const pitch = options.pitchDeg ?? FORECAST_POINT_FRAMING.pitchDeg;
    return this.fly(sphere, new HeadingPitchRange(CesiumMath.toRadians(options.headingDeg ?? 0), CesiumMath.toRadians(pitch), FORECAST_POINT_FRAMING.rangeM), options);
  }

  interrupt(reason: InterruptReason): void {
    const active = this.active;
    if (!active) return;
    this.active = null;
    active.cancel();
    this.emit('interrupted', { flightId: active.id, reason });
  }

  sample(): CameraSample {
    const carto = this.viewer.camera.positionCartographic;
    return { heightAboveTerrainM: carto.height, approximate: true, pitchDeg: CesiumMath.toDegrees(this.viewer.camera.pitch), settled: this.active === null };
  }

  dispose(): void {
    this.interrupt('dispose');
    this.removeDomListeners();
    this.removeCameraListeners();
    (Object.keys(this.listeners) as (keyof CameraEvents)[]).forEach((k) => this.listeners[k].clear());
    this.sampleListeners.clear();
  }

  private fly(sphere: BoundingSphere, offset: HeadingPitchRange, options: FlightOptions): FlightHandle {
    if (this.active) this.interrupt('superseded');
    const id = `flight-${++this.flightSeq}`;
    const cut = options.cut === true || this.motion === 'reduced';

    if (cut) {
      this.emit('started', { flightId: id, durationMs: 0, cut: true, reason: options.reason });
      this.veil.classList.add('is-on');
      this.cutTo(sphere.center, offset);
      this.container.dataset.flightMaxHeight = String(Math.round(this.viewer.camera.positionCartographic.height));
      this.publishSample(true, true);
      this.emit('settled', { flightId: id, cut: true });
      window.setTimeout(() => this.veil.classList.remove('is-on'), MOTION.duration.micro);
      return { id, settled: Promise.resolve({ outcome: 'settled', band: 'orbital', cut: true } satisfies FlightResult), interrupt: () => {} };
    }

    const camera = this.viewer.camera;
    const from = camera.positionCartographic;
    const to = Cartographic.fromCartesian(sphere.center);
    const distance = Cartesian3.distance(Cartesian3.fromRadians(from.longitude, from.latitude), sphere.center);
    const durationMs = computeFlightDuration(distance, Math.abs(from.height - (offset.range ?? 0)), 1);
    let resolveSettled: (r: FlightResult) => void = () => {};
    const settled = new Promise<FlightResult>((resolve) => { resolveSettled = resolve; });

    // Flight apex cap (plan row 3 / step 1.7): a basin→basin arc must never rise above the
    // composed home frame, where the discard boundary and vignette edge flash into view.
    // `maximumHeight` passes straight through flyToBoundingSphere (Camera.js:3756) into
    // CameraFlightPath, where it is the apex itself — so reproduce Cesium's default apex
    // (flight-math.ts) and clamp it to the envelope ceiling rather than hand over the ceiling.
    // Every framing is nadir, so the destination sits `range` straight above the centre.
    const end = Cartesian3.fromRadians(to.longitude, to.latitude, to.height + offset.range);
    const diff = Cartesian3.subtract(camera.position, end, new Cartesian3());
    const frustum = camera.frustum;
    const perspective = frustum instanceof PerspectiveFrustum && frustum.fovy !== undefined && frustum.aspectRatio !== undefined
      ? { fovyRad: frustum.fovy, aspectRatio: frustum.aspectRatio }
      : null;
    const maximumHeight = cappedArcApexM(
      // Cesium's order: the UP component first, the RIGHT component second (flight-math.ts).
      defaultArcApexM(Math.abs(Cartesian3.dot(diff, camera.up)), Math.abs(Cartesian3.dot(diff, camera.right)), perspective),
      ZOOM_CEILING_M,
    );

    // Apex log for tests/tooling: the running maximum of positionCartographic.height over the
    // flight, sampled from preRender and written to the container only when it rises.
    let maxHeight = from.height;
    this.container.dataset.flightMaxHeight = String(Math.round(maxHeight));
    const scene = this.viewer.scene;
    const trackApex = () => {
      const h = camera.positionCartographic.height;
      if (h <= maxHeight) return;
      maxHeight = h;
      this.container.dataset.flightMaxHeight = String(Math.round(maxHeight));
    };
    scene.preRender.addEventListener(trackApex);
    const stopTracking = () => scene.preRender.removeEventListener(trackApex);

    this.active = {
      id,
      cancel: () => {
        stopTracking();
        camera.cancelFlight();
        resolveSettled({ outcome: 'interrupted', band: 'orbital', cut: false });
      },
    };
    this.emit('started', { flightId: id, durationMs, cut: false, reason: options.reason });
    camera.flyToBoundingSphere(sphere, {
      offset,
      duration: durationMs / 1000,
      easingFunction: minimumJerk,
      maximumHeight,
      complete: () => {
        if (this.active?.id !== id) return;
        stopTracking();
        trackApex();
        this.active = null;
        this.publishSample(true, true);
        this.emit('settled', { flightId: id, cut: false });
        resolveSettled({ outcome: 'settled', band: 'orbital', cut: false });
      },
      cancel: () => {
        if (this.active?.id !== id) return;
        stopTracking();
        this.active = null;
        this.emit('interrupted', { flightId: id, reason: 'user-input' });
        resolveSettled({ outcome: 'interrupted', band: 'orbital', cut: false });
      },
    });
    return { id, settled, interrupt: (reason = 'superseded') => { if (this.active?.id === id) this.interrupt(reason); } };
  }

  private cutTo(center: Cartesian3, offset: HeadingPitchRange): void {
    this.viewer.camera.lookAt(center, offset);
    this.viewer.camera.lookAtTransform(Matrix4.IDENTITY);
    this.viewer.scene.requestRender();
  }

  private narrowestHalfAngle(): number {
    const frustum = this.viewer.camera.frustum;
    if (frustum instanceof PerspectiveFrustum) return Math.min(frustum.fov ?? Math.PI / 3, frustum.fovy ?? Math.PI / 3) / 2;
    return Math.PI / 6;
  }

  private publishSample(settled: boolean, force = false): void {
    const now = performance.now();
    if (!settled && !force && now - this.lastSampleAt < SAMPLE_MIN_INTERVAL_MS) return;
    this.lastSampleAt = now;
    const sample = { ...this.sample(), settled };
    this.sampleListeners.forEach((h) => h(sample));
  }

  private emit<E extends keyof CameraEvents>(event: E, payload: CameraEvents[E]): void {
    this.listeners[event].forEach((h) => h(payload));
  }
}
