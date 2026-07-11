"""SPEC §5 gate acceptance windows + rationale — decisions, not physics.

`constants.py` holds graded physics: numbers whose provenance traces to
the literature (refs/pentacene_maser_parameter_provenance.md, SPEC §6).
This module holds ACCEPTANCE DECISIONS: how close the forward model
must land to count as reproducing an anchor. Decisions are revisable
without touching graded provenance, and each one carries its own
rationale string so the writeup can defend it.

Single-source rule respected: every anchor value below is REFERENCED
from `cavity.provenance.constants` (TARGETS, TARGET, EXTRACTION_TOL),
never re-typed. Only the acceptance knobs themselves (window widths,
order-of-magnitude bounds) originate here.

The six §5 rows are carried VERBATIM from the SPEC table (check /
target / source columns) so the gate report is auditable against the
SPEC without a lookup.
"""

from __future__ import annotations

from dataclasses import dataclass

from cavity.provenance.constants import (
    BOOTH_IMPLIED_F_M,
    BOOTH_IMPLIED_V_MODE_M3,
    EXTRACTION_TOL,
    TARGET,
    TARGETS,
)

# --- acceptance knobs (decisions original to this module) -------------
#
# Each knob's defence lives in the tolerance_rationale of the check spec
# that uses it; the values here are deliberately provisional where the
# rationale says so.

F_ROW_HALF_WIDTH_HZ: float = 0.5e6
"""±0.5 MHz about 1.45 GHz — half a unit in the fourth significant
figure, i.e. round-to-4-s.f. must give 1.450 GHz."""

BOOTH_TWO_POINT_REL_TOL: float = 0.01
"""±1% on the Booth Table 8 anchors (Q, V_mode, implied F_m).
UNCHANGED by the 2026-07-11 V_mode re-base: the re-base re-derived the
V window's BASIS (the anchor it centres on — BOOTH_IMPLIED_V_MODE_M3
instead of the 225/360-corrupted print), never this tolerance (§11
item 8's reserved path). Provisional until live converged solves
calibrate the actual mesh scatter."""

CONFINEMENT_ENDPOINT_Q_LO: float = 9_000.0
CONFINEMENT_ENDPOINT_Q_HI: float = 10_500.0
"""Q window at the tight-confinement endpoint of the §5 trend row:
brackets 'toward ~10,000' across the §6 tan_delta band (ceiling
1/tan_delta = 10,000 at 1.0e-4, 9,091 at 1.1e-4) with room for
residual wall loss below and the 1.0e-4 ceiling above."""

CONFINEMENT_ENDPOINT_V_MODE_MAX_M3: float = 0.22e-6
"""The trend must actually reach Breeze's confinement point: the
tightest sampled V_mode must be within 10% of 0.2 cm^3."""

CONFINEMENT_MIN_POINTS: int = 3
"""SPEC §5: 'The gap must reproduce as a continuous confinement trend,
not two unrelated points.' Two points cannot show a trend."""

F_M_ORDER_LO: float = 1.0e7
F_M_ORDER_HI: float = 1.0e8
"""'order 10^7' read as floor(log10(F_m)) == 7."""


@dataclass(frozen=True)
class GateWindow:
    """Closed acceptance interval on the measured quantity.

    `lo` / `hi` may each be None for one-sided windows. Margin
    conventions (implemented in `validation.gate`):
      - two-sided: distance to nearest edge over the half-width
        (1.0 at centre, 0.0 at an edge, negative outside);
      - upper-only (residual checks, lo=None): headroom fraction
        (hi - measured) / hi;
      - lower-only: no numeric margin (structural checks).
    """

    lo: float | None
    hi: float | None


@dataclass(frozen=True)
class GateCheckSpec:
    """One typed check inside a §5 row."""

    check_id: str
    description: str
    window: GateWindow
    target_value: float | None
    provenance: str
    tolerance_rationale: str


@dataclass(frozen=True)
class GateRowSpec:
    """One row of the SPEC §5 table, verbatim, plus its typed checks.

    `requires_comsol`: True for every row — the real Phase-1 gate
    judges COMSOL solves; CI exercises the identical judgment logic on
    synthetic/cached payloads (SPEC §1).

    `blocked_on`: why the row's live payload does not exist yet (None
    when a live input path is already available today).
    """

    row_id: str
    check_text: str
    target_text: str
    source_text: str
    checks: tuple[GateCheckSpec, ...]
    requires_comsol: bool = True
    blocked_on: str | None = None


