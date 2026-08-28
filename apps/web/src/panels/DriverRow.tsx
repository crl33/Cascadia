/** One headline driver: name, value-with-unit or UNAVAILABLE, direction, provenance. */
import type { BasinVisualizationState, ProvenanceRef } from '../contracts/schemas';
import { ProvenanceLine } from './ProvenanceLine';
import { formatNumber, words } from './format';

type Driver = NonNullable<BasinVisualizationState['headline_drivers']>[number];

export function DriverRow({ driver, refs }: { driver: Driver; refs: Record<string, ProvenanceRef | undefined> }) {
  const unavailable = driver.value == null;
  return (
    <li className="driver" data-testid={`driver-${driver.feature}`}>
      <div className="driver-head">
        <span className="driver-name" title={driver.feature}>{words(driver.feature)}</span>
        <span className="driver-value mono" data-testid={`driver-${driver.feature}-value`}>
          {unavailable ? 'UNAVAILABLE' : `${formatNumber(driver.value)} ${driver.unit ?? ''}`.trim()}
        </span>
      </div>
      <span className="driver-direction mono">{words(driver.direction)}</span>
      <ProvenanceLine provKey={driver.prov} prov={refs[driver.prov]} truth={null} testId={`driver-${driver.feature}-badge`} />
    </li>
  );
}

