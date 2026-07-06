"""Validation — SPEC §5 gate + §8 analytic benchmark + §4 wall-loss split.

§8 (`analytic`) is pure Python and is the traceability anchor: the
COMSOL forward model must reproduce its closed-form values to <0.1%
before any number from the solver is trusted.

§4 (`wall_loss`) decomposes Q_total into Q_diel + Q_wall from two
solves (Impedance BC and PEC) of the same closed-cavity geometry,
with linear error propagation and a below-resolution flag for the
Breeze-end of the §6 confinement trend.

§5 (`gate` + `providers` + `report`) is the Phase-1-complete check.
The gate consumes payloads from a `SolveProvider` and judges the six
§5 rows through ONE code path regardless of source: synthetic CI
payloads, cached SPEC §1 solve records, or a live COMSOL session
(`requires_comsol` tier). Missing inputs are reported as
`deferred_requires_comsol`, never silently dropped; reports land as
JSON artifacts under `runs/` with the §1 reproducibility block.
Acceptance windows live in `cavity.provenance.gate_targets`.
"""

from cavity.validation.analytic import (
    C_LIGHT,
    bessel_zero_j,
    bessel_zero_jprime,
    f_te_mnp,
    f_tm_mnp,
    magnetic_purcell_factor,
    q_dielectric_homogeneous,
    q_dielectric_partial_fill,
)
from cavity.validation.gate import (
    GATE_REPORT_SCHEMA_VERSION,
    CheckStatus,
    GateCheckResult,
    GateReport,
    GateRowResult,
    evaluate_window,
    run_gate,
)
from cavity.validation.providers import (
    BoothPayload,
    ConfinementPayload,
    ConfinementPoint,
    EmptyCavityPayload,
    LiveComsolProvider,
    PecLossyPayload,
    ReproducibilityMetadata,
    SolveProvider,
    StaticProvider,
    Unavailable,
    WallLossPayload,
    provider_from_cache,
)
from cavity.validation.report import (
    REPORT_FILENAME,
    create_run_dir,
    report_to_dict,
    write_gate_report,
)
from cavity.validation.wall_loss import (
    WallLossDecomposition,
    decompose_wall_loss,
)

__all__ = [
    "C_LIGHT",
    "GATE_REPORT_SCHEMA_VERSION",
    "REPORT_FILENAME",
    "BoothPayload",
    "CheckStatus",
    "ConfinementPayload",
    "ConfinementPoint",
    "EmptyCavityPayload",
    "GateCheckResult",
    "GateReport",
    "GateRowResult",
    "LiveComsolProvider",
    "PecLossyPayload",
    "ReproducibilityMetadata",
    "SolveProvider",
    "StaticProvider",
    "Unavailable",
    "WallLossDecomposition",
    "WallLossPayload",
    "bessel_zero_j",
    "bessel_zero_jprime",
    "create_run_dir",
    "decompose_wall_loss",
    "evaluate_window",
    "f_te_mnp",
    "f_tm_mnp",
    "magnetic_purcell_factor",
    "provider_from_cache",
    "q_dielectric_homogeneous",
    "q_dielectric_partial_fill",
    "report_to_dict",
    "run_gate",
    "write_gate_report",
]
