"""SPEC §3 export-grid tests — weights must recover areas exactly.

The extraction layer's FieldSample contract requires explicit r-z plane
quadrature weights (m^2); `gridding` is the single builder of those
weights for solver exports. If the weight sum drifts from the half-plane
area, every V_mode / p_e downstream is silently wrong.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.forward_model.gridding import (
    GridSpec,
    structured_grid,
    trapezoid_weights_1d,
)


class TestTrapezoidWeights1D:
    def test_uniform_sum_recovers_interval(self):
        x = np.linspace(0.0, 2.0, 41)
        w = trapezoid_weights_1d(x)
        assert w.sum() == pytest.approx(2.0, rel=1e-14)

    def test_nonuniform_sum_recovers_interval(self):
        x = np.array([0.0, 0.1, 0.15, 0.4, 1.0])
        w = trapezoid_weights_1d(x)
        assert w.sum() == pytest.approx(1.0, rel=1e-14)

    def test_exact_for_linear_integrand(self):
        # The trapezoid rule is exact for degree-1 polynomials.
        x = np.array([0.0, 0.2, 0.5, 0.6, 1.3])
        w = trapezoid_weights_1d(x)
        f = 3.0 * x + 2.0
        exact = 1.5 * 1.3**2 + 2.0 * 1.3
        assert np.dot(w, f) == pytest.approx(exact, rel=1e-14)

    def test_rejects_non_increasing(self):
        with pytest.raises(ValueError, match="strictly increasing"):
            trapezoid_weights_1d(np.array([0.0, 1.0, 1.0]))

    def test_rejects_too_few_nodes(self):
        with pytest.raises(ValueError, match="at least two"):
            trapezoid_weights_1d(np.array([1.0]))


class TestStructuredGrid:
    def test_weight_sum_recovers_half_plane_area(self):
        r_max, z_max = 6.14e-3, 18.42e-3
        grid = structured_grid(r_max, z_max, n_r=31, n_z=47)
        assert grid.weights_m2.sum() == pytest.approx(
            r_max * z_max, rel=1e-12
        )

    def test_shape_and_ordering(self):
        grid = structured_grid(1.0, 2.0, n_r=3, n_z=5)
        assert grid.shape_rz == (3, 5)
        assert grid.n_nodes == 15
        # 'ij' ordering: r varies slowest, z fastest.
        assert np.array_equal(grid.r_m[:5], np.zeros(5))
        assert grid.z_m[0] == 0.0 and grid.z_m[4] == 2.0

    def test_axis_column_present(self):
        grid = structured_grid(1.0, 1.0, n_r=4, n_z=4)
        assert np.min(grid.r_m) == 0.0

    def test_rejects_negative_r_min(self):
        with pytest.raises(ValueError, match="half-plane"):
            structured_grid(1.0, 1.0, n_r=4, n_z=4, r_min_m=-0.1)

    def test_rejects_degenerate_extent(self):
        with pytest.raises(ValueError, match="extents"):
            structured_grid(0.0, 1.0, n_r=4, n_z=4)

    def test_rejects_too_few_nodes(self):
        with pytest.raises(ValueError, match=">= 2"):
            structured_grid(1.0, 1.0, n_r=1, n_z=4)


class TestGridSpec:
    def test_build_matches_structured_grid(self):
        spec = GridSpec(n_r=11, n_z=13)
        grid = spec.build(2.0e-3, 3.0e-3)
        assert grid.shape_rz == (11, 13)
        assert grid.weights_m2.sum() == pytest.approx(6.0e-6, rel=1e-12)

    def test_rejects_degenerate_resolution(self):
        with pytest.raises(ValueError, match=">= 2"):
            GridSpec(n_r=1, n_z=10)
