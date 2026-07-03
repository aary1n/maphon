"""SPEC §3 export contract — structured (r, z) grid with explicit weights.

The extraction layer refuses raw nodal samples: every node must carry an
r-z plane quadrature weight in m^2 (the 2*pi*r Jacobian is applied
inside `axisymmetric_volume_integral`, in one place). COMSOL's mesh
nodes are unstructured and carry no such weights, so solver fields are
resampled onto a tensor-product (r, z) grid built here, with closed
composite-trapezoid weights whose sum recovers the half-plane area
exactly.

Pure Python/numpy. `solve.py` owns the COMSOL-side evaluation and the
scipy resampling; this module owns only the grid and its weights.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


def trapezoid_weights_1d(x: NDArray[np.floating]) -> NDArray[np.floating]:
    """Closed trapezoid weights w_i so sum(w_i * f_i) ~= integral of f.

    Uniform x gives the textbook composite rule; non-uniform x
    generalises to (x_{i+1} - x_{i-1}) / 2 at interior nodes and the
    half-spacing at the endpoints. Strictly increasing x required.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1 or x.size < 2:
        raise ValueError("x must be 1D with at least two nodes")
    if np.any(np.diff(x) <= 0):
        raise ValueError("x must be strictly increasing")
    w = np.empty_like(x)
    w[0] = 0.5 * (x[1] - x[0])
    w[-1] = 0.5 * (x[-1] - x[-2])
    if x.size > 2:
        w[1:-1] = 0.5 * (x[2:] - x[:-2])
    return w


@dataclass(frozen=True)
class StructuredGrid:
    """Tensor-product (r, z) grid flattened to 1D node arrays.

    `r_m`, `z_m`, `weights_m2`: (N,) arrays with N = n_r * n_z and
    weights_m2 = w_r * w_z node-by-node ('ij' ordering: r varies
    slowest). `shape_rz` = (n_r, n_z) lets callers reshape per-node
    arrays back into the grid for profile extraction (mode-ID walks
    the axis column this way).
    """

    r_m: NDArray[np.floating]
    z_m: NDArray[np.floating]
    weights_m2: NDArray[np.floating]
    shape_rz: tuple[int, int]

    @property
    def n_nodes(self) -> int:
        return self.r_m.shape[0]


def structured_grid(
    r_max_m: float,
    z_max_m: float,
    n_r: int,
    n_z: int,
    r_min_m: float = 0.0,
    z_min_m: float = 0.0,
) -> StructuredGrid:
    """Uniform tensor-product (r, z) grid with trapezoid weights.

    sum(weights_m2) recovers (r_max - r_min) * (z_max - z_min) exactly
    (up to float rounding), which the tests assert.
    """
    if n_r < 2 or n_z < 2:
        raise ValueError("n_r and n_z must each be >= 2")
    if r_max_m <= r_min_m or z_max_m <= z_min_m:
        raise ValueError("grid extents must be positive")
    if r_min_m < 0:
        raise ValueError("r_min_m must be >= 0 (axisymmetric half-plane)")
    r = np.linspace(r_min_m, r_max_m, n_r)
    z = np.linspace(z_min_m, z_max_m, n_z)
    w_r = trapezoid_weights_1d(r)
    w_z = trapezoid_weights_1d(z)

    rr, zz = np.meshgrid(r, z, indexing="ij")
    wr, wz = np.meshgrid(w_r, w_z, indexing="ij")

    return StructuredGrid(
        r_m=rr.ravel(),
        z_m=zz.ravel(),
        weights_m2=(wr * wz).ravel(),
        shape_rz=(n_r, n_z),
    )


@dataclass(frozen=True)
class GridSpec:
    """Resolution of the §3 export grid, part of the solve fingerprint.

    Defaults resolve the Booth box (6.14 x 18.42 mm half-plane) to
    ~30 um in r and ~60 um in z — below the dielectric mesh scale, so
    the resampling is not the resolution bottleneck for V_mode / p_e.
    The E-field normal discontinuity at the dielectric boundary is
    smeared over one grid cell by the linear resampling; refine the
    grid, not the mesh, if p_e convergence stalls.
    """

    n_r: int = 201
    n_z: int = 301

    def __post_init__(self) -> None:
        if self.n_r < 2 or self.n_z < 2:
            raise ValueError("grid resolution must be >= 2 in each direction")

    def build(self, r_max_m: float, z_max_m: float) -> StructuredGrid:
        return structured_grid(r_max_m, z_max_m, self.n_r, self.n_z)
