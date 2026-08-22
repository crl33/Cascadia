/**
 * The SceneLayer interface (docs/LAYER_SYSTEM.md §1, spike subset): id, truth class, band
 * visibility row, lifecycle, setVisible/setData/setBand/setSelection, status and hitTest.
 * SceneHandle is an opaque brand — renderer types never cross this file.
 */
import type { TruthClass } from '../contracts/schemas';
import type { Band } from '../scene/bands';
import type { LayerId, EntityId } from '../state/store';
import type { MotionPreference } from '../design-system/motion';

export type { LayerId, EntityId };
export type BandVisibility = 'full' | 'reduced' | 'hidden';
export type LayerStatus = 'created' | 'loading' | 'current' | 'stale' | 'partial' | 'missing' | 'unknown' | 'degraded' | 'error';

export interface SceneHandle { readonly __brand: 'SceneHandle' }

export interface SelectionState {
  basinId: EntityId | null;
  forecastPointId: EntityId | null;
  hovered: EntityId | null;
}

export interface LayerHit { layerId: LayerId; entityId: EntityId; basinId: EntityId | null }

export interface SceneLayer<Data = unknown> {
  readonly id: LayerId;
  readonly displayName: string;
  readonly truthClass: TruthClass;
  readonly bands: Record<Band, BandVisibility>;

  mount(scene: SceneHandle): void;
  unmount(): void;
  dispose(): void;

  setVisible(visible: boolean): void;
  setData(data: Data): void;
  setBand(band: Band): void;
  setSelection(selection: SelectionState): void;
  setMotion(motion: MotionPreference): void;

  readonly status: LayerStatus;
  readonly statusReason: string | null;

  /** Resolve the tag this layer wrote on a renderer primitive back to an entity id. */
  hitTest(rendererTag: string): LayerHit | null;
}
