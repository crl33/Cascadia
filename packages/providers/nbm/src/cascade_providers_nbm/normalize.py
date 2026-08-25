"""Decoded GRIB fields + a basin mask -> basin means, with units, times and quality decided.

This is where the provider's numbers become Cascadia Papsukkal numbers, and the three things
that must never be fudged are fixed here:

- **Units are asserted, never converted.** APCP arrives as ``kg m**-2``; that is millimetres
  of liquid water equivalent by definition, so the stored unit is ``mm`` and the native unit
  is recorded alongside it. If a cycle ever arrives in a different native unit the field is
  refused, not scaled. SNOWLVL has no unit in eccodes (NCEP local table), so its unit comes
  from docs/DATA_SOURCES.md W2 and carries the ``unit_from_documentation`` quality flag.
- **Times are three-valued.** ``issued_at`` is the model cycle, ``valid_time`` is the end of
  the accumulation window (or the instant for snow level), and ``available_at`` is when
  Cascadia Papsukkal could first have known it — ``max(cycle, retrieved_at)``.
- **A percentile field is pointwise.** Every percentile-derived mean carries the
  ``pointwise_percentile`` quality flag into the store, so nothing downstream can mistake it
  for a basin-scale percentile.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from cascade_geo import BasinMask, MaskError, weighted_mean
from cascade_hydrology.forcing import (
    POINTWISE_FLAG,
    QPF_UNIT,
    SNOW_LEVEL_UNIT,
    BasinQpf,
    qpf_feature,
    snow_level_feature,
)
from cascade_providers_nbm.parser import (
    APCP,
    NATIVE_UNITS,
    SNOWLVL,
    UNIT_FROM_DOCUMENTATION,
    Field,
    NbmParseError,
)

#: eccodes reports no unit for NCEP local-table parameters; the documented unit is used and
#: the value is flagged as documented rather than declared by the payload.
_UNDECLARED = {"unknown", ""}


@dataclass(frozen=True)
class Refusal:
    """A basin mean that was NOT computed, and exactly why. Never a substituted number."""

    basin_id: str
    feature: str
    reason: str
    kind: str


def stored_unit(field: Field) -> tuple[str, str, tuple[str, ...]]:
    """(stored unit, native unit, quality flags) for a decoded field."""
    native = field.units
    expected = NATIVE_UNITS.get(field.key.parameter)
    if field.key.parameter == APCP:
        if native != expected:
            raise NbmParseError("unexpected_unit", f"APCP arrived as {native!r}, expected {expected!r}; refusing to scale it")
        # kg m-2 of water equivalent IS mm of depth. A rename with a fixed identity, not a
        # unit conversion (DATA_DOCTRINE: values are never converted between units).
        return QPF_UNIT, native, ()
    if field.key.parameter == SNOWLVL:
        if native.strip().lower() in _UNDECLARED:
            return SNOW_LEVEL_UNIT, native, (UNIT_FROM_DOCUMENTATION,)
        if native != expected:
            raise NbmParseError("unexpected_unit", f"SNOWLVL arrived as {native!r}, expected {expected!r}; refusing to scale it")
        return SNOW_LEVEL_UNIT, native, ()
    raise NbmParseError("unknown_parameter", f"no unit policy for parameter {field.key.parameter}")


def basin_mean(field: Field, mask: BasinMask, *, basin_id: str) -> BasinQpf | Refusal:
    """Apply ``method:basin-qpf@1.0.0`` to one field over one basin.

    Returns a :class:`Refusal` rather than raising when the grid and the mask disagree or a
    masked cell has no value: the caller records the refusal with its reason so the surface
    can say UNKNOWN and why, which is the correct answer.
    """
    is_snow = field.key.parameter == SNOWLVL
    feature = (
        snow_level_feature(field.key.percentile)
        if is_snow
        else qpf_feature(field.key.end_step_h, field.key.percentile)
    )
    if mask.grid_definition_hash != field.grid.definition_hash:
        return Refusal(
            basin_id=basin_id,
            feature=feature,
            kind="grid_definition_changed",
            reason=(
                f"mask was built for grid {mask.grid_definition_hash[:12]}, this cycle carries "
                f"{field.grid.definition_hash[:12]}"
            ),
        )
    unit, native, flags = stored_unit(field)
    if field.values is None:
        raise NbmParseError("no_values", f"{feature}: field decoded without values")
    try:
        zonal = weighted_mean(field.values, mask, grid=field.grid)
    except MaskError as exc:
        return Refusal(basin_id=basin_id, feature=feature, kind=exc.kind, reason=exc.detail)
    quality = list(flags)
    if field.key.percentile is not None:
        quality.append(POINTWISE_FLAG)
    return BasinQpf(
        basin_id=basin_id,
        feature=feature,
        value=zonal.value,
        unit=unit,
        window_h=None if is_snow else field.key.window_h,
        percentile=field.key.percentile,
        cycle=field.cycle,
        valid_time=field.valid_time,
        cell_count=zonal.cell_count,
        weight_sum=zonal.weight_sum,
        masked_area_km2=mask.masked_area_km2,
        grid_definition_hash=field.grid.definition_hash,
        native_unit=native,
        quality=tuple(quality),
    )


def available_at_of(cycle: datetime, retrieved_at: datetime) -> datetime:
    """Knowledge time of a derived forecast feature (ADR-0010): max(cycle, retrieved_at)."""
    return max(cycle, retrieved_at)
