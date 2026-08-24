/** Entry: seeds the store from the deep link and the reduced-motion media query, then renders. */
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './api/hooks';
import { App } from './app/App';
import { parseDeepLink } from './app/deep-link';
import { useSceneStore } from './state/store';
import { anchorForBoot, truncateToMinute, windowEndingAt } from './timeline/window';
import './design-system/tokens.css';
import './app/app.css';

const link = parseDeepLink(window.location.search);
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

// `cam` wins over `sel` for framing (docs/CAMERA_SYSTEM.md §7): an entity anchor with no
// selection of its own kind seeds the selection so the existing deep-link cut frames it.
// Free (g:) anchors and range/heading/pitch application need a CameraController restore API
// (camera workstream); until then the pose is not kept in the store, so the URL never claims
// a camera view that is not actually shown.
const camEntityId = link.cam !== null && link.cam.anchor.kind === 'entity' ? link.cam.anchor.id : null;
const basinId = link.basinId ?? (camEntityId?.startsWith('basin:') ? camEntityId : null);
const forecastPointId = link.forecastPointId ?? (camEntityId?.startsWith('fp:nwps:') ? camEntityId : null);

// Replay knowledge time is minute-aligned (timeline/window.ts); the window anchors at now,
// or at as_of when it predates the live 72 h window.
const asOf = link.asOf === null ? null : truncateToMinute(link.asOf);
const window72h = windowEndingAt(anchorForBoot(asOf, new Date().toISOString()));

useSceneStore.setState({
  selectedBasinId: basinId,
  selectedForecastPointId: forecastPointId,
  motionSetting: link.motion ?? 'system',
  altitudeBand: link.band ?? 'orbital',
  systemReducedMotion: reducedMotionQuery.matches,
  timeline: { mode: asOf === null ? 'now' : 'past', asOf, window: window72h },
});
reducedMotionQuery.addEventListener('change', (e) => useSceneStore.getState().setSystemReducedMotion(e.matches));

// No StrictMode: its dev-only double effect would build and destroy the Cesium viewer twice.
createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
);
