/**
 * SceneController: creates the ion-free Cesium Viewer imperatively in the given container, owns
 * the clock (fixed to now in the spike), the layer registry, selection → camera framing, picking
 * and hover, band → layer visibility, and disposal. Geography (basin bboxes, forecast-point
 * locations) arrives through setGeography/setData — the controller never fetches.
 */
import { Cartesian2, Cartesian3, CesiumTerrainProvider, Clock, ClockRange, ClockStep, Color, Credit, CreditDisplay, Entity, JulianDate, Math as CesiumMath, Rectangle, SceneTransforms, ScreenSpaceEventHandler, ScreenSpaceEventType, Viewer } from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { CameraController } from '../camera/CameraController';
import { CameraEnvelope } from '../camera/CameraEnvelope';
import { HARD_DOMAIN, TILT_CAP_DEG_BY_BAND, ZOOM_CEILING_M, ZOOM_FLOOR_M } from '../camera/envelope';
import type { FlightReason } from '../camera/types';
import type { BasinListItem, FieldRasterState, FloodGeography, RiverEnvelope } from '../contracts/schemas';
import type { MotionPreference } from '../design-system/motion';
import { createSceneHandle } from '../layers/cesium-handle';
import type { LayerHit, LayerId, SceneHandle, SceneLayer, SelectionState } from '../layers/contract';
import { BasinsLayer, type BasinsLayerData } from '../layers/basins/BasinsLayer';
import { BasinSusceptibilityLayer, type BasinSusceptibilityLayerData } from '../layers/susceptibility/BasinSusceptibilityLayer';
import { resolveBasemap, type BasemapProvider } from '../layers/basemap/BasemapProvider';
import { createDomainVignetteLayer } from '../layers/basemap/edge-vignette';
import { RiverNetworkLayer, type RiverNetworkDisplay } from '../layers/network/RiverNetworkLayer';
import { LabelsLayer, type LabelSet as LabelSetData } from '../layers/labels/LabelsLayer';
import { CameraLayer, type CameraSetData } from '../layers/cameras/CameraLayer';
import { FloodHazardLayer, LeveesLayer } from '../layers/flood/FloodHazardLayer';
import { WeatherFieldLayer } from '../layers/fields/WeatherFieldLayer';
import { precipPixel } from '../layers/precip/style';
import { snowPixel } from '../layers/snow/style';
import { RiversLayer } from '../layers/rivers/RiversLayer';
import { CESIUM_RENDERER_CREDIT_HTML } from './credits';
import { SemanticZoomController } from './SemanticZoomController';
import { TransitionPlate } from './TransitionPlate';
import type { Band } from './bands';

/** A transient queue-zero between LOD generations must not read as a composed ground; the
 * queue has to stay empty this long before the opening frame counts as coherent (F2). */
const GROUND_SUSTAINED_ZERO_MS = 600;

export interface SceneControllerOptions { motion: MotionPreference; basemap?: BasemapProvider }
export interface Selection { basinId: string | null; forecastPointId: string | null }
export interface SelectOptions { reason: FlightReason; cut?: boolean }
export type PickedHandler = (hit: LayerHit) => void;

interface LayerDataMap {
  river_network: RiverNetworkDisplay;
  precip_observed: FieldRasterState | null;
  snow_cover: FieldRasterState | null;
  labels: LabelSetData;
  cameras: CameraSetData;
  floodplain: FloodGeography;
  levees: FloodGeography;
  basins: BasinsLayerData;
  rivers: RiverEnvelope;
  basin_susceptibility: BasinSusceptibilityLayerData;
}

export class SceneController {
  readonly viewer: Viewer;
  readonly camera: CameraController;
  private readonly envelope: CameraEnvelope;
  private readonly plate: TransitionPlate;
  readonly zoom: SemanticZoomController;
  readonly basemap: BasemapProvider;

