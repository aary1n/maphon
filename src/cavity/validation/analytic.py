"""SPEC §8 — closed-form analytic benchmark (pure Python).

The empty (air-filled) right-circular copper cylinder has tabulated
eigenfrequencies via Bessel zeros; a homogeneously dielectric-filled
cavity has Q = 1/tan(delta), and a partial-fill cavity has
Q = 1/(p_e * tan(delta)) where p_e is the electric-energy filling
factor.

These are the traceability anchor in the Oxborrow 2007 sense
(IEEE TMTT 55, 1209). The COMSOL forward model must reproduce:

  - the empty-cavity TE011 frequency to <0.1% (mesh-limited), and
  - the Q-in-the-limit formulas to within extraction tolerance.

Sign convention: Q = Re(f) / (2 * Im(f)) with f = f' + i*f''. This
module computes Q from the closed forms; the COMSOL convention is
asserted against these in tests/test_q_convention.py once §2 is online.
"""

from __future__ import annotations

import math

from scipy.special import jn_zeros, jnp_zeros

C_LIGHT: float = 299_792_458.0


def bessel_zero_j(m: int, n: int) -> float:
    """Return the n-th positive zero of J_m (n is 1-indexed)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return float(jn_zeros(m, n)[-1])


def bessel_zero_jprime(m: int, n: int) -> float:
    """Return the n-th positive zero of J_m' (n is 1-indexed)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return float(jnp_zeros(m, n)[-1])


def f_te_mnp(m: int, n: int, p: int, a: float, L: float) -> float:
    """TE_mnp eigenfrequency of an empty right-circular cylindrical cavity.

    f = (c / 2 pi) * sqrt[(x'_mn / a)^2 + (p * pi / L)^2]

    a, L in metres; result in Hz. p >= 1 (TE_mn0 is not a resonant cavity mode).
    """
    if p < 1:
        raise ValueError("p must be >= 1 for a TE cavity mode")
    if a <= 0 or L <= 0:
        raise ValueError("a and L must be positive")
    xpmn = bessel_zero_jprime(m, n)
    return (C_LIGHT / (2.0 * math.pi)) * math.sqrt(
        (xpmn / a) ** 2 + (p * math.pi / L) ** 2
    )


def f_tm_mnp(m: int, n: int, p: int, a: float, L: float) -> float:
    """TM_mnp eigenfrequency of an empty right-circular cylindrical cavity.

    f = (c / 2 pi) * sqrt[(x_mn / a)^2 + (p * pi / L)^2]

    a, L in metres; result in Hz. p >= 0 (TM_mn0 exists).
    """
    if p < 0:
        raise ValueError("p must be >= 0 for a TM cavity mode")
    if a <= 0 or L <= 0:
        raise ValueError("a and L must be positive")
    xmn = bessel_zero_j(m, n)
    return (C_LIGHT / (2.0 * math.pi)) * math.sqrt(
        (xmn / a) ** 2 + (p * math.pi / L) ** 2
    )


def q_dielectric_homogeneous(tan_delta: float) -> float:
    """Q of a homogeneously dielectric-filled, PEC-walled cavity.

    Q_diel = 1 / tan(delta).
    """
    if tan_delta <= 0:
        raise ValueError("tan_delta must be positive")
    return 1.0 / tan_delta


def q_dielectric_partial_fill(p_e: float, tan_delta: float) -> float:
    """Q with electric-energy filling factor p_e in the dielectric.

    Q = 1 / (p_e * tan(delta)). Reduces to the homogeneous case at p_e = 1.
    """
    if not 0.0 < p_e <= 1.0:
        raise ValueError("p_e must lie in (0, 1]")
    if tan_delta <= 0:
        raise ValueError("tan_delta must be positive")
    return 1.0 / (p_e * tan_delta)


def magnetic_purcell_factor(q: float, v_mode_m3: float, f_hz: float) -> float:
    """Standard magnetic Purcell factor.

    F_m = (3 / (4 pi^2)) * lambda^3 * (Q / V_mode), with lambda = c / f.

    SPEC §3 fixes this form (NOT Breeze's printed prefactor, which is
    dimensionally inconsistent); the validation test checks it reproduces
    Breeze's STO row (~3.4-3.6e7 from Q=1e4, V=0.2 cm^3, f=1.45 GHz).
    """
    if q <= 0 or v_mode_m3 <= 0 or f_hz <= 0:
        raise ValueError("q, v_mode_m3, f_hz must all be positive")
    wavelength = C_LIGHT / f_hz
    return (3.0 / (4.0 * math.pi**2)) * wavelength**3 * q / v_mode_m3
