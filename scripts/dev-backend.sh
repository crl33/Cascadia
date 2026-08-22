#!/usr/bin/env bash
# Dev loop: install editable packages, seed the local sqlite DB, ingest once from the LIVE
# providers (network), then serve the read-only API on :8000. Ctrl-C stops uvicorn.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
bash "$ROOT/scripts/install-dev.sh"
PY="$ROOT/.venv/bin/python"
"$PY" -m cascade_worker seed
"$PY" -m cascade_worker run-once
exec "$ROOT/.venv/bin/uvicorn" cascade_api.main:app --host 127.0.0.1 --port 8000
