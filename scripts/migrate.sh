#!/usr/bin/env bash
# Apply the database schema, then the Procrastinate queue schema (when that CLI exists).
# Connection comes from CASCADE_ALEMBIC_URL / CASCADE_DB_URL in the environment —
# env var names only, no credentials in this repository, ever.
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

alembic -c infra/migrations/alembic.ini upgrade head
python -m cascade_worker apply-queue-schema || echo "queue schema step pending"
