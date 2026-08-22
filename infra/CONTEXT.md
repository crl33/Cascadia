# infra/ — run it the same way everywhere

Planned contents (Phase 0): `docker-compose.yml` (postgis, seaweedfs, api, worker), Dockerfiles
(single Python image, two entrypoints; static web build), `.env.example` (no secrets),
migration job, runbooks (`RUNBOOK-ingestion.md`, `RUNBOOK-provider-outage.md`). Cloud-agnostic:
PostgreSQL + S3 API are the only external contracts.

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
| Env | `NODE_VERSION=22`, `VITE_API_BASE=/` (same-origin) |

Do not point this hostname at jets/yachts/mail, or at Worker `papsukkal-site`.

When stub fixtures change, run `scripts/sync-pages-fixtures.sh` so `functions/fixtures/` stays in lockstep.
