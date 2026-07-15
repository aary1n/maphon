"""L4 PCE — basis pins (45/36), orthonormality, exact recovery,
analytic-LOO vs brute-force refit, standardisation round trips.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.surrogate.pce import (
    PCESurrogate,
    legendre_orthonormal_1d,
    n_basis_terms,
    total_degree_indices,
)
from cavity.sweep.design import SamplingDim
from cavity.sweep.dofs import DistributionKind

RNG = np.random.default_rng(20260715)


def _uniform_dims(d: int) -> tuple[SamplingDim, ...]:
    """Uniform [0,1] dims: the CDF is the identity, so standardised
    coordinates equal the raw ones — ideal for exactness tests."""
    return tuple(
        SamplingDim(
            name=f"x{j}",
            lo=0.0,
            hi=1.0,
            nominal=0.5,
            distribution=DistributionKind.UNIFORM,
        )
        for j in range(d)
    )


# ---------------------------------------------------------------------------
# Basis
# ---------------------------------------------------------------------------


def test_order2_basis_counts_pinned_45_and_36():
    # §6/§9: C(8+2, 2) = 45 at d = 8; C(7+2, 2) = 36 at d = 7.
    assert n_basis_terms(8, 2) == 45
    assert n_basis_terms(7, 2) == 36


def test_total_degree_indices_complete_unique_and_bounded():
    for d, order in [(2, 3), (8, 2), (7, 2)]:
        indices = total_degree_indices(d, order)
        assert len(indices) == n_basis_terms(d, order)
        assert len(set(indices)) == len(indices)
        assert all(len(a) == d and sum(a) <= order for a in indices)
        assert indices[0] == (0,) * d  # constant term first


def test_indices_validate_inputs():
    with pytest.raises(ValueError):
        total_degree_indices(0, 2)
    with pytest.raises(ValueError):
        n_basis_terms(3, -1)


def test_legendre_orthonormal_on_unit_interval():
    # Gauss-Legendre quadrature (exact for polynomial products).
    nodes, weights = np.polynomial.legendre.leggauss(12)
    u = 0.5 * (nodes + 1.0)
    w = 0.5 * weights  # ∫₀¹ du
    for j in range(5):
        for k in range(5):
            inner = float(
                np.sum(
                    w
                    * legendre_orthonormal_1d(u, j)
                    * legendre_orthonormal_1d(u, k)
                )
            )
            assert inner == pytest.approx(
                1.0 if j == k else 0.0, abs=1e-12
            )


# ---------------------------------------------------------------------------
# Fit — exactness, LOO, refusals
# ---------------------------------------------------------------------------


def test_exact_recovery_of_an_in_basis_polynomial():
    d, order = 3, 2
    dims = _uniform_dims(d)
    indices = total_degree_indices(d, order)
    true_coeffs = RNG.normal(size=len(indices))
    x = RNG.uniform(size=(40, d))
    a = PCESurrogate._design_matrix(dims, indices, x)
    y = a @ true_coeffs
    s = PCESurrogate.fit(dims, x, y, order=order)
    np.testing.assert_allclose(s.coeffs, true_coeffs, atol=1e-10)
    assert s.q2 == pytest.approx(1.0, abs=1e-9)
    np.testing.assert_allclose(s.predict(x), y, atol=1e-9)


def test_analytic_loo_equals_brute_force_refit():
    d, order = 2, 2
    dims = _uniform_dims(d)
    x = RNG.uniform(size=(20, d))
    # A smooth NOT-in-basis response so residuals are non-trivial.
    y = np.sin(3.0 * x[:, 0]) + np.exp(x[:, 1])
    s = PCESurrogate.fit(dims, x, y, order=order)

    indices = total_degree_indices(d, order)
    a = PCESurrogate._design_matrix(dims, indices, x)
    e_loo_brute = np.empty(x.shape[0])
    for i in range(x.shape[0]):
        mask = np.arange(x.shape[0]) != i
        coeffs_i, *_ = np.linalg.lstsq(a[mask], y[mask], rcond=None)
        e_loo_brute[i] = y[i] - a[i] @ coeffs_i
    analytic_rmse = s.loo_rmse
    assert analytic_rmse == pytest.approx(
        float(np.sqrt(np.mean(e_loo_brute**2))), rel=1e-9
    )
    # ...and Q² from the same residuals.
    q2_brute = 1.0 - float(np.sum(e_loo_brute**2)) / float(
        np.sum((y - y.mean()) ** 2)
    )
    assert s.q2 == pytest.approx(q2_brute, rel=1e-9)


def test_underdetermined_fit_refused():
    dims = _uniform_dims(8)
    x = RNG.uniform(size=(40, 8))  # 40 < 45 order-2 terms
    y = RNG.normal(size=40)
    with pytest.raises(ValueError, match="under-determined"):
        PCESurrogate.fit(dims, x, y, order=2)


def test_rank_deficient_design_refused():
    dims = _uniform_dims(2)
    x = RNG.uniform(size=(30, 2))
    x[:, 1] = 0.5  # a constant dim: its Legendre columns collapse
    y = RNG.normal(size=30)
    with pytest.raises(ValueError, match="rank-deficient"):
        PCESurrogate.fit(dims, x, y, order=2)


def test_shape_validation():
    dims = _uniform_dims(2)
    with pytest.raises(ValueError, match="row counts"):
        PCESurrogate.fit(
            dims, RNG.uniform(size=(10, 2)), RNG.normal(size=9)
        )
    with pytest.raises(ValueError, match="inconsistent"):
        PCESurrogate._standardise(dims, RNG.uniform(size=(10, 3)))


def test_fit_is_deterministic():
    dims = _uniform_dims(2)
    x = RNG.uniform(size=(25, 2))
    y = x[:, 0] ** 2 + x[:, 1]
    a = PCESurrogate.fit(dims, x, y, order=2)
    b = PCESurrogate.fit(dims, x, y, order=2)
    np.testing.assert_array_equal(a.coeffs, b.coeffs)


def test_standardisation_uses_each_dims_own_cdf():
    """Non-uniform dims standardise through their own law: a
    truncated-Gaussian dim's median maps to u = 0.5 even though it is
    not the midpoint of an asymmetric band."""
    dim = SamplingDim(
        name="x",
        lo=0.0,
        hi=1.0,
        nominal=0.25,  # asymmetric truncation
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
    )
    u = PCESurrogate._standardise(
        (dim,), np.array([[dim.ppf(np.array([0.5]))[0]]])
    )
    assert u[0, 0] == pytest.approx(0.5, abs=1e-12)
