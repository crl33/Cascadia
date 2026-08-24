/**
 * ProvenancePopover: the per-value provenance inspector (inspector v1, VISUAL_TRUTH_DOCTRINE
 * §6). The trigger is the value's source-kind badge; clicking it opens a small dialog
 * rendering the full ProvenanceRef via toProvenanceFields. A missing ref still opens and says
 * the document is incomplete — the value is UNKNOWN, never defaulted. Closes on Escape,
 * outside click and the close button. The entrance animation uses the --dur-micro token, so
 * the reduced-motion path zeroes it (tokens.css).
 */
import { useEffect, useRef, useState } from 'react';
import { Badge } from './Badge';
import { badgeForSourceKind } from './badges';
import { toProvenanceFields } from './provenance-record';
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import './popover.css';

interface ProvenanceRecordProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  truth: TruthClass | null;
  onClose: () => void;
}

/** The dialog body: pure rendering of the record. Exported for render tests. */
export function ProvenanceRecord({ provKey, prov, truth, onClose }: ProvenanceRecordProps) {
  return (
    <dialog
      open
      className="prov-popover"
      aria-label={`Provenance for ${provKey}`}
      data-testid="layer-inspector"
    >
      <header className="prov-popover-header">
        <span className="eyebrow">PROVENANCE · {provKey}</span>
        <button type="button" className="link-button" onClick={onClose} aria-label="Close inspector" data-testid="inspector-close">close</button>
      </header>
      {prov ? (
        <dl className="prov-popover-grid">
          {toProvenanceFields(prov, truth).map((field) => (
            <div key={field.key} className="prov-popover-row">
              <dt>{field.key}</dt>
              <dd className="mono" data-testid={`inspector-${field.key.toLowerCase().replace(/\s+/g, '-')}`}>{field.value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="prov-popover-missing">No provenance record for "{provKey}" — the document is incomplete; the value is UNKNOWN.</p>
      )}
    </dialog>
  );
}

interface ProvenancePopoverProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  truth?: TruthClass | null;
  testId?: string;
  /** Initial open state, for tests and static rendering only. */
  defaultOpen?: boolean;
}

export function ProvenancePopover({ provKey, prov, truth = null, testId, defaultOpen = false }: ProvenancePopoverProps) {
  const [open, setOpen] = useState(defaultOpen);
  const anchorRef = useRef<HTMLSpanElement>(null);

  // External-system bridge: document listeners while open, removed on close/unmount.
  useEffect(() => {
    if (!open) return;
    anchorRef.current?.querySelector<HTMLElement>('dialog')?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    const onPointerDown = (event: MouseEvent) => {
      if (anchorRef.current && event.target instanceof Node && !anchorRef.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('mousedown', onPointerDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.removeEventListener('mousedown', onPointerDown);
    };
  }, [open]);

  const badge = badgeForSourceKind(prov?.source_kind ?? 'UNKNOWN');
  const title = prov
    ? `${prov.label} — click for provenance`
    : `provenance ref "${provKey}" missing from the document — click for detail`;
  return (
    <span className="prov-popover-anchor" ref={anchorRef}>
      <Badge badge={badge} title={title} testId={testId} onClick={() => setOpen((wasOpen) => !wasOpen)} />
      {open ? <ProvenanceRecord provKey={provKey} prov={prov} truth={truth} onClose={() => setOpen(false)} /> : null}
    </span>
  );
}
