"""SPEC §6 / §6T — load-bearing constants, the single source of truth.

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

§3 extraction quality thresholds live in `ExtractionTolerances`; the
F_m self-consistency anchor lives in `FMBenchmarkRange`. C_LIGHT is the
SI speed of light, kept here so the F_m formula and the §8 analytic
benchmark resolve to a single physical constant.
"""

from __future__ import annotations

from dataclasses import dataclass


C_LIGHT: float = 299_792_458.0
"""Speed of light in vacuum, m/s. CODATA exact value."""


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


@dataclass(frozen=True)
class ExtractionTolerances:
    """SPEC §3 + §8 extraction-quality thresholds.

    `q_emw_cross_check_rel_tol`: when COMSOL exposes its emw.Qfactor, it
    is derived from the same complex eigenpair as f'/(2 f''); the two
    must agree to numerical-precision level. Used as a cross-check
    assertion only — never as a replacement for the primary f'/(2 f'')
    value (SPEC §3).

    `q_pec_lossy_rel_tol`: the §8 partial-fill anchor — in the PEC walls
    + lossy-dielectric limit Q must equal 1/(p_e * tan delta). Mesh-
    limited; loose enough that converged solves pass but inverted sign
    conventions or wrong Jacobians fail. This is the assertion that
    pins the COMSOL eigenfrequency convention (SPEC §11 gap #4).
    """

    q_emw_cross_check_rel_tol: float = 1.0e-3
    q_pec_lossy_rel_tol: float = 5.0e-3


@dataclass(frozen=True)
class WallLossThresholds:
    """SPEC §4 wall-loss decomposition resolution gate.

    1/Q_wall = 1/Q_total - 1/Q_diel is a cancellation-prone subtraction
    when Q_total approaches Q_diel (the Breeze regime, walls
    negligible). The linearised relative uncertainty in Q_wall blows
    up as the difference vanishes; we refuse to report a trustworthy
    interval on Q_wall when sigma(Q_wall) / Q_wall exceeds this
    threshold, and the decomposition returns `below_resolution = True`.

    Above threshold: linear sigma_Q_wall is reported as a real
    interval. Below threshold flagged: the magnitude carries the
    `below_resolution` caveat and its only valid use is "Q_wall is
    large enough that walls don't load this mode", consistent with
    SPEC §6's claim that Breeze's modelled Q sits at the dielectric
    ceiling.

    `below_resolution_rel_uncertainty = 0.5` is a starting knob: at
    that level the linearised interval spans 0.5 * Q_wall to
    1.5 * Q_wall, which is wide enough that the magnitude is no
    longer informative. Tightening this will reclassify more
    boundary cases as resolved; loosening it tolerates wider noise.
    Justify in the writeup, not in the code.
    """

    below_resolution_rel_uncertainty: float = 0.5
    reason: str = (
        "1/Q_wall = 1/Q_total - 1/Q_diel is cancellation-prone when "
        "Q_total ~ Q_diel; in that regime the linearised relative "
        "uncertainty on Q_wall exceeds this threshold and the "
        "magnitude is reported as below_resolution, consistent with "
        "walls being negligible (the Breeze end of the §6 confinement "
        "trend) rather than carrying a confident finite value."
    )


@dataclass(frozen=True)
class FMBenchmarkRange:
    """SPEC §3 F_m self-consistency anchor on Breeze inputs.

    Q = 1e4, V = 0.2e-6 m^3, f = 1.45 GHz must give F_m in
    [f_m_lo, f_m_hi]:
      - lower bound 3.3e7 accommodates the exact (3/(2π)^2) prefactor
        result 3.36e7 (which SPEC §3 rounds to 3.4e7 at 2 s.f.);
      - upper bound 3.6e7 is Breeze's tabulated value.

    The ~7% gap is the provenance trap SPEC §3 calls out: Breeze's
    printed prefactor is dimensionally inconsistent, so the formula
    floor and the tabulated ceiling do not coincide. Falling inside
    this range is the gate: anything outside means the formula or the
    units are wrong, and no F_m downstream is to be trusted.
    """

    f_m_lo: float = 3.3e7
    f_m_hi: float = 3.6e7


