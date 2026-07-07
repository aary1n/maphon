"""SPEC §7T / §8 discipline — analytic anchors for the maser-cylinder solver.

The finite-cylinder Bessel/Robin anchor (`cavity.thermal.cylinder`, §7.T1
geometry split — the maser-crystal geometry, §7.T5 observable (b)) is
trusted only after it reproduces hand-derived closed forms:

  (i)   uniform volumetric heating, Dirichlet side wall → radial parabola
        q̇(R² − r²)/(4·k_r), plus the volume-average q̇R²/(8·k_r);
  (ii)  all-lateral-insulated, Dirichlet base → the 1-D axial slab, for
        uniform AND Beer-Lambert deposition (independent re-derivations
        in the test bodies);
  (iii) energy conservation — Σ boundary fluxes = P, deficit = radial
        truncation only (Robin-side rate caveat pinned separately);
  (iv)  Robin → Dirichlet continuity and Robin-h monotonicity;
  (v)   cross-check against the INDEPENDENT layered/Hankel machinery in
        their common regime (wide cylinder ≈ laterally-unbounded slab).

Plus the eigenvalue-machinery pins, the anisotropy stretch identity, the
Bi_s → 0 and l_abs → {0, ∞} bridges, the confluent-branch straddle, and
the graded-constants maser worked example. No COMSOL anywhere.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import j0, j1, jn_zeros

from cavity.provenance.constants import (
    CRYSTAL,
    EMISSIVITY_PTP,
    H_CONV_AIR,
    K_PTP,
    L_ABS_PUMP,
    RIG_GEOMETRY,
)
from cavity.thermal.cylinder import (
    CylinderSpec,
    PumpSource,
    SurfaceBC,
    robin_radial_eigenvalues,
    solve,
)
from cavity.thermal.layered import Layer, delta_t_gaussian_volumetric
from cavity.thermal.radiation import h_top_with_radiation

P = 1.0  # W — ΔT is linear in P (test_thermal_layered.py convention)
K = 0.3  # W/m/K — representative of the k_PTP band under test
R = 1.5e-3  # m — maser-crystal-scale radius (CRYSTAL.diameter_m / 2)
L = 8.0e-3  # m — maser-crystal-scale height (CRYSTAL.height_m)


# --- eigenvalue machinery ----------------------------------------------------


def test_robin_eigenvalues_satisfy_root_equation():
    """xₙ·J₁(xₙ) = Bi·J₀(xₙ) to root-refinement accuracy across the Bi range."""
    for bi in (1e-10, 0.05, 1.0, 100.0, 1e6):
        x = robin_radial_eigenvalues(bi, 8)
        resid = np.abs(x * j1(x) - bi * j0(x))
        # residual scale: |g'| ~ max(xₙ, Bi)·|J| near the root
        assert resid.max() < 1e-9 * max(1.0, bi * 1e-4)


def test_robin_eigenvalues_interlace_bessel_zeros():
    """Exactly one root per bracket (j₁,ₙ₋₁, j₀,ₙ), j₁,₀ := 0, for any Bi."""
    j0z = jn_zeros(0, 8)
    j1z = np.concatenate(([0.0], jn_zeros(1, 7)))
    for bi in (0.01, 1.0, 50.0):
        x = robin_radial_eigenvalues(bi, 8)
        assert np.all(x > j1z) and np.all(x < j0z)
        assert np.all(np.diff(x) > 0)


def test_robin_eigenvalue_small_bi_asymptote():
    """Bi → 0: x₁ → √(2·Bi) (expand x·J₁ ≈ x²/2, J₀ ≈ 1 in the root equation)."""
    bi = 1e-10
    x1 = robin_radial_eigenvalues(bi, 1)[0]
    assert math.isclose(x1, math.sqrt(2.0 * bi), rel_tol=1e-9)


def test_robin_eigenvalues_large_bi_approach_dirichlet():
    """Bi → ∞: roots → j₀,ₙ from below, error first-order in 1/Bi. The
    Dirichlet side itself uses jn_zeros exactly — this pins the finite-Bi
    branch against that exact target, not another root-finder output."""
    j0z = jn_zeros(0, 5)
    gaps = []
    for bi in (1e3, 1e4, 1e5):
        x = robin_radial_eigenvalues(bi, 5)
        assert np.all(x < j0z)
        gaps.append((j0z - x).max())
    assert gaps[0] > gaps[1] > gaps[2]
    assert 9.0 < gaps[0] / gaps[1] < 11.0  # ∝ 1/Bi


def test_norm_formula_matches_quadrature():
    """Nₙ = (R²/2)[J₀(xₙ)² + J₁(xₙ)²] — exact for ANY λ, pinned numerically."""
    for x in robin_radial_eigenvalues(1.0, 3):
        num, _ = quad(lambda rho: j0(x * rho) ** 2 * rho, 0.0, 1.0)
        assert math.isclose(num, 0.5 * (j0(x) ** 2 + j1(x) ** 2), rel_tol=1e-10)


# --- anchor (i): uniform source, Dirichlet side → radial parabola ------------


def test_anchor_i_uniform_dirichlet_side_parabola():
    """Uniform q̇ = P/(πR²L), side ΔT = 0, top/base insulated: the axial
    direction drops out and ΔT(r) = q̇(R² − r²)/(4·k_r) — peak P/(4π·k_r·L),
    volume average q̇R²/(8·k_r) (∫(1−ρ²)·2ρ dρ = 1/2 of the peak factor)."""
    spec = CylinderSpec(
        R, L, K, SurfaceBC.dirichlet(), SurfaceBC.robin(0.0), SurfaceBC.robin(0.0)
    )
    sol = solve(spec, PumpSource(P, "uniform", "flood"), n_modes=256)
    qdot = P / (math.pi * R**2 * L)
    for rho in (0.0, 0.3, 0.6, 0.9):
        exact = qdot * R**2 * (1.0 - rho**2) / (4.0 * K)
        assert math.isclose(float(sol.delta_t(rho * R, 0.5 * L)), exact, rel_tol=1e-6)
    # z-independence (insulated ends): same profile at any height
    assert math.isclose(
        float(sol.delta_t(0.3 * R, 0.1 * L)),
        float(sol.delta_t(0.3 * R, 0.9 * L)),
        rel_tol=1e-12,
    )
    assert math.isclose(sol.peak_k, P / (4.0 * math.pi * K * L), rel_tol=1e-6)
    assert math.isclose(sol.volume_average_k(), qdot * R**2 / (8.0 * K), rel_tol=1e-6)


# --- anchor (ii): 1-D axial slab ---------------------------------------------


def test_anchor_ii_axial_slab_uniform():
    """Side + top insulated (exact Bi = 0 branch), base Dirichlet, uniform g:
    only the constant radial mode survives (flood fₙ ∝ J₁(j₁,ₙ) = 0 exactly)
    and ΔT(z) = (q̇/2k_z)(L² − z²), peak q̇L²/(2k_z) = PL/(2πR²k_z)."""
    spec = CylinderSpec(
        R, L, K, SurfaceBC.robin(0.0), SurfaceBC.robin(0.0), SurfaceBC.dirichlet()
    )
    sol = solve(spec, PumpSource(P, "uniform", "flood"), n_modes=8)
    qdot = P / (math.pi * R**2 * L)
    for zf in (0.0, 0.25, 0.7):
        exact = (qdot / (2.0 * K)) * (L**2 - (zf * L) ** 2)
        # r-independent: evaluate off-axis to exercise the radial sum too
        assert math.isclose(float(sol.delta_t(0.4 * R, zf * L)), exact, rel_tol=1e-12)
    assert math.isclose(sol.peak_k, P * L / (2.0 * math.pi * R**2 * K), rel_tol=1e-12)


def test_anchor_ii_axial_slab_beer_lambert():
    """Same slab, Beer-Lambert g. Independent derivation (by parts, as in
    layered.anchor_one_dimensional_volumetric but re-derived for the full
    slab): flux φ(z) = q₀·(1−e^(−z/l))/c with q₀ = P/(πR²), c = 1−e^(−L/l);
    ΔT(0) = ∫₀ᴸ φ/k_z dz = (q₀/k_z c)·[L − l·c], i.e. (P/(πR²k_z))(L−l·c)/c."""
    spec = CylinderSpec(
        R, L, K, SurfaceBC.robin(0.0), SurfaceBC.robin(0.0), SurfaceBC.dirichlet()
    )
    l_abs = 200e-6
    sol = solve(spec, PumpSource(P, "beer_lambert", "flood", l_abs_m=l_abs), n_modes=8)
    c = -math.expm1(-L / l_abs)
    exact = (P / (math.pi * R**2 * K)) * (L - l_abs * c) / c
    assert math.isclose(sol.peak_k, exact, rel_tol=1e-12)
    # the positive modes carry nothing: the convergence tail is nil
    assert sol.tail_estimate_rel("volume_average") < 1e-12


# --- anchor (iii): energy conservation ----------------------------------------


ROBIN_SPEC = CylinderSpec(
    R, L, K, SurfaceBC.robin(10.0), SurfaceBC.robin(15.0), SurfaceBC.robin(25.0)
)
BL_FLOOD = PumpSource(P, "beer_lambert", "flood", l_abs_m=100e-6)


def test_anchor_iii_energy_conservation_robin_sides():
    """Flood + Beer-Lambert, Robin everywhere: Σ boundary fluxes = P.
    Deficit < 1e-6 rel at N = 64 — a ROBIN-SIDE level (deficit tail
    ~ Bi_s²/N³, ≈ 5e-8·Bi_s² at N = 64); see the Dirichlet-side test below
    for the contrast — and shrinks monotonically as N doubles."""
    deficits = []
    for n in (16, 32, 64, 128):
        bp = solve(ROBIN_SPEC, BL_FLOOD, n_modes=n).boundary_power_w()
        deficits.append((P - bp["total"]) / P)
    assert all(d > 0 for d in deficits)
    assert deficits[2] < 1e-6
    assert deficits[0] > deficits[1] > deficits[2] > deficits[3]


def test_energy_dirichlet_side_flood_monotone_only():
    """Dirichlet-side flood: captured power per mode is 4P/xₙ² (Σ 4/j₀,ₙ² = 1),
    so the deficit decays only ~1/N — ≈ 0.6% at N = 64, four orders above the
    Robin-side level. That slow tail is truncation of the flood source's
    radial expansion, NOT a broken anchor: this config gets (and pins) the
    monotone-decrease assertion only. boundary_power_w() docstring carries
    the same caveat so config-(i)-style runs don't read as broken."""
    spec = CylinderSpec(
        R, L, K, SurfaceBC.dirichlet(), SurfaceBC.robin(0.0), SurfaceBC.robin(0.0)
    )
    src = PumpSource(P, "uniform", "flood")
    deficits = []
    for n in (32, 64, 128):
        bp = solve(spec, src, n_modes=n).boundary_power_w()
        deficits.append((P - bp["total"]) / P)
    assert deficits[0] > deficits[1] > deficits[2] > 0
    assert 1e-4 < deficits[1] < 0.02  # the ~0.6%-at-N=64 scale, pinned
    assert 1.8 < deficits[1] / deficits[2] < 2.2  # ∝ 1/N


