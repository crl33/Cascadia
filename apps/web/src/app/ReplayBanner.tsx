/**
 * Persistent replay-honesty banner: whenever the app is in past mode it states the knowledge
 * time on screen. Every freshness badge below it shows the REPLAYED freshness the server
 * returned for that knowledge time — never client-now math (docs/VISUAL_TRUTH_DOCTRINE.md).
 */
import { formatUtc } from '../panels/format';
import { useSceneStore } from '../state/store';

export function ReplayBanner() {
  const timeline = useSceneStore((s) => s.timeline);
  if (timeline.mode !== 'past' || timeline.asOf === null) return null;
  return (
    <div className="replay-banner" role="status" data-testid="as-of-banner">
      <strong>AS OF <span className="mono">{formatUtc(timeline.asOf)}</span></strong> — replay: showing what was known then; nothing learned later is shown.
    </div>
  );
}
