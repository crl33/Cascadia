#!/usr/bin/env bash
# Run the whole offline test suite (unit + fixture + integration + contracts). No network.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
exec "$ROOT/.venv/bin/python" -m pytest -q "$@"
