"""NBM v5.0 client: NOMADS server-side subsets (primary) and the S3 PDS archive (fallback).

Two origins, deliberately (docs/research/p3-surfaces-design-2026-08-24.md §1.2-§1.3, FACT):

- **NOMADS ``filter_blend.pl``** is the primary path. It clips a GRIB2 file to a lat/lon box
  server-side, which is the whole cost argument for this surface: the 12Z ``qmd.f072`` CONUS
  file is 785 MB and the WA-box subset of its APCP records is 1.05 MB — a factor of 751. A
  GRIB2 record is spatially monolithic, so no client-side range trick can do this.
- **``noaa-nbm-grib2-pds`` on S3** is archive/backfill only (``.idx`` + ranged GET). It works
  (verified), but a ranged GET returns a whole-CONUS record, 35 MB per cycle for the twelve
  records forcing v0 needs. NOMADS keeps only 1-2 days, so S3 is the recovery path after a
  long outage, and its cost is why it is not the daily one.

Direct GETs of the NOMADS ``/pub/data/...`` file tree return 403: NOMADS blocks automated
traversal of the raw tree but not the filter CGI (verified under four User-Agents). Only the
CGI is called here.

Every subset is archived under the ``nbm/`` object-store prefix with retention class
``gridded-90d``: the R2 lifecycle rule ``expire-nbm-90d`` expires those bytes after 90 days
(infra/CONTEXT.md, DATA_DOCTRINE §13) while the RawArtifact row survives, so provenance can
say the grid expired rather than 404.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_NBM_CORE, PRODUCT_NBM_QMD

BASE_URL = "https://nomads.ncep.noaa.gov/cgi-bin/filter_blend.pl"
ARCHIVE_BASE_URL = "https://noaa-nbm-grib2-pds.s3.amazonaws.com/"
ALLOWED_HOSTS = frozenset({"nomads.ncep.noaa.gov"})
ARCHIVE_ALLOWED_HOSTS = frozenset({"noaa-nbm-grib2-pds.s3.amazonaws.com"})

OBJECT_PREFIX = "nbm/"
#: The CGI subsets server-side and legitimately takes 15-20 s per file (measured 16.1 s for
#: f024, 18.3 s for f072), so these calls override the fetcher's 30 s default rather than
#: failing intermittently against it.
SUBSET_TIMEOUT_S = 120.0
RETENTION_CLASS = "gridded-90d"
SUFFIX = ".grib2"
ACCEPT = "application/octet-stream"

#: qmd runs only for these cycles and lands ~7 h 20 m later (design §1.1, measured).
QMD_CYCLE_HOURS = (0, 6, 12, 18)
#: The 0-N day cumulative APCP windows live one per file: f024 -> 0-1 day, f048 -> 0-2 day,
#: f072 -> 0-3 day. One file per horizon, not one file per forecast hour.
QMD_HORIZONS_H = (24, 48, 72)
#: Snow level comes from `core` (there are no QPF percentiles in core, and no SNOWLVL in qmd).
#: **Measured live 2026-08-24 (18Z core `.idx` sidecars):** `core` publishes the 15 SNOWLVL
#: PERCENTILE levels through f048 only -- f024 and f048 carry 16 SNOWLVL records (15 percentiles
#: + the deterministic field), while f054, f060, f066 and f072 carry the deterministic
#: `SNOWLVL:0 m above mean sea level` record ALONE. Asking for a percentile at f072 therefore
#: buys a subset that cannot contain the field, so the horizon list stops where the provider's
#: percentiles stop. (Only the shortest lead is ever displayed: `forcing._nearest_snow_row`
#: picks it, so nothing downstream loses a number by this.)
CORE_HORIZONS_H = (24, 48)

_FILE_RE = re.compile(r"^blend\.t\d{2}z\.(core|qmd)\.f\d{3}\.co\.grib2$")


@dataclass(frozen=True)
class SubRegion:
    """A NOMADS ``subregion`` box in degrees, longitudes negative-west."""

    toplat: float
    bottomlat: float
    leftlon: float
    rightlon: float

    def params(self) -> dict[str, str]:
        # `subregion=` must be present and empty; the CGI keys off its presence.
        return {
            "subregion": "",
            "toplat": f"{self.toplat:.2f}",
            "leftlon": f"{self.leftlon:.2f}",
            "rightlon": f"{self.rightlon:.2f}",
            "bottomlat": f"{self.bottomlat:.2f}",
        }


#: The union of the six seed basin bounding boxes (-122.7155..-120.6546, 46.7823..49.3134),
#: rounded outward. Returns a 99 x 142 = 14,058-point clip of the 2345 x 1597 CONUS grid.
WA_BASINS = SubRegion(toplat=49.40, bottomlat=46.70, leftlon=-122.90, rightlon=-120.55)


@dataclass(frozen=True)
class Cycle:
    """One NBM model cycle: the date and hour of the run, in UTC."""

    year: int
    month: int
    day: int
    hour: int

    @classmethod
    def from_datetime(cls, dt: datetime) -> Cycle:
        d = dt.astimezone(UTC)
        return cls(d.year, d.month, d.day, d.hour)

    @property
    def issued_at(self) -> datetime:
        return datetime(self.year, self.month, self.day, self.hour, tzinfo=UTC)

    @property
    def yyyymmdd(self) -> str:
        return f"{self.year:04d}{self.month:02d}{self.day:02d}"

    def dir_for(self, kind: str) -> str:
        return f"/blend.{self.yyyymmdd}/{self.hour:02d}/{kind}"

    def file_for(self, kind: str, fhour: int) -> str:
        return f"blend.t{self.hour:02d}z.{kind}.f{fhour:03d}.co.grib2"

    def __str__(self) -> str:
        return f"{self.yyyymmdd}T{self.hour:02d}Z"


def latest_qmd_cycle(now: datetime, *, latency_hours: float = 7.5) -> Cycle:
    """The newest qmd cycle that should have landed by ``now``.

    qmd starts 6 h 40 m after its cycle and the f072 file was observed at cycle + 7 h 20 m
    (design §1.1). ``latency_hours`` is that observation rounded up, not a published schedule
    (DATA_SOURCES open item 12); the job re-checks by fetching, and a miss is a miss, never a
    substituted cycle.
    """
    t = now.astimezone(UTC)
    candidate = t.replace(minute=0, second=0, microsecond=0)
    for _ in range(48):  # two days back is well past NOMADS retention; then give up
        if candidate.hour in QMD_CYCLE_HOURS and (t - candidate).total_seconds() >= latency_hours * 3600:
            return Cycle.from_datetime(candidate)
        candidate -= timedelta(hours=1)
    raise ValueError(f"no qmd cycle old enough at {now.isoformat()}")


def subset_url_params(*, kind: str, cycle: Cycle, fhour: int, variable: str, region: SubRegion) -> dict[str, str]:
    """The exact query the CGI expects. ``dir`` is percent-encoded by the HTTP layer."""
    if kind not in ("core", "qmd"):
        raise ValueError(f"unknown NBM file kind {kind!r}")
    filename = cycle.file_for(kind, fhour)
    if not _FILE_RE.match(filename):  # defence in depth: nothing unvalidated reaches the CGI
        raise ValueError(f"refusing to request {filename!r}")
    if not re.fullmatch(r"[A-Z0-9]{3,8}", variable):
        raise ValueError(f"refusing to request variable {variable!r}")
    return {"dir": cycle.dir_for(kind), "file": filename, f"var_{variable}": "on", **region.params()}


async def fetch_qmd_apcp(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    cycle: Cycle,
    fhour: int,
    region: SubRegion = WA_BASINS,
) -> FetchResult:
    """All APCP records (every window, all 21 percentile levels, deterministic and
    exceedance) for one qmd file, clipped to ``region``. Measured 214 KB / 557 KB / 1.05 MB
    for f024 / f048 / f072: the full CDF comes along for free at this size, so v0 archives
    the whole APCP subset rather than hand-picking records."""
    return await fetcher.fetch(
        session,
        url=BASE_URL,
        params=subset_url_params(kind="qmd", cycle=cycle, fhour=fhour, variable="APCP", region=region),
        allowed_hosts=ALLOWED_HOSTS,
        product_id=PRODUCT_NBM_QMD,
        suffix=SUFFIX,
        accept=ACCEPT,
        prefix=OBJECT_PREFIX,
        retention_class=RETENTION_CLASS,
        timeout_s=SUBSET_TIMEOUT_S,
    )


async def fetch_core_snowlvl(
    fetcher: ArchivingFetcher,
    session: AsyncSession,
    *,
    cycle: Cycle,
    fhour: int,
    region: SubRegion = WA_BASINS,
) -> FetchResult:
    """SNOWLVL (deterministic + 15 percentiles) for one core file, clipped to ``region``."""
    return await fetcher.fetch(
        session,
        url=BASE_URL,
        params=subset_url_params(kind="core", cycle=cycle, fhour=fhour, variable="SNOWLVL", region=region),
        allowed_hosts=ALLOWED_HOSTS,
        product_id=PRODUCT_NBM_CORE,
        suffix=SUFFIX,
        accept=ACCEPT,
        prefix=OBJECT_PREFIX,
        retention_class=RETENTION_CLASS,
        timeout_s=SUBSET_TIMEOUT_S,
    )


def archive_url(*, kind: str, cycle: Cycle, fhour: int, index: bool = False) -> str:
    """S3 PDS URL for the whole CONUS file or its ``.idx`` sidecar (backfill path only)."""
    return f"{ARCHIVE_BASE_URL}blend.{cycle.yyyymmdd}/{cycle.hour:02d}/{kind}/{cycle.file_for(kind, fhour)}{'.idx' if index else ''}"
