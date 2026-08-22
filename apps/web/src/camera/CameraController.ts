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
import { computeFlightDuration, framingRange } from './flight-math';
import type { Bbox, CameraEvents, FlightHandle, FlightOptions, FlightResult, InterruptReason } from './types';

export const CASCADIA_VIEW = { lon: -122.3, lat: 47.6, rangeM: 1_500_000, pitchDeg: -55, headingDeg: 0 } as const;
export const BASIN_FRAMING = { pitchDeg: -60, paddingFactor: 1.1 } as const;
export const FORECAST_POINT_FRAMING = { rangeM: 12_000, pitchDeg: -45 } as const;
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
  private readonly removeDomListeners: () => void;
  private readonly removeCameraListeners: () => void;

  constructor(private readonly viewer: Viewer, container: HTMLElement, motion: MotionPreference) {
    this.motion = motion;
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

  /** Initial view: Cascadia at ~1,500 km with a gentle pitch. Always a cut (first frame is the final frame). */
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
      this.publishSample(true, true);
      this.emit('settled', { flightId: id, cut: true });
      window.setTimeout(() => this.veil.classList.remove('is-on'), MOTION.duration.micro);
      return { id, settled: Promise.resolve({ outcome: 'settled', band: 'orbital', cut: true } satisfies FlightResult), interrupt: () => {} };
    }

    const from = this.viewer.camera.positionCartographic;
    const to = Cartographic.fromCartesian(sphere.center);
    const distance = Cartesian3.distance(Cartesian3.fromRadians(from.longitude, from.latitude), sphere.center);
    const durationMs = computeFlightDuration(distance, Math.abs(from.height - (offset.range ?? 0)), 1);
    let resolveSettled: (r: FlightResult) => void = () => {};
    const settled = new Promise<FlightResult>((resolve) => { resolveSettled = resolve; });

    this.active = {
      id,
      cancel: () => {
        this.viewer.camera.cancelFlight();
        resolveSettled({ outcome: 'interrupted', band: 'orbital', cut: false });
      },
    };
    this.emit('started', { flightId: id, durationMs, cut: false, reason: options.reason });
    this.viewer.camera.flyToBoundingSphere(sphere, {
      offset,
      duration: durationMs / 1000,
      easingFunction: minimumJerk,
      complete: () => {
        if (this.active?.id !== id) return;
        this.active = null;
        this.publishSample(true, true);
        this.emit('settled', { flightId: id, cut: false });
        resolveSettled({ outcome: 'settled', band: 'orbital', cut: false });
      },
      cancel: () => {
        if (this.active?.id !== id) return;
        this.active = null;
        this.emit('interrupted', { flightId: id, reason: 'user-input' });
        resolveSettled({ outcome: 'interrupted', band: 'orbital', cut: false });
      },
    });
    void to;
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
