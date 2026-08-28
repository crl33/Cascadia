"""Basin hypsometry: the elevation-area curve that turns a snow level into an area fraction.

Reads ``basin_hypsometry.json`` from the geo directory — derived offline by
``scripts/build_basin_hypsometry.py`` from USGS 3DEP 1-arc-second tiles and checked in like every
other geometry fixture, so it ships with the container and never touches the network or a raster
library at runtime. This module is deliberately stdlib-only.

Two facts every consumer must carry forward, recorded here because this is the choke point:

- **The geometry is the seeded HUC8 union**, not an outlet-delineated contributing area. A
  fraction of this surface is a fraction of the HUC8 union; presenting it as "the basin above the
  gauge" would claim a delineation nobody has done. The caveat text travels on the object.
- **The curve is far more precise than anything it will be intersected with.** 20 m bins against
  a forecast snow level whose p10-p90 spread has a 241 m median — so interpolation details inside
  a bin cannot matter, and the honest uncertainty always comes from the snow level, never from
  the terrain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

METHOD_ID = "method:basin-hypsometry@1.0.0"

__all__ = ["METHOD_ID", "BasinHypsometry", "Hypsometry", "HypsometryError", "load_hypsometry"]


class HypsometryError(Exception):
    """The file is missing or malformed. Refused loudly; never a silently absent curve."""


@dataclass(frozen=True)
class BasinHypsometry:
    """One basin's elevation-area distribution, in km2 per fixed-width bin."""

    basin_id: str
    origin_m: float
    bin_m: float
    counts_km2: tuple[float, ...]
    under_km2: float  # area below origin (tidal flats, small negatives at the delta)
    over_km2: float  # area above the last bin edge
    total_km2: float
    min_m: float
    max_m: float

    def fraction_below(self, elevation_m: float) -> float:
        """Fraction of the basin surface at or below ``elevation_m``, in [0, 1].

        Linear within a bin (a 20 m bin against a 241 m-spread input; the interpolation cannot
        matter). Clamped: below the lowest terrain the answer is 0, above the highest it is 1 —
        which is itself information ("the entire surface is below the snow level" is the normal
        late-summer state on a low basin).
        """
        if self.total_km2 <= 0:
            raise HypsometryError(f"{self.basin_id}: zero total area")
        if elevation_m <= self.origin_m:
            below = self.under_km2 if elevation_m >= self.min_m else 0.0
            return below / self.total_km2
        area = self.under_km2
        span = elevation_m - self.origin_m
        full_bins = int(span // self.bin_m)
        if full_bins >= len(self.counts_km2):
            return 1.0 if elevation_m >= self.max_m else (
                (area + sum(self.counts_km2)) / self.total_km2
            )
        area += sum(self.counts_km2[:full_bins])
        area += self.counts_km2[full_bins] * ((span - full_bins * self.bin_m) / self.bin_m)
        return min(1.0, area / self.total_km2)


@dataclass(frozen=True)
class Hypsometry:
    basins: dict[str, BasinHypsometry]
    method_id: str
    derived_at: str
    dem_product: str
    #: The HUC8-union caveat, verbatim from the derivation — consumers print it, never soften it.
    geometry_caveat: str

    def for_basin(self, basin_id: str) -> BasinHypsometry | None:
        return self.basins.get(basin_id)


def _req(obj: dict, key: str, ctx: str):
    if key not in obj:
        raise HypsometryError(f"missing {key!r} in {ctx}")
    return obj[key]


def load_hypsometry(path: Path) -> Hypsometry:
    """Load and validate the checked-in curves. Absent file raises — the caller decides policy."""
    try:
        doc = json.loads(path.read_text())
    except FileNotFoundError as e:
        raise HypsometryError(f"no hypsometry file at {path}") from e
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HypsometryError(f"{path} is not JSON: {e}") from e

    prov = _req(doc, "_provenance", str(path))
    bins = _req(prov, "bins", "_provenance")
    origin = float(_req(bins, "origin_m", "bins"))
    width = float(_req(bins, "width_m", "bins"))
    if width <= 0:
        raise HypsometryError(f"non-positive bin width {width}")
    caveat = str(_req(_req(prov, "polygon_source", "_provenance"), "caveat", "polygon_source"))

    basins: dict[str, BasinHypsometry] = {}
    for basin_id, row in _req(doc, "basins", str(path)).items():
        counts = tuple(float(c) for c in _req(row, "counts_km2", basin_id))
        if any(c < 0 for c in counts):
            raise HypsometryError(f"{basin_id}: negative bin area")
        total = float(_req(row, "total_km2", basin_id))
        parts = sum(counts) + float(row.get("under_km2", 0.0)) + float(row.get("over_km2", 0.0))
        if total <= 0 or abs(parts - total) > 0.01 * total:
            raise HypsometryError(
                f"{basin_id}: bins sum to {parts:.1f} km2 but total says {total:.1f} — the curve "
                "does not account for its own area"
            )
        basins[basin_id] = BasinHypsometry(
            basin_id=basin_id,
            origin_m=origin,
            bin_m=width,
            counts_km2=counts,
            under_km2=float(row.get("under_km2", 0.0)),
            over_km2=float(row.get("over_km2", 0.0)),
            total_km2=total,
            min_m=float(_req(row, "min_m", basin_id)),
            max_m=float(_req(row, "max_m", basin_id)),
        )
    if not basins:
        raise HypsometryError(f"{path} carries no basins")
    return Hypsometry(
        basins=basins,
        method_id=str(_req(prov, "method_id", "_provenance")),
        derived_at=str(_req(prov, "derived_at", "_provenance")),
        dem_product=str(_req(_req(prov, "dem", "_provenance"), "product", "dem")),
        geometry_caveat=caveat,
    )
