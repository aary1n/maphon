"""Lineshape + power-model guards (calibration/lineshape.py).

Anchor tests fit committed synthetic truth sets (§8 discipline: known
parameters in, recovered parameters out within stated tolerance). The
D6 gate tests are the pre-registration substance: they pin the claim
thresholds in code BEFORE any raw number exists to look at."""

from __future__ import annotations

import numpy as np
import pytest

from calibration.lineshape import (
    D6_MIN_DELTA_AICC,
    D6_MIN_POWER_POINTS,
    EXTRAPOLATION_REFUSAL,
    LineshapeError,
    fit_power_models,
    fit_spectrum,
    gaussian,
    lorentzian,
    voigt_effective_fwhm,
    zero_power_extrapolation,
)

RNG = np.random.default_rng(20260720)


def _lorentzian_spectrum(f0=1.4493e9, fwhm=1.4e6, amp=-0.06, noise=1e-4):
    freq = np.linspace(f0 - 8e6, f0 + 8e6, 161)
    clean = lorentzian(freq, f0, fwhm, amp, 1.0, 0.0)
    return freq, clean + RNG.normal(0.0, noise, freq.size)


class TestSpectrumFits:
    def test_lorentzian_truth_recovery(self):
        f0, fwhm = 1.4493e9, 1.4e6
        freq, signal = _lorentzian_spectrum(f0=f0, fwhm=fwhm)
        fit = fit_spectrum(freq, signal, model="lorentzian", sigma=1e-4)
        assert fit.f0_hz == pytest.approx(f0, abs=5e3)
        assert fit.fwhm_hz == pytest.approx(fwhm, rel=0.02)
        assert fit.chi2_dof == pytest.approx(1.0, abs=0.4)
        assert fit.f0_sigma_hz > 0

    def test_gaussian_truth_recovery(self):
        f0, fwhm = 1.4493e9, 2.0e6
        freq = np.linspace(f0 - 8e6, f0 + 8e6, 161)
        signal = gaussian(freq, f0, fwhm, -0.05, 1.0, 0.0) + RNG.normal(
            0, 1e-4, freq.size
        )
        fit = fit_spectrum(freq, signal, model="gaussian", sigma=1e-4)
        assert fit.fwhm_hz == pytest.approx(fwhm, rel=0.02)

    def test_voigt_lorentzian_limit(self):
        """fwhm_g -> 0 must reproduce the Lorentzian width through the
        Olivero-Longbothum effective form (second code path)."""
        assert voigt_effective_fwhm(0.0, 1.4e6) == pytest.approx(
            1.4e6, rel=1e-3
        )
        assert voigt_effective_fwhm(1.4e6, 0.0) == pytest.approx(
            1.4e6, rel=1e-3
        )

    def test_window_is_applied_and_recorded(self):
        freq, signal = _lorentzian_spectrum()
        lo, hi = 1.4488e9, 1.4498e9
        fit = fit_spectrum(
            freq, signal, model="lorentzian", sigma=1e-4, window_hz=(lo, hi)
        )
        assert fit.fit_window_hz[0] >= lo
        assert fit.fit_window_hz[1] <= hi

    def test_no_sigma_means_no_chi2(self):
        freq, signal = _lorentzian_spectrum()
        fit = fit_spectrum(freq, signal, model="lorentzian")
        assert fit.chi2_dof is None
        assert "residual rms" in fit.sigma_source

    def test_too_few_points_refused(self):
        with pytest.raises(LineshapeError, match="points"):
            fit_spectrum(
                np.linspace(0, 1, 5), np.zeros(5), model="lorentzian"
            )

    def test_dip_and_peak_both_fit(self):
        freq, dip = _lorentzian_spectrum(amp=-0.06)
        freq2, peak = _lorentzian_spectrum(amp=+0.06)
        assert fit_spectrum(freq, dip, sigma=1e-4).params["amp"] < 0
        assert fit_spectrum(freq2, peak, sigma=1e-4).params["amp"] > 0


