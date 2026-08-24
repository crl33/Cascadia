/**
 * Event replay registry (P2 Event Zero; docs/EVENT_ZERO.md, docs/CINEMATIC_ROADMAP.md §11).
 * Navigation configuration ONLY — ids, labels, window bounds and default framing cited from
 * docs/EVENT_ZERO.md; no science, no fabricated values. The event window is scrubbed in EVENT
 * time (valid/issued time). Queries in event mode carry NO as_of: backfilled archive rows have
 * available_at = retrieval time (ADR-0010), so a knowledge-time replay at a 2025 instant would
 * honestly return UNKNOWN — the event experience selects by valid/issued-time windows instead
 * and says so on the EventBanner.
 */
import type { TimelineState } from '../state/store';
import { clampToWindow, truncateToMinute, type TimelineWindow } from '../timeline/window';

export interface EventDescriptor {
  readonly id: string;
  readonly label: string;
  /** Short chip text for the timeline bar. */
  readonly chipLabel: string;
  /** Event window in EVENT time (UTC ISO). Dec 3–22 2025 PST as UTC bounds. */
  readonly window: TimelineWindow;
  readonly defaultSel: string;
  readonly defaultBasin: string;
  /** Boot cursor: the first MVEW1 FLW issuance (EVENT_ZERO §5 #25). */
  readonly defaultAt: string;
  /** Where the bounds come from — a doc citation, never a computed value. */
  readonly source: string;
}

export const EVENT_ZERO_ID = 'event-zero-2025-12';

export const EVENTS: readonly EventDescriptor[] = [
  {
    id: EVENT_ZERO_ID,
    label: 'December 2025 flood — Event Zero',
    chipLabel: 'Dec 2025',
    window: ['2025-12-03T08:00:00Z', '2025-12-23T08:00:00Z'],
    defaultSel: 'fp:nwps:MVEW1',
    defaultBasin: 'basin:skagit',
    defaultAt: '2025-12-09T17:01:00Z',
    source: 'docs/EVENT_ZERO.md (§2 event span, §5 #25 first MVEW1 FLW, §8 golden table)',
  },
];

export const eventById = (id: string): EventDescriptor | null => EVENTS.find((e) => e.id === id) ?? null;
export const isEventId = (id: string): boolean => eventById(id) !== null;

/**
 * The timeline state an event boots (or is entered) with: window = the event window; the
 * cursor `at` = the deep-linked instant clamped into it (minute-aligned), or the descriptor's
 * default; asOf stays null — event mode never routes through knowledge time.
 */
export function eventBootTimeline(event: EventDescriptor, at: string | null): TimelineState {
  let cursor = event.defaultAt;
  if (at !== null) {
    try {
      cursor = clampToWindow(truncateToMinute(at), event.window);
    } catch {
      cursor = event.defaultAt;
    }
  }
  return { mode: 'event', asOf: null, window: event.window, eventId: event.id, at: cursor };
}

/** Client-side search entry for an event replay (no API change; see interactions/SearchBox). */
export interface EventSearchResult {
  readonly kind: 'event';
  readonly id: string;
  readonly name: string;
}

const EVENT_QUERY = /event|zero|december|2025|flood/i;

/** Synthetic search results offered when the query names the event. */
export const eventSearchResults = (query: string): EventSearchResult[] =>
  EVENT_QUERY.test(query) ? EVENTS.map((e) => ({ kind: 'event' as const, id: e.id, name: e.label })) : [];
