/**
 * ProvenancePopover: the per-value provenance inspector (inspector v1, VISUAL_TRUTH_DOCTRINE
 * §6). The trigger is the value's source-kind badge; clicking it opens a small dialog
 * rendering the full ProvenanceRef via toProvenanceFields. A missing ref still opens and says
 * the document is incomplete — the value is UNKNOWN, never defaulted. Closes on Escape,
 * outside click and the close button. The entrance animation uses the --dur-micro token, so
 * the reduced-motion path zeroes it (tokens.css).
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Badge } from './Badge';
import { useDismiss } from './dismiss';
import { badgeForSourceKind } from './badges';
import { toProvenanceFields } from './provenance-record';
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import './popover.css';

interface ProvenanceRecordProps {
  provKey: string;
  prov: ProvenanceRef | undefined;
  truth: TruthClass | null;
  onClose: () => void;
  /** Which way the dialog opens — decided from the anchor's viewport half, so a badge in
   * the bottom chrome opens UPWARD instead of pushing the document taller (audit F12). */
  drop?: 'down' | 'up';
  align?: 'start' | 'end';
}

/** The dialog body: pure rendering of the record. Exported for render tests. */
export function ProvenanceRecord({ provKey, prov, truth, onClose, drop = 'down', align = 'start' }: ProvenanceRecordProps) {
  return (
    <dialog
      open
      className="prov-popover glass-surface glass-popover shape-card"
      aria-label={`Provenance for ${provKey}`}
      data-testid="layer-inspector"
      data-drop={drop}
      data-align={align}
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
  const [placement, setPlacement] = useState<{ drop: 'down' | 'up'; align: 'start' | 'end' }>({ drop: 'down', align: 'start' });
  const anchorRef = useRef<HTMLSpanElement>(null);

  const close = useCallback(() => setOpen(false), []);
  useDismiss(anchorRef, close, { enabled: open });
  useEffect(() => {
    if (!open) return;
    anchorRef.current?.querySelector<HTMLElement>('dialog')?.focus();
  }, [open]);

  const toggle = () => {
    if (!open) {
      const rect = anchorRef.current?.getBoundingClientRect();
      if (rect) {
        setPlacement({
          drop: rect.top > window.innerHeight / 2 ? 'up' : 'down',
          align: rect.left > window.innerWidth - 340 ? 'end' : 'start',
        });
      }
    }
    setOpen(!open);
  };

  const badge = badgeForSourceKind(prov?.source_kind ?? 'UNKNOWN');
  const title = prov
    ? `${prov.label} — click for provenance`
    : `provenance ref "${provKey}" missing from the document — click for detail`;
  return (
    <span className="prov-popover-anchor" ref={anchorRef}>
      <Badge badge={badge} title={title} testId={testId} onClick={toggle} />
      {open ? <ProvenanceRecord provKey={provKey} prov={prov} truth={truth} onClose={close} drop={placement.drop} align={placement.align} /> : null}
    </span>
  );
}
