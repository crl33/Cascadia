"""MRMS on the NODD S3 mirror: observed precipitation, and the covariate that qualifies it.

Two products, fetched together on purpose (DATA_SOURCES P1):

- ``MultiSensor_QPE_01H_Pass2`` — the best hourly QPE, radar blended with gauges, PRISM
  climatology and HRRR fill, ~57 min after the accumulation closes.
- ``GaugeInflIndex_01H_Pass2`` — how much of each cell's QPE came from gauges rather than radar.
  **In western Washington this is not optional context**: KATX is beam-blocked by the Olympics
  and the Cascade headwaters are overshot, so the "radar" QPE over the seed basins is largely
  gauge/model fill. A basin QPE published without its gauge-influence would present radar-weak
  numbers unqualified.

**Discovery is a LIST, not a guess.** File keys carry the accumulation end time, but the honest
publication instant is the S3 object's ``LastModified`` — measured ~57 min after the timestamp —
and that is what ``available_at`` must carry (ADR-0010: a replay must not know an accumulation
before NODD served it). So the job lists the day prefix (a ~2 KB XML answer, archived like any
other response) and reads keys AND LastModified from it, rather than constructing keys and
inventing a publication time.

**Retention economics.** Raw gz is ~0.85 MB (QPE) + ~4 MB (gauge influence) per hour — ~116
MB/day. The `mrms/` object prefix exists so a bucket lifecycle rule can bound it (the `nbm/`
precedent); the DERIVED per-basin rows are permanent and tiny. QPE is re-obtainable from the IEM
MTArchive back to 2014; GaugeInflIndex is NOT in that archive, which is another reason the
derived rows — not the raw grids — are the permanent record.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_MRMS_GAUGEINFL, PRODUCT_MRMS_QPE

__all__ = [
    "BUCKET_URL",
    "GAUGEINFL_PRODUCT_DIR",
    "MRMS_HOSTS",
    "OBJECT_PREFIX",
    "QPE_PRODUCT_DIR",
    "S3Object",
    "fetch_object",
    "list_day",
    "parse_listing",
]

BUCKET_URL = "https://noaa-mrms-pds.s3.amazonaws.com/"
MRMS_HOSTS = frozenset({"noaa-mrms-pds.s3.amazonaws.com"})

QPE_PRODUCT_DIR = "MultiSensor_QPE_01H_Pass2_00.00"
GAUGEINFL_PRODUCT_DIR = "GaugeInflIndex_01H_Pass2_00.00"

#: Object-store prefix, so a lifecycle rule can bound the raw grids without touching anything
#: else. Unlike `hefs/` (never expire), `mrms/` is bounded on purpose: ~116 MB/day of raw gz
#: against a 10 GB tier, with the permanent record being the derived per-basin rows.
OBJECT_PREFIX = "mrms/"

_KEY_RE = re.compile(
    r"MRMS_(?P<product>[A-Za-z0-9_]+?)_(?P<level>\d\d\.\d\d)_(?P<stamp>\d{8}-\d{6})\.grib2\.gz$"
)


@dataclass(frozen=True)
class S3Object:
    key: str
    #: The END of the 1-h accumulation, from the key. Naive-UTC in the key, aware here.
    valid_time: datetime
    #: When NODD actually served it — the publication instant, from LastModified.
    last_modified: datetime
    size: int


def parse_listing(xml: bytes) -> tuple[S3Object, ...]:
    """The S3 ListObjectsV2 answer, without an XML library dependency.

    The response is machine-generated with a fixed element order (Key, LastModified, ..., Size
    inside each Contents). A regex over that shape is deliberate: it refuses (returns nothing
    for) entries that do not match, and the job treats "the listing parsed to nothing on a day
    that should have files" as a failure rather than an empty success.
    """
    text = xml.decode("utf-8", errors="strict")
    out: list[S3Object] = []
    for m in re.finditer(
        # Tempered dot: consume anything between LastModified and Size (ETag, checksum tags —
        # the set has already grown once) WITHOUT crossing into the next Contents block.
        r"<Contents><Key>([^<]+)</Key><LastModified>([^<]+)</LastModified>"
        r"(?:(?!</Contents>).)*?<Size>(\d+)</Size>",
        text,
    ):
        key, last_modified, size = m.group(1), m.group(2), int(m.group(3))
        km = _KEY_RE.search(key)
        if not km:
            continue
        stamp = datetime.strptime(km.group("stamp"), "%Y%m%d-%H%M%S").replace(tzinfo=UTC)
        out.append(
            S3Object(
                key=key,
                valid_time=stamp,
                last_modified=datetime.fromisoformat(last_modified.replace("Z", "+00:00")),
                size=size,
            )
        )
    return tuple(out)


async def list_day(
    fetcher: ArchivingFetcher, session: AsyncSession, *, product_dir: str, day: datetime
) -> FetchResult:
    """One day's objects for one product. ~2 KB of XML, archived like any response."""
    return await fetcher.fetch(
        session,
        url=BUCKET_URL,
        params={
            "list-type": "2",
            "prefix": f"CONUS/{product_dir}/{day:%Y%m%d}/",
            "max-keys": "100",
        },
        allowed_hosts=MRMS_HOSTS,
        product_id=PRODUCT_MRMS_QPE if product_dir == QPE_PRODUCT_DIR else PRODUCT_MRMS_GAUGEINFL,
        prefix=OBJECT_PREFIX,
        suffix=".xml",
        accept="application/xml",
    )


async def fetch_object(
    fetcher: ArchivingFetcher, session: AsyncSession, *, key: str, product_id: str
) -> FetchResult:
    """One grib2.gz by its listed key. ~0.85-4 MB; 60 s covers the larger covariate.

    The fetcher's default 8 MB cap stands: the largest object observed (gauge influence) is
    ~4.1 MB, and a response past 8 MB means the product changed shape — refusing it is right.
    """
    return await fetcher.fetch(
        session,
        url=f"{BUCKET_URL}{key}",
        params=None,
        allowed_hosts=MRMS_HOSTS,
        product_id=product_id,
        suffix=".grib2.gz",
        accept="*/*",
        prefix=OBJECT_PREFIX,
        timeout_s=60.0,
    )
