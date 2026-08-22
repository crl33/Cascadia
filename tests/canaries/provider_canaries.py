"""Scheduled live canaries (network; never in CI): USGS IV and NWPS reachability/schema/flow.
Usage: .venv/bin/python tests/canaries/provider_canaries.py  -> JSON report on stdout, exit 0 always."""

import asyncio
import json

from cascade_providers_nwps.canary import check as nwps_check
from cascade_providers_usgs.canary import check as usgs_check


async def main() -> None:
    usgs, nwps = await asyncio.gather(usgs_check(), nwps_check())
    print(json.dumps({"usgs": usgs, "nwps": nwps}, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