# --- anchor (iv): Robin → Dirichlet continuity, h monotonicity -----------------


def test_anchor_iv_bi_ladder_approaches_dirichlet():
    """Config (i) with finite side Bi ∈ {1e2, 1e3, 1e4, 1e6}: peak strictly
    decreasing in Bi (more cooling), error vs the exact-Dirichlet peak
    strictly decreasing and first-order in 1/Bi."""
    spec_d = CylinderSpec(
        R, L, K, SurfaceBC.dirichlet(), SurfaceBC.robin(0.0), SurfaceBC.robin(0.0)
    )
    src = PumpSource(P, "uniform", "flood")
    peak_d = solve(spec_d, src, n_modes=64).peak_k
    peaks, errs = [], []
    for bi in (1e2, 1e3, 1e4, 1e6):
        spec = CylinderSpec(
            R,
            L,
            K,
            SurfaceBC.robin(bi * K / R),
            SurfaceBC.robin(0.0),
            SurfaceBC.robin(0.0),
        )
        pk = solve(spec, src, n_modes=64).peak_k
        peaks.append(pk)
        errs.append(abs(pk - peak_d))
    assert all(a > b for a, b in zip(peaks, peaks[1:]))
    assert all(a > b for a, b in zip(errs, errs[1:]))
    assert 9.0 < errs[0] / errs[1] < 11.0  # ∝ 1/Bi


