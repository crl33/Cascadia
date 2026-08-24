#!/bin/bash
# Cascadia Papsukkal container entrypoint — one image, mode chosen by the
# container command (Dockerfile CMD, compose `command:`, Railway start command):
#   api    -> uvicorn serving cascade_api on ${PORT:-8000}
#   worker -> python -m cascade_worker worker (procrastinate queue consumer)
#   all    -> api + worker as sibling processes under this shell (the
#             single-container production mode). The moment EITHER sibling
#             exits, the other is drained with SIGTERM and the container exits
#             non-zero so the platform restart policy revives the pair — a dead
#             worker can never linger behind a healthy-looking API with
#             ingestion silently stopped. SIGTERM/SIGINT are forwarded to both
#             children for a graceful drain (uvicorn finishes in-flight
#             requests; procrastinate finishes running jobs).
# Anything else is exec'd verbatim (e.g. `python -m cascade_worker seed`,
# `python -m cascade_worker run-once`, or a full uvicorn command line —
# Railway custom start commands land here and behave identically).
set -eu

MODE="${1:-api}"
# The HEALTHCHECK probe reads this marker: api and all modes get an HTTP probe.
printf '%s\n' "$MODE" > /tmp/cascade-run-mode

case "$MODE" in
  api)
    exec uvicorn cascade_api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
    ;;
  worker)
    exec python -m cascade_worker worker
    ;;
  all)
    uvicorn cascade_api.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
    api_pid=$!
    python -m cascade_worker worker &
    worker_pid=$!

    shutdown_requested=0
    forward_term() {
      shutdown_requested=1
      kill -TERM "$api_pid" "$worker_pid" 2>/dev/null || true
    }
    trap forward_term TERM INT

    # Block until ONE child exits; a trapped signal also interrupts the wait
    # (trap runs first, wait returns >128), which is exactly the drain path.
    set +e
    wait -n
    first_status=$?
    kill -TERM "$api_pid" "$worker_pid" 2>/dev/null
    wait "$api_pid"
    api_status=$?
    wait "$worker_pid"
    worker_status=$?
    set -e

    if [ "$shutdown_requested" -eq 1 ]; then
      echo "entrypoint(all): SIGTERM/SIGINT — drained api=$api_status worker=$worker_status" >&2
      exit 143
    fi
    echo "entrypoint(all): a supervised process exited (wait=$first_status api=$api_status worker=$worker_status) — exiting non-zero so the platform restarts the pair" >&2
    exit 1
    ;;
  *)
    exec "$@"
    ;;
esac
