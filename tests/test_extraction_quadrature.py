"""SPEC §3 axisymmetric_volume_integral primitive — analytic test (1).

A constant scalar field g over a rectangular r-z domain [r0, r1] x
[z0, z1] integrates to

    int_V g dV = 2*pi * g * (z1 - z0) * (r1^2 - r0^2) / 2
              = pi * g * (z1 - z0) * (r1^2 - r0^2).

Trapezoid quadrature on a uniform grid is exact for linear integrands
in each direction; since g * r is linear in r when g is constant, the
primitive must reproduce the closed form to machine precision.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cavity.extraction import axisymmetric_volume_integral

from tests._extraction_fixtures import make_structured_grid


def _closed_form_constant_integral(
    g: float, r0: float, r1: float, z0: float, z1: float
) -> float:
    return math.pi * g * (z1 - z0) * (r1 ** 2 - r0 ** 2)


class TestAxisymmetricPrimitive:
    """SPEC §3 hard requirement: build and test the primitive first."""

    def test_constant_scalar_recovers_closed_form_machine_precision(self):
        r0, r1 = 1.0e-3, 6.0e-3
        z0, z1 = -3.0e-3, 9.0e-3
        g_value = 7.25
        grid = make_structured_grid(r0, r1, z0, z1, n_r=11, n_z=13)
        g = np.full_like(grid.r_m, g_value, dtype=np.float64)

        result = axisymmetric_volume_integral(
            g, grid.r_m, grid.weights_m2
        )
        expected = _closed_form_constant_integral(g_value, r0, r1, z0, z1)
        assert result.real == pytest.approx(expected, rel=1e-12)
        assert result.imag == pytest.approx(0.0, abs=1e-18)

    def test_returns_volume_units_meter_cubed(self):
        """Sanity: g = 1 over [0, 1] x [0, 1] gives 2pi * 1 * 1^2/2 = pi (m^3)."""
        grid = make_structured_grid(0.0, 1.0, 0.0, 1.0, n_r=5, n_z=5)
        g = np.ones_like(grid.r_m)
        result = axisymmetric_volume_integral(g, grid.r_m, grid.weights_m2)
        assert result.real == pytest.approx(math.pi, rel=1e-12)

    def test_handles_complex_integrand(self):
        """Complex g passes through; real / imag parts integrated independently."""
        grid = make_structured_grid(0.0, 2.0e-3, 0.0, 2.0e-3, n_r=6, n_z=6)
        g = np.full_like(
            grid.r_m, complex(3.0, -1.5), dtype=np.complex128
        )
        result = axisymmetric_volume_integral(
            g, grid.r_m, grid.weights_m2
        )
        expected_real = _closed_form_constant_integral(
            3.0, 0.0, 2.0e-3, 0.0, 2.0e-3
        )
        expected_imag = _closed_form_constant_integral(
            -1.5, 0.0, 2.0e-3, 0.0, 2.0e-3
        )
        assert result.real == pytest.approx(expected_real, rel=1e-12)
        assert result.imag == pytest.approx(expected_imag, rel=1e-12)

    def test_shape_mismatch_raises(self):
        g = np.ones(10)
        r = np.linspace(0.0, 1.0, 10)
        w = np.ones(9)
        with pytest.raises(ValueError, match="shape mismatch"):
            axisymmetric_volume_integral(g, r, w)

    def test_linear_g_in_r_still_exact_on_uniform_grid(self):
        """Trapezoid is exact for cubic integrand here: g(r) = r => int = r^2,
        and g*r = r^2 is the integrand inside the (r dr) measure. Uniform-grid
        trapezoid on quadratics is not exact — so loosen the tolerance.
        """
        r0, r1 = 0.0, 1.0
        z0, z1 = 0.0, 1.0
        grid = make_structured_grid(r0, r1, z0, z1, n_r=257, n_z=3)
        g = grid.r_m.copy()
        result = axisymmetric_volume_integral(
            g, grid.r_m, grid.weights_m2
        )
        expected = 2.0 * math.pi * (z1 - z0) * (r1 ** 3 - r0 ** 3) / 3.0
        assert result.real == pytest.approx(expected, rel=1e-4)