  private readonly handle: SceneHandle;
  private readonly creditsContainer: HTMLElement;
  private readonly layers = new Map<LayerId, SceneLayer>();
  private readonly intents = new Map<LayerId, boolean>();
  private readonly basins = new Map<string, BasinListItem>();
  private readonly points = new Map<string, { lon: number; lat: number; basinId: string }>();
  private selection: SelectionState = { basinId: null, forecastPointId: null, hovered: null };
  private framed: string | null = null;
  private pending: { target: string; options: SelectOptions } | null = null;
  private readonly pickedHandlers = new Set<PickedHandler>();
  private readonly emptyClickHandlers = new Set<() => void>();
  private readonly followSelectHandlers = new Set<(basinId: string) => void>();
  private readonly renderErrorHandlers = new Set<(message: string) => void>();
  private readonly eventHandler: ScreenSpaceEventHandler;
  private readonly unsubscribes: (() => void)[] = [];
  private disposed = false;

  constructor(container: HTMLElement, options: SceneControllerOptions) {
    this.basemap = options.basemap ?? resolveBasemap();
    const clock = new Clock({ currentTime: JulianDate.now(), clockRange: ClockRange.UNBOUNDED, clockStep: ClockStep.SYSTEM_CLOCK, shouldAnimate: false });
    // Attribution is always rendered: the credit display lives in its own strip above the disclaimer.
    const credits = document.createElement('div');
    credits.className = 'scene-credits';
    credits.setAttribute('data-testid', 'scene-credits');
    container.appendChild(credits);
    // Attribution honesty (docs/research/spike-report-2026-08-22.md gap 7): this viewer is
    // ion-free, so Cesium's default ion logo credit would misattribute an app that never calls
    // ion. Replace it through the supported CreditDisplay.cesiumCredit API with a text credit
    // for the renderer — assigned before the Viewer is constructed so the ion default is never
    // built. The basemap credit (OSM) still renders on screen in this container; hiding credits
    // with CSS is forbidden because it would suppress that required attribution too.
    CreditDisplay.cesiumCredit = new Credit(CESIUM_RENDERER_CREDIT_HTML, true);
    this.creditsContainer = credits;
    this.viewer = new Viewer(container, {
      creditContainer: credits,
      baseLayer: this.basemap.createImagery(),
      terrainProvider: this.basemap.createTerrain(),
      clockViewModel: undefined,
      geocoder: false, baseLayerPicker: false, homeButton: false, sceneModePicker: false, navigationHelpButton: false,
      animation: false, timeline: false, fullscreenButton: false, infoBox: false, selectionIndicator: false, vrButton: false,
      shadows: false, shouldAnimate: false, showRenderLoopErrors: false,
      contextOptions: { webgl: { failIfMajorPerformanceCaveat: false, preserveDrawingBuffer: true } },
    });
    this.viewer.clock.currentTime = clock.currentTime;
    this.viewer.clock.shouldAnimate = false;
    this.viewer.scene.globe.enableLighting = false;
    // Continuity tuning (visual-continuity pass 2026-08-29): keep ancestors AND siblings of
    // visible tiles warm so pans/zooms reveal composed ground instead of a tile checkerboard,
    // and hold ~6x the default tile cache so revisiting a band re-shows instantly instead of
    // re-fetching. Memory cost measured in the session checkpoint; requests unchanged at rest.
    this.viewer.scene.globe.preloadAncestors = true;
    this.viewer.scene.globe.preloadSiblings = true;
    this.viewer.scene.globe.tileCacheSize = 800;
    // Unloaded ground reads as night-dark earth, not Cesium's white void: while imagery
    // composes, missing tiles must recede into the design's canvas instead of flashing —
    // the sweep caught whole coastlines floating on white during a basin cut.
    this.viewer.scene.globe.baseColor = Color.fromCssColorString('hsl(222, 52%, 6%)');
    // LESSON (owner screenshot 2026-09-01): a high loadingDescendantLimit batches
    // refinement into HALF-SCREEN generation blocks whose boundaries are far uglier than
    // granular replacement. Cesium's default (20) is the tuned balance — leave it alone.

    // THE CASCADIA OPERATING ENVELOPE (mission §2–3): this is a Pacific-Northwest
    // instrument. The globe is not drawn outside the hard domain (a shader discard —
    // beyond it lies the design's own canvas, not space), the zoom band keeps the planet
    // out of reach, look is disabled, and the rotate gesture stays north-up. The dark
    // background + no stars/atmosphere make the domain edge dissolve instead of cutting.
    this.viewer.scene.globe.cartographicLimitRectangle = Rectangle.fromDegrees(
      HARD_DOMAIN.west, HARD_DOMAIN.south, HARD_DOMAIN.east, HARD_DOMAIN.north,
    );
    this.viewer.scene.backgroundColor = Color.fromCssColorString('hsl(222, 52%, 6%)');
    if (this.viewer.scene.skyBox) this.viewer.scene.skyBox.show = false;
    if (this.viewer.scene.skyAtmosphere) this.viewer.scene.skyAtmosphere.show = false;
    // Fallback chain, bottom-up: coarse base plate (always-valid earth) → main imagery
    // (voids transparent) → domain vignette. A void pixel now reveals real coarse ground.
    const basePlate = this.basemap.createBasePlate?.();
    if (basePlate) this.viewer.imageryLayers.add(basePlate, 0);
    const vignette = createDomainVignetteLayer();
    if (vignette) this.viewer.imageryLayers.add(vignette);
    const sscc = this.viewer.scene.screenSpaceCameraController;
    sscc.minimumZoomDistance = ZOOM_FLOOR_M;
    sscc.maximumZoomDistance = ZOOM_CEILING_M;
    sscc.enableLook = false;
    sscc.enableTilt = false; // owner 2026-09-01: top-down, no angles — no tilt gesture at all
    this.viewer.camera.constrainedAxis = Cartesian3.UNIT_Z;
    // Stays false WITH terrain too, deliberately: every hydrologic layer drapes (clamped
    // polylines, ground hatches), and a gauge marker hidden behind a ridge would be a
    // legibility bug, not realism (ADR-0021 exit test names this decision).
    this.viewer.scene.globe.depthTestAgainstTerrain = false;
    void this.upgradeTerrain();
    this.handle = createSceneHandle(this.viewer);

    this.camera = new CameraController(this.viewer, container, options.motion);
    this.zoom = new SemanticZoomController();
    this.unsubscribes.push(this.camera.onSample((sample) => this.zoom.onCameraSample(sample)));
    this.unsubscribes.push(this.zoom.on('bandChanged', (e) => this.applyBand(e.next)));
    this.envelope = new CameraEnvelope(this.viewer, this.camera, () => this.zoom.band, options.motion);
    // Tiles appear all at once: the last gesture/flight frame holds while the scene warms
    // beneath, then one crossfade (TransitionPlate — the §2 composition layer).
    this.plate = new TransitionPlate(this.viewer, container);
    this.unsubscribes.push(this.camera.on('settled', () => this.plate.onFlightSettled()));
    const onFollowMoveEnd = () => this.evaluateFollowSelect();
    this.viewer.camera.moveEnd.addEventListener(onFollowMoveEnd);
    this.unsubscribes.push(() => this.viewer.camera.moveEnd.removeEventListener(onFollowMoveEnd));

    // UNIFORM GENERATION DURING MOTION (owner 2026-09-01: "cinematic shifting while
    // scrolling"): mid-gesture the renderer can only scale what it has, and mixed
    // generations ARE the patchwork. So while a zoom/pan gesture is ACTIVE the whole
    // world renders one LOD step softer — uniformly, no crisp-next-to-blurry — and the
    // moment the hand lifts, the TransitionPlate captures that uniform frame FIRST, the
    // threshold restores UNDER the plate, and full detail reveals as one crossfade.
    // The earlier version of this idea flashed because HOVER armed it and the restore
    // was naked; now only wheel and button-down drags count, and the restore is hidden.
    const MOTION_SSE = 3.2;
    const MOTION_IDLE_MS = 260;
    let motionIdle: number | null = null;
    let dragging = false;
    const motionStart = () => {
      this.viewer.scene.globe.maximumScreenSpaceError = MOTION_SSE;
      if (motionIdle !== null) window.clearTimeout(motionIdle);
      motionIdle = window.setTimeout(() => {
        motionIdle = null;
        this.plate.holdNow(); // capture the uniform frame BEFORE sharpening begins
        this.viewer.scene.globe.maximumScreenSpaceError = 2;
        this.viewer.scene.requestRender();
      }, MOTION_IDLE_MS);
    };
    const sceneCanvas = this.viewer.scene.canvas;
    const onWheelMotion = () => motionStart();
    const onPointerDownMotion = () => { dragging = true; };
    const onPointerMoveMotion = () => { if (dragging) motionStart(); };
    const onPointerUpMotion = () => { dragging = false; };
    sceneCanvas.addEventListener('wheel', onWheelMotion, { passive: true });
    sceneCanvas.addEventListener('pointerdown', onPointerDownMotion);
    sceneCanvas.addEventListener('pointermove', onPointerMoveMotion);
    sceneCanvas.addEventListener('pointerup', onPointerUpMotion);
    sceneCanvas.addEventListener('pointerleave', onPointerUpMotion);
    this.unsubscribes.push(() => {
      sceneCanvas.removeEventListener('wheel', onWheelMotion);
      sceneCanvas.removeEventListener('pointerdown', onPointerDownMotion);
      sceneCanvas.removeEventListener('pointermove', onPointerMoveMotion);
      sceneCanvas.removeEventListener('pointerup', onPointerUpMotion);
      sceneCanvas.removeEventListener('pointerleave', onPointerUpMotion);
      if (motionIdle !== null) window.clearTimeout(motionIdle);
    });

    for (const layer of [
      new WeatherFieldLayer({ id: 'snow_cover', displayName: 'Snow water equivalent (SNODAS, daily)', truthClass: 'authoritative_model', pixel: snowPixel }),
      new WeatherFieldLayer({ id: 'precip_observed', displayName: 'Observed precipitation (MRMS QPE, 1 h)', truthClass: 'observation', pixel: precipPixel }),
      new FloodHazardLayer(), new LeveesLayer(), new BasinSusceptibilityLayer(), new RiverNetworkLayer(), new LabelsLayer(), new CameraLayer(), new BasinsLayer(), new RiversLayer(),
    ] as SceneLayer[]) {
      this.layers.set(layer.id, layer);
      this.intents.set(layer.id, true);
      layer.mount(this.handle);
      layer.setMotion(options.motion);
    }

    this.eventHandler = new ScreenSpaceEventHandler(this.viewer.scene.canvas);
    this.eventHandler.setInputAction((e: ScreenSpaceEventHandler.PositionedEvent) => {
      const hit = this.hitAt(e.position);
      if (hit) this.pickedHandlers.forEach((h) => h(hit));
      else this.emptyClickHandlers.forEach((h) => h());
    }, ScreenSpaceEventType.LEFT_CLICK);
    this.eventHandler.setInputAction((e: ScreenSpaceEventHandler.MotionEvent) => {
      const hit = this.hitAt(e.endPosition);
      const hovered = hit?.entityId ?? null;
      if (hovered === this.selection.hovered) return;
      this.viewer.scene.canvas.style.cursor = hovered ? 'pointer' : '';
      this.setSelection({ ...this.selection, hovered });
    }, ScreenSpaceEventType.MOUSE_MOVE);

    // Tile-load diagnostic for tests and tooling: the container carries the pending-tile
    // count as a data attribute (imperative DOM, no React) so a visual spec can await a
    // settled ground instead of guessing a timeout — the source of the mid-load baselines.
    //
    // Ground progress for the boot manifest (UX reconstruction 2026-08-31): the queue's
    // high-water mark is the denominator, so `1 - pending/highWater` is measured work, not a
    // timer. "Composed" requires the queue to stay empty for a beat — the first transient
    // zero can land between the coarse pass and child-tile discovery, and revealing there is
    // exactly the blurry opening frame the audit recorded (F2).
    const onTileProgress = (pending: number) => {
      container.dataset.tilesPending = String(pending);
      if (pending > 0) {
        this.groundSawLoading = true;
        this.groundHighWater = Math.max(this.groundHighWater, pending);
        if (this.groundZeroTimer !== null) {
          window.clearTimeout(this.groundZeroTimer);
          this.groundZeroTimer = null;
        }
      }
      const progress = this.groundHighWater > 0 ? 1 - pending / this.groundHighWater : 0;
      this.groundProgressHandlers.forEach((h) => h(Math.max(0, Math.min(1, progress))));
      if (pending === 0 && this.groundSawLoading && !this.groundComposed && this.groundZeroTimer === null) {
        this.groundZeroTimer = window.setTimeout(() => {
          this.groundZeroTimer = null;
          if (this.groundComposed) return;
          this.groundComposed = true;
          this.groundComposedHandlers.forEach((h) => h());
          this.groundComposedHandlers.clear();
        }, GROUND_SUSTAINED_ZERO_MS);
      }
    };
    this.viewer.scene.globe.tileLoadProgressEvent.addEventListener(onTileProgress);
    container.dataset.tilesPending = '0';
    this.unsubscribes.push(() => {
      this.viewer.scene.globe.tileLoadProgressEvent.removeEventListener(onTileProgress);
      if (this.groundZeroTimer !== null) window.clearTimeout(this.groundZeroTimer);
    });

    // A render-loop error stops rendering; surface it as a degraded scene instead of Cesium's modal panel.
    const onRenderError = (_scene: unknown, error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      console.error('render loop error', error);
      this.renderErrorHandlers.forEach((h) => h(message));
    };
    this.viewer.scene.renderError.addEventListener(onRenderError);
    this.unsubscribes.push(() => this.viewer.scene.renderError.removeEventListener(onRenderError));

    this.camera.setInitialView();
    this.applyBand(this.zoom.band);
    // Dev-only escape hatch for in-browser diagnosis; never present in production builds.
    if (import.meta.env.DEV) (window as unknown as { __cascadiaScene?: SceneController }).__cascadiaScene = this;
  }

