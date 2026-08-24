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

export const SOURCE_KIND_BADGE: Record<SourceKind, BadgeDescriptor> = {
  OBSERVED: { label: 'OBSERVED', glyph: '●', tone: 'cyan', pattern: 'solid' },
  OFFICIAL_FORECAST: { label: 'OFFICIAL FORECAST', glyph: '◆', tone: 'glacier', pattern: 'solid' },
  MODELED: { label: 'MODELED', glyph: '◇', tone: 'secondary', pattern: 'dashed' },
  DERIVED: { label: 'DERIVED', glyph: '△', tone: 'muted', pattern: 'dotted' },
  EXPERIMENTAL: { label: 'EXPERIMENTAL', glyph: '✶', tone: 'amber-watch', pattern: 'striped' },
  CONFIGURED: { label: 'CONFIGURED', glyph: '⚙', tone: 'muted', pattern: 'dashed' },
  UNKNOWN: { label: 'UNKNOWN', glyph: '?', tone: 'neutral', pattern: 'dotted' },
};

export const badgeForSourceKind = (kind: SourceKind): BadgeDescriptor => SOURCE_KIND_BADGE[kind];

/** Flood category word + tone. Red is earned only by moderate/major official categories. */
export const CATEGORY_BADGE: Record<FloodCategory, BadgeDescriptor> = {
  none: { label: 'NONE', glyph: '·', tone: 'cyan', pattern: 'solid' },
  action: { label: 'ACTION', glyph: '▲', tone: 'amber-watch', pattern: 'solid' },
  minor: { label: 'MINOR', glyph: '▲', tone: 'amber-elevated', pattern: 'solid' },
  moderate: { label: 'MODERATE', glyph: '▲▲', tone: 'flood-red', pattern: 'solid' },
  major: { label: 'MAJOR', glyph: '▲▲▲', tone: 'flood-red', pattern: 'solid' },
  unknown: { label: 'UNKNOWN', glyph: '?', tone: 'neutral', pattern: 'dotted' },
};

export const FRESHNESS_BADGE: Record<FreshnessState, BadgeDescriptor> = {
  current: { label: 'CURRENT', glyph: '✓', tone: 'cyan', pattern: 'solid' },
  stale: { label: 'STALE', glyph: '⏱', tone: 'amber-watch', pattern: 'dashed' },
  degraded: { label: 'DEGRADED', glyph: '!', tone: 'amber-elevated', pattern: 'dashed' },
  missing: { label: 'MISSING', glyph: '∅', tone: 'neutral', pattern: 'dotted' },
  partial: { label: 'PARTIAL', glyph: '◐', tone: 'muted', pattern: 'dotted' },
  unknown: { label: 'UNKNOWN', glyph: '?', tone: 'neutral', pattern: 'dotted' },
};

/**
 * Backfilled archive values (ADR-0010): retrieved long after the historical instant; never
 * styled as live. Word + glyph, never colour alone.
 */
export const BACKFILLED_BADGE: BadgeDescriptor = { label: 'BACKFILLED', glyph: '⧗', tone: 'amber-watch', pattern: 'dashed' };
