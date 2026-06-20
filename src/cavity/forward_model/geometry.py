"""SPEC §2 — 2D axisymmetric (r, z) geometry, azimuthal index m = 0.

Two switchable dielectric cross-sections (`DielectricShape`):

  PUCK   right-circular cylinder of radius `dielectric_radius_m` and
         height `dielectric_height_m`, axially centred at z = box_height/2.
  TORUS  ring with major radius `dielectric_radius_m` and circular minor
         radius `dielectric_minor_radius_m`, centred at the mid-plane.

Booth's appendix under-specifies the cross-section (gap #1, SPEC §11) —
expose the switch and let §4 (wall-loss split) decide empirically which
shape reproduces the Booth two-point target.

Pure Python. COMSOL knows nothing about this module; `build.py`
translates the geometry into MPh calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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

    @classmethod
    def from_nominal(
        cls,
        shape: DielectricShape,
        dielectric_height_m: float | None = None,
        dielectric_minor_radius_m: float | None = None,
        nominal: NominalGeometry = GEOM,
    ) -> "CavityGeometry":
        """Build the Booth Appendix A geometry from `NominalGeometry`.

        Pass `dielectric_height_m` for PUCK or `dielectric_minor_radius_m`
        for TORUS — Booth tabulates only the major radius (2.46 mm); the
        second dimension is unpinned (SPEC §11 gap #1).
        """
        return cls(
            box_radius_m=nominal.box_radius_m,
            box_height_m=nominal.box_height_m,
            dielectric_radius_m=nominal.dielectric_radius_m,
            dielectric_shape=shape,
            dielectric_height_m=dielectric_height_m,
            dielectric_minor_radius_m=dielectric_minor_radius_m,
        )
