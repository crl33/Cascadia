"""CLI: python -m cascade_worker seed | run-once | run"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from cascade_core.db import create_schema
from cascade_core.seed import seed_all
from cascade_core.settings import Settings
from cascade_worker.runtime import Runtime
from cascade_worker.scheduler import run_forever, run_once


async def _seed(rt: Runtime) -> dict[str, int]:
    await create_schema(rt.engine)
    async with rt.sessions() as session:
        return await seed_all(session, geo_dir=rt.settings.geo_dir, seed_file=rt.settings.seed_file)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="cascade_worker")
    parser.add_argument("command", choices=["seed", "run-once", "run"])
    args = parser.parse_args(argv)
    rt = Runtime.build(Settings.from_env())
    if args.command == "seed":
        print(json.dumps(asyncio.run(_seed(rt))))
        return 0
    if args.command == "run-once":
        results = asyncio.run(run_once(rt))
        print(json.dumps([{"job": n, "ok": ok, "rows_written": rows, "error": err} for n, ok, rows, err in results], indent=1))
        return 0 if all(ok for _, ok, _, _ in results) else 1
    asyncio.run(run_forever(rt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
