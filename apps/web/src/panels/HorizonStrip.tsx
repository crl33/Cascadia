/**
 * HorizonStrip: NOW / +12 / +24 / +48 / +72 — the official forecast read at fixed leads
 * (mission §16). Every cell is a REAL slice: NOW is the observed value; each horizon is the
 * nearest stored official-forecast point within tolerance, and a horizon past the run's end
 * says "ends" instead of inventing a number. The category chip carries the official
 * register; nothing here is a probability and nothing is Cascade-derived.
 *
 * Datum handling (production find 2026-08-29): five cells each saying "44.4 ft (NAVD88)"
 * overlapped each other in the real panel. When every quantity in the strip shares one datum
 * it is stated ONCE in the register line; cells go bare. A mixed-datum strip (should not
 * exist for one gauge) keeps the full per-cell form rather than mislabeling a value.
 */
import type { Quantity, RiverVisualizationState } from '../contracts/schemas';
import { CATEGORY_BADGE } from '../design-system/badges';
import { Badge } from '../design-system/Badge';
import { formatQuantity, formatQuantityBare } from './format';
import { sharedDatum } from './horizon-math';

export function HorizonStrip({ outlet }: { outlet: RiverVisualizationState }) {
  const horizons = outlet.horizons ?? [];
  if (horizons.length === 0) return null;
  const observed = outlet.observed?.stage ?? outlet.observed?.flow ?? null;

  const datum = sharedDatum([observed, ...horizons.map((h) => h.official)]);
  const format = (q: Quantity | null | undefined): string => {
    if (q == null) return '—';
    const digits = q.unit === 'cfs' ? 0 : 1;
    return datum !== null ? formatQuantityBare(q, digits) : formatQuantity(q, digits);
  };

  return (
    <div className="horizon-strip" data-testid="horizon-strip" aria-label="Official forecast horizons">
      <div className="horizon-cell" data-testid="horizon-now">
        <span className="horizon-lead">NOW</span>
        <span className="horizon-value">{format(observed)}</span>
        <Badge badge={CATEGORY_BADGE[outlet.observed_category ?? 'unknown']} />
      </div>
      {horizons.map((h) => (
        <div className="horizon-cell" key={h.lead_h} data-testid={`horizon-${h.lead_h}`} title={h.reason ?? undefined}>
          <span className="horizon-lead">+{h.lead_h}H</span>
          <span className="horizon-value">{format(h.official)}</span>
          <Badge badge={CATEGORY_BADGE[h.category]} />
        </div>
      ))}
      <span className="horizon-register">
        OFFICIAL FORECAST · NWRFC{datum ? ` · ${datum}` : ''}
      </span>
    </div>
  );
}
