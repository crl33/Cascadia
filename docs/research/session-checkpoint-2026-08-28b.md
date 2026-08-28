# Session checkpoint — 2026-08-28 (second checkpoint of the date)

Continuation point for the full-force implementation mission. Supersedes
`session-checkpoint-2026-08-28.md`. Every claim below was verified against the live system at
writing time, not inferred from intent; the landed / deployed / proven distinction is explicit.

## HEAD and tree

- **HEAD: `88fcbb3`** (`runbook: database URL variables must name the installed driver`),
  pushed; working tree clean except this checkpoint file. **29 commits this session** from
  `e7ba235` — hypsometry, MRMS, NWS alerts, antecedent QPE (contract **1.4.0**), WPC QPF, SSE,
  /system/metrics, SNODAS, C3 alert-dash, HEFS-quantiles endpoint (P5 opens), Event Zero MRMS
  backfill, mypy adoption, api_reader role, NWRFC reservoirs.
- No worktrees. Migration head **0005** (applied to production Neon). Jobs **17**, sources 16,
  products 20, stations **14** (7 reservoir stations added), all merged/seeded into Neon.

## Landed, deployed, AND proven in production (each verified live)

1. **NWS CAP alerts** — `nws.fetch_alerts` (5-min): append-only `official_alert` (migration
   0005), UGC→basin routing at write time (`method:basin-ugc-mapping@1.0.0`), envelopes fill
   `official_alerts`. Proven: 2 real east-side alerts stored, routed to zero seed basins
   (correct); freshness anchored valid-until-superseded (quiet weather ≠ outage).
2. **Antecedent QPE (contract 1.4.0)** — 6/24/72 h trailing sums anchored at the newest
   OBSERVED hour; partial = declared underestimate, never scaled. Proven live with real hours;
   panel section + e2e assertions + refreshed 1.4.0 production capture as the stub fixture.
3. **WPC official QPF** — `wpc.fetch_qpf` (10 11,23Z): Day 1/2/3 24-h windows, ~2 MB/day.
   Proven: 18 rows, Cedar Day-2 4.2 mm, **available_at 22:48Z < issued_at 00Z** (the measured
   publication inversion, stored verbatim). Forcing surface carries the 72-h official total as
   a context driver, never averaged with NBM (proven live on Cedar: 4.67 mm).
4. **SSE `/system/events`** — notify-then-fetch ({kind, available_at}, no payloads); poller
   runs ONLY while a client is connected; client invalidates live keys only, kind map pinned
   to the registry from both sides. Proven streaming through the Pages gateway.
5. **`/system/metrics`** — Prometheus projection of the health model (same registry walk).
   Proven live.
6. **SNODAS SWE** — `snodas.fetch_swe` (40 13Z): unmasked grid (BC headwaters), land-mean SWE +
   snow-covered fraction; saturated glacier cells excluded+flagged; static water mask
   understood. Proven: 36 rows (3-day lookback), Puyallup 77.83 mm exactly matching the
   fixture-pinned figure; susceptibility carries both as MODELED context drivers (proven live).
7. **C3 alert presence** — an alerted basin's edge goes DASHED (colour stays category — an Air
   Quality alert must not paint flood-amber). Landed+deployed; VISUAL proof deferred until a
   real alert covers a seed basin (style tests pin the mapping meanwhile).
8. **HEFS quantiles endpoint (P5 opens)** — `GET /forecast-points/{lid}/hefs/latest` serves
   the NWRFC ladder VERBATIM on the knowledge clock (§9(a)). Proven: MVEW1 11 levels × 121
   rows, CFS; 404 before available_at.
9. **Event Zero MRMS backfill** — 1590 rows, 265 hours (2025-12-05..16) from IEM, same
   method/masks as live (grid hash identical); available_at = retrieval (ADR-0010), original
   knowable instant preserved per row. Proven against the event: **129 mm/72 h Skagit ending
   at the 2025-12-12 08Z record crest**, ~5 mm/h peaks 30 h earlier.
10. **api_reader** — SELECT-only LOGIN role; API on `CASCADE_API_DB_URL`. Proven at the
    database: `pg_stat_activity` shows `api_reader` serving the API; INSERT refused
    (InsufficientPrivilege). Cost: two FAILED deploys from a URL missing the driver scheme
    (`postgresql+psycopg://` required) — runbook + memory updated; production never went down
    (failed deploys never serve).
