"""COMSOL forward model — SPEC §2.

2D axisymmetric (r, z), m = 0, Eigenfrequency study near 1.45 GHz.

The pure-Python "what to build" layer (`geometry`, `materials`, `mesh`,
`study`) is importable without COMSOL/MPh and is re-exported here.
`build` and `solve` touch MPh; import them explicitly when needed and
call `is_comsol_available()` from `build` to check before invoking.
"""

from cavity.forward_model.geometry import (
    CavityGeometry,
    DielectricShape,
)
from cavity.forward_model.materials import (
    MU_0,
    MaterialSpec,
    copper_surface_resistance,
    sto_complex_permittivity,
)
from cavity.forward_model.mesh import (
    ConvergenceCriterion,
    MeshConfig,
)
from cavity.forward_model.study import (
    EigenStudyConfig,
    WallBC,
)

__all__ = [
    "MU_0",
    "CavityGeometry",
    "ConvergenceCriterion",
    "DielectricShape",
    "EigenStudyConfig",
    "MaterialSpec",
    "MeshConfig",
    "WallBC",
    "copper_surface_resistance",
    "sto_complex_permittivity",
]
