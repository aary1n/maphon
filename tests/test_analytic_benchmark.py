"""SPEC §8 analytic benchmark — pure-Python checks.

Every assertion in this file must pass before any COMSOL value is trusted
(SPEC §5 + CLAUDE.md). The COMSOL-recovery side of §8 (Q convention,
empty-cavity TE011 to <0.1%) is asserted separately once the forward
model is online; this file pins the closed-form ground truth.
"""

from __future__ import annotations

import math

import pytest

from cavity.provenance import GEOM, STO, TARGET
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


# Reference Bessel-zero values from Abramowitz & Stegun Table 9.5.
ABRAMOWITZ_J = {
    (0, 1): 2.4048255577,
    (0, 2): 5.5200781103,
    (1, 1): 3.8317059702,
    (1, 2): 7.0155866698,
    (2, 1): 5.1356223018,
}
ABRAMOWITZ_JPRIME = {
    (0, 1): 3.8317059702,  # SPEC §8: TE011 uses x'_01 = 3.8317.
    (0, 2): 7.0155866698,
    (1, 1): 1.8411837813,
    (1, 2): 5.3314427735,
    (2, 1): 3.0542369282,
}


class TestBesselZeros:
    """Verify scipy returns the textbook Bessel zeros."""

    @pytest.mark.parametrize("mn,expected", list(ABRAMOWITZ_J.items()))
    def test_j_zeros_match_abramowitz(self, mn, expected):
        m, n = mn
        assert bessel_zero_j(m, n) == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize("mn,expected", list(ABRAMOWITZ_JPRIME.items()))
    def test_jprime_zeros_match_abramowitz(self, mn, expected):
        m, n = mn
        assert bessel_zero_jprime(m, n) == pytest.approx(expected, rel=1e-9)

    def test_te011_x_prime_value_quoted_in_spec(self):
        """SPEC §8: TE011 uses x'_01 = 3.8317."""
        assert bessel_zero_jprime(0, 1) == pytest.approx(3.8317, abs=1e-4)

    def test_rejects_zero_index(self):
        with pytest.raises(ValueError):
            bessel_zero_j(0, 0)
        with pytest.raises(ValueError):
            bessel_zero_jprime(0, 0)


class TestEmptyCavityEigenfrequencies:
    """Closed-form TE/TM cylindrical-cavity frequencies."""

    def test_te011_canonical_5cm_cavity(self):
        """Pencil-and-paper anchor: empty cylinder a = L = 5 cm.

        f = (c/2pi) * sqrt[(x'_01/a)^2 + (pi/L)^2]
          = (c/2pi) * sqrt[(3.8317/0.05)^2 + (pi/0.05)^2]
          ~ 4.729 GHz.
        """
        f = f_te_mnp(0, 1, 1, a=0.05, L=0.05)
        assert f == pytest.approx(4.729e9, rel=1e-3)

    def test_te011_booth_box_empty_air(self):
        """Empty-air TE011 of Booth's box (no STO): the value COMSOL must hit.

        a = 6.14 mm, L = 18.42 mm -> ~30.87 GHz. With STO (epsilon_r ~316)
        this scales to O(1.7 GHz), consistent with the 1.45 GHz design once
        the puck only partially fills the box (TE01delta).
        """
        f = f_te_mnp(0, 1, 1, a=GEOM.box_radius_m, L=GEOM.box_height_m)
        # Hand-derived value (high precision):
        x = bessel_zero_jprime(0, 1)
        expected = (C_LIGHT / (2.0 * math.pi)) * math.sqrt(
            (x / GEOM.box_radius_m) ** 2 + (math.pi / GEOM.box_height_m) ** 2
        )
        assert f == pytest.approx(expected, rel=1e-12)
        assert 30.8e9 < f < 30.9e9

    def test_tm010_independent_of_length(self):
        """TM010 has p = 0: frequency depends on a only."""
        a = 0.05
        assert f_tm_mnp(0, 1, 0, a, L=0.10) == pytest.approx(
            f_tm_mnp(0, 1, 0, a, L=0.20), rel=1e-12
        )

    def test_te_requires_p_at_least_1(self):
        with pytest.raises(ValueError):
            f_te_mnp(0, 1, 0, 0.05, 0.10)

    def test_tm_allows_p_zero_but_rejects_negative(self):
        f_tm_mnp(0, 1, 0, 0.05, 0.10)  # should not raise
        with pytest.raises(ValueError):
            f_tm_mnp(0, 1, -1, 0.05, 0.10)

    def test_rejects_non_positive_dimensions(self):
        with pytest.raises(ValueError):
            f_te_mnp(0, 1, 1, a=0.0, L=0.05)
        with pytest.raises(ValueError):
            f_te_mnp(0, 1, 1, a=0.05, L=-0.05)


