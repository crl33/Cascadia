/**
 * TimelineBar: ONE temporal mental model (mission §21). The user sees local time, once.
 *
 *   LIVE     `LIVE` chip · slider at the right edge · "Aug 31 · 4:58 PM"
 *   PAST     `AS OF` chip · slider in the window · "Aug 30 · 1:35 PM · 27 h ago" — the
 *            top banner explains replay semantics; this bar never repeats the timestamp
 *   EVENT    archived replay — edges become ABSOLUTE dates (an event window is not
 *            relative to now), chip names the event
 *
 * Edge labels are relative (−72 h ↔ now) in live/past, absolute UTC only in event mode.
 * Full UTC stays available on hover/aria (technical register), never as chrome text.
 * No value is ever animated — time is data.
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
  new Date(ms).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });

const agoLabel = (ms: number, nowMs: number): string => {
  const hours = Math.round((nowMs - ms) / 3_600_000);
  return hours <= 0 ? 'now' : `${hours} h ago`;
};

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

  const chip = timeline.mode === 'now' ? 'LIVE' : timeline.mode === 'past' ? 'AS OF' : `EVENT REPLAY · ${event?.chipLabel ?? timeline.eventId}`;
  const eventMode = timeline.mode === 'event';
  const readout =
    timeline.mode === 'past' ? `${localLabel(positionMs)} · ${agoLabel(positionMs, endMs)}` : localLabel(positionMs);

  return (
    <div className="timeline-bar glass-surface glass-chrome shape-capsule" data-occlusion="timeline" data-testid="timeline" data-mode={timeline.mode} role="group" aria-label="Timeline">
      <span className={`timeline-chip mono timeline-chip-${timeline.mode}`} data-testid="timeline-mode-chip">
        {chip}
      </span>
      <span className="timeline-edge mono" data-testid="timeline-window-start" title={formatUtc(timeline.window[0])}>
        {eventMode ? formatUtc(timeline.window[0]) : '−72 h'}
      </span>
      <input
        type="range"
        className="timeline-scrubber"
        data-testid="timeline-scrubber"
        min={startMs}
        max={endMs}
        step={SCRUB_STEP_MS}
        value={positionMs}
        aria-label={eventMode ? 'Event time (scrub the archived event window)' : 'Knowledge time (scrub the past 72 hours)'}
        aria-valuetext={`${formatUtc(positionIso)} (${localLabel(positionMs)} local)`}
        onChange={onScrub}
      />
      <span className="timeline-edge mono" data-testid="timeline-window-end" title={formatUtc(timeline.window[1])}>
        {eventMode ? formatUtc(timeline.window[1]) : 'now'}
      </span>
      <span className="timeline-readout mono" data-testid="timeline-readout" title={formatUtc(positionIso)}>
        {readout}
      </span>
      {timeline.mode === 'now' ? null : (
        <button
          type="button"
          className="timeline-now link-button"
          data-testid="snap-to-now"
          onClick={() => controller.snapToNow()}
          title={eventMode ? 'Exit event replay to live' : 'Return to live'}
        >
          NOW
        </button>
      )}
    </div>
  );
}