11. **NWRFC reservoirs** — `nwrfc.fetch_reservoirs` (50 * * * *): 7 dams, 21 series,
    Observation rows (forebay/storage/inflow/outflow), units verbatim, datum never invented,
    SHEF multi-code instants collapsed by declared preference. **Proven**: bootstrap run
    succeeded 09:14:57Z; 264 rows across 12 serving series, newest instants 08:00Z, job `ok`.
12. **mypy** — contracts+geo+core CLEAN and pinned via `[tool.mypy].files`; hydrology's 67
    findings recorded, not admitted.

## Production health at writing

**`status: ok`, `reasons: []`** after the reservoir bootstrap — every one of the 17 jobs `ok`,
every monitored product `current`. Neon DB 47 MB; 51,198 observations, 3,291 derived features, 212 forecast
runs, 3,002 raw artifacts, 24 grid masks (3 grids × 6 basins + NBM sets).

## Gates (all green at HEAD)

offline pytest **558**, pg suite **15** (chain 0001→0005 on PostGIS; run with
`CASCADE_TEST_PG_URL=postgresql+psycopg://postgres:dev@127.0.0.1:5433/cascadia`), web vitest
**180**, Playwright e2e **22**, perf budget **16 queries** (documented ladder 13→14→15→16),
lint-imports 5/5, ruff clean, mypy clean (21 files). Mutation testing this session: alerts 4/4,
antecedent 4/4, WPC 4/4, SSE 2/2, SNODAS 4/4, NWRFC 4/4 — every mutant caught after two test
strengthenings that the mutations themselves exposed (vacuous priming test; empty anchor
catalogue).

## Cost / storage

- R2 lifecycle rules: `nbm/` 90 d, `mrms/` 30 d, `wpc/` 90 d (new), `snodas/` 30 d (new),
  `hefs/` never. New steady-state raw: WPC ~2 MB/day, SNODAS ~5-7 MB/day (winter larger),
  NWRFC ~0.3 MB/day, alerts ~0.1 MB/day. Event Zero MRMS raw NOT archived (re-fetchable IEM;
  cited by URL+sha256).
- Railway: ~8 image builds this session (each push auto-builds; 2 failed builds cost nothing
  in serving). GitHub Actions free (public repo).
- Neon: db 47 MB; api_reader adds one pooled connection.

## Newly unblocked

- **Rain-on-snow gate, half-open**: `basin_snow_covered_fraction` (MODELED) now stored daily;
  the gate still wants an OBSERVED snow-covered area (VIIRS VNP10A1F, S9) before any
  rain-on-snow fraction is computed.
- **P6 hindcast antecedent**: Dec-2025 hourly QPE exists with preserved original availability;
  the hindcast harness can now compute honest antecedent windows through the event.
- **P5 continuation**: the quantile ladder is served; next is the RIVER panel consuming it and
  the agreement surface comparing WPC-official vs NBM QPF (both stored per basin per cycle).
- **Reservoir surfacing**: rows exist; nothing renders them yet (river/basin panel section,
  C-side).

## Known open items (deliberate, with reasons)

- `ingest_writer` role: blocked on partition-DDL ownership (monthly maintenance job creates
  partitions) — needs an ADR (migrator-run partition path vs SECURITY DEFINER helper).
  Grants drafted in `scripts/sql/roles.sql`.
- checkSuites CI gate on Railway auto-deploy: needs OWNER console (project-token mutation 500s).
- Alert-dash VISUAL proof: pending a real alert over a seed basin; kind map + style tests pin it.
- Several researched NWRFC series serve empty today (DIAW1 all; UBDW1 partial) —
  `SERVED_ON_CAPTURE` pins reality; the poll keeps asking.
- hydrology mypy (67 findings); DIAW1/TLRW1/MORW1 empty series.

## Post-checkpoint additions (same session, each proven live)

- **Reservoir surfacing** — `GET /basins/{id}/reservoirs` (as_of-honest; empty list is the
  Nooksack's truth) + a panel Reservoirs section (verbatim units, "(datum unstated)" beside
  every forebay number). Proven: Howard Hanson 1154.33 ft / 35.16 k-acre-feet / 40 cfs inflow
  live; Nooksack `[]`.
