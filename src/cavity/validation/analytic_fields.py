"""SPEC §8 — closed-form TE011 field maps (the field-level analytic anchor).

`cavity.validation.analytic` anchors *frequencies* (Bessel-zero closed
forms) and *Q limits*; nothing in the repo anchored field-consuming
machinery until this module. It supplies the exact TE011 eigenfields of
an empty (vacuum, PEC-walled) right-circular cylinder, evaluated on the
same structured (r, z) grids the §3 extraction stack consumes, plus the
closed-form sub-region integrals (Lommel radial x elementary axial)
that pin the §3 weight functionals (`cavity.extraction.weights`) and
the export normalisation (`cavity.export`) to hand-derivable numbers.

Amplitude prefactor chain (LOAD-BEARING — do not re-normalise)
==============================================================
The three non-zero TE011 components are NOT three independent shape
functions: their relative amplitudes are fixed by Maxwell's equations,
and every energy-level anchor in this module tests exactly that chain.
With the SPEC §2 phasor convention e^{+i omega t}, cylindrical
components (r, phi, z), cavity radius a and length L (z in [0, L]):

    E_phi(r, z) = E0 *              J1(kc r) * sin(kz z)
    H_r(r, z)   = -i * (kz/(omega mu0)) * E0 * J1(kc r) * cos(kz z)
    H_z(r, z)   = +i * (kc/(omega mu0)) * E0 * J0(kc r) * sin(kz z)
    E_r = E_z = H_phi = 0

    kc = x'_01 / a   (x'_01 = first zero of J0' = first zero of J1,
                      3.8317..., via `bessel_zero_jprime(0, 1)`),
    kz = pi / L,
    omega^2 mu0 eps0 = kc^2 + kz^2   (the resonance condition; the
                      frequency is consumed from `f_te_mnp(0,1,1,a,L)`,
                      never re-derived here).

Derivation (each step checkable by hand):
  1. E_phi must vanish on the end plates (tangential at z = 0, L)
     => sin(kz z); and on the barrel (tangential at r = a)
     => J1(kc a) = 0, i.e. kc a = x'_01. Amplitude E0 fixes the scale.
  2. Faraday, e^{+i omega t}: curl E = -i omega mu0 H, and for
     E = E_phi(r, z) phi_hat:
         (curl E)_r = -dE_phi/dz,
         (curl E)_z = (1/r) d(r E_phi)/dr.
     With (1/x) d(x J1(x))/dx = J0(x) this gives the H_r and H_z lines
     above — including the -i / +i quadrature phases (H lags E by 90
     degrees: standing-wave energy exchange) and the kz/(omega mu0),
     kc/(omega mu0) prefactors.
  3. Ampere closes the loop: (curl H)_phi = dH_r/dz - dH_z/dr equals
     +i omega eps0 E_phi IF AND ONLY IF kc^2 + kz^2 = omega^2 mu0 eps0.
     The prefactor chain and the resonance condition are therefore one
     package; breaking either breaks the other.

Consequence for the anchors: the stored-energy identity U_E = U_H at
resonance holds only through this chain — via the Lommel integral both
radial integrals reduce to (a^2/2) J0^2(x'_01), so
    U_E = U_H = (pi/8) eps0 E0^2 a^2 L J0^2(x'_01)
with U_H's kz^2 + kc^2 collapsing under the resonance condition.
Implementing the three shape functions with independent unit amplitudes
makes U_E = U_H silently vacuous (it fails, or passes regardless of the
physics once re-normalised) — the reason the equality is asserted in
`tests/test_analytic_fields.py` against THIS docstring.

Closed-form sub-region integrals
================================
Radial (Lommel): int_0^b J_n^2(k r) r dr
    = (b^2/2) * [J_n'^2(kb) + (1 - n^2/(kb)^2) * J_n^2(kb)].
Axial (elementary): int sin^2/cos^2(kz z) dz over [z1, z2]
    = (z2 - z1)/2 -/+ [sin(2 kz z2) - sin(2 kz z1)]/(4 kz).
Products of the two give every coaxial-sub-cylinder energy integral the
weight anchors need, with zero numerical quadrature on the analytic
side. Tolerances in the tests are grid-resolution-bounded (composite
trapezoid, O(h^2)) and stated per anchor, §8 style.

Physical constants come from `scipy.constants` (CODATA), matching
`cavity.thermal.radiation` practice. Since the 2019 SI redefinition
mu0 and eps0 are measured values: mu0*eps0*c^2 = 1 only to ~1e-10,
far below every stated quadrature tolerance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.constants import epsilon_0 as EPS_0
from scipy.constants import mu_0 as MU_0
from scipy.special import j0, j1, jvp

from cavity.validation.analytic import bessel_zero_jprime, f_te_mnp


@dataclass(frozen=True)
class TE011Mode:
    """Exact TE011 eigenmode of an empty PEC right-circular cylinder.

    `e0_v_per_m` scales E_phi; the H amplitudes are then FIXED by the
    prefactor chain in the module docstring — they are exposed as
    derived properties, never as free parameters.
    """

    radius_m: float
    length_m: float
    e0_v_per_m: float = 1.0

    def __post_init__(self) -> None:
        if self.radius_m <= 0 or self.length_m <= 0:
            raise ValueError("radius_m and length_m must be positive")
        if self.e0_v_per_m <= 0:
            raise ValueError("e0_v_per_m must be positive")

    @property
    def k_c_per_m(self) -> float:
        """Radial wavenumber kc = x'_01 / a."""
        return bessel_zero_jprime(0, 1) / self.radius_m

    @property
    def k_z_per_m(self) -> float:
        """Axial wavenumber kz = pi / L (fundamental axial index p = 1)."""
        return math.pi / self.length_m

    @property
    def f_hz(self) -> float:
        """Resonant frequency — consumed from the §8 closed form."""
        return f_te_mnp(0, 1, 1, self.radius_m, self.length_m)

    @property
    def omega_rad_per_s(self) -> float:
        return 2.0 * math.pi * self.f_hz

    @property
    def h_r_amp_a_per_m(self) -> float:
        """|H_r| amplitude prefactor kz/(omega mu0) * E0 — Maxwell-fixed."""
        return self.k_z_per_m / (self.omega_rad_per_s * MU_0) * self.e0_v_per_m

    @property
    def h_z_amp_a_per_m(self) -> float:
        """|H_z| amplitude prefactor kc/(omega mu0) * E0 — Maxwell-fixed."""
        return self.k_c_per_m / (self.omega_rad_per_s * MU_0) * self.e0_v_per_m


