/**
 * Tier 0 inside the basin susceptibility row: the LEVEL, the CHANGE, and whether that change is
 * itself unusual. Three questions, three visually separate answers, and no fourth number
 * summarising them — a composite of these is exactly the flood-risk score the doctrine forbids
 * (`docs/VISUAL_TRUTH_DOCTRINE.md` §1, and the contract's own note on `HydrologicState`).
 *
 * What this file deliberately does NOT do:
 *
 * - It computes no hydrology. Every number arrives in the contract; the only arithmetic here is
 *   `toFixed`/`toLocaleString` in `format.ts`.
 * - It never turns a rank into a percentile or a percentage. "759th largest of 34,957" carries
 *   its own denominator; "top 2 %" would advertise resolution the count does not have and would
 *   read as comparable to the day-of-year percentile, which is a different quantity against a
 *   different sample.
 * - It never colours these statements with the red/amber alarm family. They are C-EXPERIMENTAL
 *   and DERIVED, and `VISUAL_TRUTH_DOCTRINE.md` §2 forbids the red register for them. An NWS
 *   warning is the only thing in this panel allowed to look like an alert.
 * - `boundary` is a CONDITION, not a confidence and not a probability. `near_band_edge` renders
 *   as "the record cannot separate X from Y here" — a statement about the sample, not about
 *   belief.
 *
 * Every statement carries its own `prov`, because they do not share one: the level and its rank
 * come from `method:streamflow-tail-state@0.1.0`, each change from
 * `method:streamflow-state-change@0.1.0`, and the two are read against different references.
 */
import type { BasinVisualizationState, ProvenanceRef } from '../contracts/schemas';
import { ProvenanceLine } from './ProvenanceLine';
import { formatCount, formatMultiplier, formatOrdinal, formatQuantity, words } from './format';

type HydrologicState = NonNullable<BasinVisualizationState['hydrologic_state']>;
type StateChangeEntry = NonNullable<BasinVisualizationState['state_change']>[number];
type Refs = Record<string, ProvenanceRef | undefined>;

/** A refusal: a short state a reader can scan, with the contract's own sentence beside it. */
function Refusal({ state, reason, testId }: { state: string; reason: string; testId: string }) {
  return (
    <details className="t0-refusal" data-testid={testId}>
      <summary>
        <span className="t0-refusal-state">{state}</span>
        <span className="t0-refusal-more">why</span>
      </summary>
      <p className="reason" data-testid={`${testId}-reason`}>{reason}</p>
    </details>
  );
}

/** "the record cannot separate moderate from high here" — a property of the sample, never a confidence. */
function boundaryText(state: HydrologicState): string | null {
  const bands = state.bands_within_sampling_error ?? [];
  if (state.boundary === 'near_band_edge' && bands.length > 1) {
    return `The record cannot separate ${bands.map(words).join(' from ')} at this value.`;
  }
  if (state.boundary === 'unquantified') {
    return 'Sampling error is not quantified here: the percentile is a bound, not an estimate, so a spread either side of it would claim resolution the ladder does not have.';
  }
  return null;
}

function LevelBlock({ state, refs }: { state: HydrologicState; refs: Refs }) {
  const rank = state.rank;
  const multiple = state.multiple;
  const boundary = boundaryText(state);
  return (
    <div className="t0-block" data-testid="tier0-level">
      <p className="t0-kicker">Level: how unusual for the date</p>
      <p className="t0-line" data-testid="tier0-level-observed">
        <span className="mono t0-figure">{formatQuantity(state.observed, 0)}</span>
        <span className="muted">on {state.day}</span>
      </p>
      {state.percentile_clamped ? (
        <p className="t0-note" data-testid="tier0-level-clamped">
          At or above the stored p{multiple?.reference_percentile ?? 95} limit. The ladder stops
          discriminating here, so the percentile is a bound rather than an estimate.
        </p>
      ) : null}
      {multiple ? (
        <p className="t0-line" data-testid="tier0-level-multiple">
          <span className="mono t0-figure">{formatMultiplier(multiple.multiple)}</span>
          <span className="muted">
            the seasonal p{multiple.reference_percentile} reference ({formatQuantity(multiple.reference, 0)})
          </span>
        </p>
      ) : null}
      {rank && rank.rank != null ? (
        <p className="t0-line" data-testid="tier0-level-rank">
          <span className="mono t0-figure">{formatOrdinal(rank.rank)}</span>
          <span className="muted">
            largest of {formatCount(rank.of)} on record for this day-of-year window
            {rank.exceeds_record && rank.previous_max
              ? `; the previous largest was ${formatQuantity(rank.previous_max, 0)}${rank.previous_max_day ? ` on ${rank.previous_max_day}` : ''}`
              : ''}
          </span>
        </p>
      ) : rank && rank.reason ? (
        <Refusal state="Exact rank not read" reason={rank.reason} testId="tier0-level-rank-absent" />
      ) : null}
      {boundary ? <p className="t0-note" data-testid="tier0-level-boundary">{boundary}</p> : null}
      {state.reference ? (
        <p className="t0-ref muted" data-testid="tier0-level-reference">
          against {formatCount(state.reference.n)} daily means across{' '}
          {formatCount(state.reference.independent_years)} independent years
          {state.reference.period_start && state.reference.period_end
            ? ` (${state.reference.period_start}–${state.reference.period_end})` : ''}
        </p>
      ) : null}
      <ProvenanceLine provKey={state.prov} prov={refs[state.prov]} truth={state.truth} testId="tier0-level-badge" />
    </div>
  );
}

