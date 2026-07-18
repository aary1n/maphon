"""SPEC §2 geometry — axisymmetric (r, z) layout, puck vs torus switch."""

from __future__ import annotations

import numpy as np
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


class TestDielectricMask:
    """The analytic mask the §3 export uses — never COMSOL domain
    numbers. Probed at hand-picked points on both sides of each
    boundary."""

    def test_puck_mask(self):
        geom = CavityGeometry.from_nominal(
            DielectricShape.PUCK, dielectric_height_m=4.0e-3
        )
        z0 = geom.dielectric_centre_z_m
        r = np.array([0.0, 2.0e-3, 2.46e-3, 2.5e-3, 0.0, 0.0])
        z = np.array([z0, z0, z0, z0, z0 + 2.0e-3, z0 + 2.1e-3])
        mask = geom.dielectric_mask(r, z)
        # on axis, interior, boundary-inclusive in r; outside in r;
        # boundary-inclusive in z; outside in z.
        assert mask.tolist() == [True, True, True, False, True, False]

    def test_torus_mask(self):
        geom = CavityGeometry.from_nominal(
            DielectricShape.TORUS, dielectric_minor_radius_m=1.0e-3
        )
        z0 = geom.dielectric_centre_z_m
        r_maj = geom.dielectric_radius_m
        r = np.array([r_maj, r_maj + 1.0e-3, r_maj + 1.1e-3, 0.0])
        z = np.array([z0, z0, z0, z0])
        mask = geom.dielectric_mask(r, z)
        # tube centre, boundary-inclusive, outside the tube, on axis
        # (the torus never touches the axis).
        assert mask.tolist() == [True, True, False, False]

    def test_centre_is_box_midplane(self):
        geom = CavityGeometry.from_nominal(
            DielectricShape.PUCK, dielectric_height_m=4.0e-3
        )
        assert geom.dielectric_centre_z_m == pytest.approx(
            0.5 * GEOM.box_height_m
        )


# ---------------------------------------------------------------------------
# RING (2026-07-18, Wu-ring re-base) — rectangle-section annulus + seat
# ---------------------------------------------------------------------------

from cavity.forward_model import SpacerSpec  # noqa: E402
from cavity.provenance import GEOM_WU_STO_RING  # noqa: E402


def _wu_spacer() -> SpacerSpec:
    g = GEOM_WU_STO_RING
    return SpacerSpec(
        base_inner_radius_m=g.spacer_base_inner_radius_m,
        base_outer_radius_m=g.spacer_base_outer_radius_m,
        base_height_m=g.spacer_base_height_m,
        lip_inner_radius_m=g.spacer_lip_inner_radius_m,
        lip_outer_radius_m=g.spacer_lip_outer_radius_m,
        lip_height_m=g.spacer_lip_height_m,
    )


def _wu_ring(**overrides) -> CavityGeometry:
    """Valid Wu-build RING at the as-operated internal height; the ring
    height is a plain float HERE ONLY because geometry construction is
    fork-agnostic — DOF-level selection is Q13-gated in cavity.sweep."""
    g = GEOM_WU_STO_RING
    kwargs = dict(
        box_radius_m=g.box_inner_radius_m,
        box_height_m=g.box_internal_height_asoperated_m,
        dielectric_radius_m=g.sto_outer_radius_m,
        dielectric_shape=DielectricShape.RING,
        dielectric_height_m=8.6e-3,
        dielectric_inner_radius_m=g.sto_inner_radius_m,
        ring_bottom_z_m=g.deck_clearance_m,
    )
    kwargs.update(overrides)
    return CavityGeometry(**kwargs)


