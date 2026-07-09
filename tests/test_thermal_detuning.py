"""SPEC §7.T5(b)/§7.T4 — detuning-integration anchors A1-A11 (§8 discipline).

Anchor map (plan of record, amendment branch (b) applied to A2/A4):

A1  spin-arm uniform-ΔT: exact coefficient x ΔT, width == 0.0 exactly.
A2  cavity-arm uniform-ΔT: exact u^p_e closed form (the truth map).
C3  linear-limit consistency: pure-CW slope identity vs the committed
    §6T point function (exact algebraic identity + documented <=2%
    mixing bound at the 293-300 K base points).
A4  budget round-trip against the TRUE u^p_e map after one Newton step
    (<1e-9 relative), plus the quadratic-seed deviation pin
    f*p_e*(p_e-1)/2*(u-1)^2 (~ppm of f at the 30 K envelope).
A5  1/sqrt(Q) asymptotic exponent under C0 = c*Q_L, kappa_c = f/Q_L;
    positive exponent near threshold.
A6  kappa_c cyclic-Hz unit-trap guard + planning-point hand values.
A7  wiring identity: uniform probe mean == volume_average_k.
A8  1-D parabolic slab moments (mean Θ/3, rms Θ/sqrt(45)) — exact.
A9  Beer-Lambert 1-D moments vs the hand-derived closed-form profile.
A10 envelope-discrepancy pins (integrated vs point-slope vs
    first-order integral) — the §6T caveat made quantitative.
A11 flag propagation: DifferentialDetuning cannot exist unflagged;
    report carries the D8/composite/§5a status notes; committed report
    is byte-pinned to the generator.
"""

from __future__ import annotations

import dataclasses
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

from cavity.provenance.constants import (
    CRYSTAL,
    DELOAD_K,
    DF_CAVITY_DT,
    DF_SPIN_DT,
    STO,
    TARGET,
    TARGETS,
    cavity_df_dt_hz_per_k,
)
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.cylinder import CylinderSpec, PumpSource, SurfaceBC, solve
from cavity.thermal.detuning import (
    COMMON_DELTA_T_NOTE,
    Q_MARGIN_RUNG,
    SPIN_WEIGHT_RUNG,
    UNIFORM_PLACEHOLDER_RUNG,
    DifferentialDetuning,
    cavity_arm_shift_hz,
    cavity_arm_shift_uniform_hz,
    crystal_probe_grid,
    cylinder_delta_t_samples,
    cylinder_line_observable,
    delta_f_max_hz,
    delta_t_max_k,
    differential_detuning_from_cylinder,
    differential_detuning_from_samples,
    differential_detuning_hz,
    p_max_w,
    q_loaded,
    uniform_probe_measure,
)
from cavity.thermal.report_margin import PLANNING_C0, build_report

from tests._gate_record_fixture import GATE_P_E

F_HZ = TARGET.f_design_hz
T0_CW = DF_CAVITY_DT.curie_weiss_t0_k
T_BASE = DF_CAVITY_DT.t_window_lo_k  # 293 K
T_TOP = DF_CAVITY_DT.t_window_hi_k  # 323 K
TAU = T_BASE - T0_CW


def _one_d_spec(k: float = 0.35) -> CylinderSpec:
    """Insulated side + insulated top + Dirichlet base: with a flood
    source the positive radial modes project to exactly zero
    (f_hat_n ∝ J1(j1_n) = 0), leaving the pure 1-D axial physics."""
    return CylinderSpec(
        radius_m=CRYSTAL.diameter_m / 2.0,
        height_m=CRYSTAL.height_m,
        k_r_w_m_k=k,
        side=SurfaceBC.robin(0.0),
        top=SurfaceBC.robin(0.0),
        base=SurfaceBC.dirichlet(),
    )


# --- A1 / A2: uniform-ΔT closed forms ---------------------------------------


