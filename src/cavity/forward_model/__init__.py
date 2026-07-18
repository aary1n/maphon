"""COMSOL forward model — SPEC §2.

2D axisymmetric (r, z), m = 0, Eigenfrequency study near 1.45 GHz,
packaged RF interface (SPEC §11 gap #4, resolved 2026-07-02).

The pure-Python layer (`geometry`, `materials`, `mesh`, `study`,
`gridding`, `mode_id`, `convergence`, `persistence`) is importable
without COMSOL/MPh and is re-exported here. `build`, `solve` and
`runner` touch MPh; import them explicitly when needed and call
`is_comsol_available()` from `build` to check before invoking.
"""

from cavity.forward_model.convergence import (
    MIN_CONVERGENCE_LEVELS,
    ConvergenceAssessment,
    ConvergenceError,
    assess_convergence,
)
from cavity.forward_model.geometry import (
    CavityGeometry,
    DielectricShape,
    SpacerSpec,
)
from cavity.forward_model.gridding import (
    GridSpec,
    StructuredGrid,
    structured_grid,
    trapezoid_weights_1d,
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
    refinement_ladder,
)
from cavity.forward_model.mode_id import (
    ModeDiagnostics,
    ModeIdentificationError,
    TE01DeltaCriteria,
    compute_mode_diagnostics,
    identify_te01delta,
)
from cavity.forward_model.persistence import (
    SolveRecord,
    load_solve_record,
    save_solve_record,
    solve_fingerprint,
    solve_hash,
)
from cavity.forward_model.study import (
    EigenStudyConfig,
    WallBC,
)

__all__ = [
    "MIN_CONVERGENCE_LEVELS",
    "MU_0",
    "CavityGeometry",
    "SpacerSpec",
    "ConvergenceAssessment",
    "ConvergenceCriterion",
    "ConvergenceError",
    "DielectricShape",
    "EigenStudyConfig",
    "GridSpec",
    "MaterialSpec",
    "MeshConfig",
    "ModeDiagnostics",
    "ModeIdentificationError",
    "SolveRecord",
    "StructuredGrid",
    "TE01DeltaCriteria",
    "WallBC",
    "assess_convergence",
    "compute_mode_diagnostics",
    "copper_surface_resistance",
    "identify_te01delta",
    "load_solve_record",
    "refinement_ladder",
    "save_solve_record",
    "solve_fingerprint",
    "solve_hash",
    "structured_grid",
    "sto_complex_permittivity",
    "trapezoid_weights_1d",
]
