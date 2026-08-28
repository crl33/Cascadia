import { useBasinReservoirs } from '../api/hooks';
import { ProvenancePopover } from '../design-system/ProvenancePopover';
import { formatNumber, words } from './format';

const VARIABLE_LABEL: Record<string, string> = {
  forebay_elevation: 'forebay', storage: 'storage', inflow: 'inflow', outflow: 'outflow',
};

/**
 * Reservoir state for a regulated basin: the latest observation per (dam, variable), verbatim.
 * Long-form units are the provider's own and stay unabbreviated; a forebay elevation renders
 * with its no-datum caveat, because a number on an unstated datum invites false comparison;
 * an unregulated basin renders nothing at all — no section, no empty shell.
 */
export function ReservoirsSection({ basinId }: { basinId: string }) {
  const query = useBasinReservoirs(basinId);
  const doc = query.data;
  if (query.isError) {
    // a failed endpoint must not read as "unregulated": Green with Howard Hanson dark is a
    // different fact from the Nooksack having no dams (adversarial review 2026-08-28)
    return (
      <div className="row" data-testid="reservoirs">
        <div className="row-head"><span className="row-title">Reservoirs</span></div>
        <p className="reason" data-testid="reservoirs-error">Reservoir state unavailable: {query.error.message}</p>
      </div>
    );
  }
  if (!doc || doc.reservoirs.length === 0) return null;
  const refs = doc.provenance_refs;
  return (
    <div className="row" data-testid="reservoirs">
      <div className="row-head"><span className="row-title">Reservoirs</span></div>
      <ul>
        {doc.reservoirs.map((r) => (
          <li key={r.station_id} data-testid={`reservoir-${r.lid}`}>
            <div className="driver-head">
              <span className="driver-name">{r.name}</span>
              {r.prov ? <ProvenancePopover provKey={r.prov} prov={refs[r.prov]} truth={null} /> : null}
            </div>
            {Object.keys(r.variables).length > 0 ? (
              <p className="value-line mono" data-testid={`reservoir-${r.lid}-values`}>
                {Object.entries(r.variables).map(([name, v]) => (
                  <span key={name}>
                    {VARIABLE_LABEL[name] ?? words(name)} {v.value === null ? 'UNKNOWN' : formatNumber(v.value)} {v.unit}
                    {name === 'forebay_elevation' ? <span className="muted"> (datum unstated)</span> : null}
                  </span>
                ))}
              </p>
            ) : (
              <p className="reason">No series served for this dam at this knowledge time.</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

