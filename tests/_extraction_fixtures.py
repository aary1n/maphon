"""Shared synthetic-field builders for the cavity.extraction tests.

Underscore-prefixed so pytest does not collect this file. Helpers build
small structured (r, z) grids with explicit trapezoid quadrature
weights (m^2) — the §3-compliant input shape the extraction primitive
consumes. Raw `numpy.trapz` is forbidden by SPEC §3, so the weight
arrays are constructed once here and reused by every test.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


def _trapezoid_weights_1d(x: NDArray[np.floating]) -> NDArray[np.floating]:
    """Closed trapezoid weights w_i so sum(w_i * f_i) ~= integral of f over x.

    For uniform x this is the textbook composite trapezoid rule; for
    non-uniform x it generalises to (x_{i+1} - x_{i-1}) / 2 at interior
    nodes and the half-spacing at endpoints.
    """
    if x.ndim != 1 or x.size < 2:
        raise ValueError("x must be 1D with at least two nodes")
    w = np.empty_like(x, dtype=np.float64)
    w[0] = 0.5 * (x[1] - x[0])
    w[-1] = 0.5 * (x[-1] - x[-2])
    if x.size > 2:
        w[1:-1] = 0.5 * (x[2:] - x[:-2])
    return w


@dataclass(frozen=True)
class StructuredAxisymmetricGrid:
    """Tensor-product (r, z) grid flattened to 1D node arrays.

    `r_m`, `z_m`, `weights_m2`: (N,) arrays where N = n_r * n_z, with
    weights_m2 = w_r * w_z node-by-node.
    `shape_rz`: (n_r, n_z) for callers that want to reshape per-node
    arrays back into a grid for index masking.
    """

    r_m: NDArray[np.floating]
    z_m: NDArray[np.floating]
    weights_m2: NDArray[np.floating]
    shape_rz: tuple[int, int]


def make_structured_grid(
    r_lo: float,
    r_hi: float,
    z_lo: float,
    z_hi: float,
    n_r: int,
    n_z: int,
) -> StructuredAxisymmetricGrid:
    """Build a uniform tensor-product (r, z) grid with trapezoid weights.

    All distances in metres. The weight at node (i, j) is w_r[i] *
    w_z[j], so sum(weights) recovers the r-z plane area (r_hi - r_lo) *
    (z_hi - z_lo) exactly.
    """
    if n_r < 2 or n_z < 2:
        raise ValueError("n_r and n_z must each be >= 2")
    r = np.linspace(r_lo, r_hi, n_r)
    z = np.linspace(z_lo, z_hi, n_z)
    w_r = _trapezoid_weights_1d(r)
    w_z = _trapezoid_weights_1d(z)

    rr, zz = np.meshgrid(r, z, indexing="ij")
    wr, wz = np.meshgrid(w_r, w_z, indexing="ij")
    weights = wr * wz

    return StructuredAxisymmetricGrid(
        r_m=rr.ravel(),
        z_m=zz.ravel(),
        weights_m2=weights.ravel(),
        shape_rz=(n_r, n_z),
    )


def zero_complex_3vec(n: int) -> NDArray[np.complexfloating]:
    """(n, 3) zero complex array — fill component-by-component for fields."""
    return np.zeros((n, 3), dtype=np.complex128)