function ChangeRow({ change, refs }: { change: StateChangeEntry; refs: Refs }) {
  const id = `tier0-change-${change.window_h}h`;
  const spanDiffers = change.span_h != null && Math.abs(change.span_h - change.window_h) > 0.05;
  return (
    <li className="t0-change" data-testid={id}>
      {change.growth != null ? (
        <p className="t0-line" data-testid={`${id}-growth`}>
          <span className="mono t0-figure">{formatMultiplier(change.growth)}</span>
          <span className="muted">in {change.window_h} h</span>
          <span className="t0-direction mono">{words(change.direction)}</span>
        </p>
      ) : (
        <Refusal state={`No ${change.window_h} h change`} reason={change.reason ?? 'No reason was carried for this refusal.'} testId={`${id}-absent`} />
      )}
      {spanDiffers ? (
        <p className="t0-note" data-testid={`${id}-span`}>
          measured over {change.span_h} h, not the nominal {change.window_h} h
        </p>
      ) : null}
      {change.rank != null && change.rank_of != null ? (
        <p className="t0-line" data-testid={`${id}-rank`}>
          <span className="mono t0-figure">{formatOrdinal(change.rank)}</span>
          <span className="muted">largest of {formatCount(change.rank_of)} comparable {change.window_h} h changes in this gauge&rsquo;s record</span>
        </p>
      ) : change.growth != null && change.rank_reason ? (
        <Refusal state="Not ranked" reason={change.rank_reason} testId={`${id}-rank-absent`} />
      ) : null}
      <ProvenanceLine provKey={change.prov} prov={refs[change.prov]} truth={null} testId={`${id}-badge`} />
    </li>
  );
}

interface Tier0SectionProps {
  state: BasinVisualizationState['hydrologic_state'];
  changes: BasinVisualizationState['state_change'];
  refs: Refs;
  /** The susceptibility surface's own reason, shown when Tier 0 is absent so the gap has a cause. */
  surfaceReason: string | null | undefined;
}

export function Tier0Section({ state, changes, refs, surfaceReason }: Tier0SectionProps) {
  const entries = changes ?? [];
  if (!state && entries.length === 0) {
    return (
      <div className="t0" data-testid="tier0-absent">
        <p className="reason" data-testid="tier0-absent-reason">
          No level or change statement at this knowledge time.{surfaceReason ? ` ${surfaceReason}` : ''}
        </p>
      </div>
    );
  }
  return (
    <div className="t0" data-testid="tier0">
      {state ? <LevelBlock state={state} refs={refs} /> : (
        <div className="t0-block" data-testid="tier0-level-absent">
          <p className="t0-kicker">Level: how unusual for the date</p>
          <p className="reason">{surfaceReason ?? 'No level statement at this knowledge time.'}</p>
        </div>
      )}
      {entries.length > 0 ? (
        <div className="t0-block" data-testid="tier0-change">
          <p className="t0-kicker">Change: how fast, and how unusual that is</p>
          <ul className="t0-changes">
            {entries.map((c) => <ChangeRow key={c.window_h} change={c} refs={refs} />)}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
