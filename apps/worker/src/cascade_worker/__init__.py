"""cascade_worker — the only process type that writes.

Owns: the runtime (engine, object store, archiving fetcher with rate limits), the job registry
with cadences, job-run bookkeeping for /system/health, and the CLI (seed | run-once | run).
Science and parsing live in packages; this module only sequences them.
"""
