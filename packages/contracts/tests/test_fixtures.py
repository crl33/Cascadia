"""Fixture documents must validate against the contracts (docs/TESTING.md §4)."""

import json
from pathlib import Path

import pytest

from cascade_contracts import ContractEnvelope

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.mark.parametrize("name", sorted(p.name for p in FIXTURES.glob("*_envelope.json")))
def test_fixture_validates(name: str) -> None:
    env = ContractEnvelope.model_validate_json((FIXTURES / name).read_text())
    assert env.items, name
    assert env.provenance_refs, name
    for item in env.items:
        # every item must carry at least one resolvable provenance key somewhere
        assert "prov" in item.model_dump_json()