class TestD6Gate:
    """The strict AND gate, pinned. These tests are the pre-registration:
    they exist before any raw Cowley-Semple number does."""

    def test_gate_constants_pinned(self):
        assert D6_MIN_POWER_POINTS == 8
        assert D6_MIN_DELTA_AICC == 4.0

    def _quadratic_data(self, n):
        p = np.linspace(1.0, 15.0, n)
        y = 1449.0e6 - 0.08e6 * p - 0.01e6 * p * p
        return p, y, np.full(n, 0.02e6)

    def test_six_points_never_claimable_regardless_of_delta(self):
        """Current datasets have 4-6 points: nonlinear models stay
        reported-only diagnostics no matter how decisive the AICc."""
        p, y, s = self._quadratic_data(6)
        cmp_ = fit_power_models(p, y, s)
        assert cmp_.claimable_nonlinear is None
        assert "point-count arm FAILED" in cmp_.gate_note
        # the diagnostics are still REPORTED (listed, unclaimed)
        assert cmp_.quadratic is not None
        assert cmp_.delta_aicc_quadratic is not None

    def test_ten_points_strong_curvature_claimable(self):
        p, y, s = self._quadratic_data(10)
        cmp_ = fit_power_models(p, y, s)
        assert cmp_.claimable_nonlinear == "quadratic"
        assert cmp_.delta_aicc_quadratic >= D6_MIN_DELTA_AICC
        assert "PASSED" in cmp_.gate_note

    def test_linear_data_stays_linear_at_any_n(self):
        p = np.linspace(1.0, 15.0, 12)
        y = 1449.0e6 - 0.1e6 * p + RNG.normal(0, 0.01e6, 12)
        cmp_ = fit_power_models(p, y, np.full(12, 0.01e6))
        assert cmp_.claimable_nonlinear is None
        assert cmp_.linear.chi2_dof < 3.0

    def test_duplicate_powers_refused(self):
        p = np.array([1.0, 2.0, 2.0, 4.0, 5.0])
        with pytest.raises(LineshapeError, match="INDEPENDENT"):
            fit_power_models(p, p, np.ones(5))

    def test_piecewise_recovers_breakpoint(self):
        p = np.linspace(1.0, 15.0, 12)
        y = np.where(p < 8.0, 10.0 - 0.1 * p, 10.0 - 0.1 * p - 0.5 * (p - 8.0))
        cmp_ = fit_power_models(p, y, np.full(12, 0.01))
        assert cmp_.piecewise is not None
        assert cmp_.piecewise.breakpoint == pytest.approx(8.0, abs=1.5)
        assert cmp_.claimable_nonlinear == "piecewise-linear"


class TestExtrapolationPolicy:
    def test_linear_stands_gives_intercept(self):
        p = np.linspace(2.0, 14.0, 7)
        y = 1.40e6 + 0.05e6 * p
        cmp_ = fit_power_models(p, y, np.full(7, 0.01e6))
        ext = zero_power_extrapolation(cmp_, p, y)
        assert not ext.refused
        assert ext.basis == "linear"
        assert ext.grade == "fit-extrapolated"
        assert ext.value == pytest.approx(1.40e6, rel=1e-6)

    def test_undiscriminated_form_refuses_with_verbatim_statement(self):
        """Nonlinear preferred by AICc but n < 8: the form is
        undiscriminated — refuse, and report the lowest-power measured
        value as the operational bound (plan §3, verbatim wording)."""
        p = np.linspace(1.0, 15.0, 6)
        y = 1.4e6 + 0.02e6 * p + 0.01e6 * p * p
        cmp_ = fit_power_models(p, y, np.full(6, 0.005e6))
        assert cmp_.nonlinear_suggested_but_unclaimable
        ext = zero_power_extrapolation(cmp_, p, y)
        assert ext.refused
        assert EXTRAPOLATION_REFUSAL in ext.statement
        assert ext.operational_bound == pytest.approx(float(y[0]))
        assert ext.value is None

    def test_claimable_quadratic_extrapolates_its_intercept(self):
        p = np.linspace(1.0, 15.0, 10)
        y = 1.4e6 + 0.02e6 * p + 0.01e6 * p * p
        cmp_ = fit_power_models(p, y, np.full(10, 0.005e6))
        ext = zero_power_extrapolation(cmp_, p, y)
        assert not ext.refused
        assert ext.basis == "quadratic"
        assert ext.value == pytest.approx(1.4e6, rel=1e-4)
