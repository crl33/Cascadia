/**
 * HorizonStrip: NOW / +12 / +24 / +48 / +72 — the official forecast read at fixed leads
 * (mission §16). Every cell is a REAL slice: NOW is the observed value; each horizon is the
 * nearest stored official-forecast point within tolerance, and a horizon past the run's end
 * says "ends" instead of inventing a number. The category chip carries the official
 * register; nothing here is a probability and nothing is Cascade-derived.
 */
import type { ForecastHorizon, RiverVisualizationState } from '../contracts/schemas';
import { CATEGORY_BADGE } from '../design-system/badges';
import { Badge } from '../design-system/Badge';
import { formatQuantity } from './format';

function cellValue(h: ForecastHorizon): string {
  if (h.official == null) return '—';
  return formatQuantity(h.official, h.official.unit === 'cfs' ? 0 : 1);
}

export function HorizonStrip({ outlet }: { outlet: RiverVisualizationState }) {
  const horizons = outlet.horizons ?? [];
  if (horizons.length === 0) return null;
  const observed = outlet.observed?.stage ?? outlet.observed?.flow ?? null;
  return (
    <div className="horizon-strip" data-testid="horizon-strip" aria-label="Official forecast horizons">
      <div className="horizon-cell" data-testid="horizon-now">
        <span className="horizon-lead">NOW</span>
        <span className="horizon-value">{observed ? formatQuantity(observed, observed.unit === 'cfs' ? 0 : 1) : '—'}</span>
        <Badge badge={CATEGORY_BADGE[outlet.observed_category ?? 'unknown']} />
      </div>
      {horizons.map((h) => (
        <div className="horizon-cell" key={h.lead_h} data-testid={`horizon-${h.lead_h}`} title={h.reason ?? undefined}>
          <span className="horizon-lead">+{h.lead_h}H</span>
          <span className="horizon-value">{cellValue(h)}</span>
          <Badge badge={CATEGORY_BADGE[h.category]} />
        </div>
      ))}
      <span className="horizon-register">OFFICIAL FORECAST · NWRFC</span>
    </div>
  );
}
