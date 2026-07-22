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


class TestCrystalDielectric:
    """SPEC §5b crystal material (2026-07-22): eps_r enters only via the
    Q11 resolution payload at call sites; tan_delta deliberately
    ungraded = 0 (the spacer precedent)."""

    def test_no_default_epsilon(self):
        from cavity.forward_model import CrystalDielectric

        with pytest.raises(TypeError):
            CrystalDielectric()  # epsilon_r_real is required

    def test_rejects_non_positive_epsilon(self):
        from cavity.forward_model import CrystalDielectric

        with pytest.raises(ValueError, match="positive"):
            CrystalDielectric(epsilon_r_real=0.0)

    def test_lossless_defaults_and_complex_eps(self):
        from cavity.forward_model import CrystalDielectric

        crystal = CrystalDielectric(epsilon_r_real=3.0)
        assert crystal.tan_delta == 0.0
        assert crystal.mu_r == 1.0
        assert crystal.sigma == 0.0
        spec = MaterialSpec(crystal=crystal)
        assert spec.crystal_complex_eps_r == complex(3.0, 0.0)

    def test_complex_eps_raises_without_crystal(self):
        with pytest.raises(ValueError, match="no crystal material"):
            _ = MaterialSpec().crystal_complex_eps_r

    def test_q11_payload_is_the_epsilon_source(self):
        # The W2-class call sites read eps_r from RESOLUTION_Q11 — pin
        # that the payload value round-trips into the material.
        from cavity.forward_model import CrystalDielectric
        from cavity.sweep.resolutions import RESOLUTION_Q11

        eps = float(RESOLUTION_Q11.payload["crystal_epsilon_r"])
        crystal = CrystalDielectric(epsilon_r_real=eps)
        assert crystal.epsilon_r_real == 3.0


class TestCrystalConsistencyValidator:
    """build.validate_crystal_consistency — one switch, one owner
    (pure-Python check, no COMSOL needed)."""

    def _ring(self, with_crystal: bool):
        from cavity.forward_model import CavityGeometry, DielectricShape
        from cavity.provenance import GEOM_WU_STO_RING as G

        kwargs = dict(
            box_radius_m=G.box_inner_radius_m,
            box_height_m=G.box_internal_height_asoperated_m,
            dielectric_radius_m=G.sto_outer_radius_m,
            dielectric_shape=DielectricShape.RING,
            dielectric_height_m=8.6e-3,
            dielectric_inner_radius_m=G.sto_inner_radius_m,
            ring_bottom_z_m=G.deck_clearance_m,
        )
        if with_crystal:
            kwargs.update(
                crystal_radius_m=0.5 * G.crystal_diameter_m,
                crystal_height_m=G.crystal_height_m,
                crystal_centre_z_m=G.deck_clearance_m + 0.5 * 8.6e-3,
            )
        return CavityGeometry(**kwargs)

    def test_mismatch_refused_both_ways(self):
        from cavity.forward_model import CrystalDielectric
        from cavity.forward_model.build import validate_crystal_consistency

        with pytest.raises(ValueError, match="crystal switch mismatch"):
            validate_crystal_consistency(self._ring(True), MaterialSpec())
        with pytest.raises(ValueError, match="crystal switch mismatch"):
            validate_crystal_consistency(
                self._ring(False),
                MaterialSpec(crystal=CrystalDielectric(epsilon_r_real=3.0)),
            )

    def test_agreement_passes(self):
        from cavity.forward_model import CrystalDielectric
        from cavity.forward_model.build import validate_crystal_consistency

        validate_crystal_consistency(self._ring(False), MaterialSpec())
        validate_crystal_consistency(
            self._ring(True),
            MaterialSpec(crystal=CrystalDielectric(epsilon_r_real=3.0)),
        )
