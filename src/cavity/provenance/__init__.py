"""SPEC §6 parameter provenance — single source of truth.

Every load-bearing number used by the forward model, extraction, sweep,
and validation gate imports from here. Do not hard-code these values
anywhere else.

The graded provenance lives in
refs/pentacene_maser_parameter_provenance.md; this module encodes only
the §6 summary findings and the §5/§5b published anchors.
"""

from cavity.provenance.constants import (
    COPPER,
    CRYSTAL,
    DELOAD_K,
    GEOM,
    STO,
    TARGET,
    TARGETS,
    TOL,
    Copper,
    Crystal,
    NominalGeometry,
    PublishedTarget,
    STOSingleCrystal,
    TargetMode,
    TolRanges,
    ValidationTargets,
)

__all__ = [
    "COPPER",
    "CRYSTAL",
    "DELOAD_K",
    "GEOM",
    "STO",
    "TARGET",
    "TARGETS",
    "TOL",
    "Copper",
    "Crystal",
    "NominalGeometry",
    "PublishedTarget",
    "STOSingleCrystal",
    "TargetMode",
    "TolRanges",
    "ValidationTargets",
]
