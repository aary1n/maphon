"""SPEC §2 geometry — axisymmetric (r, z) layout, puck vs torus switch."""

from __future__ import annotations

import pytest

from cavity.forward_model import CavityGeometry, DielectricShape
from cavity.provenance import GEOM


class TestNominalConstruction:
    def test_nominal_puck_from_constants(self):
        g = CavityGeometry.from_nominal(
            DielectricShape.PUCK, dielectric_height_m=4.0e-3
        )
        assert g.box_radius_m == pytest.approx(GEOM.box_radius_m)
        assert g.box_height_m == pytest.approx(GEOM.box_height_m)
        assert g.dielectric_radius_m == pytest.approx(GEOM.dielectric_radius_m)
        assert g.dielectric_shape is DielectricShape.PUCK
        assert g.dielectric_height_m == pytest.approx(4.0e-3)
        assert g.dielectric_minor_radius_m is None

    def test_nominal_torus_from_constants(self):
        g = CavityGeometry.from_nominal(
            DielectricShape.TORUS, dielectric_minor_radius_m=1.0e-3
        )
        assert g.dielectric_shape is DielectricShape.TORUS
        assert g.dielectric_minor_radius_m == pytest.approx(1.0e-3)
        assert g.dielectric_height_m is None


class TestPuckValidation:
    def test_requires_height(self):
        with pytest.raises(ValueError, match="PUCK requires"):
            CavityGeometry.from_nominal(DielectricShape.PUCK)

    def test_rejects_height_outside_box(self):
        with pytest.raises(ValueError, match="dielectric height"):
            CavityGeometry.from_nominal(
                DielectricShape.PUCK,
                dielectric_height_m=GEOM.box_height_m,
            )

    def test_rejects_negative_height(self):
        with pytest.raises(ValueError, match="positive"):
            CavityGeometry.from_nominal(
                DielectricShape.PUCK, dielectric_height_m=-1.0e-3
            )

    def test_rejects_minor_radius_with_puck(self):
        with pytest.raises(ValueError, match="PUCK does not use"):
            CavityGeometry.from_nominal(
                DielectricShape.PUCK,
                dielectric_height_m=4.0e-3,
                dielectric_minor_radius_m=1.0e-3,
            )


class TestTorusValidation:
    def test_requires_minor_radius(self):
        with pytest.raises(ValueError, match="TORUS requires"):
            CavityGeometry.from_nominal(DielectricShape.TORUS)

    def test_rejects_torus_crossing_axis(self):
        with pytest.raises(ValueError, match="symmetry axis"):
            CavityGeometry.from_nominal(
                DielectricShape.TORUS,
                dielectric_minor_radius_m=GEOM.dielectric_radius_m + 1.0e-4,
            )

    def test_rejects_torus_punching_wall(self):
        # Booth's nominal box (R=6.14, r=2.46) can't fit a wall-punching torus
        # without first crossing the axis -- need a wider box for this case.
        with pytest.raises(ValueError, match="strictly inside box in r"):
            CavityGeometry(
                box_radius_m=10.0e-3,
                box_height_m=20.0e-3,
                dielectric_radius_m=7.0e-3,
                dielectric_shape=DielectricShape.TORUS,
                dielectric_minor_radius_m=4.0e-3,
            )

    def test_rejects_torus_taller_than_box(self):
        with pytest.raises(ValueError, match="inside box in z"):
            # tube diameter == box height: degenerate. Use a minor radius that
            # fits in r but blows z; box is 12.28 mm wide and 18.42 mm tall,
            # major radius 2.46 mm, so minor up to ~3.6 mm fits in r.
            CavityGeometry(
                box_radius_m=20.0e-3,
                box_height_m=4.0e-3,
                dielectric_radius_m=5.0e-3,
                dielectric_shape=DielectricShape.TORUS,
                dielectric_minor_radius_m=3.0e-3,
            )

    def test_rejects_height_with_torus(self):
        with pytest.raises(ValueError, match="TORUS does not use"):
            CavityGeometry.from_nominal(
                DielectricShape.TORUS,
                dielectric_height_m=4.0e-3,
                dielectric_minor_radius_m=1.0e-3,
            )


class TestBoxValidation:
    def test_rejects_non_positive_box(self):
        with pytest.raises(ValueError, match="box dimensions"):
            CavityGeometry(
                box_radius_m=0.0,
                box_height_m=1.0e-3,
                dielectric_radius_m=0.5e-3,
                dielectric_shape=DielectricShape.PUCK,
                dielectric_height_m=0.5e-3,
            )

    def test_rejects_dielectric_radius_outside_box(self):
        with pytest.raises(ValueError, match="dielectric radius"):
            CavityGeometry(
                box_radius_m=2.0e-3,
                box_height_m=4.0e-3,
                dielectric_radius_m=2.0e-3,
                dielectric_shape=DielectricShape.PUCK,
                dielectric_height_m=1.0e-3,
            )
