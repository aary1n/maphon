"""SPEC §6 parameter provenance — single source of truth.

Every load-bearing number used by the forward model, extraction, sweep,
and validation gate imports from here. Do not hard-code these values
anywhere else.

The graded provenance lives in
refs/pentacene_maser_parameter_provenance.md; this module encodes only
the §6 summary findings and the §5/§5b published anchors.

§5 gate ACCEPTANCE windows (decisions, not physics) live separately in
`gate_targets` — they reference the anchors here and are revisable
without touching graded provenance.
"""

from cavity.provenance.constants import (
    BOOTH_IMPLIED_F_M,
    BOOTH_IMPLIED_V_MODE_M3,
    BOOTH_MPH_TAN_DELTA,
    BOOTH_TABLE8_REVOLUTION_FACTOR,
    COPPER,
    CRYSTAL,
    C_LIGHT,
    DELOAD_K,
    EXTRACTION_TOL,
    F_M_BENCHMARK,
    GEOM,
    GEOM_BOOTH_TE01D,
    KAPPA_S,
    STO,
    TARGET,
    TARGETS,
    TOL,
    WALL_LOSS_THRESHOLDS,
    BoothTE01DeltaGeometry,
    Copper,
    Crystal,
    ExtractionTolerances,
    FMBenchmarkRange,
    NominalGeometry,
    PublishedTarget,
    SpinResonanceLinewidth,
    STOSingleCrystal,
    TargetMode,
    TolRanges,
    ValidationTargets,
    WallLossThresholds,
)
from cavity.provenance.gate_targets import (
    GATE_ROWS,
    GateCheckSpec,
    GateRowSpec,
    GateWindow,
)

__all__ = [
    "GATE_ROWS",
    "GateCheckSpec",
    "GateRowSpec",
    "GateWindow",
    "BOOTH_IMPLIED_F_M",
    "BOOTH_IMPLIED_V_MODE_M3",
    "BOOTH_MPH_TAN_DELTA",
    "BOOTH_TABLE8_REVOLUTION_FACTOR",
    "BoothTE01DeltaGeometry",
    "GEOM_BOOTH_TE01D",
    "COPPER",
    "CRYSTAL",
    "C_LIGHT",
    "DELOAD_K",
    "EXTRACTION_TOL",
    "F_M_BENCHMARK",
    "GEOM",
    "KAPPA_S",
    "STO",
    "TARGET",
    "TARGETS",
    "TOL",
    "WALL_LOSS_THRESHOLDS",
    "Copper",
    "Crystal",
    "ExtractionTolerances",
    "FMBenchmarkRange",
    "NominalGeometry",
    "PublishedTarget",
    "SpinResonanceLinewidth",
    "STOSingleCrystal",
    "TargetMode",
    "TolRanges",
    "ValidationTargets",
    "WallLossThresholds",
]
