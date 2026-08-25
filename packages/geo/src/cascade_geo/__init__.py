"""cascade_geo — basin geometry, grid projections and zonal aggregation.

No provider code, no hydrology, no science: this package turns polygons and grid definitions
into masks and weighted means, and knows nothing about what is being aggregated.
"""

from cascade_geo.lcc import GridSpec, LambertConformalConic
from cascade_geo.masks import (
    METHOD_GRID_MASK,
    BasinMask,
    MaskError,
    ZonalMean,
    build_basin_mask,
    load_basin_polygons,
    polygons_of,
    weighted_mean,
)

__all__ = [
    "METHOD_GRID_MASK",
    "BasinMask",
    "GridSpec",
    "LambertConformalConic",
    "MaskError",
    "ZonalMean",
    "build_basin_mask",
    "load_basin_polygons",
    "polygons_of",
    "weighted_mean",
]
