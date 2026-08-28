"""Static basin geography from the committed LOD GeoJSON fixtures (cartographic truth class)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cascade_core.seed import load_basin_features


@dataclass(frozen=True)
class Geography:
    by_lod: dict[str, dict]
    #: The derived river network (scripts/build_river_network.py), CARTOGRAPHIC register —
    #: where the rivers ARE; every state stays on truth-classed elements. None when the
    #: fixture is absent: the map then simply draws no rivers, loudly logged at startup.
    river_network: dict | None = None

    @classmethod
    def load(cls, geo_dir: Path) -> Geography:
        rivers = None
        path = geo_dir / "river_network.json.gz"
        if path.exists():
            import gzip
            import json

            rivers = json.loads(gzip.decompress(path.read_bytes()))
        return cls(
            by_lod={lod: load_basin_features(geo_dir, lod) for lod in ("state", "basin")},
            river_network=rivers,
        )

    def provenance(self) -> dict:
        return dict(self.by_lod["state"].get("provenance", {}))

    def basins(self) -> list[dict]:
        out = []
        for f in self.by_lod["state"]["features"]:
            p = f["properties"]
            out.append({k: p.get(k) for k in ("id", "name", "regulation_class", "outlet_forecast_point_id", "centroid", "bbox", "area_km2_wbd_sum", "huc8")})
        return out

    def feature(self, basin_id: str, lod: str) -> dict | None:
        coll = self.by_lod[lod]
        for f in coll["features"]:
            if f["properties"].get("id") == basin_id:
                props = dict(f["properties"])
                props["provenance"] = dict(coll.get("provenance", {}))
                return {"type": "Feature", "id": basin_id, "properties": props, "geometry": f["geometry"]}
        return None
