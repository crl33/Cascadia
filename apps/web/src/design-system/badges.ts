/**
 * Provenance badge descriptors: source_kind -> label + glyph + tone. Colour is never the only
 * carrier (docs/VISUAL_TRUTH_DOCTRINE.md §7.2): every badge prints its word and a glyph. This is
 * the single mapping both panels and layer labels use; the test asserts totality.
 */
import type { SourceKind, FloodCategory, FreshnessState } from '../contracts/schemas';

export type BadgeTone = 'cyan' | 'glacier' | 'secondary' | 'muted' | 'amber-watch' | 'amber-elevated' | 'flood-red' | 'neutral';

export interface BadgeDescriptor {
  label: string;
  glyph: string;
  tone: BadgeTone;
  pattern: 'solid' | 'dashed' | 'dotted' | 'striped';
}

/** Labels speak human (mission §17–18): the formal truth class stays in the contract and
 * the inspector; the chip carries a word a first-time reader understands. EXPERIMENTAL is
 * Cascadia's own derived intelligence — it headlines as the platform's assessment, and the
 * inspector says "experimental methodology" (§18's maturation path needs no redesign). */
export const SOURCE_KIND_BADGE: Record<SourceKind, BadgeDescriptor> = {
  OBSERVED: { label: 'Observed', glyph: '●', tone: 'cyan', pattern: 'solid' },
  OFFICIAL_FORECAST: { label: 'Official forecast', glyph: '◆', tone: 'glacier', pattern: 'solid' },
  MODELED: { label: 'Model', glyph: '◇', tone: 'secondary', pattern: 'dashed' },
  DERIVED: { label: 'Derived', glyph: '△', tone: 'muted', pattern: 'dotted' },
  EXPERIMENTAL: { label: 'Cascadia assessment', glyph: '✶', tone: 'amber-watch', pattern: 'striped' },
  CONFIGURED: { label: 'Configured', glyph: '⚙', tone: 'muted', pattern: 'dashed' },
  UNKNOWN: { label: 'Unknown', glyph: '?', tone: 'neutral', pattern: 'dotted' },
};

export const badgeForSourceKind = (kind: SourceKind): BadgeDescriptor => SOURCE_KIND_BADGE[kind];

/** Flood category word + tone. Red is earned only by moderate/major official categories. */
export const CATEGORY_BADGE: Record<FloodCategory, BadgeDescriptor> = {
  none: { label: 'None', glyph: '·', tone: 'cyan', pattern: 'solid' },
  action: { label: 'Action', glyph: '▲', tone: 'amber-watch', pattern: 'solid' },
  minor: { label: 'Minor', glyph: '▲', tone: 'amber-elevated', pattern: 'solid' },
  moderate: { label: 'Moderate', glyph: '▲▲', tone: 'flood-red', pattern: 'solid' },
  major: { label: 'Major', glyph: '▲▲▲', tone: 'flood-red', pattern: 'solid' },
  unknown: { label: 'Unknown', glyph: '?', tone: 'neutral', pattern: 'dotted' },
};

export const FRESHNESS_BADGE: Record<FreshnessState, BadgeDescriptor> = {
  current: { label: 'Current', glyph: '✓', tone: 'cyan', pattern: 'solid' },
  stale: { label: 'Stale', glyph: '⏱', tone: 'amber-watch', pattern: 'dashed' },
  degraded: { label: 'Degraded', glyph: '!', tone: 'amber-elevated', pattern: 'dashed' },
  missing: { label: 'Missing', glyph: '∅', tone: 'neutral', pattern: 'dotted' },
  partial: { label: 'Partial', glyph: '◐', tone: 'muted', pattern: 'dotted' },
  unknown: { label: 'Unknown', glyph: '?', tone: 'neutral', pattern: 'dotted' },
};

/**
 * Backfilled archive values (ADR-0010): retrieved long after the historical instant; never
 * styled as live. Word + glyph, never colour alone.
 */
export const BACKFILLED_BADGE: BadgeDescriptor = { label: 'Backfilled', glyph: '⧗', tone: 'amber-watch', pattern: 'dashed' };

/**
 * Occupies the freshness slot for an ARCHIVED value instead of CURRENT/STALE. A record of a past
 * instant is not a live feed that has fallen behind: `stale` is a fault word (DATA_DOCTRINE §5 —
 * ingestion is late), while an archive is old on purpose. Rendering STALE beside a December 2025
 * crest invites reading the age as the value's age *at the event time*, which it is not: the age
 * is always measured from the read clock (VISUAL_TRUTH_DOCTRINE §5.6).
 */
export const ARCHIVED_BADGE: BadgeDescriptor = { label: 'Archived', glyph: '▤', tone: 'muted', pattern: 'dashed' };