class TestQFromTanDelta:
    """Closed-form Q assertions in the limits SPEC §8 calls out.

    These pin the convention that the COMSOL extraction will be asserted
    against in tests/test_q_convention.py (SPEC §3: 'Do not trust the
    convention blind').
    """

    def test_q_homogeneous_at_sto_nominal(self):
        """tan delta = 1.1e-4 -> Q_diel ~ 9091."""
        assert q_dielectric_homogeneous(STO.tan_delta) == pytest.approx(
            1.0 / 1.1e-4, rel=1e-12
        )
        assert q_dielectric_homogeneous(1.1e-4) == pytest.approx(9090.9091, rel=1e-6)

    def test_partial_fill_reduces_to_homogeneous_at_full_fill(self):
        for td in (1.0e-4, 1.1e-4, 2.3e-4):
            assert q_dielectric_partial_fill(1.0, td) == pytest.approx(
                q_dielectric_homogeneous(td), rel=1e-12
            )

    def test_partial_fill_at_breeze_ceiling(self):
        """Breeze STO row: Q ~ 10,000 at tan delta = 1.1e-4 implies p_e ~ 0.909.

        Direct check of the SPEC §6 arithmetic
        (ceiling 1/tan delta = 9091 vs Breeze 10,000 -> wall-loss-free).
        """
        assert q_dielectric_partial_fill(0.909, 1.1e-4) == pytest.approx(
            10000.0, rel=2e-3
        )

    def test_partial_fill_inverse_in_tan_delta(self):
        q_low = q_dielectric_partial_fill(0.95, 1.1e-4)
        q_high = q_dielectric_partial_fill(0.95, 2.2e-4)
        assert q_low == pytest.approx(2.0 * q_high, rel=1e-12)

    @pytest.mark.parametrize("p_e", [0.0, -0.1, 1.5, 2.0])
    def test_partial_fill_rejects_out_of_range_pe(self, p_e):
        with pytest.raises(ValueError):
            q_dielectric_partial_fill(p_e, 1.1e-4)

    @pytest.mark.parametrize("td", [0.0, -1e-5])
    def test_rejects_non_positive_tan_delta(self, td):
        with pytest.raises(ValueError):
            q_dielectric_homogeneous(td)
        with pytest.raises(ValueError):
            q_dielectric_partial_fill(0.5, td)


class TestMagneticPurcellFormula:
    """SPEC §3 fixes F_m = (3/4pi^2) * lambda^3 * (Q / V_mode).

    Validation: Breeze STO row Q = 1e4, V_mode = 0.2 cm^3, f = 1.45 GHz
    must reproduce ~3.6e7 (SPEC computes 3.4e7 by the same formula --
    both within tolerance of the tabulated value).
    """

    def test_breeze_sto_row_order_1e7(self):
        v_mode_m3 = 0.2e-6  # 0.2 cm^3 in m^3
        f_m = magnetic_purcell_factor(q=1.0e4, v_mode_m3=v_mode_m3, f_hz=1.45e9)
        # SPEC arithmetic: (3/4pi^2) * (20.69 cm)^3 * (1e4 / 0.2 cm^3) ~ 3.37e7.
        assert f_m == pytest.approx(3.37e7, rel=5e-3)
        assert 3.0e7 < f_m < 4.0e7  # encompasses Breeze's tabulated 3.6e7.

    def test_uses_target_frequency_consistently(self):
        """Sanity: design f = 1.45 GHz and measured f_xz = 1.4493 GHz differ
        by ~600 ppm, swinging F_m by ~3x600 ppm = 0.18% via the lambda^3 factor."""
        v_mode_m3 = 0.2e-6
        f_m_design = magnetic_purcell_factor(1.0e4, v_mode_m3, TARGET.f_design_hz)
        f_m_meas = magnetic_purcell_factor(1.0e4, v_mode_m3, TARGET.f_xz_measured_hz)
        rel_swing = abs(f_m_design - f_m_meas) / f_m_design
        assert 1e-3 < rel_swing < 3e-3

    def test_scales_linearly_with_q(self):
        v_mode_m3 = 0.2e-6
        f_m_1 = magnetic_purcell_factor(1.0e4, v_mode_m3, 1.45e9)
        f_m_2 = magnetic_purcell_factor(2.0e4, v_mode_m3, 1.45e9)
        assert f_m_2 == pytest.approx(2.0 * f_m_1, rel=1e-12)

    def test_scales_inversely_with_v_mode(self):
        f_m_a = magnetic_purcell_factor(1.0e4, 0.2e-6, 1.45e9)
        f_m_b = magnetic_purcell_factor(1.0e4, 0.4e-6, 1.45e9)
        assert f_m_a == pytest.approx(2.0 * f_m_b, rel=1e-12)

    @pytest.mark.parametrize(
        "q,v,f",
        [(0.0, 1e-7, 1e9), (-1.0, 1e-7, 1e9), (1e4, 0.0, 1e9), (1e4, 1e-7, 0.0)],
    )
    def test_rejects_non_positive_inputs(self, q, v, f):
        with pytest.raises(ValueError):
            magnetic_purcell_factor(q, v, f)
