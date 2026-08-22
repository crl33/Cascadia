/** LayerInspector: the provenance lines for one value (VISUAL_TRUTH_DOCTRINE §6). Pure rendering of the record. */
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import { toInspectorRecord } from './inspector-record';

interface LayerInspectorProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  truth: TruthClass | null;
  onClose: () => void;
}

export function LayerInspector({ provKey, prov, truth, onClose }: LayerInspectorProps) {
  return (
    <section className="inspector" data-testid="layer-inspector" aria-label="Provenance inspector">
      <header className="inspector-header">
        <span className="eyebrow">INSPECTOR · {provKey}</span>
        <button type="button" className="link-button" onClick={onClose} aria-label="Close inspector">close</button>
      </header>
      {prov ? (
        <dl className="inspector-grid">
          {toInspectorRecord(prov, truth).map((line) => (
            <div key={line.key} className="inspector-row">
              <dt>{line.key}</dt>
              <dd className="mono">{line.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="muted">No provenance record for "{provKey}" — the document is incomplete; the value is UNKNOWN.</p>
      )}
    </section>
  );
}
