"""Docker HEALTHCHECK probe. In api mode, GET /system/health on the local
port and require HTTP 200. In any other mode (worker, one-shot commands)
exit 0 — there is no HTTP server to probe. Stdlib only."""
import os
import sys
import urllib.request

try:
    with open("/tmp/cascade-run-mode", encoding="ascii") as f:
        mode = f.read().strip()
except OSError:
    mode = ""

if mode != "api" and not mode.startswith("uvicorn"):
    sys.exit(0)

port = os.environ.get("PORT", "8000")
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/system/health", timeout=4) as resp:
        sys.exit(0 if resp.status == 200 else 1)
except Exception:
    sys.exit(1)
