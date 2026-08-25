"""Live canary (network; never in CI): the NBM NOMADS subset path.
Usage: .venv/bin/python tests/canaries/nbm_canary.py  -> JSON report on stdout, exit 0 always.

Asks whether the path forcing v0 is built on still has the shape it was built for: the CGI
answers with GRIB2, the WA clip is still 99x142 with the same Section 3 hash (so stored basin
masks still fit), the 0-N day cumulative windows and percentile ladders are present, SNOWLVL
is still selectable by (0, 19, 236), and one cycle still costs ~1.82 MB."""

import asyncio, json

from cascade_providers_nbm.canary import check


if __name__ == "__main__":
    print(json.dumps(asyncio.run(check()), indent=1, default=str))