def test_a1_spin_arm_uniform_exact_shift_zero_width():
    n = 40
    delta_t = np.full(n, 3.0)
    probe = np.full(n, 1.0 / n)
    result = differential_detuning_from_samples(delta_t, probe, T_BASE)
    # coefficient x ΔT to float precision (np.average accumulates ~1 ulp
    # on the weighted mean); the IDENTICALLY-enforced piece is the width
    assert result.delta_f_spin_hz == pytest.approx(
        DF_SPIN_DT.df_dt_hz_per_k * 3.0, rel=1e-14
    )
    assert result.inhom_width_hz == 0.0  # identically, not to rounding
    assert result.mean_delta_t_k == pytest.approx(3.0, rel=1e-14)
    # §6T signs: cavity positive, spin negative, differential ADDS
    assert result.delta_f_cavity_hz > 0 > result.delta_f_spin_hz
    assert result.delta_f_differential_hz == pytest.approx(
        result.delta_f_cavity_hz + abs(result.delta_f_spin_hz), rel=1e-14
    )


def test_a2_cavity_arm_uniform_matches_u_pe_closed_form():
    delta_t = 30.0  # the ruled envelope
    for p_e in (1.0, GATE_P_E):
        # the truth map, computed independently of the module
        u = math.sqrt((TAU + delta_t) / TAU)
        expected = F_HZ * (u**p_e - 1.0)
        closed = cavity_arm_shift_uniform_hz(delta_t, T_BASE, p_e=p_e)
        assert closed == pytest.approx(expected, rel=1e-14)
        # weighted machinery on constant samples adds exactly nothing
        samples = np.full(17, delta_t)
        probe = np.linspace(1.0, 2.0, 17)  # any positive weights
        weighted = cavity_arm_shift_hz(samples, probe, T_BASE, p_e=p_e)
        assert weighted == pytest.approx(closed, rel=1e-14)


def test_a2_validity_floor_guard():
    with pytest.raises(ValueError, match="112"):
        cavity_arm_shift_uniform_hz(0.0, 100.0)
    with pytest.raises(ValueError, match="validity floor"):
        cavity_arm_shift_hz(
            np.array([-200.0]), np.array([1.0]), T_BASE
        )


# --- C3: linear-limit consistency vs the committed §6T point function -------


def test_c3_committed_slope_identity_and_mixing_bound():
    # exact algebraic identity at every window temperature:
    # committed(T) * eps_canon / eps_CW(T) == f / (2 (T - T0_CW))
    for t in (T_BASE, DF_CAVITY_DT.t_ref_k, T_TOP):
        eps_cw = DF_CAVITY_DT.curie_constant_k / (t - T0_CW)
        lhs = cavity_df_dt_hz_per_k(t) * STO.epsilon_r_real / eps_cw
        rhs = F_HZ / (2.0 * (t - T0_CW))
        assert lhs == pytest.approx(rhs, rel=1e-12)
    # documented mixing bound at the base points this map is used from:
    # +1.9% at 293 K, +0.8% at 300 K (eps_CW/eps_canon)
    for t, bound in ((T_BASE, 0.02), (DF_CAVITY_DT.t_ref_k, 0.01)):
        pure_cw = F_HZ / (2.0 * (t - T0_CW))
        committed = cavity_df_dt_hz_per_k(t)
        assert abs(committed / pure_cw - 1.0) < bound


def test_c3_small_delta_t_limit_is_pure_cw_slope():
    h = 1e-6
    slope = cavity_arm_shift_uniform_hz(h, T_BASE, p_e=GATE_P_E) / h
    expected = F_HZ * GATE_P_E / (2.0 * TAU)
    assert slope == pytest.approx(expected, rel=1e-6)


# --- A4: inversion round-trip (amendment branch (b)) -------------------------


