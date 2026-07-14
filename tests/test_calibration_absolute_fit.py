"""T5 — absolute fits and the observable-a feed (calibration/absolute_fit.py).

The chain algebra is checked closed-form against hand values computed IN
THE TEST from the graded constants (independent arithmetic path); the
committed feed values are regression-pinned; the ratified df_spin/dT
arbitration (condition 3) is asserted as a convention, not just prose.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from calibration.absolute_fit import (
    MHZ_PER_MW_TO_HZ_PER_W,
    absolute_fit_sample,
    render_report,
    run_absolute_fits,
)
from calibration.samples import SAMPLES
from calibration.slope_fit import fit_all
from cavity.provenance.constants import DF_SPIN_DT


@pytest.fixture(scope="module")
def feed():
    return run_absolute_fits()


class TestChainAlgebra:
    def test_unit_conversion(self):
        assert 0.1 * MHZ_PER_MW_TO_HZ_PER_W == pytest.approx(1e8)  # MHz/mW -> Hz/W

    def test_point_and_band_closed_form(self, feed):
        """Independent arithmetic: point = |slope|/|df point|, band edges =
        (|slope| ∓ σ)/(steep, shallow) coefficient edges."""
        fits = fit_all()
        for name in ("d14", "h14"):
            f = feed.fits[name]
            slope = abs(fits.fits[name].slope_mhz_per_mw) * 1e9
            sigma = fits.fits[name].slope_sigma_mhz_per_mw * 1e9
            assert f.eta_r_point_k_per_w == pytest.approx(slope / 109_000.0, rel=1e-12)
            assert f.eta_r_band_lo_k_per_w == pytest.approx((slope - sigma) / 120_000.0, rel=1e-12)
            assert f.eta_r_band_hi_k_per_w == pytest.approx((slope + sigma) / 64_000.0, rel=1e-12)
            assert f.eta_r_band_lo_k_per_w < f.eta_r_point_k_per_w < f.eta_r_band_hi_k_per_w

    def test_probe_inferred_heating_is_eta_abs_free(self, feed):
        """heating = point × P_max: pure (measured shift)/(coefficient) — no
        absorption assumption may enter this number."""
        for name in ("d14", "h14"):
            f = feed.fits[name]
            p_max_w = max(SAMPLES[name].powers_mw) * 1e-3
            assert f.heating_at_max_power_k == pytest.approx(
                f.eta_r_point_k_per_w * p_max_w, rel=1e-12
            )


class TestRatifiedDfDtArbitration:
    """Condition 3: graded DF_SPIN_DT in, prompt band out."""

    def test_graded_constant_is_the_source(self):
        assert DF_SPIN_DT.df_dt_hz_per_k == -109_000.0
        assert DF_SPIN_DT.df_dt_band_lo_hz_per_k == -120_000.0
        assert DF_SPIN_DT.df_dt_band_hi_hz_per_k == -64_000.0

    def test_stale_prompt_band_flagged_in_feed(self, feed):
        assert "overruled as stale" in feed.df_dt_source
        assert "-50 to -108" in feed.df_dt_source


class TestFeedPins:
    """Regression pins of the committed 2026-07-14 feed."""

    def test_d14(self, feed):
        f = feed.fits["d14"]
        assert f.eta_r_point_k_per_w == pytest.approx(917, abs=5)
        assert f.eta_r_band_lo_k_per_w == pytest.approx(781, abs=5)
        assert f.eta_r_band_hi_k_per_w == pytest.approx(1659, abs=8)
        assert f.heating_at_max_power_k == pytest.approx(13.2, abs=0.1)

    def test_h14(self, feed):
        f = feed.fits["h14"]
        assert f.eta_r_point_k_per_w == pytest.approx(683, abs=5)
        assert f.heating_at_max_power_k == pytest.approx(9.8, abs=0.1)

    def test_heating_lands_in_the_tens_of_k_class(self, feed):
        """Order-of-magnitude consistency with Oxborrow's in-thread
        'several tens of Celsius' inference — a class check, not a target."""
        for f in feed.fits.values():
            assert 5.0 < f.heating_at_max_power_k < 100.0

    def test_sweep_mostly_feasible(self, feed):
        for f in feed.fits.values():
            assert f.feasible_sweep_fraction > 0.9
            assert 0.0 < f.eta_abs_at_nominal_config <= 1.0

    def test_t4_verdict_carried(self, feed):
        assert feed.t4_verdict == "geometry-sufficient"


class TestDeuterationAsymmetry:
    def test_h14_clean_d14_caveated(self, feed):
        assert feed.fits["h14"].deuteration_caveat.startswith("clean")
        assert "deuteration-transfer caveat" in feed.fits["d14"].deuteration_caveat


class TestOutputs:
    def test_json_schema(self, feed):
        payload = json.loads(feed.to_json())
        assert payload["workstream"] == "layer-b-calibration/observable-a"
        assert "graph-digitized-provisional" in payload["provenance"]
        assert set(payload["samples"]) == {"d14", "h14"}
        for sample in payload["samples"].values():
            for key in (
                "slope_hz_per_w",
                "eta_r_point_k_per_w",
                "eta_r_band_lo_k_per_w",
                "eta_r_band_hi_k_per_w",
                "heating_at_max_power_k",
                "feasible_sweep_fraction",
                "deuteration_caveat",
            ):
                assert key in sample
        assert payload["t4_ratio_test"]["verdict"] == "geometry-sufficient"
        assert "open Angus ask" in payload["units"]["slope"]

    def test_report_content(self, feed):
        report = render_report(feed)
        assert "overruled as stale" in report
        assert "probe-inferred" in report.lower()
        assert "geometry-sufficient" in report
        assert "h14 is the CLEAN absolute fit" in report

    def test_synthetic_sample_feasibility_direction(self):
        """A sweep whose Θ all sit below the required η_abs·R_int is 0%
        feasible; all above is 100% — the constraint direction."""
        fits = fit_all()
        point = feed_point = abs(fits.fits["d14"].slope_mhz_per_mw) * 1e9 / 109_000.0
        low_thetas = np.full(10, 0.5 * point)
        high_thetas = np.full(10, 2.0 * point)
        f_low = absolute_fit_sample("d14", fits.fits["d14"], low_thetas)
        f_high = absolute_fit_sample("d14", fits.fits["d14"], high_thetas)
        assert f_low.feasible_sweep_fraction == 0.0
        assert f_high.feasible_sweep_fraction == 1.0
