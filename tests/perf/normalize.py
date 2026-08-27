"""The semantic baseline: canonicalise a response body so two runs can be diffed byte for byte.

The optimisation this exists to police is allowed to change WHEN queries run, never WHAT the
endpoint says. So the comparison has to be total — every key, every value, every ordering — with
exactly one class of exception: fields the endpoint legitimately computes from the clock at read
time. Normalising anything else would be building a hole into the safety net.

**What is genuinely read-time varying, and what only looks it.** With an explicit ``as_of`` on the
request, far less varies than one would assume:

- ``generated_at`` is ``utcnow()`` at request time. Genuinely varying. Always normalised.
- ``as_of`` and ``time.valid`` are the *pinned knowledge time* — the query parameter, echoed back.
  Constant across runs at the same ``as_of``. Normalised only in :data:`LOOSE` mode, which exists
  for comparing captures taken at different knowledge times.
- ``time.mode`` is ``"now"`` within 300 s of ``as_of`` and ``"past"`` outside it
  (``assemble._envelope``). At a historical ``as_of`` it is deterministically ``"past"``.
- **Freshness ages are NOT read-time varying.** Every ``compute_freshness`` call on this path is
  passed ``now=k.as_of``, not the wall clock (`assemble._fresh`, `assess_point`,
  `forecast_run_ref`). Pinned ``as_of`` in, deterministic ``age_seconds`` out. They are therefore
  compared by default: an age that moves after an optimisation means the anchor timestamp
  changed — a freshness badge now computed from a different row — which is precisely the kind of
  silent semantic drift this baseline is for. :data:`LOOSE` blanks them for the case where a
  capture really was taken against a moving clock.

Default is :data:`STRICT`. Reach for :data:`LOOSE` only with a reason, and say the reason.
"""

from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from typing import Any

#: Placeholder written in place of a normalised value. Distinctive so it cannot collide with data.
BLANK = "<read-time>"

#: Keys blanked wherever they appear at the top level of the envelope.
_CLOCK_KEYS = ("generated_at",)
#: Keys blanked only under LOOSE.
_LOOSE_CLOCK_KEYS = ("as_of", "valid")


@dataclass(frozen=True)
class Mode:
    name: str
    #: Blank ``as_of`` / ``time.valid`` too (captures taken at different knowledge times).
    knowledge_time: bool
    #: Blank every ``freshness.age_seconds`` (captures taken against a moving clock).
    freshness_ages: bool


#: Same pinned ``as_of`` on both sides: only ``generated_at`` may move.
STRICT = Mode("strict", knowledge_time=False, freshness_ages=False)
#: Different clocks on the two sides: knowledge time and freshness ages are blanked as well.
LOOSE = Mode("loose", knowledge_time=True, freshness_ages=True)


def normalize(body: Any, mode: Mode = STRICT) -> Any:
    """A deep copy of ``body`` with the read-time-only fields replaced by :data:`BLANK`."""
    return _walk(copy.deepcopy(body), mode)


def _walk(node: Any, mode: Mode) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        is_freshness = "state" in node and ("age_seconds" in node or "expected_cadence_seconds" in node)
        for key, value in node.items():
            if key in _CLOCK_KEYS:
                out[key] = BLANK
            elif mode.knowledge_time and key in _LOOSE_CLOCK_KEYS:
                out[key] = BLANK
            elif mode.freshness_ages and is_freshness and key == "age_seconds":
                out[key] = BLANK
            else:
                out[key] = _walk(value, mode)
        return out
    if isinstance(node, list):
        return [_walk(v, mode) for v in node]
    return node