  onRenderError(handler: (message: string) => void): () => void {
    this.renderErrorHandlers.add(handler);
    return () => this.renderErrorHandlers.delete(handler);
  }

  get band(): Band { return this.zoom.band; }

  onPicked(handler: PickedHandler): () => void {
    this.pickedHandlers.add(handler);
    return () => this.pickedHandlers.delete(handler);
  }

  /** A click on the world that hit nothing — the map's own "click away" (dismissal §12). */
  onEmptyClick(handler: () => void): () => void {
    this.emptyClickHandlers.add(handler);
    return () => this.emptyClickHandlers.delete(handler);
  }

  /** VIEWPORT-FOLLOW SELECTION (owner request 2026-08-31): while a basin panel is open,
   * panning the world re-selects the basin under the view centre — the intelligence
   * follows the map, without a flight (framed is pre-set so the bridge's select is a
   * no-op for the camera). Fires with the basin id when the centre settles over a
   * DIFFERENT seeded basin. */
  onFollowSelect(handler: (basinId: string) => void): () => void {
    this.followSelectHandlers.add(handler);
    return () => this.followSelectHandlers.delete(handler);
  }

  private evaluateFollowSelect(): void {
    if (this.selection.basinId === null) return; // no menu open — never grab a selection
    if (this.camera.flightActive) return;
    if (this.zoom.band === 'orbital') return;
    const canvas = this.viewer.scene.canvas;
    const center = new Cartesian2(canvas.clientWidth / 2, canvas.clientHeight / 2);
    const picked = this.viewer.camera.pickEllipsoid(center, this.viewer.scene.globe.ellipsoid);
    if (!picked) return;
    const carto = this.viewer.scene.globe.ellipsoid.cartesianToCartographic(picked);
    const lon = CesiumMath.toDegrees(carto.longitude);
    const lat = CesiumMath.toDegrees(carto.latitude);
    const contains = (b: BasinListItem): boolean => {
      const [w, so, e, n] = b.bbox;
      return lon >= w && lon <= e && lat >= so && lat <= n;
    };
    const current = this.basins.get(this.selection.basinId);
    if (current && contains(current)) return; // hysteresis: stay while still over it
    let best: { id: string; d: number } | null = null;
    for (const b of this.basins.values()) {
      if (!contains(b)) continue;
      const [w, so, e, n] = b.bbox;
      const d = Math.hypot(lon - (w + e) / 2, lat - (so + n) / 2);
      if (best === null || d < best.d) best = { id: b.id, d };
    }
    if (best === null || best.id === this.selection.basinId) return;
    this.framed = best.id; // the follow is selection-only: the user is already looking there
    this.followSelectHandlers.forEach((h) => h(best.id));
  }

