"""Validation — SPEC §5 gate + §8 analytic benchmark.

§8 (this module's `analytic`) is pure Python and is the traceability
anchor: the COMSOL forward model must reproduce its closed-form values
to <0.1% before any number from the solver is trusted.

§5 (`gate`) is the Phase-1-complete check (f, Booth two-point, confinement
trend, wall-loss split, F_m order). Requires COMSOL — stubbed.
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

__all__ = [
    "C_LIGHT",
    "bessel_zero_j",
    "bessel_zero_jprime",
    "f_te_mnp",
    "f_tm_mnp",
    "magnetic_purcell_factor",
    "q_dielectric_homogeneous",
    "q_dielectric_partial_fill",
]
