"""NWRFC ``xml.cgi`` reservoir series: client, strict parser, and the SHEF-code pick policy.

Why reservoirs at all: five of the six seed basins are regulated, and DATA_DOCTRINE treats
regulation as a first-class caveat — the Skagit's flood response passes through Ross/Diablo/
Upper Baker decisions, the Green through Howard Hanson, the Puyallup-White through Mud
Mountain. Forebay elevation, storage, inflow and outflow are the observable state of those
decisions (HYDROLOGY §10). DATA_SOURCES R4 carries the research; the PE codes per site were
verified there and are pinned in ``SERIES``.

Parser honesty rules:

- **Units are stored verbatim** ("feet", "k-acre-feet", "cubic feet per second") — asserted
  from the payload, never converted, never abbreviated at ingest (display may shorten; the
  row may not).
- **No datum is asserted.** A forebay elevation is stage-like, but the provider states no
  vertical datum for it, so ``datum=None`` travels with quality ``datum_unstated_by_provider``
  rather than an invented NGVD29 (ADR-0009: never guess a datum).
- **Duplicate instants across SHEF type-source codes are real** (measured: LS serves the same
  instant under RG and RR, HP under RZ and RG). One row per instant is stored, chosen by a
  DECLARED preference (``TS_PREFERENCE``, then lexicographic — deterministic, never
  first-seen); the chosen code rides in ``qualifier_raw``, and when the codes DISAGREE about
  the value beyond 0.01 the row is flagged ``multi_source_values_differ`` — disagreement is
  information, not noise to average.
- Naive timestamps are refused; the provider serves Z-suffixed instants and a silent
  assumption would be exactly the day-boundary bug ADR-0017 exists to prevent.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_NWRFC_RESERVOIR

BASE_URL = "https://www.nwrfc.noaa.gov/xml/xml.cgi"
NWRFC_HOSTS = frozenset({"www.nwrfc.noaa.gov"})
OBJECT_PREFIX = "nwrfc/"

#: PE code -> the variable name rows carry. HF and HP are both forebay/pool elevations; the
#: provider's own value element is <forebay_elevation> for both.
VARIABLE_BY_PE = {"HF": "forebay_elevation", "HP": "forebay_elevation",
                  "LS": "storage", "QI": "inflow", "QR": "outflow"}

#: Which PE codes each reservoir station serves (DATA_SOURCES R4, verified 2026-08-28 by the
#: captured fixtures). Keys are the NWS LIDs; station ids are ``station:nwrfc:<LID>``.
SERIES: dict[str, tuple[str, ...]] = {
    "HHDW1": ("HF", "LS", "QI"),
    "MMRW1": ("HF", "LS", "QI", "QR"),
    "RODW1": ("HF", "LS", "QI", "QR"),
    "UBDW1": ("HF", "LS", "QI", "QR"),
    "DIAW1": ("HF", "LS", "QI"),
    "MORW1": ("HP", "QI"),
    "TLRW1": ("HP", "QI", "QR"),
}

#: Deterministic pick when one instant arrives under several SHEF type-source codes.
TS_PREFERENCE = ("RZ", "RG", "RR")

__all__ = [
    "BASE_URL",
    "NWRFC_HOSTS",
    "OBJECT_PREFIX",
    "SERIES",
    "TS_PREFERENCE",
    "VARIABLE_BY_PE",
    "ReservoirParseError",
    "ReservoirValue",
    "fetch_series",
    "parse_series",
]


class ReservoirParseError(Exception):
    def __init__(self, kind: str, detail: str) -> None:
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


@dataclass(frozen=True)
class ReservoirValue:
    valid_time: datetime
    value: float
    unit: str  # verbatim from the payload
    ts_code: str  # the SHEF type-source code the value was chosen from
    disagrees: bool  # other codes at this instant carried a different value


async def fetch_series(
    fetcher: ArchivingFetcher, session: AsyncSession, lid: str, pe: str, *, numdays: int = 1
) -> FetchResult:
    return await fetcher.fetch(
        session,
        url=BASE_URL,
        params={"id": lid, "pe": pe, "dtype": "b", "numdays": str(numdays)},
        allowed_hosts=NWRFC_HOSTS,
        product_id=PRODUCT_NWRFC_RESERVOIR,
        prefix=OBJECT_PREFIX,
        suffix=".xml",
        accept="*/*",
    )


def _strip(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_series(content: bytes, *, lid: str, pe: str) -> tuple[ReservoirValue, ...]:
    """Observed values only (``forecastData`` is deliberately not read here: reservoir release
    FORECASTS are official forecast runs and belong to the ForecastRun shape when they land)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        raise ReservoirParseError("not_xml", str(e)) from e
    site = next((el for el in root.iter() if _strip(el.tag) == "SiteData"), None)
    if site is None:
        raise ReservoirParseError("no_site", f"{lid}/{pe}: payload carries no SiteData")
    got = site.attrib.get("id")
    if got != lid:
        raise ReservoirParseError("wrong_site", f"asked {lid}, payload says {got!r}")

    variable = VARIABLE_BY_PE.get(pe)
    if variable is None:
        raise ReservoirParseError("unknown_pe", pe)

    by_instant: dict[datetime, list[tuple[str, float, str]]] = {}
    for ov in site.iter():
        if _strip(ov.tag) != "observedValue":
            continue
        if ov.attrib.get("petype") != pe:
            raise ReservoirParseError("wrong_pe", f"asked {pe}, payload row says {ov.attrib.get('petype')!r}")
        ts_code = str(ov.attrib.get("tsCode", ""))
        when: datetime | None = None
        value: float | None = None
        unit: str | None = None
        for child in ov:
            tag = _strip(child.tag)
            if tag == "dataDateTime":
                raw = (child.text or "").strip()
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ReservoirParseError("naive_instant", f"{lid}/{pe}: {raw!r} carries no offset")
                when = parsed.astimezone(UTC)
            else:
                unit = str(child.attrib.get("units", ""))
                try:
                    value = float((child.text or "").strip())
                except ValueError as e:
                    raise ReservoirParseError("bad_value", f"{lid}/{pe}: {child.text!r}") from e
        if when is None or value is None or not unit:
            raise ReservoirParseError("incomplete_row", f"{lid}/{pe}: a row lacks instant, value or unit")
        by_instant.setdefault(when, []).append((ts_code, value, unit))

    out: list[ReservoirValue] = []
    for when in sorted(by_instant):
        candidates = by_instant[when]
        rank = {code: i for i, code in enumerate(TS_PREFERENCE)}
        candidates.sort(key=lambda c: (rank.get(c[0], len(TS_PREFERENCE)), c[0]))
        ts_code, value, unit = candidates[0]
        disagrees = any(abs(v - value) > 0.01 for _, v, _ in candidates[1:])
        out.append(ReservoirValue(valid_time=when, value=value, unit=unit, ts_code=ts_code, disagrees=disagrees))
    return tuple(out)
