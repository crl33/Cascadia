/** App shell: globe underneath, floating top strip and panels, persistent disclaimer. No dashboard grid. */
import { ErrorBoundary } from './ErrorBoundary';
import { SceneView } from './SceneView';
import { TopStrip } from './TopStrip';
import { UrlSync } from './UrlSync';
import { BasinPanel } from '../panels/BasinPanel';
import { RiverPanel } from '../panels/RiverPanel';
import { resolveMotion } from '../design-system/motion';
import { OSM_ATTRIBUTION } from '../layers/basemap/BasemapProvider';
import { useSceneStore } from '../state/store';

export const DISCLAIMER = 'Not an official alert authority; official forecasts and warnings come from the National Weather Service';

export function App() {
  const motion = useSceneStore((s) => resolveMotion(s.motionSetting, s.systemReducedMotion));
  return (
    <div className="app" data-motion={motion}>
      <SceneView />
      <TopStrip />
      <aside className="panels" aria-label="Intelligence panels">
        <ErrorBoundary name="Basin panel"><BasinPanel /></ErrorBoundary>
        <ErrorBoundary name="River panel"><RiverPanel /></ErrorBoundary>
      </aside>
      <footer className="disclaimer" data-testid="disclaimer">
        <span>{DISCLAIMER}.</span>
        <span className="muted"> Basemap {OSM_ATTRIBUTION}.</span>
      </footer>
      <UrlSync />
    </div>
  );
}
