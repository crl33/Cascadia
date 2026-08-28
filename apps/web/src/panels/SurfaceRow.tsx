/** One surface's forensic row: state word, reason, provenance line, optional value/after. */
import type { ReactNode } from 'react';
import type { ProvenanceRef, TruthClass } from '../contracts/schemas';
import type { BasinVisualizationState } from '../contracts/schemas';
import { ProvenanceLine } from './ProvenanceLine';
import { formatNumber, formatQuantity, words } from './format';

type Surfaces = BasinVisualizationState['surfaces'];
type SurfaceState = Surfaces['forcing'];

interface SurfaceRowProps {
  title: string;
  state: string;
  reason: string | null | undefined;
  provKey: string;
  refs: Record<string, ProvenanceRef | undefined>;
  truth: TruthClass | null;
  testId: string;
  extra?: ReactNode;
  /** Rendered BELOW this surface's own provenance line, so a trailing badge is never misread as
   *  belonging to the block after it. Tier 0 uses this: its statements carry their own badges. */
  after?: ReactNode;
}

export function SurfaceRow({ title, state, reason, provKey, refs, truth, testId, extra, after }: SurfaceRowProps) {
  return (
    <div className="row" data-testid={testId}>
      <div className="row-head">
        <span className="row-title">{title}</span>
        <span className={`state-word state-${state}`} data-testid={`${testId}-state`}>{words(state).toUpperCase()}</span>
      </div>
      {extra}
      {reason ? <p className="reason" data-testid={`${testId}-reason`}>{reason}</p> : null}
      <ProvenanceLine provKey={provKey} prov={refs[provKey]} truth={truth} testId={`${testId}-badge`} />
      {after}
    </div>
  );
}

/**
 * The headline quantity a surface was banded from, its named spread points and its confidence.
 * Absent when the surface has no value — an UNKNOWN surface prints its reason instead, never a
 * blank number.
 */
export function SurfaceValue({ surface, testId }: { surface: SurfaceState; testId: string }) {
  const spread = surface.spread ? Object.entries(surface.spread) : [];
  if (!surface.value && spread.length === 0) return null;
  const unit = surface.value?.unit ?? '';
  return (
    <p className="value-line" data-testid={testId}>
      {surface.value ? <span className="value" data-testid={`${testId}-quantity`}>{formatQuantity(surface.value, 1)}</span> : null}
      {spread.map(([key, value]) => (
        <span key={key} className="muted mono">{words(key)} {formatNumber(value)} {unit}</span>
      ))}
      <span className="muted">confidence {words(surface.confidence)}</span>
    </p>
  );
}