def test_anchor_iv_h_top_monotonicity():
    """Robin-h monotonicity at fixed source: peak ΔT strictly decreasing in
    h_top (the §7.T4-style acceptance item)."""
    peaks = []
    for h in (0.0, 5.0, 10.0, 20.0):
        spec = CylinderSpec(
            R, L, K, SurfaceBC.robin(10.0), SurfaceBC.robin(h), SurfaceBC.dirichlet()
        )
        peaks.append(solve(spec, BL_FLOOD, n_modes=64).peak_k)
    assert all(a > b for a, b in zip(peaks, peaks[1:]))


# --- anchor (v): cross-check vs the layered/Hankel machinery -------------------


def test_anchor_v_layered_cross_check():
    """Common regime of the two INDEPENDENT solvers: a laterally-unbounded
    slab ≈ a wide cylinder. Layered: single Layer(t = 0.5 mm plate, K) on an
    isothermal base, Gaussian w = 100 µm (w/t = 0.2), Beer-Lambert
    l_abs = 200 µm, h_top ∈ {0, composed Robin}. Cylinder: same k, L = t,
    Dirichlet base, Dirichlet side at R = 10t — legitimate because the
    lateral far field decays as e^(−πr/(2t)): the slowest lateral mode under
    an insulated top + Dirichlet base is the quarter-wave cos(πz/(2t)), so
    the side-wall suppression at R = 10t is e^(−5π) ≈ 1.5e-7, nil (with the
    Robin top the decay constant sits between π/(2t) and π/t, so the
    suppression is ≥ e^(−5π)). N = 300 — deliberately the narrow-source
    slow regime (ω = w/R = 0.02), showing it converges when paid for.

    Expected agreement ≲ 1e-5 (assert ≤ 1e-4). Measured ≈ 8.5e-6, and the
    residual sits on the LAYERED side: the cylinder value is stable to
    1e-10 under N = 300 → 500, a 4× denser projection rule, and R = 10t →
    14t, so the difference is the layered solver's quadrature chain."""
    t = RIG_GEOMETRY.t_plate_m  # 0.5 mm plate — the rig-geometry scale
    w, l_abs = 100e-6, 200e-6  # w inside the RigSampleGeometry box; L_ABS grid point
    h_robin = h_top_with_radiation(
        H_CONV_AIR.h_band_hi_w_m2_k, EMISSIVITY_PTP.eps_nominal, 300.0
    )
    src = PumpSource(P, "beer_lambert", "gaussian", l_abs_m=l_abs, gaussian_w_m=w)
    for h_top in (0.0, h_robin):
        ref = delta_t_gaussian_volumetric(0.0, (Layer(t, K),), P, w, l_abs, h_top=h_top)
        spec = CylinderSpec(
            10 * t, t, K, SurfaceBC.dirichlet(), SurfaceBC.robin(h_top), SurfaceBC.dirichlet()
        )
        got = float(solve(spec, src, n_modes=300).delta_t(0.0, 0.0))
        assert abs(got - ref) / ref <= 1e-4