def test_a4_round_trip_exact_against_true_map():
    # from sub-Hz budgets to the full 30 K envelope scale
    envelope_df = differential_detuning_hz(30.0, T_BASE, p_e=GATE_P_E)
    for df in (1e3, 1e5, 1.7e6, envelope_df):
        dt_max = delta_t_max_k(df, T_BASE, p_e=GATE_P_E)
        back = differential_detuning_hz(dt_max, T_BASE, p_e=GATE_P_E)
        assert back == pytest.approx(df, rel=1e-9)
    # cavity-only branch (df_spin = 0 is allowed by the <= 0 guard)
    dt_max = delta_t_max_k(
        1.7e6, T_BASE, p_e=GATE_P_E, df_spin_dt_hz_per_k=0.0
    )
    back = differential_detuning_hz(
        dt_max, T_BASE, p_e=GATE_P_E, df_spin_dt_hz_per_k=0.0
    )
    assert back == pytest.approx(1.7e6, rel=1e-9)
    assert delta_t_max_k(0.0, T_BASE) == 0.0


def test_a4_quadratic_seed_deviation_pin():
    """The seed solves the p_e-LINEARISED map; its residual against the
    true u^p_e map is second order — f*p_e*(p_e-1)/2*(u-1)^2, ~ppm of f
    at the 30 K envelope (amendment (a) pin, kept under branch (b))."""
    p_e = GATE_P_E
    s = abs(DF_SPIN_DT.df_dt_hz_per_k)
    df = differential_detuning_hz(30.0, T_BASE, p_e=p_e)
    # replicate the seed exactly (Citardauq form, as in delta_t_max_k)
    b = F_HZ * p_e
    rhs = df + s * TAU + b
    disc = math.sqrt(b * b + 4.0 * s * TAU * rhs)
    u0 = 2.0 * rhs / (b + disc)
    # seed residual against the true map: the spin term is exact in the
    # seed, so g(u0) = f*(u0^p_e - 1) - f*p_e*(u0 - 1) identically
    residual = F_HZ * (u0**p_e - 1.0) - F_HZ * p_e * (u0 - 1.0)
    predicted = F_HZ * p_e * (p_e - 1.0) / 2.0 * (u0 - 1.0) ** 2
    assert residual == pytest.approx(predicted, rel=0.05)  # 2nd-order law
    assert abs(residual) < 1e-5 * F_HZ  # "~ppm of f" at the envelope


def test_a4_sign_convention_guards():
    with pytest.raises(ValueError, match="sign convention"):
        differential_detuning_hz(1.0, T_BASE, df_spin_dt_hz_per_k=1e5)
    with pytest.raises(ValueError, match="sign convention"):
        delta_t_max_k(1e6, T_BASE, df_spin_dt_hz_per_k=1e5)
    with pytest.raises(ValueError, match="non-negative"):
        differential_detuning_hz(-1.0, T_BASE)
    with pytest.raises(ValueError, match="non-negative"):
        delta_t_max_k(-1.0, T_BASE)


# --- A5: 1/sqrt(Q) asymptotic exponent --------------------------------------


def _log_slope(q_l: float, c_per_q: float) -> float:
    eps = 1e-4
    hi = delta_f_max_hz(c_per_q * q_l * (1 + eps), F_HZ / (q_l * (1 + eps)))
    lo = delta_f_max_hz(c_per_q * q_l / (1 + eps), F_HZ * (1 + eps) / q_l)
    return (math.log(hi) - math.log(lo)) / (2.0 * math.log(1 + eps))


def test_a5_inverse_sqrt_q_asymptote_and_threshold_departure():
    # napkin assumptions: C0 = c*Q_L, kappa_c = f/Q_L, all else fixed
    assert _log_slope(1e6, 1.0) == pytest.approx(-0.5, abs=1e-4)
    # near threshold the exponent is POSITIVE (more Q helps there):
    # d ln Δf_max / d ln Q = -1 + cQ/(2(cQ - 1)) = +0.5 at cQ = 1.5
    assert _log_slope(1.5, 1.0) == pytest.approx(0.5, abs=1e-3)


