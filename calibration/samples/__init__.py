"""T2 — sample configurations for the Cowley-Semple 2026-07-14 dataset.

Two entries, `D14` and `H14`, assembled entirely from `calibration.constants`
(no fresh literals) plus the T2 sweep grid the rig model runs over. The
grades live on the constants; a `SampleConfig` only wires them together.

The deuteration flag is load-bearing downstream: T5's df_spin/dT source
(Singh, SPEC §6T) is a PROTONATED crystal, so the h14 absolute fit is the
clean one and d14 carries the deuteration-transfer caveat; T4's intrinsic
branch is where a real d14/h14 material difference (k or df/dT) would land.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from calibration.constants import (
    CONCENTRATION,
    EXCITATION,
    LATERAL,
    RADIUS_MAPPING,
    SPOT,
    THICKNESS,
    UNDERSIDE,
)
from cavity.provenance.constants import K_PTP


@dataclass(frozen=True)
class SampleConfig:
    """One dataset sample: identity + the per-sample confirmed geometry."""

    name: str
    lateral_m: float  # collaborator-confirmed caliper width (see constants)
    powers_mw: tuple[float, ...]
    nominal_concentration: float
    concentration_grade: str
    deuterated: bool

    def disc_radius_m(self, radius_factor: float) -> float:
        """Equivalent-disc radius under the (swept) square→disc mapping."""
        if not RADIUS_MAPPING.factor_lo <= radius_factor <= RADIUS_MAPPING.factor_hi:
            raise ValueError(
                f"radius_factor {radius_factor} outside the mapped band "
                f"[{RADIUS_MAPPING.factor_lo}, {RADIUS_MAPPING.factor_hi}]"
            )
        return radius_factor * self.lateral_m


D14 = SampleConfig(
    name="d14",
    lateral_m=LATERAL.d14_lateral_m,
    powers_mw=EXCITATION.powers_d14_mw,
    nominal_concentration=CONCENTRATION.d14_nominal,
    concentration_grade=CONCENTRATION.d14_grade,
    deuterated=True,
)

H14 = SampleConfig(
    name="h14",
    lateral_m=LATERAL.h14_lateral_m,
    powers_mw=EXCITATION.powers_h14_mw,
    nominal_concentration=CONCENTRATION.h14_nominal,
    concentration_grade=CONCENTRATION.h14_grade,
    deuterated=False,
)

SAMPLES: dict[str, SampleConfig] = {"d14": D14, "h14": H14}


@dataclass(frozen=True)
class SweepGrid:
    """The T2 sweep axes (SI units). Shared axes are common to both samples
    in the T4 ratio; thickness is per-sample independent (plan T2/T4)."""

    thickness_m: tuple[float, ...]
    spot_diameter_m: tuple[float, ...]
    h_sub_w_m2_k: tuple[float, ...]
    k_w_m_k: tuple[float, ...]
    radius_factor: tuple[float, ...]

    @property
    def n_shared(self) -> int:
        return (
            len(self.spot_diameter_m)
            * len(self.h_sub_w_m2_k)
            * len(self.k_w_m_k)
            * len(self.radius_factor)
        )


def default_grid(
    n_thickness: int = 5, n_spot: int = 3, n_h_sub: int = 13, n_k: int = 3
) -> SweepGrid:
    """The ratified T2 grid: thickness linear over its bounds, spot linear
    300–500 µm, h_sub log over its decades, k log over the §6T band,
    radius mapping at {inscribed, equal-area, circumscribed}."""
    return SweepGrid(
        thickness_m=tuple(np.linspace(THICKNESS.lo_m, THICKNESS.hi_m, n_thickness)),
        spot_diameter_m=tuple(
            np.linspace(SPOT.diameter_sweep_lo_m, SPOT.diameter_sweep_hi_m, n_spot)
        ),
        h_sub_w_m2_k=tuple(
            np.logspace(
                math.log10(UNDERSIDE.h_sub_lo_w_m2_k),
                math.log10(UNDERSIDE.h_sub_hi_w_m2_k),
                n_h_sub,
            )
        ),
        k_w_m_k=tuple(
            np.logspace(
                math.log10(K_PTP.k_band_lo_w_m_k), math.log10(K_PTP.k_band_hi_w_m_k), n_k
            )
        ),
        radius_factor=(
            RADIUS_MAPPING.factor_lo,
            RADIUS_MAPPING.factor_point,
            RADIUS_MAPPING.factor_hi,
        ),
    )
