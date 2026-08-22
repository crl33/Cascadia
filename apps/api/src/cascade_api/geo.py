"""Static basin geography from the committed LOD GeoJSON fixtures (cartographic truth class)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cascade_core.seed import load_basin_features


@dataclass(frozen=True)
class Geography:
    by_lod: dict[str, dict]

    @classmethod
    def load(cls, geo_dir: Path) -> Geography:
        return cls(by_lod={lod: load_basin_features(geo_dir, lod) for lod in ("state", "basin")})

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
