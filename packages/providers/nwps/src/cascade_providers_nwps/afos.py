"""Strict parser for archived NWS AFOS FLW/FLS river text products (Event Zero T3).

Input is the raw bytes of one AFOS transmission as served by the IEM archive
(``/api/1/nwstext/{product_id}``); a ``?nolimit=1`` response may concatenate several
products separated by SOH (``\\x01``), so :func:`parse_afos` always returns a tuple.

What is parsed (docs/EVENT_ZERO.md §7 "Reconstruct from products"):

- product header: WMO line (``WGUS46 KSEW 091701``), PIL line (``FLWSEW``), MND local
  time line — kept verbatim. The WMO ``ddHHMM`` cross-checks the archive's ``issued_at``
  (which is FACT from the IEM listing / R2 manifest) but never replaces it.
- segments split on UGC lines .. ``$$``: P-VTEC line(s), the single H-VTEC line (LID,
  severity, cause, begin/crest/end times, record flag), and the ``- Forecast...`` bullet.
- forecast crest: every ``to|of [a crest of] <number> feet|cfs`` match INSIDE the
  Forecast bullet only (Flood History and IMPACTS numbers never count); the crest is the
  MAX of those mentions. The crest *time* comes from the H-VTEC crest field — the bullet
  gives only wording ("early Friday morning"). A segment without a Forecast bullet, or
  whose bullet matches nothing, has ``crest = None``: UNKNOWN over fabrication.
- log-only context (never stored as values): "Flood stage is X feet" / "Flood flow is
  X cfs", and the observed "the stage|flow was X feet|cfs" citation.

Times inside VTEC tokens are ``yymmddTHHMMZ``; the all-zero token ``000000T0000Z``
("until further notice" / missing) becomes ``None``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime


class AfosParseError(ValueError):
    pass


_WMO = re.compile(r"^(?P<ttaaii>[A-Z]{4}\d{2}) (?P<office>[A-Z]{4}) (?P<ddhhmm>\d{6})(?: (?P<bbb>[A-Z]{3}))?\s*$", re.M)
_PIL = re.compile(r"^[A-Z][A-Z0-9]{3,8}\s*$")
_MND_TIME = re.compile(r"^\d{3,4} (?:AM|PM) [A-Z]{3,4} [A-Za-z]{3} [A-Za-z]{3} \d{1,2} \d{4}\s*$", re.M)
_UGC = re.compile(r"^[A-Z]{2}[CZ]\d{3}(?:[->][A-Z0-9]{3,6})*-\s*$")
_PVTEC = re.compile(
    r"^/[OTEX]\.(?P<action>[A-Z]{3})\.(?P<office>[A-Z]{4})\.(?P<phen>[A-Z]{2})\.(?P<sig>[A-Z])"
    r"\.(?P<etn>\d{4})\.(?P<begin>\d{6}T\d{4}Z)-(?P<end>\d{6}T\d{4}Z)/\s*$"
)
_HVTEC = re.compile(
    r"^/(?P<lid>[A-Z0-9]{5})\.(?P<severity>[0-3NU])\.(?P<cause>[A-Z]{2})"
    r"\.(?P<begin>\d{6}T\d{4}Z)\.(?P<crest>\d{6}T\d{4}Z)\.(?P<end>\d{6}T\d{4}Z)\.(?P<record>[A-Z]{2})/\s*$"
)
# Only inside the Forecast bullet. "feet" and "cfs" are the only unit spellings KSEW emits.
_CREST = re.compile(r"\b(?:to|of)\s+(?:a crest of\s+)?(?P<num>\d[\d,]*(?:\.\d+)?)\s+(?P<unit>feet|cfs)\b")
_FLOOD_STAGE = re.compile(r"\bFlood (?P<var>stage|flow) is (?P<num>\d[\d,]*(?:\.\d+)?)\s+(?P<unit>feet|cfs)\b")
_OBSERVED = re.compile(r"\bthe (?P<var>stage|flow) was (?P<num>\d[\d,]*(?:\.\d+)?)\s+(?P<unit>feet|cfs)\b")

_UNIT = {"feet": "ft", "cfs": "cfs"}


def _num(tok: str) -> float:
    return float(tok.replace(",", ""))


def _vtec_time(tok: str) -> datetime | None:
    if tok == "000000T0000Z":
        return None
    return datetime.strptime(tok, "%y%m%dT%H%MZ").replace(tzinfo=UTC)


@dataclass(frozen=True)
class PVtec:
    action: str  # NEW | CON | EXT | CAN | EXP | ...
    office: str  # KSEW
    phenomenon: str  # FL
    significance: str  # W | Y | A
    etn: int
    begin: datetime | None
    end: datetime | None
    raw: str


@dataclass(frozen=True)
class HVtec:
    lid: str  # NWSLI, e.g. MVEW1
    severity: str  # 0-3 | N | U
    cause: str  # ER | SM | ...
    begin: datetime | None
    crest: datetime | None  # None == 000000T0000Z (missing crest time)
    end: datetime | None
    record: str  # NO | NR | UU | OO
    raw: str


@dataclass(frozen=True)
class CrestMention:
    value: float
    unit: str  # ft | cfs


@dataclass(frozen=True)
class AfosSegment:
    ugc: str
    pvtec: tuple[PVtec, ...]
    hvtec: HVtec | None
    flood_stage: CrestMention | None  # "Flood stage is 28.0 feet" (log-only)
    observed: CrestMention | None  # "the stage was 25.3 feet" (log-only)
    forecast_text: str | None  # the "- Forecast..." bullet, verbatim
    crest_mentions: tuple[CrestMention, ...]  # matches inside forecast_text only

    @property
    def lid(self) -> str | None:
        return self.hvtec.lid if self.hvtec is not None else None

    @property
    def crest(self) -> CrestMention | None:
        """Forecast crest = MAX numeric mention in the Forecast bullet; None == UNKNOWN."""
        return max(self.crest_mentions, key=lambda m: m.value, default=None)


@dataclass(frozen=True)
class AfosProduct:
    ttaaii: str  # WGUS46
    office: str  # KSEW
    wmo_ddhhmm: str  # "091701" — cross-check only; issued_at authority is the archive
    bbb: str | None  # correction/retransmission flag (CCA, RRA, ...)
    pil: str  # FLWSEW | FLSSEW
    mnd_time_raw: str | None  # "901 AM PST Tue Dec 9 2025", verbatim
    segments: tuple[AfosSegment, ...]

    def wmo_matches(self, issued_at: datetime) -> bool:
        """True when the WMO header day/hour/minute equals the archive issuance time."""
        return self.wmo_ddhhmm == issued_at.strftime("%d%H%M")


def _forecast_bullet(lines: list[str]) -> str | None:
    """The '- Forecast...' bullet with its continuation lines, verbatim; None if absent."""
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("- Forecast"):
            continue
        bullet = [line]
        for cont in lines[i + 1 :]:
            s = cont.strip()
            if not s or s.startswith("- ") or s.startswith("*") or s in ("&&", "$$"):
                break
            bullet.append(cont)
        return "\n".join(bullet)
    return None


def _first_mention(rx: re.Pattern[str], text: str) -> CrestMention | None:
    m = rx.search(text)
    if m is None:
        return None
    return CrestMention(value=_num(m.group("num")), unit=_UNIT[m.group("unit")])


def _parse_segment(lines: list[str], ugc: str) -> AfosSegment:
    text = "\n".join(lines)
    pvtec = tuple(
        PVtec(
            action=m.group("action"),
            office=m.group("office"),
            phenomenon=m.group("phen"),
            significance=m.group("sig"),
            etn=int(m.group("etn")),
            begin=_vtec_time(m.group("begin")),
            end=_vtec_time(m.group("end")),
            raw=m.group(0).strip(),
        )
        for line in lines
        if (m := _PVTEC.match(line)) is not None
    )
    hvtecs = [m for line in lines if (m := _HVTEC.match(line)) is not None]
    if len(hvtecs) > 1:
        raise AfosParseError(f"segment {ugc!r} carries {len(hvtecs)} H-VTEC lines; expected at most one")
    hvtec = None
    if hvtecs:
        m = hvtecs[0]
        hvtec = HVtec(
            lid=m.group("lid"),
            severity=m.group("severity"),
            cause=m.group("cause"),
            begin=_vtec_time(m.group("begin")),
            crest=_vtec_time(m.group("crest")),
            end=_vtec_time(m.group("end")),
            record=m.group("record"),
            raw=m.group(0).strip(),
        )
    forecast_text = _forecast_bullet(lines)
    mentions: tuple[CrestMention, ...] = ()
    if forecast_text is not None:
        mentions = tuple(
            CrestMention(value=_num(m.group("num")), unit=_UNIT[m.group("unit")])
            for m in _CREST.finditer(forecast_text)
        )
    return AfosSegment(
        ugc=ugc,
        pvtec=pvtec,
        hvtec=hvtec,
        flood_stage=_first_mention(_FLOOD_STAGE, text),
        observed=_first_mention(_OBSERVED, text),
        forecast_text=forecast_text,
        crest_mentions=mentions,
    )


def _parse_one(text: str) -> AfosProduct:
    wmo = _WMO.search(text)
    if wmo is None:
        raise AfosParseError("no WMO heading line (TTAAii CCCC ddHHMM) found")
    after = text[wmo.end() :].lstrip("\n").splitlines()
    if not after or not _PIL.match(after[0]):
        raise AfosParseError(f"no AFOS PIL line after WMO heading {wmo.group(0).strip()!r}")
    pil = after[0].strip()
    mnd = _MND_TIME.search(text)
    lines = text.splitlines()
    segments: list[AfosSegment] = []
    i = 0
    while i < len(lines):
        if _UGC.match(lines[i]):
            j = i + 1
            while j < len(lines) and lines[j].strip() != "$$":
                j += 1
            segments.append(_parse_segment(lines[i + 1 : j], ugc=lines[i].strip()))
            i = j
        i += 1
    return AfosProduct(
        ttaaii=wmo.group("ttaaii"),
        office=wmo.group("office"),
        wmo_ddhhmm=wmo.group("ddhhmm"),
        bbb=wmo.group("bbb"),
        pil=pil,
        mnd_time_raw=mnd.group(0).strip() if mnd else None,
        segments=tuple(segments),
    )


def parse_afos(content: bytes) -> tuple[AfosProduct, ...]:
    """Parse one archived AFOS transmission; SOH-separated concatenations yield several."""
    if not content or not content.strip():
        raise AfosParseError("empty product text")
    text = content.decode("utf-8", errors="replace").replace("\r", "")
    chunks = [c for c in text.split("\x01") if c.strip()]
    if not chunks:
        raise AfosParseError("no product text between SOH separators")
    return tuple(_parse_one(chunk.replace("\x03", "")) for chunk in chunks)
