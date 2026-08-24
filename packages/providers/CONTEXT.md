# packages/providers — adding a data source

One job: turn an external product into archived raw artifacts and normalized, provenance-
carrying rows. Nothing here computes features or assessments.

## Inputs
- Reference (every adapter): `../../docs/DATA_SOURCES.md` (the provider's row: authority,
  cadence, latency, units, sentinels, quality flags, licensing), `../../docs/DATA_DOCTRINE.md`
  §1–§8, `../../.claude/skills/vibesec/references/cascadia-papsukkal-addendum.md` §1–§2.
- Working: the captured fixtures in `<name>/fixtures/` with `manifest.yaml`.

Do NOT load: other providers' code, hydrology methods, the web app.

## Process (every provider, same shape)
1. `client.py` — allowlisted base URL constant; timeout; max bytes; User-Agent with contact;
   per-host token bucket; circuit breaker; archive raw payload (sha256 → object store) before
   returning bytes.
2. `parser.py` — strict typed parse of the fields we use; tolerate extras; typed errors.
3. `normalize.py` — units (native + canonical), times (UTC + provider zone), sentinels ⇒
   quality flags, `available_at`; emit `Observation` / `ForecastRun` / `Threshold` /
   `GridProduct` rows with `raw_artifact_id`.
4. `jobs.py` — idempotent job(s) keyed by `(product_id, scope, issued_at|valid_time)`;
   declared cadence; health reporting.
5. `fixtures/` — the eight cases in `../../docs/TESTING.md` §3.
6. `canary.py` — reachable? schema? flowing? (non-blocking; feeds `/system/health`).

## Outputs
- `DataSource` and `SourceProduct` registry rows (seed migration or data file).
- Rows in the value tables; raw artifacts in object storage.

## Human check
Open one normalized row and its raw artifact side by side: value, unit, valid time (with
offset), quality and `available_at` must be traceable to bytes in the payload. If a number
cannot be pointed at in the raw payload, the adapter is wrong.
