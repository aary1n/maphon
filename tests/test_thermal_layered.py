"""SPEC §7T / §8 discipline — analytic anchors for the layered Hankel solver.

The general solver is trusted only after it reproduces the closed forms
(anchors a–c of the §7.T5 identifiability-sweep brief):

  a. semi-infinite single-layer limit — classical spreading-resistance
     results for disk and Gaussian flux (Carslaw & Jaeger §8.2; the
     Gaussian forms are derived in cavity/thermal/layered.py's module
     docstring and asserted here);
  b. thin-layer / 1-D limit — series-resistance slab formula;
  c. layer-collapse consistency — merging equal-k layers is exact.

Plus the flux-normalisation, Hankel-space-limit, and Robin-top checks
that pin the conventions the sweep rides on.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cavity.thermal.layered import (
    Layer,
    anchor_half_space_disk_average,
    anchor_half_space_disk_center,
    anchor_half_space_gaussian_center,
    anchor_half_space_gaussian_profile,
    anchor_one_dimensional_center,
    delta_t_disk_average,
    delta_t_disk_center,
    delta_t_gaussian,
    disk_flux_hankel,
    gaussian_flux_hankel,
    series_resistance,
    surface_impedance,
)

P = 1.0  # W — ΔT is linear in P (SPEC §7.T5: the observable is dΔT/dP shape)
K = 0.3  # W/m/K — representative of the k_PTP band under test


# --- convention pins -------------------------------------------------------


def test_flux_transforms_carry_total_power():
    """q̂(ξ→0) = P/2π for any normalised flux (total-power convention)."""
    assert math.isclose(float(gaussian_flux_hankel(0.0, P, 10e-6)), P / (2 * math.pi))
    assert math.isclose(
        float(disk_flux_hankel(1e-12, P, 10e-6)), P / (2 * math.pi), rel_tol=1e-9
    )


def test_surface_impedance_limits():
    """Z(ξ→0) = Σt/k (1-D series); Z(ξ→∞) = 1/(k₁ξ) (top layer half-space)."""
    stack = (Layer(0.5e-3, 0.3), Layer(10e-6, 0.24), Layer(1e-3, 1.14))
    r_series = series_resistance(stack)
    assert math.isclose(float(surface_impedance(1e-6, stack)), r_series, rel_tol=1e-6)
    xi_hi = 1e7  # xi*t1 = 5000: only the top layer is visible
    assert math.isclose(
        float(surface_impedance(xi_hi, stack)), 1.0 / (0.3 * xi_hi), rel_tol=1e-9
    )


def test_infinite_layer_terminates_stack():
    """A semi-infinite layer must make anything below it unreachable."""
    xi = np.logspace(2, 6, 5)
    half = (Layer(math.inf, K),)
    buried = (Layer(math.inf, K), Layer(1e-3, 100.0))
    np.testing.assert_allclose(
        surface_impedance(xi, half), surface_impedance(xi, buried), rtol=0
    )


# --- anchor a: semi-infinite single layer ----------------------------------


def test_anchor_a_disk_center_half_space():
    """Uniform-disk flux on a half-space: ΔT(0,0) = P/(πka)."""
    a = 25e-6
    got = delta_t_disk_center((Layer(math.inf, K),), P, a)
    assert math.isclose(got, anchor_half_space_disk_center(P, K, a), rel_tol=1e-6)


def test_anchor_a_disk_average_half_space_and_isothermal_bound():
    """Disk-average rise = 8P/(3π²ka) exactly; P/(4ka) only to the 1.081
    isoflux/isothermal constriction factor (deliberate: the 4ka form is
    the CONSTANT-TEMPERATURE-disk spreading resistance, a different BC —
    see layered.py docstring)."""
    a = 25e-6
    got = delta_t_disk_average((Layer(math.inf, K),), P, a)
    exact = anchor_half_space_disk_average(P, K, a)
    assert math.isclose(got, exact, rel_tol=1e-5)
    isothermal = P / (4.0 * K * a)
    assert math.isclose(exact / isothermal, 32.0 / (3.0 * math.pi**2), rel_tol=1e-12)
    assert abs(got / isothermal - 1.0) < 0.09  # the classical ~8.1% gap


def test_anchor_a_gaussian_center_half_space():
    """Gaussian flux (1/e² radius w) on a half-space: ΔT(0,0) = P/(√(2π)kw)."""
    w = 10e-6
    got = delta_t_gaussian(0.0, (Layer(math.inf, K),), P, w)
    assert math.isclose(got, anchor_half_space_gaussian_center(P, K, w), rel_tol=1e-8)


def test_anchor_a_gaussian_center_deep_finite_layer():
    """t_PTP → ∞ recovery: a layer 10⁴ spots deep matches the half-space
    closed form to the O(w/t) truncation scale."""
    w = 10e-6
    got = delta_t_gaussian(0.0, (Layer(1e4 * w, K),), P, w)
    assert math.isclose(got, anchor_half_space_gaussian_center(P, K, w), rel_tol=1e-4)


def test_anchor_a_gaussian_radial_profile():
    """Full profile ΔT(r,0) = ΔT₀·e^{−r²/w²}I₀(r²/w²) on the half-space."""
    w = 10e-6
    for r_over_w in (0.5, 1.0, 2.0, 4.0):
        got = delta_t_gaussian(r_over_w * w, (Layer(math.inf, K),), P, w)
        want = float(anchor_half_space_gaussian_profile(r_over_w * w, P, K, w))
        assert math.isclose(got, want, rel_tol=1e-7), f"r/w={r_over_w}"


# --- anchor b: thin-layer / 1-D limit --------------------------------------


def test_anchor_b_one_dimensional_limit_converges():
    """w ≫ stack: ΔT(0,0) → (2P/πw²)·Σt_i/k_i, monotonically from below
    (lateral spreading can only lower the peak below the 1-D value)."""
    stack = (Layer(0.5e-3, 0.3), Layer(10e-6, 0.24), Layer(1e-3, 1.14))
    total_t = sum(layer.thickness_m for layer in stack)
    rel_errors = []
    for w_over_t in (10.0, 30.0, 100.0):
        w = w_over_t * total_t
        got = delta_t_gaussian(0.0, stack, P, w)
        want = anchor_one_dimensional_center(P, w, stack)
        assert got < want
        rel_errors.append(abs(got / want - 1.0))
    assert rel_errors[0] > rel_errors[1] > rel_errors[2]
    assert rel_errors[-1] < 1e-3


# --- anchor c: layer collapse ----------------------------------------------


def test_anchor_c_layer_collapse():
    """k_wax = k_PTP with merged thicknesses must equal the two-layer solve."""
    k_shared, t1, t2 = 0.3, 0.5e-3, 20e-6
    glass = Layer(1e-3, 1.14)
    three = (Layer(t1, k_shared), Layer(t2, k_shared), glass)
    two = (Layer(t1 + t2, k_shared), glass)
    for w in (3e-6, 30e-6, 300e-6):
        a = delta_t_gaussian(0.0, three, P, w)
        b = delta_t_gaussian(0.0, two, P, w)
        assert math.isclose(a, b, rel_tol=1e-10), f"w={w}"


def test_anchor_c_sublayer_split_is_exact():
    """Splitting one layer into five equal sub-layers changes nothing."""
    glass = Layer(1e-3, 1.14)
    whole = (Layer(0.5e-3, 0.3), glass)
    split = tuple(Layer(0.1e-3, 0.3) for _ in range(5)) + (glass,)
    got = delta_t_gaussian(0.0, split, P, 20e-6)
    want = delta_t_gaussian(0.0, whole, P, 20e-6)
    assert math.isclose(got, want, rel_tol=1e-10)


# --- Robin top (switchable BC, §7.T1) --------------------------------------


def test_robin_top_reduces_delta_t_monotonically():
    """h > 0 bleeds heat from the top: ΔT must fall monotonically in h."""
    stack = (Layer(0.5e-3, 0.1), Layer(10e-6, 0.24), Layer(1e-3, 1.14))
    w = 100e-6
    vals = [delta_t_gaussian(0.0, stack, P, w, h_top=h) for h in (0.0, 10.0, 20.0)]
    assert vals[0] > vals[1] > vals[2]


def test_robin_top_effect_is_bounded_for_rig_stack():
    """Free convection + radiation (h ≲ 20 W/m²K) is a few-percent effect on
    the rig stack — the quantitative justification for the insulated-top
    default (reported, not hand-waved; worst case is low-k thick plate)."""
    stack = (Layer(0.5e-3, 0.1), Layer(100e-6, 0.24), Layer(1e-3, 1.14))
    w = 500e-6  # widest spot = most top area at temperature = worst case
    insulated = delta_t_gaussian(0.0, stack, P, w, h_top=0.0)
    lossy = delta_t_gaussian(0.0, stack, P, w, h_top=20.0)
    assert 0.0 < (insulated - lossy) / insulated < 0.10


def test_invalid_layers_rejected():
    with pytest.raises(ValueError):
        Layer(0.0, 1.0)
    with pytest.raises(ValueError):
        Layer(1e-3, -0.1)
    with pytest.raises(ValueError):
        delta_t_gaussian(0.0, (Layer(1e-3, 1.0),), P, 0.0)
