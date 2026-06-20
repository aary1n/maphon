"""SPEC §2 + §4 — eigenfrequency study config.

`WallBC` selects between Impedance BC (default; includes wall loss,
gives Q_total) and PEC (lossless walls; isolates Q_diel for the §4
wall-loss split).

`search_hz` anchors the eigenvalue solver near 1.45 GHz. The picked
mode is identified by **field pattern** (azimuthal E, axial H antinode,
H circulating in r-z), not by eigenvalue order — the field-symmetry
filter lives with the solver call, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from cavity.provenance import TARGET, TargetMode


class WallBC(Enum):
    """Wall boundary condition. PEC zeroes wall loss for §4 Q_diel."""

    IMPEDANCE = "impedance"
    PEC = "pec"


@dataclass(frozen=True)
class EigenStudyConfig:
    """Settings for one COMSOL eigenfrequency solve.

    `search_hz`: COMSOL searches near this frequency. Default
    `TARGET.f_design_hz` = 1.45 GHz; TE01delta sits within a few %
    once the puck partially fills the box.

    `n_modes`: number of eigenpairs returned. Several modes near 1.45 GHz
    coexist; the field-symmetry filter (SPEC §2 mode-ID) picks TE01delta
    from the list.

    `wall_bc`: IMPEDANCE for §5 Q_total; PEC for §4 Q_diel.
    """

    wall_bc: WallBC = WallBC.IMPEDANCE
    search_hz: float = TARGET.f_design_hz
    n_modes: int = 6
    target: TargetMode = TARGET

    def __post_init__(self) -> None:
        if self.search_hz <= 0:
            raise ValueError("search_hz must be positive")
        if self.n_modes < 1:
            raise ValueError("n_modes must be >= 1")