class TestRingValidation:
    def test_requires_height_inner_and_bottom(self):
        for missing in (
            "dielectric_height_m",
            "dielectric_inner_radius_m",
            "ring_bottom_z_m",
        ):
            with pytest.raises(ValueError, match="RING requires"):
                _wu_ring(**{missing: None})

    def test_rejects_inner_not_below_outer(self):
        with pytest.raises(ValueError, match="inner radius must be <"):
            _wu_ring(dielectric_inner_radius_m=6.0e-3)

    def test_rejects_ring_crossing_axis(self):
        with pytest.raises(ValueError, match="inner radius must be positive"):
            _wu_ring(dielectric_inner_radius_m=-1.0e-3)

    def test_rejects_ring_punching_wall(self):
        with pytest.raises(ValueError, match="strictly inside box radius"):
            _wu_ring(dielectric_radius_m=14.0e-3)

    def test_rejects_ring_exceeding_box_height(self):
        # The strict ceiling check IS the physical p_tune travel floor.
        with pytest.raises(ValueError, match="strictly below the box ceiling"):
            _wu_ring(box_height_m=11.0e-3)

    def test_rejects_minor_radius_with_ring(self):
        with pytest.raises(ValueError, match="RING does not use"):
            _wu_ring(dielectric_minor_radius_m=1.0e-3)


class TestRingGeometry:
    def test_ring_centre_is_bottom_plus_half_height(self):
        geom = _wu_ring()
        assert geom.dielectric_centre_z_m == pytest.approx(
            3.0e-3 + 0.5 * 8.6e-3
        )

    def test_ring_mask(self):
        geom = _wu_ring()
        z0 = geom.dielectric_centre_z_m
        r = np.array([2.025e-3, 6.0e-3, 1.0e-3, 7.0e-3, 4.0e-3, 4.0e-3])
        z = np.array([z0, z0, z0, z0, 2.9e-3, 3.0e-3])
        mask = geom.dielectric_mask(r, z)
        # inner boundary, outer boundary, in the bore, outside the ring,
        # below the ring underside, on the underside (boundary-inclusive)
        assert mask.tolist() == [True, True, False, False, False, True]


class TestSpacer:
    def test_spacer_requires_ring(self):
        with pytest.raises(ValueError, match="does not use `spacer`"):
            CavityGeometry(
                box_radius_m=GEOM.box_radius_m,
                box_height_m=GEOM.box_height_m,
                dielectric_radius_m=GEOM.dielectric_radius_m,
                dielectric_shape=DielectricShape.PUCK,
                dielectric_height_m=4.0e-3,
                spacer=_wu_spacer(),
            )

    def test_spacer_mask_empty_when_absent(self):
        geom = _wu_ring()
        r = np.array([3.0e-3, 7.0e-3])
        z = np.array([1.0e-3, 4.0e-3])
        assert not geom.spacer_mask(r, z).any()

    def test_spacer_base_must_meet_ring_bottom_and_lip_wraps_outside(self):
        geom = _wu_ring(spacer=_wu_spacer())
        r = np.array([3.0e-3, 7.0e-3, 7.0e-3, 1.0e-3])
        z = np.array([1.0e-3, 4.0e-3, 5.0e-3, 1.0e-3])
        # base under the ring, lip beside the ring, above the lip, in the
        # open bore column (the seat is NOT a plug).
        assert geom.spacer_mask(r, z).tolist() == [True, True, False, False]
        # seat height must equal the deck clearance...
        bad_seat = SpacerSpec(
            base_inner_radius_m=2.5e-3,
            base_outer_radius_m=8.1e-3,
            base_height_m=2.0e-3,
            lip_inner_radius_m=6.1e-3,
            lip_outer_radius_m=8.1e-3,
            lip_height_m=1.5e-3,
        )
        with pytest.raises(ValueError, match="seats on the BASE"):
            _wu_ring(spacer=bad_seat)
        # ...and the lip must wrap OUTSIDE the ring (no domain overlap).
        bad_lip = SpacerSpec(
            base_inner_radius_m=2.5e-3,
            base_outer_radius_m=8.1e-3,
            base_height_m=3.0e-3,
            lip_inner_radius_m=5.0e-3,
            lip_outer_radius_m=8.1e-3,
            lip_height_m=1.5e-3,
        )
        with pytest.raises(ValueError, match="wrap OUTSIDE the ring"):
            _wu_ring(spacer=bad_lip)


class TestPistonStep:
    def test_piston_step_fields_jointly_required(self):
        with pytest.raises(ValueError, match="jointly"):
            _wu_ring(piston_radius_m=13.0e-3)
        with pytest.raises(ValueError, match="jointly"):
            _wu_ring(piston_gap_depth_m=1.0e-3)
        geom = _wu_ring(piston_radius_m=13.0e-3, piston_gap_depth_m=1.0e-3)
        assert geom.piston_radius_m == 13.0e-3
