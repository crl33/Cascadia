import { describe, expect, it } from 'vitest';
import { EVENTS, EVENT_ZERO_ID, eventById, eventBootTimeline, eventSearchResults, isEventId } from './registry';

const EZ = eventById(EVENT_ZERO_ID)!;

describe('event registry', () => {
  it('declares a valid Event Zero window (Dec 3–22 2025 PST as UTC bounds)', () => {
    expect(EZ.window[0]).toBe('2025-12-03T08:00:00Z');
    expect(EZ.window[1]).toBe('2025-12-23T08:00:00Z');
    expect(Date.parse(EZ.window[0])).toBeLessThan(Date.parse(EZ.window[1]));
    expect(isEventId(EVENT_ZERO_ID)).toBe(true);
    expect(isEventId('event-nope')).toBe(false);
    for (const event of EVENTS) {
      expect(Date.parse(event.defaultAt)).toBeGreaterThanOrEqual(Date.parse(event.window[0]));
      expect(Date.parse(event.defaultAt)).toBeLessThanOrEqual(Date.parse(event.window[1]));
    }
  });

  describe('eventBootTimeline (window anchoring)', () => {
    it('anchors the timeline window to the event window, never the live 72 h window', () => {
      expect(eventBootTimeline(EZ, null)).toEqual({
        mode: 'event', asOf: null, window: EZ.window, eventId: EVENT_ZERO_ID, at: EZ.defaultAt,
      });
    });
    it('clamps a deep-linked at into the window and truncates to the minute', () => {
      expect(eventBootTimeline(EZ, '2025-12-12T08:15:30Z').at).toBe('2025-12-12T08:15:00Z');
      expect(eventBootTimeline(EZ, '2024-01-01T00:00:00Z').at).toBe(EZ.window[0]);
      expect(eventBootTimeline(EZ, '2026-08-24T00:00:00Z').at).toBe(EZ.window[1]);
    });
    it('falls back to the default cursor on an unparseable at', () => {
      expect(eventBootTimeline(EZ, 'yesterday').at).toBe(EZ.defaultAt);
    });
    it('event mode never carries a knowledge time (asOf stays null)', () => {
      expect(eventBootTimeline(EZ, '2025-12-12T08:15:00Z').asOf).toBeNull();
    });
  });

  it('offers the event as a client-side search result only for matching queries', () => {
    expect(eventSearchResults('december').map((r) => r.id)).toEqual([EVENT_ZERO_ID]);
    expect(eventSearchResults('Event Zero')).toHaveLength(1);
    expect(eventSearchResults('flood replay')).toHaveLength(1);
    expect(eventSearchResults('skag')).toEqual([]);
  });
});
