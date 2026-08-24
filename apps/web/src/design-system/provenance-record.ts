/**
 * toProvenanceFields: the full per-value provenance record the popover inspector renders
 * (VISUAL_TRUTH_DOCTRINE §6): SOURCE, KIND, TRUTH, PRODUCT, METHOD, ISSUED, VALID, RETRIEVED,
 * FRESHNESS, QUALITY, RAW ARTIFACT. Pure derivation from a ProvenanceRef; it never computes
 * science and never invents a value — absent fields print as "—" or an explicit "n/a".
 * Formatting helpers are local because design-system may import contracts types only
 * (apps/web/AGENTS.md); they mirror panels/format.ts.
 */
import type { Freshness, ProvenanceRef, TruthClass } from '../contracts/schemas';

export interface ProvenanceField {
  key: string;
  value: string;
}

const TRUTH_WORDS: Record<TruthClass, string> = {
  observation: 'A · observation',
  authoritative_model: 'B · authoritative model',
  cascade_derived: 'C · Cascade-derived',
  cartographic: 'D · cartographic',
  cinematic: 'E · cinematic',
};

const formatInstantUtc = (iso: string | null | undefined): string => {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return `${date.toISOString().slice(0, 16).replace('T', ' ')} UTC`;
};

const formatAgeSeconds = (seconds: number | null | undefined): string => {
  if (seconds == null) return 'unknown';
  if (seconds < 90) return `${seconds} s`;
  if (seconds < 5400) return `${Math.round(seconds / 60)} min`;
  if (seconds < 172800) return `${(seconds / 3600).toFixed(1)} h`;
  return `${(seconds / 86400).toFixed(1)} d`;
};

const formatFreshnessLine = (freshness: Freshness): string => {
  const parts = [`${freshness.state}`, `age ${formatAgeSeconds(freshness.age_seconds)}`];
  if (freshness.expected_cadence_seconds != null) parts.push(`cadence ${formatAgeSeconds(freshness.expected_cadence_seconds)}`);
  return parts.join(' · ');
};

/** Retrieval this long after the instant described means the value came out of an archive. */
export const ARCHIVE_RETRIEVAL_LAG_SECONDS = 7 * 24 * 3600;

/**
 * Is this value an archived record rather than a live reading?
 *
 * Decided from the value's OWN provenance, not from the app's mode, so a December observation is
 * an archive value wherever it is shown and a live reading stays live inside Event Zero (where
 * some panel rows are still live). Two independent signals, either sufficient: the ingestion path
 * flagged the row `backfilled` (ADR-0010), or it was retrieved long after the instant it
 * describes — the shape of every reconstruction (issued December 2025, retrieved August 2026).
 */
export function provIsArchived(prov: ProvenanceRef): boolean {
  if (prov.quality?.includes('backfilled')) return true;
  const anchor = prov.valid_time ?? prov.issued_at;
  if (anchor == null || prov.retrieved_at == null) return false;
  const lagSeconds = (Date.parse(prov.retrieved_at) - Date.parse(anchor)) / 1000;
  return Number.isFinite(lagSeconds) && lagSeconds > ARCHIVE_RETRIEVAL_LAG_SECONDS;
}

/**
 * The age of an archived value, said in the only terms that are true of it. `age_seconds` is
 * always `read clock − valid_time` (DATA_DOCTRINE §5), so for an archive it measures distance
 * from TODAY — never how old the value was at the event time being replayed. The word "before
 * today" is the whole point: it names the clock at the point of use.
 */
export function formatArchiveAge(freshness: Freshness): string {
  return freshness.age_seconds == null ? 'archive age unknown' : `${formatAgeSeconds(freshness.age_seconds)} before today`;
}

export function toProvenanceFields(prov: ProvenanceRef, truth: TruthClass | null): ProvenanceField[] {
  const isObservation = prov.source_kind === 'OBSERVED';
  const isArchived = provIsArchived(prov);
  return [
    { key: 'SOURCE', value: `${[prov.source_id, prov.product_id].filter(Boolean).join(' · ')} — ${prov.label}` },
    { key: 'KIND', value: prov.source_kind.replace(/_/g, ' ').toLowerCase() },
    { key: 'TRUTH', value: truth ? TRUTH_WORDS[truth] : 'not stated' },
    { key: 'PRODUCT', value: prov.product_id ?? '—' },
    { key: 'METHOD', value: prov.method_id ?? 'none (untransformed)' },
    { key: 'ISSUED', value: isObservation ? 'n/a (observation)' : formatInstantUtc(prov.issued_at) },
    { key: 'VALID', value: formatInstantUtc(prov.valid_time) },
    { key: 'RETRIEVED', value: formatInstantUtc(prov.retrieved_at) },
    {
      key: 'FRESHNESS',
      // For an archive, the inspector states the archive age and keeps the server's own word
      // visible with the clock it was measured against — the record is never rewritten, only
      // explained (VISUAL_TRUTH_DOCTRINE §5.6).
      value: isArchived
        ? `archived · ${formatArchiveAge(prov.freshness)} (server state "${prov.freshness.state}": currency against today's clock, not age at the event time)`
        : formatFreshnessLine(prov.freshness),
    },
    { key: 'QUALITY', value: prov.quality && prov.quality.length > 0 ? prov.quality.join(', ') : '—' },
    { key: 'RAW ARTIFACT', value: prov.raw_artifact_id ?? '—' },
  ];
}
