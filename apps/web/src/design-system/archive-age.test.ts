/**
 * Archive age is not staleness (VISUAL_TRUTH_DOCTRINE §5.6).
 *
 * `freshness.age_seconds` is always `read clock − valid_time` (DATA_DOCTRINE §5). For a live
 * reading that is currency. For a record of December 2025 retrieved in August 2026 it is the
 * distance from TODAY — and rendering it as "STALE · age 244.2 d" beside an Event Zero cursor
 * reading 2025-12-14 invites exactly one false reading: that the observation was already 244 days
 * old at the event time. These tests pin the distinction and the words that carry it.
 */
import { describe, expect, it } from 'vitest';
import { toProvenanceFields, provIsArchived, formatArchiveAge, ARCHIVE_RETRIEVAL_LAG_SECONDS } from './provenance-record';
import type { ProvenanceRef } from '../contracts/schemas';

const ref = (over: Partial<ProvenanceRef>): ProvenanceRef => ({
  source_id: 'src:usgs-nwis-iv',
  source_kind: 'OBSERVED',
  product_id: 'product:usgs-iv',
  method_id: null,
  issued_at: null,
  valid_time: '2026-08-24T11:45:00Z',
  retrieved_at: '2026-08-24T12:00:00Z',
  freshness: { state: 'current', age_seconds: 900, expected_cadence_seconds: 900 },
  quality: ['provisional'],
  label: 'USGS instantaneous values',
  ...over,
});

/** The real Event Zero shape: the Mount Vernon record crest, retrieved 8 months later. */
const EVENT_ZERO_CREST = ref({
  valid_time: '2025-12-12T08:15:00Z',
  retrieved_at: '2026-08-24T12:00:00Z',
  quality: ['approved', 'backfilled'],
  freshness: { state: 'stale', age_seconds: 21_902_700, expected_cadence_seconds: 900 },
});

describe('provIsArchived', () => {
  it('a live reading is not archived', () => {
    expect(provIsArchived(ref({}))).toBe(false);
  });

  it('the ingestion path flagging `backfilled` is sufficient on its own', () => {
    // even with timestamps that look live, the row said what it is (ADR-0010)
    expect(provIsArchived(ref({ quality: ['approved', 'backfilled'] }))).toBe(true);
  });

  it('retrieval long after the instant described is sufficient on its own', () => {
    // a reconstructed forecast run: issued during the event, parsed out of the archive in 2026,
    // and carrying no quality flag of its own — identity comes from the timestamps
    expect(provIsArchived(ref({
      source_kind: 'OFFICIAL_FORECAST',
      valid_time: null,
      issued_at: '2025-12-09T17:01:00Z',
      retrieved_at: '2026-08-24T12:00:00Z',
      quality: [],
    }))).toBe(true);
  });

  it('falls back to issued_at when there is no valid_time, and refuses to guess without either', () => {
    expect(provIsArchived(ref({ valid_time: null, issued_at: null, retrieved_at: '2026-08-24T12:00:00Z', quality: [] }))).toBe(false);
    expect(provIsArchived(ref({ valid_time: '2025-12-12T08:15:00Z', retrieved_at: null, quality: [] }))).toBe(false);
  });

  it('the lag threshold is a week, and a normal ingestion delay does not cross it', () => {
    const lagged = (seconds: number): ProvenanceRef => ref({
      quality: [],
      valid_time: '2026-08-01T00:00:00Z',
      retrieved_at: new Date(Date.parse('2026-08-01T00:00:00Z') + seconds * 1000).toISOString(),
    });
    expect(provIsArchived(lagged(ARCHIVE_RETRIEVAL_LAG_SECONDS - 60))).toBe(false);
    expect(provIsArchived(lagged(ARCHIVE_RETRIEVAL_LAG_SECONDS + 60))).toBe(true);
  });

  it('the December crest is archived', () => {
    expect(provIsArchived(EVENT_ZERO_CREST)).toBe(true);
  });
});

describe('formatArchiveAge', () => {
  it('names the clock it is measured against', () => {
    // 253.5 d, and the words say from WHEN — never "age 253.5 d" beside a December cursor
    expect(formatArchiveAge(EVENT_ZERO_CREST.freshness)).toBe('253.5 d before today');
    expect(formatArchiveAge(EVENT_ZERO_CREST.freshness)).not.toContain('stale');
  });

  it('says so plainly when the server could not compute an age', () => {
    expect(formatArchiveAge({ state: 'stale', age_seconds: null, expected_cadence_seconds: 900 })).toBe('archive age unknown');
  });
});

describe('the inspector record for an archived value', () => {
  it('states the archive age and keeps the server word with the clock it used', () => {
    const byKey = Object.fromEntries(toProvenanceFields(EVENT_ZERO_CREST, 'observation').map((f) => [f.key, f.value]));
    expect(byKey['FRESHNESS']).toBe(
      'archived · 253.5 d before today (server state "stale": currency against today\'s clock, not age at the event time)',
    );
    // the record itself is never rewritten: the raw instants stay exactly as delivered
    expect(byKey['VALID']).toBe('2025-12-12 08:15 UTC');
    expect(byKey['RETRIEVED']).toBe('2026-08-24 12:00 UTC');
    expect(byKey['QUALITY']).toBe('approved, backfilled');
  });

  it('leaves a live value’s freshness line alone', () => {
    const byKey = Object.fromEntries(toProvenanceFields(ref({}), 'observation').map((f) => [f.key, f.value]));
    expect(byKey['FRESHNESS']).toBe('current · age 15 min · cadence 15 min');
  });
});
