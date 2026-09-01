/** App shell: globe underneath, floating top strip, panels, timeline bar, persistent disclaimer. No dashboard grid. */
import { useEffect, useState } from 'react';
import { queryClient } from '../api/hooks';
import { ErrorBoundary } from './ErrorBoundary';
import { ReplayBanner } from './ReplayBanner';
import { SceneView } from './SceneView';
import { TopStrip } from './TopStrip';
import { UrlSync } from './UrlSync';
import { EventBanner } from '../event/EventBanner';
import { ForecastEvolution } from '../event/ForecastEvolution';
import { BasinPanel } from '../panels/BasinPanel';
import { RiverPanel } from '../panels/RiverPanel';
import { resolveMotion } from '../design-system/motion';
import { setRefractionQuality } from '../design-system/refraction';
import { resolveBasemap } from '../layers/basemap/BasemapProvider';
import { useSceneStore } from '../state/store';
import { FieldLegend } from './FieldLegend';
import { TimelineBar } from '../timeline/TimelineBar';
import { TimelineController } from '../timeline/TimelineController';

export const DISCLAIMER = 'Not an official alert authority; official forecasts and warnings come from the National Weather Service';

export function App() {
  const motion = useSceneStore((s) => resolveMotion(s.motionSetting, s.systemReducedMotion));
  const qualityTier = useSceneStore((s) => s.qualityTier);
  const [timelineController] = useState(() => new TimelineController(useSceneStore, queryClient));
  useEffect(() => () => timelineController.dispose(), [timelineController]);
  // Quality tier fans out once, at the root: CSS reads <html data-quality>; the refraction
  // module re-tunes or strips its Chromium enhancement (mission §31).
  useEffect(() => {
    document.documentElement.dataset.quality = qualityTier;
    setRefractionQuality(qualityTier);
  }, [qualityTier]);
  return (
    <div className="app" data-motion={motion}>
      <SceneView />
      <TopStrip />
      <ReplayBanner />
      <EventBanner />
      <aside className="panels" aria-label="Intelligence panels">
        <ErrorBoundary name="Basin panel"><BasinPanel /></ErrorBoundary>
        <ErrorBoundary name="River panel"><RiverPanel /></ErrorBoundary>
        <ErrorBoundary name="Forecast evolution"><ForecastEvolution /></ErrorBoundary>
      </aside>
      <ErrorBoundary name="Field legend"><FieldLegend /></ErrorBoundary>
      <ErrorBoundary name="Timeline"><TimelineBar controller={timelineController} /></ErrorBoundary>
      <footer className="disclaimer glass-surface glass-compact shape-control" data-testid="disclaimer">
        <span>{DISCLAIMER}.</span>
        <span className="muted"> Imagery: {resolveBasemap().attribution}. Terrain: USGS 3DEP.</span>
      </footer>
      <UrlSync />
    </div>
  );
}
