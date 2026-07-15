"""L4 composed-space CV gate — ratified Q8 thresholds, planning pins
re-derived independently in-test, κs-branch reporting (rider R1).
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.provenance import DELOAD_K, KAPPA_S, STO, TARGET, TOL
from cavity.surrogate.cv_gate import (
    GateThresholds,
    evaluate_cv_gate,
    planning_threshold_pins,
)
from cavity.sweep.centre_check import PINNED_CENTRE
from cavity.sweep.compose import AnchorPoint, c0_anchored, kappa_c_hz
from cavity.sweep.dofs import Rung
from cavity.thermal.detuning import delta_f_max_hz
from cavity.thermal.report_margin import PLANNING_C0


def _rows(n=12, seed=7):
    rng = np.random.default_rng(seed)
    tand = rng.uniform(TOL.tan_delta_min, TOL.tan_delta_max, n)
    q_wall = 1.0 / (
        1.0 / PINNED_CENTRE.q0 - PINNED_CENTRE.p_e * STO.tan_delta
    )
    q0 = 1.0 / (PINNED_CENTRE.p_e * tand + 1.0 / q_wall)
    eta = rng.uniform(0.3, 0.4, n)
    return [
        {
            "f_real_hz": TARGET.f_xz_measured_hz,
            "q": float(q0[i]),
            "magnetic_filling_factor": float(eta[i]),
            "gain_mask_is_fallback": False,
            "record_hash": f"r{i:04d}",
        }
        for i in range(n)
    ]


def _anchor():
    return AnchorPoint(
        f_hz=TARGET.f_xz_measured_hz,
        eta_h=0.35,
        kappa_c_hz=kappa_c_hz(TARGET.f_xz_measured_hz, PINNED_CENTRE.q0),
        record_hash="anchor",
        gain_mask_is_fallback=False,
    )


def _perfect_predictions(rows):
    f = np.array([r["f_real_hz"] for r in rows])
    lq = np.log([r["q"] for r in rows])
    le = np.log([r["magnetic_filling_factor"] for r in rows])
    return f, lq, le


# ---------------------------------------------------------------------------
# Thresholds — ratified defaults (rider R1)
# ---------------------------------------------------------------------------


def test_thresholds_ratified_by_default_citing_the_ruling():
    t = GateThresholds()
    assert t.delta_f_max_frac_of_p5 == 0.05
    assert t.f_rmse_frac_of_min_kappa_c == 0.10
    assert t.ratified is True
    assert "2026-07-15" in t.ratification
    assert "ticklish-possum" in t.ratification
    assert t.rung is Rung.PLANNING_ASSUMPTION


def test_threshold_fractions_validated():
    with pytest.raises(ValueError):
        GateThresholds(delta_f_max_frac_of_p5=0.0)
    with pytest.raises(ValueError):
        GateThresholds(f_rmse_frac_of_min_kappa_c=1.5)


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------


def test_perfect_surrogate_passes_both_gates():
    rows = _rows()
    f, lq, le = _perfect_predictions(rows)
    report = evaluate_cv_gate(
        rows, f, lq, le, anchor=_anchor()
    )
    assert report["gate1_margin_arm"]["verdict"] == "PASS"
    assert report["gate2_tuning_arm"]["verdict"] == "PASS"
    # exp(log(·)) round-trip leaves float dust only.
    assert report["gate1_margin_arm"][
        "max_abs_delta_f_max_error_hz"
    ] == pytest.approx(0.0, abs=1e-6)
    assert report["gate2_tuning_arm"]["f_rmse_hz"] == 0.0


def test_corrupted_surrogate_fails_each_gate():
    rows = _rows()
    f, lq, le = _perfect_predictions(rows)
    # Gate 1: a 30% η error moves C₀ (and Δf_max) far beyond 5% of P5.
    bad_eta = le + np.log(1.3)
    report = evaluate_cv_gate(rows, f, lq, bad_eta, anchor=_anchor())
    assert report["gate1_margin_arm"]["verdict"] == "FAIL"
    # Gate 2: a 100 kHz f bias >> 10% of min κc (≈ 24 kHz scale).
    bad_f = f + 1.0e5
    report = evaluate_cv_gate(rows, bad_f, lq, le, anchor=_anchor())
    assert report["gate2_tuning_arm"]["verdict"] == "FAIL"


def test_unratified_instance_reports_advisory_only():
    rows = _rows()
    f, lq, le = _perfect_predictions(rows)
    report = evaluate_cv_gate(
        rows, f, lq, le,
        anchor=_anchor(),
        thresholds=GateThresholds(ratified=False),
    )
    assert report["gate1_margin_arm"]["verdict"] == "ADVISORY-PASS"
    assert report["gate2_tuning_arm"]["verdict"] == "ADVISORY-PASS"


def test_report_prints_kappa_s_branch_and_sidebar():
    rows = _rows()
    f, lq, le = _perfect_predictions(rows)
    report = evaluate_cv_gate(rows, f, lq, le, anchor=_anchor())
    # Rider R1: every gate report prints its κs branch.
    assert report["kappa_s_branch"] == "point"
    assert report["kappa_s_hz"] == KAPPA_S.kappa_s_hz
    sidebar = report["gate1_kappa_s_band_sidebar"]
    assert set(sidebar) == {"lo", "hi"}
    for entry in sidebar.values():
        assert entry["binding"] is False
    assert (
        sidebar["lo"]["p5_delta_f_max_hz"]
        < report["gate1_margin_arm"]["p5_delta_f_max_hz"]
        < sidebar["hi"]["p5_delta_f_max_hz"]
    )


def test_composed_path_agrees_with_direct_detuning_law():
    """Second code path: the gate's composed P5 equals the direct
    compose + delta_f_max_hz arithmetic on the truth rows."""
    rows = _rows()
    f, lq, le = _perfect_predictions(rows)
    anchor = _anchor()
    report = evaluate_cv_gate(rows, f, lq, le, anchor=anchor)
    dfmax = []
    for r in rows:
        kc = kappa_c_hz(r["f_real_hz"], r["q"])
        c0 = c0_anchored(
            r["f_real_hz"], r["magnetic_filling_factor"], kc, anchor
        )
        dfmax.append(delta_f_max_hz(c0, kc, KAPPA_S.kappa_s_hz))
    assert report["gate1_margin_arm"]["p5_delta_f_max_hz"] == (
        pytest.approx(float(np.percentile(dfmax, 5)), rel=1e-12)
    )


def test_prediction_shape_mismatch_refused():
    rows = _rows(n=5)
    f, lq, le = _perfect_predictions(rows)
    with pytest.raises(ValueError, match="match truth_rows"):
        evaluate_cv_gate(rows, f[:-1], lq[:-1], le[:-1], anchor=_anchor())


# ---------------------------------------------------------------------------
# Planning pins — re-derived independently (feedback_scoping_numbers)
# ---------------------------------------------------------------------------


def test_planning_pins_match_independent_monte_carlo():
    """Independent second path: numerical P5 over the uniform tanδ band
    (5×10⁵ draws) through the same committed constants must reproduce
    the closed-form pins (which use the monotone-map quantile image)."""
    pins = planning_threshold_pins()
    rng = np.random.default_rng(20260715)
    tand = rng.uniform(TOL.tan_delta_min, TOL.tan_delta_max, 500_000)
    q_wall = 1.0 / (
        1.0 / PINNED_CENTRE.q0 - PINNED_CENTRE.p_e * STO.tan_delta
    )
    q0 = 1.0 / (PINNED_CENTRE.p_e * tand + 1.0 / q_wall)
    f_spin = TARGET.f_xz_measured_hz
    kc = (1.0 + DELOAD_K) * f_spin / q0
    c0 = PLANNING_C0 * q0 / PINNED_CENTRE.q0
    assert q_wall == pytest.approx(pins["q_wall"], rel=1e-12)
    for branch, ks in [
        ("point", KAPPA_S.kappa_s_hz),
        ("lo", KAPPA_S.kappa_s_band_lo_hz),
        ("hi", KAPPA_S.kappa_s_band_hi_hz),
    ]:
        dfmax = (kc + ks) / 2.0 * np.sqrt(c0 - 1.0)
        p5_mc = float(np.percentile(dfmax, 5))
        assert pins["p5_delta_f_max_hz_by_kappa_s_branch"][branch] == (
            pytest.approx(p5_mc, rel=2e-3)
        )
    assert pins["min_kappa_c_hz"] == pytest.approx(
        float(np.min(kc)), rel=1e-3
    )


def test_planning_pins_carry_the_ratified_planning_values():
    """The ratified plan's quoted planning quantifications: gate 1
    threshold ≈ 479 kHz (κs point branch), gate 2 threshold ≈ 24.0 kHz.
    Quoted-precision windows, not new tolerances."""
    pins = planning_threshold_pins()
    assert 478.0e3 < pins["gate1_threshold_hz_point_branch"] < 480.0e3
    assert 23.9e3 < pins["gate2_threshold_hz"] < 24.1e3
    # And the P5 planning points per branch as quoted in the plan.
    p5 = pins["p5_delta_f_max_hz_by_kappa_s_branch"]
    assert p5["point"] == pytest.approx(9.571e6, rel=1e-3)
    assert p5["lo"] == pytest.approx(5.183e6, rel=1e-3)
    assert p5["hi"] == pytest.approx(11.378e6, rel=1e-3)


def test_delta_f_max_is_monotone_decreasing_in_tan_delta():
    """The closed-form P5 = image-of-95th-percentile rests on
    monotonicity; verify it across the band for every κs branch."""
    q_wall = 1.0 / (
        1.0 / PINNED_CENTRE.q0 - PINNED_CENTRE.p_e * STO.tan_delta
    )
    tand = np.linspace(TOL.tan_delta_min, TOL.tan_delta_max, 201)
    q0 = 1.0 / (PINNED_CENTRE.p_e * tand + 1.0 / q_wall)
    kc = (1.0 + DELOAD_K) * TARGET.f_xz_measured_hz / q0
    c0 = PLANNING_C0 * q0 / PINNED_CENTRE.q0
    for ks in (
        KAPPA_S.kappa_s_hz,
        KAPPA_S.kappa_s_band_lo_hz,
        KAPPA_S.kappa_s_band_hi_hz,
    ):
        dfmax = (kc + ks) / 2.0 * np.sqrt(c0 - 1.0)
        assert np.all(np.diff(dfmax) < 0.0)


def test_pins_are_labelled_superseded_by_the_sweep():
    pins = planning_threshold_pins()
    assert "sweep" in pins["superseded_by"]
