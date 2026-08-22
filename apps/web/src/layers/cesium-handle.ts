/** The concrete SceneHandle: only scene/ and layers/* may see the Viewer behind the brand. */
import type { Viewer } from 'cesium';
import type { SceneHandle } from './contract';

interface CesiumSceneHandle extends SceneHandle { readonly viewer: Viewer }

export const createSceneHandle = (viewer: Viewer): SceneHandle => ({ __brand: 'SceneHandle', viewer }) as CesiumSceneHandle;
export const viewerOf = (handle: SceneHandle): Viewer => (handle as CesiumSceneHandle).viewer;
