"""SPEC §2 materials — complex permittivity + IBC surface resistance."""

from __future__ import annotations

import math

import pytest

from cavity.forward_model import (
    MU_0,
    MaterialSpec,
    copper_surface_resistance,
    sto_complex_permittivity,
)
from cavity.provenance import COPPER, STO, Copper, STOSingleCrystal


class TestSTOComplexPermittivity:
    def test_default_uses_provenance_constants(self):
        eps = sto_complex_permittivity()
        assert eps.real == pytest.approx(STO.epsilon_r_real, rel=1e-12)
        assert eps.imag == pytest.approx(
            -STO.epsilon_r_real * STO.tan_delta, rel=1e-12
        )

    def test_sign_is_negative_imag(self):
        """SPEC §2 + COMSOL e^(+i omega t) convention: lossy => Im(eps_r) < 0."""
        eps = sto_complex_permittivity()
        assert eps.imag < 0

    def test_loss_scales_with_tan_delta(self):
        weak = sto_complex_permittivity(
            STOSingleCrystal(epsilon_r_real=316.3, tan_delta=1.0e-4)
        )
        strong = sto_complex_permittivity(
            STOSingleCrystal(epsilon_r_real=316.3, tan_delta=2.0e-4)
        )
        assert strong.imag == pytest.approx(2.0 * weak.imag, rel=1e-12)
        assert weak.real == pytest.approx(strong.real, rel=1e-12)

    def test_lossless_at_zero_tan_delta(self):
        eps = sto_complex_permittivity(
            STOSingleCrystal(epsilon_r_real=316.3, tan_delta=0.0)
        )
        assert eps.imag == 0.0


class TestCopperSurfaceResistance:
    """R_s = sqrt(omega * mu_0 / (2 * sigma)).

    Hand-arithmetic at 1.45 GHz, sigma = 6e7:
      omega = 2 pi * 1.45e9 ~ 9.111e9 rad/s
      omega * mu_0 / (2 sigma) ~ 9.54e-5
      R_s ~ 9.77 milli-ohm/sq.
    """

    def test_textbook_value_at_1p45_ghz(self):
        rs = copper_surface_resistance(1.45e9)
        assert rs == pytest.approx(9.77e-3, rel=2e-3)

    def test_scales_as_sqrt_f(self):
        rs1 = copper_surface_resistance(1.0e9)
        rs4 = copper_surface_resistance(4.0e9)
        assert rs4 == pytest.approx(2.0 * rs1, rel=1e-12)

    def test_scales_inversely_with_sqrt_sigma(self):
        rs_default = copper_surface_resistance(1.45e9)
        rs_quartered = copper_surface_resistance(
            1.45e9, Copper(sigma=COPPER.sigma / 4.0)
        )
        assert rs_quartered == pytest.approx(2.0 * rs_default, rel=1e-12)

    @pytest.mark.parametrize("f", [0.0, -1.0e9])
    def test_rejects_non_positive_f(self, f):
        with pytest.raises(ValueError):
            copper_surface_resistance(f)

    def test_rejects_non_positive_sigma(self):
        with pytest.raises(ValueError):
            copper_surface_resistance(1.45e9, Copper(sigma=0.0))


class TestMaterialSpec:
    def test_defaults_use_provenance(self):
        spec = MaterialSpec()
        assert spec.sto is STO
        assert spec.copper is COPPER
        assert spec.wall_pec is False

    def test_pec_variant_flips_only_wall(self):
        ibc = MaterialSpec()
        pec = MaterialSpec(wall_pec=True)
        assert pec.sto is ibc.sto
        assert pec.copper is ibc.copper
        assert pec.wall_pec != ibc.wall_pec

    def test_sto_complex_eps_r_matches_helper(self):
        spec = MaterialSpec()
        assert spec.sto_complex_eps_r == sto_complex_permittivity(spec.sto)


class TestMu0Constant:
    def test_mu_0_matches_4pi_e_minus_7(self):
        assert MU_0 == pytest.approx(4.0 * math.pi * 1.0e-7, rel=1e-15)
