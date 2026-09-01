/**
 * scene/bridge.ts — the ONLY module that subscribes the Zustand store to the controllers, and
 * the only place controller events write back to the store. Store → controller: selection,
 * motion preference, layer intents, experience choice. Controller → store: altitude band,
 * flight state, picks, the resolved quality tier.
 */
import { shallow } from 'zustand/shallow';
import { resolveMotion } from '../design-system/motion';
import type { SceneStoreApi } from '../state/store';
import type { SceneController } from './SceneController';

export function attachScene(controller: SceneController, store: SceneStoreApi): () => void {
  const unsubscribes: (() => void)[] = [];
  const initial = store.getState();

  // Deep-link load is a cut regardless of motion preference (docs/CAMERA_SYSTEM.md §7).
  if (initial.selectedBasinId || initial.selectedForecastPointId) {
    controller.select({ basinId: initial.selectedBasinId, forecastPointId: initial.selectedForecastPointId }, { reason: 'deep-link', cut: true });
  }

  unsubscribes.push(
    store.subscribe(
      (s) => ({ basinId: s.selectedBasinId, forecastPointId: s.selectedForecastPointId }),
      (selection) => controller.select(selection, { reason: 'selection' }),
      { equalityFn: shallow },
    ),
    store.subscribe((s) => resolveMotion(s.motionSetting, s.systemReducedMotion), (motion) => controller.setMotion(motion), { fireImmediately: true }),
    store.subscribe((s) => s.activeLayers, (layers) => controller.setLayerIntents(layers), { fireImmediately: true }),
    store.subscribe((s) => s.experience, (choice) => controller.setExperience(choice), { fireImmediately: true }),
    controller.onQualityResolved((tier, detected) => store.getState().setQualityResolved(tier, detected)),
    controller.zoom.on('bandChanged', (e) => store.getState().setAltitudeBand(e.next)),
    controller.camera.on('started', () => store.getState().setFlightState('flying')),
    controller.camera.on('settled', () => store.getState().setFlightState('settled')),
    controller.camera.on('interrupted', () => store.getState().setFlightState('settled')),
    controller.onFollowSelect((basinId) => {
      const state = store.getState();
      if (state.selectedBasinId !== basinId) state.selectBasin(basinId);
    }),
    controller.onEmptyClick(() => {
      const state = store.getState();
      if (state.pinnedCameraId !== null) state.pinCamera(null);
    }),
    controller.onPicked((hit) => {
      const state = store.getState();
      // §12 exact semantics: a click on any NON-camera entity dismisses the preview AND
      // selects that entity (the owner's failing case was land clicks — they pick the
      // basin polygon, so the empty-click path never ran).
      if (hit.entityId.startsWith('cam:')) {
        state.pinCamera(state.pinnedCameraId === hit.entityId ? null : hit.entityId);
        return;
      }
      if (state.pinnedCameraId !== null) state.pinCamera(null);
      if (hit.entityId.startsWith('basin:')) state.selectBasin(hit.entityId);
      else if (hit.entityId.startsWith('fp:nwps:')) state.selectForecastPoint(hit.entityId, hit.basinId);
    }),
  );
  store.getState().setAltitudeBand(controller.zoom.band);

  return () => unsubscribes.forEach((u) => u());
}
