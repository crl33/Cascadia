"""Forcing surface v0: basin-scale precipitation forcing from NBM QPF percentiles.

Two versioned methods live here (docs/HYDROLOGY.md §4, p3-surfaces-design §1.4):

``method:basin-qpf@1.0.0``
    The area-weighted mean of one NBM field over one basin's grid mask. Arithmetic only —
    no banding, no judgement — but it is a Cascadia Papsukkal derivation and its rows say so.

``method:forcing-assessment@0.1.0``
    The banded surface state, its score and its drivers. EXPERIMENTAL by construction: the
    band edges are an ASSUMPTION (:data:`FORCING_BANDS`), not a calibrated threshold, and the
    score is not a probability of anything.

**The claim this module is most likely to overstate, and does not.** NBM percentile fields
are *pointwise*: the p90 field is the 90th percentile at each grid cell independently. The
area-weighted mean of a p90 field is therefore "the basin mean of the pointwise 90th
percentile", which is NOT the 90th percentile of basin-mean QPF — that would need the joint
spatial distribution, which the product does not carry. So every percentile-derived feature
id and every rendered label says ``pointwise``, the spread keys say ``pointwise``, and the
surface's confidence is capped at ``moderate`` while this is the spread method.

Nothing here averages an official forecast with a model forecast: NBM is MODELED guidance and
appears only as itself.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from cascade_contracts import (
    ConfidenceLabel,
    Freshness,
    FreshnessState,
    ProvenanceRef,
    Quantity,
    SourceKind,
    SurfaceState,
    TruthClass,
)
from cascade_contracts.visualization import Driver, SurfaceLevel
from cascade_core.freshness import compute_freshness
from cascade_core.knowledge import Knowledge
from cascade_core.models import Basin, DerivedFeature, SourceProduct
from cascade_core.registry import (
    PRODUCT_NBM_CORE,
    PRODUCT_NBM_QMD,
    SOURCES,
    SRC_CASCADE,
    SRC_NBM,
)

METHOD_BASIN_QPF = "method:basin-qpf@1.0.0"
#: The same area-weighted-mean arithmetic applied to the NBM snow-level field. It is a
#: separate id on purpose: a provenance popover that said `method:basin-qpf` over a snow level
#: would answer "what transformed this number" with the wrong answer.
METHOD_BASIN_SNOW_LEVEL = "method:basin-snow-level@1.0.0"
METHOD_FORCING_ASSESSMENT = "method:forcing-assessment@0.1.0"

FORCING_HORIZON_H = 72
#: Cumulative windows measured from the model cycle. 72 h is the assessed horizon; 24 and 48
#: are stored so a later method can use them without a re-ingest.
QPF_WINDOWS_H = (24, 48, 72)
#: Percentile levels stored per window. NBM qmd carries 0-100 % in 5 % steps; these five are
#: the ones the surface and its drivers use.
QPF_PERCENTILES = (10, 25, 50, 75, 90)
#: The percentile that the state is banded from.
HEADLINE_PERCENTILE = 50
#: Snow-level percentiles stored from NBM core, and the lead time the driver reports.
SNOW_LEVEL_PERCENTILES = (10, 50, 90)
SNOW_LEVEL_LEAD_H = 24

QPF_UNIT = "mm"  # kg m-2 of water equivalent IS mm of depth; a rename, never a conversion
SNOW_LEVEL_UNIT = "m"  # metres above mean sea level

#: How far back a cycle may be and still be read at all. Beyond this the surface is UNKNOWN
#: with the "no cycle" reason rather than showing a value from an arbitrary distance in time.
MAX_CYCLE_AGE = timedelta(days=2)

DIRECTION_INCREASES = "increases_forcing"
DIRECTION_DECREASES = "decreases_forcing"
DIRECTION_CONTEXT = "context_not_scored"

#: Quality flag every pointwise-percentile derivation carries into the store.
POINTWISE_FLAG = "pointwise_percentile"
#: Quality flag a refusal row carries when the provider's grid no longer matches any mask.
GRID_CHANGED_FLAG = "grid_definition_changed"


class ForcingReason:
    """The UNKNOWN vocabulary. A reason is always specific about which input is missing."""

    NO_CYCLE = "No NBM qmd cycle known at this knowledge time."
    NO_VALUE = "The latest NBM qmd cycle produced no usable basin mean for this basin."

    @staticmethod
    def grid_changed(grid_hash: str | None) -> str:
        shown = (grid_hash or "unknown")[:12]
        return (
            f"NBM grid definition changed (no basin mask for grid {shown}); "
            "the basin mean was refused rather than approximated."
        )


@dataclass(frozen=True)
class Band:
    """One band of a banded quantity: values below ``upper`` are ``level``."""

    upper: float | None  # None = open-ended top band
    level: SurfaceLevel


@dataclass(frozen=True)
class BandTable:
    """A versioned parameter block, not a chain of if-statements.

    ``assumption`` travels with the numbers wherever they are explained, because these edges
    are a defensible first cut for western-Washington basins and NOT a calibrated threshold.
    Calibration is hindcast-evaluation work (ADR-0008, docs/TESTING.md §7); until then the
    only property tested is that the banding is monotone and reproducible, never that it is
    right. When a ``Method`` table exists this block becomes a row in it.
    """

    method_id: str
    quantity: str
    unit: str
    bands: tuple[Band, ...]
    score_cap: float
    assumption: str

    def level(self, value: float) -> SurfaceLevel:
        for band in self.bands:
            if band.upper is None or value < band.upper:
                return band.level
        return self.bands[-1].level

    def score(self, value: float) -> float:
        """Piecewise-linear map onto [0, 1] using the same edges. Never a probability.

        Each band occupies an equal slice of [0, 1], so the score crosses 0.25 / 0.5 / 0.75
        exactly where the state changes, and is capped at ``score_cap``.
        """
        edges = [0.0] + [b.upper for b in self.bands if b.upper is not None] + [self.score_cap]
        v = min(max(value, 0.0), self.score_cap)
        slice_width = 1.0 / (len(edges) - 1)
        for idx in range(len(edges) - 1):
            lo, hi = edges[idx], edges[idx + 1]
            if v <= hi:
                span = hi - lo
                within = 0.0 if span <= 0 else (v - lo) / span
                return min(1.0, max(0.0, (idx + within) * slice_width))
        return 1.0


FORCING_BANDS = BandTable(
    method_id=METHOD_FORCING_ASSESSMENT,
    quantity="basin mean of the NBM pointwise 50th-percentile QPF, 0-72 h",
    unit=QPF_UNIT,
    bands=(
        Band(25.0, SurfaceLevel.LOW),
        Band(75.0, SurfaceLevel.MODERATE),
        Band(150.0, SurfaceLevel.HIGH),
        Band(None, SurfaceLevel.VERY_HIGH),
    ),
    score_cap=200.0,
    assumption=(
        "ASSUMPTION, not a calibrated threshold: 25/75/150 mm per 72 h are a defensible first "
        "cut for western-Washington basins (75 mm/72 h is roughly the scale at which Cascade "
        "foothill basins begin producing action-stage responses). They have not passed "
        "hindcast evaluation, so this surface is EXPERIMENTAL and its score is not a "
        "probability of anything (ADR-0008)."
    ),
)

POINTWISE_CAVEAT = (
    "NBM percentile fields are pointwise: this is the basin mean of a per-cell percentile, "
    "not the percentile of basin-mean QPF. The two differ and only the first is computable "
    "from this product."
)


# ------------------------------------------------------------------ feature vocabulary


def qpf_feature(window_h: int, percentile: int | None) -> str:
    """``basin_qpf_72h_pointwise_p50`` / ``basin_qpf_72h_deterministic``.

    ``pointwise`` is in the id on purpose: an id of ``basin_qpf_72h_p90`` would assert a
    basin-scale 90th percentile that this product cannot support (p3-surfaces-design §1.4).
    """
    if percentile is None:
        return f"basin_qpf_{window_h}h_deterministic"
    return f"basin_qpf_{window_h}h_pointwise_p{percentile}"


def snow_level_feature(percentile: int | None) -> str:
    if percentile is None:
        return "basin_snow_level_deterministic"
    return f"basin_snow_level_pointwise_p{percentile}"


def qpf_label(window_h: int, percentile: int | None) -> str:
    if percentile is None:
        return f"basin mean of the NBM deterministic QPF, 0-{window_h} h"
    return f"basin mean of the NBM pointwise {_ordinal(percentile)}-percentile QPF, 0-{window_h} h"


def snow_level_label(percentile: int | None, lead_h: int) -> str:
    if percentile is None:
        return f"basin mean of the NBM deterministic snow level at +{lead_h} h"
    return f"basin mean of the NBM pointwise {_ordinal(percentile)}-percentile snow level at +{lead_h} h"


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def window_label(window_h: int) -> str:
    return f"{window_h}h"


# ------------------------------------------------------------------ method:basin-qpf


@dataclass(frozen=True)
class BasinQpf:
    """One basin mean of one NBM field: the output of ``method:basin-qpf@1.0.0``."""

    basin_id: str
    feature: str
    value: float
    unit: str
    window_h: int | None
    percentile: int | None
    cycle: datetime
    valid_time: datetime
    cell_count: int
    weight_sum: float
    masked_area_km2: float
    grid_definition_hash: str
    native_unit: str
    quality: tuple[str, ...] = ()


# ---------------------------------------------------------- source kinds from the registry

_SOURCE_KINDS: dict[str, str] = {str(s["id"]): str(s["kind"]) for s in SOURCES}


def source_kind_of(source_id: str) -> SourceKind:
    """Resolve a source's kind from the registry — never hardcode one at a call site.

    docs/DATA_DOCTRINE.md §2: the registry (and the seeded ``data_source`` row it becomes)
    is the only declaration of a source's kind. An unknown id yields ``UNKNOWN``, which is a
    legitimate state; guessing is not.
    """
    try:
        return SourceKind(_SOURCE_KINDS[source_id])
    except (KeyError, ValueError):
        return SourceKind.UNKNOWN


def _product_source(product_id: str, products: dict[str, SourceProduct]) -> str:
    product = products.get(product_id)
    return product.source_id if product is not None else SRC_NBM


def _fresh(products: dict[str, SourceProduct], product_id: str, *, cycle: datetime | None, retrieved_at: datetime | None, now: datetime) -> Freshness:
    product = products.get(product_id)
    return compute_freshness(
        expected_cadence_seconds=product.expected_cadence_seconds if product else None,
        grace_seconds=product.grace_seconds if product else None,
        # The anchor is the CYCLE, not the valid time: a 72-h QPF is legitimately valid in the
        # future, and anchoring on it would report every forecast as perfectly fresh.
        valid_time=cycle,
        retrieved_at=retrieved_at,
        now=now,
    )


# ------------------------------------------------------- method:forcing-assessment@0.1.0


@dataclass(frozen=True)
class ForcingAssessment:
    surface: SurfaceState
    refs: dict[str, ProvenanceRef]
    drivers: tuple[Driver, ...]


def _unknown(basin_id: str, reason: str) -> ForcingAssessment:
    key = assessment_ref_key(basin_id)
    return ForcingAssessment(
        surface=SurfaceState(
            state=SurfaceLevel.UNKNOWN,
            horizon_h=FORCING_HORIZON_H,
            prov=key,
            truth=TruthClass.CASCADE_DERIVED,
            confidence=ConfidenceLabel.UNKNOWN,
            experimental=True,
            reason=reason,
        ),
        refs={
            key: ProvenanceRef(
                source_id=SRC_CASCADE,
                source_kind=SourceKind.EXPERIMENTAL,
                method_id=METHOD_FORCING_ASSESSMENT,
                freshness=Freshness(state=FreshnessState.MISSING),
                # The reason travels with the provenance too: a popover on an UNKNOWN surface
                # must say the same specific thing the surface says.
                label=f"Cascade forcing assessment (EXPERIMENTAL): {reason}",
            )
        },
        drivers=(),
    )


def assessment_ref_key(basin_id: str) -> str:
    return f"cascade-forcing-{basin_id.split(':')[-1]}"


def qpf_ref_key(basin_id: str) -> str:
    return f"nbm-forcing-{basin_id.split(':')[-1]}"


def snow_ref_key(basin_id: str) -> str:
    return f"nbm-snowlvl-{basin_id.split(':')[-1]}"


def assess_from_rows(
    basin_id: str,
    *,
    qpf_rows: Sequence[DerivedFeature],
    snow_rows: Sequence[DerivedFeature] = (),
    products: dict[str, SourceProduct],
    now: datetime,
) -> ForcingAssessment:
    """Band the surface from stored basin-QPF rows of ONE cycle.

    ``qpf_rows`` must all share an ``issued_at`` — mixing cycles inside one spread would
    describe a forecast that was never issued. The caller (:func:`assess`) enforces that by
    selecting a cycle first.
    """
    by_feature = {row.feature: row for row in qpf_rows}
    headline = by_feature.get(qpf_feature(FORCING_HORIZON_H, HEADLINE_PERCENTILE))
    if headline is None:
        return _unknown(basin_id, ForcingReason.NO_CYCLE)
    if headline.value is None:
        reason = (
            ForcingReason.grid_changed((headline.values_json or {}).get("grid_definition_hash"))
            if GRID_CHANGED_FLAG in (headline.quality or [])
            else ForcingReason.NO_VALUE
        )
        return _unknown(basin_id, reason)

    product_id = headline.product_id or PRODUCT_NBM_QMD
    qpf_key, snow_key, assess_key = qpf_ref_key(basin_id), snow_ref_key(basin_id), assessment_ref_key(basin_id)
    freshness = _fresh(products, product_id, cycle=headline.issued_at, retrieved_at=headline.available_at, now=now)
    confidence = {
        FreshnessState.CURRENT: ConfidenceLabel.MODERATE,  # capped at moderate: pointwise spread
        FreshnessState.PARTIAL: ConfidenceLabel.LOW,
        FreshnessState.STALE: ConfidenceLabel.LOW,
        FreshnessState.DEGRADED: ConfidenceLabel.LOW,
    }.get(freshness.state, ConfidenceLabel.LOW)

    refs: dict[str, ProvenanceRef] = {
        qpf_key: ProvenanceRef(
            source_id=_product_source(product_id, products),
            source_kind=source_kind_of(_product_source(product_id, products)),
            product_id=product_id,
            method_id=headline.method_id,
            issued_at=headline.issued_at,
            valid_time=headline.valid_time,
            retrieved_at=headline.computed_at,
            freshness=freshness,
            quality=(POINTWISE_FLAG,),
            label=f"NBM v5.0 basin-mean QPF, {FORCING_HORIZON_H} h, pointwise percentile spread. {POINTWISE_CAVEAT}",
            raw_artifact_id=str(headline.raw_artifact_id) if headline.raw_artifact_id is not None else None,
        ),
        assess_key: ProvenanceRef(
            source_id=SRC_CASCADE,
            source_kind=SourceKind.EXPERIMENTAL,
            product_id=product_id,
            method_id=METHOD_FORCING_ASSESSMENT,
            issued_at=headline.issued_at,
            valid_time=headline.valid_time,
            retrieved_at=headline.computed_at,
            freshness=freshness,
            label=f"Cascade forcing assessment (EXPERIMENTAL) banded from NBM basin QPF. {FORCING_BANDS.assumption}",
        ),
    }

    drivers: list[Driver] = [
        Driver(feature=headline.feature, value=headline.value, unit=headline.unit, direction=DIRECTION_INCREASES, rank=1, prov=qpf_key)
    ]
    spread: dict[str, float] = {}
    for rank, (percentile, direction) in enumerate(((90, DIRECTION_INCREASES), (10, DIRECTION_DECREASES)), start=2):
        row = by_feature.get(qpf_feature(FORCING_HORIZON_H, percentile))
        if row is None or row.value is None:
            continue
        spread[f"pointwise_p{percentile}"] = row.value
        drivers.append(Driver(feature=row.feature, value=row.value, unit=row.unit, direction=direction, rank=rank, prov=qpf_key))

    snow = _nearest_snow_row(snow_rows)
    if snow is not None and snow.value is not None:
        snow_product = snow.product_id or PRODUCT_NBM_CORE
        snow_source = _product_source(snow_product, products)
        lead_h = int(round((snow.valid_time - snow.issued_at).total_seconds() / 3600)) if snow.issued_at else SNOW_LEVEL_LEAD_H
        refs[snow_key] = ProvenanceRef(
            source_id=snow_source,
            source_kind=source_kind_of(snow_source),
            product_id=snow_product,
            method_id=snow.method_id,
            issued_at=snow.issued_at,
            valid_time=snow.valid_time,
            retrieved_at=snow.computed_at,
            freshness=_fresh(products, snow_product, cycle=snow.issued_at, retrieved_at=snow.available_at, now=now),
            quality=(POINTWISE_FLAG,),
            # HYDROLOGY snow doctrine: a snow level is context. It is not scored, and more
            # snow is never more risk on its own.
            label=f"{snow_level_label(SNOW_LEVEL_PERCENTILES[1], lead_h)} (context only; not scored)",
            raw_artifact_id=str(snow.raw_artifact_id) if snow.raw_artifact_id is not None else None,
        )
        drivers.append(
            Driver(feature=snow.feature, value=snow.value, unit=snow.unit, direction=DIRECTION_CONTEXT, rank=len(drivers) + 1, prov=snow_key)
        )

    level = FORCING_BANDS.level(headline.value)
    return ForcingAssessment(
        surface=SurfaceState(
            state=level,
            horizon_h=FORCING_HORIZON_H,
            score=FORCING_BANDS.score(headline.value),
            value=Quantity(value=headline.value, unit=headline.unit),
            spread=spread or None,
            prov=assess_key,
            truth=TruthClass.CASCADE_DERIVED,
            confidence=confidence,
            experimental=True,
            reason=None,
        ),
        refs=refs,
        drivers=tuple(drivers),
    )


def _nearest_snow_row(rows: Sequence[DerivedFeature]) -> DerivedFeature | None:
    """The snow-level row at the shortest lead time of the newest cycle.

    Lead times are never averaged together: a snow level at +24 h and one at +72 h are two
    different forecasts, and the driver reports one of them and says which.
    """
    if not rows:
        return None
    newest = max(r.issued_at for r in rows if r.issued_at is not None) if any(r.issued_at for r in rows) else None
    candidates = [r for r in rows if r.issued_at == newest] if newest else list(rows)
    return min(candidates, key=lambda r: r.valid_time)


async def assess(k: Knowledge, basin: Basin, products: dict[str, SourceProduct], *, now: datetime | None = None) -> ForcingAssessment:
    """Read the stored basin-QPF features known at ``k.as_of`` and band the surface.

    Reads four features per basin: the 72-h pointwise p50 (which selects the cycle), the
    pointwise p90 and p10 of that same cycle, and the snow-level context driver. A cycle
    older than :data:`MAX_CYCLE_AGE` is not read at all — the surface says it has no cycle
    rather than presenting an arbitrary old one.
    """
    when = now or k.as_of
    horizon_rows = await k.derived_features(
        qpf_feature(FORCING_HORIZON_H, HEADLINE_PERCENTILE),
        basin.id,
        method_id=METHOD_BASIN_QPF,
        window=window_label(FORCING_HORIZON_H),
        valid_from=when - MAX_CYCLE_AGE,
    )
    # The stored knowledge filter is on valid_time; the honest bound is on the CYCLE, since a
    # 72-h forecast's valid_time is three days later than the cycle it came from.
    horizon_rows = [r for r in horizon_rows if r.issued_at is not None and r.issued_at >= when - MAX_CYCLE_AGE]
    if not horizon_rows:
        return _unknown(basin.id, ForcingReason.NO_CYCLE)
    cycle = max((r.issued_at for r in horizon_rows if r.issued_at is not None), default=None)
    qpf_rows = [r for r in horizon_rows if r.issued_at == cycle]
    for percentile in (90, 10):
        qpf_rows += [
            r
            for r in await k.derived_features(
                qpf_feature(FORCING_HORIZON_H, percentile),
                basin.id,
                method_id=METHOD_BASIN_QPF,
                window=window_label(FORCING_HORIZON_H),
                valid_from=when - MAX_CYCLE_AGE,
            )
            if r.issued_at == cycle
        ]
    snow_rows = [
        r
        for r in await k.derived_features(
            snow_level_feature(SNOW_LEVEL_PERCENTILES[1]),
            basin.id,
            method_id=METHOD_BASIN_SNOW_LEVEL,
            valid_from=when - MAX_CYCLE_AGE,
        )
        if r.issued_at is not None and r.issued_at >= when - MAX_CYCLE_AGE
    ]
    return assess_from_rows(basin.id, qpf_rows=qpf_rows, snow_rows=snow_rows, products=products, now=when)
