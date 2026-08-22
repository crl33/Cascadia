"""Flood category from OFFICIAL thresholds (ADR-0011). The function signature cannot accept a
CONFIGURED threshold: `ThresholdSet` is only ever built from Threshold rows whose source_kind
is OFFICIAL_FORECAST (see assemble.threshold_set). Comparisons are `>=` and refuse any mismatch
of basis (stage vs flow), unit (ft vs m, cfs vs kcfs) or vertical datum (NGVD29 vs NAVD88)."""

from __future__ import annotations

from dataclasses import dataclass

from cascade_contracts import FloodCategory

ORDER: tuple[str, ...] = ("action", "minor", "moderate", "major")


@dataclass(frozen=True)
class ThresholdSet:
    basis: str  # stage | flow
    unit: str
    datum: str | None
    action: float | None = None
    minor: float | None = None
    moderate: float | None = None
    major: float | None = None

    def value_of(self, category: str) -> float | None:
        return getattr(self, category)

    def defined(self) -> list[tuple[str, float]]:
        return [(c, v) for c in ORDER if (v := self.value_of(c)) is not None]


@dataclass(frozen=True)
class Measure:
    basis: str
    value: float
    unit: str
    datum: str | None = None


@dataclass(frozen=True)
class CategoryResult:
    category: FloodCategory
    reason: str


def compatibility_problem(m: Measure, t: ThresholdSet) -> str | None:
    if m.basis != t.basis:
        return f"basis mismatch: value is {m.basis}, official thresholds are {t.basis}"
    if m.unit != t.unit:
        return f"unit mismatch: value in {m.unit}, thresholds in {t.unit} (no implicit conversion)"
    if t.basis == "stage" and (m.datum is None or t.datum is None or m.datum != t.datum):
        return f"datum mismatch: value datum {m.datum}, threshold datum {t.datum}"
    return None


def categorize(m: Measure | None, t: ThresholdSet | None, *, label: str = "Value") -> CategoryResult:
    if t is None:
        return CategoryResult(FloodCategory.UNKNOWN, "no official NWPS thresholds known for this point")
    if m is None:
        return CategoryResult(FloodCategory.UNKNOWN, f"no {t.basis} value available to compare")
    problem = compatibility_problem(m, t)
    if problem:
        return CategoryResult(FloodCategory.UNKNOWN, problem)
    defined = t.defined()
    if not defined:
        return CategoryResult(FloodCategory.UNKNOWN, "official thresholds carry no category values")
    datum = f", {t.datum}" if t.datum else ""
    reached = [(c, v) for c, v in defined if m.value >= v]
    if not reached:
        c0, v0 = defined[0]
        return CategoryResult(FloodCategory.NONE, f"{label} {m.value:g} {m.unit} is below {c0} {t.basis} {v0:g} {t.unit}{datum} (official NWPS).")
    c, v = reached[-1]
    return CategoryResult(FloodCategory(c), f"{label} {m.value:g} {m.unit} is at or above {c} {t.basis} {v:g} {t.unit}{datum} (official NWPS).")
