"""SPEC §2/§5a — recovered Booth TE01delta geometry + faithful-branch
tan_delta (provenance pins for the 2026-07-10 §5a additions).

Pins the ratified constants.py additions against their documented
derivation (refs/booth_geometry_recovery.md):

  - Table 4 construction ratios EXACT on the recovered fields
    (minor = x/5, major = x/2, height = 1.5x at x = 12.28 mm);
  - the printed 2.46 mm is the 3-s.f. round of the ratio-exact
    2.456 mm (the sensitivity-solve literal, not the gate value);
  - the recovered torus is constructible in the geometry engine
    (fits-in-box invariants enforced by CavityGeometry.__post_init__);
  - BOOTH_MPH_TAN_DELTA reproduces the .mph material node's imaginary
    part and the unrounded Debye scaling of Booth Table 1, and sits
    the documented ~4.4% below the canonical 1.1e-4.
"""

from __future__ import annotations

import pytest

from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.provenance import (
    BOOTH_MPH_TAN_DELTA,
    GEOM_BOOTH_TE01D,
    STO,
    TARGETS,
)


class TestRecoveredGeometryRatios:
    def test_table_4_ratios_exact(self):
        x = GEOM_BOOTH_TE01D.box_radius_m
        assert x == 12.28e-3
        # Table 4 (Booth p. 15): Box Height (3/2)x, Dielectric Radius x/5,
        # major radius = the .mph-pinned radial midpoint x/2.
        assert GEOM_BOOTH_TE01D.box_height_m == pytest.approx(
            1.5 * x, rel=1e-12
        )
        assert GEOM_BOOTH_TE01D.torus_minor_radius_m == pytest.approx(
            x / 5.0, rel=1e-12
        )
        assert GEOM_BOOTH_TE01D.torus_major_radius_m == pytest.approx(
            x / 2.0, rel=1e-12
        )

    def test_printed_minor_is_3_sf_round_of_ratio_value(self):
        # App. A prints 2.46 (3 s.f.); the ratio value is 2.456.
        printed_mm = GEOM_BOOTH_TE01D.printed_minor_radius_m * 1e3
        exact_mm = GEOM_BOOTH_TE01D.torus_minor_radius_m * 1e3
        assert printed_mm == pytest.approx(2.46, abs=1e-12)
        assert round(exact_mm, 2) == pytest.approx(printed_mm, abs=1e-12)
        assert printed_mm != exact_mm  # the two literals are distinct roles

    def test_recovered_torus_constructible_and_fits_in_box(self):
        geom = CavityGeometry(
            box_radius_m=GEOM_BOOTH_TE01D.box_radius_m,
            box_height_m=GEOM_BOOTH_TE01D.box_height_m,
            dielectric_radius_m=GEOM_BOOTH_TE01D.torus_major_radius_m,
            dielectric_shape=DielectricShape.TORUS,
            dielectric_minor_radius_m=GEOM_BOOTH_TE01D.torus_minor_radius_m,
        )
        # __post_init__ already enforced: tube clear of axis, inside box
        # in r and z. Re-assert the physical clearances explicitly.
        r_inner = geom.dielectric_radius_m - geom.dielectric_minor_radius_m
        r_outer = geom.dielectric_radius_m + geom.dielectric_minor_radius_m
        assert r_inner > 0.0
        assert r_outer < geom.box_radius_m
        assert 2.0 * geom.dielectric_minor_radius_m < geom.box_height_m
        assert geom.dielectric_centre_z_m == pytest.approx(
            0.5 * GEOM_BOOTH_TE01D.box_height_m
        )


class TestFaithfulBranchTanDelta:
    def test_reproduces_mph_material_node(self):
        # .mph node: eps_r = 316.3 - j*0.0333378 at eps_r' = 316.3
        # (= TARGETS.booth.epsilon_r_real — no fresh eps_r literal).
        eps_r = TARGETS.booth.epsilon_r_real
        assert eps_r == 316.3
        assert BOOTH_MPH_TAN_DELTA * eps_r == pytest.approx(
            0.0333378, rel=1e-14
        )
        assert BOOTH_MPH_TAN_DELTA == pytest.approx(1.05400e-4, rel=1e-4)

    def test_is_unrounded_debye_scaling_of_table_1(self):
        # Booth Table 1: tan_delta = 1.6e-3 at 22 GHz; Debye scaling
        # (omega*tau >> omega_cavity regime) down to 1.45 GHz.
        debye = 1.6e-3 * 1.45 / 22.0
        assert BOOTH_MPH_TAN_DELTA == pytest.approx(debye, rel=1e-3)
        # ... whose 2-s.f. round is Table 2's printed 1.1e-4 = canonical.
        assert float(f"{debye:.2g}") == pytest.approx(STO.tan_delta)

    def test_canonical_delta_is_the_documented_q_lever(self):
        # canonical 1.1e-4 sits ~4.4% above the faithful branch — the
        # ~3-4% Q lever the branch gating exists for (a like-for-like
        # reproduction cannot stack it against a ±1% window).
        rel_delta = (STO.tan_delta - BOOTH_MPH_TAN_DELTA) / BOOTH_MPH_TAN_DELTA
        assert 0.04 < rel_delta < 0.05
