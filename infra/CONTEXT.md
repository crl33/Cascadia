# infra/ — run it the same way everywhere

One backend image, mode chosen by the container command; cloud-agnostic: PostgreSQL +
S3 API are the only external contracts. Build context is always the REPO ROOT
(`docker build -f infra/Dockerfile .` — the root `.dockerignore` allowlists what ships).

| File | What it is |
|---|---|
| `Dockerfile` | `python:3.14-slim`, non-root user `cascade`. Layered for cache: pyprojects → third-party deps (extracted via tomllib) + prod-only runtime (psycopg, procrastinate, obstore, geoalchemy2, alembic — pinned here until package pyprojects declare them, M2) → sources → simple pip installs of the 7 local packages → geo fixtures + entrypoint. `HEALTHCHECK` probes `/system/health` in api mode only. |
| `docker-entrypoint.sh` | Mode selector: `api` → uvicorn on `${PORT:-8000}`; `worker` → `python -m cascade_worker worker`; anything else exec'd verbatim (so `python -m cascade_worker seed` and Railway full-command start commands both work). Writes `/tmp/cascade-run-mode` for the healthcheck probe. |
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
| API | Pages Function `functions/[[path]].js` — same fixture stub as `apps/web/dev/stub-api.mjs` |
| Trigger | GitHub Action `.github/workflows/deploy-preview.yml` POSTs Pages deploy hook `github-main` (secret `CF_PAGES_DEPLOY_HOOK`) |

Do not point this hostname at jets/yachts/mail, or at Worker `papsukkal-site`.

`cascadia.papsukkal.com` is a Worker custom domain on `cascadia-gateway` (`infra/gateway/`) that reverse-proxies Pages production. Wrangler OAuth can attach Worker custom domains; it cannot write zone DNS records directly. Deploy the gateway with `npx wrangler deploy` from `infra/gateway/` if the hostname is missing.

When stub fixtures change, run `scripts/sync-pages-fixtures.sh` so `functions/fixtures/` stays in lockstep.