# --- anisotropy: stretch identity ----------------------------------------------


def test_anisotropy_stretch_identity():
    """Native (k_r, k_z) solve == isotropic-k_r solve on the stretched
    problem — exact, independent algebra for the anisotropic wiring (D6).
    With s = √(k_r/k_z): z̃ = s·z, L̃ = s·L, l̃ = s·l, h̃_top/base = s·h
    AND P̃ = s·P — the stretch dilates the deposition length, so matching
    the volumetric density needs s× the power (check: the 1-D slab peak
    P̃L̃/(2πR²k_r) = PL/(2πR²k_z) forces P̃ = s·P). Side h and k_r untouched."""
    k_r, k_z = K, K / 2.0  # the K_PTP ~2× anisotropy scale as a knob
    s = math.sqrt(k_r / k_z)
    l_abs = 500e-6
    h_side, h_top, h_base = 7.0, 12.0, 30.0
    nat = solve(
        CylinderSpec(
            R,
            L,
            k_r,
            SurfaceBC.robin(h_side),
            SurfaceBC.robin(h_top),
            SurfaceBC.robin(h_base),
            k_z_w_m_k=k_z,
        ),
        PumpSource(P, "beer_lambert", "flood", l_abs_m=l_abs),
        n_modes=48,
    )
    stretched = solve(
        CylinderSpec(
            R,
            L * s,
            k_r,
            SurfaceBC.robin(h_side),
            SurfaceBC.robin(h_top * s),
            SurfaceBC.robin(h_base * s),
        ),
        PumpSource(P * s, "beer_lambert", "flood", l_abs_m=l_abs * s),
        n_modes=48,
    )
    for rf, zf in ((0.0, 0.0), (0.5, 0.3), (0.9, 0.9), (0.3, 1.0)):
        a = float(nat.delta_t(rf * R, zf * L))
        b = float(stretched.delta_t(rf * R, zf * L * s))
        assert math.isclose(a, b, rel_tol=1e-12)


