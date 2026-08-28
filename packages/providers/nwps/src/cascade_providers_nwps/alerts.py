"""NWS CAP alerts (api.weather.gov): client, strict parser, and the UGC->basin routing.

The alerts endpoint has been researched since Phase 1 (DATA_SOURCES W1) and the envelope has
carried an empty ``official_alerts`` tuple since the spike. This closes the gap.

Routing is by UGC code, never by per-alert geometry: the offline derivation
(`scripts/build_basin_ugc.py`, `method:basin-ugc-mapping@1.0.0`) intersected every WA county and
forecast zone with the basin polygons once, so the worker maps an alert to basins by lookup. The
row records WHICH mapping routed it — a re-derived mapping never silently re-explains old rows.

An alert that routes to NO seed basin is stored anyway. It is knowledge (a replay of "what was
known at T" includes it), it is cheap, and dropping it would make the ingest look selective in a
way nobody could audit later.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from cascade_core.fetch import ArchivingFetcher, FetchResult
from cascade_core.registry import PRODUCT_NWS_ALERTS
from cascade_providers_nwps.reaches_parser import ParseError

ALERTS_URL = "https://api.weather.gov/alerts/active"
NWS_API_HOSTS = frozenset({"api.weather.gov"})
UGC_MAPPING_METHOD = "method:basin-ugc-mapping@1.0.0"

__all__ = [
    "ALERTS_URL",
    "NWS_API_HOSTS",
    "UGC_MAPPING_METHOD",
    "CapAlert",
    "UgcMapping",
    "fetch_active_alerts",
    "load_ugc_mapping",
    "parse_active_alerts",
]


@dataclass(frozen=True)
class CapAlert:
    id: str
    event: str
    status: str
    message_type: str
    severity: str | None
    certainty: str | None
    urgency: str | None
    headline: str | None
    sender_name: str | None
    sent: datetime
    onset: datetime | None
    expires: datetime | None
    ends: datetime | None
    ugc: tuple[str, ...]
    references: tuple[str, ...]


@dataclass(frozen=True)
class UgcMapping:
    method_id: str
    #: zone code -> basin ids it overlaps (fractions live in the file; routing needs only ids)
    zones: dict[str, tuple[str, ...]]

    def basins_for(self, ugc_codes: tuple[str, ...]) -> tuple[str, ...]:
        out: set[str] = set()
        for code in ugc_codes:
            out.update(self.zones.get(code, ()))
        return tuple(sorted(out))


def load_ugc_mapping(path: Path) -> UgcMapping:
    """The derived zone->basin mapping. Absent or malformed refuses loudly: routing alerts with
    no mapping would silently file every alert as basin-less, which reads as 'no alerts'."""
    try:
        doc = json.loads(path.read_text())
    except FileNotFoundError as e:
        raise ParseError(f"no UGC mapping at {path}") from e
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParseError(f"{path} is not JSON: {e}") from e
    prov = doc.get("_provenance") or {}
    method = prov.get("method_id")
    zones_in = doc.get("zones")
    if not method or not isinstance(zones_in, dict) or not zones_in:
        raise ParseError(f"{path} carries no method_id or no zones")
    return UgcMapping(
        method_id=str(method),
        zones={code: tuple(sorted(row.get("basins", {}))) for code, row in zones_in.items()},
    )


async def fetch_active_alerts(fetcher: ArchivingFetcher, session: AsyncSession) -> FetchResult:
    """All active WA alerts in one request. ~5-50 KB; the poll cadence honours the provider's
    own abusive-user guidance (at most once or twice a minute; we ask every five)."""
    return await fetcher.fetch(
        session,
        url=ALERTS_URL,
        params={"area": "WA"},
        allowed_hosts=NWS_API_HOSTS,
        product_id=PRODUCT_NWS_ALERTS,
        accept="application/geo+json",
    )


def _req(obj: dict, key: str, ctx: str):
    if key not in obj or obj[key] is None:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def _instant(raw, ctx: str) -> datetime:
    """CAP timestamps carry offsets ('2026-08-27T11:52:00-07:00'); normalised to aware UTC."""
    try:
        when = datetime.fromisoformat(str(raw))
    except ValueError as e:
        raise ParseError(f"{ctx}: {raw!r} is not an ISO instant") from e
    if when.tzinfo is None:
        raise ParseError(f"{ctx}: {raw!r} carries no offset; refusing to assume a zone")
    return when.astimezone(UTC)


def parse_active_alerts(content: bytes) -> tuple[CapAlert, ...]:
    try:
        doc = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON alerts: {e}") from e
    features = doc.get("features")
    if features is None:
        raise ParseError("alerts payload has no 'features'")
    out: list[CapAlert] = []
    for i, feature in enumerate(features):
        props = _req(feature, "properties", f"alert {i}")
        ctx = f"alert {props.get('id', i)}"
        geocode = props.get("geocode") or {}
        references = tuple(
            str(r.get("identifier") or r.get("@id") or "")
            for r in (props.get("references") or [])
        )
        out.append(
            CapAlert(
                id=str(_req(props, "id", ctx)),
                event=str(_req(props, "event", ctx)),
                status=str(_req(props, "status", ctx)),
                message_type=str(_req(props, "messageType", ctx)),
                severity=props.get("severity"),
                certainty=props.get("certainty"),
                urgency=props.get("urgency"),
                headline=props.get("headline"),
                sender_name=props.get("senderName"),
                sent=_instant(_req(props, "sent", ctx), f"{ctx} sent"),
                onset=_instant(props["onset"], f"{ctx} onset") if props.get("onset") else None,
                expires=_instant(props["expires"], f"{ctx} expires") if props.get("expires") else None,
                ends=_instant(props["ends"], f"{ctx} ends") if props.get("ends") else None,
                ugc=tuple(str(u) for u in (geocode.get("UGC") or [])),
                references=tuple(r for r in references if r),
            )
        )
    return tuple(out)
