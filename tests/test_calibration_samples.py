"""T2 — sample configs and sweep grid (calibration/samples, calibration/constants).

Pins every collaborator-stated number to the archived 2026-07-14 email
values and enforces the grading/boundary conventions the plan ratified.
"""

from __future__ import annotations

import math

import pytest

import calibration.constants as constants
from calibration.constants import (
    AMBIENT,
    CONCENTRATION,
    EXCITATION,
    LATERAL,
    RADIUS_MAPPING,
    SPOT,
    THICKNESS,
    UNDERSIDE,
)
from calibration.samples import D14, H14, SAMPLES, default_grid


class TestEmailPinnedValues:
    def test_ambient(self):
        assert AMBIENT.t_inf_k == 293.15  # "Temperature: 20 degrees Celsius"
        assert AMBIENT.enclosed is True

    def test_lateral_sizes(self):
        assert D14.lateral_m == 1.12e-3
        assert H14.lateral_m == 1.79e-3

    def test_powers_per_trace(self):
        assert D14.powers_mw == (3.81, 6.06, 10.16, 14.39)
        assert H14.powers_mw == (3.81, 6.06, 8.05, 10.16, 12.33, 14.39)
        # every power stays under the confirmed 15 mW pigtail maximum
        assert max(D14.powers_mw + H14.powers_mw) < EXCITATION.max_power_mw

    def test_excitation(self):
        assert EXCITATION.wavelength_nm == 520.0
        assert "LP520-SF15A" in EXCITATION.part

    def test_deuteration_flags(self):
        assert D14.deuterated is True
        assert H14.deuterated is False
        assert set(SAMPLES) == {"d14", "h14"}

    def test_concentration_grades_are_asymmetric(self):
        """d14's 0.1% is stated in the email text; h14's only in the spectra
        figure title — the ratified grade split must not collapse."""
        assert CONCENTRATION.d14_nominal == CONCENTRATION.h14_nominal == 1e-3
        assert CONCENTRATION.d14_grade == "collaborator-confirmed"
        assert "figure-stated" in CONCENTRATION.h14_grade


class TestGradingConventions:
    def test_every_constant_is_marked_non_transferable(self):
        """The provenance boundary in prose: each graded dataclass carries
        NON-TRANSFERABLE (or sits under the module docstring's blanket
        statement, which must itself be present)."""
        assert "NON-TRANSFERABLE" in constants.__doc__
        for cls in (
            constants.AmbientConditions,
            constants.ExcitationSource,
            constants.SpotGeometry,
            constants.SampleLateralSize,
            constants.CrystalThickness,
            constants.UndersideCoupling,
            constants.NominalConcentration,
        ):
            assert "NON-TRANSFERABLE" in cls.__doc__, cls.__name__

    def test_spot_is_suggested_not_confirmed(self):
        assert "COLLABORATOR-SUGGESTED" in constants.SpotGeometry.__doc__
        assert "NOT a measurement" in constants.SpotGeometry.__doc__

    def test_power_plane_open_ask_recorded(self):
        assert "open Angus ask" in EXCITATION.power_plane


class TestRadiusMapping:
    def test_equal_area_point_and_band(self):
        assert RADIUS_MAPPING.factor_point == pytest.approx(1.0 / math.sqrt(math.pi))
        assert RADIUS_MAPPING.factor_lo == 0.5
        assert RADIUS_MAPPING.factor_hi == pytest.approx(1.0 / math.sqrt(2.0))
        assert RADIUS_MAPPING.factor_lo < RADIUS_MAPPING.factor_point < RADIUS_MAPPING.factor_hi

    def test_disc_radius_applies_factor(self):
        assert D14.disc_radius_m(0.5) == pytest.approx(0.56e-3)
        assert H14.disc_radius_m(0.5) == pytest.approx(0.895e-3)

    def test_out_of_band_factor_rejected(self):
        with pytest.raises(ValueError, match="outside the mapped band"):
            D14.disc_radius_m(1.0)


class TestSweepGrid:
    def test_default_grid_spans_the_ratified_axes(self):
        grid = default_grid()
        assert grid.thickness_m[0] == THICKNESS.lo_m and grid.thickness_m[-1] == THICKNESS.hi_m
        assert grid.spot_diameter_m[0] == SPOT.diameter_sweep_lo_m
        assert grid.spot_diameter_m[-1] == SPOT.diameter_sweep_hi_m
        assert grid.h_sub_w_m2_k[0] == pytest.approx(UNDERSIDE.h_sub_lo_w_m2_k)
        assert grid.h_sub_w_m2_k[-1] == pytest.approx(UNDERSIDE.h_sub_hi_w_m2_k)
        assert grid.k_w_m_k[0] == pytest.approx(0.1) and grid.k_w_m_k[-1] == pytest.approx(1.0)
        assert grid.radius_factor == (
            RADIUS_MAPPING.factor_lo,
            RADIUS_MAPPING.factor_point,
            RADIUS_MAPPING.factor_hi,
        )

    def test_shared_size_excludes_thickness(self):
        grid = default_grid()
        assert grid.n_shared == 3 * 13 * 3 * 3  # spot x h_sub x k x radius_factor