# --- continuity and regression bridges ------------------------------------------


def test_bi_side_continuity_at_zero():
    """Bi_s = 1e-10 (root branch, x₁ ≈ √(2·Bi)) ≈ exact Bi_s = 0 branch
    (constant mode + J₁ zeros): the two eigenbasis representations agree."""
    src = PumpSource(P, "beer_lambert", "flood", l_abs_m=200e-6)
    top, base = SurfaceBC.robin(0.0), SurfaceBC.dirichlet()
    tiny = solve(
        CylinderSpec(R, L, K, SurfaceBC.robin(1e-10 * K / R), top, base), src, n_modes=32
    )
    exact = solve(
        CylinderSpec(R, L, K, SurfaceBC.robin(0.0), top, base), src, n_modes=32
    )
    assert math.isclose(tiny.peak_k, exact.peak_k, rel_tol=1e-7)


BRIDGE_SPEC = CylinderSpec(
    R, L, K, SurfaceBC.robin(10.0), SurfaceBC.robin(5.0), SurfaceBC.dirichlet()
)


def test_l_abs_to_zero_bridge():
    """Beer-Lambert → the exact surface-flux form linearly in l_abs (the
    regression bridge, mirroring test_thermal_volumetric's)."""
    surf = solve(BRIDGE_SPEC, PumpSource(P, "surface", "flood"), n_modes=48).peak_k
    d1 = (
        solve(
            BRIDGE_SPEC,
            PumpSource(P, "beer_lambert", "flood", l_abs_m=L / 1000),
            n_modes=48,
        ).peak_k
        - surf
    )
    d2 = (
        solve(
            BRIDGE_SPEC,
            PumpSource(P, "beer_lambert", "flood", l_abs_m=L / 2000),
            n_modes=48,
        ).peak_k
        - surf
    )
    assert abs(d1) / surf < 5e-3
    assert 1.98 < d1 / d2 < 2.02  # first-order in l_abs


def test_l_abs_large_bridge():
    """l_abs ≫ L: Beer-Lambert → the uniform-g result, first-order in L/l."""
    unif = solve(BRIDGE_SPEC, PumpSource(P, "uniform", "flood"), n_modes=48).peak_k
    e1 = (
        solve(
            BRIDGE_SPEC,
            PumpSource(P, "beer_lambert", "flood", l_abs_m=100 * L),
            n_modes=48,
        ).peak_k
        - unif
    )
    e2 = (
        solve(
            BRIDGE_SPEC,
            PumpSource(P, "beer_lambert", "flood", l_abs_m=200 * L),
            n_modes=48,
        ).peak_k
        - unif
    )
    assert abs(e1) / unif < 5e-3
    assert 1.99 < e1 / e2 < 2.01  # first-order in 1/l_abs


