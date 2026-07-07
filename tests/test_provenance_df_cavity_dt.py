"""SPEC §6T — CavityFreqTempCoefficient derivation guards (no COMSOL).

Pins the graded df_cavity/dT constant: sign (positive, opposite to the
spin arm — the differential detuning ADDS), magnitude against an
independent hand calculation, the no-fresh-literals consistency between
the stored point value and the derivation function evaluated at the
canonical εr/f, the band/window composition rule, and the 112 K
validity guard.

Band endpoints are checked THROUGH the derivation function at test time
(never against stored endpoint literals), so any future edit that makes
the band, window, and Curie-Weiss parameters mutually inconsistent
fails loudly here.
"""

import math

import pytest

from cavity.provenance.constants import (
    DF_CAVITY_DT,
    DF_SPIN_DT,
    STO,
    TARGET,
    cavity_df_dt_hz_per_k,
)


class TestSignConvention:
    def test_cavity_arm_positive(self):
        """Cavity mode blue-shifts on heating (dεr/dT < 0, f ∝ εr^-1/2)."""
        assert DF_CAVITY_DT.df_dt_hz_per_k > 0

    def test_opposite_sign_to_spin_arm(self):
        assert DF_CAVITY_DT.df_dt_hz_per_k * DF_SPIN_DT.df_dt_hz_per_k < 0

    def test_differential_adds(self):
        """SPEC §6T: |df_cav/dT - df_spin/dT| = df_cav/dT + |df_spin/dT|."""
        cav = DF_CAVITY_DT.df_dt_hz_per_k
        spin = DF_SPIN_DT.df_dt_hz_per_k
        assert abs(cav - spin) == cav + abs(spin)

    def test_function_positive_across_window(self):
        for temp_k in (
            DF_CAVITY_DT.t_window_lo_k,
            DF_CAVITY_DT.t_ref_k,
            DF_CAVITY_DT.t_window_hi_k,
        ):
            assert cavity_df_dt_hz_per_k(temp_k) > 0


class TestMagnitude:
    def test_hand_calculation_at_300k(self):
        """Independent arithmetic, written out in full.

        R&B 1962 Eq. (1): dεr/dT = -C/(T - T0)² = -8.25e4/263² =
        -1.1927 /K at 300 K; df/dT = -(f/2)·(dεr/dT)/εr with the
        canonical εr = 316.3 and f = 1.45 GHz ⇒ +2.734e6 Hz/K.
        """
        d_eps_dt = -8.25e4 / (300.0 - 37.0) ** 2
        expected = -(1.45e9 / 2.0) * d_eps_dt / 316.3
        assert math.isclose(
            cavity_df_dt_hz_per_k(300.0), expected, rel_tol=1e-9
        )
        assert math.isclose(expected, 2.734e6, rel_tol=1e-3)


class TestCanonicalInputConsistency:
    def test_stored_point_value_matches_function_at_t_ref(self):
        """The stored literal is the function at t_ref, 3-s.f. rounded."""
        assert math.isclose(
            DF_CAVITY_DT.df_dt_hz_per_k,
            cavity_df_dt_hz_per_k(DF_CAVITY_DT.t_ref_k),
            rel_tol=5e-3,
        )

    def test_defaults_are_the_canonical_constants(self):
        """No-fresh-literals guard: the default-arg call must equal the
        call wired explicitly to STO.epsilon_r_real / TARGET.f_design_hz
        and the constant's own Curie-Weiss fields."""
        explicit = cavity_df_dt_hz_per_k(
            DF_CAVITY_DT.t_ref_k,
            f_hz=TARGET.f_design_hz,
            epsilon_r=STO.epsilon_r_real,
            curie_constant_k=DF_CAVITY_DT.curie_constant_k,
            curie_weiss_t0_k=DF_CAVITY_DT.curie_weiss_t0_k,
        )
        assert cavity_df_dt_hz_per_k(DF_CAVITY_DT.t_ref_k) == explicit


class TestBandAndWindow:
    def test_window_brackets_t_ref(self):
        assert (
            DF_CAVITY_DT.t_window_lo_k
            < DF_CAVITY_DT.t_ref_k
            < DF_CAVITY_DT.t_window_hi_k
        )

    def test_band_ordering_and_point_containment(self):
        assert (
            DF_CAVITY_DT.df_dt_band_lo_hz_per_k
            < DF_CAVITY_DT.df_dt_hz_per_k
            < DF_CAVITY_DT.df_dt_band_hi_hz_per_k
        )

    def test_band_covers_window_endpoint_evaluations(self):
        """Band endpoints computed via the derivation function at test
        time, never stored endpoint literals. The local slope decreases
        monotonically in T, so the window's hi end bounds the band's
        low side and vice versa."""
        assert DF_CAVITY_DT.df_dt_band_lo_hz_per_k <= cavity_df_dt_hz_per_k(
            DF_CAVITY_DT.t_window_hi_k
        )
        assert DF_CAVITY_DT.df_dt_band_hi_hz_per_k >= cavity_df_dt_hz_per_k(
            DF_CAVITY_DT.t_window_lo_k
        )


class TestValidityGuard:
    def test_raises_below_phase_transition(self):
        with pytest.raises(ValueError, match="112"):
            cavity_df_dt_hz_per_k(100.0)

    def test_floor_itself_evaluates(self):
        assert cavity_df_dt_hz_per_k(DF_CAVITY_DT.t_validity_floor_k) > 0
