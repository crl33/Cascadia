"""The comparator is the safety net for the whole optimisation, so it gets tested too.

An unverified comparator is worse than none: it would report "body identical" for a change that
was not identical, and the optimisation would ship with a silent regression carrying a green tick.
These cases run against the real captured baseline, not a toy dict, so they also fail if the
envelope's shape moves out from under the normalisation rules.

The pairing that matters: `generated_at` may move (it is `utcnow()` at request time), and NOTHING
ELSE may — least of all a freshness age, which at a pinned `as_of` is computed from `k.as_of` and
is therefore deterministic. tests/perf/normalize.py argues that at length; this is the assertion.
"""

from __future__ import annotations

import copy
import json

import pytest

from tests.perf import normalize
from tests.perf.harness import BASELINE_DIR


@pytest.fixture(scope="module")
def body() -> dict:
    return json.loads((BASELINE_DIR / "viz_basins.json").read_text())


def _first_freshness_key(body: dict) -> str:
    return next(k for k in sorted(body["provenance_refs"]) if body["provenance_refs"][k]["freshness"].get("age_seconds") is not None)


def test_an_unchanged_body_is_clean(body: dict) -> None:
    assert normalize.diff(body, copy.deepcopy(body)) == []
    assert normalize.canonical_json(body) == normalize.canonical_json(copy.deepcopy(body))


def test_generated_at_may_move(body: dict) -> None:
    """The one field the endpoint recomputes from the wall clock on every request."""
    moved = copy.deepcopy(body)
    moved["generated_at"] = "2027-01-01T00:00:00Z"
    assert normalize.diff(body, moved) == []
    assert normalize.canonical_json(body) == normalize.canonical_json(moved)


@pytest.mark.parametrize(
    ("what", "mutate"),
    [
        ("knowledge time", lambda b: b.__setitem__("as_of", "2027-01-01T00:00:00Z")),
        ("time context", lambda b: b["time"].__setitem__("valid", "2027-01-01T00:00:00Z")),
        ("time mode", lambda b: b["time"].__setitem__("mode", "now")),
        ("a surface score", lambda b: b["items"][0]["surfaces"]["forcing"].__setitem__("score", 0.999)),
        ("a surface reason", lambda b: b["items"][0]["surfaces"]["agreement"].__setitem__("reason", "because")),
        ("item order", lambda b: b.__setitem__("items", list(reversed(b["items"])))),
        ("a driver rank", lambda b: b["items"][0]["headline_drivers"][0].__setitem__("rank", 99)),
    ],
)
def test_everything_else_is_caught(body: dict, what: str, mutate) -> None:  # noqa: ANN001
    changed = copy.deepcopy(body)
    mutate(changed)
    assert normalize.diff(body, changed), f"{what} changed and the comparator did not notice"


def test_a_freshness_age_is_caught(body: dict) -> None:
    """Ages are NOT normalised by default, and this is why: an age that moves means the anchor
    timestamp moved — a badge now computed from a different row. That is semantic drift, however
    much it looks like clock noise."""
    key = _first_freshness_key(body)
    changed = copy.deepcopy(body)
    changed["provenance_refs"][key]["freshness"]["age_seconds"] += 1
    assert normalize.diff(body, changed) == [f"provenance_refs.{key}.freshness.age_seconds: {body['provenance_refs'][key]['freshness']['age_seconds']} -> {body['provenance_refs'][key]['freshness']['age_seconds'] + 1}"]
    # ...and LOOSE, which exists for captures taken at different clocks, deliberately does not.
    assert normalize.diff(body, changed, normalize.LOOSE) == []


def test_a_dropped_or_added_provenance_ref_is_caught(body: dict) -> None:
    """The failure mode a query budget invites: fewer queries because less was fetched."""
    key = _first_freshness_key(body)
    dropped = copy.deepcopy(body)
    dropped["provenance_refs"].pop(key)
    assert normalize.diff(body, dropped) == [f"provenance_refs.{key}: present in baseline, absent now"]

    added = copy.deepcopy(body)
    added["provenance_refs"]["invented"] = added["provenance_refs"][key]
    assert normalize.diff(body, added) == ["provenance_refs.invented: absent in baseline, present now"]


def test_read_time_values_are_reported_not_hidden(body: dict) -> None:
    """Normalising a field must not make it unobservable — the values are recorded beside it."""
    values = normalize.read_time_values(body)
    assert set(values) == {"generated_at", "as_of", "time.valid"}
    assert values["as_of"] == body["as_of"]


def test_float_comparison_tolerates_ulps_but_not_real_changes() -> None:
    """The semantic baseline must survive a change of architecture, not of answer.

    CI runs x86_64 and the baseline is captured on arm64; summation order and FMA contraction
    over ~1,500 grid cells differ, so bit-exact float equality failed on differences in the last
    one or two ULPs (3186.777804321641 vs 3186.777804321643) while the answer was identical.
    A tolerance loose enough to absorb that must still be far tighter than anything hydrologically
    meaningful, or the test stops protecting the read path.
    """
    from tests.perf.normalize import diff

    base = {"items": [{"v": 3186.777804321641, "p": 0.021569362835888197}]}

    # last-ULP drift: not a change
    assert diff(base, {"items": [{"v": 3186.777804321643, "p": 0.02156936283588834}]}) == []

    # a change of one part in ten million IS a change and must be reported
    assert diff(base, {"items": [{"v": 3186.7781224, "p": 0.021569362835888197}]}) != []

    # and so is anything a person could see
    assert diff(base, {"items": [{"v": 3187.0, "p": 0.021569362835888197}]}) != []

    # zero-adjacent values use the absolute floor rather than a meaningless relative one
    assert diff({"v": 0.0}, {"v": 1e-13}) == []
    assert diff({"v": 0.0}, {"v": 1e-6}) != []


def test_canonical_json_is_portable_across_architectures_but_still_strict() -> None:
    """The canonical form must not encode this machine's floating-point last digits.

    The first fix made `diff()` tolerant and left this second assertion bit-exact, so CI stayed
    red for the same reason with a different traceback. Both comparisons have to answer the same
    question or the pair is incoherent.
    """
    from tests.perf.normalize import canonical_json

    base = {"v": 3186.777804321641, "p": 0.021569362835888197}
    ulp = {"v": 3186.777804321643, "p": 0.02156936283588834}
    real = {"v": 3186.7781224, "p": 0.021569362835888197}

    assert canonical_json(base) == canonical_json(ulp)
    assert canonical_json(base) != canonical_json(real)
    # structure and non-float values stay exact
    assert canonical_json({"a": 1, "b": "x"}) != canonical_json({"a": 1, "b": "y"})
    assert canonical_json({"a": [1, 2]}) != canonical_json({"a": [2, 1]})
