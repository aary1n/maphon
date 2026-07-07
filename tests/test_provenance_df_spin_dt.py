"""SPEC §6T — SpinFreqTempCoefficient raw-data grading guards (no COMSOL).

Pins the 2026-07-07 re-grade of df_spin/dT against the archived Singh
raw Fig. 2B data (refs/singh_2025_raw/) and the committed fit script
`cavity.provenance.singh_raw_fits`:

- archive integrity (SHA-256 + point counts — the files are
  byte-for-byte as received; any edit fails loudly here);
- the canonical window fits, the quantisation-aware uncertainty floor,
  the figure↔file affine axis map, and the cold-finger-branch offset;
- constant/script consistency: the stored point value is the fit at
  the constant's own window, and the band endpoints are checked
  THROUGH the branch-fit functions at test time (never against stored
  endpoint literals) — same discipline as the df_cavity/dT guards.

X-Y and Y-Z fits are pinned only as archive-audit regression values:
no constant derives from them (SPEC §6T).
"""

import hashlib
import math

from cavity.provenance.constants import DF_CAVITY_DT, DF_SPIN_DT
from cavity.provenance.singh_raw_fits import (
    SIGMA_QUANT_MHZ,
    XY_FILE,
    XZ_FILE,
    YZ_FILE,
    affine_map_vs_extraction,
    band_hi_window_fit,
    band_lo_window_fit,
    coldfinger_offset_k,
    load_xy,
    load_xz,
    load_yz,
    ols_slope,
    point_window_fit,
    transition_midpoint_k,
)

SHA256_PINS = {
    XZ_FILE: "9a0a513a59cb03bb3c335620f27c58c13bd729881fe552e75d6e26925bb98828",
    XY_FILE: "73e61d6281ef155b6cc8676eb6e98b1a8ce5f02f41802c69c71fe593453e9fc2",
    YZ_FILE: "2c24de00e9630e3cfae95a2e1524d5a752436c78facf1b02afb8fa01934d185d",
}


class TestArchiveIntegrity:
    def test_sha256_byte_for_byte(self):
        """The archived files are verbatim as received 2026-07-07."""
        for path, expected in SHA256_PINS.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path

    def test_point_counts(self):
        assert len(load_xz()[0]) == 197  # = the figure's marker count
        assert len(load_xy()[0]) == 260
        assert len(load_yz()[0]) == 356

    def test_frequency_on_0p1_mhz_grid(self):
        """The quantisation model's premise: every frequency is a
        multiple of 0.1 MHz in all three files."""
        for t, f in (load_xz(), load_xy(), load_yz()):
            scaled = f * 10.0
            assert all(
                math.isclose(v, round(v), abs_tol=1e-6) for v in scaled
            )


class TestXZWindowFits:
    """Regression pins for the canonical fit table (kHz/K, ±0.5 abs)."""

    def _pin(self, lo, hi, expected):
        t, f = load_xz()
        fit = ols_slope(t, f, lo, hi)
        assert math.isclose(fit.slope_khz_per_k, expected, abs_tol=0.5), fit

    def test_region_iii_proxy_150_330(self):
        self._pin(150.0, 330.0, -65.0)

    def test_drawn_red_line_span_254_324(self):
        """Resolves the printed −101: the raw data over the paper's
        own drawn-line span."""
        self._pin(254.0, 324.0, -102.3)

    def test_254_330(self):
        self._pin(254.0, 330.0, -103.4)

    def test_operating_290_310(self):
        self._pin(290.0, 310.0, -115.4)

    def test_operating_293_310_point_window(self):
        self._pin(293.0, 310.0, -108.5)

    def test_band_lo_window_290_330(self):
        self._pin(290.0, 330.0, -119.7)

    def test_cold_finger_branch_window(self):
        fit = band_hi_window_fit()
        assert math.isclose(fit.slope_khz_per_k, -64.4, abs_tol=0.5), fit

    def test_statistical_errors_small(self):
        """Residual-based SEs are 1-3 kHz/K — the systematic band,
        not the statistics, carries the uncertainty."""
        for fit in (point_window_fit(), band_lo_window_fit(), band_hi_window_fit()):
            assert fit.se_khz_per_k < 3.0, fit


class TestQuantisationAwareUncertainty:
    def test_sigma_quant_value(self):
        """sigma_q = 0.1 MHz / sqrt(12) = 28.87 kHz."""
        assert math.isclose(SIGMA_QUANT_MHZ * 1e3, 28.87, abs_tol=0.01)

    def test_point_window_quantisation_floor(self):
        """Quantisation-only slope SE at the point window ≈ 1.2 kHz/K,
        and the residual-based SE (which includes it) sits above it."""
        fit = point_window_fit()
        assert math.isclose(fit.se_quant_khz_per_k, 1.22, abs_tol=0.05)
        assert fit.se_khz_per_k >= fit.se_quant_khz_per_k

    def test_narrow_window_rmse_near_quantisation_floor(self):
        """The point window's RMSE (~49 kHz) sits within ~2x of the
        29 kHz floor: quantisation is a large share of the residual
        there, which is why it is stated explicitly in the grade."""
        fit = point_window_fit()
        assert SIGMA_QUANT_MHZ * 1e3 < fit.rmse_khz < 4 * SIGMA_QUANT_MHZ * 1e3


