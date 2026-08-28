/**
 * PrecipFieldLayer: the observed MRMS QPE hour as a georeferenced wash — C3b, the first
 * weather FIELD on the map ("precipitation is arriving here", design direction 2026-08-28).
 *
 * OBSERVED register: the document's truth class is `observation` and every pixel comes from
 * `precipPixel` (style.ts), whose honesty rules — dry is transparent, unknown is transparent,
 * the ramp saturates — are pinned there. The raster georeferences itself from its own spec
 * (ADR-0020: the window is a decision, not a constant); the rectangle spans cell EDGES, so
 * the spec's NW cell center gets half a cell of margin on each side.
 *
 * Cesium mechanics: one canvas painted per data push, shown as a SingleTileImageryProvider
 * imagery layer under the vector layers. An hourly cadence means replace-not-diff is the
 * right cost; nothing here runs per frame.
 */
import {
  ImageryLayer,
  Rectangle,
  SingleTileImageryProvider,
  type Viewer,
} from 'cesium';
import type { FieldRasterState } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { decodeFieldCells } from './decode';
import { precipPixel } from './style';

export class PrecipFieldLayer implements SceneLayer<FieldRasterState | null> {
  readonly id = 'precip_observed' as const;
  readonly displayName = 'Observed precipitation (MRMS QPE, 1 h)';
  readonly truthClass = 'observation' as const;
  readonly bands: SceneLayer['bands'] = {
    orbital: 'full', state: 'full', basin: 'full', river: 'full', local: 'full',
  };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  private viewer: Viewer | null = null;
  private imagery: ImageryLayer | null = null;
  private visible = true;
  private disposed = false;
  private generation = 0;

  mount(scene: SceneHandle): void {
    this.viewer = viewerOf(scene);
    if (this.imagery) this.attach(this.imagery);
  }

  unmount(): void {
    this.detach();
    this.viewer = null;
  }

  dispose(): void {
    this.detach();
    this.imagery = null;
    this.disposed = true;
  }

  setVisible(visible: boolean): void {
    this.visible = visible;
    if (this.imagery) this.imagery.show = visible;
    this.viewer?.scene.requestRender();
  }

  setBand(_band: Band): void {
    // The field reads at every band; restraint lives in the wash alpha, not in band gating.
  }

  setSelection(_selection: SelectionState): void {
    // Weather does not select. Cells carry no identity to pick.
  }

  setMotion(_motion: MotionPreference): void {
    // Static wash; C4's animated weather owns motion preferences.
  }

  setData(state: FieldRasterState | null): void {
    if (this.disposed) return;
    const generation = (this.generation += 1);
    if (state === null) {
      // "nothing current to draw" — absence is the rendering, and stale imagery must not linger
      this.detach();
      this.imagery = null;
      this.status = 'unknown';
      this.statusReason = 'no observed field within the freshness bound';
      this.viewer?.scene.requestRender();
      return;
    }
    void this.rebuild(state, generation);
  }

  hitTest(_rendererTag: string): LayerHit | null {
    return null;
  }

  private async rebuild(state: FieldRasterState, generation: number): Promise<void> {
    let cells: Float32Array;
    try {
      cells = await decodeFieldCells(state);
    } catch (error) {
      this.status = 'error';
      this.statusReason = error instanceof Error ? error.message : 'field decode failed';
      return;
    }
    if (this.disposed || generation !== this.generation) return; // a newer push superseded this one

    const { nx, ny, lo1, la1, dlon, dlat } = state.spec;
    const canvas = document.createElement('canvas');
    canvas.width = nx;
    canvas.height = ny;
    const ctx = canvas.getContext('2d');
    if (ctx === null) {
      this.status = 'error';
      this.statusReason = 'no 2d canvas context (headless renderer)';
      return;
    }
    const image = ctx.createImageData(nx, ny);
    for (let i = 0; i < cells.length; i += 1) {
      const px = precipPixel(Number.isNaN(cells[i]) ? null : cells[i]);
      const o = i * 4;
      image.data[o] = px.r;
      image.data[o + 1] = px.g;
      image.data[o + 2] = px.b;
      image.data[o + 3] = px.a;
    }
    ctx.putImageData(image, 0, 0);

    // cell centers -> cell edges: half a step of margin each side
    const rectangle = Rectangle.fromDegrees(
      lo1 - dlon / 2,
      la1 - (ny - 1) * dlat - dlat / 2,
      lo1 + (nx - 1) * dlon + dlon / 2,
      la1 + dlat / 2,
    );
    const provider = new SingleTileImageryProvider({
      url: canvas.toDataURL('image/png'),
      tileWidth: nx,
      tileHeight: ny,
      rectangle,
    });
    this.detach();
    this.imagery = new ImageryLayer(provider, {});
    this.attach(this.imagery);
    this.status = 'current';
    this.statusReason = null;
    this.viewer?.scene.requestRender();
  }

  private attach(imagery: ImageryLayer): void {
    if (!this.viewer) return;
    if (!this.viewer.imageryLayers.contains(imagery)) this.viewer.imageryLayers.add(imagery);
    imagery.show = this.visible;
  }

  private detach(): void {
    if (this.viewer && this.imagery && this.viewer.imageryLayers.contains(this.imagery)) {
      this.viewer.imageryLayers.remove(this.imagery, true);
    }
  }
}