# --- A6: planning-point hand values + unit-trap guard ------------------------


def test_a6_kappa_c_cyclic_hz_and_planning_point():
    q_l = q_loaded(TARGETS.booth.q_factor)
    assert q_l == pytest.approx(
        TARGETS.booth.q_factor / (1.0 + DELOAD_K), rel=1e-14
    )
    kappa_c = resonance_linewidth_hz(F_HZ, q_l)
    # hand value: 1.45e9 * 1.2 / 6980 = 249.284 kHz CYCLIC. The W20
    # angular-"Hz" trap (provenance table, trap 1) would give 2*pi*f/Q_L
    # ≈ 1.566e6 rad/s — the tolerance would catch it by a factor 2*pi.
    assert kappa_c == pytest.approx(249.284e3, rel=1e-4)
    df_max = delta_f_max_hz(PLANNING_C0, kappa_c)
    assert df_max == pytest.approx(1.7135e6, rel=1e-3)  # hand: 1.7135 MHz
    # ΔT_max at the planning point (adopted map, gate p_e, 293 K base)
    dt_max = delta_t_max_k(df_max, T_BASE, p_e=GATE_P_E)
    assert dt_max == pytest.approx(0.5840, rel=1e-3)
    # band endpoints via the §6T coefficient bands (linear, sub-K regime)
    lo = df_max / (
        DF_CAVITY_DT.df_dt_band_hi_hz_per_k
        + abs(DF_SPIN_DT.df_dt_band_lo_hz_per_k)
    )
    hi = df_max / (
        DF_CAVITY_DT.df_dt_band_lo_hz_per_k
        + abs(DF_SPIN_DT.df_dt_band_hi_hz_per_k)
    )
    assert lo == pytest.approx(0.567, rel=2e-3)
    assert hi == pytest.approx(0.725, rel=2e-3)


def test_a6_delta_f_max_domain():
    assert delta_f_max_hz(1.0, 1e5) == 0.0  # at threshold: zero margin
    assert delta_f_max_hz(0.5, 1e5) == 0.0  # below threshold: zero, no gate
    with pytest.raises(ValueError, match="cyclic"):
        delta_f_max_hz(190.0, 0.0)


# --- A7: wiring identity vs volume_average_k ---------------------------------


def test_a7_uniform_probe_mean_is_volume_average():
    spec = CylinderSpec(
        radius_m=CRYSTAL.diameter_m / 2.0,
        height_m=CRYSTAL.height_m,
        k_r_w_m_k=0.2,
        side=SurfaceBC.robin(15.0),
        top=SurfaceBC.robin(15.0),
        base=SurfaceBC.dirichlet(),
    )
    source = PumpSource(p_w=0.5, axial_form="beer_lambert", l_abs_m=2e-3)
    sol = solve(spec, source, n_modes=24)
    grid = crystal_probe_grid(n_r=96, n_z=96)
    probe = uniform_probe_measure(grid)
    mean = float(
        np.average(cylinder_delta_t_samples(sol, grid), weights=probe)
    )
    assert mean == pytest.approx(sol.volume_average_k(), rel=1e-6)
    # grid measure sanity: node volumes integrate to the cylinder volume
    vol = grid.node_volumes_m3().sum()
    expected = math.pi * grid.radius_m**2 * grid.height_m
    assert vol == pytest.approx(expected, rel=1e-12)


# --- A8 / A9: 1-D closed-form moment anchors ---------------------------------


