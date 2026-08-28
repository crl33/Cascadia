"""Visualization contracts (docs/VISUALIZATION_CONTRACTS.md §2–§3, §7–§8).

Rules enforced here by type:
- every scientific value carries `prov` (a key into the envelope's provenance_refs) and a
  `truth` class;
- no field names a renderer concept (no colour, material, opacity, camera);
- thresholds carry `basis` (stage|flow), unit and datum so the client can never compare the
  wrong things.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import Field, model_validator

from cascade_contracts.common import (
    CONTRACT_VERSION,
    ConfidenceLabel,
    ProvenanceRef,
    Quantity,
    StrictModel,
    TruthClass,
)


class FloodCategory(StrEnum):
    NONE = "none"
    ACTION = "action"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    UNKNOWN = "unknown"


class SurfaceLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNKNOWN = "unknown"


class AgreementLevel(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class TimeContext(StrictModel):
    valid: datetime
    mode: str = Field(pattern="^(now|past|forecast)$")


class Provenanced(StrictModel):
    prov: str = Field(description="key into ContractEnvelope.provenance_refs")
    truth: TruthClass


class SurfaceState(Provenanced):
    """One of the risk surfaces (docs/HYDROLOGY.md §3–§6).

    `state` is the banded answer, `value` is the quantity it was banded from, and `spread`
    names the uncertainty points that came with that quantity. **None of `score`, `value` or
    `spread` is ever a probability.** Where `experimental` is true the surface is a Cascadia
    Papsukkal derivation whose method has not passed hindcast evaluation, so its number is
    EXPERIMENTAL by definition: it carries a `method_id` through `prov`, it is uncalibrated,
    and no client may render it as a chance of anything (ADR-0008, docs/DATA_DOCTRINE.md §9).
    A threshold-crossing probability may only ever come from counted model members, never
    from here. `state = unknown` with a specific `reason` is a legitimate, correct answer;
    a fabricated value is not.
    """

    state: SurfaceLevel
    horizon_h: int | None = Field(default=None, ge=0)
    score: float | None = Field(
        default=None, ge=0, le=1,
        description="EXPERIMENTAL index in [0,1] from the surface's own band table; never a probability",
    )
    value: Quantity | None = Field(
        default=None,
        description=(
            "the headline quantity `state` was banded from, in its own unit (e.g. 72-h "
            "basin-mean QPF in mm, or a day-of-year flow percentile in pct). EXPERIMENTAL "
            "whenever `experimental` is true; never a probability"
        ),
    )
    spread: dict[str, float] | None = Field(
        default=None,
        description=(
            "named spread points for `value`, in the SAME unit, e.g. {'p10': 88.0, 'p90': "
            "211.0}. Keys name the method's own statistic and nothing more: a model's "
            "pointwise percentile is not a basin-scale percentile and must be labeled as "
            "what it is. Never a probability"
        ),
    )
    confidence: ConfidenceLabel = ConfidenceLabel.UNKNOWN
    experimental: bool = False
    reason: str | None = Field(default=None, description="why UNKNOWN, when it is")


class HazardState(Provenanced):
    horizon_h: int = Field(ge=0)
    official_category: FloodCategory
    official_prov: str | None = None
    model_probability: dict[str, str | float] | None = Field(
        default=None, description='e.g. {"model": "nwm-mr-ens", "exceeds": "minor", "fraction": 0.43}'
    )
    cascade_index: float | None = Field(default=None, description="only after hindcast evaluation (ADR-0008)")
    reason: str | None = None


class AgreementState(StrictModel):
    state: AgreementLevel
    reason: str | None = Field(default=None, description="why UNKNOWN/LOW, when it is")
    explanation_ref: str | None = None
    prov: tuple[str, ...] = ()


class Driver(StrictModel):
    feature: str
    value: float | None = None
    unit: str | None = None
    direction: str
    rank: int = Field(ge=1)
    prov: str


class BandBoundary(StrEnum):
    """Whether the reference distribution can separate this value from a band edge.

    A **condition**, not a confidence: there is no number here and no coverage claim. The
    day-of-year ladder's breakpoints are sample quantiles estimated from a finite number of
    independent years, so a value sitting a point or two from a band edge is not distinguishable
    from the other side of it by the record that drew the edge.

    - ``separated`` — no band edge lies inside the reported sampling error of the percentile.
    - ``near_band_edge`` — one does; :attr:`HydrologicState.bands_within_sampling_error` names
      the bands the record cannot tell apart here.
    - ``unquantified`` — the sample size behind the ladder is not known, so the question cannot
      be answered at all. This is the **fail-closed** state: it never means "separated".
    """

    SEPARATED = "separated"
    NEAR_BAND_EDGE = "near_band_edge"
    UNQUANTIFIED = "unquantified"


class ReferenceWindow(StrictModel):
    """The empirical day-of-year sample a level statement is ranked against.

    Printed beside every number derived from it, because a rank means nothing without the
    sample it is a rank in. `independent_years` is the sample count deflated by the smoothing
    window (a ±2-day window pools 5 consecutive days of each year, so `n` days are not `n`
    independent draws); it is the denominator any statement about sampling error must use.
    """

    doy_key: str = Field(pattern=r"^\d{2}-\d{2}$", description='day-of-year key, "MM-DD"')
    window_days: int = Field(ge=0, description="half-width of the smoothing window in days")
    n: int = Field(ge=0, description="values in the window sample")
    independent_years: int = Field(ge=0, description="n deflated by the smoothing window; the honest denominator")
    period_start: int | None = Field(
        default=None,
        description=(
            "first calendar year of the record the reference was built from. A calendar SPAN, "
            "not a count of years with data: a gauge can reach back further than it observed"
        ),
    )
    period_end: int | None = None
    method_id: str = Field(description="the climatology method that built the sample, method:<name>@<semver>")


class SeasonalMultiple(StrictModel):
    """`value ÷ the day-of-year reference flow`. Unbounded, and never a flood magnitude.

    The reference is the ladder's TOP stored breakpoint, so `multiple >= 1` is exactly the
    condition under which the percentile clamps: this begins where the percentile stops
    discriminating. It is a multiple of a *seasonal* reference — a late-summer flash flow on a
    tiny denominator can exceed a winter flood's multiple — so the absolute flow always renders
    beside it, and it is never banded on a year-round cutoff.
    """

    multiple: float = Field(ge=0)
    reference_percentile: int = Field(ge=0, le=100)
    reference: Quantity = Field(description="the reference flow itself, in the observation's own unit")
    prov: str


class RecordRank(StrictModel):
    """Where the value sits among the reference window sample, as a count and nothing more.

    Deliberately not a plotting position: "3rd largest of 491 daily means" says its own sample
    size, where "p99.48" advertises resolution the sample does not have. Censored at 1 — a value
    above the record maximum is "the largest", and so is one twice as big — but it censors
    HONESTLY, naming the record it beat. `rank` is None where only a bound is available, and
    `reason` then says why.
    """

    rank: int | None = Field(default=None, ge=1, description="1 = largest; None when only a bound is known")
    of: int = Field(ge=1, description="sample size including the value being ranked")
    exceeds_record: bool = False
    previous_max: Quantity | None = None
    previous_max_day: date | None = None
    reason: str | None = None
    prov: str


class HydrologicState(StrictModel):
    """Where the river is: one observation said three ways that are never combined.

    `percentile` is the shipped, still-clamped day-of-year percentile — unchanged, uncalibrated
    and EXPERIMENTAL. `rank` says how unusual it is against a named record. `multiple` says how
    big it is against a named reference. **There is no fourth field summarising the three, and
    there must never be one**: a composite of these would be exactly the flood-risk score the
    doctrine forbids. A client may not colour, size or order one of them by another.
    """

    prov: str
    truth: TruthClass
    observed: Quantity = Field(description="the daily-mean flow the three statements are about")
    day: date = Field(description="the station-local calendar day the daily mean covers")
    percentile: float | None = Field(default=None, ge=0, le=100)
    percentile_clamped: bool = Field(
        default=False,
        description="the value fell outside the stored ladder, so the percentile is a bound, not an estimate",
    )
    reference: ReferenceWindow | None = None
    rank: RecordRank | None = None
    multiple: SeasonalMultiple | None = None
    boundary: BandBoundary = BandBoundary.UNQUANTIFIED
    bands_within_sampling_error: tuple[SurfaceLevel, ...] = Field(
        default=(), description="the bands the reference distribution cannot separate here; empty when it can"
    )
    reason: str | None = None


class StateChange(StrictModel):
    """How fast the river is moving, as a multiplicative growth of the daily mean over a window.

    `growth = Q(t) / Q(t − window_h)`. Computed on the observation, never on the percentile: the
    ladder clamps, so a percentile derivative reads +0 through a crest. Three properties follow
    and all three are load-bearing — it does not depend on any ladder or its vintage, it has no
    extrapolated region (it is arithmetic on two observations), and it stays exact while the
    level is censored.

    It is a **driver, not a score**: nothing here is weighted against the level, and no band edge
    is drawn on it. `rank` answers "is that fast?" descriptively, against this gauge's own past
    changes over the same window, because no evidence yet exists for a cutoff.
    """

    window_h: int = Field(ge=1)
    growth: float | None = Field(default=None, gt=0, description="Q(t) / Q(t − window_h); dimensionless")
    direction: str = Field(pattern="^(rising|falling|steady|unknown)$")
    from_value: Quantity | None = None
    to_value: Quantity | None = None
    span_h: float | None = Field(default=None, description="the span actually covered, which is what growth is over")
    rank: int | None = Field(default=None, ge=1, description="1 = largest change in this gauge's record")
    rank_of: int | None = Field(default=None, ge=1)
    rank_reason: str | None = Field(default=None, description="why the rank is absent or a bound")
    reason: str | None = Field(default=None, description="why growth is absent, when it is")
    prov: str


class AntecedentPrecip(StrictModel):
    """Basin-mean precipitation that has ALREADY fallen over a trailing window (observed QPE).

    A wetness driver beside the forecast surface, never fused with it. The window ENDS at the
    newest observed hour known at this knowledge time (`window_end`), not at the request
    instant: the radar-gauge product reaches the archive about an hour after the fact, and a
    wall-clock window would report every recent hour as missing on a healthy feed.

    `total` is the sum of exactly the hours that exist. When hours are missing inside the
    window, the total is a KNOWN UNDERESTIMATE and `reason` says so — it is never scaled up to
    "estimate" the gap, because a scaled gap is a fabricated number wearing an observed truth
    class. `hours_present` / `hours_expected` carry the coverage arithmetic so a client can
    qualify the display without re-deriving it.
    """

    window_h: int = Field(ge=1)
    window_end: datetime | None = Field(
        default=None, description="end of the newest hour included; None when nothing is known"
    )
    total: Quantity | None = None
    hours_present: int = Field(ge=0)
    hours_expected: int = Field(ge=1)
    truth: TruthClass
    prov: str
    reason: str | None = None


class OfficialAlert(StrictModel):
    id: str
    event: str
    severity: str | None = None
    onset: datetime | None = None
    expires: datetime | None = None
    issuer: str
    prov: str


class GeometryRef(StrictModel):
    lod: str = Field(pattern="^(orbital|state|basin|river|local|ground)$")
    feature_id: str
    url: str | None = Field(default=None, description="GeoJSON or tile URL template; cartographic truth class")


class BasinSurfaces(StrictModel):
    susceptibility: SurfaceState
    forcing: SurfaceState
    hazard: HazardState
    agreement: AgreementState


class BasinVisualizationState(StrictModel):
    id: str = Field(pattern=r"^basin:[a-z0-9-]+$")
    name: str
    regulation_class: str = Field(pattern="^(natural|partially_regulated|regulated|regulated_upper|unknown)$")
    surfaces: BasinSurfaces
    tension: float | None = Field(default=None, ge=0, le=1, description="wake-up intensity hint; documented method; not a probability")
    #: The high-tail level statement and its velocity, beside the banded surface and never fused
    #: with it (docs/research/high-tail-selection-2026-08-27.md §9). Both are absent where the
    #: inputs are, with a reason on the state and on each change.
    hydrologic_state: HydrologicState | None = None
    state_change: tuple[StateChange, ...] = ()
    headline_drivers: tuple[Driver, ...] = ()
    official_alerts: tuple[OfficialAlert, ...] = ()
    #: Observed trailing-window precipitation (6/24/72 h), a driver beside the surfaces.
    antecedent_precip: tuple[AntecedentPrecip, ...] = ()
    outlet_forecast_point_id: str | None = None
    geometry_ref: GeometryRef
    label_priority: int = Field(default=3, ge=1, le=5)


class ObservedRiverState(Provenanced):
    stage: Quantity | None = None
    flow: Quantity | None = None
    valid_time: datetime


class Trend(Provenanced):
    window_h: int = Field(ge=1)
    rate: Quantity | None = None
    direction: str = Field(pattern="^(rising|falling|steady|unknown)$")


class Headroom(StrictModel):
    basis: str = Field(pattern="^(stage|flow)$")
    to_category: FloodCategory
    value: Quantity | None = None
    time_to_threshold_h: float | None = None
    prov: str
    reason: str | None = None


class OfficialForecastSummary(Provenanced):
    issued_at: datetime
    issuer: str
    crest: Quantity | None = None
    crest_valid_time: datetime | None = None
    category: FloodCategory
    points: int = Field(ge=0)


class Thresholds(StrictModel):
    basis: str = Field(pattern="^(stage|flow)$")
    unit: str
    datum: str | None = None
    action: float | None = None
    minor: float | None = None
    moderate: float | None = None
    major: float | None = None
    prov: str

    @model_validator(mode="after")
    def _stage_requires_datum(self) -> Thresholds:
        if self.basis == "stage" and self.datum is None:
            raise ValueError("stage thresholds must carry a vertical datum (ADR-0009)")
        return self


class Topology(StrictModel):
    upstream: tuple[str, ...] = ()
    downstream: tuple[str, ...] = ()


class Regulation(StrictModel):
    class_: str = Field(alias="class", pattern="^(natural|partially_regulated|regulated|regulated_upper|unknown)$")
    regulated_by: tuple[str, ...] = ()

    model_config = {"populate_by_name": True, "extra": "forbid", "frozen": True}


class RiverVisualizationState(StrictModel):
    id: str = Field(pattern=r"^fp:nwps:[A-Z0-9]+$|^station:[a-z]+:[A-Za-z0-9:._-]+$")
    name: str
    station_id: str | None = None
    reach_id: str | None = None
    basin_id: str
    observed: ObservedRiverState | None = None
    observed_category: FloodCategory = FloodCategory.UNKNOWN
    observed_category_reason: str | None = None
    trend: Trend | None = None
    headroom: Headroom | None = None
    official_forecast: OfficialForecastSummary | None = None
    thresholds: Thresholds | None = None
    topology: Topology = Topology()
    regulation: Regulation = Regulation(class_="unknown")  # type: ignore[call-arg]  # populate_by_name resolves the "class" alias
    location: tuple[float, float] | None = Field(default=None, description="[lon, lat] WGS84; cartographic")
    flow_visual_intensity: float | None = Field(default=None, ge=0, le=1, description="display hint from percentile; not depth")


class ContractEnvelope(StrictModel):
    contract: str
    version: str = CONTRACT_VERSION
    generated_at: datetime
    as_of: datetime
    time: TimeContext
    items: tuple[BasinVisualizationState | RiverVisualizationState, ...]
    provenance_refs: dict[str, ProvenanceRef]

    @model_validator(mode="after")
    def _all_prov_keys_resolve(self) -> ContractEnvelope:
        missing: set[str] = set()

        def visit(obj: object) -> None:
            if isinstance(obj, StrictModel):
                for name in type(obj).model_fields:
                    val = getattr(obj, name)
                    if name == "prov" and isinstance(val, str) and val not in self.provenance_refs:
                        missing.add(val)
                    elif name == "prov" and isinstance(val, tuple):
                        missing.update(v for v in val if v not in self.provenance_refs)
                    elif name in ("official_prov",) and isinstance(val, str) and val not in self.provenance_refs:
                        missing.add(val)
                    else:
                        visit(val)
            elif isinstance(obj, (list, tuple)):
                for v in obj:
                    visit(v)
            elif isinstance(obj, dict):
                for v in obj.values():
                    visit(v)

        visit(self.items)
        if missing:
            raise ValueError(f"unresolved provenance refs: {sorted(missing)}")
        return self


class SceneSummary(StrictModel):
    """docs/VISUALIZATION_CONTRACTS.md §8 — the band-appropriate subset for a request."""

    band: str = Field(pattern="^(orbital|state|basin|river|local|ground)$", description="ground is served with local content until ground-band products exist")
    as_of: datetime
    basins: ContractEnvelope | None = None
    rivers: ContractEnvelope | None = None
