"""SPEC §3 magnetic Purcell factor.

    F_m = (3 / (2 pi)^2) * lambda^3 * (Q / V_mode),    lambda = c / f.

SPEC §3 fixes this form (the standard Purcell expression), **not**
Breeze's printed prefactor — which is dimensionally inconsistent and
reproduces Breeze Table 1 only by happening to land in the same ~3e7
ballpark. The validation anchor is the Breeze STO row (Q = 1e4, V =
0.2e-6 m^3, f = 1.45 GHz): F_m must land in
`[F_M_BENCHMARK.f_m_lo, F_M_BENCHMARK.f_m_hi]`, where the lower bound
covers the formula's exact 3.36e7 and the upper bound is Breeze's
tabulated 3.6e7. Falling outside the range means the formula or units
are wrong; stop and fix before any F_m downstream is trusted.

c is imported from `cavity.provenance` — no local physical-constant
literals.
"""

from __future__ import annotations

import math

from cavity.provenance import C_LIGHT


def magnetic_purcell_factor(q: float, v_mode_m3: float, f_hz: float) -> float:
    """F_m = (3 / (2 pi)^2) * lambda^3 * (Q / V_mode), SI in / SI out.

    Args:
        q: quality factor (dimensionless).
        v_mode_m3: magnetic mode volume (m^3).
        f_hz: real eigenfrequency (Hz).

    Returns:
        F_m (dimensionless).
    """
    if q <= 0 or v_mode_m3 <= 0 or f_hz <= 0:
        raise ValueError(
            "q, v_mode_m3, f_hz must all be positive; "
            f"got q={q}, V={v_mode_m3}, f={f_hz}"
        )
    wavelength_m = C_LIGHT / f_hz
    return (3.0 / (2.0 * math.pi) ** 2) * wavelength_m ** 3 * q / v_mode_m3
