/**
 * toInspectorRecord: pure derivation of the layer-inspector lines (VISUAL_TRUTH_DOCTRINE §6)
 * from a ProvenanceRef and a truth class. SOURCE, TYPE, TRUTH, VALID, ISSUED, RETRIEVED,
 * FRESHNESS, QUALITY, METHOD. It never computes science.
 */
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import { formatFreshness, formatUtc, words } from './format';

export interface InspectorLine { key: string; value: string }

const TRUTH_WORDS: Record<TruthClass, string> = {
  observation: 'A · observation',
  authoritative_model: 'B · authoritative model',
  cascade_derived: 'C · Cascade-derived',
  cartographic: 'D · cartographic',
  cinematic: 'E · cinematic',
};

export function toInspectorRecord(prov: ProvenanceRef, truth: TruthClass | null): InspectorLine[] {
  const isObservation = prov.source_kind === 'OBSERVED';
  return [
    { key: 'SOURCE', value: [prov.source_id, prov.product_id].filter(Boolean).join(' · ') + ` — ${prov.label}` },
    { key: 'TYPE', value: words(prov.source_kind).toLowerCase() },
    { key: 'TRUTH', value: truth ? TRUTH_WORDS[truth] : 'not stated' },
    { key: 'VALID', value: formatUtc(prov.valid_time) },
    { key: 'ISSUED', value: isObservation ? 'n/a (observation)' : formatUtc(prov.issued_at) },
    { key: 'RETRIEVED', value: formatUtc(prov.retrieved_at) },
    { key: 'FRESHNESS', value: `${prov.freshness.state} — ${formatFreshness(prov.freshness)}` },
    { key: 'QUALITY', value: prov.quality && prov.quality.length ? prov.quality.join(', ') : '—' },
    { key: 'METHOD', value: prov.method_id ?? 'none (untransformed)' },
  ];
}