def test_confluent_branch_straddle():
    """The Beer-Lambert particular solution switches to the confluent
    z·e^(−z/l) branch at |mₙ·ℓ − 1| < 1e-6 (denominator kept in the FACTORED
    form (mₙ − 1/ℓ)(mₙ + 1/ℓ) outside it). Straddle the branch point with
    mode 1: values must be finite and continuous across the switch."""
    bi_s = 10.0 * R / K
    x1 = robin_radial_eigenvalues(bi_s, 1)[0]
    ell_c = 1.0 / ((L / R) * x1)  # mode-1 confluence, isotropic
    spec = CylinderSpec(
        R, L, K, SurfaceBC.robin(10.0), SurfaceBC.robin(5.0), SurfaceBC.dirichlet()
    )

    def peak(fac: float, expect_confluent: bool) -> float:
        sol = solve(
            spec,
            PumpSource(P, "beer_lambert", "flood", l_abs_m=ell_c * L * fac),
            n_modes=32,
        )
        # guard: the straddle must actually exercise both branches
        assert bool(sol._modes.confluent.any()) is expect_confluent
        assert np.isfinite(sol.peak_k)
        return sol.peak_k

    exact = peak(1.0, True)
    for fac, conf in ((1 - 5e-7, True), (1 + 5e-7, True), (1 - 2e-6, False), (1 + 2e-6, False)):
        assert abs(peak(fac, conf) - exact) / exact < 2e-6  # measured ≤ 4.7e-7


# --- truncation behaviour ---------------------------------------------------------


def test_convergence_under_mode_doubling():
    """Pinned scalars stable as N doubles: flood (Robin side) and a Gaussian
    with ω = w/R = 0.25 (modes needed only up to xₙ ≲ 17.2/ω ≈ 69, i.e.
    N ≈ 22 — N = 64 vs 128 is deep in the converged regime). The
    per-solution tail estimate agrees that N = 64 is converged."""
    gauss = PumpSource(
        P, "beer_lambert", "gaussian", l_abs_m=100e-6, gaussian_w_m=0.25 * R
    )
    for src in (BL_FLOOD, gauss):
        s64 = solve(ROBIN_SPEC, src, n_modes=64)
        s128 = solve(ROBIN_SPEC, src, n_modes=128)
        assert abs(s128.peak_k - s64.peak_k) / s64.peak_k < 1e-6
        assert (
            abs(s128.volume_average_k() - s64.volume_average_k())
            / s64.volume_average_k()
            < 1e-6
        )
        assert s64.tail_estimate_rel("peak") < 1e-6
        assert s64.tail_estimate_rel("volume_average") < 1e-6


def test_volume_average_segment_additivity():
    """Closed-form segment integrals: equal-height halves average to the
    whole (exact identity), and the top-heated half is the hotter one."""
    sol = solve(ROBIN_SPEC, BL_FLOOD, n_modes=64)
    whole = sol.volume_average_k()
    top_half = sol.volume_average_k(z_lo_m=0.0, z_hi_m=L / 2)
    bottom_half = sol.volume_average_k(z_lo_m=L / 2, z_hi_m=L)
    assert math.isclose(whole, 0.5 * (top_half + bottom_half), rel_tol=1e-12)
    assert top_half > bottom_half


# --- maser-crystal worked example (graded constants only) -------------------------


