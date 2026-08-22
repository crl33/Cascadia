# apps/api — read-only projections

One job: answer the spike API spec from the database through `as_known_at(session, as_of)` and
the contract models. It never fetches from a provider and has no mutating endpoint.

## Inputs
- Environment (`CASCADE_DB_URL`, `CASCADE_CORS_ORIGINS`, `CASCADE_GEO_DIR`), the seeded sqlite DB
  written by `apps/worker`, and the geo LOD fixtures for `/basins` and `/basins/{id}/geometry`.

## Outputs
- `GET /basins`, `/basins/{id}/geometry`, `/basins/{id}/state`, `/viz/basins`, `/viz/rivers`,
  `/forecast-points/{LID}/state`, `/forecast-points/{LID}/runs/latest`,
  `/stations/{id}/series`, `/scene/summary`, `/search`, `/system/health`; `/openapi.json`.
- Every read accepts `as_of=<ISO>`; envelopes are `ContractEnvelope.model_dump(mode="json",
  by_alias=True)`; limits: `hours <= 720`, ids by pattern, `q <= 64` chars.

## Human check
`curl 'localhost:8000/viz/rivers?basin=basin:skagit'` — the observed stage value, its
`valid_time`, and the `provisional` flag must match the USGS row in sqlite and the archived raw
file. With `as_of` set before the first ingestion, every category is `unknown` with a reason.
