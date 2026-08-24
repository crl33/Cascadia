#!/bin/sh
# Cascadia Papsukkal container entrypoint — one image, mode chosen by the
# container command (Dockerfile CMD, compose `command:`, Railway start command):
#   api    -> uvicorn serving cascade_api on ${PORT:-8000}
#   worker -> python -m cascade_worker worker (procrastinate queue consumer, M2)
# Anything else is exec'd verbatim (e.g. `python -m cascade_worker seed`,
# `python -m cascade_worker run-once`, or a full uvicorn command line —
# Railway custom start commands land here and behave identically).
set -eu

MODE="${1:-api}"
# The HEALTHCHECK probe reads this marker: only api mode gets an HTTP probe.
printf '%s\n' "$MODE" > /tmp/cascade-run-mode

case "$MODE" in
  api)
    exec uvicorn cascade_api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
    ;;
  worker)
    exec python -m cascade_worker worker
    ;;
  *)
    exec "$@"
    ;;
esac
