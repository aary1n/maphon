"""Validation — SPEC §5 gate + §8 analytic benchmark + §4 wall-loss split.

§8 (`analytic`) is pure Python and is the traceability anchor: the
COMSOL forward model must reproduce its closed-form values to <0.1%
before any number from the solver is trusted.

§4 (`wall_loss`) decomposes Q_total into Q_diel + Q_wall from two
solves (Impedance BC and PEC) of the same closed-cavity geometry,
with linear error propagation and a below-resolution flag for the
Breeze-end of the §6 confinement trend.

§5 (`gate`) is the Phase-1-complete check (f, Booth two-point,
confinement trend, wall-loss split, F_m order). Requires COMSOL,
stubbed.
"""

from cavity.validation.analytic import (
    C_LIGHT,
    bessel_zero_j,
    bessel_zero_jprime,
    f_te_mnp,
    f_tm_mnp,
    magnetic_purcell_factor,
    q_dielectric_homogeneous,
    q_dielectric_partial_fill,
)
from cavity.validation.wall_loss import (
    WallLossDecomposition,
    decompose_wall_loss,
)

__all__ = [
    "C_LIGHT",
    "WallLossDecomposition",
    "bessel_zero_j",
    "bessel_zero_jprime",
    "decompose_wall_loss",
    "f_te_mnp",
    "f_tm_mnp",
    "magnetic_purcell_factor",
    "q_dielectric_homogeneous",
    "q_dielectric_partial_fill",
]