# SPEC §11 gap #1 (Booth's dielectric cross-section unpinned) was the
# blocker on the f / Booth two-point / wall-loss / F_m rows. CLOSED
# 2026-07-10 by document recovery (refs/booth_geometry_recovery.md):
# the recovered torus is single-sourced as provenance.GEOM_BOOTH_TE01D
# and the rows have a live input path (LiveComsolProvider), so their
# blocked_on is now None. Only the confinement-trend row stays blocked
# (it needs the §7 parametric sweep, a Breeze-side scope decision).

_PEC_LOSSY_RATIONALE = (
    "Same constant the §8 guard uses: "
    "EXTRACTION_TOL.q_pec_lossy_rel_tol — one constant, no fork "
    "(assert_pec_lossy_q_consistency is invoked alongside this check "
    "as the convention guard). Mesh-limited: loose enough that "
    "converged solves pass, tight enough that an inverted "
    "eigenfrequency sign convention or a missing 2*pi*r Jacobian "
    "fails."
)

_F_ROW_RATIONALE = (
    "'>=4 s.f.' read literally: rounding the extracted f to four "
    "significant figures must give 1.450 GHz, i.e. "
    "|f - 1.45 GHz| <= 0.5 MHz (half a unit in the fourth "
    "significant figure). Scope clauses: (a) 4-s.f. CONVERGENCE "
    "STABILITY is asserted upstream by the §2 mesh-convergence study, "
    "not re-checked here — the gate presupposes a converged f; "
    "(b) the window is meaningful only at the standardised eps_r of "
    "the target being reproduced: it is far tighter than the ~14 MHz "
    "shift the §6 eps_r spread (316.3-318) induces, so this row is a "
    "convergence-at-fixed-material check, not a material-uncertainty "
    "tolerance."
)

_BOOTH_RATIONALE = (
    "±1% (BOOTH_TWO_POINT_REL_TOL) about the Booth Table 8 printed "
    "value: printed-value half-ULP is far tighter (0.007% on Q, 0.12% "
    "on V_mode) than plausible mesh-convergence scatter, while 1% "
    "stays an order below the 30% Breeze/Booth confinement gap the "
    "row must discriminate. Provisional until the first live "
    "converged solve calibrates the actual scatter. V_mode is judged "
    "on the GLOBAL-max variant (the standard definition); the local "
    "variant is recorded in inputs for diagnosis (SPEC §3 requires "
    "both)."
)

_BOOTH_V_RATIONALE = (
    "±1% (BOOTH_TWO_POINT_REL_TOL — UNCHANGED) about "
    "BOOTH_IMPLIED_V_MODE_M3, the Table 8 print corrected for the "
    "225/360 partial-revolution factor read from Booth's own results "
    "tree (SPEC §5a finding 2026-07-11; "
    "BOOTH_TABLE8_REVOLUTION_FACTOR carries the full rung, incl. "
    "written-confirmation-PENDING). This is §11 item 8's reserved "
    "path — the window's BASIS re-derived from her actual definition, "
    "never a tolerance widening. V_mode is judged on the GLOBAL-max "
    "variant (the standard definition); the local variant is recorded "
    "in inputs for diagnosis (SPEC §3 requires both)."
)

_CONFINEMENT_RATIONALE = (
    "Endpoint window [9,000, 10,500] brackets 'toward ~10,000' across "
    "the §6 tan_delta band (dielectric ceiling 1/tan_delta = 10,000 "
    "at 1.0e-4, 9,091 at 1.1e-4), allowing residual wall loss below "
    "and the 1.0e-4 ceiling above. The trend must be strictly "
    "monotone (Q rises as V_mode tightens) over >= 3 points and must "
    "reach V_mode <= 0.22 cm^3*1e-6 (within 10% of Breeze's 0.2 cm^3) "
    "— SPEC §5 demands a continuous trend, not two unrelated points. "
    "Provisional pending the first live sweep."
)

