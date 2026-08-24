# RUNBOOK — first deploy of the backend (Railway + Neon + R2)

Audience: a first-time Railway user with nothing preconfigured. Outcome: two Railway
services (`api`, `worker`) built from `infra/Dockerfile` in the GitHub repo
`crl33/Cascadia`, talking to a Neon PostgreSQL database, archiving raw payloads to
Cloudflare R2. Nothing in this runbook is a secret; every secret is named here but
lives only in the platforms' secret stores.

## 0. What you need before starting

- A GitHub account that can see the repo `crl33/Cascadia` (the deploy source).
- A Neon account (free tier is fine) — https://neon.tech
- A Cloudflare account with R2 enabled (section 5) — only needed once the worker
  writes raw payloads to object storage; the api/worker will run without it using
  `CASCADE_OBJECT_STORE=local` (ephemeral on Railway — fine for a first smoke test,
  wrong for production).

## 1. Create the Railway account and project

1. Go to https://railway.app → **Login** → **Sign in with GitHub**. Authorize Railway.
2. Railway may ask for a plan; the Hobby plan is enough for this deployment.
3. Click **New Project** → **Deploy from GitHub repo**.
4. If `crl33/Cascadia` is not listed, click **Configure GitHub App** and grant Railway
   access to that repository, then pick it.
5. This creates the project with one service. Rename the project (top-left) to
   something like `cascadia-papsukkal`.

## 2. Create the two services (same repo, same Dockerfile, different start command)

The repo produces ONE image with two run modes; the container command selects the mode
(see `infra/docker-entrypoint.sh`). Railway's "Custom Start Command" is that command.

### 2.1 Service `api`

1. Click the service that was created from the repo. Rename it `api`
   (Settings → Service name).
2. **Settings → Source**: Root Directory = `/` (the repo root — the Dockerfile COPYs
   `packages/`, `apps/`, `tests/fixtures/geo/`, so the build context must be the root).
   Branch = `main`.
3. **Settings → Build**: Builder = `Dockerfile`, Dockerfile Path = `infra/Dockerfile`.
   (If the UI hides this field, set a service variable `RAILWAY_DOCKERFILE_PATH=infra/Dockerfile`
   instead — same effect.)
4. **Settings → Deploy → Custom Start Command**:

       uvicorn cascade_api.main:app --host 0.0.0.0 --port ${PORT:-8000}

   Railway injects `PORT` at runtime; do not set it yourself.
