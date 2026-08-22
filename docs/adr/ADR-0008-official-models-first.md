# ADR-0008: Official models first; no Cascade-derived probabilities before hindcast evaluation

- Status: Accepted
- Date: 2026-08-22

## Context
NOAA/NWS (NWRFC via NWPS) issues official river forecasts for all six seed points (FACT, live 2026-08-22). The National Water Model provides reach-level modeled streamflow and ensembles. V1's plan proposed TimesFM-style forecasting in Phase 4 without an evaluation framework.

## Decision
Cascade Oracle is an intelligence-fusion layer above authoritative data and models. It displays official forecasts and categories, authoritative model outputs and their disagreement, and transparent derived indicators (susceptibility index, forcing, headroom). It does not display a Cascade-derived exceedance probability until a method has been hindcast-evaluated against stored history (Event Zero first) with reliability and skill reported (`docs/TESTING.md` §7). Until then such outputs are labeled EXPERIMENTAL and shown as indices.

## Alternatives considered
- Build a custom ML flood model early — no history, no evaluation, high risk of confident nonsense.
- Never build custom models — forecloses genuine incremental value (e.g. regime-conditional bias correction). The decision sequences, it does not forbid.

## Consequences
The roadmap front-loads history capture and the hindcast harness. Product copy uses "official forecast", "model probability (named)", and "experimental index" precisely.
