/**
 * FloodHazardLayer (`floodplain`) + LeveesLayer (`levees`): the static flood geography —
 * FEMA regulatory zones and NLD levee centerlines, STATIC HAZARD register (style.ts owns the
 * doctrine; this file diffs entities).
 *
 * Only the SELECTED basin's geometry is instantiated: the fixture holds ~2,200 zone rings
 * across six basins and the entity budgets (LAYER_SYSTEM §7) are real — a selection change
 * rebuilds a few hundred entities, which is cheap; six basins at once would not be. Zones
 * draw at river/local bands (0.2% at local only); nothing draws for a basin whose
 * availability is not covered — that absence is stated in the panel, never papered over.
 */
import {
  Cartesian3,
  Color,
  ColorMaterialProperty,
  CustomDataSource,
  PolylineDashMaterialProperty,
  type Viewer,
} from 'cesium';
import type { FloodGeography } from '../../contracts/schemas';
import type { MotionPreference } from '../../design-system/motion';
import type { Band } from '../../scene/bands';
import type { LayerHit, LayerStatus, SceneHandle, SceneLayer, SelectionState } from '../contract';
import { viewerOf } from '../cesium-handle';
import { hazardZone, leveeLine, type FloodAvailability, type HazardClass } from './style';

const hsl = (c: { h: number; s: number; l: number }, alpha: number) =>
  Color.fromHsl(c.h / 360, c.s / 100, c.l / 100, alpha);

abstract class FloodBase<TId extends 'floodplain' | 'levees'> implements SceneLayer<FloodGeography> {
  abstract readonly id: TId;
  abstract readonly displayName: string;
  readonly truthClass = 'cartographic' as const;
  readonly bands: SceneLayer['bands'] = {
    orbital: 'hidden', state: 'hidden', basin: 'hidden', river: 'full', local: 'full',
  };

  status: LayerStatus = 'created';
  statusReason: string | null = 'no data yet';

  protected viewer: Viewer | null = null;
  protected readonly source: CustomDataSource;
  protected data: FloodGeography | null = null;
  protected band: Band = 'orbital';
  protected selectedBasinId: string | null = null;
  protected visible = true;
  private disposed = false;

  constructor(sourceName: string) {
    this.source = new CustomDataSource(sourceName);
  }

  mount(scene: SceneHandle): void {
    this.viewer = viewerOf(scene);
    if (!this.viewer.dataSources.contains(this.source)) void this.viewer.dataSources.add(this.source);
  }

  unmount(): void {
    if (this.viewer?.dataSources.contains(this.source)) this.viewer.dataSources.remove(this.source, false);
    this.viewer = null;
  }

  dispose(): void {
    this.unmount();
    this.source.entities.removeAll();
    this.disposed = true;
  }

  setVisible(visible: boolean): void {
    this.visible = visible;
    this.source.show = visible;
    this.viewer?.scene.requestRender();
  }

  setBand(band: Band): void {
    if (band === this.band) return;
    this.band = band;
    this.rebuild();
  }

  setSelection(selection: SelectionState): void {
    if (selection.basinId === this.selectedBasinId) return;
    this.selectedBasinId = selection.basinId;
    this.rebuild();
  }

  setMotion(_motion: MotionPreference): void {}

  setData(data: FloodGeography): void {
    if (this.disposed) return;
    this.data = data;
    this.status = 'current';
    this.statusReason = null;
    this.rebuild();
  }

  hitTest(_rendererTag: string): LayerHit | null {
    return null; // static hazard is context; the panel carries its words
  }

  protected abstract rebuild(): void;
}

export class FloodHazardLayer extends FloodBase<'floodplain'> {
  readonly id = 'floodplain' as const;
  readonly displayName = 'FEMA flood hazard zones (static, effective NFHL)';

  constructor() {
    super('floodplain');
  }

  protected rebuild(): void {
    this.source.entities.removeAll();
    const basin = this.selectedBasinId ? this.data?.basins[this.selectedBasinId] : undefined;
    if (this.data && basin) {
      const availability = basin.availability as FloodAvailability;
      for (const cls of ['pct02', 'sfha', 'floodway'] as HazardClass[]) {
        const style = hazardZone(cls, this.band, availability);
        if (!style.show) continue;
        for (const [index, ring] of basin[cls].entries()) {
          if (ring.length < 4) continue;
          this.source.entities.add({
            id: `floodplain|${this.selectedBasinId}|${cls}|${index}`,
            polygon: {
              hierarchy: Cartesian3.fromDegreesArray(ring.flat()),
              material: new ColorMaterialProperty(hsl(style.fill, style.fillAlpha)),
              outline: style.outlineAlpha > 0 && !style.dashed,
              outlineColor: hsl(style.fill, style.outlineAlpha),
            },
          });
          if (style.dashed && style.outlineAlpha > 0) {
            this.source.entities.add({
              id: `floodplain|${this.selectedBasinId}|${cls}|${index}|edge`,
              polyline: {
                positions: Cartesian3.fromDegreesArray(ring.flat()),
                clampToGround: true,
                width: 1,
                material: new PolylineDashMaterialProperty({ color: hsl(style.fill, style.outlineAlpha), dashLength: 12 }),
              },
            });
          }
        }
      }
    }
    this.source.show = this.visible;
    this.viewer?.scene.requestRender();
  }
}

export class LeveesLayer extends FloodBase<'levees'> {
  readonly id = 'levees' as const;
  readonly displayName = 'Levee centerlines (USACE NLD, as received)';

  constructor() {
    super('levees');
  }

  protected rebuild(): void {
    this.source.entities.removeAll();
    const basin = this.selectedBasinId ? this.data?.basins[this.selectedBasinId] : undefined;
    const style = leveeLine(this.band);
    if (this.data && basin && style.show) {
      for (const levee of basin.levees) {
        for (const [index, path] of levee.paths.entries()) {
          if (path.length < 2) continue;
          this.source.entities.add({
            id: `levees|${levee.system_id}|${index}`,
            polyline: {
              positions: Cartesian3.fromDegreesArray(path.flat()),
              clampToGround: true,
              width: style.widthPx,
              material: new PolylineDashMaterialProperty({ color: hsl(style.color, style.alpha), dashLength: 8 }),
            },
          });
        }
      }
    }
    this.source.show = this.visible;
    this.viewer?.scene.requestRender();
  }
}
