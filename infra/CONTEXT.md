# infra/ — run it the same way everywhere

One backend image, mode chosen by the container command; cloud-agnostic: PostgreSQL +
S3 API are the only external contracts. Build context is always the REPO ROOT
(`docker build -f infra/Dockerfile .` — the root `.dockerignore` allowlists what ships).

| File | What it is |
|---|---|
| `Dockerfile` | `python:3.14-slim`, non-root user `cascade`. Layered for cache: pyprojects → third-party deps (extracted via tomllib; no Dockerfile-only pins — psycopg[binary,pool]/obstore/geoalchemy2 are declared by cascade-core, procrastinate by cascade-worker; alembic is deliberately absent, migrations run from a repo checkout via `scripts/migrate.sh`) → sources → simple pip installs of the 7 local packages → geo fixtures + entrypoint. `HEALTHCHECK` probes `/system/health` in api and all modes. |
| `docker-entrypoint.sh` | Mode selector: `api` → uvicorn on `${PORT:-8000}`; `worker` → `python -m cascade_worker worker`; `all` → api + worker as supervised siblings — if EITHER exits, the other is drained with SIGTERM and the container exits non-zero so the platform restart policy revives the pair (SIGTERM/SIGINT forwarded to both for graceful drain); anything else exec'd verbatim (so `python -m cascade_worker seed` and Railway full-command start commands both work). Writes `/tmp/cascade-run-mode` for the healthcheck probe. |
| `container-healthcheck.py` | Stdlib probe: GET `/system/health` when mode is api/uvicorn, exit 0 otherwise. Railway ignores it (uses its own Healthcheck Path). |
| `docker-compose.dev.yml` | Local parity: `postgis` (postgis/postgis:18-3.6, host 127.0.0.1:5433, named volume at `/var/lib/postgresql` — the pg18 mount point), `api` (127.0.0.1:8000) and `worker` built from `Dockerfile`, env from `../.env` (optional) + in-network `CASCADE_DB_URL`, gated on postgis health. All ports loopback-only. Clashes with a standalone `cascadia-pg` on 5433 — stop one. |
| `.env.example` | The environment contract (no secrets, placeholders only). Every variable the containers read; `POSTGRES_PASSWORD` is compose-dev-only. |
| `RUNBOOK-deploy.md` | First-time Railway deploy: account → project → two services from `crl33/Cascadia` with `infra/Dockerfile` + custom start commands; per-service variables (secrets marked); Neon pooled vs DIRECT strings (queue needs DIRECT — PgBouncer can't carry LISTEN/NOTIFY); Cloudflare R2 dashboard steps (wrangler OAuth has no R2 scope); Railway CLI auth for the orchestrator (project token recommended). |
| `gateway/` | Cloudflare Worker reverse-proxy for `cascadia.papsukkal.com` (see below). |

Resolved (2026-08-24 verification): `python -m cascade_worker worker` landed with the
procrastinate port (ADR-0003). The worker CLI now offers `seed | run-once | run | worker |
apply-queue-schema | queue-status`, so the `worker` service starts cleanly on current source
(verified live against the local PostGIS database; see
docs/research/pg-migration-verification-2026-08-24.md).

## Preview site (Cloudflare Pages)

The cinematic web spike deploys automatically from GitHub so each push to `main` is testable.

| | |
|---|---|
| URL | https://cascadia.papsukkal.com |
| Pages project | `cascadia` (account `dbad4adbc34ebf59fff33de8e6afe161`) |
| Repo | `crl33/Cascadia`, production branch `main` |
| Build | `npm ci --prefix apps/web && npm run build --prefix apps/web` |
| Output | `apps/web/dist` |
| API | Pages Function `functions/[[path]].js` — reverse proxy to `BACKEND_ORIGIN` (Pages secret, currently the Railway backend); fixture stub only when no origin is configured (previews) |
| Trigger | GitHub Action `.github/workflows/deploy-preview.yml` POSTs Pages deploy hook `github-main` (secret `CF_PAGES_DEPLOY_HOOK`) |

Do not point this hostname at jets/yachts/mail, or at Worker `papsukkal-site`.

`cascadia.papsukkal.com` is a Worker custom domain on `cascadia-gateway` (`infra/gateway/`) that reverse-proxies Pages production. Wrangler OAuth can attach Worker custom domains; it cannot write zone DNS records directly. Deploy the gateway with `npx wrangler deploy` from `infra/gateway/` if the hostname is missing.

When stub fixtures change, run `scripts/sync-pages-fixtures.sh` so `functions/fixtures/` stays in lockstep.

## Production backend (deployed 2026-08-24)

| | |
|---|---|
| Compute | Railway project `affectionate-stillness` (rename in UI if desired), service `papsukkal-backend`, env `production` — ONE container running api + worker — start command should be the entrypoint's `all` mode (supervised siblings; the container exits non-zero when either process dies so Railway restarts the pair — the previous `sh -c "python -m cascade_worker worker & exec uvicorn ..."` left the API serving with ingestion silently stopped when the worker died), built from `infra/Dockerfile` (`RAILWAY_DOCKERFILE_PATH`) |
| Public URL | https://papsukkal-backend-production.up.railway.app (proxied same-origin via the Pages gateway at cascadia.papsukkal.com) |
| Database | Neon `cascadia-papsukkal` (PG 18, PostGIS 3.6, `us-west-2`); API/worker use the pooled URL, the queue uses the DIRECT URL (`CASCADE_QUEUE_DB_URL`) |
| Raw archive | R2 bucket `cascadia-raw` (`CASCADE_OBJECT_STORE=s3`), content-addressed sha256 keys |
| Event Zero archive | R2 bucket `cascadia-event-zero` (`usgs_timeslices` copied; larger tiers pending owner cost approval) |
| Secrets | Railway service variables + Pages secret `BACKEND_ORIGIN` + local `~/.config/cascadia-papsukkal/` (0600) — never in git |
| R2 retention | `cascadia-raw` carries lifecycle rule `expire-nbm-90d`: objects under `nbm/` expire after 90 days (added 2026-08-24 for P3). NBM raw GRIB subsets are re-derivable from NOMADS/AWS within their own retention and the basin aggregates are stored separately, so the archive stays bounded at ~1.2 GB instead of growing ~400 MB/month forever. Observation and forecast raw payloads are NOT expired — they are the provenance of stored values. |
| Free-tier watchpoints | Neon compute-hours (15-min polling keeps the endpoint warm), Railway $5 Hobby/trial usage (single small container), R2 10 GB free (raw archive grows slowly; Event Zero tiers are paid) |