_WALL_LOSS_RATIONALE = (
    "Windows referenced from TARGETS.q_diel_lo/hi and "
    "TARGETS.wall_loss_fraction_lo/hi — the SPEC §4 acceptance "
    "intervals derived from Booth Table 8 and the tan_delta ceiling; "
    "not re-typed here. A below_resolution decomposition fails the "
    "wall-fraction check: at the Booth regime the split must be "
    "resolved (the cancellation guard is for the Breeze end, not "
    "here)."
)

_F_M_RATIONALE = (
    "±1% (BOOTH_TWO_POINT_REL_TOL) consistency against "
    "BOOTH_IMPLIED_F_M — the §3 formula at Booth's printed Q, the "
    "corrected BOOTH_IMPLIED_V_MODE_M3 and f = 1.45 GHz (~7.16e6, "
    "order 10^6.85). Re-scoped 2026-07-11 (SPEC §5a finding): the old "
    "[1e7, 1e8) order window at the Booth point was satisfiable ONLY "
    "through the x1.6-inflated V_mode print (0.409 => 1.15e7) — with "
    "the true V no faithful model can land order 10^7 there — and an "
    "order-of-magnitude window becoming a 1% consistency check is a "
    "TIGHTENING, not a loosening. The order-10^7 physics window moves "
    "to the confinement endpoint where its Breeze anchor lives "
    "(confinement_trend/f_m_order — DEFERRED with that row, not "
    "deleted, not weakened). Judged on the global-max V_mode variant "
    "(the conservative, smaller-F_m choice); the formula's own "
    "3.3-3.6e7 self-consistency anchor on Breeze inputs is gated "
    "separately by F_M_BENCHMARK in the §3 extraction tests."
)

_F_M_CONFINEMENT_RATIONALE = (
    "'order 10^7' read as floor(log10(F_m)) == 7, i.e. F_m in "
    "[1e7, 1e8] — judged at the tightest sampled confinement point, "
    "where the source anchor actually lives (Breeze Table 1: "
    "F_m = 3.6e7 AT V = 0.2 cm^3, not at Booth's 0.65 cm^3 point). "
    "Re-scoped here from the Booth point 2026-07-11 (SPEC §5a "
    "finding; see f_m/booth_consistency): the window itself is "
    "carried VERBATIM. Deferred with the row until the §7 sweep "
    "exists."
)

