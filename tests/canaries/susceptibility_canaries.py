"""Scheduled live canaries for SUSCEPTIBILITY v0 (network; never in CI, never blocking).
Usage: .venv/bin/python tests/canaries/susceptibility_canaries.py  -> JSON on stdout, exit 0 always."""

import asyncio, json

from cascade_providers_awdb.canary import check as awdb_check
from cascade_providers_usgs.stats_canary import check as usgs_stats_check


async def main() -> None:
    # Sequential, not gathered: two providers, one at a time, is the polite shape (DATA_SOURCES §5.5).
    usgs = await usgs_stats_check()
    awdb = await awdb_check()
    print(json.dumps({"usgs_stats": usgs, "awdb": awdb}, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