5. **Settings → Deploy → Healthcheck Path**: `/system/health`
   (Railway ignores the image's Docker HEALTHCHECK; this field is its replacement.)
6. **Settings → Networking → Public Networking → Generate Domain**. Note the
   `*.up.railway.app` URL — the Worker gateway will proxy `/api/*` to it (M1).

### 2.2 Service `worker`

1. In the project canvas: **+ New** (or right-click) → **GitHub Repo** → pick
   `crl33/Cascadia` again. Rename the new service `worker`.
2. Same Source and Build settings as the api (Root Directory `/`, Dockerfile
   `infra/Dockerfile`).
3. **Settings → Deploy → Custom Start Command**:

       python -m cascade_worker worker

4. No public networking, no healthcheck path — the worker serves no HTTP.

Every push to `main` now rebuilds and redeploys both services.

## 3. Neon database (both connection strings)

1. In Neon: **New Project** (pick a region near Railway's, e.g. AWS us-west-2),
   database name e.g. `cascadia`.
2. Neon's connection widget ("Connect") offers TWO hosts for the same database:
   - **Pooled** — hostname contains `-pooler` (PgBouncer). Fine for the app's normal
     queries.
   - **Direct** — same hostname without `-pooler`. REQUIRED for the procrastinate
     queue: PgBouncer cannot carry LISTEN/NOTIFY, so a pooled host silently breaks
     job wakeups.
3. Copy both strings and convert the scheme for SQLAlchemy: replace leading
   `postgres://` or `postgresql://` with `postgresql+psycopg://`, keep
   `?sslmode=require`.
4. PostGIS: Neon supports `CREATE EXTENSION postgis;` — run it once in the Neon SQL
   editor on the `cascadia` database (migrations will assert it exists).

(Railway also offers its own Postgres plugin; we deliberately use Neon — managed
PostGIS, branching, and the pooled/direct split are the reasons.)

## 4. Environment variables per service

Set these under each service → **Variables**. Everything marked **secret** contains a
credential: paste values only into Railway's variable store, never into the repo, chat
logs, or files. All names come from `infra/.env.example` (the environment contract).

### `api` service

| Variable | Value | Secret? |
|---|---|---|
| `CASCADE_DB_URL` | Neon **pooled** string, `postgresql+psycopg://…-pooler…/cascadia?sslmode=require` | **yes** (embedded password) |
| `CASCADE_CORS_ORIGINS` | `https://cascadia.papsukkal.com,https://cascadia-c7y.pages.dev` | no |
| `CASCADE_CONTACT` | a real reachable email (goes into the outbound User-Agent) | no |

Not needed on the api: `PORT` (Railway injects it), `CASCADE_GEO_DIR` / `CASCADE_RAW_DIR`
(baked into the image), queue/object-store variables (the api neither queues nor archives).

### `worker` service

| Variable | Value | Secret? |
|---|---|---|
| `CASCADE_DB_URL` | Neon **pooled** string (same as api) | **yes** |
| `CASCADE_QUEUE_DB_URL` | Neon **DIRECT** (non-pooled) string — see section 3 | **yes** |
| `CASCADE_OBJECT_STORE` | `s3` (or `local` for a first smoke test — ephemeral!) | no |
| `CASCADE_S3_ENDPOINT` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` | no |
| `CASCADE_S3_BUCKET` | the R2 bucket name (e.g. `cascadia-raw`) | no |
| `AWS_ACCESS_KEY_ID` | R2 API token key id (section 5) — read by obstore, not Settings | **yes** |
| `AWS_SECRET_ACCESS_KEY` | R2 API token secret (section 5) | **yes** |
| `CASCADE_USGS_API_KEY` | USGS OGC API key — only once the OGC adapter lands (M3) | **yes** |
| `CASCADE_CONTACT` | same as api | no |

Tip: put shared values (`CASCADE_DB_URL`, `CASCADE_CONTACT`) in the project's
**Shared Variables** and reference them from both services.

## 5. Cloudflare R2 (dashboard steps the user must do)

The orchestrator cannot do this part: the current wrangler OAuth token has **no R2
scope**, so R2 must be enabled and credentialed by a human in the Cloudflare dashboard.

1. Cloudflare dashboard → **R2 Object Storage** → if prompted, enable R2 for the
   account (requires accepting R2 pricing and having a payment method on file; the
   free tier — 10 GB storage, no egress fees — covers this workload for a long time).
2. **Create bucket** → name e.g. `cascadia-raw`, location hint North America. Leave
   versioning/lifecycle defaults for now.
3. R2 overview → **Manage R2 API Tokens** → **Create API token**:
   - Permission: **Object Read & Write**
   - Scope: **Apply to specific buckets only** → select `cascadia-raw`
   - TTL: no expiry (rotate manually) or your policy's maximum.
4. Cloudflare shows the **Access Key ID**, **Secret Access Key**, and the S3 endpoint
   `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` exactly once — paste them straight
   into the Railway `worker` variables (section 4) and nowhere else.

## 6. Letting the orchestrator (Claude) drive Railway

Two ways to give the automation a Railway CLI session; both end with
`railway status` working non-interactively.

**Option A — interactive login (human present):** run `railway login` in a terminal
(installs: `npm i -g @railway/cli` or `brew install railway`). It opens a browser
pairing flow; the CLI stores a session for your whole account. Simple, but the token
is account-wide and tied to your interactive session.

**Option B — project token (recommended):** in the Railway project →
**Settings → Tokens** → create a **Project Token** scoped to this project +
environment (`production`). Hand it to the orchestrator as the environment variable
`RAILWAY_TOKEN` (e.g. prefix it on invocations: `RAILWAY_TOKEN=… railway up`). It
cannot touch other projects, survives your logout, and revokes in one click — that
scoping is why it is the recommended path. Treat it as a secret: environment
variable only, never in a file.

## 7. First-deploy smoke test

1. Both services green in Railway → open `https://<api-domain>/system/health` — expect
   HTTP 200 JSON (states may be `unknown`/`down` until the worker has run jobs).
2. Seed once (schema + stations): Railway → `worker` service → ⋯ → one-off command
   (or temporarily set the start command to) `python -m cascade_worker seed`, then
   restore `python -m cascade_worker worker`.
3. `https://<api-domain>/basins/basin:skagit/state` should validate against the 1.1.0
   contracts (M1 exit test, together with the Playwright live-API suite).

## Local parity

`docker compose -f infra/docker-compose.dev.yml up --build` runs the same image
against local PostGIS 18/3.6, everything bound to 127.0.0.1 (API on :8000, Postgres
on :5433). Stop any standalone `cascadia-pg` container first — it holds port 5433.

## Operational gotcha discovered 2026-08-24: Railway start command bypasses ENTRYPOINT

A Railway custom start command replaces the image's ENTRYPOINT+CMD, not just CMD. A start
command of `all` therefore executes a literal `all` binary (instant exit, deployment FAILED
with an empty runtime log and build logs that innocently end at "image push"). The correct
production start command is:

    /usr/local/bin/docker-entrypoint.sh all

Diagnosis pattern for "build green, deploy FAILED, no runtime logs": the container command
never executed - check the start command against the entrypoint contract before suspecting
the registry or the healthcheck.
