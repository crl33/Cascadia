"""Units (ADR-0009): provider-native units are stored; conversion goes through pint and is explicit.

Only the handful of unit spellings the spike meets are normalized here; anything unknown is
kept verbatim (never guessed) so a comparison against it is refused downstream.
"""

from __future__ import annotations

import pint

ureg: pint.UnitRegistry = pint.UnitRegistry()
ureg.define("cfs = foot ** 3 / second")
ureg.define("kcfs = 1000 * cfs")

_ALIASES = {"ft3/s": "cfs", "ft^3/s": "cfs", "cfs": "cfs", "kcfs": "kcfs", "ft": "ft", "feet": "ft"}


def normalize_unit(raw: str) -> str:
    """Provider unit spelling → registry spelling ('ft3/s' → 'cfs'). Unknown spellings pass through."""
    return _ALIASES.get(raw.strip(), raw.strip())


def convert(value: float, from_unit: str, to_unit: str) -> float:
    f, t = normalize_unit(from_unit), normalize_unit(to_unit)
    if f == t:
        return float(value)
    return float((value * ureg(f)).to(t).magnitude)
