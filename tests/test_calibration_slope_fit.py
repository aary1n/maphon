"""T3 — slope fits of the digitized ODMR points (calibration/slope_fit.py).

Regression pins are the ratification-condition values, which were computed
INDEPENDENTLY of this module (user WLS, 2026-07-14): d14 −0.100 ± 0.006,
h14 −0.0745 ± 0.006 MHz/mW, ratio 1.34 ± 0.13. A second in-test
independent path (numpy.polyfit with weights) cross-checks the module's
closed form on the same data.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from calibration.constants import DIGITIZED_SIGMA_MHZ
from calibration.slope_fit import (
    DEFAULT_CSV,
    PROVENANCE_STAMP,
    PowerSeries,
    fit_all,
    fit_sample,
    load_digitized,
    render_report,
    slope_ratio,
    step_test,
    wls_line,
)


@pytest.fixture(scope="module")
def results():
    return fit_all()


class TestProvenanceEnforcement:
    def test_loader_parses_both_samples(self):
        series = load_digitized()
        assert set(series) == {"d14", "h14"}
        assert len(series["d14"].powers_mw) == 4
        assert len(series["h14"].powers_mw) == 6
        assert series["d14"].provenance == PROVENANCE_STAMP

    def test_missing_grade_header_refused(self, tmp_path):
        stripped = tmp_path / "no_header.csv"
        lines = DEFAULT_CSV.read_text(encoding="utf-8").splitlines()
        stripped.write_text(
            "\n".join(ln for ln in lines if "Grade:" not in ln), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="refusing to fit ungraded data"):
            load_digitized(stripped)

    def test_missing_error_model_refused(self, tmp_path):
        stripped = tmp_path / "no_sigma.csv"
        lines = DEFAULT_CSV.read_text(encoding="utf-8").splitlines()
        stripped.write_text(
            "\n".join(ln for ln in lines if "0.05 MHz" not in ln), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="refusing to fit ungraded data"):
            load_digitized(stripped)


class TestSlopePins:
    """Ratification-condition pins (independent WLS, 2026-07-14)."""

    def test_d14_slope(self, results):
        f = results.fits["d14"]
        assert f.slope_mhz_per_mw == pytest.approx(-0.100, abs=5e-4)
        assert f.slope_sigma_mhz_per_mw == pytest.approx(0.006, abs=5e-4)

    def test_h14_slope(self, results):
        f = results.fits["h14"]
        assert f.slope_mhz_per_mw == pytest.approx(-0.0745, abs=5e-4)
        assert f.slope_sigma_mhz_per_mw == pytest.approx(0.006, abs=5e-4)

    def test_ratio(self, results):
        assert results.ratio.ratio == pytest.approx(1.34, abs=5e-3)
        assert results.ratio.sigma == pytest.approx(0.13, abs=5e-3)

    def test_cross_check_against_numpy_polyfit(self):
        """Same data through an independent fitting code path."""
        series = load_digitized()
        for name, s in series.items():
            fit = fit_sample(s)
            coeffs, cov = np.polyfit(
                s.powers_mw,
                s.f_peak_mhz,
                deg=1,
                w=np.full_like(s.powers_mw, 1.0 / s.sigma_mhz),
                cov="unscaled",
            )
            assert fit.slope_mhz_per_mw == pytest.approx(coeffs[0], rel=1e-12), name
            assert fit.slope_sigma_mhz_per_mw == pytest.approx(
                math.sqrt(cov[0, 0]), rel=1e-9
            ), name


class TestWlsClosedForm:
    def test_exact_line_recovered_with_zero_chi2(self):
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = 5.0 - 0.7 * x
        slope, intercept, s_sig, i_sig, chi2, dof = wls_line(x, y, sigma=0.05)
        assert slope == pytest.approx(-0.7)
        assert intercept == pytest.approx(5.0)
        assert chi2 == pytest.approx(0.0, abs=1e-20)
        assert dof == 2
        # textbook floor-propagated slope error
        assert s_sig == pytest.approx(0.05 / math.sqrt(5.0))

    def test_too_few_points_rejected(self):
        with pytest.raises(ValueError, match="at least 3"):
            wls_line(np.array([1.0, 2.0]), np.array([0.0, 1.0]), sigma=0.05)

    def test_ratio_propagation_matches_monte_carlo(self, results):
        """Delta-method ratio ± σ vs 200k-draw MC. The MC mean of a ratio
        carries the second-order bias ratio·(σ_h/h)² ≈ 0.008 relative to the
        delta-method point — allowed for explicitly, not hidden in a loose
        tolerance."""
        rng = np.random.default_rng(20260714)
        d, h = results.fits["d14"], results.fits["h14"]
        draws = rng.normal(d.slope_mhz_per_mw, d.slope_sigma_mhz_per_mw, 200_000) / rng.normal(
            h.slope_mhz_per_mw, h.slope_sigma_mhz_per_mw, 200_000
        )
        bias = results.ratio.ratio * (h.slope_sigma_mhz_per_mw / h.slope_mhz_per_mw) ** 2
        assert float(np.mean(draws)) == pytest.approx(results.ratio.ratio + bias, abs=2e-3)
        assert results.ratio.sigma == pytest.approx(float(np.std(draws)), rel=0.08)


class TestStepNonlinearity:
    def test_h14_step_values(self, results):
        step = results.h14_step
        assert step.observed_step_mhz == pytest.approx(-0.30, abs=1e-12)
        # predicted = slope * 2.17 mW ~= -0.162 MHz; excess ~= -0.138 MHz
        assert step.predicted_step_mhz == pytest.approx(-0.1616, abs=2e-3)
        assert step.excess_mhz == pytest.approx(-0.138, abs=2e-3)

    def test_h14_step_does_not_exceed_floor_at_2sigma(self, results):
        """The plan's scoping estimate (z ~= -1.9): borderline but below 2σ —
        the apparent knee is NOT resolved above the digitization floor."""
        step = results.h14_step
        assert -2.0 < step.z_score < -1.5
        assert not step.exceeds_floor_2sigma

    def test_step_powers_must_exist_in_trace(self, results):
        series = load_digitized()["d14"]  # d14 has no 12.33 mW point
        with pytest.raises(ValueError, match="not in the d14 trace"):
            step_test(series, results.fits["d14"])


class TestReport:
    def test_report_carries_stamp_and_verdict(self, results):
        report = render_report(results)
        assert PROVENANCE_STAMP in report
        assert "does NOT exceed" in report
        assert f"±{DIGITIZED_SIGMA_MHZ}" in report
        assert "1.34" in report

    def test_lack_of_fit_is_reported_per_sample(self, results):
        for fit in results.fits.values():
            assert fit.dof == fit.n_points - 2
            assert fit.chi2 >= 0.0


def test_synthetic_series_roundtrip():
    """Fit machinery on synthetic data with known truth + noise floor."""
    rng = np.random.default_rng(7)
    powers = np.array([3.0, 5.0, 8.0, 11.0, 14.0])
    truth_slope, truth_intercept = -0.09, 1450.0
    freqs = truth_intercept + truth_slope * powers + rng.normal(0, 0.05, len(powers))
    series = PowerSeries(
        sample="synthetic",
        powers_mw=powers,
        f_peak_mhz=freqs,
        sigma_mhz=0.05,
        provenance="synthetic",
    )
    fit = fit_sample(series)
    assert fit.slope_mhz_per_mw == pytest.approx(truth_slope, abs=3 * fit.slope_sigma_mhz_per_mw)
