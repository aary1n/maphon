"""SPEC §6 — load-bearing constants, the single source of truth.

Every numeric value here traces back to a specific finding in
refs/pentacene_maser_parameter_provenance.md or to a published anchor
from SPEC §5/§5b. Do not duplicate these numbers elsewhere in the
codebase; import from this module.

Units: SI throughout (m, m^3, Hz, S/m). tan delta dimensionless.

Phase 2 input distributions live in `TolRanges` — keep them grounded
in §6, not in paper face values.

Published anchors live in `ValidationTargets`. Each `PublishedTarget`
carries the eps_r the paper actually used: reproducing Breeze Q=10,000
needs 318; reproducing Booth Q=6,980 needs 316.3. Pairing a target
with the wrong eps_r chases a phantom ~14 MHz frequency shift.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class STOSingleCrystal:
    """Flame-fusion STO single crystal at ~1.45 GHz, room temperature.

    `epsilon_r_real = 316.3` is Booth's input. Breeze uses 318 and Wu uses
    312; the 0.5% Breeze/Booth gap is Q-irrelevant, the full 1.9% spread
    shifts f by ~14 MHz (a tuning-range matter, not yield pass/fail).

    `tan_delta = 1.1e-4` is Booth's 22-GHz extrapolation (Debye,
    omega tau_ionic >> omega_cavity), which sits at the optimistic end
    of measured-device effective loss 1.0-2.3e-4.
    """

    epsilon_r_real: float = 316.3
    tan_delta: float = 1.1e-4
    mu_r: float = 1.0
    sigma: float = 0.0


@dataclass(frozen=True)
class Copper:
    """Cavity wall material. Drives the Impedance BC surface resistance."""

    sigma: float = 6.0e7
    mu_r: float = 1.0


@dataclass(frozen=True)
class Crystal:
    """Pentacene:p-terphenyl sub-domain (Breeze 2017).

    Booth argues this perturbs the mode only slightly; Phase 1b (§5b)
    verifies rather than assumes.
    """

    diameter_m: float = 3.0e-3
    height_m: float = 8.0e-3
    doping_mol_frac: float = 0.053e-2
    epsilon_r_upper_bound: float = 5.0
    mu_r: float = 1.0


@dataclass(frozen=True)
class NominalGeometry:
    """Booth Appendix A, STO TE01delta resonator.

    `dielectric_height_m` is UNPINNED in Booth (gap #1, SPEC §11). Either
    sweep it or load Booth's .mph when supervisor delivers it; the §4
    wall-loss split closes the gap empirically.
    """

    box_width_m: float = 12.28e-3
    box_radius_m: float = 6.14e-3
    box_height_m: float = 18.42e-3
    dielectric_radius_m: float = 2.46e-3
    dielectric_height_m: float | None = None


@dataclass(frozen=True)
class TargetMode:
    """The X-Z spin transition the cavity must overlap.

    `f_xz_measured_hz` is the cavity-pulled output peak (Breeze, Long);
    `f_design_hz` is the rounded nominal used in design talk.
    """

    f_xz_measured_hz: float = 1.4493e9
    f_design_hz: float = 1.45e9
    azimuthal_index_m: int = 0


@dataclass(frozen=True)
class TolRanges:
    """Phase 2 input distributions (SPEC §7). Refine geometry tols with supervisor.

    `machining_tol_m` is a uniform scalar dimension tolerance — a placeholder
    for the radii / heights of box and dielectric. It does NOT cover bore
    eccentricity: SPEC §7 calls out "bore-centring and wall-thickness
    tolerance are physically real and untunable" as a distinct DOF — a
    centring error, not a dimension scatter. When sweep/ adds the bore
    geometry (Phase 1b / §5b), bore eccentricity must enter as its own
    parameter; do not silently fold it into `machining_tol_m`.
    """

    epsilon_r_min: float = 312.0
    epsilon_r_max: float = 318.0
    tan_delta_min: float = 1.0e-4
    tan_delta_max: float = 2.3e-4
    machining_tol_m: float = 25e-6


@dataclass(frozen=True)
class PublishedTarget:
    """One published anchor: modelled or measured Q, V_mode, F_m at a stated eps_r.

    Each target carries the eps_r the paper actually used — pairing Breeze's
    Q=10,000 with Booth's 316.3 chases a phantom ~14 MHz shift.

    `v_mode_m3` and `f_m` are None for measured anchors that publish only
    loaded Q. `kind`: "modelled" (Breeze/Booth tables, compare to forward-
    model Q_0 directly) or "measured_loaded" (cold-cavity Q_L; de-load to
    Q_0 with `DELOAD_K` before comparing).
    """

    source: str
    epsilon_r_real: float
    q_factor: float
    f_hz: float
    v_mode_m3: float | None = None
    f_m: float | None = None
    kind: str = "modelled"


@dataclass(frozen=True)
class ValidationTargets:
    """SPEC §5/§5b published anchors. `validation.gate` imports from here.

    Modelled (forward model must reproduce these Q_0 directly):
      - breeze: Q=10,000, V=0.2 cm^3, F_m=3.6e7, eps_r=318       (Breeze Table 1)
      - booth:  Q=6,980,  V=0.409 cm^3,           eps_r=316.3    (Booth Table 8)

    Measured loaded-Q anchors (de-load with DELOAD_K to compare):
      - breeze_measured: Q_L=8,900   (Breeze 2017 cold-cavity)
      - npj_measured:    Q_L=8,500   (Salvadori npj 2020)
      - wu_measured:     Q_L=3,600   (Wu 2020; coupling unstated -> gap #3)

    Wall-loss split (SPEC §4, derived from the two modelled anchors and
    Q_diel_ceiling = 1/tan_delta = 9,091 at tan_delta = 1.1e-4):
      - Q_diel in [9_000, 10_000]
      - wall-loss fraction in [0.23, 0.27]

    Analytic benchmark (SPEC §8): empty-cavity TE_011 < 0.1% mesh-limited.
    """

    breeze: PublishedTarget
    booth: PublishedTarget
    breeze_measured: PublishedTarget
    npj_measured: PublishedTarget
    wu_measured: PublishedTarget

    q_diel_lo: float = 9_000.0
    q_diel_hi: float = 10_000.0
    wall_loss_fraction_lo: float = 0.23
    wall_loss_fraction_hi: float = 0.27

    empty_cavity_rel_error_max: float = 1.0e-3


# Applying k = 0.2 to Wu is an **assumption** — Wu's coupling coefficient
# is unstated (SPEC §11, gap #3). Breeze 2017 and Salvadori npj 2020 use
# k = 0.2; reusing it for Wu lets us de-load Q_L=3,600 -> Q_0 ~ 4,320 for
# the cross-paper comparison, but the resulting tan_delta upper bound
# (2.3e-4) carries that assumption.
DELOAD_K: float = 0.2


STO = STOSingleCrystal()
COPPER = Copper()
CRYSTAL = Crystal()
GEOM = NominalGeometry()
TARGET = TargetMode()
TOL = TolRanges()

TARGETS = ValidationTargets(
    breeze=PublishedTarget(
        source="Breeze 2017 Table 1 (STO row)",
        epsilon_r_real=318.0,
        q_factor=10_000.0,
        f_hz=1.45e9,
        v_mode_m3=0.2e-6,
        f_m=3.6e7,
        kind="modelled",
    ),
    booth=PublishedTarget(
        source="Booth 2018 Table 8 + Appendix A",
        epsilon_r_real=316.3,
        q_factor=6_980.0,
        f_hz=1.45e9,
        v_mode_m3=0.409e-6,
        f_m=None,
        kind="modelled",
    ),
    breeze_measured=PublishedTarget(
        source="Breeze 2017 cold-cavity loaded Q",
        epsilon_r_real=318.0,
        q_factor=8_900.0,
        f_hz=1.4493e9,
        kind="measured_loaded",
    ),
    npj_measured=PublishedTarget(
        source="Salvadori npj 2020 cold-cavity loaded Q",
        epsilon_r_real=318.0,
        q_factor=8_500.0,
        f_hz=1.4493e9,
        kind="measured_loaded",
    ),
    wu_measured=PublishedTarget(
        source="Wu 2020 cold-cavity loaded Q (coupling unstated, gap #3)",
        epsilon_r_real=312.0,
        q_factor=3_600.0,
        f_hz=1.4493e9,
        kind="measured_loaded",
    ),
)
