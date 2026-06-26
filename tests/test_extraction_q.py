"""SPEC §3 Q extraction — analytic tests (4) and (5).

(4) COMSOL's imaginary-frequency sign convention: Im(f) > 0 yields
    positive Q; Im(f) <= 0 raises (no silent abs).
(5) emw.Qfactor is a cross-check only — never the primary Q. Matching
    values pass through; mismatched values raise AssertionError.
"""

from __future__ import annotations

import math

import pytest

from cavity.extraction import q_from_eigenfrequency
from cavity.provenance import EXTRACTION_TOL


def _f_complex_for_q(f_prime: float, q_target: float) -> complex:
    """Build f' + i*f'' with f'' chosen so f'/(2 f'') = q_target."""
    return complex(f_prime, f_prime / (2.0 * q_target))


class TestQFromComplexEigenfrequency:
    """Q = f' / (2 f'') with strict sign-convention enforcement."""

    def test_positive_imag_returns_positive_q(self):
        f_prime = 1.45e9
        q_target = 9091.0
        f = _f_complex_for_q(f_prime, q_target)
        q = q_from_eigenfrequency(f)
        assert q == pytest.approx(q_target, rel=1e-12)
        assert q > 0

    def test_im_f_zero_raises(self):
        with pytest.raises(ValueError, match="Im\\(f\\)"):
            q_from_eigenfrequency(complex(1.45e9, 0.0))

    def test_im_f_negative_raises_no_silent_abs(self):
        """The COMSOL convention assertion is the first line of defence
        against the SPEC §11 gap #4 sign trap. Silently abs()-ing Im(f)
        would hide the bug.
        """
        with pytest.raises(ValueError, match="convention is inverted"):
            q_from_eigenfrequency(complex(1.45e9, -1.0e4))

    def test_re_f_non_positive_raises(self):
        with pytest.raises(ValueError, match="Re\\(f\\)"):
            q_from_eigenfrequency(complex(-1.45e9, 1.0e4))

    def test_q_at_breeze_ceiling(self):
        """tan_delta = 1.1e-4, p_e = 1 -> Q = 1/tan_delta ~ 9091."""
        f = _f_complex_for_q(1.45e9, 1.0 / 1.1e-4)
        q = q_from_eigenfrequency(f)
        assert q == pytest.approx(1.0 / 1.1e-4, rel=1e-12)


class TestEmwQfactorCrossCheck:
    """SPEC §3: emw.Qfactor compared as cross-check, never primary."""

    def test_matching_cross_check_passes_through(self):
        q_target = 6_980.0
        f = _f_complex_for_q(1.45e9, q_target)
        q = q_from_eigenfrequency(f, q_emw_cross_check=q_target)
        assert q == pytest.approx(q_target, rel=1e-12)

    def test_cross_check_within_tolerance_passes(self):
        q_target = 6_980.0
        f = _f_complex_for_q(1.45e9, q_target)
        # Drift within EXTRACTION_TOL.q_emw_cross_check_rel_tol — accept.
        tol = EXTRACTION_TOL.q_emw_cross_check_rel_tol
        near = q_target * (1.0 + 0.5 * tol)
        q = q_from_eigenfrequency(f, q_emw_cross_check=near)
        assert q == pytest.approx(q_target, rel=1e-12)

    def test_cross_check_beyond_tolerance_raises(self):
        q_target = 6_980.0
        f = _f_complex_for_q(1.45e9, q_target)
        tol = EXTRACTION_TOL.q_emw_cross_check_rel_tol
        far = q_target * (1.0 + 10.0 * tol)
        with pytest.raises(AssertionError, match="cross-check"):
            q_from_eigenfrequency(f, q_emw_cross_check=far)

    def test_primary_value_is_f_prime_over_two_f_double_prime_not_emw(self):
        """If the caller hands in an emw.Qfactor in the same ballpark
        (within tolerance), the returned Q is still f'/(2 f'') — not the
        cross-check value. We engineer the inputs so the two differ by
        an amount that survives `isclose` and check the return.
        """
        q_primary = 6_980.0
        f = _f_complex_for_q(1.45e9, q_primary)
        tol = EXTRACTION_TOL.q_emw_cross_check_rel_tol
        near = q_primary * (1.0 + 0.5 * tol)
        q = q_from_eigenfrequency(f, q_emw_cross_check=near)
        # Returned q is f'/(2 f'') == q_primary, NOT `near`.
        assert math.isclose(q, q_primary, rel_tol=1e-12)
        assert q != near

    def test_negative_cross_check_rejected(self):
        f = _f_complex_for_q(1.45e9, 9_091.0)
        with pytest.raises(ValueError, match="must be positive"):
            q_from_eigenfrequency(f, q_emw_cross_check=-1.0)

    def test_explicit_rel_tol_overrides_default(self):
        q_target = 6_980.0
        f = _f_complex_for_q(1.45e9, q_target)
        # A drift that's beyond the default but accepted with a looser
        # override:
        loose = q_target * (1.0 + 0.05)
        with pytest.raises(AssertionError):
            q_from_eigenfrequency(
                f, q_emw_cross_check=loose,
                rel_tol=EXTRACTION_TOL.q_emw_cross_check_rel_tol,
            )
        q = q_from_eigenfrequency(
            f, q_emw_cross_check=loose, rel_tol=0.1
        )
        assert q == pytest.approx(q_target, rel=1e-12)