def read_time_values(body: Any) -> dict[str, Any]:
    """The read-time fields' actual values, so normalising them does not make them invisible.

    Returned beside the canonical form and stored with the baseline: a reviewer can see that
    ``generated_at`` moved (expected) without the diff drowning in it, and can see that
    ``as_of`` did NOT move (required).
    """
    found: dict[str, Any] = {}

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                here = f"{path}.{key}" if path else key
                if key in (*_CLOCK_KEYS, *_LOOSE_CLOCK_KEYS):
                    found[here] = value
                else:
                    visit(value, here)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                visit(value, f"{path}[{i}]")

    visit(body, "")
    return found


#: Significant digits floats are quantised to before the body is serialised for byte comparison.
#: 12 absorbs the last-ULP differences between architectures (the baseline is captured on arm64,
#: CI runs x86_64, and the basin surfaces are sums over ~1,500 grid cells) while staying about
#: five orders of magnitude tighter than any hydrologically meaningful change. `diff()` applies
#: the same reasoning as a relative tolerance; this is the same rule expressed for serialisation.
CANONICAL_FLOAT_SIGNIFICANT_DIGITS = 12


def _quantise(value: Any) -> Any:
    """Round floats to a fixed significant-figure count so the canonical form is portable."""
    if isinstance(value, bool) or not isinstance(value, float):
        if isinstance(value, dict):
            return {k: _quantise(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_quantise(v) for v in value]
        return value
    if value == 0 or not math.isfinite(value):
        return value
    return float(f"%.{CANONICAL_FLOAT_SIGNIFICANT_DIGITS}g" % value)


def canonical_json(body: Any, mode: Mode = STRICT) -> str:
    """The normalised body as one canonical string, with floats quantised so it is portable.

    Byte equality on raw IEEE doubles is not a property this test can ask for: it fails between
    architectures for reasons that have nothing to do with the answer (see
    `CANONICAL_FLOAT_SIGNIFICANT_DIGITS`). Structure, keys, ordering and every non-float value
    are still compared exactly.
    """
    return json.dumps(_quantise(normalize(body, mode)), sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def diff(baseline: Any, candidate: Any, mode: Mode = STRICT) -> list[str]:
    """Per-path differences between two bodies after normalisation; empty means identical.

    Paths are reported rather than a text diff because the envelope is deep and a one-value
    change buried in `provenance_refs` has to be legible without reading 4,000 lines.
    """
    out: list[str] = []
    _compare(normalize(baseline, mode), normalize(candidate, mode), "", out)
    return out


def _compare(a: Any, b: Any, path: str, out: list[str]) -> None:
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        out.append(f"{path or '<root>'}: type {type(a).__name__} -> {type(b).__name__}")
        return
    if isinstance(a, dict):
        for key in a.keys() - b.keys():
            out.append(f"{path}.{key}: present in baseline, absent now")
        for key in b.keys() - a.keys():
            out.append(f"{path}.{key}: absent in baseline, present now")
        for key in a.keys() & b.keys():
            _compare(a[key], b[key], f"{path}.{key}" if path else key, out)
        return
    if isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} -> {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            _compare(x, y, f"{path}[{i}]", out)
        return
    if isinstance(a, float) or isinstance(b, float):
        # Floats compare within a relative tolerance, NOT bit-exactly. The basin surfaces are
        # sums over ~1,500 grid cells and ~100 observations, and summation order and FMA
        # contraction differ between architectures: the baseline is captured on arm64 and CI runs
        # x86_64, which produced last-ULP differences (3186.777804321641 vs ...43) and failed a
        # test whose question is "did the optimisation change the answer".
        #
        # 1e-9 relative is about six orders of magnitude tighter than the smallest difference that
        # could matter hydrologically (a 1e-9 relative change in a 3,000 cfs driver is 3 micro-cfs),
        # so a real change in the read path still fails here. Absolute floor covers values at or
        # near zero, where relative tolerance is meaningless.
        if a == b or math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-12):
            return
        out.append(f"{path or '<root>'}: {a!r} -> {b!r}")
        return
    if a != b:
        out.append(f"{path or '<root>'}: {a!r} -> {b!r}")
