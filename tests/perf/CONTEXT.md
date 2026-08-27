# tests/perf — what a request is allowed to cost

The `/viz/basins` amplification baseline: 120 statements from 12 distinct SQL texts, measured
2026-08-26 before any optimisation, and the response bodies those 120 statements produced.

Read `README.md` first — it is the inventory (every query, its table, its call site, and whether
it is a duplicate, an N+1 or genuinely singular) and it carries the before/after numbers.

Two rules for anything added here:

- **Read-only.** Nothing in this folder may be imported by `cascade_api`, `cascade_core` or
  `cascade_hydrology`. The instrumentation attaches to an engine from the outside and detaches
  again; `test_query_budget.py` asserts the endpoint answers identically with it and without it.
- **`baseline/` is evidence, not cache.** Those bodies are the semantic contract the optimisation
  must preserve. Regenerating them to make a test pass falsifies the measurement — if a diff
  appears, either the change is wrong or the contract changed on purpose, and the second needs its
  own commit and its own reason.

The budget in `test_query_budget.py` starts at today's count and only ever goes down.
