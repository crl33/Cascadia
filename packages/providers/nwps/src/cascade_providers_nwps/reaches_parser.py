"""Strict parser for NWPS `/reaches/{reachId}/streamflow?series=medium_range` (NWM v3.1).

This is a **different source** from the `/gauges/*` endpoints parsed in `parser.py`, served by
the same API host: the reach endpoints return National Water Model output, which is MODELED,
while `/gauges/{lid}/stageflow` returns the NWRFC's official forecast. Nothing here may be
described with the vocabulary of the other (docs/DATA_DOCTRINE.md §2; design §3.1).

Payload shape verified live 2026-08-24 (six WA reaches, 157–161 KB each):

    {"reach": {"reachId","name","latitude","longitude","streamflow":[...],
               "route":{"upstream":[{"reachId","streamOrder"}],"downstream":[...]}},
     "mediumRange": {"mean":   {"referenceTime","units","data":[{"validTime","flow"}, ...240]},
                     "member1": {... 240 points}, "member2".."member6": {... 204 points}},
     "analysisAssimilation": {}, "shortRange": {}, "longRange": {}, "mediumRangeBlend": {}}

Three rules this parser exists to enforce:

- **The member list is read, never assumed.** NWM member counts are a version-dependent fact
  (design §7 item 4); `members` is whatever the payload contained, and any member fraction
  downstream must use that count as its denominator.
- **`mean` is not a member.** NWPS computes it; it is kept separately, labeled as a read-time
  average produced by the provider, and never counted as a seventh member
  (docs/DATA_DOCTRINE.md §9).
- **Units are checked, not converted.** NWM streamflow is published as `ft³/s`, which is the
  same quantity as the registry's `cfs`, so the spelling is normalized and the numbers are
  passed through untouched. Any other spelling is a ParseError — the parser refuses rather
  than converting (ADR-0009).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from cascade_core.timeutils import parse_iso

#: -9999 in the NWPS JSON family means "no value" (verified on /gauges/{lid}/stageflow, where
#: every CRNW1 secondary value is this sentinel). Applied here too: a sentinel becomes None and
#: never a number.
SENTINEL = -9999.0

#: Provider spellings of cubic feet per second that mean exactly the registry's `cfs`. Recording
#: them here (rather than in cascade_core.units) keeps the acceptance narrow: an unrecognised
#: spelling stops the parse instead of being silently coerced.
FLOW_UNIT_SPELLINGS = frozenset({"ft³/s", "ft3/s", "ft^3/s", "cfs"})
FLOW_UNIT = "cfs"

MEAN_SERIES = "mean"
SERIES_KEY = "mediumRange"
SERIES_NAME = "medium_range"


class ParseError(ValueError):
    pass


def _req(obj: object, key: str, ctx: str) -> object:
    if not isinstance(obj, dict) or key not in obj:
        raise ParseError(f"missing required field {key!r} in {ctx}")
    return obj[key]


def _num(x: object, ctx: str) -> float | None:
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ParseError(f"{ctx}: expected number, got {type(x).__name__}")
    v = float(x)
    if v == SENTINEL or v != v:  # sentinel or NaN
        return None
    return v


@dataclass(frozen=True)
class ReachRecord:
    reach_id: str
    name: str
    lat: float | None
    lon: float | None
    available_series: tuple[str, ...]
    upstream_reach_ids: tuple[str, ...]
    downstream_reach_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReachPoint:
    valid_time: datetime
    flow: float | None  # cfs, as published (ft³/s ≡ cfs); None for a sentinel


@dataclass(frozen=True)
class ReachSeries:
    name: str  # mean | member1 | member2 | ...
    reference_time: datetime  # the model cycle
    unit: str  # always "cfs" — anything else raised in the parser
    points: tuple[ReachPoint, ...]


@dataclass(frozen=True)
class MediumRangeEnsemble:
    """One NWM medium-range cycle at one reach: the provider's mean plus the members it shipped."""

    reach: ReachRecord
    mean: ReachSeries | None
    members: tuple[ReachSeries, ...]

    @property
    def member_count(self) -> int:
        """The observed member count — the only honest denominator for a member fraction."""
        return len(self.members)

    @property
    def reference_time(self) -> datetime | None:
        return self.mean.reference_time if self.mean is not None else (self.members[0].reference_time if self.members else None)

    def series(self, name: str) -> ReachSeries | None:
        if name == MEAN_SERIES:
            return self.mean
        return next((s for s in self.members if s.name == name), None)


