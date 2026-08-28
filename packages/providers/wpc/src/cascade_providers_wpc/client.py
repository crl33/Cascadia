"""WPC 5-km QPF file server (ftp-wpc.ncep.noaa.gov): the official national QPF, three files.

The scientifically sufficient subset (DATA_SOURCES W6, decided on measurement 2026-08-28): the
three 24-hour windows ``p24m_{cycle}f024/f048/f072`` — Day 1, Day 2, Day 3 — at ~300 KB each,
~2 MB/day across both cycles. The 6-hourly files carry nothing these cannot reconstruct at the
basin scale this platform works at, and the 120/168-h files reach past the 72-h hazard horizon.

**Publication precedes the nominal cycle.** Measured: the 12Z files land ~10:48Z, the 00Z files
~22:48Z the previous evening — WPC issues the "00Z" QPF before 00Z exists. The HTTP
Last-Modified is therefore the honest ``available_at`` and it is legitimately EARLIER than
``issued_at`` (the cycle identity); a 23:00Z replay may honestly see the 00Z-cycle QPF, because
the forecaster had genuinely published it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_WPC_QPF

BASE_URL = "https://ftp-wpc.ncep.noaa.gov/5km_qpf/"
WPC_HOSTS = frozenset({"ftp-wpc.ncep.noaa.gov"})
OBJECT_PREFIX = "wpc/"
#: Day 1 / Day 2 / Day 3, as forecast-hour suffixes of the 24-h accumulation files.
FORECAST_HOURS = (24, 48, 72)
#: Cycles that publish the full window set (the 06/18Z runs do not exist for p24m).
CYCLE_HOURS = (0, 12)

__all__ = [
    "BASE_URL",
    "CYCLE_HOURS",
    "FORECAST_HOURS",
    "OBJECT_PREFIX",
    "WPC_HOSTS",
    "cycle_candidates",
    "fetch_qpf_file",
    "qpf_filename",
]


def qpf_filename(cycle: datetime, fhour: int) -> str:
    return f"p24m_{cycle:%Y%m%d%H}f{fhour:03d}.grb"


def cycle_candidates(now: datetime, count: int = 3) -> list[datetime]:
    """The most recent 00/12Z cycles that may exist at ``now``, newest first.

    "May exist" includes the cycle ~70 minutes AHEAD of the clock (measured: files land
    ~48 minutes before the nominal hour), so the 23:10Z poll finds the next day's 00Z cycle.
    """
    if now.tzinfo is None:
        # astimezone() would silently reinterpret a naive instant as machine-local time —
        # a hindcast on a PST machine then reads a cycle 8 h in its future (review 2026-08-28)
        raise ValueError("cycle_candidates requires an aware datetime; naive instants are refused")
    horizon = now.astimezone(UTC) + timedelta(minutes=75)
    day = horizon.date()
    out: list[datetime] = []
    while len(out) < count:
        for hour in sorted(CYCLE_HOURS, reverse=True):
            candidate = datetime(day.year, day.month, day.day, hour, tzinfo=UTC)
            if candidate <= horizon and len(out) < count:
                out.append(candidate)
        day -= timedelta(days=1)
    return out


async def fetch_qpf_file(
    fetcher: ArchivingFetcher, session: AsyncSession, cycle: datetime, fhour: int
) -> FetchResult:
    return await fetcher.fetch(
        session,
        url=BASE_URL + qpf_filename(cycle, fhour),
        params=None,
        allowed_hosts=WPC_HOSTS,
        product_id=PRODUCT_WPC_QPF,
        prefix=OBJECT_PREFIX,
        suffix=".grb",
        accept="*/*",
    )
