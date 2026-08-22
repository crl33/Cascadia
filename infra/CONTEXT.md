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
| Trigger | GitHub Action `.github/workflows/deploy-preview.yml` POSTs Pages deploy hook `github-main` (secret `CF_PAGES_DEPLOY_HOOK`) |

Do not point this hostname at jets/yachts/mail, or at Worker `papsukkal-site`.

`cascadia.papsukkal.com` is a Worker custom domain on `cascadia-gateway` (`infra/gateway/`) that reverse-proxies Pages production. Wrangler OAuth can attach Worker custom domains; it cannot write zone DNS records directly. Deploy the gateway with `npx wrangler deploy` from `infra/gateway/` if the hostname is missing.

When stub fixtures change, run `scripts/sync-pages-fixtures.sh` so `functions/fixtures/` stays in lockstep.