GATE_ROWS: tuple[GateRowSpec, ...] = (
    GateRowSpec(
        row_id="analytic_benchmark",
        check_text="Analytic benchmark passes",
        target_text="empty-cavity TE011 < 0.1% error",
        source_text="§8, build FIRST",
        blocked_on=None,
        checks=(
            GateCheckSpec(
                check_id="analytic_benchmark/te011",
                description=(
                    "min relative error of the solved empty-cavity "
                    "spectrum against the closed-form TE011 frequency"
                ),
                window=GateWindow(
                    lo=None, hi=TARGETS.empty_cavity_rel_error_max
                ),
                target_value=0.0,
                provenance=(
                    "SPEC §8 (Oxborrow 2007, IEEE Trans. MTT 55, "
                    "1209); TARGETS.empty_cavity_rel_error_max"
                ),
                tolerance_rationale=(
                    "0.1% is the SPEC §8 mesh-limited target; the "
                    "bound is referenced from "
                    "TARGETS.empty_cavity_rel_error_max (single "
                    "source), the same constant the live COMSOL "
                    "anchor test asserts."
                ),
            ),
            GateCheckSpec(
                check_id="analytic_benchmark/pec_lossy_q",
                description=(
                    "closed-form residual |Q * p_e * tan_delta - 1| "
                    "on a PEC-walled lossy-dielectric solve "
                    "(SPEC §8: Q = 1/(p_e * tan_delta))"
                ),
                window=GateWindow(
                    lo=None, hi=EXTRACTION_TOL.q_pec_lossy_rel_tol
                ),
                target_value=0.0,
                provenance=(
                    "SPEC §8 Q-from-tan_delta closed check; "
                    "EXTRACTION_TOL.q_pec_lossy_rel_tol; guard: "
                    "cavity.extraction.assert_pec_lossy_q_consistency"
                ),
                tolerance_rationale=_PEC_LOSSY_RATIONALE,
            ),
        ),
    ),
    GateRowSpec(
        row_id="f",
        check_text="f",
        target_text="1.45 GHz, ≥4 s.f.",
        source_text="Booth, Breeze",
        blocked_on=None,
        checks=(
            GateCheckSpec(
                check_id="f/f_at_booth_geometry",
                description=(
                    "extracted f of the walls-on solve at Booth "
                    "geometry (eps_r = 316.3)"
                ),
                window=GateWindow(
                    lo=TARGET.f_design_hz - F_ROW_HALF_WIDTH_HZ,
                    hi=TARGET.f_design_hz + F_ROW_HALF_WIDTH_HZ,
                ),
                target_value=TARGET.f_design_hz,
                provenance=(
                    "TARGET.f_design_hz (Booth, Breeze design value; "
                    "SPEC §5)"
                ),
                tolerance_rationale=_F_ROW_RATIONALE,
            ),
        ),
    ),
    GateRowSpec(
        row_id="booth_two_point",
        check_text="Booth two-point",
        target_text=(
            "Q ≈ 6,980, V_mode ≈ 0.409 cm³ at Booth geometry "
            "(walls on)"
        ),
        source_text="Booth Table 8 + App. A",
        blocked_on=None,
        checks=(
            GateCheckSpec(
                check_id="booth_two_point/q",
                description="extracted Q, Impedance-BC walls",
                window=GateWindow(
                    lo=TARGETS.booth.q_factor
                    * (1.0 - BOOTH_TWO_POINT_REL_TOL),
                    hi=TARGETS.booth.q_factor
                    * (1.0 + BOOTH_TWO_POINT_REL_TOL),
                ),
                target_value=TARGETS.booth.q_factor,
                provenance=(
                    "TARGETS.booth (Booth 2018 Table 8 + Appendix A; "
                    "eps_r = 316.3)"
                ),
                tolerance_rationale=_BOOTH_RATIONALE,
            ),
            GateCheckSpec(
                check_id="booth_two_point/v_mode",
                description=(
                    "extracted V_mode (global-max variant), m^3"
                ),
                window=GateWindow(
                    lo=BOOTH_IMPLIED_V_MODE_M3
                    * (1.0 - BOOTH_TWO_POINT_REL_TOL),
                    hi=BOOTH_IMPLIED_V_MODE_M3
                    * (1.0 + BOOTH_TWO_POINT_REL_TOL),
                ),
                target_value=BOOTH_IMPLIED_V_MODE_M3,
                provenance=(
                    "BOOTH_IMPLIED_V_MODE_M3 (Booth 2018 Table 8 print "
                    "0.409 cm^3 corrected x360/225 — SPEC §5a finding "
                    "2026-07-11, BOOTH_TABLE8_REVOLUTION_FACTOR; "
                    "eps_r = 316.3)"
                ),
                tolerance_rationale=_BOOTH_V_RATIONALE,
            ),
        ),
    ),
    GateRowSpec(
        row_id="confinement_trend",
        check_text="Confinement trend",
        target_text=(
            "tightening toward V_mode ≈ 0.2 raises Q toward ~10,000"
        ),
        source_text="Breeze Table 1",
        blocked_on=(
            "requires the §7 parametric confinement sweep — "
            "deliberately not implemented in this pass (SPEC §5 "
            "gate scope)."
        ),
        checks=(
            GateCheckSpec(
                check_id="confinement_trend/monotonic",
                description=(
                    "min consecutive Q increment as V_mode tightens "
                    "(strictly > 0 over >= "
                    f"{CONFINEMENT_MIN_POINTS} points)"
                ),
                window=GateWindow(lo=0.0, hi=None),
                target_value=None,
                provenance="SPEC §5 confinement-trend clause; §6",
                tolerance_rationale=_CONFINEMENT_RATIONALE,
            ),
            GateCheckSpec(
                check_id="confinement_trend/endpoint_q",
                description=(
                    "Q at the tightest sampled V_mode (which must "
                    "reach <= 0.22e-6 m^3)"
                ),
                window=GateWindow(
                    lo=CONFINEMENT_ENDPOINT_Q_LO,
                    hi=CONFINEMENT_ENDPOINT_Q_HI,
                ),
                target_value=TARGETS.breeze.q_factor,
                provenance=(
                    "TARGETS.breeze (Breeze 2017 Table 1, STO row; "
                    "eps_r = 318)"
                ),
                tolerance_rationale=_CONFINEMENT_RATIONALE,
            ),
            GateCheckSpec(
                check_id="confinement_trend/f_m_order",
                description=(
                    "F_m (§3 formula) at the tightest sampled "
                    "confinement point"
                ),
                window=GateWindow(lo=F_M_ORDER_LO, hi=F_M_ORDER_HI),
                target_value=TARGETS.breeze.f_m,
                provenance=(
                    "TARGETS.breeze.f_m (Breeze 2017 Table 1, STO "
                    "row: F_m = 3.6e7 at V = 0.2 cm^3); re-scoped "
                    "here from the Booth point per the SPEC §5a "
                    "finding 2026-07-11"
                ),
                tolerance_rationale=_F_M_CONFINEMENT_RATIONALE,
            ),
        ),
    ),
    GateRowSpec(
        row_id="wall_loss_split",
        check_text="Wall-loss split",
        target_text="Q_diel ≈ 9–10k, wall fraction ~23–27%",
        source_text="§4",
        blocked_on=None,
        checks=(
            GateCheckSpec(
                check_id="wall_loss_split/q_diel",
                description="Q_diel from the §4 PEC solve",
                window=GateWindow(
                    lo=TARGETS.q_diel_lo, hi=TARGETS.q_diel_hi
                ),
                target_value=None,
                provenance=(
                    "TARGETS.q_diel_lo/hi (SPEC §4; Booth Table 8 + "
                    "tan_delta ceiling)"
                ),
                tolerance_rationale=_WALL_LOSS_RATIONALE,
            ),
            GateCheckSpec(
                check_id="wall_loss_split/wall_fraction",
                description=(
                    "wall-loss fraction Q_total/Q_wall from the §4 "
                    "two-solve decomposition"
                ),
                window=GateWindow(
                    lo=TARGETS.wall_loss_fraction_lo,
                    hi=TARGETS.wall_loss_fraction_hi,
                ),
                target_value=None,
                provenance=(
                    "TARGETS.wall_loss_fraction_lo/hi (SPEC §4; "
                    "Booth Table 8)"
                ),
                tolerance_rationale=_WALL_LOSS_RATIONALE,
            ),
        ),
    ),
    GateRowSpec(
        row_id="f_m",
        check_text="F_m",
        target_text=(
            "±1% consistency vs BOOTH_IMPLIED_F_M at the Booth point "
            "(order 10⁷ re-scoped to the confinement endpoint — "
            "finding 2026-07-11)"
        ),
        source_text="Breeze (STO F_m = 3.6×10⁷)",
        blocked_on=None,
        checks=(
            GateCheckSpec(
                check_id="f_m/booth_consistency",
                description=(
                    "F_m (global-max V_mode variant) via the SPEC §3 "
                    "formula, vs the Booth-implied anchor"
                ),
                window=GateWindow(
                    lo=BOOTH_IMPLIED_F_M
                    * (1.0 - BOOTH_TWO_POINT_REL_TOL),
                    hi=BOOTH_IMPLIED_F_M
                    * (1.0 + BOOTH_TWO_POINT_REL_TOL),
                ),
                target_value=BOOTH_IMPLIED_F_M,
                provenance=(
                    "BOOTH_IMPLIED_F_M (§3 formula at Booth's printed "
                    "Q = 6,980, BOOTH_IMPLIED_V_MODE_M3, f = 1.45 GHz "
                    "— SPEC §5a finding 2026-07-11); F_M_BENCHMARK "
                    "gates the formula itself in the §3 tests"
                ),
                tolerance_rationale=_F_M_RATIONALE,
            ),
        ),
    ),
)

__all__ = [
    "BOOTH_TWO_POINT_REL_TOL",
    "CONFINEMENT_ENDPOINT_Q_HI",
    "CONFINEMENT_ENDPOINT_Q_LO",
    "CONFINEMENT_ENDPOINT_V_MODE_MAX_M3",
    "CONFINEMENT_MIN_POINTS",
    "F_M_ORDER_HI",
    "F_M_ORDER_LO",
    "F_ROW_HALF_WIDTH_HZ",
    "GATE_ROWS",
    "GateCheckSpec",
    "GateRowSpec",
    "GateWindow",
]