def te011_fields(
    mode: TE011Mode,
    r_m: NDArray[np.floating],
    z_m: NDArray[np.floating],
) -> tuple[NDArray[np.complexfloating], NDArray[np.complexfloating]]:
    """Evaluate the TE011 fields at (r, z) nodes in the §3 contract shape.

    Returns `(e_complex, h_complex)`, both (N, 3) complex128 in
    cylindrical component order (r, phi, z) — the `FieldSample` layout.
    The relative amplitudes AND the -i/+i quadrature phases follow the
    module-docstring prefactor chain exactly.
    """
    r = np.asarray(r_m, dtype=np.float64)
    z = np.asarray(z_m, dtype=np.float64)
    if r.shape != z.shape or r.ndim != 1:
        raise ValueError("r_m and z_m must be same-shape 1D arrays")
    if np.any(r < 0):
        raise ValueError("r_m must be non-negative")

    kc_r = mode.k_c_per_m * r
    kz_z = mode.k_z_per_m * z

    n = r.shape[0]
    e = np.zeros((n, 3), dtype=np.complex128)
    h = np.zeros((n, 3), dtype=np.complex128)
    e[:, 1] = mode.e0_v_per_m * j1(kc_r) * np.sin(kz_z)
    h[:, 0] = -1j * mode.h_r_amp_a_per_m * j1(kc_r) * np.cos(kz_z)
    h[:, 2] = +1j * mode.h_z_amp_a_per_m * j0(kc_r) * np.sin(kz_z)
    return e, h


