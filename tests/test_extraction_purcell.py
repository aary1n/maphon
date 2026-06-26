"""SPEC §3 F_m self-consistency anchor on Breeze inputs.

The SPEC §3 + user requirement: F_m must land in [3.4e7, 3.6e7] from
Q = 1e4, V = 0.2e-6 m^3, f = 1.45e9 Hz. The lower bound is loosened to
3.3e7 in `F_M_BENCHMARK` to absorb the SPEC §3 2-s.f. rounding (the
exact prefactor result is 3.36e7, which rounds up to 3.4e7).

This test must pass before extraction is considered implemented. If it
fails, the F_m formula or units are wrong — stop and fix before
trusting any F_m downstream.
"""

from __future__ import annotations

import math

import pytest

from cavity.extraction import magnetic_purcell_factor
from cavity.provenance import C_LIGHT, F_M_BENCHMARK, TARGETS


class TestFMBreezeBenchmark:
    """The SPEC §3 mandatory anchor."""

    def test_breeze_inputs_land_in_benchmark_range(self):
        """Q = 1e4, V = 0.2e-6 m^3, f = 1.45e9 Hz -> F_m in
        [F_M_BENCHMARK.f_m_lo, F_M_BENCHMARK.f_m_hi]."""
        anchor = TARGETS.breeze
        assert anchor.q_factor == 1.0e4
        assert anchor.v_mode_m3 == pytest.approx(0.2e-6, rel=1e-12)
        assert anchor.f_hz == pytest.approx(1.45e9, rel=1e-12)

        f_m = magnetic_purcell_factor(
            q=anchor.q_factor,
            v_mode_m3=anchor.v_mode_m3,
            f_hz=anchor.f_hz,
        )
        assert F_M_BENCHMARK.f_m_lo <= f_m <= F_M_BENCHMARK.f_m_hi, (
            f"F_m = {f_m:.3e} outside SPEC §3 benchmark range "
            f"[{F_M_BENCHMARK.f_m_lo:.2e}, {F_M_BENCHMARK.f_m_hi:.2e}]; "
            "the formula or the units are wrong — stop and fix."
        )

    def test_matches_exact_prefactor_value(self):
        """Direct hand-computation: F_m = (3/(2 pi)^2) * lambda^3 * (Q/V)."""
        q = 1.0e4
        v = 0.2e-6
        f = 1.45e9
        f_m = magnetic_purcell_factor(q, v, f)

        wavelength = C_LIGHT / f
        expected = (
            (3.0 / (2.0 * math.pi) ** 2) * wavelength ** 3 * q / v
        )
        assert f_m == pytest.approx(expected, rel=1e-12)
        # SPEC arithmetic: ~3.36e7.
        assert f_m == pytest.approx(3.36e7, rel=5e-3)

    def test_matches_breeze_tabulated_value_within_prefactor_gap(self):
        """Breeze tabulates 3.6e7; the ~7% gap is the printed-prefactor
        provenance trap SPEC §3 calls out."""
        anchor = TARGETS.breeze
        f_m = magnetic_purcell_factor(
            anchor.q_factor, anchor.v_mode_m3, anchor.f_hz
        )
        assert f_m == pytest.approx(anchor.f_m, rel=8e-2)

    def test_scales_linearly_with_q(self):
        f_m_1 = magnetic_purcell_factor(1.0e4, 0.2e-6, 1.45e9)
        f_m_2 = magnetic_purcell_factor(2.0e4, 0.2e-6, 1.45e9)
        assert f_m_2 == pytest.approx(2.0 * f_m_1, rel=1e-12)

    def test_scales_inversely_with_v_mode(self):
        f_m_a = magnetic_purcell_factor(1.0e4, 0.2e-6, 1.45e9)
        f_m_b = magnetic_purcell_factor(1.0e4, 0.4e-6, 1.45e9)
        assert f_m_a == pytest.approx(2.0 * f_m_b, rel=1e-12)

    def test_uses_provenance_c_light(self):
        """No local C constant — the value must come from provenance.
        Sanity check that re-computing with the provenance constant
        matches the function output bit-for-bit.
        """
        q, v, f = 1.0e4, 0.2e-6, 1.45e9
        wavelength = C_LIGHT / f
        manual = (3.0 / (2.0 * math.pi) ** 2) * wavelength ** 3 * q / v
        assert magnetic_purcell_factor(q, v, f) == manual

    @pytest.mark.parametrize(
        "q,v,f",
        [
            (0.0, 0.2e-6, 1.45e9),
            (-1.0, 0.2e-6, 1.45e9),
            (1.0e4, 0.0, 1.45e9),
            (1.0e4, -0.2e-6, 1.45e9),
            (1.0e4, 0.2e-6, 0.0),
            (1.0e4, 0.2e-6, -1.45e9),
        ],
    )
    def test_rejects_non_positive_inputs(self, q, v, f):
        with pytest.raises(ValueError):
            magnetic_purcell_factor(q, v, f)
