/**
 * SceneController: creates the ion-free Cesium Viewer imperatively in the given container, owns
 * the clock (fixed to now in the spike), the layer registry, selection → camera framing, picking
 * and hover, band → layer visibility, and disposal. Geography (basin bboxes, forecast-point
 * locations) arrives through setGeography/setData — the controller never fetches.
 */
import { Clock, ClockRange, ClockStep, Credit, CreditDisplay, Entity, JulianDate, ScreenSpaceEventHandler, ScreenSpaceEventType, Viewer } from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { CameraController } from '../camera/CameraController';
import type { FlightReason } from '../camera/types';
import type { BasinListItem, RiverEnvelope } from '../contracts/schemas';
import type { MotionPreference } from '../design-system/motion';
import { createSceneHandle } from '../layers/cesium-handle';
import type { LayerHit, LayerId, SceneHandle, SceneLayer, SelectionState } from '../layers/contract';
import { BasinsLayer, type BasinsLayerData } from '../layers/basins/BasinsLayer';
import { osmKeyless, type BasemapProvider } from '../layers/basemap/BasemapProvider';
import { RiversLayer } from '../layers/rivers/RiversLayer';
import { CESIUM_RENDERER_CREDIT_HTML } from './credits';
import { SemanticZoomController } from './SemanticZoomController';
import type { Band } from './bands';

export interface SceneControllerOptions { motion: MotionPreference; basemap?: BasemapProvider }
export interface Selection { basinId: string | null; forecastPointId: string | null }
export interface SelectOptions { reason: FlightReason; cut?: boolean }
export type PickedHandler = (hit: LayerHit) => void;

interface LayerDataMap { basins: BasinsLayerData; rivers: RiverEnvelope }

export class SceneController {
  readonly viewer: Viewer;
  readonly camera: CameraController;
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
  private readonly renderErrorHandlers = new Set<(message: string) => void>();
  private readonly eventHandler: ScreenSpaceEventHandler;
  private readonly unsubscribes: (() => void)[] = [];
  private disposed = false;

  constructor(container: HTMLElement, options: SceneControllerOptions) {
    this.basemap = options.basemap ?? osmKeyless;
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
    this.viewer.scene.globe.depthTestAgainstTerrain = false;
    this.handle = createSceneHandle(this.viewer);

    this.camera = new CameraController(this.viewer, container, options.motion);
    this.zoom = new SemanticZoomController();
    this.unsubscribes.push(this.camera.onSample((sample) => this.zoom.onCameraSample(sample)));
    this.unsubscribes.push(this.zoom.on('bandChanged', (e) => this.applyBand(e.next)));

    for (const layer of [new BasinsLayer(), new RiversLayer()] as SceneLayer[]) {
      this.layers.set(layer.id, layer);
      this.intents.set(layer.id, true);
      layer.mount(this.handle);
      layer.setMotion(options.motion);
    }

    this.eventHandler = new ScreenSpaceEventHandler(this.viewer.scene.canvas);
    this.eventHandler.setInputAction((e: ScreenSpaceEventHandler.PositionedEvent) => {
      const hit = this.hitAt(e.position);
      if (hit) this.pickedHandlers.forEach((h) => h(hit));
    }, ScreenSpaceEventType.LEFT_CLICK);
    this.eventHandler.setInputAction((e: ScreenSpaceEventHandler.MotionEvent) => {
      const hit = this.hitAt(e.endPosition);
      const hovered = hit?.entityId ?? null;
      if (hovered === this.selection.hovered) return;
      this.viewer.scene.canvas.style.cursor = hovered ? 'pointer' : '';
      this.setSelection({ ...this.selection, hovered });
    }, ScreenSpaceEventType.MOUSE_MOVE);

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

  setMotion(motion: MotionPreference): void {
    this.camera.setMotionPreference(motion);
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

  dispose(): void {
    if (this.disposed) return;
    this.disposed = true;
    this.unsubscribes.forEach((u) => u());
    this.eventHandler.destroy();
    this.layers.forEach((layer) => layer.dispose());
    this.camera.dispose();
    this.viewer.destroy();
    this.creditsContainer.remove(); // the credits div is ours, not the Viewer's; remove it so a remount cannot leave orphan attribution strips
  }

  private setSelection(selection: SelectionState): void {
    this.selection = selection;
    this.layers.forEach((layer) => layer.setSelection(selection));
  }

  private applyBand(band: Band): void {
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

  private hitAt(position: { x: number; y: number }): LayerHit | null {
    const picked: unknown = this.viewer.scene.pick(position as never);
    const entity = (picked as { id?: unknown } | undefined)?.id;
    if (!(entity instanceof Entity) || typeof entity.id !== 'string') return null;
    for (const layer of this.layers.values()) {
      const hit = layer.hitTest(entity.id);
      if (hit) return hit;
    }
    return null;
  }
}