class TestAffineAxisMap:
    """The three-way-resolution mechanism (figure axis vs file axis).

    Symmetric-agnostic by design: these pins assert the two axes
    DIFFER by this affine map, not which side is the calibrated
    sensor reading (unresolved — PROVENANCE.md ask 1).
    """

    def test_map_parameters(self):
        amap = affine_map_vs_extraction()
        assert math.isclose(amap.scale, 0.9316, abs_tol=0.001)
        assert math.isclose(amap.offset_k, 16.56, abs_tol=0.1)
        assert amap.rms_resid_k <= 0.15

    def test_pairing_proof_frequency_residuals(self):
        """Frequency residuals at the quantisation floor prove the
        rank-order pairing (a one-point slip would read ~450 kHz)."""
        amap = affine_map_vs_extraction()
        assert amap.freq_resid_rms_khz <= 45.0

    def test_slope_inflation_reconciles_digitised_minus_112(self):
        """Raw −103.4 (254–330) × the inflation factor lands on the
        re-digitised −111.9 to within ~1%."""
        amap = affine_map_vs_extraction()
        t, f = load_xz()
        raw = ols_slope(t, f, 254.0, 330.0).slope_khz_per_k
        assert math.isclose(raw * amap.slope_inflation, -111.9, rel_tol=0.015)


class TestColdFingerBranch:
    def test_transition_midpoint_and_offset(self):
        """Raw X-Z transition jump at file-axis ~132.0 K ⇒ +61.0 K
        offset, conditional on the paper's abs-193 K identification."""
        t, f = load_xz()
        assert math.isclose(transition_midpoint_k(t, f), 132.0, abs_tol=0.5)
        assert math.isclose(coldfinger_offset_k(), 61.0, abs_tol=0.5)


class TestConstantScriptConsistency:
    def test_point_is_fit_at_own_window(self):
        """Stored point = 3-s.f. rounding of the script's fit over the
        constant's own (t_window_lo_k, t_window_hi_k)."""
        t, f = load_xz()
        fit = ols_slope(
            t, f, DF_SPIN_DT.t_window_lo_k, DF_SPIN_DT.t_window_hi_k
        )
        assert math.isclose(
            DF_SPIN_DT.df_dt_hz_per_k, fit.slope_hz_per_k, rel_tol=5e-3
        )

    def test_band_ordering_and_point_interior(self):
        """Convention shift (2026-07-07, documented in the docstring):
        the point is INTERIOR to the band, no longer at an edge."""
        assert (
            DF_SPIN_DT.df_dt_band_lo_hz_per_k
            < DF_SPIN_DT.df_dt_hz_per_k
            < DF_SPIN_DT.df_dt_band_hi_hz_per_k
        )

    def test_band_covers_branch_fits(self):
        """Band endpoints checked THROUGH the branch-fit functions at
        test time (outward rounding), never against stored endpoint
        literals."""
        assert DF_SPIN_DT.df_dt_band_lo_hz_per_k <= band_lo_window_fit().slope_hz_per_k
        assert DF_SPIN_DT.df_dt_band_hi_hz_per_k >= band_hi_window_fit().slope_hz_per_k

    def test_window_matches_cavity_operating_envelope(self):
        """Same 293-310 numerals as the cavity arm's planning envelope
        (different axis semantics — file axis; documented)."""
        assert DF_SPIN_DT.t_window_lo_k == DF_CAVITY_DT.t_window_lo_k
        assert DF_SPIN_DT.t_window_hi_k == DF_CAVITY_DT.t_window_hi_k

    def test_sign_and_magnitude_class(self):
        """Negative, and 60-120 kHz/K class — two orders below the
        cavity arm (the §6T magnitude check)."""
        assert DF_SPIN_DT.df_dt_hz_per_k < 0
        assert 6.0e4 <= abs(DF_SPIN_DT.df_dt_hz_per_k) <= 1.2e5
        assert abs(DF_SPIN_DT.df_dt_hz_per_k) < 0.05 * DF_CAVITY_DT.df_dt_hz_per_k

    def test_retired_ensemble_edge_outside_band(self):
        """Oxborrow's in-thread −50 kHz/K is retired from band duty:
        it falls outside the new raw-data band (kept as docstring
        context only, per its SOURCE_MISSING audit verdict)."""
        assert -50e3 > DF_SPIN_DT.df_dt_band_hi_hz_per_k


class TestXYAndYZAuditOnly:
    """Archive-audit regression pins; NO constants derive from these."""

    def test_xy_region_iii_slope(self):
        t, f = load_xy()
        fit = ols_slope(t, f, 150.0, 330.0)
        assert math.isclose(fit.slope_khz_per_k, 9.7, abs_tol=0.3)

    def test_yz_slope_and_noise(self):
        t, f = load_yz()
        fit = ols_slope(t, f, 150.0, 306.0)
        assert math.isclose(fit.slope_khz_per_k, -63.1, abs_tol=0.5)
        # visibly noisier than XZ: RMSE ~0.5 MHz vs ~0.2 over the
        # comparable span
        assert fit.rmse_khz > 400.0
