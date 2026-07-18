"""SPEC §2 — material specification for the eigenfrequency study.

STO enters as a **complex relative permittivity**:

    eps_r_complex = eps_r' * (1 - i * tan_delta)

with sigma = 0 (flame-fusion STO is lossless DC; tan_delta carries all
dielectric loss). The sign of the imaginary part follows COMSOL's
default e^(+i omega t) frequency-domain convention — verified against
the §8 partial-fill Q assertion before f'' is trusted (SPEC §11 gap #4).

Copper enters via the **Impedance Boundary Condition** on the box
walls. COMSOL computes R_s = sqrt(omega * mu_0 / (2 * sigma)) internally
from the wall conductivity; `copper_surface_resistance` is exposed for
sanity-checking. The §4 PEC variant is switched via `wall_pec=True`,
which suppresses wall loss entirely without changing the bulk dielectric.

Air defaults to vacuum (eps_r = mu_r = 1, sigma = 0).

Pure Python. `build.py` translates the spec into MPh material assignments.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cavity.provenance import (
    COPPER,
    STO,
    Copper,
    CrossLinkedPolystyrene,
    STOSingleCrystal,
)

MU_0: float = 4.0e-7 * math.pi


def sto_complex_permittivity(sto: STOSingleCrystal = STO) -> complex:
    """eps_r_complex = eps_r' * (1 - i * tan_delta)."""
    return sto.epsilon_r_real * (1.0 - 1j * sto.tan_delta)


def copper_surface_resistance(f_hz: float, copper: Copper = COPPER) -> float:
    """Surface resistance R_s = sqrt(omega * mu_0 / (2 * sigma)).

    Units: ohms per square. At 1.45 GHz with sigma = 6e7 S/m,
    R_s ~ 9.77 milli-ohm/sq.
    """
    if f_hz <= 0:
        raise ValueError("f_hz must be positive")
    if copper.sigma <= 0:
        raise ValueError("copper sigma must be positive")
    omega = 2.0 * math.pi * f_hz
    return math.sqrt(omega * MU_0 / (2.0 * copper.sigma))


@dataclass(frozen=True)
class MaterialSpec:
    """Material assignments for one §2 forward-model solve.

    `wall_pec=True` is the SPEC §4 variant: PEC walls (sigma -> infinity)
    isolate dielectric loss so Q -> Q_diel. Run once IBC + once PEC at
    the same geometry to extract 1/Q_wall = 1/Q_total - 1/Q_diel.

    `spacer` (2026-07-18, Wu-ring re-base): the cross-linked polystyrene
    seat material (`provenance.CLPS`) for RING geometries that declare a
    spacer sub-domain; None otherwise. Geometry and materials must agree
    — `build.validate_spacer_consistency` refuses a spacer-bearing
    geometry without a spacer material and vice versa.
    """

    sto: STOSingleCrystal = STO
    copper: Copper = COPPER
    wall_pec: bool = False
    spacer: CrossLinkedPolystyrene | None = None

    @property
    def sto_complex_eps_r(self) -> complex:
        return sto_complex_permittivity(self.sto)

    @property
    def spacer_complex_eps_r(self) -> complex:
        """eps_r_complex of the spacer (lossless this pass — see the
        `CrossLinkedPolystyrene` grade note). Raises when no spacer."""
        if self.spacer is None:
            raise ValueError("MaterialSpec has no spacer material")
        return self.spacer.epsilon_r_real * (
            1.0 - 1j * self.spacer.tan_delta
        )
