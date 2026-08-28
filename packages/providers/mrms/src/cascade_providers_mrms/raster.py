"""MRMS's use of the shared window-raster cut (ADR-0020).

The general machinery — window constants, packing, the refusal when a grid stops covering
the window — lives in :mod:`cascade_geo.window_raster` so SNODAS and later fields share ONE
implementation. This module keeps MRMS's own decisions: QPE quantizes at 0.1 mm (hourly
accumulations live in 0–65 mm; 0.1 mm steps keep drizzle distinguishable), and the field
name the rows carry.
"""

from __future__ import annotations

from cascade_geo.window_raster import (
    METHOD_RASTER,
    SENTINEL,
    WindowOutsideGridError,
    WindowRaster,
)
from cascade_geo.window_raster import (
    cut_window as _cut,
)
from cascade_providers_mrms.parser import MrmsField

__all__ = ["FIELD_QPE", "METHOD_RASTER", "SCALE_MM", "SENTINEL", "WindowOutsideGridError", "WindowRaster", "cut_window"]

SCALE_MM = 0.1
FIELD_QPE = "qpe_01h"


def cut_window(field: MrmsField) -> WindowRaster:
    return _cut(field.grid, field.values, scale=SCALE_MM, unit="mm")
