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

export function toProvenanceFields(prov: ProvenanceRef, truth: TruthClass | null): ProvenanceField[] {
  const isObservation = prov.source_kind === 'OBSERVED';
  return [
    { key: 'SOURCE', value: `${[prov.source_id, prov.product_id].filter(Boolean).join(' · ')} — ${prov.label}` },
    { key: 'KIND', value: prov.source_kind.replace(/_/g, ' ').toLowerCase() },
    { key: 'TRUTH', value: truth ? TRUTH_WORDS[truth] : 'not stated' },
    { key: 'PRODUCT', value: prov.product_id ?? '—' },
    { key: 'METHOD', value: prov.method_id ?? 'none (untransformed)' },
    { key: 'ISSUED', value: isObservation ? 'n/a (observation)' : formatInstantUtc(prov.issued_at) },
    { key: 'VALID', value: formatInstantUtc(prov.valid_time) },
    { key: 'RETRIEVED', value: formatInstantUtc(prov.retrieved_at) },
    { key: 'FRESHNESS', value: formatFreshnessLine(prov.freshness) },
    { key: 'QUALITY', value: prov.quality && prov.quality.length > 0 ? prov.quality.join(', ') : '—' },
    { key: 'RAW ARTIFACT', value: prov.raw_artifact_id ?? '—' },
  ];
}
