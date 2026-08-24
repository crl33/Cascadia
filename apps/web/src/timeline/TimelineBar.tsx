/**
 * TimelineBar: the bottom scrub bar for replay time. In live/past mode dragging replays the
 * past 72 h of KNOWLEDGE time through the TimelineController (one store commit per frame;
 * superseded requests aborted); in event mode the same slider scrubs the archived EVENT
 * window in EVENT time (valid/issued time — no as_of anywhere; see event/registry). The chip
 * states the mode (NOW live / AS OF <time> past / EVENT REPLAY); NOW returns to live from
 * either replay. The readout prints the position in UTC and local time. No value is ever
 * animated — time is data, and the replayed freshness on every badge comes from the server
 * document, never from client-now math.
 */
import type { ChangeEvent } from 'react';
import { eventById } from '../event/registry';
import { formatUtc } from '../panels/format';
import { useSceneStore } from '../state/store';
import type { TimelineController } from './TimelineController';
import { SCRUB_STEP_MS } from './window';
import './timeline.css';

interface TimelineBarProps { controller: TimelineController }

const localLabel = (ms: number): string =>
  new Date(ms).toLocaleString(undefined, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });

export function TimelineBar({ controller }: TimelineBarProps) {
  const timeline = useSceneStore((s) => s.timeline);
  const event = timeline.mode === 'event' && timeline.eventId !== null ? eventById(timeline.eventId) : null;
  const startMs = Date.parse(timeline.window[0]);
  const endMs = Date.parse(timeline.window[1]);
  const positionIso = (timeline.mode === 'event' ? timeline.at : timeline.asOf) ?? timeline.window[1];
  const positionMs = Date.parse(positionIso);
  const onScrub = (changeEvent: ChangeEvent<HTMLInputElement>) => {
    const iso = new Date(Number(changeEvent.currentTarget.value)).toISOString();
    if (timeline.mode === 'event') controller.scrubEvent(iso);
    else controller.scrub(iso);
  };
  const chip = timeline.mode === 'now'
    ? 'NOW · live'
    : timeline.mode === 'past'
      ? `AS OF ${formatUtc(timeline.asOf)} · past`
      : `EVENT REPLAY · ${event?.chipLabel ?? timeline.eventId}`;

  return (
    <div className="timeline-bar" data-testid="timeline" data-mode={timeline.mode} role="group" aria-label="Timeline">
      <span className={`timeline-chip mono timeline-chip-${timeline.mode}`} data-testid="timeline-mode-chip">
        {chip}
      </span>
      <span className="timeline-edge mono" data-testid="timeline-window-start">{formatUtc(timeline.window[0])}</span>
      <input
        type="range"
        className="timeline-scrubber"
        data-testid="timeline-scrubber"
        min={startMs}
        max={endMs}
        step={SCRUB_STEP_MS}
        value={positionMs}
        aria-label={timeline.mode === 'event' ? 'Event time (scrub the archived event window)' : 'Knowledge time (scrub the past 72 hours)'}
        aria-valuetext={`${formatUtc(positionIso)} (${localLabel(positionMs)} local)`}
        onChange={onScrub}
      />
      <span className="timeline-edge mono" data-testid="timeline-window-end">{formatUtc(timeline.window[1])}</span>
      <span className="timeline-readout mono" data-testid="timeline-readout">
        {formatUtc(positionIso)} · {localLabel(positionMs)} local
      </span>
      <button
        type="button"
        className="timeline-now link-button"
        data-testid="snap-to-now"
        onClick={() => controller.snapToNow()}
        disabled={timeline.mode === 'now'}
        title={timeline.mode === 'event' ? 'Exit event replay to live NOW' : 'Return to live NOW'}
      >
        NOW
      </button>
    </div>
  );
}
