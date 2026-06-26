"""SPEC §3 quality factor from the complex eigenfrequency.

The primary value is Q = f' / (2 f'') with f = f' + i*f''. COMSOL also
exposes a built-in `emw.Qfactor` scalar; SPEC §3 is emphatic that this
is **not** the primary value — it is used only as a cross-check, and
must not silently shadow f'/(2 f'').

The sign convention is asserted before any Q flows downstream (SPEC §3
"do not trust the convention blind", and §11 gap #4). We refuse to
silently abs() Im(f): if it is non-positive, the COMSOL output is in a
flipped convention and the caller must resolve that explicitly via the
§8 PEC + lossy-dielectric check (see `cavity.extraction.validate`).
"""

from __future__ import annotations

import math

from cavity.provenance import EXTRACTION_TOL


def q_from_eigenfrequency(
    f_complex: complex,
    q_emw_cross_check: float | None = None,
    rel_tol: float | None = None,
) -> float:
    """Q = f' / (2 f''). emw.Qfactor is verified as a cross-check if supplied.

    Args:
        f_complex: COMSOL eigenfrequency, f' + i*f''.
        q_emw_cross_check: optional emw.Qfactor scalar from the same
            solve. If supplied, it must agree with f'/(2 f'') within
            `EXTRACTION_TOL.q_emw_cross_check_rel_tol` (override with
            `rel_tol`). It is never used as the primary Q.
        rel_tol: override the default emw.Qfactor cross-check
            tolerance.

    Returns:
        Q from f'/(2 f'').

    Raises:
        ValueError: if Re(f) <= 0 or Im(f) <= 0 (sign convention
            failure; SPEC §11 gap #4).
        AssertionError: if the optional emw.Qfactor disagrees with
            f'/(2 f'') beyond the cross-check tolerance.
    """
    f_prime = f_complex.real
    f_double_prime = f_complex.imag
    if f_prime <= 0:
        raise ValueError(
            f"Re(f) must be positive; got {f_prime} Hz"
        )
    if f_double_prime <= 0:
        raise ValueError(
            f"Im(f) must be > 0 for Q = f'/(2 f''); got {f_double_prime} Hz. "
            "COMSOL eigenfrequency sign convention is inverted — resolve "
            "via the SPEC §8 1/(p_e * tan delta) limit before downstream "
            "use (SPEC §11 gap #4). Do not silently abs() Im(f)."
        )

    q = f_prime / (2.0 * f_double_prime)

    if q_emw_cross_check is not None:
        if q_emw_cross_check <= 0:
            raise ValueError(
                "emw.Qfactor cross-check must be positive; "
                f"got {q_emw_cross_check}"
            )
        tol = (
            EXTRACTION_TOL.q_emw_cross_check_rel_tol
            if rel_tol is None
            else rel_tol
        )
        if not math.isclose(q, q_emw_cross_check, rel_tol=tol):
            raise AssertionError(
                f"emw.Qfactor cross-check {q_emw_cross_check} disagrees "
                f"with primary f'/(2 f'') = {q} beyond rel tol {tol}. "
                "SPEC §3: emw.Qfactor is a cross-check only — primary "
                "value is f'/(2 f''). Investigate the COMSOL eigenpair "
                "before any downstream Q is trusted."
            )

    return q