  setMotion(motion: MotionPreference): void {
    this.camera.setMotionPreference(motion);
    this.envelope.setMotionPreference(motion);
    this.layers.forEach((layer) => layer.setMotion(motion));
  }

  setLayerIntents(active: readonly LayerId[]): void {
    const activeSet = new Set(active);
    for (const id of this.layers.keys()) this.intents.set(id, activeSet.has(id));
    this.applyBand(this.zoom.band);
  }

  setGeography(basins: readonly BasinListItem[]): void {
    basins.forEach((b) => this.basins.set(b.id, b));
    this.reconcile();
  }

  setData<K extends keyof LayerDataMap>(layerId: K, data: LayerDataMap[K]): void {
    if (this.disposed) return;
    if (layerId === 'rivers') {
      for (const item of (data as RiverEnvelope).items) {
        if (item.location) this.points.set(item.id, { lon: item.location[0], lat: item.location[1], basinId: item.basin_id });
      }
    }
    const layer = this.layers.get(layerId) as SceneLayer<LayerDataMap[K]> | undefined;
    layer?.setData(data);
    this.reconcile();
  }

  /** Selection from the store. Frames the forecast point if present, else the basin; pending until geography arrives. */
  select(selection: Selection, options: SelectOptions): void {
    this.setSelection({ ...selection, hovered: this.selection.hovered });
    const target = selection.forecastPointId ?? selection.basinId;
    if (!target) { this.pending = null; this.framed = null; return; }
    if (target === this.framed) return;
    this.pending = { target, options };
    this.reconcile();
  }

