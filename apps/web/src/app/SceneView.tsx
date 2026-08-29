/**
 * SceneView: the ref-held container in which SceneController builds the viewer once. If the
 * renderer cannot start (no WebGL), a static fallback is shown and the panels keep working.
 * This is the only React component that touches scene/ (and it never touches Cesium).
 */
import { useEffect, useRef, useState } from 'react';
import { resolveMotion } from '../design-system/motion';
import { resolveBasemap } from '../layers/basemap/BasemapProvider';
import { attachScene } from '../scene/bridge';
import { SceneController } from '../scene/SceneController';
import { useSceneStore } from '../state/store';
import { CameraPreviewHost } from './CameraPreviewHost';
import { LoadingVeil } from './LoadingVeil';
import { SceneDataBridge } from './SceneDataBridge';

export function SceneView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [controller, setController] = useState<SceneController | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [degraded, setDegraded] = useState<string | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let created: SceneController | null = null;
    let detach = () => {};
    let detachErrors = () => {};
    try {
      const state = useSceneStore.getState();
      created = new SceneController(container, { motion: resolveMotion(state.motionSetting, state.systemReducedMotion), basemap: resolveBasemap() });
      detach = attachScene(created, useSceneStore);
      detachErrors = created.onRenderError((message) => setDegraded(message));
      setController(created);
    } catch (error) {
      console.error('renderer unavailable', error);
      setFailure(error instanceof Error ? error.message : String(error));
    }
    return () => {
      detachErrors();
      detach();
      created?.dispose();
      setController(null);
    };
  }, []);

  return (
    <div className="scene" data-testid="scene" data-scene-state={failure ? 'unavailable' : degraded ? 'degraded' : controller ? 'ready' : 'booting'}>
      <div ref={containerRef} className="scene-canvas" data-testid="scene-canvas" />
      {failure ? (
        <div className="scene-fallback" role="status" data-testid="scene-fallback">
          <p><strong>3D renderer unavailable</strong> (WebGL could not start). Intelligence panels, search and provenance still work.</p>
          <p className="mono muted">{failure}</p>
        </div>
      ) : null}
      {degraded ? (
        <div className="scene-degraded" role="status" data-testid="scene-degraded">
          <strong>Renderer degraded</strong> — rendering stopped: <span className="mono">{degraded}</span>. Panels and provenance remain authoritative.
        </div>
      ) : null}
      <LoadingVeil controller={controller} />
      {controller ? <SceneDataBridge controller={controller} /> : null}
      {controller ? <CameraPreviewHost controller={controller} /> : null}
    </div>
  );
}
