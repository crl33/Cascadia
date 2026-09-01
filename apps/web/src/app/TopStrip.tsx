/**
 * Thin top strip — product chrome only (mission §19–20): wordmark, search, data-feed
 * health, settings. The internals the strip used to expose (semantic band, flight state,
 * motion plumbing) are not product concepts; they remain as invisible diagnostic stamps
 * because tests and tooling read them, but no human is asked to learn them.
 */
import { useHealth } from '../api/hooks';
import { resolveMotion } from '../design-system/motion';
import { SearchBox } from '../interactions/SearchBox';
import { useSceneStore } from '../state/store';
import { SettingsMenu } from './SettingsMenu';

const HEALTH_TITLE: Record<string, string> = {
  ok: 'Data feeds: healthy',
  degraded: 'Data feeds: degraded — some sources are late',
  down: 'Data feeds: unreachable',
  unknown: 'Data feeds: checking…',
};

export function TopStrip() {
  const band = useSceneStore((s) => s.altitudeBand);
  const motionSetting = useSceneStore((s) => s.motionSetting);
  const systemReduced = useSceneStore((s) => s.systemReducedMotion);
  const flightState = useSceneStore((s) => s.flightState);
  const health = useHealth();
  const resolved = resolveMotion(motionSetting, systemReduced);
  const healthState = health.isError ? 'down' : health.data?.status ?? 'unknown';

  return (
    <header className="top-strip glass-surface glass-chrome shape-control">
      <span className="wordmark">Cascadia Papsukkal</span>
      <SearchBox />
      <span className="top-strip-spacer" aria-hidden="true" />
      {/* Diagnostic stamps: read by tests/tooling, never shown — internals are not chrome. */}
      <span className="visually-hidden" data-testid="band-indicator">{band.toUpperCase()}</span>
      <span className="visually-hidden" data-testid="flight-state" data-flight-state={flightState}>{flightState}</span>
      <span className="visually-hidden" data-testid="motion-toggle" data-motion={resolved} />
      <span
        className={`health-dot health-${healthState}`}
        data-testid="health-dot"
        title={HEALTH_TITLE[healthState] ?? HEALTH_TITLE.unknown}
        role="status"
      >
        <span className="visually-hidden">{HEALTH_TITLE[healthState] ?? HEALTH_TITLE.unknown}</span>
      </span>
      <SettingsMenu />
    </header>
  );
}
