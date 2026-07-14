"""T4 — ratio discrimination test (calibration/ratio_test.py).

The verdict logic is unit-tested on synthetic ratio sets (all three
branches); the real-sweep verdict and the glue-confound factors are
regression-pinned from the committed report
(calibration/reports/ratio_test_digitized.md).
"""

from __future__ import annotations

import numpy as np
import pytest

from calibration.ratio_test import (
    GEOMETRY_SUFFICIENT,
    INDETERMINATE,
    INTRINSIC_REQUIRED,
    classify,
    glue_confound_factor,
    model_ratio_grid,
    render_report,
    run_ratio_test,
)
from calibration.rig_model import sweep_sample
from calibration.samples import D14, H14, default_grid


@pytest.fixture(scope="module")
def result():
    return run_ratio_test()


class TestClassifyRule:
    """The ratified three-way criteria, fixed before the data was seen."""

    def test_point_inside_two_sigma_is_geometry_sufficient(self):
        assert classify(np.array([1.30]), 1.343, 0.132) == GEOMETRY_SUFFICIENT

    def test_all_points_one_side_is_intrinsic_required(self):
        assert classify(np.array([0.9, 1.0]), 1.343, 0.132) == INTRINSIC_REQUIRED
        assert classify(np.array([1.7, 1.9]), 1.343, 0.132) == INTRINSIC_REQUIRED

    def test_straddle_without_landing_inside_is_indeterminate(self):
        assert classify(np.array([0.9, 1.9]), 1.343, 0.132) == INDETERMINATE

    def test_boundary_is_inclusive(self):
        assert classify(np.array([1.343 + 2 * 0.132]), 1.343, 0.132) == GEOMETRY_SUFFICIENT


class TestModelRatioGrid:
    def test_shape_and_pairing(self):
        grid = default_grid(n_thickness=2, n_spot=1, n_h_sub=2, n_k=1)
        r_d14 = sweep_sample(D14, grid)
        r_h14 = sweep_sample(H14, grid)
        ratios = model_ratio_grid(r_d14, r_h14)
        assert ratios.shape == (grid.n_shared, 2, 2)
        # diagonal = equal thickness; d14 hotter at shared params
        assert np.all(ratios[:, 0, 0] > 1.0)
        assert np.all(ratios[:, 1, 1] > 1.0)
        # element [s, i, j] = theta_d14[s, i] / theta_h14[s, j]
        assert ratios[0, 0, 1] == pytest.approx(
            r_d14.theta_k_per_w[0, 0] / r_h14.theta_k_per_w[0, 1]
        )

    def test_mismatched_grids_rejected(self):
        g1 = default_grid(n_thickness=2, n_spot=1, n_h_sub=2, n_k=1)
        g2 = default_grid(n_thickness=3, n_spot=1, n_h_sub=2, n_k=1)
        with pytest.raises(ValueError, match="same grid"):
            model_ratio_grid(sweep_sample(D14, g1), sweep_sample(H14, g2))


class TestRealSweepVerdict:
    """Regression pins of the committed 2026-07-14 verdict."""

    def test_verdict_geometry_sufficient(self, result):
        assert result.verdict == GEOMETRY_SUFFICIENT

    def test_measured_ratio_from_t3(self, result):
        assert result.measured_ratio == pytest.approx(1.343, abs=5e-3)
        assert result.measured_sigma == pytest.approx(0.132, abs=5e-3)

    def test_model_band_brackets_measurement(self, result):
        assert result.model_ratio_min == pytest.approx(0.584, abs=0.02)
        assert result.model_ratio_max == pytest.approx(2.329, abs=0.02)
        assert result.model_ratio_min < result.measured_ratio < result.model_ratio_max

    def test_fraction_within_two_sigma(self, result):
        assert result.fraction_within_2sigma == pytest.approx(0.539, abs=0.02)
        assert result.n_ratio_points == 351 * 5 * 5

    def test_verdict_stable_across_radius_mapping_band(self, result):
        assert set(result.verdict_by_radius_factor.values()) == {GEOMETRY_SUFFICIENT}

    def test_comsol_trigger_not_fired(self, result):
        """Licence discipline: analytic engine remains sufficient."""
        assert result.comsol_trigger is False

    def test_provenance_stamp_carried(self, result):
        assert "graph-digitized-provisional" in result.provenance


class TestGlueConfound:
    def test_factors_pinned(self, result):
        phi = result.glue_confound_factor
        assert phi[1e2] == pytest.approx(1.49, abs=0.05)
        assert phi[1e3] == pytest.approx(0.53, abs=0.05)
        assert phi[1e4] == pytest.approx(0.0743, rel=0.1)
        assert phi[1e5] == pytest.approx(0.00778, rel=0.1)

    def test_factor_monotone_decreasing_in_reference_h_sub(self, result):
        values = [result.glue_confound_factor[h] for h in (1e2, 1e3, 1e4, 1e5)]
        assert all(v is not None for v in values)
        assert all(a > b for a, b in zip(values, values[1:]))

    def test_direct_evaluation_reproduces_measured_ratio(self, result):
        """Round-trip: apply the found φ and recover the measured ratio."""
        from calibration.constants import RADIUS_MAPPING, SPOT, THICKNESS
        from calibration.rig_model import RigConfig, theta_probe_k_per_w
        from cavity.provenance.constants import K_PTP

        h_ref = 1e3
        phi = glue_confound_factor(result.measured_ratio, h_ref)
        t_mid = 0.5 * (THICKNESS.lo_m + THICKNESS.hi_m)

        def theta(sample, h_sub):
            return theta_probe_k_per_w(
                RigConfig(
                    sample=sample,
                    thickness_m=t_mid,
                    spot_diameter_m=SPOT.diameter_m,
                    h_sub_w_m2_k=h_sub,
                    k_w_m_k=K_PTP.k_mid_w_m_k,
                    radius_factor=RADIUS_MAPPING.factor_point,
                )
            )

        recovered = theta(D14, phi * h_ref) / theta(H14, h_ref)
        assert recovered == pytest.approx(result.measured_ratio, rel=1e-6)


class TestReport:
    def test_report_carries_verdict_confound_and_scope(self, result):
        report = render_report(result)
        assert "GEOMETRY-SUFFICIENT" in report
        assert "does NOT cancel" in report
        assert "deliberately not decomposed" in report
        assert "licence discipline holds" in report
        assert "l_abs ≪ t" in report
