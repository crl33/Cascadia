"""Export JSON Schema for every contract to packages/contracts/schema/*.json.

Usage: python -m cascade_contracts.export_schema [out_dir]
The web client's TypeScript types are generated from these files; a diff in CI fails the build.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cascade_contracts import (
    BasinVisualizationState,
    ContractEnvelope,
    ProvenanceRef,
    RiverVisualizationState,
    SceneSummary,
)

CONTRACTS = {
    "ProvenanceRef": ProvenanceRef,
    "BasinVisualizationState": BasinVisualizationState,
    "RiverVisualizationState": RiverVisualizationState,
    "ContractEnvelope": ContractEnvelope,
    "SceneSummary": SceneSummary,
}


def export(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in CONTRACTS.items():
        schema = model.model_json_schema(by_alias=True)
        schema["$id"] = f"https://cascade-oracle.dev/schema/{name}.json"
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        written.append(path)
    return written


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "schema"
    for p in export(target):
        print(p)
