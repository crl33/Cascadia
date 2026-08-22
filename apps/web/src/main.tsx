/** Entry: seeds the store from the deep link and the reduced-motion media query, then renders. */
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './api/hooks';
import { App } from './app/App';
import { parseDeepLink } from './app/deep-link';
import { useSceneStore } from './state/store';
import './design-system/tokens.css';
import './app/app.css';

const link = parseDeepLink(window.location.search);
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
useSceneStore.setState({
  selectedBasinId: link.basinId,
  selectedForecastPointId: link.forecastPointId,
  motionSetting: link.motion ?? 'system',
  altitudeBand: link.band ?? 'orbital',
  systemReducedMotion: reducedMotionQuery.matches,
});
reducedMotionQuery.addEventListener('change', (e) => useSceneStore.getState().setSystemReducedMotion(e.matches));

// No StrictMode: its dev-only double effect would build and destroy the Cesium viewer twice.
createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>,
);