def test_a8_parabolic_slab_moments_exact():
    """Uniform deposition, insulated top, Dirichlet base, insulated side
    => ΔT(z) = Θ(1 - ζ²)/2, Θ = PL/(πR²k_z). Uniform-weight moments:
    mean Θ/3, rms Θ/sqrt(45) — hand-derived (∫(1-ζ²)/2 dζ = 1/3;
    ∫((1-ζ²)/2)² dζ = 2/15; var = 2/15 - 1/9 = 1/45)."""
    spec = _one_d_spec()
    p_w = 1.0
    sol = solve(spec, PumpSource(p_w=p_w, axial_form="uniform"), n_modes=8)
    theta = p_w * spec.height_m / (
        math.pi * spec.radius_m**2 * spec.k_z
    )
    grid = crystal_probe_grid(n_r=8, n_z=16)
    obs = cylinder_line_observable(sol, grid)
    assert obs.mean_delta_t_k == pytest.approx(theta / 3.0, rel=1e-12)
    assert obs.rms_delta_t_k == pytest.approx(
        theta / math.sqrt(45.0), rel=1e-12
    )
    assert obs.mean_shift_hz == pytest.approx(
        DF_SPIN_DT.df_dt_hz_per_k * theta / 3.0, rel=1e-12
    )
    assert obs.inhom_width_hz == pytest.approx(
        abs(DF_SPIN_DT.df_dt_hz_per_k) * theta / math.sqrt(45.0), rel=1e-12
    )


def test_a9_beer_lambert_slab_moments_vs_hand_profile():
    """Same 1-D BCs, Beer-Lambert deposition. Hand-derived profile
    (θ'(0) = 0, θ(1) = 0, θ'' = -g):
    ΔT(ζ) = Θ[(1-ζ) + ℓ(e^{-1/ℓ} - e^{-ζ/ℓ})]/c, c = 1 - e^{-1/ℓ}."""
    spec = _one_d_spec()
    p_w, l_abs = 0.8, 2e-3
    ell = l_abs / spec.height_m
    sol = solve(
        spec,
        PumpSource(p_w=p_w, axial_form="beer_lambert", l_abs_m=l_abs),
        n_modes=8,
    )
    theta = p_w * spec.height_m / (math.pi * spec.radius_m**2 * spec.k_z)
    c_norm = -math.expm1(-1.0 / ell)

    def profile(zeta: float) -> float:
        return (
            theta
            * ((1.0 - zeta) + ell * (math.exp(-1.0 / ell) - math.exp(-zeta / ell)))
            / c_norm
        )

    # module field matches the hand profile pointwise
    for zeta in (0.0, 0.2, 0.5, 0.9, 1.0):
        assert sol.delta_t(0.0, zeta * spec.height_m) == pytest.approx(
            profile(zeta), rel=1e-12, abs=1e-15
        )
    m1, _ = quad(profile, 0.0, 1.0, epsabs=0.0, epsrel=1e-12)
    m2, _ = quad(lambda z: profile(z) ** 2, 0.0, 1.0, epsabs=0.0, epsrel=1e-12)
    grid = crystal_probe_grid(n_r=8, n_z=64)
    obs = cylinder_line_observable(sol, grid)
    assert obs.mean_delta_t_k == pytest.approx(m1, rel=1e-9)
    assert obs.rms_delta_t_k == pytest.approx(
        math.sqrt(m2 - m1 * m1), rel=1e-9
    )


# --- A10: envelope-discrepancy pins ------------------------------------------


def test_a10_envelope_form_discrepancies_pinned():
    """The §6T 'integrate, don't multiply' caveat and the item-2 branch
    choice, as quantitative regression facts (p_e = 1, 293 -> 323 K)."""
    integrated = cavity_arm_shift_uniform_hz(T_TOP - T_BASE, T_BASE)
    point_300 = cavity_df_dt_hz_per_k(DF_CAVITY_DT.t_ref_k) * (T_TOP - T_BASE)
    slope_293 = cavity_df_dt_hz_per_k(T_BASE) * (T_TOP - T_BASE)
    # first-order integral of the committed slope function over the window
    first_order = (
        (F_HZ / (2.0 * STO.epsilon_r_real))
        * DF_CAVITY_DT.curie_constant_k
        * (1.0 / (T_BASE - T0_CW) - 1.0 / (T_TOP - T0_CW))
    )
    assert integrated == pytest.approx(82.61e6, rel=1e-3)  # hand: 82.6 MHz
    assert 1.003 < integrated / point_300 < 1.012  # ~ +0.7%
    assert 1.060 < integrated / first_order < 1.075  # ~ +6.6% (resummation)
    assert 0.945 < integrated / slope_293 < 0.965  # ~ -4.6% (local slope)


