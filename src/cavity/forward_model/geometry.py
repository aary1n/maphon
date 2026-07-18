"""SPEC §2 — 2D axisymmetric (r, z) geometry, azimuthal index m = 0.

Three switchable dielectric cross-sections (`DielectricShape`):

  PUCK   right-circular cylinder of radius `dielectric_radius_m` and
         height `dielectric_height_m`, axially centred at z = box_height/2.
  TORUS  ring with major radius `dielectric_radius_m` and circular minor
         radius `dielectric_minor_radius_m`, centred at the mid-plane.
  RING   rectangle-cross-section annulus (added 2026-07-18, geometry
         re-base — the Wu build, `provenance.GEOM_WU_STO_RING`): inner
         radius `dielectric_inner_radius_m`, OUTER radius
         `dielectric_radius_m`, height `dielectric_height_m`, seated
         with its underside at `ring_bottom_z_m` above the floor (the
         deck clearance — NOT mid-plane-centred). RING-only extras: an
         optional `spacer` sub-domain (`SpacerSpec`, the cross-linked
         polystyrene seat under the ring — Wu's own COMSOL includes it,
         Fig. 6) and an optional piston step (`piston_radius_m` +
         `piston_gap_depth_m`: the box ceiling is the tuning piston, and
         the annular gap between piston edge and barrel is MODELLED,
         not simplified away — ratified 2026-07-18; the gap depth is
         unprinted and rides Q2).

Booth's appendix under-specified the cross-section (gap #1, SPEC §11);
the switch was exposed so §4 (wall-loss split) could decide empirically.
RESOLVED at the Booth point (2026-07-10, refs/booth_geometry_recovery.md):
the dielectric is a TORUS (Booth's own words, pp. 13/16), App. A's
2.46 mm is the cross-section (MINOR) radius per Table 4's x/5 ratio
(ratio-exact 2.456 mm), and the major radius is the one free DOF,
pinned at x/2 = 6.14 mm by the supervisor .mph (= App. A's anapole
row). The recovered values live in `provenance.GEOM_BOOTH_TE01D`; the
puck branch stays for non-Booth studies (e.g. the §8 PEC anchors), and
the TORUS branch is UNTOUCHED by the re-base — Booth remains the §5a
solver-correctness anchor.

Pure Python. COMSOL knows nothing about this module; `build.py`
translates the geometry into MPh calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from cavity.provenance import GEOM, NominalGeometry


class DielectricShape(Enum):
    PUCK = "puck"
    TORUS = "torus"
    RING = "ring"


@dataclass(frozen=True)
class SpacerSpec:
    """Stepped annular SEAT under the RING (Wu 2020 Fig. 6, digitized):
    a base annulus on the floor (z in [0, base_height]) whose top face
    carries the ring, plus an outer registration lip standing BESIDE the
    ring's outside wall (z in [base_height, base_height + lip_height]).
    NOT a bore plug — nothing sits under the bore.

    Model layout only; the graded dimensions live on
    `provenance.WuSTORingGeometry` (figure-derived, +/- ~0.3 mm) and the
    material grade on `provenance.CLPS`. Cross-checks against the ring
    (seat height = ring bottom; lip wraps outside the ring, no domain
    overlap) live in `CavityGeometry.__post_init__`.
    """

    base_inner_radius_m: float
    base_outer_radius_m: float
    base_height_m: float
    lip_inner_radius_m: float
    lip_outer_radius_m: float
    lip_height_m: float

    def __post_init__(self) -> None:
        for name in (
            "base_inner_radius_m",
            "base_outer_radius_m",
            "base_height_m",
            "lip_inner_radius_m",
            "lip_outer_radius_m",
            "lip_height_m",
        ):
            if getattr(self, name) <= 0:
                raise ValueError(f"spacer {name} must be positive")
        if self.base_inner_radius_m >= self.base_outer_radius_m:
            raise ValueError("spacer base inner radius must be < outer")
        if self.lip_inner_radius_m >= self.lip_outer_radius_m:
            raise ValueError("spacer lip inner radius must be < outer")

    def mask(
        self,
        r_m: NDArray[np.floating],
        z_m: NDArray[np.floating],
    ) -> NDArray[np.bool_]:
        """True inside (or on the boundary of) the seat cross-section —
        union of the base and lip rectangles; same boundary-inclusive
        convention as `CavityGeometry.dielectric_mask`."""
        r = np.asarray(r_m, dtype=np.float64)
        z = np.asarray(z_m, dtype=np.float64)
        base = (
            (r >= self.base_inner_radius_m)
            & (r <= self.base_outer_radius_m)
            & (z >= 0.0)
            & (z <= self.base_height_m)
        )
        lip = (
            (r >= self.lip_inner_radius_m)
            & (r <= self.lip_outer_radius_m)
            & (z >= self.base_height_m)
            & (z <= self.base_height_m + self.lip_height_m)
        )
        return base | lip


@dataclass(frozen=True)
class CavityGeometry:
    """Cavity layout in the r-z half-plane (axisymmetric, m = 0).

    Box: rectangle [0, box_radius_m] x [0, box_height_m]. The full 3D
    cavity is the volume of revolution about r = 0.

    PUCK is centred on the axis (r = 0) and axially at z = box_height/2.
    TORUS is centred at (r = dielectric_radius_m, z = box_height/2) with
    minor radius `dielectric_minor_radius_m`.
    RING (2026-07-18) is the annulus dielectric_inner_radius_m <= r <=
    dielectric_radius_m, ring_bottom_z_m <= z <= ring_bottom_z_m +
    dielectric_height_m — seated above the floor, NOT mid-plane-centred.
    RING-only extras: `spacer` (seat sub-domain under/around the ring)
    and the piston step (`piston_radius_m` + `piston_gap_depth_m`,
    jointly present or jointly None: the ceiling at z = box_height_m is
    the tuning piston of radius piston_radius_m, and the annular gap
    piston_radius_m <= r <= box_radius_m extends piston_gap_depth_m
    ABOVE the ceiling plane — the modelled piston-to-barrel clearance).

    All lengths SI (m). Validates that the dielectric fits strictly
    inside the box and that exactly the shape-matched dimensions are
    provided.
    """

    box_radius_m: float
    box_height_m: float
    dielectric_radius_m: float
    dielectric_shape: DielectricShape
    dielectric_height_m: float | None = None
    dielectric_minor_radius_m: float | None = None
    dielectric_inner_radius_m: float | None = None
    ring_bottom_z_m: float | None = None
    spacer: SpacerSpec | None = None
    piston_radius_m: float | None = None
    piston_gap_depth_m: float | None = None

    def __post_init__(self) -> None:
        if self.box_radius_m <= 0 or self.box_height_m <= 0:
            raise ValueError("box dimensions must be positive")
        if self.dielectric_radius_m <= 0:
            raise ValueError("dielectric radius must be positive")
        if self.dielectric_radius_m >= self.box_radius_m:
            raise ValueError(
                "dielectric radius must lie strictly inside box radius"
            )

        if self.dielectric_shape is not DielectricShape.RING:
            for name in (
                "dielectric_inner_radius_m",
                "ring_bottom_z_m",
                "spacer",
                "piston_radius_m",
                "piston_gap_depth_m",
            ):
                if getattr(self, name) is not None:
                    raise ValueError(
                        f"{self.dielectric_shape.name} does not use `{name}`"
                    )

        if self.dielectric_shape is DielectricShape.PUCK:
            if self.dielectric_height_m is None:
                raise ValueError(
                    "PUCK requires `dielectric_height_m` (unpinned in Booth; "
                    "sweep or load Booth's .mph -- SPEC §11 gap #1)"
                )
            if self.dielectric_height_m <= 0:
                raise ValueError("dielectric height must be positive")
            if self.dielectric_height_m >= self.box_height_m:
                raise ValueError(
                    "dielectric height must lie strictly inside box height"
                )
            if self.dielectric_minor_radius_m is not None:
                raise ValueError(
                    "PUCK does not use `dielectric_minor_radius_m`"
                )
        elif self.dielectric_shape is DielectricShape.TORUS:
            if self.dielectric_minor_radius_m is None:
                raise ValueError(
                    "TORUS requires `dielectric_minor_radius_m` (unpinned in "
                    "Booth; sweep or load Booth's .mph -- SPEC §11 gap #1)"
                )
            if self.dielectric_minor_radius_m <= 0:
                raise ValueError("torus minor radius must be positive")
            r_min = self.dielectric_radius_m - self.dielectric_minor_radius_m
            r_max = self.dielectric_radius_m + self.dielectric_minor_radius_m
            if r_min <= 0:
                raise ValueError(
                    "torus tube must not cross the symmetry axis "
                    "(minor radius < major radius)"
                )
            if r_max >= self.box_radius_m:
                raise ValueError(
                    "torus must lie strictly inside box in r"
                )
            if 2.0 * self.dielectric_minor_radius_m >= self.box_height_m:
                raise ValueError(
                    "torus minor diameter must lie strictly inside box in z"
                )
            if self.dielectric_height_m is not None:
                raise ValueError(
                    "TORUS does not use `dielectric_height_m`"
                )
        elif self.dielectric_shape is DielectricShape.RING:
            if (
                self.dielectric_height_m is None
                or self.dielectric_inner_radius_m is None
                or self.ring_bottom_z_m is None
            ):
                raise ValueError(
                    "RING requires `dielectric_height_m`, "
                    "`dielectric_inner_radius_m` and `ring_bottom_z_m`"
                )
            if self.dielectric_minor_radius_m is not None:
                raise ValueError(
                    "RING does not use `dielectric_minor_radius_m`"
                )
            if self.dielectric_inner_radius_m <= 0:
                raise ValueError("ring inner radius must be positive")
            if self.dielectric_inner_radius_m >= self.dielectric_radius_m:
                raise ValueError(
                    "ring inner radius must be < outer radius "
                    "(`dielectric_radius_m` is the OUTER radius for RING)"
                )
            if self.dielectric_height_m <= 0:
                raise ValueError("ring height must be positive")
            if self.ring_bottom_z_m <= 0:
                raise ValueError(
                    "ring bottom (deck clearance) must be positive"
                )
            if (
                self.ring_bottom_z_m + self.dielectric_height_m
                >= self.box_height_m
            ):
                # This strict check is what makes the p_tune travel floor
                # PHYSICAL: a box internal height drawn at or below the
                # ring's top refuses at construction.
                raise ValueError(
                    "ring top must lie strictly below the box ceiling "
                    "(ring_bottom_z_m + height < box_height_m)"
                )
            if self.spacer is not None:
                if self.spacer.base_height_m != self.ring_bottom_z_m:
                    raise ValueError(
                        "spacer base height must equal ring_bottom_z_m "
                        "(the ring seats on the BASE of the seat)"
                    )
                if self.spacer.lip_inner_radius_m < self.dielectric_radius_m:
                    raise ValueError(
                        "spacer lip must wrap OUTSIDE the ring "
                        "(lip inner radius >= ring outer radius; the seat "
                        "is not a bore plug and domains must not overlap)"
                    )
                if self.spacer.base_outer_radius_m >= self.box_radius_m or (
                    self.spacer.lip_outer_radius_m >= self.box_radius_m
                ):
                    raise ValueError(
                        "spacer must lie strictly inside the box in r"
                    )
            if (self.piston_radius_m is None) != (
                self.piston_gap_depth_m is None
            ):
                raise ValueError(
                    "piston fields are jointly present or jointly None "
                    "(`piston_radius_m` + `piston_gap_depth_m`)"
                )
            if self.piston_radius_m is not None:
                assert self.piston_gap_depth_m is not None
                if not (0.0 < self.piston_radius_m < self.box_radius_m):
                    raise ValueError(
                        "piston radius must lie strictly inside box radius"
                    )
                if self.piston_gap_depth_m <= 0:
                    raise ValueError("piston gap depth must be positive")

    @property
    def dielectric_centre_z_m(self) -> float:
        """Axial centre of the dielectric — the box mid-plane for
        PUCK/TORUS; ring bottom + half height for RING (the Wu ring is
        seated on its deck clearance, not mid-plane-centred)."""
        if self.dielectric_shape is DielectricShape.RING:
            assert (
                self.ring_bottom_z_m is not None
                and self.dielectric_height_m is not None
            )
            return self.ring_bottom_z_m + 0.5 * self.dielectric_height_m
        return 0.5 * self.box_height_m

    def dielectric_mask(
        self,
        r_m: NDArray[np.floating],
        z_m: NDArray[np.floating],
    ) -> NDArray[np.bool_]:
        """True at (r, z) nodes inside (or on the boundary of) the
        dielectric cross-section.

        This is the analytic mask the §3 export uses for `FieldSample`
        — computed from the geometry definition itself, never inferred
        from COMSOL domain numbering. Nodes exactly on the interface
        count as dielectric (the linear resampling smears the E-field
        discontinuity over one grid cell anyway).
        """
        r = np.asarray(r_m, dtype=np.float64)
        z = np.asarray(z_m, dtype=np.float64)
        z0 = self.dielectric_centre_z_m
        if self.dielectric_shape is DielectricShape.PUCK:
            assert self.dielectric_height_m is not None
            half_h = 0.5 * self.dielectric_height_m
            return (r <= self.dielectric_radius_m) & (
                np.abs(z - z0) <= half_h
            )
        if self.dielectric_shape is DielectricShape.RING:
            assert (
                self.dielectric_height_m is not None
                and self.dielectric_inner_radius_m is not None
            )
            half_h = 0.5 * self.dielectric_height_m
            return (
                (r >= self.dielectric_inner_radius_m)
                & (r <= self.dielectric_radius_m)
                & (np.abs(z - z0) <= half_h)
            )
        assert self.dielectric_minor_radius_m is not None
        return (r - self.dielectric_radius_m) ** 2 + (
            z - z0
        ) ** 2 <= self.dielectric_minor_radius_m**2

    def spacer_mask(
        self,
        r_m: NDArray[np.floating],
        z_m: NDArray[np.floating],
    ) -> NDArray[np.bool_]:
        """True inside the spacer seat; all-False when no spacer is
        declared. Same analytic-mask doctrine as `dielectric_mask` —
        computed from the definition, never from COMSOL domain
        numbering. The spacer must NEVER enter `dielectric_mask`
        (p_e is STO filling by definition); at the shared seat-top /
        ring-underside interface the existing boundary convention wins
        — interface nodes count as DIELECTRIC — so the dielectric mask
        is subtracted here."""
        if self.spacer is None:
            r = np.asarray(r_m, dtype=np.float64)
            z = np.asarray(z_m, dtype=np.float64)
            return np.zeros(np.broadcast(r, z).shape, dtype=bool)
        return self.spacer.mask(r_m, z_m) & ~self.dielectric_mask(r_m, z_m)

    @classmethod
    def from_nominal(
        cls,
        shape: DielectricShape,
        dielectric_height_m: float | None = None,
        dielectric_minor_radius_m: float | None = None,
        nominal: NominalGeometry = GEOM,
    ) -> "CavityGeometry":
        """Build a geometry from `NominalGeometry` (the SUPERSEDED
        width-as-diameter reading — see `NominalGeometry`'s docstring).

        Pass `dielectric_height_m` for PUCK or `dielectric_minor_radius_m`
        for TORUS. NOTE (2026-07-10 recovery): Booth's tabulated 2.46 mm
        is the torus MINOR (cross-section) radius per Table 4, not the
        major radius as this constructor's nominal wiring assumes; the
        major radius is the free DOF, pinned at x/2 by the supervisor
        .mph. For the Booth point build from `GEOM_BOOTH_TE01D` directly
        (validation.providers does); this constructor remains for the
        §8 anchors that solved at the old nominals.
        """
        return cls(
            box_radius_m=nominal.box_radius_m,
            box_height_m=nominal.box_height_m,
            dielectric_radius_m=nominal.dielectric_radius_m,
            dielectric_shape=shape,
            dielectric_height_m=dielectric_height_m,
            dielectric_minor_radius_m=dielectric_minor_radius_m,
        )
