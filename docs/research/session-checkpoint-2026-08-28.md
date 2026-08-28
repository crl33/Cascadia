# Session checkpoint — 2026-08-28

What landed, what is deployed, what is proven, and what to do next. Written to be actionable
without the conversation that produced it.

## 1. Exact state

| | |
|---|---|
| `HEAD` = `origin/main` | `9c5e652eb87606b93f4391d7014fddcaca6b55f9` |
| Deployed revision | **the same SHA** (`/system/version`) |
| Tree | clean; **one** worktree (three stale ones removed, their branches kept) |
| Gates | 474 offline, 15 pg, ruff, import-linter 5/5, 164 web, eslint, tsc — all green |
| CI | all five jobs green on every landed SHA |
| `/system/health` | `ok`, no reasons, **12 of 12 products current**, no job not-ok |

## 2. What landed this session

Five commits, each with its measurement in the message.

1. **`609b699` NWM reaches — per-reach fault isolation.** 15 of 16 production failures were a
   `ReadTimeout` on ONE reach, and because the fetch sat unguarded in the loop `run_job` discarded
   the whole session — throwing away reaches that had already parsed. The module had claimed "a
   partial run is not an error" since it was written; the transport path now obeys it too.
   `MEDIUM_RANGE_TIMEOUT_S = 90` addresses why a reach was counted slow at all. Four mutations,
   all caught behaviourally.
2. **`c107eba` HEFS — the ensemble that disappears in ten days.** Had zero lines of code. See §3.
3. **`a81e82a` SNOTEL basin attribution.** Two pillows NRCS itself associates with no seeded basin
   were being counted as Skagit snow. A first version of the rule was discarded before shipping —
   it also dropped two genuinely west-side sites. See §4.
4. **`9c5e652` Client — the globe says the Cascade index.** First Cascade-derived thing on the
   map, in the experimental register, with the doctrine limits as tests.
5. Doc corrections landed alongside: the forecast snow level DOES exist, which halves the distance
   to a rain-exposed fraction.

## 3. HEFS is archiving, and ten days were recovered

The only machine-readable OFFICIAL probabilistic streamflow forecast for Washington. ROADMAP
Phase 5 says "archived daily from Phase 1 onward"; Phase 1 had been ingesting since 2026-08-24
with no adapter, so history was being lost every day.

Verified live 2026-08-27/28: the provider retains exactly **10 cycles spanning 9.0 days**, one per
day at 12Z, at all six seed points, published ~3.9 h after the cycle.

Production now holds, from the first run:

```
hefs_ensemble_flow_series   n=60   10 cycles x 6 points, 2026-08-18 .. 2026-08-27
hefs_exceedance_quantiles   n=6    latest cycle (the provider serves no older ones)
45 members, CFS, grid encoding · 72 raw artifacts, 23.8 MB under the `hefs/` prefix
```

**That prefix must never get an expiry lifecycle rule.** Unlike `nbm/`, these bytes cannot be
re-fetched.

## 4. Two corrections made to my own work, both before shipping

Recorded because the reasoning is the reusable part.

- **The SNOTEL rule was too blunt at first.** Testing association against the one BASIN dropped
  Meadows Pass and Tinkham Creek, which are filed under Cedar while all their Puget associations
  are Green-Duwamish/Puyallup-White — plainly west-side sites. The rule now tests association with
  the seeded DOMAIN, and those two are kept and flagged rather than dropped or re-attributed.
- **A style test asserted its own contradiction.** It required the label not to match
  `/probability/` while the label correctly says "not a probability". The doctrine forbids a
  *number formatted as* a probability, so the check is on numerals.

## 5. What the audit found and what is still open

A five-lens audit reconciled docs against code. Highest-value items still open, in dependency
order:

1. **Hypsometry** — now the ONLY blocker for a rain-exposed / rain-on-snow fraction, the most
   valuable missing Cascades hydrology. And it is cheaper than it looks: the snow level's own
   p10-p90 spread is **241 m median, 908 m max** over 96 live basin-hours, so a DEM finer than
   that cannot improve the intersection. A coarse DEM is the honest choice, not a compromise.
2. **The stub serves the pre-P3 envelope** (carried-forward item 4). It is why the new
   susceptibility layer could not be visually confirmed today: the stub reports susceptibility
   UNKNOWN, so the browser correctly renders the unknown treatment and never the tone or stripe.
   Regenerating `packages/contracts/fixtures/basin_skagit_envelope.json` from a real `/viz/basins`
   unblocks that.
3. **`nbm.fetch_core_snowlvl` cron/selector mismatch** — flagged PRODUCTION-DEFECT by the audit,
   not yet verified by me. Verify before changing.
4. **Basin polygon != contributing area of the declared outlet** — flagged PRODUCTION-DEFECT.
5. **Provider canaries exist but nothing runs them** — including the new HEFS one.
6. **M2 remainder**: `/metrics`, least-privilege DB roles, mypy in CI.
7. NWS alerts + SSE; MRMS/HRRR/GEFS; USACE; NID/NLD — all UNSTARTED.

## 6. Things worth knowing before touching production

- **A registry edit reaches production only on re-seed.** Both HEFS and the USGS normals hit this:
  the job fails with a `ForeignKeyViolation` on `source_product` until the catalogues are merged.
  Merge SOURCES and PRODUCTS only — no `create_schema`, no geometry, no stations.
- **Railway has no scriptable in-container exec.** `railway run` executes LOCALLY with production
  variables (its own help says so) and is never proof of container behaviour; `preDeployCommand`
  set via the API did not execute on either a redeploy or a fresh `up`. The working mechanism is
  the production worker: register a Procrastinate task and `defer_async()` it.
- **The queueing lock is per job name.** A second `defer_async()` while one is queued raises
  `AlreadyEnqueued` — which is correct, and means waiting for the retry rather than forcing one.
- **`job_run` counts ATTEMPTS, not cycles.** Retry bursts inflate apparent failure rates; cluster
  by incident before concluding a job is unhealthy. This is what made `nbm.fetch_qmd` look like a
  40 % failure when its last failure was 2026-08-25 and every scheduled run since has been green.

## 7. Cost

GitHub Actions is **free** — the repo is public, so unlimited standard-runner minutes; do not
optimise CI for money. The spend is Railway: cycle-to-date **31.2 vCPU-hr, 1212.9 GB-hr memory,
0.82 GB egress**, dominated by the always-on container rather than deploys. The one real lever is
job cadence (`usgs.fetch_instantaneous` at `*/15` also keeps Neon warm against a 191.9
compute-hour free tier) — a science decision, not a unilateral optimisation.
