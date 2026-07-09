"""SPEC §7.T5(b) — differential-detuning integration + §7.T4 budget maps.

First wiring of the two BUILT-but-unwired pieces into Δf numbers for our
geometry: the §7.T5(b) weight machinery (`cavity.extraction.weights`) and
the maser-cylinder ΔT(r, z) transport core (`cavity.thermal.cylinder`),
composed through `cavity.thermal.broadening`'s geometry-agnostic
observable map. Everything here is a pure function of
(field-or-samples, probe measure, coefficients, base temperature) —
no solver state, no caching, and NO fresh physics literals: every
coefficient resolves at call time from `cavity.provenance.constants`
(C, T0_CW, the validity floor, f, DELOAD_K, CRYSTAL dims, the df/dT
points and bands), exactly the `broadening.py` convention.

Cavity arm — integrated Curie-Weiss map (NOT coefficient x <ΔT>)
================================================================
SPEC §6T rules the form: the df_cavity/dT slope is LOCAL (+6%/-15%
across 293-323 K) and "budget arithmetic over the full envelope should
integrate, not multiply" — the ruled 30 K envelope sits exactly in the
integrate regime. Adopted map, exactly:

pointwise, under the pure Curie-Weiss law eps_r = C/(T - T0_CW), the
local permittivity RATIO is C-independent:

    rho(x) = eps_r(T_base + ΔT(x)) / eps_r(T_base)
           = (T_base - T0_CW) / (T_base + ΔT(x) - T0_CW);

the Bethe-Schwinger perturbation integral is linear in Δeps, so the
rigorous first-order spatial object is the weighted mean <rho>_w (the
weight-centered fluctuation contributes exactly zero at first order);
the bulk change is resummed exactly through d ln f = -(p_e/2) d ln eps_r:

    Δf_cav = f * ( <rho>_w^(-p_e/2) - 1 ).

Uniform-ΔT limit: Δf_cav = f * (u^p_e - 1) with
u = sqrt((T2 - T0_CW)/(T1 - T0_CW)) — the exponentiated §6T closed form
(Δf/f = (1/2) ln((T2-T0)/(T1-T0)), resummed). ΔT -> 0 limit: the
pure-CW local slope f*p_e/(2*(T_base - T0_CW)).

Branch choices, stated (re-grade discipline; pinned in
tests/test_thermal_detuning.py):

1. RESUMMED RATIO over first-order integral of the committed slope
   function: integrating `cavity_df_dt_hz_per_k` over 293->323 gives
   ~77.5 MHz; the resummed form gives ~82.6 MHz (~+7%). Adopted because
   f ∝ eps_r^(-1/2) is the exact scaling law and first-order is its
   truncation; the difference is pinned (anchor A10) and must ride any
   envelope-wide headline number.
2. SELF-CONSISTENT CW eps_r(T_base) over canonical 316.3 in the
   denominator (this is what makes C cancel — only T0_CW, f, p_e
   enter). Consequence, exact identity (anchor C3):
   cavity_df_dt_hz_per_k(T) == [f/(2(T - T0_CW))] * eps_CW(T)/eps_canon,
   so this map's ΔT->0 slope sits eps_CW(T_base)/eps_canon from the
   committed §6T point function — +1.9% at 293 K, +0.8% at 300 K (the
   documented "harmless at band resolution" mixing; it grows to ~-9% by
   323 K, where the committed function's fixed canonical eps_r is the
   stale side — this map is always based at the operating baseline).

Spin arm — uniform coefficient (point + band), deliberately
===========================================================
Δf_spin = df_spin/dT * <ΔT>_probe and width = |df_spin/dT| * sigma_T,
via `broadening.line_observable_from_samples` unchanged. No pointwise
T-integration: (i) heating from 293 K moves AWAY from the 193 K
transition (Lang's steepening is toward cold) and 30 K sliding windows
on the Singh raw series stay inside the carried band over 293-323 K;
(ii) the spin arm is ~4% of the differential — curvature there is
invisible against the cavity band; (iii) the dominant df_spin/dT
uncertainty is the x1.7 temperature-axis branch systematic (it IS the
band) — a pointwise refinement would be precision the provenance
cannot support. Revisit if the axis ask resolves.

Two-arms/one-temperature convention (D8 — planning assumption)
==============================================================
Layer C's ΔT_max = Δf_max / |df_cav/dT - df_spin/dT| puts BOTH arms at
one ΔT. Here both arms are evaluated at the crystal's probe-weighted
mean rise <ΔT>_probe, because the crystal->STO thermal path is
unmodelled (D7, `cavity.thermal.cylinder`) — no ΔT_STO field exists.
Direction: conservative — ΔT_STO <= ΔT_crystal at steady state and the
cavity arm dominates, so this OVERSTATES detuning per unit crystal
heating and UNDERSTATES ΔT_max / P_max. Magnitude unmodelled.
Retirement: model D7, or a ruled ΔT_STO/ΔT_crystal ratio (Oxborrow —
SPEC §11 item-10 bundle, D8). Carried as `COMMON_DELTA_T_NOTE` in every
result's `status_notes`.

Probe weight — uniform-over-crystal PLACEHOLDER this pass
=========================================================
The §7.T2 output-3 probe weight for the maser is w_s by construction
(`WeightField.probe_measure()` is the designed `weights` argument of
`line_observable_from_samples`). But today's w_s lives on the
STO-fallback mask in cavity coordinates (Phase 1b bore + crystal
unbuilt) — disjoint from the crystal domain — so the shipped instance
uses a uniform-over-crystal probe measure, flagged in every result
(`probe_weight_is_placeholder`, `UNIFORM_PLACEHOLDER_RUNG`). The
signatures take any per-node probe measure; Phase 1b supplies the real
w_s via a crystal-frame <-> cavity-frame co-registration transform, and
nothing here changes shape. Any Δf_spin produced meanwhile inherits
UNRATIFIED-w_s status doubly (placeholder now, unratified projection
after Phase 1b) — rung strings below mirror `cavity.export.writer`.

§7.T4 budget maps and the inversion-consistency amendment (2026-07-09)
======================================================================
Δf_max(C0, kappa_c) = (kappa_c/2) * sqrt(C0 - 1), from the Lorentzian
roll-off C(Δ) = C0 / (1 + (2Δ/kappa_c)^2). UNIT CONVENTION, pinned
against the provenance table's verified W20 angular-"Hz" trap:
kappa_c here is the CYCLIC-Hz FWHM linewidth f/Q_L
(`broadening.resonance_linewidth_hz`), NEVER the angular 2*pi*f/Q_L —
feeding rad/s inflates Δf_max by 2*pi (anchor A6).

`delta_t_max_k` inverts the TRUE differential map
D(u) = f*(u^p_e - 1) + s*tau*(u^2 - 1), u = sqrt(1 + ΔT/tau),
tau = T_base - T0_CW, s = |df_spin/dT| — the same u^p_e map anchor A2
pins as the uniform-ΔT truth. AMENDMENT BRANCH (b): the closed-form
quadratic solves only the p_e-LINEARISED companion (cavity term
f*p_e*(u-1)) as a SEED — its deviation from the true map is second
order, f*p_e*(p_e-1)/2*(u-1)^2 (~ppm of f at the 30 K envelope; pinned,
anchor A4) — and ONE Newton step against the true map follows, driving
the round-trip residual below 1e-9 relative (quadratic convergence from
a <=ppm seed). A2 and A4 therefore pin the SAME map: no exactness is
claimed for two non-identical maps.

Signs: the §6T convention |df_cav/dT - df_spin/dT| = df_cav/dT +
|df_spin/dT| (opposite signs, differential ADDS) is asserted —
`delta_t_max_k` requires df_spin_dt <= 0 (§6T: spins red-shift on
heating) and the cavity arm is positive by the CW law.

Evidence rungs composed here (carry into any writeup)
=====================================================
- w_s projection: |H|^2 default literature-backed; projected variants
  derived, UNRATIFIED — which mode headlines observable-(b) is an
  Oxborrow/literature item (`SPIN_WEIGHT_RUNG`, mirrors writer.py).
- Uniform probe placeholder: planning assumption, retired by Phase 1b.
- Common-ΔT convention: planning assumption D8, item-10 bundle.
- §7.T4: question endorsed (Oxborrow-verbal 2026-07-06); RESULT
  unratified — these maps are algebra + a planning point, not the
  joint C0/kappa_c DOF derivation (Layer A; SPEC §11 item 9).
- df_spin/dT: raw-data-graded, axis-branch band carried (§6T).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from cavity.extraction.quadrature import axisymmetric_node_volumes
from cavity.provenance.constants import (
    CRYSTAL,
    DELOAD_K,
    DF_CAVITY_DT,
    DF_SPIN_DT,
    TARGET,
)
from cavity.thermal.broadening import (
    ThermalLineObservable,
    line_observable_from_samples,
)
from cavity.thermal.cylinder import CylinderSolution

# Rung / status strings — writer.py-convention carriage (module docstring).
SPIN_WEIGHT_RUNG = (
    "isotropic |H|^2 default is literature-backed (Breeze 2017 npj QI 3, "
    "40; arXiv:2412.21166 practice); axis-projected variants implement "
    "Breeze's S_y statement — derived, unratified"
)

UNIFORM_PLACEHOLDER_RUNG = (
    "probe weight is a UNIFORM-OVER-CRYSTAL PLACEHOLDER, not the "
    "SPEC §7.T5(b) gain-region w_s (Phase 1b bore + crystal unbuilt; "
    "crystal-frame co-registration pending) — spin-arm numbers inherit "
    "UNRATIFIED-w_s status doubly until Phase 1b supplies w_s"
)

COMMON_DELTA_T_NOTE = (
    "COMMON-DELTA-T TWO-ARMS CONVENTION (D8, planning assumption — "
    "proposed for the SPEC §11 item-10 bundle): both arms evaluated at "
    "the crystal's probe-weighted mean temperature rise because the "
    "crystal->STO thermal path is unmodelled (D7). Direction "
    "conservative — overstates detuning, understates ΔT_max/P_max; "
    "magnitude unmodelled; retires via D7 or a ruled "
    "ΔT_STO/ΔT_crystal ratio."
)

Q_MARGIN_RUNG = (
    "SPEC §7.T4 rung: the Q-margin QUESTION is supervisor-endorsed "
    "(Oxborrow-verbal 2026-07-06); the RESULT is unratified — these are "
    "budget maps and a planning point, not the joint C0/kappa_c DOF "
    "derivation (Layer A; SPEC §11 item 9)"
)


@dataclass(frozen=True)
class CrystalProbeGrid:
    """Gauss-Legendre product grid over the crystal cylinder (r, z).

    `weights_m2` are the r-z plane quadrature weights (the same measure
    contract as `FieldSample.weights_m2`); the volume measure comes from
    `axisymmetric_node_volumes` so the 2*pi*r Jacobian enters in exactly
    one module (SPEC §3 discipline). Flattened 'ij': r varies slowest,
    matching the export-schema grid ordering.
    """

    r_m: NDArray[np.float64]
    z_m: NDArray[np.float64]
    weights_m2: NDArray[np.float64]
    radius_m: float
    height_m: float

    def __post_init__(self) -> None:
        n = self.r_m.shape[0]
        for name in ("z_m", "weights_m2"):
            arr = getattr(self, name)
            if arr.shape != (n,):
                raise ValueError(
                    f"{name} shape {arr.shape} must match r_m ({n},)"
                )
        if not (self.radius_m > 0.0 and self.height_m > 0.0):
            raise ValueError("grid extents must be positive")

    def node_volumes_m3(self) -> NDArray[np.float64]:
        """Per-node dV_i = 2*pi*r_i*w_i via the §3 primitive."""
        return axisymmetric_node_volumes(self.r_m, self.weights_m2)


def crystal_probe_grid(
    radius_m: float | None = None,
    height_m: float | None = None,
    n_r: int = 64,
    n_z: int = 64,
) -> CrystalProbeGrid:
    """GL product grid over the crystal; defaults = `CRYSTAL` (§5b dims)."""
    if radius_m is None:
        radius_m = CRYSTAL.diameter_m / 2.0
    if height_m is None:
        height_m = CRYSTAL.height_m
    if n_r < 2 or n_z < 2:
        raise ValueError("need at least 2 nodes per direction")
    xr, wr = np.polynomial.legendre.leggauss(n_r)
    xz, wz = np.polynomial.legendre.leggauss(n_z)
    r = 0.5 * radius_m * (xr + 1.0)
    z = 0.5 * height_m * (xz + 1.0)
    w_r = 0.5 * radius_m * wr
    w_z = 0.5 * height_m * wz
    r2d, z2d = np.meshgrid(r, z, indexing="ij")  # r varies slowest
    w2d = np.outer(w_r, w_z)
    return CrystalProbeGrid(
        r_m=r2d.ravel(),
        z_m=z2d.ravel(),
        weights_m2=w2d.ravel(),
        radius_m=float(radius_m),
        height_m=float(height_m),
    )


def uniform_probe_measure(grid: CrystalProbeGrid) -> NDArray[np.float64]:
    """The PLACEHOLDER probe measure: pi_i ∝ dV_i, normalised to sum 1.

    Volume-uniform probing of the crystal — NOT w_s (module docstring).
    Under it the probe-weighted mean is exactly the unweighted volume
    average, which is the anchor-A7 wiring identity against
    `CylinderSolution.volume_average_k`.
    """
    dv = grid.node_volumes_m3()
    return np.asarray(dv / dv.sum(), dtype=np.float64)


def cylinder_delta_t_samples(
    solution: CylinderSolution, grid: CrystalProbeGrid
) -> NDArray[np.float64]:
    """ΔT(r_i, z_i) on the grid nodes (K)."""
    return np.asarray(solution.delta_t(grid.r_m, grid.z_m), dtype=np.float64)


def cylinder_line_observable(
    solution: CylinderSolution,
    grid: CrystalProbeGrid,
    df_dt_hz_per_k: float | None = None,
    probe_measure: NDArray[np.float64] | None = None,
) -> ThermalLineObservable:
    """SPEC §7.T2 output 3, maser-cylinder instance.

    Depth-resolved from birth: the cylinder field is natively (r, z)-
    resolved and the probe measure is volumetric, so the rig instance's
    radial-only accuracy boundary does not apply here (it lives in
    `layered.py`'s surface evaluation, not in the observable map).
    Deposition-agnostic: end-fire Beer-Lambert (D2, ruled 2026-07-08)
    enters only through the solution. `probe_measure` defaults to the
    uniform placeholder; `df_dt_hz_per_k` defaults to the §6T
    `DF_SPIN_DT` point (band sweeps pass the band fields explicitly).
    """
    if df_dt_hz_per_k is None:
        df_dt_hz_per_k = DF_SPIN_DT.df_dt_hz_per_k
    if probe_measure is None:
        probe_measure = uniform_probe_measure(grid)
    return line_observable_from_samples(
        cylinder_delta_t_samples(solution, grid),
        probe_measure,
        df_dt_hz_per_k,
    )


# --- cavity arm -----------------------------------------------------------


def _cw_tau_k(t_base_k: float, curie_weiss_t0_k: float) -> float:
    if t_base_k < DF_CAVITY_DT.t_validity_floor_k:
        raise ValueError(
            f"t_base_k = {t_base_k} K is below the "
            f"{DF_CAVITY_DT.t_validity_floor_k} K phase transition; the "
            "paraelectric Curie-Weiss form is invalid there (SPEC §6T)."
        )
    return t_base_k - curie_weiss_t0_k


def cavity_arm_shift_hz(
    delta_t_k: NDArray[np.float64],
    probe_measure: NDArray[np.float64],
    t_base_k: float,
    *,
    f_hz: float | None = None,
    p_e: float = 1.0,
    curie_weiss_t0_k: float | None = None,
) -> float:
    """Weighted integrated-CW cavity shift (module docstring map).

    Δf_cav = f * (<rho>_w^(-p_e/2) - 1) with the pointwise ratio
    rho_i = (T_base - T0_CW)/(T_base + ΔT_i - T0_CW). C cancels; only
    T0_CW, f, p_e enter. Uniform samples reduce EXACTLY to
    `cavity_arm_shift_uniform_hz` (anchor A2). The weight for the
    §7.T5(b) cavity arm is w_E over an STO ΔT field — which does not
    exist yet (D7/D8); the common-ΔT instance feeds the probe-weighted
    scalar through `cavity_arm_shift_uniform_hz` instead.
    """
    if f_hz is None:
        f_hz = TARGET.f_design_hz
    if curie_weiss_t0_k is None:
        curie_weiss_t0_k = DF_CAVITY_DT.curie_weiss_t0_k
    tau = _cw_tau_k(t_base_k, curie_weiss_t0_k)
    dt = np.asarray(delta_t_k, dtype=float)
    wt = np.asarray(probe_measure, dtype=float)
    if dt.shape != wt.shape or dt.size == 0:
        raise ValueError("delta_t and probe_measure must be same-shape, non-empty")
    if np.any(wt < 0) or not np.sum(wt) > 0:
        raise ValueError("probe_measure must be non-negative with positive sum")
    local_t = t_base_k + dt
    if np.any(local_t < DF_CAVITY_DT.t_validity_floor_k):
        raise ValueError(
            "a local temperature falls below the 112 K validity floor "
            "(SPEC §6T) — the CW ratio map is invalid there"
        )
    rho = tau / (local_t - curie_weiss_t0_k)
    mean_rho = float(np.average(rho, weights=wt))
    return f_hz * (mean_rho ** (-0.5 * p_e) - 1.0)


def cavity_arm_shift_uniform_hz(
    delta_t_k: float,
    t_base_k: float,
    *,
    f_hz: float | None = None,
    p_e: float = 1.0,
    curie_weiss_t0_k: float | None = None,
) -> float:
    """Uniform-ΔT closed form: Δf_cav = f * (u^p_e - 1),
    u = sqrt((T_base + ΔT - T0_CW)/(T_base - T0_CW)) — the exponentiated
    §6T closed form; the anchor-A2 truth map and the map
    `delta_t_max_k` inverts (amendment branch (b))."""
    if f_hz is None:
        f_hz = TARGET.f_design_hz
    if curie_weiss_t0_k is None:
        curie_weiss_t0_k = DF_CAVITY_DT.curie_weiss_t0_k
    tau = _cw_tau_k(t_base_k, curie_weiss_t0_k)
    if t_base_k + delta_t_k < DF_CAVITY_DT.t_validity_floor_k:
        raise ValueError(
            "T_base + ΔT falls below the 112 K validity floor (SPEC §6T)"
        )
    u = math.sqrt((tau + delta_t_k) / tau)
    return f_hz * (u**p_e - 1.0)


# --- §7.T4 budget maps ----------------------------------------------------


def q_loaded(q_unloaded: float, coupling_k: float | None = None) -> float:
    """Q_L = Q0/(1 + k) — the §6 de-loading convention (DELOAD_K default)."""
    if coupling_k is None:
        coupling_k = DELOAD_K
    if not (q_unloaded > 0 and coupling_k >= 0):
        raise ValueError("need Q0 > 0 and k >= 0")
    return q_unloaded / (1.0 + coupling_k)


def delta_f_max_hz(c0: float, kappa_c_hz: float) -> float:
    """Δf_max = (kappa_c/2)*sqrt(C0 - 1) — Lorentzian threshold budget.

    kappa_c is the CYCLIC-Hz FWHM linewidth f/Q_L
    (`broadening.resonance_linewidth_hz`), never angular rad/s (the W20
    trap — module docstring; anchor A6). C0 <= 1 returns 0.0: a
    below-threshold draw has no thermal margin (the retargeted Layer C
    convention — no thresholding step, the margin is just zero).
    """
    if not kappa_c_hz > 0:
        raise ValueError("kappa_c must be positive (cyclic Hz, f/Q_L)")
    if c0 <= 1.0:
        return 0.0
    return 0.5 * kappa_c_hz * math.sqrt(c0 - 1.0)


def differential_detuning_hz(
    delta_t_k: float,
    t_base_k: float,
    *,
    f_hz: float | None = None,
    p_e: float = 1.0,
    df_spin_dt_hz_per_k: float | None = None,
    curie_weiss_t0_k: float | None = None,
) -> float:
    """Common-ΔT differential |Δf_cav - Δf_spin| = Δf_cav + |c_s|*ΔT.

    The scalar forward map `delta_t_max_k` inverts: integrated-CW cavity
    arm (u^p_e truth map) + linear spin arm, both at one ΔT (D8 —
    module docstring). Requires df_spin_dt <= 0 (§6T sign convention:
    the arms ADD; a positive coefficient would subtract and the
    closed-form inversion below would not apply).
    """
    if df_spin_dt_hz_per_k is None:
        df_spin_dt_hz_per_k = DF_SPIN_DT.df_dt_hz_per_k
    if df_spin_dt_hz_per_k > 0:
        raise ValueError(
            "df_spin_dt > 0 contradicts the §6T sign convention "
            "(spins red-shift on heating; the differential adds)"
        )
    if delta_t_k < 0:
        raise ValueError("delta_t_k must be non-negative")
    cav = cavity_arm_shift_uniform_hz(
        delta_t_k,
        t_base_k,
        f_hz=f_hz,
        p_e=p_e,
        curie_weiss_t0_k=curie_weiss_t0_k,
    )
    return cav + abs(df_spin_dt_hz_per_k) * delta_t_k


def delta_t_max_k(
    delta_f_max_hz_value: float,
    t_base_k: float,
    *,
    f_hz: float | None = None,
    p_e: float = 1.0,
    df_spin_dt_hz_per_k: float | None = None,
    curie_weiss_t0_k: float | None = None,
) -> float:
    """Invert `differential_detuning_hz` for the thermal budget ΔT_max.

    Amendment branch (b), module docstring: closed-form quadratic seed
    on the p_e-linearised cavity term (Citardauq form, cancellation-
    safe), then ONE Newton step against the TRUE u^p_e map. Seed
    deviation is second order (f*p_e*(p_e-1)/2*(u-1)^2, ~ppm of f at
    the 30 K envelope); after the Newton step the round-trip residual
    is below 1e-9 relative across the envelope (anchor A4).
    """
    if f_hz is None:
        f_hz = TARGET.f_design_hz
    if curie_weiss_t0_k is None:
        curie_weiss_t0_k = DF_CAVITY_DT.curie_weiss_t0_k
    if df_spin_dt_hz_per_k is None:
        df_spin_dt_hz_per_k = DF_SPIN_DT.df_dt_hz_per_k
    if df_spin_dt_hz_per_k > 0:
        raise ValueError(
            "df_spin_dt > 0 contradicts the §6T sign convention "
            "(spins red-shift on heating; the differential adds)"
        )
    if delta_f_max_hz_value < 0:
        raise ValueError("delta_f_max must be non-negative")
    if delta_f_max_hz_value == 0.0:
        return 0.0
    tau = _cw_tau_k(t_base_k, curie_weiss_t0_k)
    s = abs(df_spin_dt_hz_per_k)
    b = f_hz * p_e
    df = delta_f_max_hz_value

    # quadratic seed: s*tau*u^2 + b*u - (df + s*tau + b) = 0, root > 1
    rhs = df + s * tau + b
    if s > 0.0:
        disc = math.sqrt(b * b + 4.0 * s * tau * rhs)
        u = 2.0 * rhs / (b + disc)  # Citardauq: no b - sqrt cancellation
    else:
        u = 1.0 + df / b  # p_e-linearised, cavity-only

    # one Newton step against the true map (branch (b))
    g = f_hz * (u**p_e - 1.0) + s * tau * (u * u - 1.0) - df
    g_prime = f_hz * p_e * u ** (p_e - 1.0) + 2.0 * s * tau * u
    u -= g / g_prime
    return tau * (u * u - 1.0)


def p_max_w(
    solution: CylinderSolution,
    grid: CrystalProbeGrid,
    delta_t_max_k_value: float,
    probe_measure: NDArray[np.float64] | None = None,
) -> float:
    """Pump-power budget P_max = P_ref * ΔT_max / <ΔT>_probe(P_ref).

    Exact by the transport core's linearity in P (`cylinder.py`:
    "ΔT is exactly linear in the pump power P"). The governing
    statistic is the probe-weighted mean — the same convention as the
    common-ΔT differential (D8).
    """
    if delta_t_max_k_value < 0:
        raise ValueError("delta_t_max must be non-negative")
    if probe_measure is None:
        probe_measure = uniform_probe_measure(grid)
    dt = cylinder_delta_t_samples(solution, grid)
    mean_dt = float(np.average(dt, weights=probe_measure))
    if not mean_dt > 0:
        raise ValueError("probe-weighted mean ΔT must be positive")
    return solution.source.p_w * delta_t_max_k_value / mean_dt


# --- composed result ------------------------------------------------------


@dataclass(frozen=True)
class DifferentialDetuning:
    """Composed §7.T5(b) result. EVERY field is required — a result
    cannot be constructed without its ratification flags (anchor A11).

    `delta_f_differential_hz` = delta_f_cavity_hz - delta_f_spin_hz
    (opposite §6T signs ⇒ the arms add). `spin_projection` is
    `SpinProjection.to_meta()` when a real w_s probe measure was
    supplied, None under the uniform placeholder.
    `gain_mask_is_fallback` is None under the placeholder (no gain mask
    was involved at all)."""

    t_base_k: float
    mean_delta_t_k: float
    rms_delta_t_k: float
    delta_f_cavity_hz: float
    delta_f_spin_hz: float
    inhom_width_hz: float
    delta_f_differential_hz: float
    f_hz: float
    p_e: float
    df_spin_dt_hz_per_k: float
    probe_weight_is_placeholder: bool
    spin_projection: dict | None
    gain_mask_is_fallback: bool | None
    spin_weight_rung: str
    status_notes: tuple[str, ...]


def differential_detuning_from_samples(
    delta_t_k: NDArray[np.float64],
    probe_measure: NDArray[np.float64],
    t_base_k: float,
    *,
    f_hz: float | None = None,
    p_e: float = 1.0,
    df_spin_dt_hz_per_k: float | None = None,
    curie_weiss_t0_k: float | None = None,
    probe_weight_is_placeholder: bool = True,
    spin_projection: dict | None = None,
    gain_mask_is_fallback: bool | None = None,
) -> DifferentialDetuning:
    """Geometry-agnostic composed observable from weighted ΔT samples.

    Spin arm: `line_observable_from_samples` (mean shift + width).
    Cavity arm: the integrated-CW closed form at the probe-weighted
    mean rise — the common-ΔT convention (D8, module docstring), NOT a
    w_E-weighted STO field (none exists; D7). Supplying a real w_s
    probe measure requires `probe_weight_is_placeholder=False` plus its
    `spin_projection` meta and `gain_mask_is_fallback` flag (writer.py
    convention); the placeholder default carries the placeholder rung.
    """
    if f_hz is None:
        f_hz = TARGET.f_design_hz
    if df_spin_dt_hz_per_k is None:
        df_spin_dt_hz_per_k = DF_SPIN_DT.df_dt_hz_per_k
    if not probe_weight_is_placeholder and spin_projection is None:
        raise ValueError(
            "a real (non-placeholder) probe weight must carry its "
            "SpinProjection meta (writer.py convention)"
        )
    if probe_weight_is_placeholder and spin_projection is not None:
        raise ValueError(
            "the uniform placeholder has no SpinProjection — "
            "pass probe_weight_is_placeholder=False with a real w_s"
        )

    spin = line_observable_from_samples(
        delta_t_k, probe_measure, df_spin_dt_hz_per_k
    )
    cav = cavity_arm_shift_uniform_hz(
        spin.mean_delta_t_k,
        t_base_k,
        f_hz=f_hz,
        p_e=p_e,
        curie_weiss_t0_k=curie_weiss_t0_k,
    )

    notes = [COMMON_DELTA_T_NOTE, Q_MARGIN_RUNG]
    if probe_weight_is_placeholder:
        notes.append(UNIFORM_PLACEHOLDER_RUNG)
    else:
        notes.append(SPIN_WEIGHT_RUNG)
        if gain_mask_is_fallback:
            notes.append(
                "gain_region_mask was the STO-dielectric fallback — the "
                "probe weight describes the STO puck, NOT the pentacene "
                "gain region (Phase 1b pending)"
            )

    return DifferentialDetuning(
        t_base_k=float(t_base_k),
        mean_delta_t_k=spin.mean_delta_t_k,
        rms_delta_t_k=spin.rms_delta_t_k,
        delta_f_cavity_hz=cav,
        delta_f_spin_hz=spin.mean_shift_hz,
        inhom_width_hz=spin.inhom_width_hz,
        delta_f_differential_hz=cav - spin.mean_shift_hz,
        f_hz=float(f_hz),
        p_e=float(p_e),
        df_spin_dt_hz_per_k=float(df_spin_dt_hz_per_k),
        probe_weight_is_placeholder=probe_weight_is_placeholder,
        spin_projection=spin_projection,
        gain_mask_is_fallback=gain_mask_is_fallback,
        spin_weight_rung=(
            UNIFORM_PLACEHOLDER_RUNG
            if probe_weight_is_placeholder
            else SPIN_WEIGHT_RUNG
        ),
        status_notes=tuple(notes),
    )


def differential_detuning_from_cylinder(
    solution: CylinderSolution,
    grid: CrystalProbeGrid,
    t_base_k: float,
    *,
    f_hz: float | None = None,
    p_e: float = 1.0,
    df_spin_dt_hz_per_k: float | None = None,
    probe_measure: NDArray[np.float64] | None = None,
    spin_projection: dict | None = None,
    gain_mask_is_fallback: bool | None = None,
) -> DifferentialDetuning:
    """Maser-cylinder instance: samples the transport core on the grid
    and composes `differential_detuning_from_samples`. Default probe =
    the uniform placeholder (flagged)."""
    placeholder = probe_measure is None
    if placeholder:
        probe_measure = uniform_probe_measure(grid)
    return differential_detuning_from_samples(
        cylinder_delta_t_samples(solution, grid),
        probe_measure,
        t_base_k,
        f_hz=f_hz,
        p_e=p_e,
        df_spin_dt_hz_per_k=df_spin_dt_hz_per_k,
        probe_weight_is_placeholder=placeholder,
        spin_projection=spin_projection,
        gain_mask_is_fallback=gain_mask_is_fallback,
    )