# --- p_max linearity identity -------------------------------------------------


def test_p_max_linearity_identity():
    spec = _one_d_spec()
    p_ref = 0.7
    sol = solve(spec, PumpSource(p_w=p_ref, axial_form="uniform"), n_modes=8)
    grid = crystal_probe_grid(n_r=8, n_z=16)
    probe = uniform_probe_measure(grid)
    mean = float(
        np.average(cylinder_delta_t_samples(sol, grid), weights=probe)
    )
    # ΔT_max equal to the P_ref mean rise => P_max == P_ref exactly
    assert p_max_w(sol, grid, mean) == pytest.approx(p_ref, rel=1e-12)
    assert p_max_w(sol, grid, 2.0 * mean) == pytest.approx(
        2.0 * p_ref, rel=1e-12
    )


# --- A11: flag propagation + report pins --------------------------------------


def test_a11_result_cannot_exist_unflagged():
    for field in dataclasses.fields(DifferentialDetuning):
        assert field.default is dataclasses.MISSING
        assert field.default_factory is dataclasses.MISSING
    with pytest.raises(TypeError):
        DifferentialDetuning()  # every field required, flags included


def test_a11_placeholder_flags_and_notes():
    spec = _one_d_spec()
    sol = solve(spec, PumpSource(p_w=0.5, axial_form="uniform"), n_modes=8)
    grid = crystal_probe_grid(n_r=8, n_z=16)
    result = differential_detuning_from_cylinder(sol, grid, T_BASE)
    assert result.probe_weight_is_placeholder is True
    assert result.spin_projection is None
    assert result.spin_weight_rung == UNIFORM_PLACEHOLDER_RUNG
    assert COMMON_DELTA_T_NOTE in result.status_notes
    assert UNIFORM_PLACEHOLDER_RUNG in result.status_notes
    assert Q_MARGIN_RUNG in result.status_notes


def test_a11_real_weight_path_requires_projection_meta():
    delta_t = np.full(5, 1.0)
    probe = np.full(5, 0.2)
    with pytest.raises(ValueError, match="SpinProjection"):
        differential_detuning_from_samples(
            delta_t, probe, T_BASE, probe_weight_is_placeholder=False
        )
    with pytest.raises(ValueError, match="placeholder"):
        differential_detuning_from_samples(
            delta_t,
            probe,
            T_BASE,
            spin_projection={"mode": "isotropic_h2", "components": None},
        )
    result = differential_detuning_from_samples(
        delta_t,
        probe,
        T_BASE,
        probe_weight_is_placeholder=False,
        spin_projection={"mode": "isotropic_h2", "components": None},
        gain_mask_is_fallback=True,
    )
    assert result.spin_weight_rung == SPIN_WEIGHT_RUNG
    assert SPIN_WEIGHT_RUNG in result.status_notes
    assert any("STO-dielectric fallback" in n for n in result.status_notes)


def test_a11_report_status_notes_and_byte_pin():
    report = build_report()
    # REQ 1: the D8 common-ΔT wording, verbatim from the single source
    assert COMMON_DELTA_T_NOTE in report
    # REQ 2: the cross-build composite line
    assert "CROSS-BUILD COMPOSITE" in report
    assert "NEITHER build's number" in report
    # R5: the §5a own-model gate line
    assert "phase1_complete: false" in report
    assert "§5a" in report
    # the committed report is exactly what the generator produces
    committed = (
        Path(__file__).resolve().parents[1]
        / "thermal"
        / "reports"
        / "q_margin_planning_point.md"
    )
    assert committed.read_text(encoding="utf-8") == report