def lommel_jn_squared_integral(n: int, k: float, b: float) -> float:
    """int_0^b J_n^2(k r) r dr via the Lommel closed form.

    (b^2/2) * [J_n'^2(kb) + (1 - n^2/(kb)^2) * J_n^2(kb)]; b = 0
    returns 0 exactly (the n = 1 limit is finite but the integral
    vanishes).
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    if k <= 0:
        raise ValueError("k must be positive")
    if b < 0:
        raise ValueError("b must be non-negative")
    if b == 0.0:
        return 0.0
    x = k * b
    jn = float(jvp(n, x, 0))
    jnp = float(jvp(n, x, 1))
    return (b * b / 2.0) * (jnp * jnp + (1.0 - (n / x) ** 2) * jn * jn)


def sin_squared_axial_integral(k_z: float, z_lo: float, z_hi: float) -> float:
    """int_{z_lo}^{z_hi} sin^2(kz z) dz, closed form."""
    if k_z <= 0:
        raise ValueError("k_z must be positive")
    if z_hi < z_lo:
        raise ValueError("z_hi must be >= z_lo")
    return 0.5 * (z_hi - z_lo) - (
        math.sin(2.0 * k_z * z_hi) - math.sin(2.0 * k_z * z_lo)
    ) / (4.0 * k_z)


def cos_squared_axial_integral(k_z: float, z_lo: float, z_hi: float) -> float:
    """int_{z_lo}^{z_hi} cos^2(kz z) dz, closed form."""
    if k_z <= 0:
        raise ValueError("k_z must be positive")
    if z_hi < z_lo:
        raise ValueError("z_hi must be >= z_lo")
    return 0.5 * (z_hi - z_lo) + (
        math.sin(2.0 * k_z * z_hi) - math.sin(2.0 * k_z * z_lo)
    ) / (4.0 * k_z)


def te011_stored_energies(mode: TE011Mode) -> tuple[float, float]:
    """(U_E, U_H) in joules, each through its OWN closed-form chain.

    U_E = (eps0/4) int |E_phi|^2 dV uses the n = 1 Lommel integral;
    U_H = (mu0/4) int (|H_r|^2 + |H_z|^2) dV uses BOTH Lommel integrals
    and the Maxwell prefactors. The two are computed independently so
    the U_E == U_H resonance identity is a genuine cross-check of the
    prefactor chain (module docstring), not one formula echoed twice.
    Time-averaged peak-phasor densities (|.|^2 / 4 with peak phasors).
    """
    a, length = mode.radius_m, mode.length_m
    kc, kz = mode.k_c_per_m, mode.k_z_per_m

    radial_j1 = lommel_jn_squared_integral(1, kc, a)
    radial_j0 = lommel_jn_squared_integral(0, kc, a)
    axial_sin = sin_squared_axial_integral(kz, 0.0, length)
    axial_cos = cos_squared_axial_integral(kz, 0.0, length)

    # JACOBIAN: closed-form dV = 2*pi*r dr dz — the 2*pi rides here,
    # the r inside the Lommel integrals.
    u_e = (
        (EPS_0 / 4.0)
        * mode.e0_v_per_m**2
        * 2.0
        * math.pi
        * radial_j1
        * axial_sin
    )
    u_h = (
        (MU_0 / 4.0)
        * 2.0
        * math.pi
        * (
            mode.h_r_amp_a_per_m**2 * radial_j1 * axial_cos
            + mode.h_z_amp_a_per_m**2 * radial_j0 * axial_sin
        )
    )
    return u_e, u_h


def te011_electric_energy_fraction_inside_radius(
    mode: TE011Mode, b_m: float
) -> float:
    """Electric-energy fraction in the coaxial sub-cylinder r < b (full z).

    The axial sin^2 integral cancels in the ratio, so this is the pure
    n = 1 Lommel ratio — the closed form that IS a p_e for a synthetic
    'dielectric' sub-cylinder with eps_r = 1 (cavity-arm anchor).
    """
    if not 0.0 < b_m <= mode.radius_m:
        raise ValueError("b_m must lie in (0, radius_m]")
    kc = mode.k_c_per_m
    return lommel_jn_squared_integral(1, kc, b_m) / lommel_jn_squared_integral(
        1, kc, mode.radius_m
    )


def te011_h2_subregion_integral(
    mode: TE011Mode, b_m: float, z_lo_m: float, z_hi_m: float
) -> float:
    """int (|H_r|^2 + |H_z|^2) dV over the coaxial region r < b, z in [z_lo, z_hi].

    Closed form: Maxwell prefactors x Lommel radial x elementary axial
    integrals (H_phi = 0 for TE011). This is the spin-arm weight's
    normalisation integral over a crystal-like sub-region, hand-derivable.
    """
    if not 0.0 < b_m <= mode.radius_m:
        raise ValueError("b_m must lie in (0, radius_m]")
    if not 0.0 <= z_lo_m < z_hi_m <= mode.length_m:
        raise ValueError("need 0 <= z_lo < z_hi <= length_m")
    kc, kz = mode.k_c_per_m, mode.k_z_per_m
    # JACOBIAN: closed-form dV = 2*pi*r dr dz, as in te011_stored_energies.
    return (
        2.0
        * math.pi
        * (
            mode.h_r_amp_a_per_m**2
            * lommel_jn_squared_integral(1, kc, b_m)
            * cos_squared_axial_integral(kz, z_lo_m, z_hi_m)
            + mode.h_z_amp_a_per_m**2
            * lommel_jn_squared_integral(0, kc, b_m)
            * sin_squared_axial_integral(kz, z_lo_m, z_hi_m)
        )
    )


def te011_h2_total_integral(mode: TE011Mode) -> float:
    """int (|H_r|^2 + |H_z|^2) dV over the whole cavity, closed form."""
    return te011_h2_subregion_integral(
        mode, mode.radius_m, 0.0, mode.length_m
    )