def _member_order(name: str) -> tuple[str, int, str]:
    """Sort member1 < member2 < … < member10 (numeric, not lexicographic).

    The member count is a version-dependent fact, so a two-digit member is possible; ordering is
    presentation only (the median is chosen by crest value, never by name) but it should not go
    wrong the day NWM ships more members."""
    head = name.rstrip("0123456789")
    tail = name[len(head) :]
    return (head, int(tail) if tail else -1, name)


def _reach(block: object) -> ReachRecord:
    reach_id = str(_req(block, "reachId", "reach"))
    assert isinstance(block, dict)
    route = block.get("route") or {}
    up = route.get("upstream") or []
    down = route.get("downstream") or []
    return ReachRecord(
        reach_id=reach_id,
        name=str(block.get("name") or ""),
        lat=_num(block.get("latitude"), "reach.latitude"),
        lon=_num(block.get("longitude"), "reach.longitude"),
        available_series=tuple(str(s) for s in (block.get("streamflow") or [])),
        upstream_reach_ids=tuple(str(r.get("reachId")) for r in up if isinstance(r, dict) and r.get("reachId")),
        downstream_reach_ids=tuple(str(r.get("reachId")) for r in down if isinstance(r, dict) and r.get("reachId")),
    )


def _series(name: str, block: object) -> ReachSeries | None:
    if not isinstance(block, dict) or not block.get("data"):
        return None
    unit_raw = str(_req(block, "units", f"mediumRange.{name}")).strip()
    if unit_raw not in FLOW_UNIT_SPELLINGS:
        raise ParseError(
            f"mediumRange.{name}: unit {unit_raw!r} is not a recognised cubic-feet-per-second "
            f"spelling {sorted(FLOW_UNIT_SPELLINGS)}; refusing rather than converting (ADR-0009)"
        )
    reference = parse_iso(str(_req(block, "referenceTime", f"mediumRange.{name}")))
    data = _req(block, "data", f"mediumRange.{name}")
    if not isinstance(data, list):
        raise ParseError(f"mediumRange.{name}.data is not a list")
    points = [
        ReachPoint(
            valid_time=parse_iso(str(_req(p, "validTime", f"mediumRange.{name}.data[{i}]"))),
            flow=_num((p or {}).get("flow") if isinstance(p, dict) else None, f"mediumRange.{name}.data[{i}].flow"),
        )
        for i, p in enumerate(data)
    ]
    points.sort(key=lambda p: p.valid_time)
    return ReachSeries(name=name, reference_time=reference, unit=FLOW_UNIT, points=tuple(points))


def parse_medium_range(content: bytes) -> MediumRangeEnsemble:
    """Parse one `/reaches/{id}/streamflow?series=medium_range` document.

    An empty `mediumRange` block is not an error — NWPS returns `{}` for series a reach does not
    carry — it yields an ensemble with no mean and no members, which every caller must treat as
    "no NWM cycle known" rather than as agreement."""
    try:
        doc = json.loads(content)
    except (ValueError, UnicodeDecodeError) as e:
        raise ParseError(f"not JSON: {e}") from e
    if not isinstance(doc, dict):
        raise ParseError("reach streamflow document is not an object")
    reach = _reach(_req(doc, "reach", "document"))
    block = doc.get(SERIES_KEY)
    if not isinstance(block, dict):
        raise ParseError(f"{SERIES_KEY} is not an object")
    mean = _series(MEAN_SERIES, block.get(MEAN_SERIES))
    names = sorted((k for k in block if k != MEAN_SERIES), key=_member_order)
    members = tuple(s for s in (_series(name, block[name]) for name in names) if s is not None)
    return MediumRangeEnsemble(reach=reach, mean=mean, members=members)
