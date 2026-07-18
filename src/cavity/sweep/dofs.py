"""Layer A DOF table — SPEC §7 / docs/plans/layer_a_sweep_design.md §2.

The design doc's nine-row (θ, p) table as code, with its rung vocabulary
and TODO-trace sentinels carried as first-class objects. Three rows are
NOT numbers yet:

  - row 5 (crystal axial offset) and row 6 (crystal centring
    eccentricity): Phase 1b crystal placement, open question Q9.
    Reframed 2026-07-16 (Oxborrow-verbal): the recovered Booth
    geometry contains a torus central opening — often termed the
    bore — but no separately constructed or independently
    parameterised bore; its clearance is implied by the torus major
    and minor radii. The former "bore radius" row is therefore
    INVALIDATED as a physical DOF (not renamed) and replaced by the
    crystal-placement coordinate;
  - row 9 (tuning plate p_tune): no plate exists in any repo artifact,
    open question Q2;
  - additionally the Phase 1b crystal permittivity (not a DOF row, but
    rider R1 makes it a solve precondition): the repo carries only
    "εr < 5" (`provenance.CRYSTAL.epsilon_r_upper_bound`) — a bound,
    not a value; open question Q11.

The Q2/Q9/Q11 gate is ENFORCED IN CODE, not convention: anything
solve-ready (design rows, the COMSOL backend, the centre-verification
block) calls `ResolutionContext.assert_solveable(mode)` and refuses
with `UnresolvedTodoTraceError` while any required sentinel is
unresolved. Ratified numbers enter later through `SentinelResolution`
— the only path — which itself refuses TODO-trace rungs.

Every committed nominal/band below is IMPORTED from
`cavity.provenance.constants`; no fresh physics literals. The εr band
is TOL [312, 318] per the Q4 ruling (2026-07-14: TOL governs; the SPEC
§6 "316.3–318" prose is the stale artifact).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from cavity.provenance import CRYSTAL, GEOM_BOOTH_TE01D, STO, TOL


class Rung(Enum):
    """Design-doc rung vocabulary (layer_a_sweep_design.md, header)."""

    LITERATURE_CONFIRMED = "literature-confirmed"
    SUPERVISOR_CONFIRMED = "supervisor-confirmed"
    PLANNING_ASSUMPTION = "planning-assumption"
    TODO_TRACE = "todo-trace"


_QUESTION_ID_PATTERN = re.compile(r"^[QW]\d+$")


@dataclass(frozen=True)
class TodoTrace:
    """A value slot with NO traceable number behind it.

    `question_id` names the open question that must resolve before the
    slot holds a number ("Q2", "Q9", "Q11"; "W1" for the L5
    perturbation window). TodoTrace is never coercible to a float —
    arithmetic on it fails loudly, which is the point.
    """

    question_id: str
    description: str
    routes_to: str

    def __post_init__(self) -> None:
        if not _QUESTION_ID_PATTERN.match(self.question_id):
            raise ValueError(
                f"question_id {self.question_id!r} must look like 'Q2'/'W1'"
            )


SENTINEL_Q2 = TodoTrace(
    question_id="Q2",
    description=(
        "tuning plate: physical mechanism, geometric parameterisation, "
        "and travel [p_min, p_max] — no repo artifact defines it "
        "(blocking-adjacent; §7.3's per-draw root-solve depends on it)"
    ),
    routes_to="Oxborrow (findings-note asks / next touchpoint)",
)
SENTINEL_Q9 = TodoTrace(
    question_id="Q9",
    description=(
        "Phase 1b crystal placement: axial-offset nominal + band "
        "(crystal_axial_offset_m — the SIGNED axial displacement of "
        "the crystal centre from the torus equatorial plane) plus the "
        "achievable lateral centring tolerance (crystal_eccentricity_m "
        "row; distinct from TOL.machining_tol_m per the TolRanges "
        "docstring). Crystal DIMENSIONS are already resolved — "
        "provenance.CRYSTAL (Breeze 2017, 3 mm x 8 mm) — so the ask "
        "is placement + centring tolerance only. Partial resolution "
        "on record: eccentricity nominal = CENTRED, per Oxborrow — "
        "supervisor-confirmed (VERBAL, in-person meeting 2026-07-16); "
        "the tolerance band is still open, so the sentinel remains "
        "unresolved."
    ),
    routes_to="Oxborrow",
)
SENTINEL_Q11 = TodoTrace(
    question_id="Q11",
    description=(
        "Phase 1b crystal permittivity: the repo carries only 'eps_r "
        f"< {CRYSTAL.epsilon_r_upper_bound:g}' (Breeze 2017) — a bound, "
        "not a graded constant; the crystal sub-domain cannot be built "
        "on a bound"
    ),
    routes_to="literature trace first (p-terphenyl host eps_r is "
    "published); escalate to Oxborrow only if the trace fails "
    "[2026-07-17: trace executed — direct static/microwave value NOT "
    "FOUND; resolved at planning grade via anthracene analogy: "
    "cavity.sweep.resolutions.RESOLUTION_Q11]",
)

#: The L5 acceptance window (rider R2, ratified 2026-07-15): a NAMED
#: ratification item queued WITH Q9 + Q11 — due the moment both
#: resolve, not after them. Until then the centre-verification block
#: reports deltas and refuses PASS/FAIL judgment.
SENTINEL_W1 = TodoTrace(
    question_id="W1",
    description=(
        "Phase 1b weak-perturbation acceptance window for the sweep "
        "centre (SPEC §5b 'verify, don't assume'): no artifact commits "
        "a numeric window; deltas are reported unjudged until this "
        "ratifies"
    ),
    routes_to="ratification pass, queued with Q9 + Q11",
)


class DofKind(Enum):
    NOISE = "noise"
    CONTROL = "control"
    #: Row 6: physically real noise, but NOT a sweep dimension — it
    #: breaks m = 0 and is handled by the §7-expanded §7.4 decision
    #: ladder (first-order estimate -> bounded 3-D -> drop).
    NOISE_NOT_A_SWEEP_DIM = "noise-not-a-sweep-dim"


class DistributionKind(Enum):
    #: Truncated Gaussian, ±3σ = band, truncated at the band edges
    #: (§7.4 process-centred reading); the uniform variant is reported
    #: alongside ("the gap is informative").
    TRUNC_GAUSSIAN_3SIGMA = "trunc-gaussian-3sigma"
    UNIFORM = "uniform"
    #: εr sensitivity variant: triangular with peak at nominal.
    TRIANGULAR_NOMINAL_PEAK = "triangular-nominal-peak"
    #: Row 9: root-solved per draw at evaluation time; sampled
    #: uniformly over its travel in the TRAINING design only (§7.5
    #: Sobol over (θ, p)).
    CONTROL_ROOT_SOLVED = "control-root-solved"
    #: No distribution assignable while the row is TODO-trace.
    UNDEFINED_TODO_TRACE = "undefined-todo-trace"


@dataclass(frozen=True)
class DofSpec:
    """One row of the design doc §2 DOF table."""

    name: str
    kind: DofKind
    nominal: float | TodoTrace
    band: tuple[float, float] | TodoTrace
    distribution: DistributionKind
    nominal_rung: Rung
    band_rung: Rung
    provenance: str

    def __post_init__(self) -> None:
        if isinstance(self.nominal, TodoTrace) and (
            self.nominal_rung is not Rung.TODO_TRACE
        ):
            raise ValueError(
                f"{self.name}: TodoTrace nominal must carry the "
                "TODO_TRACE rung"
            )
        if isinstance(self.band, TodoTrace) and (
            self.band_rung is not Rung.TODO_TRACE
        ):
            raise ValueError(
                f"{self.name}: TodoTrace band must carry the TODO_TRACE rung"
            )
        if isinstance(self.band, tuple):
            lo, hi = self.band
            if not lo < hi:
                raise ValueError(f"{self.name}: band must have lo < hi")
            if isinstance(self.nominal, float) and not (
                lo <= self.nominal <= hi
            ):
                raise ValueError(f"{self.name}: nominal outside band")

    @property
    def is_resolved(self) -> bool:
        return not (
            isinstance(self.nominal, TodoTrace)
            or isinstance(self.band, TodoTrace)
        )

    @property
    def sentinel(self) -> TodoTrace | None:
        """The TODO-trace blocking this row, if any."""
        if isinstance(self.nominal, TodoTrace):
            return self.nominal
        if isinstance(self.band, TodoTrace):
            return self.band
        return None


def _machining_band(nominal_m: float) -> tuple[float, float]:
    """nominal ± TOL.machining_tol_m — the committed ±25 µm PLACEHOLDER
    (SPEC §7-expanded §7.4; workshop confirmation is open ACTION 7.10.1
    / design-doc Q10; the table re-issues on receipt)."""
    return (nominal_m - TOL.machining_tol_m, nominal_m + TOL.machining_tol_m)


#: The nine rows of layer_a_sweep_design.md §2, in table order.
LAYER_A_DOFS: tuple[DofSpec, ...] = (
    DofSpec(
        name="box_radius_m",
        kind=DofKind.NOISE,
        nominal=GEOM_BOOTH_TE01D.box_radius_m,
        band=_machining_band(GEOM_BOOTH_TE01D.box_radius_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_BOOTH_TE01D.box_radius_m (Booth "
            "App. A r-extent, refs/booth_geometry_recovery.md); band: "
            "TOL.machining_tol_m ±25 µm committed placeholder (§7.4)"
        ),
    ),
    DofSpec(
        name="box_height_m",
        kind=DofKind.NOISE,
        nominal=GEOM_BOOTH_TE01D.box_height_m,
        band=_machining_band(GEOM_BOOTH_TE01D.box_height_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_BOOTH_TE01D.box_height_m; band: "
            "TOL.machining_tol_m placeholder (§7.4)"
        ),
    ),
    DofSpec(
        name="torus_minor_radius_m",
        kind=DofKind.NOISE,
        nominal=GEOM_BOOTH_TE01D.torus_minor_radius_m,
        band=_machining_band(GEOM_BOOTH_TE01D.torus_minor_radius_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_BOOTH_TE01D.torus_minor_radius_m "
            "(ratio-exact x/5 = 2.456 mm); band: TOL.machining_tol_m "
            "placeholder. Stiff f-lever ≈ -0.35 MHz/µm (§2 printed-2.46 "
            "sensitivity solve) — dominates the tuning-feasibility metric"
        ),
    ),
    DofSpec(
        name="torus_major_radius_m",
        kind=DofKind.NOISE,
        nominal=GEOM_BOOTH_TE01D.torus_major_radius_m,
        band=_machining_band(GEOM_BOOTH_TE01D.torus_major_radius_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.SUPERVISOR_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_BOOTH_TE01D.torus_major_radius_m "
            "(x/2 = 6.14 mm, pinned by the supervisor .mph — the one "
            "untabulated DOF); band: TOL.machining_tol_m placeholder"
        ),
    ),
    DofSpec(
        name="crystal_axial_offset_m",
        kind=DofKind.NOISE,
        nominal=SENTINEL_Q9,
        band=SENTINEL_Q9,
        distribution=DistributionKind.UNDEFINED_TODO_TRACE,
        nominal_rung=Rung.TODO_TRACE,
        band_rung=Rung.TODO_TRACE,
        provenance=(
            "signed axial displacement of the crystal centre from the "
            "torus equatorial plane (coordinate fixed with the "
            "2026-07-16 Q9 reframe; supersedes the retired 'bore "
            "radius' row — the torus central opening is not an "
            "independently parameterised geometry primitive, its "
            "clearance being implied by the torus major/minor radii). "
            "No nominal or band exists in any repo artifact (Q9); "
            "crystal dimensions themselves are resolved via "
            "provenance.CRYSTAL (Breeze 2017, 3 mm x 8 mm); trunc. "
            "Gaussian once a band exists"
        ),
    ),
    DofSpec(
        name="crystal_eccentricity_m",
        kind=DofKind.NOISE_NOT_A_SWEEP_DIM,
        nominal=0.0,  # CENTRED (design doc §2 row 6)
        band=SENTINEL_Q9,
        distribution=DistributionKind.UNDEFINED_TODO_TRACE,
        nominal_rung=Rung.SUPERVISOR_CONFIRMED,
        band_rung=Rung.TODO_TRACE,
        provenance=(
            "lateral (radial) miscentring of the crystal within the "
            "torus central opening. Nominal 0 = CENTRED — Oxborrow "
            "(verbal, in-person meeting 2026-07-16); rung upgraded "
            "from planning-assumption with the numeric nominal "
            "unchanged. Achievable centring tolerance band still "
            "unknown (Q9) — DISTINCT from TOL.machining_tol_m per the "
            "TolRanges docstring, never folded in; breaks m = 0, "
            "excluded from the axisymmetric sweep dims; §7.4 decision "
            "ladder: first-order perturbation estimate BEFORE the main "
            "sweep -> bounded 3-D -> drop"
        ),
    ),
    DofSpec(
        name="epsilon_r",
        kind=DofKind.NOISE,
        nominal=STO.epsilon_r_real,
        band=(TOL.epsilon_r_min, TOL.epsilon_r_max),
        distribution=DistributionKind.UNIFORM,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.LITERATURE_CONFIRMED,
        provenance=(
            "nominal: provenance.STO.epsilon_r_real (Booth 316.3); band: "
            "TOL [312, 318] — literature-anchored endpoints (Wu 312 / "
            "Booth 316.3 / Breeze 318, TARGETS.*.epsilon_r_real); "
            "GOVERNS per the Q4 ruling 2026-07-14 (SPEC §6 '316.3-318' "
            "prose is the stale artifact). Distribution shape uniform = "
            "planning-assumption; triangular-toward-nominal is the "
            "sensitivity variant"
        ),
    ),
    DofSpec(
        name="tan_delta",
        kind=DofKind.NOISE,
        nominal=STO.tan_delta,
        band=(TOL.tan_delta_min, TOL.tan_delta_max),
        distribution=DistributionKind.UNIFORM,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.LITERATURE_CONFIRMED,
        provenance=(
            "nominal: provenance.STO.tan_delta; band: TOL [1.0, 2.3]e-4 "
            "— measured-device effective loss span (Breeze Q0≈10.7k <-> "
            "Wu Q0≈4.3k, SPEC §6); uniform = conservative baseline; the "
            "§7.4 Bayesian re-inference is the flagged upgrade, out of "
            "scope here"
        ),
    ),
    DofSpec(
        name="p_tune",
        kind=DofKind.CONTROL,
        nominal=SENTINEL_Q2,
        band=SENTINEL_Q2,
        distribution=DistributionKind.CONTROL_ROOT_SOLVED,
        nominal_rung=Rung.TODO_TRACE,
        band_rung=Rung.TODO_TRACE,
        provenance=(
            "TODO-trace, blocking-adjacent (Q2): no plate exists in the "
            "geometry engine, the SPEC geometry, or any repo artifact; "
            "root-solved per draw onto f_spin = TARGET.f_xz_measured_hz "
            "once defined; sampled uniformly over its travel in the "
            "training design only"
        ),
    ),
)

_DOF_BY_NAME = {spec.name: spec for spec in LAYER_A_DOFS}


class DesignMode(Enum):
    """d = 8 (θ, p) baseline vs the d = 7 noise-only degraded FALLBACK
    (design doc §2/§6 — fallback, not baseline)."""

    BASELINE_D8 = "baseline-d8"
    DEGRADED_D7 = "degraded-d7"


#: The seven noise sweep dimensions (row 6 excluded by construction).
_NOISE_DIM_NAMES: tuple[str, ...] = (
    "box_radius_m",
    "box_height_m",
    "torus_minor_radius_m",
    "torus_major_radius_m",
    "crystal_axial_offset_m",
    "epsilon_r",
    "tan_delta",
)


def sweep_dimension_names(mode: DesignMode) -> tuple[str, ...]:
    """Ordered sweep dimensions for the mode (8 or 7)."""
    if mode is DesignMode.BASELINE_D8:
        return _NOISE_DIM_NAMES + ("p_tune",)
    return _NOISE_DIM_NAMES


#: Which open questions gate SOLVE-READY work per mode. Note the d = 7
#: fallback relieves only Q2: crystal axial offset (row 5) is one of the seven
#: noise dims, and rider R1 (admissible rows come from Phase 1b
#: geometry) requires the crystal sub-domain (Q11) regardless — this is
#: the critical-path partition of the design doc, in code.
SOLVE_GATE_QUESTIONS: dict[DesignMode, tuple[str, ...]] = {
    DesignMode.BASELINE_D8: ("Q2", "Q9", "Q11"),
    DesignMode.DEGRADED_D7: ("Q9", "Q11"),
}

_SENTINELS_BY_QUESTION: dict[str, TodoTrace] = {
    "Q2": SENTINEL_Q2,
    "Q9": SENTINEL_Q9,
    "Q11": SENTINEL_Q11,
    "W1": SENTINEL_W1,
}

#: Required payload keys per resolvable question. Q9 carries both the
#: axial-offset row and the eccentricity centring tolerance; Q2 carries
#: the plate travel; Q11 the graded crystal permittivity.
_REQUIRED_PAYLOAD_KEYS: dict[str, tuple[str, ...]] = {
    "Q2": ("p_tune_nominal", "p_tune_min", "p_tune_max", "mechanism"),
    "Q9": (
        "crystal_axial_offset_nominal_m",
        "crystal_axial_offset_band_m",
        "centring_tolerance_m",
    ),
    "Q11": ("crystal_epsilon_r",),
}


class UnresolvedTodoTraceError(RuntimeError):
    """Solve-ready work refused: named sentinels are still TODO-trace."""

    def __init__(self, question_ids: tuple[str, ...], what: str) -> None:
        self.question_ids = tuple(question_ids)
        details = "; ".join(
            f"{qid}: {_SENTINELS_BY_QUESTION[qid].description}"
            + f" [routes to: {_SENTINELS_BY_QUESTION[qid].routes_to}]"
            for qid in self.question_ids
            if qid in _SENTINELS_BY_QUESTION
        )
        super().__init__(
            f"{what} refused — unresolved TODO-trace sentinel(s) "
            f"{list(self.question_ids)} (design doc critical-path "
            f"partition: zero training solves until these resolve). "
            f"{details}"
        )


class MockResolutionError(RuntimeError):
    """Mock resolutions can exercise pipeline SHAPE only — anything
    solve-ready refuses them unconditionally."""


@dataclass(frozen=True)
class SentinelResolution:
    """A ratified (or mock) answer to one open question.

    The ONLY path by which Q2/Q9/Q11 numbers enter the machinery.
    Refuses `rung=TODO_TRACE` (a resolution must resolve) and refuses
    unknown questions or missing payload keys. `mock=True` marks a
    test double: it unlocks pipeline-shape exercise against the mock
    backend and is refused by every solve-ready exit.
    """

    question_id: str
    payload: dict
    rung: Rung
    provenance: str
    mock: bool = False

    def __post_init__(self) -> None:
        if self.question_id not in _REQUIRED_PAYLOAD_KEYS:
            raise ValueError(
                f"unknown/unresolvable question {self.question_id!r}; "
                f"resolvable: {sorted(_REQUIRED_PAYLOAD_KEYS)}"
            )
        if self.rung is Rung.TODO_TRACE:
            raise ValueError(
                f"{self.question_id}: a resolution cannot carry the "
                "TODO_TRACE rung — that is not a resolution"
            )
        if self.mock and self.rung is not Rung.PLANNING_ASSUMPTION:
            raise ValueError(
                "mock resolutions must carry PLANNING_ASSUMPTION — a "
                "mock claiming a confirmed rung is a provenance lie"
            )
        missing = [
            k
            for k in _REQUIRED_PAYLOAD_KEYS[self.question_id]
            if k not in self.payload
        ]
        if missing:
            raise ValueError(
                f"{self.question_id}: resolution payload missing keys "
                f"{missing}"
            )
        if not self.provenance.strip():
            raise ValueError(
                f"{self.question_id}: resolution must state provenance"
            )


@dataclass(frozen=True)
class ResolutionContext:
    """The set of resolved questions available to the pipeline."""

    resolutions: tuple[SentinelResolution, ...] = field(default=())

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for res in self.resolutions:
            if res.question_id in seen:
                raise ValueError(
                    f"duplicate resolution for {res.question_id}"
                )
            seen.add(res.question_id)

    def get(self, question_id: str) -> SentinelResolution | None:
        for res in self.resolutions:
            if res.question_id == question_id:
                return res
        return None

    @property
    def any_mock(self) -> bool:
        return any(res.mock for res in self.resolutions)

    def unresolved(self, mode: DesignMode) -> tuple[str, ...]:
        """Question IDs required by `mode` and not resolved."""
        return tuple(
            qid
            for qid in SOLVE_GATE_QUESTIONS[mode]
            if self.get(qid) is None
        )

    def assert_solveable(self, mode: DesignMode, what: str) -> None:
        """The Q2/Q9/Q11 gate: raise unless every question `mode`
        requires is resolved by a NON-MOCK resolution."""
        missing = self.unresolved(mode)
        if missing:
            raise UnresolvedTodoTraceError(missing, what)
        mocked = tuple(
            qid
            for qid in SOLVE_GATE_QUESTIONS[mode]
            if self.get(qid) is not None and self.get(qid).mock
        )
        if mocked:
            raise MockResolutionError(
                f"{what} refused — question(s) {list(mocked)} are "
                "resolved by MOCK test doubles; mock resolutions can "
                "never become solve-ready"
            )


def mock_resolutions() -> ResolutionContext:
    """Test-double context for pipeline-SHAPE exercise (dry-run tier).

    Values are arbitrary-but-plausible and carry mock=True end to end;
    every solve-ready exit refuses them. The axial-offset mock is
    chosen FRESH for the 2026-07-16 crystal-placement coordinate
    (axially centred, machining-scale band) — the retired bore-radius
    mock does NOT carry over; the crystal-εr mock respects the
    published bound (both so shape tests exercise realistic branches,
    not because these numbers mean anything).
    """
    return ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q2",
                payload={
                    "p_tune_nominal": 0.5,
                    "p_tune_min": 0.0,
                    "p_tune_max": 1.0,
                    "mechanism": "MOCK normalised plate coordinate",
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="MOCK test double (dry-run tier only)",
                mock=True,
            ),
            SentinelResolution(
                question_id="Q9",
                payload={
                    # MOCK values chosen fresh for the axial-offset
                    # coordinate (centred, machining-scale slack); the
                    # retired radius-derived mock does not carry over.
                    "crystal_axial_offset_nominal_m": 0.0,
                    "crystal_axial_offset_band_m": (
                        -2.0 * TOL.machining_tol_m,
                        +2.0 * TOL.machining_tol_m,
                    ),
                    "centring_tolerance_m": 2.0 * TOL.machining_tol_m,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="MOCK test double (dry-run tier only)",
                mock=True,
            ),
            SentinelResolution(
                question_id="Q11",
                payload={"crystal_epsilon_r": 3.0},
                rung=Rung.PLANNING_ASSUMPTION,
                provenance=(
                    "MOCK test double (dry-run tier only; below the "
                    "published 'eps_r < 5' bound by construction)"
                ),
                mock=True,
            ),
        )
    )


def dof_by_name(name: str) -> DofSpec:
    try:
        return _DOF_BY_NAME[name]
    except KeyError:
        raise KeyError(
            f"unknown DOF {name!r}; table rows: {sorted(_DOF_BY_NAME)}"
        ) from None