- **HEFS band on the hydrograph (C5 opens)** — the provider's 0.05/0.50/0.95 traces as a band
  + dashed median under full overlay honesty (flow axis only; exact levels or nothing; case-
  insensitive unit orthography; clipped rows COUNTED in the legend). **Visually proven in
  production**: `img/hefs-band-aubw1-2026-08-28.png` (band + MODELED badge + "80 rows beyond
  the charted window not drawn") and `img/hefs-refusal-mvew1-2026-08-28.png` (the stage-axis
  refusal, printed verbatim). Gotcha recorded: the Pages bundle deploys a minute behind the
  Railway API — a just-deployed feature can 404/no-op in the browser briefly.

## Adversarial review and remediation (post-checkpoint, same session)

A 27-agent adversarial workflow (find x4 module groups → refute-verify per finding) reviewed
every semantic module this session landed. ~20 findings CONFIRMED, several by concrete
reproduction against real PostgreSQL. All remediated in three batches (commits `c28acc9`,
`3ecb48a`, `8456307`+`b232295`), each fix pinned by a test. Highlights:

- antecedent read-window truncation after archive lag ("missing" said of stored hours);
- active_alerts unbounded per-envelope history + never-expiring CAP rows (now: SQL time
  slice, 48 h cap on endless messages, references scanned thin across ALL history so a
  short-lived Cancel keeps suppressing its long-lived target — query budget 16→17, deliberate);
- SSE zombie streams after queue-full drops; quiet-poll cache-defeating invalidations
  (valid-until anchors keep valid_time content-pure);
- WPC late-published cycles permanently skipped (reproduced end-to-end; the loop now visits
  every candidate) and half-published cycles crashing the job (now NOT-READY/retry);
- SNODAS non-UTC `now` wedging PostgreSQL on the identity constraint (reproduced); partial
  days now complete row-by-row; masks per each field's own grid hash; corrupt negatives named;
- NWRFC last-child-wins parsing fabricating readings (QR's element is `<discharge>` — the
  captures' own word; unexpected siblings refuse);
- Hydrograph band clipping (both sides, counted), truthful band-absence sentences, surfaced
  fetch errors, event-crest = maximum; ReservoirsSection error state; dead kind-map prefixes.

Also landed post-checkpoint: **QPF agreement live** (deltas + placement in production, every
design-note rule mutation-killed), **ADR-0018** (knowable_at hindcast clock), **ADR-0019 +
migration 0006 + ingest_writer LIVE** (the worker runs append-only in production; partition
DDL through the one SECURITY DEFINER door; proven by refused UPDATE/DELETE and a
writer-created partition owned by the migrator; role census: api_reader + ingest_writer
serving, owner idle). VIIRS S9 recorded as externally blocked (Earthdata credentials are an
owner action).

## The remediation's own regression (fixed same session)

The review remediation itself shipped one: keeping the freshness anchor's `valid_time`
content-pure (to silence the SSE broker's quiet-poll chatter) flipped live health to
`degraded` — `compute_freshness` anchors on `valid_time`, so healthy valid-until products
(thresholds 4 d, alerts 16 h of quiet) read STALE while all seventeen jobs ran green. The
offline suite could not see it because its test pinned the anchor's FIELDS, not the computed
STATE. Fixed in `55e412b`: `FreshnessAnchor.content_time` carries the pure content clock for
the broker while `valid_time` re-absorbs the poll for freshness — two questions, two fields —
plus an end-to-end state pin (old content + fresh poll must compute `current`). The lesson is
in the production-verification memory: re-check live health after every deploy touching the
health path.

## Dependency-ordered continuation

(The stub fixture was refreshed as part of this checkpoint: the committed capture is 1.4.0
with 98 refs, SNODAS/WPC/agreement drivers aboard, and the full e2e suite re-pinned to it.)


1. **Agreement-surface design note for WPC-vs-NBM QPF** (two KINDS; the comparison is
   information, never an average) — design before code.
2. **VIIRS SCA (S9)** — the observed half of the rain-on-snow gate; measure granule cost first
   (LAADS/LANCE auth needed — check keys).
3. **P6 hindcast harness design**: knowledge-time model for backfilled rows
   (`original_available_at` vs `available_at`) — an ADR before code.
4. **ingest_writer ADR** (partition DDL ownership); then the role.
5. Opportunistic: hydrology mypy burn-down; C3b MRMS raster tiles; SSE client reconnect UX.

