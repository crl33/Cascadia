"""CLI: python -m cascade_worker seed | run-once | run | worker | apply-queue-schema | queue-status

seed / run-once / run are the direct asyncio path and work on any database (sqlite included).
worker / apply-queue-schema / queue-status are the procrastinate path and require PostgreSQL
(ADR-0003); `worker` is the Railway entrypoint (jobs + periodic deferrer, graceful SIGTERM).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from cascade_core.db import create_schema
from cascade_core.seed import seed_all
from cascade_core.settings import Settings
from cascade_worker.queue import apply_queue_schema, create_queue_app, queue_status, run_worker
from cascade_worker.runtime import Runtime
from cascade_worker.scheduler import run_forever, run_once


async def _seed(rt: Runtime) -> dict[str, int]:
    await create_schema(rt.engine)
    async with rt.sessions() as session:
        return await seed_all(session, geo_dir=rt.settings.geo_dir, seed_file=rt.settings.seed_file)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="cascade_worker")
    parser.add_argument("command", choices=["seed", "run-once", "run", "worker", "apply-queue-schema", "queue-status"])
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.command in ("seed", "run-once", "run"):
        rt = Runtime.build(settings)
        if args.command == "seed":
            print(json.dumps(asyncio.run(_seed(rt))))
            return 0
        if args.command == "run-once":
            results = asyncio.run(run_once(rt))
            print(json.dumps([{"job": n, "ok": ok, "rows_written": rows, "error": err} for n, ok, rows, err in results], indent=1))
            return 0 if all(ok for _, ok, _, _ in results) else 1
        asyncio.run(run_forever(rt))
        return 0
    app = create_queue_app(settings)  # raises with a clear message on a non-PostgreSQL URL
    if args.command == "apply-queue-schema":
        print(json.dumps({"schema": asyncio.run(apply_queue_schema(app))}))
        return 0
    if args.command == "queue-status":
        print(json.dumps(asyncio.run(queue_status(app)), indent=1))
        return 0
    asyncio.run(run_worker(app))  # worker: run until SIGTERM/SIGINT (graceful shutdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
