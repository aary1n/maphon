"""SPEC §7T / §8 discipline — anchors for the volumetric (Beer-Lambert)
source extension of the layered Hankel solver, plus the check-3a
volumetric regression pins.

Anchors (task B of the 3a volumetric appendix), all before use:

  B.1  l_abs → 0 recovers the SURFACE-FLUX solution at the named grid
       points to rel 1e-4 — the regression bridge to the validated
       engine (whose own anchors are tests/test_thermal_layered.py).
  B.2  l_abs ≫ t_PTP approaches the UNIFORM-GENERATION two-region slab
       (1-D closed form, derived in layered.py:
       anchor_one_dimensional_uniform_generation — the t₁/(2k₁)
       half-thickness signature), verified in the w ≫ thickness regime;
       plus the sharper general-l_abs 1-D form
       (anchor_one_dimensional_volumetric) at any absorption depth.
  B.3  Energy: the power crossing the isothermal base equals P for all
       l_abs (the spot radius enters the budget exactly, via
       q̂(0) = P/2π — pinned in test_thermal_layered.py), and the
       truncated-renormalised depth pdf integrates to 1.

Plus the buried-sheet kernel vs the single-layer Sturm-Liouville
Green's function (exact), Robin monotonicity, and physical
monotonicity in l_abs.

The two VOLUMETRIC REGRESSION PINS extend the R_PINS discipline of
tests/test_thermal_identifiability.py: they encode the verdict-setting
numbers of thermal/reports/identifiability_3a_volumetric.md (one
small-l_abs, one large). If a deliberate physics change moves them,
re-run `python -m cavity.thermal.report_3a_volumetric`, re-read the
verdict, and update pins + report together — never the pins alone.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.integrate import quad

from cavity.provenance.constants import L_ABS_PUMP
from cavity.thermal.identifiability import FORMS, NAMED_POINTS, rig_stack
from cavity.thermal.layered import (
    Layer,
    _buried_sheet_gtilde,
    anchor_one_dimensional_uniform_generation,
    anchor_one_dimensional_volumetric,
    delta_t_gaussian,
    delta_t_gaussian_volumetric,
    volumetric_base_power,
    volumetric_depth_pdf,
)
from cavity.thermal.volumetric_3a import (
    delta_t_center_volumetric,
    log_slopes_volumetric,
    r_ratio_volumetric,
)

P = 1.0
K_MID = 0.31622776601683794  # §6T k band geometric midpoint
STACK = (Layer(0.5e-3, K_MID), Layer(31.6e-6, 0.24), Layer(1e-3, 1.14))


# --- kernel identity: buried sheet vs Sturm-Liouville Green's function ------


def test_buried_sheet_matches_single_layer_green_function():
    """Single layer on an isothermal base, insulated top: the sheet response
    must equal sinh(ξ(t−z′))/(kξ·cosh(ξt)) — the closed-form Green's
    function the transmission-line algebra was derived against."""
    t, k = 0.5e-3, K_MID
    for xi in (1e2, 3e4, 2e5):
        for z_frac in (0.1, 0.4, 0.9):
            zp = z_frac * t
            got = float(
                _buried_sheet_gtilde(xi, (Layer(t, k),), np.array([zp]), 0.0)[0]
            ) * math.exp(-xi * zp)
            want = math.sinh(xi * (t - zp)) / (k * xi * math.cosh(xi * t))
            assert math.isclose(got, want, rel_tol=1e-12), (xi, z_frac)


# --- B.1: l_abs -> 0 bridge to the surface-flux engine ----------------------


def test_bridge_labs_to_zero_recovers_surface_flux():
    """l_abs → 0 must recover the validated surface-flux solution to
    rel 1e-4 at the named grid points (all three band k values)."""
    for w, t_wax in NAMED_POINTS.values():
        for k in (0.1, K_MID, 1.0):
            stack = rig_stack(FORMS["PLATE"], k, t_wax)
            surf = delta_t_gaussian(0.0, stack, P, w)
            vol = delta_t_gaussian_volumetric(0.0, stack, P, w, 1e-10)
            assert abs(vol / surf - 1.0) < 1e-4, (w, k)


def test_bridge_error_shrinks_with_labs():
    """The bridge deviation is O(l_abs): tightening l_abs must shrink it."""
    w, t_wax = NAMED_POINTS["focused_thin_wax"]
    stack = rig_stack(FORMS["PLATE"], K_MID, t_wax)
    surf = delta_t_gaussian(0.0, stack, P, w)
    err = [
        abs(delta_t_gaussian_volumetric(0.0, stack, P, w, l) / surf - 1.0)
        for l in (1e-8, 1e-10)
    ]
    assert err[0] > err[1]


# --- B.2: uniform-generation slab limit (w >> thicknesses) ------------------


def test_anchor_uniform_generation_slab():
    """l_abs ≫ t₁ and w ≫ Σt: the Hankel solve must land on the two-region
    uniform-generation slab closed form — including its discriminating
    t₁/(2k₁) HALF-thickness term (a surface flux would give t₁/k₁)."""
    total_t = sum(layer.thickness_m for layer in STACK)
    w = 100.0 * total_t
    l_abs = 1e3 * STACK[0].thickness_m
    got = delta_t_gaussian_volumetric(0.0, STACK, P, w, l_abs)
    want_uniform = anchor_one_dimensional_uniform_generation(P, w, STACK)
    assert abs(got / want_uniform - 1.0) < 2e-3
    # sharper: the general-l 1-D form removes the residual source-shape gap
    want_general = anchor_one_dimensional_volumetric(P, w, STACK, l_abs)
    assert abs(got / want_general - 1.0) < 5e-4
    # and a surface-flux reading of the same stack is ~t₁/(2k₁) wrong:
    # the anchor discriminates, it does not just tolerate
    from cavity.thermal.layered import anchor_one_dimensional_center

    assert anchor_one_dimensional_center(P, w, STACK) / want_uniform > 1.3


def test_anchor_general_1d_limit_converges_from_below():
    """w ≫ stack at FINITE l_abs (t₁/3): ΔT(0,0) → the general 1-D closed
    form, monotonically from below (spreading only lowers the peak)."""
    total_t = sum(layer.thickness_m for layer in STACK)
    l_abs = STACK[0].thickness_m / 3.0
    rel_errors = []
    for w_over_t in (10.0, 30.0, 100.0):
        w = w_over_t * total_t
        got = delta_t_gaussian_volumetric(0.0, STACK, P, w, l_abs)
        want = anchor_one_dimensional_volumetric(P, w, STACK, l_abs)
        assert got < want
        rel_errors.append(abs(got / want - 1.0))
    assert rel_errors[0] > rel_errors[1] > rel_errors[2]
    assert rel_errors[-1] < 5e-4


def test_anchor_closed_forms_limits():
    """The general 1-D form must reduce to its own limits: t₁/k₁ (l → 0)
    and the uniform-generation form (l → ∞)."""
    from cavity.thermal.layered import anchor_one_dimensional_center

    w = 1.0
    tiny = anchor_one_dimensional_volumetric(P, w, STACK, 1e-9)
    surf = anchor_one_dimensional_center(P, w, STACK)
    assert math.isclose(tiny, surf, rel_tol=1e-5)
    huge = anchor_one_dimensional_volumetric(P, w, STACK, 1e6 * STACK[0].thickness_m)
    uni = anchor_one_dimensional_uniform_generation(P, w, STACK)
    assert math.isclose(huge, uni, rel_tol=1e-6)


# --- B.3: energy -------------------------------------------------------------


def test_energy_base_power_equals_p():
    """Steady state, insulated top: every watt of the renormalised source
    exits through the base — for l_abs ≪, ≈ and ≫ t₁. (w enters the
    budget exactly via q̂(0) = P/2π, pinned in test_thermal_layered.py.)"""
    for l_abs in (5e-6, 200e-6, 5e-3):
        got = volumetric_base_power(STACK, P, l_abs)
        assert abs(got / P - 1.0) < 1e-6, l_abs


def test_depth_pdf_normalised_for_all_labs():
    """Truncation + renormalisation: ∫₀^{t₁} g dz = 1 whatever l_abs."""
    t1 = STACK[0].thickness_m
    for l_abs in (1e-6, 50e-6, 1.0):
        val, _ = quad(
            lambda z: float(volumetric_depth_pdf(z, t1, l_abs)),
            0.0,
            t1,
            points=[min(l_abs, t1)],
            limit=200,
        )
        assert abs(val - 1.0) < 1e-9, l_abs


# --- physical invariants -----------------------------------------------------


def test_burying_the_source_lowers_the_surface_peak_monotonically():
    """ΔT(0,0) must fall strictly as l_abs grows (heat starts deeper),
    and always sit below the surface-flux value."""
    w, t_wax = NAMED_POINTS["doublet_mid_wax"]
    stack = rig_stack(FORMS["PLATE"], K_MID, t_wax)
    surface = delta_t_gaussian(0.0, stack, P, w)
    prev = surface
    for l_abs in L_ABS_PUMP.l_abs_scoping_grid_m:
        val = delta_t_gaussian_volumetric(0.0, stack, P, w, l_abs)
        assert val < prev, l_abs
        prev = val


def test_robin_top_reduces_volumetric_delta_t():
    """h > 0 must bleed heat from the top for the buried source too."""
    w, t_wax = NAMED_POINTS["doublet_mid_wax"]
    stack = rig_stack(FORMS["PLATE"], 0.1, t_wax)
    vals = [
        delta_t_gaussian_volumetric(0.0, stack, P, w, 50e-6, h_top=h)
        for h in (0.0, 10.0, 20.0)
    ]
    assert vals[0] > vals[1] > vals[2]


def test_invalid_labs_rejected():
    with pytest.raises(ValueError):
        delta_t_gaussian_volumetric(0.0, STACK, P, 10e-6, 0.0)
    with pytest.raises(ValueError):
        volumetric_depth_pdf(0.0, 1e-3, -1e-6)


# --- volumetric regression pins (extend the R_PINS discipline) --------------

# Direct (grid-free) values at the named PLATE points, one small l_abs and
# one large, adaptive quadrature at epsrel ~1e-8; pinned with 1e-6 slack.
# These encode the SCALING-SOFTENS numbers of the volumetric appendix:
# the k log-slope stays ≈ −1 while the w log-slope leaves the surface
# −1.00 (to −0.50 / −0.53 here) — the deformation of the k–w degeneracy
# that identifiability_3a_volumetric.md rules on.
VOLUMETRIC_PINS = {
    # (point, l_abs_m): (R, dlnT/dln w)
    ("focused_thin_wax", 5e-6): (2.8431604, -0.50169628),
    ("doublet_mid_wax", 200e-6): (2.7091017, -0.53465291),
}


def test_volumetric_regression_pins():
    for (point, l_abs), (r_pin, dlnw_pin) in VOLUMETRIC_PINS.items():
        w, t_wax = NAMED_POINTS[point]
        r = r_ratio_volumetric(FORMS["PLATE"], w, t_wax, l_abs)
        assert math.isclose(r, r_pin, rel_tol=1e-6), (point, r)
        slopes = log_slopes_volumetric("PLATE", w, t_wax, l_abs)
        assert math.isclose(slopes["dlnT_dlnw"], dlnw_pin, rel_tol=1e-6), (
            point,
            slopes["dlnT_dlnw"],
        )


def test_volumetric_observable_consistent_with_engine():
    """The sweep-facing wrapper must be the engine value, not a re-type."""
    w, t_wax = NAMED_POINTS["doublet_mid_wax"]
    direct = delta_t_gaussian_volumetric(
        0.0, rig_stack(FORMS["PLATE"], K_MID, t_wax), 1.0, w, 50e-6
    )
    wrapped = delta_t_center_volumetric(FORMS["PLATE"], K_MID, w, t_wax, 50e-6)
    assert math.isclose(direct, wrapped, rel_tol=1e-12)
