"""SPEC §6 parameter provenance — single source of truth.

Every load-bearing number used by the forward model, extraction, and
sweep imports from here. Do not hard-code these values anywhere else.

The graded provenance lives in
refs/pentacene_maser_parameter_provenance.md; this module encodes only
the §6 summary findings.
"""

from cavity.provenance.constants import (
    COPPER,
    CRYSTAL,
    DELOAD_K,
    GEOM,
    STO,
    TARGET,
    TolRanges,
    Copper,
    Crystal,
    NominalGeometry,
    STOSingleCrystal,
    TargetMode,
)

__all__ = [
    "COPPER",
    "CRYSTAL",
    "DELOAD_K",
    "GEOM",
    "STO",
    "TARGET",
    "TolRanges",
    "Copper",
    "Crystal",
    "NominalGeometry",
    "STOSingleCrystal",
    "TargetMode",
]