  layerStatuses(): { id: LayerId; status: string; reason: string | null }[] {
    return [...this.layers.values()].map((l) => ({ id: l.id, status: l.status, reason: l.statusReason }));
  }

  /** ADR-0021 §3: real relief when a pyramid is served, the ellipsoid otherwise — terrain is
   * enhancement, never a dependency. The default asks the same-origin gateway (`/terrain/v1`,
   * proxied to the R2 public domain); previews and the e2e stub 404 there and stay flat with
   * one console line, which is exactly the honest degraded state. */
  private async upgradeTerrain(): Promise<void> {
    const root = (import.meta.env.VITE_TERRAIN_URL as string | undefined) ?? '/terrain/v1';
    try {
      const provider = await CesiumTerrainProvider.fromUrl(root);
      if (this.disposed) return;
      this.viewer.terrainProvider = provider;
      this.viewer.scene.requestRender();
    } catch {
      console.info(`terrain: no pyramid at ${root}; the ellipsoid stands in`);
    }
  }

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.unsubscribes.forEach((u) => u());
    this.eventHandler.destroy();
    this.layers.forEach((layer) => layer.dispose());
    this.plate.dispose();
    this.envelope.dispose();
    this.camera.dispose();
    this.viewer.destroy();
    this.creditsContainer.remove(); // the credits div is ours, not the Viewer's; remove it so a remount cannot leave orphan attribution strips
  }

  private setSelection(selection: SelectionState): void {
    this.selection = selection;
    this.layers.forEach((layer) => layer.setSelection(selection));
  }

  private applyBand(band: Band): void {
    // Band ⇒ how far the tilt gesture may lean (mission §3): analytical bands stay near
    // nadir; only local earns a controlled oblique. Radians from nadir at the pivot.
    this.viewer.scene.screenSpaceCameraController.maximumTiltAngle = CesiumMath.toRadians(TILT_CAP_DEG_BY_BAND[band]);
    for (const layer of this.layers.values()) {
      const visible = (this.intents.get(layer.id) ?? true) && layer.bands[band] !== 'hidden';
      layer.setVisible(visible);
      layer.setBand(band);
    }
  }

  private reconcile(): void {
    const pending = this.pending;
    if (!pending) return;
    const { target, options } = pending;
    if (target.startsWith('basin:')) {
      const basin = this.basins.get(target);
      if (!basin) return;
      this.pending = null;
      this.framed = target;
      this.camera.flyToBasin(basin.bbox, options);
      return;
    }
    const point = this.points.get(target);
    if (!point) return;
    this.pending = null;
    this.framed = target;
    this.camera.frameForecastPoint(point.lon, point.lat, options);
  }

  /**
   * Imperative screen-space tracking for DOM overlays (camera preview cards): the callback
   * fires from Cesium's postRender with the projected window position (or null when behind
   * the globe), and the caller writes DOM transforms DIRECTLY — no React state is ever set
   * per frame (renderer-boundary rule). Returns a disposer.
   */
  trackScreenPosition(lon: number, lat: number, onMove: (pos: { x: number; y: number } | null) => void): () => void {
    const world = Cartesian3.fromDegrees(lon, lat);
    const scratch = new Cartesian2();
    let lastX = Number.NaN;
    let lastY = Number.NaN;
    const listener = () => {
      const projected = SceneTransforms.worldToWindowCoordinates(this.viewer.scene, world, scratch);
      if (!projected) {
        if (!Number.isNaN(lastX)) { lastX = Number.NaN; onMove(null); }
        return;
      }
      if (Math.abs(projected.x - lastX) < 0.5 && Math.abs(projected.y - lastY) < 0.5) return;
      lastX = projected.x;
      lastY = projected.y;
      onMove({ x: projected.x, y: projected.y });
    };
    this.viewer.scene.postRender.addEventListener(listener);
    this.viewer.scene.requestRender();
    return () => this.viewer.scene.postRender.removeEventListener(listener);
  }

  private groundSawLoading = false;
  private groundComposed = false;
  private groundHighWater = 0;
  private groundZeroTimer: number | null = null;
  private readonly groundComposedHandlers = new Set<() => void>();
  private readonly groundProgressHandlers = new Set<(progress: number) => void>();

  /** Fires ONCE, when the globe's tile queue has stayed empty for a sustained beat after
   * having loaded — the moment the opening ground is a composed picture rather than an
   * assembly in progress. Fires immediately if that already happened. Returns a disposer. */
  onGroundComposed(handler: () => void): () => void {
    if (this.groundComposed) {
      handler();
      return () => {};
    }
    this.groundComposedHandlers.add(handler);
    return () => this.groundComposedHandlers.delete(handler);
  }

  /** Measured ground-composition progress in [0,1]: the tile queue's drain against its
   * high-water mark. Real work, not a timer — feeds the boot manifest's largest slice. */
  onGroundProgress(handler: (progress: number) => void): () => void {
    if (this.groundComposed) {
      handler(1);
      return () => {};
    }
    this.groundProgressHandlers.add(handler);
    return () => this.groundProgressHandlers.delete(handler);
  }

  private hitAt(position: { x: number; y: number }): LayerHit | null {
    const picked: unknown = this.viewer.scene.pick(position as never);
    const raw = (picked as { id?: unknown } | undefined)?.id;
    // Entity picks carry an Entity whose id is the renderer tag; primitive picks (billboards,
    // labels) carry the tag string directly.
    const tag = raw instanceof Entity ? raw.id : typeof raw === 'string' ? raw : null;
    if (typeof tag !== 'string') return null;
    for (const layer of this.layers.values()) {
      const hit = layer.hitTest(tag);
      if (hit) return hit;
    }
    return null;
  }
}
