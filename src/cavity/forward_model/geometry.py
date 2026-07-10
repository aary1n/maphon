"""SPEC §2 — 2D axisymmetric (r, z) geometry, azimuthal index m = 0.

Two switchable dielectric cross-sections (`DielectricShape`):

  PUCK   right-circular cylinder of radius `dielectric_radius_m` and
         height `dielectric_height_m`, axially centred at z = box_height/2.
  TORUS  ring with major radius `dielectric_radius_m` and circular minor
         radius `dielectric_minor_radius_m`, centred at the mid-plane.

Booth's appendix under-specified the cross-section (gap #1, SPEC §11);
the switch was exposed so §4 (wall-loss split) could decide empirically.
RESOLVED at the Booth point (2026-07-10, refs/booth_geometry_recovery.md):
the dielectric is a TORUS (Booth's own words, pp. 13/16), App. A's
2.46 mm is the cross-section (MINOR) radius per Table 4's x/5 ratio
(ratio-exact 2.456 mm), and the major radius is the one free DOF,
pinned at x/2 = 6.14 mm by the supervisor .mph (= App. A's anapole
row). The recovered values live in `provenance.GEOM_BOOTH_TE01D`; the
puck branch stays for non-Booth studies (e.g. the §8 PEC anchors).

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


@dataclass(frozen=True)
class CavityGeometry:
    """Cavity layout in the r-z half-plane (axisymmetric, m = 0).

    Box: rectangle [0, box_radius_m] x [0, box_height_m]. The full 3D
    cavity is the volume of revolution about r = 0.

    PUCK is centred on the axis (r = 0) and axially at z = box_height/2.
    TORUS is centred at (r = dielectric_radius_m, z = box_height/2) with
    minor radius `dielectric_minor_radius_m`.

    All lengths SI (m). Validates that the dielectric fits strictly
    inside the box and that exactly one of the two shape-specific
    dimensions is provided.
    """

    box_radius_m: float
    box_height_m: float
    dielectric_radius_m: float
    dielectric_shape: DielectricShape
    dielectric_height_m: float | None = None
    dielectric_minor_radius_m: float | None = None

    def __post_init__(self) -> None:
        if self.box_radius_m <= 0 or self.box_height_m <= 0:
            raise ValueError("box dimensions must be positive")
        if self.dielectric_radius_m <= 0:
            raise ValueError("dielectric radius must be positive")
        if self.dielectric_radius_m >= self.box_radius_m:
            raise ValueError(
                "dielectric radius must lie strictly inside box radius"
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

    @property
    def dielectric_centre_z_m(self) -> float:
        """Axial centre of the dielectric — the box mid-plane."""
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
        assert self.dielectric_minor_radius_m is not None
        return (r - self.dielectric_radius_m) ** 2 + (
            z - z0
        ) ** 2 <= self.dielectric_minor_radius_m**2

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
