"""SPEC §7.T7 / §8 discipline — linearised radiative loss in the Robin top.

Pins for `cavity.thermal.radiation` (the §7.T7 first implementation
slot):

  a. hand-calc magnitude — 4σT³ = 6.124 W m⁻² K⁻¹ at 300 K, ε = 1
     (SPEC §7.T7's "~6"), linear ε scaling, and the §6T band image
     h_rad ≈ 4.9–5.8 W m⁻² K⁻¹;
  b. off switch — ε = 0 reproduces the prior h_top behaviour
     BIT-FOR-BIT (regression safety: the pre-§7.T7 anchor results
     remain exactly reproducible);
  c. additive composition + monotonicity in ε and T — the ratified
     design decision (h_eff = h_conv + h_rad; SPEC hunk flags it
     pending Oxborrow);
  d. linearisation error vs the exact quartic — the fixed-ambient
     validity bound, asserted against the closed form;
  e. rig-stack magnitude verdict — radiation is a CORRECTION for the
     calibration geometry (§7.T5 stack), quantified not assumed.
"""

from __future__ import annotations

import math

import pytest

from cavity.provenance.constants import EMISSIVITY_PTP
from cavity.thermal.layered import Layer, delta_t_gaussian
from cavity.thermal.radiation import (
    h_rad_exact_secant,
    h_rad_linearized,
    h_top_with_radiation,
)

P = 1.0  # W — ΔT is linear in P; per-watt values suffice for the check

# Worst-case §7.T5 rig stack for top-loss sensitivity (same configuration
# as test_thermal_layered.py::test_robin_top_effect_is_bounded_for_rig_stack:
# low-k thick plate, thick wax, widest spot = most top area at temperature).
WORST_STACK = (Layer(0.5e-3, 0.1), Layer(100e-6, 0.24), Layer(1e-3, 1.14))
WORST_W = 500e-6


# --- a. magnitude pins ------------------------------------------------------


def test_h_rad_magnitude_hand_calc():
    """4σT³ at 300 K, ε = 1: 4 × 5.6704e-8 × 2.7e7 = 6.124 W/m²K."""
    assert math.isclose(h_rad_linearized(1.0, 300.0), 6.124, rel_tol=5e-4)


def test_h_rad_scales_linearly_in_epsilon():
    full = h_rad_linearized(1.0, 300.0)
    assert math.isclose(h_rad_linearized(0.9, 300.0), 0.9 * full, rel_tol=1e-12)
    assert math.isclose(h_rad_linearized(0.25, 300.0), 0.25 * full, rel_tol=1e-12)


def test_emissivity_band_maps_to_documented_h_rad_range():
    """§6T EMISSIVITY_PTP band (0.80–0.95, nominal 0.90 = conventional
    organic-solid handbook point value in the band's upper half) maps to
    h_rad ≈ 4.9–5.8 W/m²K at 300 K — the numbers carried in the constant's
    docstring and the SPEC §7.T7 status note. Regression pins."""
    assert EMISSIVITY_PTP.eps_band_lo == 0.80
    assert EMISSIVITY_PTP.eps_band_hi == 0.95
    assert EMISSIVITY_PTP.eps_nominal == 0.90
    assert (
        EMISSIVITY_PTP.eps_band_lo
        <= EMISSIVITY_PTP.eps_nominal
        <= EMISSIVITY_PTP.eps_band_hi
    )
    assert 4.8 < h_rad_linearized(EMISSIVITY_PTP.eps_band_lo, 300.0) < 5.0
    assert 5.7 < h_rad_linearized(EMISSIVITY_PTP.eps_band_hi, 300.0) < 5.9


# --- b. off switch: ε = 0 reproduces prior behaviour bit-for-bit ------------


def test_epsilon_zero_is_exact_zero_and_identity():
    assert h_rad_linearized(0.0, 300.0) == 0.0
    assert h_top_with_radiation(0.0, 0.0, 300.0) == 0.0
    assert h_top_with_radiation(20.0, 0.0, 300.0) == 20.0


def test_epsilon_zero_reproduces_solver_results_bitwise():
    """The composed h_top at ε = 0 is the identical float, so the solver
    result is bit-for-bit the pre-§7.T7 one — insulated and convective."""
    for h_conv in (0.0, 20.0):
        prior = delta_t_gaussian(0.0, WORST_STACK, P, WORST_W, h_top=h_conv)
        with_rad_off = delta_t_gaussian(
            0.0,
            WORST_STACK,
            P,
            WORST_W,
            h_top=h_top_with_radiation(h_conv, 0.0, 300.0),
        )
        assert with_rad_off == prior


# --- c. additive composition + monotonicity ---------------------------------


def test_composition_is_additive():
    """The ratified design decision: h_eff = h_conv + h_rad, exactly.
    A refactor to a replace-h_conv semantics must break this pin."""
    for h_conv, eps in ((0.0, 0.9), (10.0, 0.8), (20.0, 0.95)):
        assert h_top_with_radiation(h_conv, eps, 300.0) == h_conv + h_rad_linearized(
            eps, 300.0
        )