@dataclass(frozen=True)
class SpinFreqTempCoefficient:
    """SPEC §6T — df_spin/dT of the X-Z (1.45 GHz) transition near RT.

    Primary (RT): Singh, D'Souza, Garrett, Singh, Blankenship, Druga,
    Montis, Tan & Ajoy, Nat. Commun. 16, 10530 (2025),
    doi 10.1038/s41467-025-65508-2 (Ajoy group, Berkeley — not
    Bayliss). Sample: 0.1% Bridgman-grown pentacene:p-terphenyl single
    crystal, CW-ODMR vs temperature. `df_dt_hz_per_k = -101e3` is the
    region-III linear fit (monoclinic phase; region III = cold-finger
    150-330 K per SI Table S1 footnote — "includes RT" only in
    cold-finger readings, see the reanalysis caveat below; Fig.
    2B(iii) red line). Sign is negative: ODMR peaks blue-shift as
    temperature DECREASES (Fig. 1D/E caption) — opposite in sign to
    the STO cavity arm (~ +2.6 MHz/K), so the differential detuning
    ADDS (SPEC §6T).

    DO NOT use the paper's headline 247 kHz/K: that is the T_xy
    (107 MHz) transition inside the 193 K phase-transition region
    (region II; Table 1 footnote "taken from phase transition
    region") — not an RT coefficient and not the maser transition.

    Band across sources (carry as the §7.6 channel-3 prior; do not
    collapse to a point): Oxborrow in-thread RT quote -50 kHz/K;
    Lang 2007 Fig. 4 average -70 kHz/K over 230-296 K (nonlinear,
    steepens toward 193 K); W20 prints -80 kHz/K off the same figure;
    Singh region-III fit -101 kHz/K. Treat -101 as the band edge, not
    a replacement local fit: a single linear fit over 195-330 K
    over-weights the steeper near-transition end if Lang's curvature
    is real.

    Caveats carried from Singh — upgraded by the 2026-07-04 SI pass
    and figure reanalysis (refs/singh_fig2biii_reanalysis.md):

    - No uncertainty exists in print anywhere: main text and SI
      Table S1 both print the slope bare. The raw data are a Zenodo
      record (doi 10.5281/zenodo.17231876) whose files are
      RESTRICTED — request access if the +/- ever becomes
      load-bearing. No numeric +/- is therefore carried here.
    - Vector extraction of Fig. 2B(iii) (197 points, tick-exact
      axes) shows the statistical error of any one fit window is
      negligible (+/-1-2 kHz/K); the dominant uncertainty is the
      FIT-WINDOW SYSTEMATIC: OLS gives -68.4 over cold-finger
      150-330 K (the SI's region III), -88 over 200-330, -97 over
      220-330, and -112 over 254-324 K — the span the paper's own
      red fit line is actually drawn on (OLS reproduces the drawn
      line exactly). The printed -101 matches no stated window and
      disagrees with the paper's own drawn fit.
    - The temperature axis is the cryostat COLD-FINGER: the
      "abs. T 193 K" transition marker is drawn at cold-finger
      ~138.5 K, i.e. a laser-heating offset of ~ +55 K at the
      stated 110 mW cw. The -101/-112 window therefore samples
      actual ~310-380 K, ABOVE room temperature. Offset-corrected,
      Singh's own local slope at actual RT reads ~ -70...-80 kHz/K,
      consistent with Lang 2007 / W20 — not -101.
    - Curvature is confirmed and monotonic (local slope ~0 at
      cold-finger 180-210 K, -130 kHz/K at 290-320 K). The flat
      stretch maps to actual ~225-265 K where Lang shows ~-50:
      either the heating offset is NOT constant (contradicting the
      authors' assertion) or the samples differ — both argue
      against importing -101 as a local RT coefficient.

    Verdict: keep -101 as the conservative band edge; the band
    below is now empirically supported by Singh's own plotted data,
    not merely prudent.

    Deuteration caveat (carry alongside): Singh measured PROTONATED
    Pc:PTP; the Cowley-Semple calibration-dataset samples are
    Pc-d14:PTP-d14. Transfer of df_spin/dT to the deuterated system
    is assumed small — the mechanism is host-lattice thermal
    expansion and the d14 host is nominally the same lattice — but
    it is unverified by any measurement in hand.
    """

    df_dt_hz_per_k: float = -101e3
    df_dt_band_lo_hz_per_k: float = -101e3
    df_dt_band_hi_hz_per_k: float = -50e3


STO = STOSingleCrystal()
COPPER = Copper()
CRYSTAL = Crystal()
GEOM = NominalGeometry()
TARGET = TargetMode()
TOL = TolRanges()
EXTRACTION_TOL = ExtractionTolerances()
F_M_BENCHMARK = FMBenchmarkRange()
WALL_LOSS_THRESHOLDS = WallLossThresholds()
DF_SPIN_DT = SpinFreqTempCoefficient()

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
