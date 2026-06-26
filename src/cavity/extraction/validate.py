"""SPEC §8 PEC + lossy-dielectric consistency check on extracted Q + p_e.

In the SPEC §4 PEC-walled variant (sigma_walls -> infinity), wall loss
is zero by construction and Q is set entirely by the dielectric. Energy
balance then forces

    Q = 1 / (p_e * tan delta).

This is the §8 traceability anchor — the assertion that pins the
COMSOL eigenfrequency sign convention (SPEC §11 gap #4) and the §3
volume-integral Jacobian. Run it on every PEC solve before any Q from
the IBC variant is trusted.

Tolerance comes from `EXTRACTION_TOL.q_pec_lossy_rel_tol`; pass
`rel_tol` to override for diagnostic comparisons.
"""

from __future__ import annotations

import math

from cavity.provenance import EXTRACTION_TOL


def assert_pec_lossy_q_consistency(
    q: float,
    p_e: float,
    tan_delta: float,
    rel_tol: float | None = None,
) -> None:
    """Assert Q ~= 1 / (p_e * tan delta) within tolerance (SPEC §8).

    Args:
        q: extracted Q (f'/(2 f'')) from a PEC-walled solve.
        p_e: extracted electric-energy filling factor.
        tan_delta: loss tangent supplied to the solve.
        rel_tol: override `EXTRACTION_TOL.q_pec_lossy_rel_tol`.

    Raises:
        ValueError: on out-of-range inputs.
        AssertionError: if Q vs 1/(p_e * tan delta) exceeds the tolerance
            — pointing to either an inverted COMSOL convention
            (SPEC §11 gap #4) or a §3 volume-integral Jacobian error.
    """
    if q <= 0:
        raise ValueError(f"q must be positive; got {q}")
    if not 0.0 < p_e <= 1.0:
        raise ValueError(f"p_e must lie in (0, 1]; got {p_e}")
    if tan_delta <= 0:
        raise ValueError(f"tan_delta must be positive; got {tan_delta}")

    tol = (
        EXTRACTION_TOL.q_pec_lossy_rel_tol
        if rel_tol is None
        else rel_tol
    )
    q_expected = 1.0 / (p_e * tan_delta)
    if not math.isclose(q, q_expected, rel_tol=tol):
        raise AssertionError(
            "SPEC §8 PEC + lossy-dielectric consistency failed: "
            f"extracted Q = {q} vs analytic 1/(p_e * tan delta) = "
            f"{q_expected} (p_e = {p_e}, tan delta = {tan_delta}); "
            f"rel tol = {tol}. Either the COMSOL eigenfrequency sign "
            "convention is inverted (SPEC §11 gap #4) or a §3 volume "
            "integral is missing the 2*pi*r Jacobian."
        )
