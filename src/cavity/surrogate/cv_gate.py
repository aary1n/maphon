"""L4 composed-space CV gate — §7.5's "≪" made numeric (Q8).

Q8 STATUS — RATIFIED 2026-07-15 (docs/plans/ticklish-possum.md,
ratification record R1), rung PLANNING-ASSUMPTION:

  Gate 1 (margin arm): per-draw held-out/LOO |δΔf_max| ≤ 5% of the
  population 5th-percentile Δf_max, both computed from the sweep's own
  composed population at the committed κs point branch (1.4 MHz), with
  the κs band edges reported alongside (lo edge reported, not binding).

  Gate 2 (tuning arm): f-surrogate RMSE ≤ 10% of the population-minimum
  κ̂c.

The gate is evaluated in COMPOSED space (Q7 ruling honours §7.5's
intent): raw-surrogate predictions (f, ln Q₀, ln η_H) are pushed
through `cavity.sweep.compose` and the committed threshold law
`cavity.thermal.detuning.delta_f_max_hz` — never a re-derivation.

Thresholds RECOMPUTE from the sweep's own population; the planning
values (≈ 479 kHz and ≈ 24.0 kHz) enter the code only through
`planning_threshold_pins()`, which derives them from committed
constants at call time (the regression pin re-derives them
independently in test — no magic numbers). They are SUPERSEDED by the
sweep itself. Every gate report prints the κs branch it was evaluated
under (rider R1).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from cavity.provenance import STO, TARGET, TOL
from cavity.sweep.centre_check import PINNED_CENTRE
from cavity.sweep.compose import (
    AnchorPoint,
    c0_anchored,
    kappa_c_hz,
    kappa_s_branch_hz,
)
from cavity.sweep.dofs import Rung
from cavity.thermal.detuning import delta_f_max_hz
from cavity.thermal.report_margin import PLANNING_C0

Q8_RATIFICATION = (
    "Q8 RATIFIED 2026-07-15 — docs/plans/ticklish-possum.md, "
    "ratification record R1: thresholds recompute from the sweep's own "
    "population; planning values are in-test re-derived regression "
    "pins; rung stays planning-assumption"
)


@dataclass(frozen=True)
class GateThresholds:
    """The two ratified Q8 quantifications of §7.5's "≪".

    `ratified` defaults True citing the 2026-07-15 R1 ruling. An
    unratified instance remains constructible (future re-opens) and
    downgrades every verdict to ADVISORY — the gate then computes
    everything but asserts nothing.
    """

    delta_f_max_frac_of_p5: float = 0.05
    f_rmse_frac_of_min_kappa_c: float = 0.10
    rung: Rung = Rung.PLANNING_ASSUMPTION
    ratified: bool = True
    ratification: str = Q8_RATIFICATION

    def __post_init__(self) -> None:
        if not 0.0 < self.delta_f_max_frac_of_p5 < 1.0:
            raise ValueError("delta_f_max fraction must be in (0, 1)")
        if not 0.0 < self.f_rmse_frac_of_min_kappa_c < 1.0:
            raise ValueError("f-RMSE fraction must be in (0, 1)")


def _composed_delta_f_max(
    f_hz: NDArray[np.float64],
    q0: NDArray[np.float64],
    eta_h: NDArray[np.float64],
    anchor: AnchorPoint,
    kappa_s_hz: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """(Δf_max, κc) per draw through the committed compositions."""
    kc = np.array(
        [kappa_c_hz(float(f), float(q)) for f, q in zip(f_hz, q0)]
    )
    c0 = np.array(
        [
            c0_anchored(float(f), float(e), float(k), anchor)
            for f, e, k in zip(f_hz, eta_h, kc)
        ]
    )
    dfmax = np.array(
        [
            delta_f_max_hz(float(c), float(k), kappa_s_hz)
            for c, k in zip(c0, kc)
        ]
    )
    return dfmax, kc


def _branch_evaluation(
    truth: tuple[NDArray, NDArray, NDArray],
    pred: tuple[NDArray, NDArray, NDArray],
    anchor: AnchorPoint,
    branch: str,
    frac_of_p5: float,
) -> dict:
    ks = kappa_s_branch_hz(branch)
    dfmax_t, kc_t = _composed_delta_f_max(*truth, anchor, ks)
    dfmax_p, _ = _composed_delta_f_max(*pred, anchor, ks)
    p5 = float(np.percentile(dfmax_t, 5))
    max_abs = float(np.max(np.abs(dfmax_p - dfmax_t)))
    threshold = frac_of_p5 * p5
    return {
        "kappa_s_branch": branch,
        "kappa_s_hz": ks,
        "p5_delta_f_max_hz": p5,
        "threshold_hz": threshold,
        "max_abs_delta_f_max_error_hz": max_abs,
        "within": bool(max_abs <= threshold),
        "min_kappa_c_hz": float(np.min(kc_t)),
    }


def evaluate_cv_gate(
    truth_rows: list[dict],
    f_pred_hz: NDArray[np.floating],
    ln_q0_pred: NDArray[np.floating],
    ln_eta_h_pred: NDArray[np.floating],
    *,
    anchor: AnchorPoint,
    thresholds: GateThresholds = GateThresholds(),
    kappa_s_branch: str = "point",
) -> dict:
    """Composed-space CV gate over a held-out (or LOO-predicted) set.

    `truth_rows` are RAW schema-v1 rows (f_real_hz, q,
    magnetic_filling_factor); predictions are the raw-basis surrogate
    outputs at the same draws. Binding verdicts at the committed κs
    point branch; the band edges ride the report as the sidebar
    (lo edge reported, not binding — ratified mechanics).
    """
    n = len(truth_rows)
    f_p = np.asarray(f_pred_hz, dtype=np.float64)
    q0_p = np.exp(np.asarray(ln_q0_pred, dtype=np.float64))
    eta_p = np.exp(np.asarray(ln_eta_h_pred, dtype=np.float64))
    if not (f_p.shape == q0_p.shape == eta_p.shape == (n,)):
        raise ValueError("prediction arrays must match truth_rows length")

    f_t = np.array([float(r["f_real_hz"]) for r in truth_rows])
    q0_t = np.array([float(r["q"]) for r in truth_rows])
    eta_t = np.array(
        [float(r["magnetic_filling_factor"]) for r in truth_rows]
    )
    truth = (f_t, q0_t, eta_t)
    pred = (f_p, q0_p, eta_p)

    binding = _branch_evaluation(
        truth, pred, anchor, kappa_s_branch,
        thresholds.delta_f_max_frac_of_p5,
    )
    sidebar = {
        branch: _branch_evaluation(
            truth, pred, anchor, branch,
            thresholds.delta_f_max_frac_of_p5,
        )
        for branch in ("lo", "hi")
        if branch != kappa_s_branch
    }

    f_rmse = float(np.sqrt(np.mean((f_p - f_t) ** 2)))
    f_threshold = (
        thresholds.f_rmse_frac_of_min_kappa_c * binding["min_kappa_c_hz"]
    )
    gate2_within = f_rmse <= f_threshold

    def verdict(within: bool) -> str:
        base = "PASS" if within else "FAIL"
        return base if thresholds.ratified else f"ADVISORY-{base}"

    return {
        "thresholds": {
            "delta_f_max_frac_of_p5": thresholds.delta_f_max_frac_of_p5,
            "f_rmse_frac_of_min_kappa_c": (
                thresholds.f_rmse_frac_of_min_kappa_c
            ),
            "rung": thresholds.rung.value,
            "ratified": thresholds.ratified,
            "ratification": thresholds.ratification,
        },
        # Rider R1: every gate report prints its κs branch.
        "kappa_s_branch": binding["kappa_s_branch"],
        "kappa_s_hz": binding["kappa_s_hz"],
        "anchor": {
            "record_hash": anchor.record_hash,
            "diagnostic_only": anchor.diagnostic_only,
        },
        "n_rows": n,
        "gate1_margin_arm": {
            **binding,
            "verdict": verdict(binding["within"]),
        },
        "gate1_kappa_s_band_sidebar": {
            branch: {
                **entry,
                "binding": False,
                "note": (
                    "reported, not binding (ratified Q8 mechanics: "
                    "binding at the committed point branch)"
                ),
            }
            for branch, entry in sidebar.items()
        },
        "gate2_tuning_arm": {
            "f_rmse_hz": f_rmse,
            "min_kappa_c_hz": binding["min_kappa_c_hz"],
            "threshold_hz": f_threshold,
            "within": bool(gate2_within),
            "verdict": verdict(gate2_within),
        },
        "failure_path": (
            "active learning within budget, then the §6 overrun cut "
            "order; a gate still failing at 300 solves is a "
            "STOP-and-report finding"
        ),
    }


def planning_threshold_pins() -> dict:
    """Pre-sweep planning quantification of both gates (SUPERSEDED by
    the sweep's own population once it exists).

    Derived at call time from committed constants only — the pinned
    canonical centre (import-only, record 823e67969516bcf2), the §4
    wall-split arithmetic 1/Q₀ = p_e·tanδ + 1/Q_wall, the TOL tanδ
    band, fixed-G planning scaling C₀ = PLANNING_C0·Q_L/Q_L_nom, and
    f = f_spin per draw (tuned operating point). Δf_max is monotone
    decreasing in tanδ over the band (MC-verified in test), so the
    population P5 is the closed-form image of the tanδ 95th percentile.
    """
    q0_nom = PINNED_CENTRE.q0
    p_e = PINNED_CENTRE.p_e
    f_spin = TARGET.f_xz_measured_hz
    q_wall = 1.0 / (1.0 / q0_nom - p_e * STO.tan_delta)

    def q0_of(tan_delta: float) -> float:
        return 1.0 / (p_e * tan_delta + 1.0 / q_wall)

    def dfmax_of(tan_delta: float, ks_hz: float) -> float:
        q0 = q0_of(tan_delta)
        kc = kappa_c_hz(f_spin, q0)
        c0 = PLANNING_C0 * q0 / q0_nom  # fixed-G planning scaling
        return delta_f_max_hz(c0, kc, ks_hz)

    span = TOL.tan_delta_max - TOL.tan_delta_min
    tan_delta_p95 = TOL.tan_delta_min + 0.95 * span
    thresholds = GateThresholds()

    p5_by_branch = {
        branch: dfmax_of(tan_delta_p95, kappa_s_branch_hz(branch))
        for branch in ("point", "lo", "hi")
    }
    min_kappa_c = kappa_c_hz(f_spin, q0_of(TOL.tan_delta_min))
    return {
        "q_wall": q_wall,
        "tan_delta_p95": tan_delta_p95,
        "p5_delta_f_max_hz_by_kappa_s_branch": p5_by_branch,
        "gate1_threshold_hz_point_branch": (
            thresholds.delta_f_max_frac_of_p5 * p5_by_branch["point"]
        ),
        "min_kappa_c_hz": min_kappa_c,
        "gate2_threshold_hz": (
            thresholds.f_rmse_frac_of_min_kappa_c * min_kappa_c
        ),
        "superseded_by": (
            "the sweep's own composed population (these are planning "
            "pins, not gate inputs)"
        ),
    }
