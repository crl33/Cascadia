/**
 * EventBanner: the event-replay honesty statement (docs/VISUAL_TRUTH_DOCTRINE.md; ADR-0010).
 * Visible exactly when the timeline is in event mode. It states the EVENT time (a valid/issued
 * time — not a knowledge time) and that the archive was retrieved in 2026-08: forecast
 * issuance times are exact product header times; retrieval knowledge times are not historical.
 */
import { eventById } from './registry';
import { formatUtc } from '../panels/format';
import { useSceneStore } from '../state/store';

export function EventBanner() {
  const timeline = useSceneStore((s) => s.timeline);
  if (timeline.mode !== 'event' || timeline.eventId === null) return null;
  const event = eventById(timeline.eventId);
  return (
    <div className="replay-banner event-banner" role="status" data-testid="event-banner">
      <strong>EVENT REPLAY — {event?.label ?? timeline.eventId}</strong>
      {' · event time '}
      <span className="mono">{formatUtc(timeline.at)}</span>
      {' — reconstructed from archived data retrieved 2026-08; forecast issuance times are exact, retrieval knowledge times are not historical.'}
    </div>
  );
}