def test_maser_worked_example_graded_inputs():
    """The anchor at the geometry it exists for, from graded constants ONLY
    (§6T "no fresh literals" enforced by example): CRYSTAL dims, K_PTP band
    midpoint, h = h_conv + h_rad composed from H_CONV_AIR (band-high) and
    EMISSIVITY_PTP at the 300 K radiation.py convention, l_abs from the
    L_ABS_PUMP scoping grid (UNSOURCED-SCOPING — test/scoping use only,
    never an absolute prediction), P = 1 W scale-free. BCs are the D1
    worked-example planning assumption: Dirichlet base ("substrate below at
    room temperature"), Robin(h_conv + h_rad) side and top. Values are
    REGRESSION PINS of this solver, not physical claims — no observable-(b)
    prediction is made here (that run is downstream, per the model-boundary
    note in SPEC §7.T5)."""
    h_eff = h_top_with_radiation(
        H_CONV_AIR.h_band_hi_w_m2_k, EMISSIVITY_PTP.eps_nominal, 300.0
    )
    spec = CylinderSpec(
        CRYSTAL.diameter_m / 2.0,
        CRYSTAL.height_m,
        K_PTP.k_mid_w_m_k,
        SurfaceBC.robin(h_eff),
        SurfaceBC.robin(h_eff),
        SurfaceBC.dirichlet(),
    )
    src = PumpSource(
        1.0, "beer_lambert", "flood", l_abs_m=L_ABS_PUMP.l_abs_scoping_grid_m[5]
    )
    sol = solve(spec, src, n_modes=64)
    assert math.isclose(sol.peak_k, 1.057203696e3, rel_tol=1e-6)
    assert math.isclose(sol.volume_average_k(), 3.703239268e2, rel_tol=1e-6)
    bp = sol.boundary_power_w()
    assert abs(1.0 - bp["total"]) < 1e-6
    # where the heat leaves (regression pin of the split, top/base/side)
    assert math.isclose(bp["top"], 0.18579, rel_tol=1e-3)
    assert math.isclose(bp["base"], 0.12272, rel_tol=1e-3)
    assert math.isclose(bp["side"], 0.69150, rel_tol=1e-3)
    # peak-location assumption (top-heated, base/side-sunk): (0, 0) is max
    r_grid = np.linspace(0.0, spec.radius_m, 7)
    z_grid = np.linspace(0.0, spec.height_m, 9)
    field = sol.delta_t(r_grid[None, :], z_grid[:, None])
    assert sol.peak_k >= field.max() - 1e-12


# --- API contracts -----------------------------------------------------------------


def test_delta_t_vectorised_and_domain_checked():
    sol = solve(ROBIN_SPEC, BL_FLOOD, n_modes=16)
    out = sol.delta_t(np.array([0.0, 0.5 * R, R]), 0.25 * L)
    assert out.shape == (3,)
    assert np.all(np.diff(out) < 0)  # centre-heated: decreasing outward
    with pytest.raises(ValueError):
        sol.delta_t(1.1 * R, 0.0)
    with pytest.raises(ValueError):
        sol.delta_t(0.0, -0.1 * L)
    with pytest.raises(ValueError):
        sol.tail_estimate_rel("nonsense")


def test_error_paths():
    robin0 = SurfaceBC.robin(0.0)
    with pytest.raises(ValueError, match="insulated"):
        CylinderSpec(R, L, K, robin0, robin0, robin0)
    with pytest.raises(ValueError, match="Dirichlet"):
        solve(
            CylinderSpec(R, L, K, robin0, SurfaceBC.dirichlet(), robin0),
            PumpSource(P, "surface", "flood"),
        )
    with pytest.raises(ValueError):
        PumpSource(P, "uniform", "flood", l_abs_m=1e-4)  # stray l_abs
    with pytest.raises(ValueError):
        PumpSource(-1.0, "uniform", "flood")
    with pytest.raises(ValueError):
        PumpSource(P, "beer_lambert", "flood")  # missing l_abs
    with pytest.raises(ValueError):
        SurfaceBC.robin(-1.0)
    with pytest.raises(ValueError):
        SurfaceBC(kind="dirichlet", h_w_m2_k=5.0)
    with pytest.raises(ValueError, match="exceeds"):
        solve(
            CylinderSpec(R, L, K, robin0, robin0, SurfaceBC.dirichlet()),
            PumpSource(P, "uniform", "disc", disc_radius_m=2.0 * R),
        )
    with pytest.raises(ValueError):
        solve(BRIDGE_SPEC, BL_FLOOD, n_modes=3)
    # Dirichlet top pins ΔT(0,0) = 0: the peak-based tail estimate is NaN
    sol = solve(
        CylinderSpec(R, L, K, robin0, SurfaceBC.dirichlet(), SurfaceBC.dirichlet()),
        BL_FLOOD,
        n_modes=16,
    )
    assert math.isnan(sol.tail_estimate_rel("peak"))