def test_h_rad_monotone_in_epsilon_and_temperature():
    eps_walk = [h_rad_linearized(e, 300.0) for e in (0.2, 0.5, 0.9)]
    assert eps_walk[0] < eps_walk[1] < eps_walk[2]
    t_walk = [h_rad_linearized(0.9, t) for t in (250.0, 300.0, 350.0)]
    assert t_walk[0] < t_walk[1] < t_walk[2]


def test_delta_t_falls_monotonically_as_epsilon_rises():
    """More radiative loss bleeds more heat from the top: ΔT strictly
    decreasing in ε at fixed h_conv (the §7.T4-convection machinery reused
    with the radiative knob, exactly as §7.T7 prescribes)."""
    vals = [
        delta_t_gaussian(
            0.0, WORST_STACK, P, WORST_W, h_top=h_top_with_radiation(0.0, e, 300.0)
        )
        for e in (0.0, 0.8, 0.95)
    ]
    assert vals[0] > vals[1] > vals[2]


# --- d. linearisation error vs the exact quartic ----------------------------


def test_linearization_error_against_exact_quartic():
    """h_rad = 4εσT_a³ is the first-order expansion of the exact secant
    εσ(T_s⁴−T_a⁴)/(T_s−T_a); exact/linear = (T_s+T_a)(T_s²+T_a²)/(4T_a³).
    At T_a = 300 K the linear form UNDER-reads by 5.1% at ΔT = 10 K and
    16.0% at ΔT = 30 K — spanning the "several tens of Celsius" inference
    (SPEC §11 item 5, ~13–30 K at 100 mA). CAVEAT CARRIED HERE (and in the
    radiation.py docstring + SPEC §7.T7 status note): because h_rad itself
    moves the rig-stack ΔT by only ~0.2–3% (test below), the COMPOUNDED
    error is negligible for the calibration geometry; if ΔT ≳ 30 K ever
    becomes calibration-relevant, upgrade via h_rad_exact_secant iteration
    rather than stretching the fixed-ambient form."""
    t_a = 300.0
    for delta_t, want in ((10.0, 0.051120), (30.0, 0.160250)):
        t_s = t_a + delta_t
        closed_form = (t_s + t_a) * (t_s**2 + t_a**2) / (4.0 * t_a**3) - 1.0
        assert math.isclose(closed_form, want, rel_tol=1e-4)
        for eps in (0.3, 0.95):  # ratio is ε-independent
            ratio = h_rad_exact_secant(eps, t_s, t_a) / h_rad_linearized(eps, t_a)
            assert math.isclose(ratio - 1.0, closed_form, rel_tol=1e-12)


def test_exact_secant_reduces_to_linear_at_equal_temperatures():
    """The factored secant form εσ(T_s+T_a)(T_s²+T_a²) is singularity-free:
    at T_s = T_a it equals 4εσT_a³ (algebraic identity, no 0/0)."""
    assert math.isclose(
        h_rad_exact_secant(0.9, 300.0, 300.0),
        h_rad_linearized(0.9, 300.0),
        rel_tol=1e-12,
    )


# --- e. rig-stack magnitude: radiation is a correction ----------------------


def test_radiative_correction_bounded_on_worst_case_rig_stack():
    """§7.T7 leading-order check, calibration geometry: radiation alone
    (band-top ε) moves ΔT by well under 3% even on the worst-case stack;
    convection worst case (h = 20) + radiation stays inside the existing
    10% Robin envelope. Radiation is a CORRECTION to the conduction-
    dominated transport here — quantified, not assumed. (The across-
    operating-range competition sweep — surface T, maser cylinder — is
    §7.T7's open follow-up, not this test.)"""
    insulated = delta_t_gaussian(0.0, WORST_STACK, P, WORST_W, h_top=0.0)
    rad_only = delta_t_gaussian(
        0.0,
        WORST_STACK,
        P,
        WORST_W,
        h_top=h_top_with_radiation(0.0, EMISSIVITY_PTP.eps_band_hi, 300.0),
    )
    rad_drop = (insulated - rad_only) / insulated
    assert 0.0 < rad_drop < 0.03

    conv_and_rad = delta_t_gaussian(
        0.0,
        WORST_STACK,
        P,
        WORST_W,
        h_top=h_top_with_radiation(20.0, EMISSIVITY_PTP.eps_band_hi, 300.0),
    )
    both_drop = (insulated - conv_and_rad) / insulated
    assert rad_drop < both_drop < 0.10


# --- input validation --------------------------------------------------------


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        h_rad_linearized(-0.1, 300.0)
    with pytest.raises(ValueError):
        h_rad_linearized(1.1, 300.0)
    with pytest.raises(ValueError):
        h_rad_linearized(0.9, 0.0)
    with pytest.raises(ValueError):
        h_rad_exact_secant(0.9, -10.0, 300.0)
    with pytest.raises(ValueError):
        h_top_with_radiation(-1.0, 0.9, 300.0)
