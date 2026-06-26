"""SPEC §8 PEC + lossy-dielectric Q consistency hook.

Construct a synthetic field with a known p_e and a complex
eigenfrequency engineered so f'/(2 f'') = 1/(p_e * tan delta). The
hook must pass; perturb f'' outside tolerance and it must raise.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.extraction import (
    FieldSample,
    assert_pec_lossy_q_consistency,
    electric_filling_factor,
    q_from_eigenfrequency,
)
from cavity.provenance import EXTRACTION_TOL, STO

from tests._extraction_fixtures import make_structured_grid, zero_complex_3vec


def _two_domain_field(
    eps_dielectric: float,
    f_complex: complex,
) -> FieldSample:
    grid = make_structured_grid(
        r_lo=0.0, r_hi=6.0e-3, z_lo=0.0, z_hi=18.0e-3,
        n_r=121, n_z=181,
    )
    n = grid.r_m.size

    dielectric_mask = (
        (grid.r_m >= 1.0e-3)
        & (grid.r_m <= 3.0e-3)
        & (grid.z_m >= 4.0e-3)
        & (grid.z_m <= 14.0e-3)
    )
    eps_r = np.where(dielectric_mask, eps_dielectric, 1.0).astype(
        np.complex128
    )

    e = zero_complex_3vec(n)
    e[:, 1] = 1.0
    h = zero_complex_3vec(n)
    h[:, 2] = 1.0

    return FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=eps_r,
        weights_m2=grid.weights_m2,
        dielectric_mask=dielectric_mask,
        complex_eigenfrequency_hz=f_complex,
    )


class TestPecLossyConsistency:
    """SPEC §8 anchor — pins the COMSOL sign convention + §3 Jacobian."""

    def test_synthetic_field_passes_consistency(self):
        tan_delta = STO.tan_delta
        # Pull an unrelated f-complex first to compute p_e; then engineer
        # f'' to match the expected Q.
        f_seed = complex(1.45e9, 1.0e5)
        field_seed = _two_domain_field(
            eps_dielectric=316.3, f_complex=f_seed
        )
        p_e = electric_filling_factor(field_seed)

        q_expected = 1.0 / (p_e * tan_delta)
        f_prime = 1.45e9
        f_double_prime = f_prime / (2.0 * q_expected)
        f_complex = complex(f_prime, f_double_prime)

        field = _two_domain_field(
            eps_dielectric=316.3, f_complex=f_complex
        )
        p_e_again = electric_filling_factor(field)
        q = q_from_eigenfrequency(field.complex_eigenfrequency_hz)

        assert p_e_again == pytest.approx(p_e, rel=1e-12)
        assert q == pytest.approx(q_expected, rel=1e-12)
        # Should not raise.
        assert_pec_lossy_q_consistency(q, p_e_again, tan_delta)

    def test_perturbed_q_outside_tolerance_raises(self):
        tan_delta = STO.tan_delta
        p_e = 0.9
        q_expected = 1.0 / (p_e * tan_delta)
        q_bad = q_expected * (
            1.0 + 10.0 * EXTRACTION_TOL.q_pec_lossy_rel_tol
        )
        with pytest.raises(AssertionError, match="PEC \\+ lossy"):
            assert_pec_lossy_q_consistency(q_bad, p_e, tan_delta)

    def test_perturbed_q_within_tolerance_passes(self):
        tan_delta = STO.tan_delta
        p_e = 0.9
        q_expected = 1.0 / (p_e * tan_delta)
        q_ok = q_expected * (
            1.0 + 0.5 * EXTRACTION_TOL.q_pec_lossy_rel_tol
        )
        assert_pec_lossy_q_consistency(q_ok, p_e, tan_delta)

    def test_rejects_non_positive_inputs(self):
        with pytest.raises(ValueError):
            assert_pec_lossy_q_consistency(-1.0, 0.9, 1.1e-4)
        with pytest.raises(ValueError):
            assert_pec_lossy_q_consistency(1.0e4, 0.0, 1.1e-4)
        with pytest.raises(ValueError):
            assert_pec_lossy_q_consistency(1.0e4, 1.5, 1.1e-4)
        with pytest.raises(ValueError):
            assert_pec_lossy_q_consistency(1.0e4, 0.9, -1.1e-4)

    def test_rel_tol_override(self):
        tan_delta = STO.tan_delta
        p_e = 0.9
        q_expected = 1.0 / (p_e * tan_delta)
        q_drift = q_expected * 1.05  # 5% drift

        with pytest.raises(AssertionError):
            assert_pec_lossy_q_consistency(q_drift, p_e, tan_delta)
        # A looser override accepts the same drift:
        assert_pec_lossy_q_consistency(
            q_drift, p_e, tan_delta, rel_tol=0.1
        )
