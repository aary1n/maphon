"""Layer A DOF table — SPEC §7 / docs/plans/layer_a_sweep_design.md §2.

RE-BASED 2026-07-18 (geometry re-base, Oxborrow-WRITTEN 2026-07-17):
the sweep's modelled build is now the Wu STO ring
(`provenance.GEOM_WU_STO_RING`); rows 1–4 re-parameterise from the
Booth torus rows {box_radius, box_height, torus_minor, torus_major} to
{box_radius, sto_outer_r, sto_inner_r, sto_height}. The Booth torus is
NOT superseded as the §5a solver-correctness anchor — it simply no
longer defines the Layer-A sweep space.

ROW INVALIDATION RECORD (invalidate, don't rename — the bore-row
discipline): the former row-2 `box_height_m` is DELETED as a noise DOF,
not renamed: in the Wu build the box internal height IS the tuning
control (the piston position) — the physical quantity did not vanish,
it BECAME row 9's `p_tune` (Q2). No noise row measures it any more.

The design doc's nine-row (θ, p) table as code, with its rung vocabulary
and TODO-trace sentinels carried as first-class objects. Rows NOT
numbers yet:

  - row 4 (sto_height_m): the ring height is a PRINT FORK {8.5, 8.6} mm
    (SM text vs Wu-2020 text + PRL Fig. 1(c) label), open question Q13
    — a `ForkTrace` whose evidence-favoured branch (8.6) is
    machine-readable but never silently selected. (2026-07-21: Q13
    RESOLVED at 8.6 mm — verbally reported caliper measurement,
    RESOLUTION_Q13, verbal rung, written confirmation pending; the
    fork object remains the record, the number enters only via the
    resolution);
  - row 5 (crystal axial offset) and row 6 (crystal centring
    eccentricity): crystal placement, open question Q9 (coordinate
    fixed with the 2026-07-16 reframe; the former "bore radius" row was
    INVALIDATED, not renamed);
  - row 9 (p_tune): the box internal height (piston position, metres).
    Mechanism now IDENTIFIED — supervisor-written 2026-07-17 and in
    print (Wu 2020 screw-suspended ceiling; PRL SM 26-mm piston on a
    brass screw); the as-operated nominal 15 mm is recorded at
    `GEOM_WU_STO_RING.box_internal_height_asoperated_m`. The travel
    [p_min, p_max] is STILL OPEN (Oxborrow asked by email 2026-07-18) —
    Q2 stays unresolved. (2026-07-21: Q2 RESOLVED — travel band
    [15, 25] mm, RESOLUTION_Q2, verbal rung, written confirmation
    pending; nominal = the as-operated 15 mm at the band's lower
    edge; the gap-depth rider remains open);
  - additionally the Phase 1b crystal permittivity (not a DOF row, but
    rider R1 makes it a solve precondition): resolved at planning grade
    via RESOLUTION_Q11 (2026-07-17); the question remains gate-tracked.

(2026-07-21 status: with RESOLUTION_Q2 + RESOLUTION_Q13 ratified at
the verbal rung alongside RESOLUTION_Q11, every solve-ready exit now
refuses on Q9 alone — still refusing, by construction.)

The Q2/Q9/Q11/Q13 gate is ENFORCED IN CODE, not convention: anything
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

from cavity.provenance import (
    CRYSTAL,
    GEOM_WU_STO_RING,
    STO,
    STO_HEIGHT_FORK,
    TOL,
)


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


@dataclass(frozen=True)
class ForkTrace(TodoTrace):
    """A TodoTrace whose answer is one of finitely many PUBLISHED
    candidates (2026-07-18, the Q13 ring-height print fork).

    Same refusal semantics as TodoTrace — never coercible to a float,
    resolved only via `SentinelResolution` — plus a machine-readable
    candidate set and evidence-favoured branch, so mock/shape tiers can
    select the favoured print EXPLICITLY and labelled, never silently.
    Defaults exist only because dataclass inheritance requires them;
    the validator refuses an empty fork.
    """

    candidates: tuple[float, ...] = ()
    evidence_favoured: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if len(self.candidates) < 2:
            raise ValueError(
                f"{self.question_id}: a ForkTrace needs >= 2 candidates"
            )
        if self.evidence_favoured not in self.candidates:
            raise ValueError(
                f"{self.question_id}: evidence_favoured must be one of "
                "the candidates"
            )


SENTINEL_Q2 = TodoTrace(
    question_id="Q2",
    description=(
        "p_tune = the box INTERNAL HEIGHT (piston position), metres — "
        "semantics fixed 2026-07-18 (geometry re-base). Mechanism now "
        "IDENTIFIED: supervisor-written 2026-07-17 and in print (Wu "
        "2020: ceiling suspended on a screw; PRL SM: 26-mm copper-disk "
        "piston on a brass screw); as-operated nominal 15 mm recorded "
        "at GEOM_WU_STO_RING.box_internal_height_asoperated_m. STILL "
        "OPEN, so the sentinel stays: the travel [p_min, p_max] (and "
        "the piston-gap depth rider) — Oxborrow asked by email "
        "2026-07-18; §7.3's per-draw root-solve depends on the travel "
        "[2026-07-21 UPDATE: travel band RESOLVED [15, 25] mm — "
        "RESOLUTION_Q2 (verbal, in-person meeting 2026-07-21; "
        "contemporaneous notes archived at "
        "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/; "
        "written confirmation pending — rides the confirmation email). "
        "The 'STILL OPEN' clause above is the pre-resolution record; "
        "the piston-step annular-gap DEPTH rider REMAINS open — it "
        "does not block the resolution.]"
    ),
    routes_to=(
        "Oxborrow (travel-band email sent 2026-07-18, reply pending; "
        "answered in person 2026-07-21 — verbal, written confirmation "
        "pending)"
    ),
)
SENTINEL_Q9 = TodoTrace(
    question_id="Q9",
    description=(
        "Phase 1b crystal placement: axial-offset nominal + band "
        "(crystal_axial_offset_m — the SIGNED axial displacement of "
        "the crystal centre from the torus equatorial plane) plus the "
        "achievable lateral centring tolerance (crystal_eccentricity_m "
        "row; distinct from TOL.machining_tol_m per the TolRanges "
        "docstring). Crystal DIMENSIONS: resolved for the Booth-context "
        "Breeze import (provenance.CRYSTAL, 3 mm x 8 mm); for the Wu "
        "build (the modelled geometry from 2026-07-18) they are a "
        "PLANNING-ASSUMPTION carrying a cross-build-transfer flag — "
        "five published Wu-side indicators lean toward a ~4 mm "
        "bore-filling crystal (GEOM_WU_STO_RING docstring; ask in the "
        "Oxborrow email queue). The Q9 ask itself is placement + "
        "centring tolerance, unchanged. Partial resolution on record: "
        "eccentricity nominal = CENTRED, per Oxborrow — "
        "supervisor-confirmed (VERBAL, in-person meeting 2026-07-16); "
        "the tolerance band is still open, so the sentinel remains "
        "unresolved. [2026-07-21 UPDATE (verbal, in-person meeting; "
        "contemporaneous notes archived at "
        "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/): "
        "test-rig placement facts recorded — the crystal is simply "
        "placed inside the ring; its length looks visually comparable "
        "to the ring height; NOT deliberately centred in this test "
        "rig; no tolerances obtained; photos exist and are archived "
        "under the same path (images/). Reconciliation, explicit: "
        "2026-07-16's eccentricity nominal = CENTRED "
        "(supervisor-confirmed) is the DESIGN nominal; 2026-07-21's "
        "'not really centred' describes the TEST-RIG realisation — "
        "compatible, and the realisation looseness is information "
        "about the centring-tolerance band (the open half of Q9), "
        "with the photos the candidate evidence for bounding it. "
        "Transfer caveat: in the actual device the crystal would be "
        "grown on a waveguide — test-rig placement bounds do not "
        "transfer; flagged, not resolved. The sentinel REMAINS "
        "unresolved; the nominal (0.0, supervisor-confirmed) is "
        "untouched.]"
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

SENTINEL_Q13 = ForkTrace(
    question_id="Q13",
    description=(
        "STO ring height PRINT FORK {8.5, 8.6} mm (geometry re-base "
        "2026-07-18): the PRL 127 SM text prints 8.5 mm; Wu 2020's text "
        "AND the PRL Fig. 1(c) photograph label print 8.6 mm. Weight of "
        "evidence favours 8.6 (two independent statements vs one) — "
        "recorded machine-readably on this sentinel and on "
        "provenance.STO_HEIGHT_FORK, but NEVER silently selected; no "
        "plain-float ring height exists in the repo until this "
        "resolves. Post-resolution the machining band (±25 µm "
        "placeholder, or a caliper-measured band riding the payload) "
        "materialises in design.materialise_dims. [2026-07-21 UPDATE: "
        "RESOLVED — the fork is decided at 8.6 mm by a verbally "
        "reported caliper measurement (RESOLUTION_Q13; verbal, "
        "in-person meeting 2026-07-21; contemporaneous notes archived "
        "at calibration/data/raw/oxborrow_meeting_notes_2026-07-21/; "
        "written confirmation pending — rides the confirmation "
        "email). The text above is the pre-resolution record; NO "
        "measured band was obtained, so the ±25 µm placeholder route "
        "applies.]"
    ),
    routes_to=(
        "Oxborrow written reply or a caliper measurement of the ring "
        "(spacer dims ride the same caliper list — 2026-07-18 rider) "
        "[2026-07-21: the caliper route fired — verbally reported, "
        "written confirmation pending]"
    ),
    candidates=STO_HEIGHT_FORK.candidates,
    evidence_favoured=STO_HEIGHT_FORK.evidence_favoured,
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


#: The nine rows of layer_a_sweep_design.md §2 (re-parameterised
#: 2026-07-18 to the Wu ring build — see the module docstring's row
#: invalidation record), in table order.
LAYER_A_DOFS: tuple[DofSpec, ...] = (
    DofSpec(
        name="box_radius_m",
        kind=DofKind.NOISE,
        nominal=GEOM_WU_STO_RING.box_inner_radius_m,
        band=_machining_band(GEOM_WU_STO_RING.box_inner_radius_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_WU_STO_RING.box_inner_radius_m "
            "(Wu 2020 Fig. 6 caption, region width 14 mm = enclosure "
            "radius). CAVEAT on the grade: the barrel is a NOMINAL "
            "28-mm end-feed pipe fitting (PRL SM), so the true bore "
            "may differ by the fitting tolerance; band: "
            "TOL.machining_tol_m ±25 µm committed placeholder (§7.4)"
        ),
    ),
    DofSpec(
        name="sto_outer_radius_m",
        kind=DofKind.NOISE,
        nominal=GEOM_WU_STO_RING.sto_outer_radius_m,
        band=_machining_band(GEOM_WU_STO_RING.sto_outer_radius_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_WU_STO_RING.sto_outer_radius_m "
            "(Wu 2020: 'O.D. = 12.0 mm', Gaskell Quartz ring); band: "
            "TOL.machining_tol_m placeholder (§7.4). [2026-07-21, "
            "Oxborrow-VERBAL, notes archived at "
            "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/: "
            "O.D. verbally reported as physically measured 12.2 mm vs "
            "the carried print 12.0 mm — 0.2 mm, 8x the machining "
            "band; unresolved two-sided discrepancy, NOT absorbed, no "
            "branch selected; queued for the confirmation email (see "
            "the GEOM_WU_STO_RING docstring)]"
        ),
    ),
    DofSpec(
        name="sto_inner_radius_m",
        kind=DofKind.NOISE,
        nominal=GEOM_WU_STO_RING.sto_inner_radius_m,
        band=_machining_band(GEOM_WU_STO_RING.sto_inner_radius_m),
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
        nominal_rung=Rung.LITERATURE_CONFIRMED,
        band_rung=Rung.PLANNING_ASSUMPTION,
        provenance=(
            "nominal: provenance.GEOM_WU_STO_RING.sto_inner_radius_m "
            "(Wu 2020: 'I.D. = 4.05 mm'; the PRL SM's '4-mm bore' is a "
            "round of this print); band: TOL.machining_tol_m "
            "placeholder (§7.4)"
        ),
    ),
    DofSpec(
        name="sto_height_m",
        kind=DofKind.NOISE,
        nominal=SENTINEL_Q13,
        band=SENTINEL_Q13,
        distribution=DistributionKind.UNDEFINED_TODO_TRACE,
        nominal_rung=Rung.TODO_TRACE,
        band_rung=Rung.TODO_TRACE,
        provenance=(
            "ring height, PRINT-FORKED {8.5, 8.6} mm (Q13; "
            "provenance.STO_HEIGHT_FORK — PRL SM text 8.5 vs Wu 2020 "
            "text + PRL Fig. 1(c) label 8.6; 8.6 evidence-favoured, "
            "never silently selected). Post-resolution band: "
            "TOL.machining_tol_m placeholder, or the caliper band "
            "riding the Q13 resolution payload"
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
            "nominal: provenance.STO.tan_delta; band: TOL [1.0, 1.4]e-4 "
            "— measured-device effective loss span, re-derived "
            "2026-07-18 at Wu's STATED coupling k = 1 (Breeze "
            "Q0≈10.7k <-> Wu Q0 = 7,200 = 2*Q_L; gap #3 closed — was "
            "[1.0, 2.3]e-4 under the assumed k = 0.2 de-load, see "
            "TolRanges.tan_delta_max); uniform = conservative baseline; "
            "the §7.4 Bayesian re-inference is the flagged upgrade, out "
            "of scope here"
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
            "TODO-trace, blocking-adjacent (Q2). SEMANTICS 2026-07-18: "
            "p_tune IS the box internal height (piston position), "
            "metres — the geometry engine now represents it directly "
            "(RING build box_height_m). Mechanism supervisor-written "
            "2026-07-17 + in print (Wu 2020 screw ceiling / PRL SM "
            "piston); as-operated nominal 15 mm recorded at "
            "GEOM_WU_STO_RING.box_internal_height_asoperated_m; travel "
            "[p_min, p_max] OPEN (email sent 2026-07-18). Root-solved "
            "per draw onto f_spin = TARGET.f_xz_measured_hz once the "
            "travel exists; sampled uniformly over it in the training "
            "design only"
        ),
    ),
)

_DOF_BY_NAME = {spec.name: spec for spec in LAYER_A_DOFS}


class DesignMode(Enum):
    """d = 8 (θ, p) baseline vs the d = 7 noise-only degraded FALLBACK
    (design doc §2/§6 — fallback, not baseline)."""

    BASELINE_D8 = "baseline-d8"
    DEGRADED_D7 = "degraded-d7"


#: The seven noise sweep dimensions (row 6 excluded by construction;
#: re-parameterised 2026-07-18 — box_height_m left the noise set, it is
#: now the p_tune control).
_NOISE_DIM_NAMES: tuple[str, ...] = (
    "box_radius_m",
    "sto_outer_radius_m",
    "sto_inner_radius_m",
    "sto_height_m",
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
#: the critical-path partition of the design doc, in code. Q13 (the
#: ring-height print fork, 2026-07-18) gates BOTH modes: sto_height_m
#: is a noise dim, so no geometry can be built in either mode without
#: a resolved height.
SOLVE_GATE_QUESTIONS: dict[DesignMode, tuple[str, ...]] = {
    DesignMode.BASELINE_D8: ("Q2", "Q9", "Q11", "Q13"),
    DesignMode.DEGRADED_D7: ("Q9", "Q11", "Q13"),
}

_SENTINELS_BY_QUESTION: dict[str, TodoTrace] = {
    "Q2": SENTINEL_Q2,
    "Q9": SENTINEL_Q9,
    "Q11": SENTINEL_Q11,
    "Q13": SENTINEL_Q13,
    "W1": SENTINEL_W1,
}

#: Required payload keys per resolvable question. Q9 carries both the
#: axial-offset row and the eccentricity centring tolerance; Q2 carries
#: the internal-height travel; Q11 the graded crystal permittivity;
#: Q13 the selected ring height plus a statement of WHICH discriminator
#: landed (written reply vs caliper) — an optional `sto_height_band_m`
#: may ride along (the RESOLUTION_Q11 extra-key precedent) for a
#: caliper-measured band.
_REQUIRED_PAYLOAD_KEYS: dict[str, tuple[str, ...]] = {
    "Q2": ("p_tune_nominal", "p_tune_min", "p_tune_max", "mechanism"),
    "Q9": (
        "crystal_axial_offset_nominal_m",
        "crystal_axial_offset_band_m",
        "centring_tolerance_m",
    ),
    "Q11": ("crystal_epsilon_r",),
    "Q13": ("sto_height_m", "selection_evidence"),
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
                    # MOCK travel about the as-operated 15 mm internal
                    # height (metres — the 2026-07-18 p_tune semantics);
                    # the fresh mock band is arbitrary, the real travel
                    # is the open Q2 ask.
                    "p_tune_nominal": (
                        GEOM_WU_STO_RING.box_internal_height_asoperated_m
                    ),
                    "p_tune_min": (
                        GEOM_WU_STO_RING.box_internal_height_asoperated_m
                        - 2.0e-3
                    ),
                    "p_tune_max": (
                        GEOM_WU_STO_RING.box_internal_height_asoperated_m
                        + 2.0e-3
                    ),
                    "mechanism": (
                        "MOCK travel band about the recorded as-operated "
                        "nominal (piston position, metres)"
                    ),
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
            SentinelResolution(
                question_id="Q13",
                payload={
                    # The ONE sanctioned pre-resolution read of the
                    # fork's machine-readable branch: mock tier only,
                    # explicit and labelled — never a silent selection.
                    # (2026-07-21: the real RESOLUTION_Q13 has since
                    # landed — same branch, verbal rung; this mock
                    # stays a mock.)
                    "sto_height_m": SENTINEL_Q13.evidence_favoured,
                    "selection_evidence": (
                        "MOCK — evidence-favoured branch, machine-read "
                        "from the Q13 fork (dry-run tier only; the real "
                        "discriminator is Oxborrow's reply or a caliper)"
                    ),
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="MOCK test double (dry-run tier only)",
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
