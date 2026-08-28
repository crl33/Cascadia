"""NWPS HEFS API v1 client — the ensemble forecast that disappears after ~10 days.

This provider exists because of a retention window, not because of a feature. HEFS serves only
about ten daily cycles and then drops them (FACT, verified 2026-08-27: `headers/?location_id=MVEW1`
returned exactly 10 cycles, 2026-08-18 .. 2026-08-27, one per day at 12Z). Nothing archives it
upstream in a form Cascadia can read, so a cycle not fetched within ten days is gone permanently.
ROADMAP Phase 5 depends on having that history and says "archive from day one"; production has
been ingesting since 2026-08-24 without this adapter, so the loss is already real and bounded only
by starting now.

Three endpoints, one shape rule each (all FACT, measured 2026-08-27):

- ``headers/``             — a bare JSON LIST, not a paginated envelope. One row per retained
                             cycle. Cheap (4.5 KB), and it is how the job discovers what exists
                             without downloading anything large.
- ``ensembles/``           — a list containing ONE list of 45 members. ~397 KB per location-cycle.
                             The irreplaceable payload.
- ``hydrograph-quantiles/``— ``{metadata, value_set}``. The OFFICIAL exceedance quantiles.

**The 100-object cap is why every call is per location and per cycle.** A query returning more
than 100 objects fails with HTTP 400 "This query returned over 100 objects" (FACT, DATA_SOURCES
H4), and 45 members already puts a two-cycle ensemble query over it. Iterating is not politeness
here, it is the only shape that works.

The host is already in `fetch.PROVIDER_HOSTS` for the NWPS gauge/reach paths, so this adapter adds
no new host to the ceiling. It carries its own object-store prefix (`hefs/`) so the archive can be
reasoned about — and, unlike `nbm/`, it must NEVER get an expiry lifecycle rule: the whole point is
that these bytes cannot be re-fetched.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_HEFS_ENSEMBLE, PRODUCT_HEFS_QUANTILES

__all__ = [
    "BASE_URL",
    "DISCHARGE_PARAMETER",
    "ENSEMBLE_TIMEOUT_S",
    "HEFS_HOSTS",
    "OBJECT_PREFIX",
    "fetch_ensemble",
    "fetch_headers",
    "fetch_quantiles",
]

BASE_URL = "https://api.water.noaa.gov/hefs/v1/"
HEFS_HOSTS = frozenset({"api.water.noaa.gov"})

#: Streamflow, instantaneous, in CFS. The only parameter served at the seed points (FACT: all six
#: return `params ['QINE']`). Named rather than defaulted so a future SWE ('IN') cannot be pulled
#: into a flow series by omission.
DISCHARGE_PARAMETER = "QINE"

#: The archived-object key prefix. Deliberately has NO bucket lifecycle rule — see the module
#: docstring. `nbm/` expires at 90 days because NOMADS can be re-subset; HEFS cannot.
OBJECT_PREFIX = "hefs/"

#: ~397 KB of 45 members from an experimental, explicitly unsupported API. The default 30 s is the
#: same budget that produced 15 ReadTimeouts on the smaller NWM reach payloads.
ENSEMBLE_TIMEOUT_S = 120.0

_LID_RE = re.compile(r"^[A-Z0-9]{4,6}$")


def _lid(location_id: str) -> str:
    if not _LID_RE.match(location_id):
        raise ValueError(f"not an NWS location id: {location_id!r}")
    return location_id


async def fetch_headers(fetcher: ArchivingFetcher, session: AsyncSession, *, location_id: str) -> FetchResult:
    """Which cycles this location still serves. Cheap, and the job's discovery step.

    Archived like everything else: the header list IS the evidence of what the provider was
    offering at that moment, which is the only way to tell later that a cycle was never served
    apart from a cycle Cascadia failed to collect.
    """
    return await fetcher.fetch(
        session,
        url=f"{BASE_URL}headers/",
        params={"location_id": _lid(location_id), "parameter_id": DISCHARGE_PARAMETER},
        allowed_hosts=HEFS_HOSTS,
        product_id=PRODUCT_HEFS_ENSEMBLE,
        prefix=OBJECT_PREFIX,
    )


async def fetch_ensemble(
    fetcher: ArchivingFetcher, session: AsyncSession, *, location_id: str, forecast_datetime: datetime
) -> FetchResult:
    """All 45 members of one cycle at one location. One call per (location, cycle) — see the cap."""
    return await fetcher.fetch(
        session,
        url=f"{BASE_URL}ensembles/",
        params={
            "location_id": _lid(location_id),
            "parameter_id": DISCHARGE_PARAMETER,
            "forecast_datetime": _instant(forecast_datetime),
        },
        allowed_hosts=HEFS_HOSTS,
        product_id=PRODUCT_HEFS_ENSEMBLE,
        prefix=OBJECT_PREFIX,
        timeout_s=ENSEMBLE_TIMEOUT_S,
    )


async def fetch_quantiles(
    fetcher: ArchivingFetcher, session: AsyncSession, *, location_id: str, forecast_datetime: datetime | None = None
) -> FetchResult:
    """The provider's OWN exceedance quantiles for a cycle.

    Fetched rather than computed from the members on purpose. DATA_DOCTRINE §9(a) lets NWS's
    published quantiles be shown as official guidance precisely because Cascadia did not derive
    them; a quantile Cascadia computed from the same members would be a Cascade-derived number
    wearing an official badge, and the two must never be confused.
    """
    params = {"location_id": _lid(location_id), "parameter_id": DISCHARGE_PARAMETER}
    if forecast_datetime is not None:
        params["forecast_datetime"] = _instant(forecast_datetime)
    return await fetcher.fetch(
        session,
        url=f"{BASE_URL}hydrograph-quantiles/",
        params=params,
        allowed_hosts=HEFS_HOSTS,
        product_id=PRODUCT_HEFS_QUANTILES,
        prefix=OBJECT_PREFIX,
    )


def _instant(when: datetime) -> str:
    """The API's own spelling: `2026-08-27T12:00:00Z`, never `+00:00`."""
    if when.tzinfo is None:
        raise ValueError("forecast_datetime must be timezone-aware")
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
