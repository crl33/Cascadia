# ADR-0014: Forecast-run bodies declare units and datum per column, not per run

- Status: Accepted
- Date: 2026-08-24
- Deciders: backend + client, resolving a finding raised twice (spike verification 2026-08-22, P1 client build 2026-08-24)

## Context
`GET /forecast-points/{LID}/runs/latest` and `GET /forecast-points/{LID}/runs` return a run as a
flat header (`primary`, `unit`, `datum`) plus `points[]`, where each point carries **both** a
`stage` and a `flow` value. NWPS publishes a primary and a secondary series together, so a run is
inherently two-column.

- FACT (live, 2026-08-24, `https://cascadia.papsukkal.com/forecast-points/AUBW1/runs/latest`):
  AUBW1 returns `primary: "flow", unit: "cfs", datum: "NGVD29"` with **all 40 points carrying a
  stage value** (56.8 ft). The datum is not junk — it describes a populated column.
- FACT: ingestion already scopes it. `packages/providers/nwps/normalize.py` stores
  `datum = gauge datum if a stage column exists else None`, and persists `stage_unit`/`flow_unit`
  next to it (`packages/core/models.py::ForecastRun`). The FLS-reconstructed December-2025 AUBW1
  runs, which have no stage column, store `datum = None`
  (`tests/integration/test_event_zero_fls_pg.py`). So the stored field has always meant *the
  gauge-zero datum of this run's stage column*.
- FACT: the envelope path is already correct — `assemble.py` uses `run.datum` only when the
  hazard basis is stage and passes `None` on flow.
- The defect is therefore naming, not data: a field called `datum` sitting beside `primary: "flow"`
  reads as the flow values' datum, which is meaningless. It was flagged as ambiguous at the spike
  and the P1 client chose to ignore it rather than trust it.

## Decision
Declare units and datum **per column**, never per run. The run header keeps `primary` and `unit`
(the variable the run is *issued* on) and additionally carries `stage_unit`, `flow_unit` and
`stage_datum`, the last being the gauge-zero vertical datum of `points[].stage` only, null when
the run carries no stage column. The flat `datum` key is removed from both run endpoints. Nothing
about ingestion or storage changes; `forecast_run.datum` continues to hold NWPS's value as-is and
is now presented under a name that says what it describes.

## Alternatives considered
- **Null the datum on flow-primary runs at assembly time** — rejected. It would strip the datum
  from 40 real stage values per AUBW1 run, leaving a populated stage column that no consumer may
  interpret. Discarding known provenance to make a field name true inverts the doctrine: the point
  of ADR-0009 is that every stage value carries its datum, and UNKNOWN is legitimate only when the
  datum is genuinely unknown. Here it is known.
- **Keep `datum` and document it in prose** — rejected. The name is the contract at the point of
  use; a reader holding a `primary: "flow"` body will not consult a document to discover that a
  neighbouring field belongs to a different column. Two independent reviewers already misread it.
- **Promote the run body to a Pydantic contract in `packages/contracts`** — deferred, not
  rejected. It is the right end state, but the schema-export pipeline compiles a single
  `SceneSummary` root and asserts every other schema is contained in it, so a new top-level
  contract needs a codegen change. Tracked as follow-up; the body stays hand-shaped in
  `apps/api/routes.py` with a hand-written zod mirror, as it already was.

## Consequences
Positive: the stage column of a flow-primary run becomes usable, because its unit and datum are
declared; the client's datum guard now reads a field that means what it says; `stage_unit`/
`flow_unit` (already stored, previously hidden) stop being dead columns. A stage overlay whose
run declares no datum is now an explicit refusal rather than a silently skipped check.

Negative: this is a **breaking rename** on two endpoints. They sit outside the versioned envelope
contracts (no `version` field, not in `packages/contracts`), so there is no version to bump and no
graceful-degradation path — the API and the web client must deploy together. `CONTRACT_VERSION`
stays at 1.1.0: no envelope contract changed.

Revisit if a run ever gains a third column, or when the run body is promoted into
`packages/contracts` — at which point it becomes version-governed like the envelopes.

## Evidence
- Live AUBW1 run body, retrieved 2026-08-24 (above); `docs/research/spike-report-2026-08-22.md`
  §6 finding 3, which first recorded the ambiguity and correctly diagnosed it as a contract
  clarification rather than a bug.
- `tests/integration/test_event_zero_fls_pg.py` (flow-primary run with no stage column stores
  `datum = None`), `tests/integration/test_pipeline_api.py` (both shapes asserted end to end).
- ADR-0009 (units and datums policy), ADR-0011 (thresholds official only).
