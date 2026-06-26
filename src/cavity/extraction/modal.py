"""SPEC §3 modal quantities: V_mode (global + local), p_e.

V_mode = (int |H|^2 dV) / |H|^2_max. SPEC §3 demands both variants
returned and labelled — the literature's 0.2-0.41 cm^3 spread is partly
this definitional choice (|H|^2_max taken globally over the cavity vs
locally over the dielectric / gain region). The validation gate
compares against the variant the source paper used; the forward model
must not silently pick one.

p_e (electric-energy filling factor) = (int_dielectric eps|E|^2 dV) /
(int_all eps|E|^2 dV). Required (not optional) — Q in §3 / §8 is
interpretable only with the filling factor. The real part of eps_r is
used: the imaginary part is loss and does not store electric energy
(coupling it into p_e would conflate confinement with dissipation).

Every volume integral routes through `axisymmetric_volume_integral`;
the 2*pi*r Jacobian rides inside that primitive.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from cavity.extraction.fields import FieldSample
from cavity.extraction.quadrature import axisymmetric_volume_integral


@dataclass(frozen=True)
class ModeVolumes:
    """SPEC §3 V_mode — both variants, in m^3.

    `global_m3`: |H|^2_max over the entire cavity.
    `local_m3`:  |H|^2_max over the gain region (defaults to the
                 dielectric; Phase 1b overrides to the crystal).

    Both come from the same int |H|^2 dV; only the normalising
    |H|^2_max differs. Booth's 0.409 cm^3 vs Breeze's 0.2 cm^3 lives in
    this choice as much as in the geometry.
    """

    global_m3: float
    local_m3: float


def _h_squared(field: FieldSample) -> NDArray[np.floating]:
    """|H|^2 = |H_r|^2 + |H_phi|^2 + |H_z|^2 at each node, real, A^2/m^2."""
    h2 = np.real(np.sum(field.h_complex * np.conj(field.h_complex), axis=1))
    return np.asarray(h2, dtype=np.float64)


def _e_squared(field: FieldSample) -> NDArray[np.floating]:
    """|E|^2 = |E_r|^2 + |E_phi|^2 + |E_z|^2 at each node, real, V^2/m^2."""
    e2 = np.real(np.sum(field.e_complex * np.conj(field.e_complex), axis=1))
    return np.asarray(e2, dtype=np.float64)


def mode_volumes(field: FieldSample) -> ModeVolumes:
    """V_mode = int |H|^2 dV / max(|H|^2), both global and local variants.

    SPEC §3: both must be returned and labelled.
    """
    h2 = _h_squared(field)
    # JACOBIAN: applied inside axisymmetric_volume_integral
    # (dV = 2*pi * r * dr * dz).
    h2_integral = axisymmetric_volume_integral(h2, field.r_m, field.weights_m2)

    h2_max_global = float(np.max(h2))

    gain_mask = field.effective_gain_mask
    if not np.any(gain_mask):
        raise ValueError(
            "gain_region_mask is empty — V_mode local undefined"
        )
    h2_max_local = float(np.max(h2[gain_mask]))

    if h2_max_global <= 0 or h2_max_local <= 0:
        raise ValueError(
            "|H|^2_max must be positive — degenerate or zero field"
        )

    integral_real = float(np.real(h2_integral))
    return ModeVolumes(
        global_m3=integral_real / h2_max_global,
        local_m3=integral_real / h2_max_local,
    )


def electric_filling_factor(field: FieldSample) -> float:
    """p_e = int_dielectric eps |E|^2 dV / int_all eps |E|^2 dV (SPEC §3).

    Uses Re(eps_r); the imaginary part is loss, not stored energy.
    """
    e2 = _e_squared(field)
    eps_real = np.real(field.eps_r_complex)
    energy_density = eps_real * e2

    integrand_diel = np.where(field.dielectric_mask, energy_density, 0.0)
    # JACOBIAN: applied inside axisymmetric_volume_integral on the
    # dielectric-masked integrand.
    num = axisymmetric_volume_integral(
        integrand_diel, field.r_m, field.weights_m2
    )
    # JACOBIAN: applied inside axisymmetric_volume_integral on the full
    # cavity integrand.
    den = axisymmetric_volume_integral(
        energy_density, field.r_m, field.weights_m2
    )

    den_real = float(np.real(den))
    num_real = float(np.real(num))
    if den_real <= 0:
        raise ValueError(
            "total electric energy non-positive — degenerate field "
            "or eps_r misconfigured"
        )
    p_e = num_real / den_real
    if not 0.0 < p_e <= 1.0:
        raise ValueError(
            f"p_e = {p_e} out of (0, 1] — check dielectric_mask, eps_r, "
            "and that the field is non-zero inside the dielectric"
        )
    return p_e
