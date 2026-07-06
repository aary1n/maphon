"""SPEC §7.T2 output 3 / §8 discipline — anchors for the inhomogeneous
thermal line observable (`cavity.thermal.broadening`).

The named limit check (SPEC 2026-07-06 meeting block): uniform T ⇒ ZERO
inhomogeneous width, pure shift — asserted EXACTLY, not to rounding.

Closed-form anchors for the rig instance, before use:

  A.1  Half-space, Gaussian spot: probe-weighted moments against the
       elliptic-integral closed forms ⟨ΔT⟩ = ΔT₀/√2 and
       ⟨ΔT²⟩ = ΔT₀²·ellipk(1/4)/π (Laplace transforms of I₀, I₀²).
  A.2  1-D limit (w ≫ stack): ⟨ΔT⟩ → ΔT₀/2, ⟨ΔT²⟩ → ΔT₀²/3 — regime
       constants DISTINCT from A.1, so the pair discriminates.
  A.3  Hankel-Parseval identity: the probe-weighted mean equals
       delta_t_gaussian(0, layers, P, √2·w) — independent algebra vs
       the real-space quadrature, on the full rig stack, with Robin
       top and with the volumetric kernel.

Plus the linewidth-unit identity (shift/[f/Q] ≡ Δf·Q/f — the §7.T4
linkage unit) and sign/validation guards.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.special import ellipk

from cavity.thermal.broadening import (
    gaussian_spot_line_observable,
    line_observable_from_samples,
    probe_weighted_surface_moments,
    resonance_linewidth_hz,
)
from cavity.thermal.identifiability import FORMS, NAMED_POINTS, rig_stack
from cavity.thermal.layered import (
    Layer,
    anchor_half_space_gaussian_center,
    anchor_one_dimensional_center,
    delta_t_gaussian,
    delta_t_gaussian_volumetric,
)

P = 1.0
K_MID = 0.31622776601683794  # §6T k band geometric midpoint
STACK = (Layer(0.5e-3, K_MID), Layer(31.6e-6, 0.24), Layer(1e-3, 1.14))
DF_DT = -80e3  # Hz/K, inside the §6T band; tests carry the sign explicitly


# --- the named limit anchor: uniform T ⇒ pure shift, zero width -------------


def test_uniform_field_gives_pure_shift_and_exactly_zero_width():
    """SPEC 2026-07-06 anchor: an isothermal probed volume must produce
    the mean shift and IDENTICALLY zero inhomogeneous width."""
    dt = np.full(37, 4.2)
    wt = np.random.default_rng(0).uniform(0.1, 1.0, 37)
    obs = line_observable_from_samples(dt, wt, DF_DT)
    assert obs.rms_delta_t_k == 0.0
    assert obs.inhom_width_hz == 0.0
    assert obs.mean_shift_hz == DF_DT * 4.2


def test_two_delta_distribution_exact_moments():
    """Half the probe weight at T₁, half at T₂: mean (T₁+T₂)/2, σ |T₂−T₁|/2."""
    obs = line_observable_from_samples(
        np.array([1.0, 3.0]), np.array([1.0, 1.0]), DF_DT
    )
    assert math.isclose(obs.mean_delta_t_k, 2.0, rel_tol=1e-15)
    assert math.isclose(obs.rms_delta_t_k, 1.0, rel_tol=1e-12)
    assert math.isclose(obs.mean_shift_hz, 2.0 * DF_DT, rel_tol=1e-15)
    assert math.isclose(obs.inhom_width_hz, abs(DF_DT), rel_tol=1e-12)


def test_sign_conventions_shift_signed_width_positive():
    """Negative df/dT ⇒ negative shift (red with heating); width ≥ 0 for
    either sign of the coefficient."""
    dt, wt = np.array([1.0, 2.0]), np.array([1.0, 1.0])
    neg = line_observable_from_samples(dt, wt, -50e3)
    pos = line_observable_from_samples(dt, wt, +50e3)
    assert neg.mean_shift_hz < 0 < pos.mean_shift_hz
    assert neg.inhom_width_hz == pos.inhom_width_hz > 0


def test_sample_validation():
    dt, wt = np.array([1.0, 2.0]), np.array([1.0, 1.0])
    with pytest.raises(ValueError):
        line_observable_from_samples(dt, wt[:1], DF_DT)
    with pytest.raises(ValueError):
        line_observable_from_samples(dt, np.array([1.0, -1.0]), DF_DT)
    with pytest.raises(ValueError):
        line_observable_from_samples(dt, np.zeros(2), DF_DT)
    with pytest.raises(ValueError):
        line_observable_from_samples(np.array([]), np.array([]), DF_DT)


# --- A.1: half-space closed-form moments -------------------------------------


def test_anchor_half_space_probe_weighted_moments():
    """ΔT(r,0)/ΔT₀ = e^{−x}I₀(x) under the e^{−s} probe measure:
    ⟨ΔT⟩ = ΔT₀/√2 and ⟨ΔT²⟩ = ΔT₀²·K(m=1/4)/π exactly (Laplace
    transforms of I₀ and I₀²); prototype accuracy ~8e-7 at 96 nodes."""
    w = 30e-6
    half_space = (Layer(math.inf, K_MID),)
    dt0 = anchor_half_space_gaussian_center(P, K_MID, w)
    m1, m2 = probe_weighted_surface_moments(
        lambda r: delta_t_gaussian(r, half_space, P, w), w
    )
    assert abs(m1 / (dt0 / math.sqrt(2.0)) - 1.0) < 5e-6
    assert abs(m2 / (dt0**2 * ellipk(0.25) / math.pi) - 1.0) < 5e-6


# --- A.2: 1-D limit moments ---------------------------------------------------


def test_anchor_one_dimensional_probe_weighted_moments():
    """w ≫ stack: the profile follows the local flux, ∝ e^{−2r²/w²}, so
    ⟨ΔT⟩ → ΔT₀/2 and ⟨ΔT²⟩ → ΔT₀²/3 — different constants from the
    half-space pair (0.707, 0.537): the two anchors discriminate."""
    w = 100.0 * sum(layer.thickness_m for layer in STACK)
    dt0 = anchor_one_dimensional_center(P, w, STACK)
    m1, m2 = probe_weighted_surface_moments(
        lambda r: delta_t_gaussian(r, STACK, P, w), w
    )
    assert abs(m1 / (dt0 / 2.0) - 1.0) < 5e-4
    assert abs(m2 / (dt0**2 / 3.0) - 1.0) < 5e-4


# --- A.3: Hankel-Parseval mean identity --------------------------------------


def test_anchor_mean_equals_sqrt2_wider_spot():
    """Independent algebra: the probe-weighted mean must equal the centre
    rise of a √2-wider spot — full rig stack, Robin top, and the
    volumetric kernel alike (the identity is kernel-agnostic)."""
    w, t_wax = NAMED_POINTS["doublet_mid_wax"]
    stack = rig_stack(FORMS["PLATE"], K_MID, t_wax)
    cases = [
        (0.0, None),
        (20.0, None),
        (0.0, 50e-6),
    ]
    for h_top, l_abs in cases:
        obs = gaussian_spot_line_observable(
            stack, P, w, DF_DT, h_top=h_top, l_abs_m=l_abs
        )
        if l_abs is None:
            want = delta_t_gaussian(0.0, stack, P, math.sqrt(2.0) * w, h_top)
        else:
            want = delta_t_gaussian_volumetric(
                0.0, stack, P, math.sqrt(2.0) * w, l_abs, h_top
            )
        assert abs(obs.mean_delta_t_k / want - 1.0) < 5e-6, (h_top, l_abs)


# --- the reporting unit -------------------------------------------------------


def test_linewidth_unit_identity_shift_times_q_over_f():
    """'In linewidths' with linewidth = f/Q_L must equal Δf·Q/f — the
    equivalence Oxborrow stated, and the §7.T4 linkage unit."""
    f, q = 1.4493e9, 6_980.0
    obs = line_observable_from_samples(
        np.array([1.0, 3.0]), np.array([1.0, 1.0]), DF_DT
    )
    lw = resonance_linewidth_hz(f, q)
    assert math.isclose(lw, f / q, rel_tol=1e-15)
    assert math.isclose(
        obs.shift_in_linewidths(lw), obs.mean_shift_hz * q / f, rel_tol=1e-12
    )
    assert math.isclose(
        obs.width_in_linewidths(lw), obs.inhom_width_hz * q / f, rel_tol=1e-12
    )
    with pytest.raises(ValueError):
        obs.shift_in_linewidths(0.0)
    with pytest.raises(ValueError):
        resonance_linewidth_hz(f, -1.0)


def test_rig_instance_width_positive_and_linear_in_df_dt():
    """A focused spot on the plate stack must broaden (spreading regime:
    the probed volume spans a genuine T-spread), and both outputs are
    linear in the coefficient."""
    w, t_wax = NAMED_POINTS["focused_thin_wax"]
    stack = rig_stack(FORMS["PLATE"], K_MID, t_wax)
    one = gaussian_spot_line_observable(stack, P, w, DF_DT)
    two = gaussian_spot_line_observable(stack, P, w, 2.0 * DF_DT)
    assert one.inhom_width_hz > 0
    assert math.isclose(two.mean_shift_hz, 2.0 * one.mean_shift_hz, rel_tol=1e-12)
    assert math.isclose(two.inhom_width_hz, 2.0 * one.inhom_width_hz, rel_tol=1e-12)
