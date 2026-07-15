"""Layer A parametric sweep — SPEC §7 / docs/plans/layer_a_sweep_design.md.

ZERO-LICENCE tier implemented per docs/plans/ticklish-possum.md
(ratified 2026-07-15): design-matrix generation over the §2 DOF table,
mock/COMSOL solve backends, the per-draw driver with the RAW-only row
store, item-9 composition plumbing, and the sentinel-gated
sweep-centre verification block.

The Q2/Q9/Q11 gate is code, not convention: solve-ready row emission
(`DesignMatrix.solve_rows`), COMSOL backend construction
(`ComsolBackend`), and the centre-verification run all refuse with
`UnresolvedTodoTraceError` while any required TODO-trace sentinel is
unresolved (critical-path partition: zero training solves until Phase
1b definition lands). The d = 7 degraded mode is the recorded FALLBACK,
not baseline (§2/§6). Mock resolutions exercise pipeline shape only and
can never become solve-ready.

Dry-run tier: python -m cavity.sweep.driver --mock
"""

from cavity.sweep.dofs import (
    LAYER_A_DOFS,
    DesignMode,
    DofSpec,
    MockResolutionError,
    ResolutionContext,
    Rung,
    SentinelResolution,
    TodoTrace,
    UnresolvedTodoTraceError,
    mock_resolutions,
    sweep_dimension_names,
)
from cavity.sweep.design import (
    DesignBlock,
    DesignMatrix,
    EpsilonRVariant,
    GeometryDistributionVariant,
    SamplingDim,
    generate_design,
    materialise_dims,
    total_budgeted_solves,
)
from cavity.sweep.backend import (
    ComsolBackend,
    DrawSolveSpec,
    MockBackend,
    SolveBackend,
    draw_solve_spec,
)
from cavity.sweep.compose import (
    AnchorPoint,
    AnchorRefusalError,
    compose_derived_row,
    compose_derived_rows,
    c0_anchored,
    g2_absolute_diagnostic,
    g2_relative,
    kappa_c_hz,
    projection_invariance_report,
    write_derived_rows,
)
from cavity.sweep.centre_check import (
    PINNED_CENTRE,
    PinnedCentre,
    centre_verification_report,
    centre_verification_specs,
    run_centre_verification,
)
# Driver orchestration (run_sweep, run_mock_dry_run, load_raw_rows,
# validate_raw_row) is imported by module path — `cavity.sweep.driver`
# — NOT re-exported here, so `python -m cavity.sweep.driver` runs
# without runpy's already-imported RuntimeWarning.

__all__ = [
    "LAYER_A_DOFS",
    "AnchorPoint",
    "AnchorRefusalError",
    "ComsolBackend",
    "DesignBlock",
    "DesignMatrix",
    "DesignMode",
    "DofSpec",
    "DrawSolveSpec",
    "EpsilonRVariant",
    "GeometryDistributionVariant",
    "MockBackend",
    "MockResolutionError",
    "PINNED_CENTRE",
    "PinnedCentre",
    "ResolutionContext",
    "Rung",
    "SamplingDim",
    "SentinelResolution",
    "SolveBackend",
    "TodoTrace",
    "UnresolvedTodoTraceError",
    "c0_anchored",
    "centre_verification_report",
    "centre_verification_specs",
    "compose_derived_row",
    "compose_derived_rows",
    "draw_solve_spec",
    "g2_absolute_diagnostic",
    "g2_relative",
    "generate_design",
    "kappa_c_hz",
    "materialise_dims",
    "mock_resolutions",
    "projection_invariance_report",
    "run_centre_verification",
    "sweep_dimension_names",
    "total_budgeted_solves",
    "write_derived_rows",
]
