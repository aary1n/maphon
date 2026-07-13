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

import math
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
    """Cavity wall material. Drives the Impedance BC surface resistance.

    `sigma = 6.0e7 S/m` is the SPEC §2/§6 committed value. Booth-primary
    corroboration (recorded 2026-07-10, §5a pass): Booth's thesis
    (MEng_thesis-01865045.pdf) Table 3 prints copper electrical
    conductivity 6.00E+07 S/m — the identical value, from the primary
    the anchors are judged against. Value untouched by the
    corroboration.
    """

    sigma: float = 6.0e7
    mu_r: float = 1.0


@dataclass(frozen=True)
class Crystal:
    """Pentacene:p-terphenyl sub-domain (Breeze 2017).

    Booth argues this perturbs the mode only slightly; Phase 1b (§5b)
    verifies rather than assumes.

    `doping_mol_frac` is the NOMINAL melt doping. Oxborrow (verbal,
    in-person meeting 2026-07-06): Bridgman growth does NOT incorporate
    pentacene at the nominal doping — the growth acts as a zone-refining
    step, so the crystal holds LESS pentacene than the melt (and the
    p-terphenyl host is purified in the same pass). Direction known,
    factor unknown. Any quantity computed from this value (spin count N,
    absorption arithmetic) inherits a bias in a known direction; see
    `PumpAbsorptionLength` for the l_abs consequence and SPEC §7.T5 for
    the check-3b concentration-ratio caveat.
    """

    diameter_m: float = 3.0e-3
    height_m: float = 8.0e-3
    doping_mol_frac: float = 0.053e-2
    epsilon_r_upper_bound: float = 5.0
    mu_r: float = 1.0


@dataclass(frozen=True)
class NominalGeometry:
    """Booth Appendix A, STO TE01delta resonator — SUPERSEDED READING
    for the Booth point (2026-07-10; fields untouched).

    This dataclass encodes the original SPEC §2 parenthetical reading:
    "box width 12.28 mm (-> box radius 6.14 mm)", dielectric radius
    2.46 mm with the second dimension unpinned (gap #1, SPEC §11). The
    2026-07-10 document recovery (refs/booth_geometry_recovery.md)
    REFUTES that reading at the Booth point: Booth's "Resonator Width"
    is the axisymmetric r-EXTENT (box radius), proven by the exact
    correspondence of the supervisor .mph (refs/comsol/booth/) with
    App. A's ANAPOLE row, and Table 4 fixes the construction ratios
    (Box Width x, Box Height 1.5x, dielectric cross-section radius x/5)
    — so App. A's 2.46 mm is the torus MINOR radius (x/5, ratio-exact
    2.456 mm), not the major radius. Use `BoothTE01DeltaGeometry` /
    `GEOM_BOOTH_TE01D` for the Booth point.

    Fields are deliberately untouched: the §8 empty-cavity anchor and
    the PEC + lossy convention check were solved and frozen at these
    dimensions (refs/gate_runs/20260706T211615Z_live_comsol), and those
    checks are geometry-independent in what they assert. New Booth-point
    work must not consume this class.
    """

    box_width_m: float = 12.28e-3
    box_radius_m: float = 6.14e-3
    box_height_m: float = 18.42e-3
    dielectric_radius_m: float = 2.46e-3
    dielectric_height_m: float | None = None


@dataclass(frozen=True)
class BoothTE01DeltaGeometry:
    """Booth's STO TE01delta resonator, RECOVERED geometry (SPEC §2,
    §5a pass 2026-07-10; full derivation refs/booth_geometry_recovery.md).

    GRADE: document recovery from primary sources in hand, closed by
    in-repo cross-checks — not a solve output. Provenance chain:

    - Booth thesis (MEng_thesis-01865045.pdf) Appendix A (p. 29), STO
      TE01delta row: Resonator Width 12.28 mm / Resonator Height
      18.42 mm / Dielectric Radius 2.46 mm.
    - "Resonator Width" = the axisymmetric r-EXTENT (box radius), NOT a
      diameter: proven by the supervisor .mph
      (refs/comsol/booth/2D Resonator Lossy.mph), whose cavity
      r in [0, 22.36] mm, z half-height 16.77 mm, circle centre
      r = 11.18 mm, radius 4.472 mm reproduce App. A's ANAPOLE row
      (22.36 / 33.54 / 4.472) verbatim with width read as r-extent,
      and whose Q = 9581.37 matches Table 8's anapole 9.58E+03 to
      3 s.f. (refs/comsol/README.md, corrected this pass).
    - Table 4 (p. 15) fixes the construction ratios: Box Width x, Box
      Height (3/2)x, Dielectric (cross-section) Radius x/5;
      "Resonator dimensions are always adjusted in a proportionate
      manner, ensuring set ratios are maintained." So App. A's printed
      2.46 is the 3-s.f. print of the ratio value x/5 = 2.456 mm (the
      anapole row prints its ratio value 4.472 = 22.36/5 at 4 s.f.).
    - Torus form is Booth's own statement ("the toroidal resonator",
      p. 13; "torus-shaped dielectric ring", p. 16) — the puck reading
      retires at the Booth point.
    - The torus MAJOR radius (centre distance) is untabulated — the one
      free DOF — pinned at the radial midpoint x/2 by the .mph
      (11.18 = 22.36/2), with p. 17 confirming the ring-to-axis
      distance was never optimised.

    `torus_minor_radius_m` = 2.456e-3 is the RATIO-EXACT value the §5a
    gates are judged at (ratified branch choice 3);
    `printed_minor_radius_m` = 2.46e-3 is App. A's 3-s.f. print, used
    only for the one finest-mesh walls-on sensitivity solve recorded as
    a diagnostic alongside the gate.
    """

    box_radius_m: float = 12.28e-3
    box_height_m: float = 18.42e-3
    torus_minor_radius_m: float = 2.456e-3
    torus_major_radius_m: float = 6.14e-3
    printed_minor_radius_m: float = 2.46e-3


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


BOOTH_MPH_TAN_DELTA: float = 0.0333378 / 316.3
"""Booth's ACTUAL model tan_delta — the faithful-reproduction branch
(§5a pass, 2026-07-10; ratified branch choice 1).

Source: the supervisor-supplied Booth-tradition reference file
refs/comsol/booth/2D Resonator Lossy.mph, material node: SrTiO3 entered
as eps_r = 316.3 - j*0.0333378, i.e. tan_delta = 0.0333378/316.3
= 1.05400e-4 (in-repo, inspectable). Corroboration: this is the
UNROUNDED Debye scaling of Booth Table 1's tan_delta = 1.6e-3 at
22 GHz down to 1.45 GHz (1.6e-3 * 1.45/22 = 1.0545e-4 — the same
arithmetic whose 2-s.f. round is Table 2's printed 1.1e-4).

Role: the §5a Q and wall-loss gates are judged on THIS branch — a
like-for-like reproduction of Booth's 6,980 cannot stack a ~4.4%
tan_delta delta (a ~3% Q lever) against a ±1% window. The CANONICAL
SPEC §2 value stays `STOSingleCrystal.tan_delta` = 1.1e-4 (unchanged):
that is the model Phase 2 runs, solved as the companion branch and
feeding the margin report. SPEC §6's account ("Booth 6,980 = same
tan_delta [1.1e-4]") receives a dated correction this pass.
"""


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

    Live status (licence-session run, 2026-07-06): the §5 gate's live
    PEC + lossy arm CLEARS this tolerance at the gate's default mesh
    level (dielectric_max_h_m = 1.25e-4, air_max_h_m = 5.0e-4 — the
    §2 e2e test's finest ladder level; assumed a/L = 0.5 puck).
    Measured: residual |Q*p_e*tan_delta - 1| = 5.64e-5, i.e. ~1.1% of
    the 5e-3 tolerance consumed (headroom margin 0.989), from
    Q = 9112.8, p_e = 0.9977, tan_delta = 1.1e-4; COMSOL 6.0, 3,825
    elements. Artifact archived with the raw eigensolution:
    refs/gate_runs/20260706T211615Z_live_comsol — git-tracked, npz
    via LFS (§1 SolveRecord 888536d768e0fba1); a working copy also
    sits in the gitignored runs/gate/, but the refs/ copy is the
    citation. This is a CONVENTION PASS AT THAT LEVEL, not a
    mesh-independence result — convergence remains §2's job. Recorded
    so the pec_lossy default mesh is not re-litigated.
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
    """SPEC §6T — df_spin/dT of the X-Z (1.45 GHz) transition at
    operating temperature.

    RAW-DATA-GRADED (2026-07-07). Primary: the raw point series behind
    Singh, D'Souza, Garrett, Singh, Blankenship, Druga, Montis, Tan &
    Ajoy, Nat. Commun. 16, 10530 (2025), doi
    10.1038/s41467-025-65508-2, Fig. 2B(iii) (Ajoy group, Berkeley —
    not Bayliss; 0.1% Bridgman-grown PROTONATED Pc:PTP single crystal,
    CW-ODMR vs temperature), received 2026-07-07 from Harpreet Singh
    (first author) via the Berkeley contact thread (Noella D'Souza /
    Joseph Garrett), archived byte-for-byte in refs/singh_2025_raw/
    (SHA-256-pinned; PROVENANCE.md there). All values below are OLS
    fits by the committed script `cavity.provenance.singh_raw_fits`
    (report: refs/singh_2025_raw/fit_report.md), pinned in
    tests/test_provenance_df_spin_dt.py with band endpoints checked
    THROUGH the fit functions at test time. This supersedes the
    197-point vector re-digitisation (refs/singh_fig2biii_reanalysis.md,
    supersession note appended there) and retires the REFUTED-class
    audit status (audits/provenance_6T_audit.md — frozen snapshot,
    correct at audit time: the refutation targeted the printed/figure
    lineage, resolved below).

    LINEAGE AND RESOLUTION (printed -101 -> digitised -112 -> raw):

    - PRINTED -101 kHz/K (main text p. 3; SI Table S1, bare; no fit
      window printed anywhere — that absence stands as flagged, exact
      window still a Harpreet ask): CONSISTENT WITH THE RAW DATA. Raw
      OLS over the span the paper's red line is drawn on gives
      -102.3 +/- 1.1 (file-axis 254-324) / -103.4 +/- 1.0 (254-330) —
      the paper's number agrees with its own raw data to ~1%.
    - DIGITISED -112 kHz/K (2026-07-04 vector reanalysis): a FAITHFUL
      READING OF THE FIGURE. Rank-order pairing of the 197 raw points
      with the 197 extracted marker centres: frequency residuals rms
      39.5 kHz ~= the 0.1 MHz quantisation floor (28.9 kHz) — the
      pairing is right — while THE TWO TEMPERATURE AXES DIFFER BY AN
      EXACT AFFINE MAP, T_fig = 0.9316*T_raw + 16.56 K (rms residual
      0.09 K). Slopes in figure-axis units are inflated x1.073:
      -103.4 x 1.073 ~= -111, matching the -111.9 measured; the drawn
      red line back-maps to ~= -104 in file-axis units, i.e. it IS the
      raw-data fit rendered on the other axis. WHICH SIDE CARRIES THE
      CALIBRATED SENSOR READING IS UNRESOLVED — the file's 5-dp values
      look sensor-native (the likelier reading), but a
      publication-side recalibration of the file data is the live
      alternative; the Harpreet metadata ask decides. Every
      figure-derived number (-68.4/-88/-97/-112 window fits, the
      +55 K offset) is superseded by its raw-axis equivalent either
      way. The blinded-refuter canary (provenance_6T_audit.md) remains
      valid as a METHODOLOGY test: it validated faithful extraction
      from the figure, not the figure's fidelity to the data.
    - RAW (this grading): the fields below.

    VALUE AND BAND — the point is a BRANCH CHOICE, not a best
    estimate. The unresolved temperature-axis definition splits the
    operating-T reading into two branches ~x1.7 apart, and the band
    spans them:

    - `df_dt_hz_per_k` = -1.09e5 (3 s.f. of the OLS -108.5 +/- 2.2
      kHz/K over file-axis `t_window_lo_k`-`t_window_hi_k` = 293-310 K):
      the FACE-VALUE branch — the file axis read as sample
      temperature. Chosen as the point because it is the CONSERVATIVE
      branch (steeper |slope| => the differential detuning grows
      faster => smaller thermal margin). If the file axis is a
      cold-finger sensor and the +61 K offset is real, the true
      operating-T slope is the band-hi branch instead.
    - `df_dt_band_lo_hz_per_k` = -1.2e5 (outward 2 s.f. of the
      steepest operating-adjacent window, 290-330: -119.7 +/- 1.2).
    - `df_dt_band_hi_hz_per_k` = -6.4e4 (outward 2 s.f. of the
      COLD-FINGER branch: the raw X-Z series puts the 193 K-absolute
      transition jump at file-axis ~132.0 K => offset ~= +61 K at
      110 mW cw, so actual 293-310 K maps to file-axis 232-249 K,
      where OLS gives -64.4 +/- 1.7).

    CONVENTION SHIFT, DELIBERATE (2026-07-07): the previous grading
    put the point AT the conservative band edge (-101 = band lo); this
    grading's point is INTERIOR to the band — a documented branch
    choice at the operating window, not an edge. A future audit should
    read the edge->interior move as this re-convention, not drift.

    Ensemble context (no longer band-setting): Lang 2007 Fig. 4
    (~-70 kHz/K average, 230-296 K) and W20's -80 (same figure) sit
    near the cold-finger branch — corroboration of that branch.
    Oxborrow's in-thread RT quote of -50 kHz/K falls OUTSIDE the new
    band and is RETIRED from band duty (its audit verdict was
    SOURCE_MISSING/AMBIGUOUS — no document exists); kept here as
    context only.

    Sign is negative — verified from the raw data, no longer only from
    the Fig. 1D/E caption: spins red-shift on heating, OPPOSITE to the
    STO cavity arm (~ +2.7 MHz/K, `CavityFreqTempCoefficient`), so the
    differential detuning ADDS (SPEC §6T). Magnitude check:
    |df_spin/dT| ~ 60-120 kHz/K << df_cavity/dT ~ +2.7 MHz/K.

    DO NOT use the paper's headline 247 kHz/K: that is the T_xy
    (107 MHz) transition inside the 193 K phase-transition region
    (region II; Table 1 footnote "taken from phase transition
    region") — not an operating-T coefficient and not the maser
    transition.

    Caveats carried:

    - TEMPERATURE-AXIS DEFINITION UNRESOLVED (the dominant systematic
      — it IS the band): cold-finger vs sample vs recalibrated; see
      the affine-map finding above and PROVENANCE.md asks 1/4/5.
    - Deuteration caveat (carry alongside): Singh measured PROTONATED
      Pc:PTP; the Cowley-Semple calibration-dataset samples are
      Pc-d14:PTP-d14. Transfer of df_spin/dT to the deuterated system
      is assumed small — the mechanism is host-lattice thermal
      expansion and the d14 host is nominally the same lattice — but
      it is unverified by any measurement in hand.
    - LOCAL slope only: curvature is real and monotone on the raw data
      (quadratic 2a ~= -1.0 kHz/K^2 over 254-324; 30 K sliding windows
      run ~0 at file-axis 165-210 to -119 at 300-330). Never use any
      single window as a global fit.
    - The files are PLOTTED-POINT EXPORTS, not raw acquisition
      (N = 197 = the figure's marker count; 0.1 MHz frequency grid;
      5-dp processed temperatures). Per-point processing unknown.
    - 0.1 MHz quantisation: sigma_q = 28.9 kHz/point => ~1.2 kHz/K
      quantisation-only SE at the point window; statistical +
      quantisation is 1-3 kHz/K throughout, dwarfed by the axis-branch
      systematic. The paper still prints NO uncertainty anywhere; the
      +/- carried here is ours, residual-based.
    - Identity with the restricted Zenodo record
      (doi 10.5281/zenodo.17231876) assumed, unverified (ask 6).
    - Attribution: acknowledgement for use of this privately-shared
      data is to be brokered via Oxborrow EARLY, not at submission
      (PROVENANCE.md; same guard as the Cowley-Semple dataset).
    """

    df_dt_hz_per_k: float = -1.09e5
    df_dt_band_lo_hz_per_k: float = -1.2e5
    df_dt_band_hi_hz_per_k: float = -6.4e4
    t_window_lo_k: float = 293.0
    t_window_hi_k: float = 310.0


@dataclass(frozen=True)
class SpinResonanceLinewidth:
    """SPEC §6T / §7.T4 — kappa_s, the spin-line FWHM entering the
    two-linewidth threshold law (graded 2026-07-13, the
    steady-crossing-linewidths pass).

    UNIT CONVENTION — CYCLIC-Hz FWHM, the same convention as the
    committed kappa_c = f/Q_L. The two-mode threshold relation
    Delta_f_max = ((kappa_c + kappa_s)/2)*sqrt(C0 - 1) is homogeneous of
    degree 1 in (Delta, kappa_c, kappa_s) and C0 = 4G^2/(kappa_c*kappa_s)
    is invariant under uniform 2*pi rescaling, so the angular derivation
    transfers verbatim. Cross-pin: FWHM-cyclic kappa_s = 1/(pi*T2) —
    O12's own convention (its fitted Delta_f ≡ 1/(pi*T2) ≈ 860 kHz).
    W20's "kappa_s = 1.1 MHz" is ANGULAR (provenance table, unit trap 1)
    and rate-vs-FWHM murky besides — NEVER feed it here (anchor A6's
    kappa_s 2*pi-trap sibling guards the planning point).

    SOURCE — the Cowley-Semple linewidth table (SPEC §11 item 5;
    "linewidths" thread 2026-06-26, Glasgow/MIT/Imperial; scraped-thread
    depth, raw table = the existing Angus raw-data rider, now
    LOAD-BEARING): 1.75 MHz (0.1% Pc:PTP) · 1.4 MHz (0.1% d14) ·
    0.55 MHz (0.01% d14) · [7 MHz picene · 1.8 MHz NAP — DIFFERENT
    HOSTS, excluded from the band]. SPEC's own caveat carries verbatim:
    "Best-per-host at differing MW/laser powers — not a controlled
    comparison."

    VALUE AND BAND — the point is a BRANCH CHOICE, not a best estimate
    (the DF_SPIN_DT convention):

    - `kappa_s_hz` = 1.4e6: the 0.1% Pc-d14:PTP-d14 branch — the
      deuterated-sample branch the Phase-2 calibration chain lives on
      (same samples as the nu(I) series), interior to the band. Stated
      against it: the maser crystal itself is 0.053% PROTONATED
      (Breeze 2017; `Crystal`) — it matches no table row, and no
      kappa_s measurement of that crystal exists (the provenance
      table's "sample-specific — not importable" warning on the
      T2/kappa_s row carries verbatim).
    - `kappa_s_band_lo_hz` = 0.55e6, `kappa_s_band_hi_hz` = 1.75e6:
      the Pc:PTP-host rows across concentration and deuteration.

    DIRECTION OF CONSERVATISM: at fixed imported C0 (the planning
    convention — C0 = 190 is imported, never recomputed from G^2),
    smaller kappa_s ⇒ smaller Delta_f_max, so the 0.55 MHz edge is the
    conservative side, and the committed kappa_s -> 0 law was the
    maximally conservative member of the family. Band-direction bias
    (ratified amendment C): sweeping kappa_s at fixed imported C0
    holds G^2/kappa_c fixed; at fixed G the growth is ~sqrt(kappa_s),
    so the kappa_s-hi edge of the Delta_f_max band is OVERSTATED under
    the import convention — the band is not convention-independent.

    Caveats carried:

    - SINGLE-HOMOGENEOUS-PACKET MAPPING: the measured ODMR FWHM folds
      homogeneous 2/T2, inhomogeneous, and MW/laser power broadening
      into one number; treating it as the effective Lorentzian FWHM of
      one spin packet is an assumption of the threshold model, not a
      property of the data. O12's "few MHz" inhomogeneous width is NOT
      additionally stacked on top.
    - TEMPERATURE DEPENDENCE: kappa_s is T-dependent in reality — the
      §7.T2 output-3 broadening machinery (`cavity.thermal.broadening`)
      computes exactly the thermally-added inhomogeneous width. This
      constant is the STATIC, T-independent planning branch; the
      kappa_s(Delta_T) feedback loop (broadening output -> kappa_s ->
      threshold) is the identified follow-on pass, NOT implemented.
    - Ensemble context (context only, never band-setting): Yang 2000
      FID 0.7 MHz (0.01% protonated), O12 fitted 860 kHz +/- 20%,
      W20's adopted 1.1e6 s^-1 (angular). The table values sit
      consistent with the concentration trend of that lineage.
    - Attribution: the table is Angus Cowley-Semple's, shared in-thread
      — same early-brokering guard as the ODMR dataset (SPEC §11
      item 5 riders).
    """

    kappa_s_hz: float = 1.4e6
    kappa_s_band_lo_hz: float = 0.55e6
    kappa_s_band_hi_hz: float = 1.75e6


@dataclass(frozen=True)
class CavityFreqTempCoefficient:
    """SPEC §6T — df_cavity/dT of the STO TE01δ mode near room temperature.

    THE PREDICTION-ARM COEFFICIENT (SPEC §7.T5 observable (b)): model-only.
    Nothing in the Glasgow calibration thread observes the cavity arm; the
    spin arm (`SpinFreqTempCoefficient`) is the calibrated one. Do not blur
    the two — this constant is predicted physics, checked against
    literature parameterisations, never against a collaboration dataset.

    Derivation (encoded in `cavity_df_dt_hz_per_k`, guarded in
    tests/test_provenance_df_cavity_dt.py): f ∝ εr^(-1/2) ⇒

        df/dT = -(f/2) · (dεr/dT) / εr,    dεr/dT = -C / (T - T0)²

    with the Curie-Weiss parameters below and εr, f taken from the
    canonical constants of this module — `STO.epsilon_r_real` = 316.3
    (primary: Goryachev 2015) and `TARGET.f_design_hz` = 1.45 GHz (§2
    search target; the 1.4493 GHz measured peak differs by 0.05%,
    immaterial). No fresh εr or f literals enter the derivation.

    Primary (Curie-Weiss parameters, printed in text): Rupprecht & Bell,
    Phys. Rev. 125, 1915 (1962), p. 1916, Eq. (1): ε = C/(T - Tc) with
    C = 8.25e4 K, Tc = 37 K (extrapolated Curie temperature). Conditions:
    SrTiO3 single-crystal and polycrystalline specimens, microwave
    3-36 GHz, zero DC bias, paraelectric regime (their analysis is
    restricted to T above the 112 K phase transition — the validity
    floor below). CITATION-DEPTH CAVEAT (superscripts re-verified on
    the page image 2026-07-07, second pass — law sentence cites ref
    14; ref 12 = Bell & Rupprecht, IRE Trans. MTT-9, 239 (1961);
    ref 13 = RBS below; ref 14 = AFCRL): Eq. (1)'s parameters cite
    ref 14 = Rupprecht et al., AFCRL-TR-60-37, Raytheon, 1960 — an
    UNPUBLISHED Air Force report. The printed C/T0 are in hand; the
    specific NUMERIC values remain report-depth. Partially retired
    2026-07-07: the published companion (Rupprecht, Bell & Silverman,
    Phys. Rev. 123, 97 (1961), ref 13 on the same page — now in hand,
    read) MEASURES the Curie-Weiss form on single crystals over
    90-230 K, 1 kc/s-36 GHz (its Eq. (2): ε(T,0) = C/(T - Tc), "can
    adequately be described in the form"), but prints NO numeric C or
    Tc — only the nonlinearity constants A_hkl, B_100 and loss-fit
    constants. So: the CW FORM at microwave on single crystals is
    published-paper-backed in hand; the parameter VALUES still bottom
    out in the unpublished report. Note also RBS 1961's measured
    εr(T) window is 90-230 K — BELOW this constant's 293-323 K
    evaluation window; RT-end support comes from the cross-checks
    (Geyer 300 K point, Goryachev RT value) and from Saifi & Cross
    (lineage caveat below).

    Cross-check (independent group and data): Geyer, Riddle, Krupka &
    Boatner, JAP 97, 104111 (2005) Table I reprints the Vendik-model
    parameterisation (after Vendik et al., JAP 84, 993 (1998); ε00 =
    2080, TC = 42 K, θD = 175 K, ξS = 0.018), validated against NIST
    dielectric-resonator data at ~2.3 GHz, zero bias, 5.4/77/300 K. Its
    logarithmic slope at 300 K, d(ln εr)/dT = -3.789e-3 /K, agrees with
    R&B's -1/(T - T0) = -3.802e-3 /K to 0.4%. Only the logarithmic
    slope is used as the cross-check: the Vendik parameterisation's
    absolute εr(300 K) ≈ 334 runs ~6% above the canonical 316.3 —
    flagged, not adopted.

    RT-value anchor: Goryachev et al., arXiv:1508.07550 (2015) — the
    canonical εr = 316.3 ± 2.2 primary (single crystal, stress-free
    mount, isotropic and frequency-flat 4-11 GHz at RT). R&B's own
    implied εr(300 K) = C/263 = 313.7 agrees to 0.8%, so mixing R&B's
    dεr/dT with the canonical εr is harmless at the band's resolution.

    GRADE: DERIVED (M→D) FROM PARAMETERS PRINTED IN IN-HAND MICROWAVE
    SOURCES; BAND, NO PRINTED UNCERTAINTY; MODEL-ONLY ARM. Not M-grade:
    no source measured df/dT at 1.45 GHz directly; neither
    parameterisation prints an uncertainty; and the R&B parameter
    VALUES bottom out in the unpublished AFCRL report above (the CW
    form itself is published-measurement-backed in hand — RBS 1961).
    The value stands on the two-parameterisation 0.4% agreement plus
    the Goryachev consistency, not on any single citation chain.

    Value and band: `df_dt_hz_per_k` = +2.73e6 Hz/K at t_ref = 300 K.
    Band [+2.3e6, +2.9e6] Hz/K = bare `cavity_df_dt_hz_per_k`
    evaluations at the operating-envelope endpoints (293 K → +2.885e6,
    323 K → +2.312e6, rounded outward to 2 s.f.); the ±0.5%
    parameterisation spread and ±0.8% normalisation-convention spread
    are folded around the POINT value only, NOT stacked on the endpoint
    evaluations (the endpoints are bare function values). The 293-323 K
    envelope is SUPERVISOR-CONFIRMED (Oxborrow-verbal, 2026-07-08): he
    set the operating heating envelope at 30 K, superseding the earlier
    293-310 K planning assumption (lab ambient floor + ~17 K headroom).
    CAVEAT: "293 + 30 = 323 K" is OUR reading of the verbal "30 K"
    ruling, not his verbatim range. The band re-derivation stays
    mechanical via the window fields (this pass cashed the previous
    "one-line re-derivation by design" promise — the 2026-07-07 band
    was [+2.5e6, +2.9e6] over 293-310 K). Oxborrow's "several tens of
    Celsius" inference remains Glasgow-crystal heating, not
    our-geometry STO heating — that transfer is still unestablished;
    the envelope ruling supersedes it as the window's basis.

    SIGN CONVENTION — verified from the source, not assumed:
    ε = C/(T - Tc) with T >> Tc ⇒ dεr/dT < 0 ⇒ df_cavity/dT > 0 — the
    cavity mode BLUE-shifts on heating. OPPOSITE in sign to the spin
    arm (`SpinFreqTempCoefficient`, negative: spins red-shift on
    heating), so the differential detuning ADDS:

        |df_cav/dT - df_spin/dT| = df_cav/dT + |df_spin/dT|.

    Caveats carried:

    - LOCAL slope only. STO is a quantum paraelectric; εr(T) is steep
      and curved (Barrett-law saturation below ~θD/2, Curie-Weiss
      above). The point value is the local slope at 300 K, drifting
      +6%/-15% across 293-323 K and ±25% across 270-330 K. Never use
      it as a global linear fit; below the 112 K transition the form
      is invalid outright (the function raises). For excursions
      ΔT ≳ 20 K integrate the closed form
      Δf/f = (1/2)·ln((T2 - T0)/(T1 - T0)) rather than multiplying the
      point slope (~5% error already at ΔT = 30 K — and the ruled 30 K
      envelope sits exactly in this regime, so budget arithmetic over
      the full envelope should integrate, not multiply).
    - Measurement-regime consistency: all three sources are
      zero-DC-bias, unstressed, single-crystal-class measurements —
      the same regime the canonical εr = 316.3 usage assumes.
    - Frequency transfer: R&B 3-36 GHz, Geyer ~2.3 GHz, Goryachev
      4-11 GHz — all above our 1.45 GHz. Justified by measured
      frequency-flatness (Goryachev: no dependence 4-11 GHz; soft-mode
      theory: flat to >100 GHz at RT). A mild downward extrapolation,
      stated.
    - E-energy weighting assumed ≈ 1: the exact first-order
      perturbation is df/f = -(p_e/2)·Δεr/εr; the §8 gate run measured
      p_e = 0.9977, a -0.2% correction folded inside the band. A
      forward-model finite difference over εr can retire this
      assumption (open ask; not a §5 gate row).
    - Lineage of the figure this displaces — CLOSED 2026-07-07: the
      prose "+2.6 MHz/K" was W20's own back-of-envelope (Wu 2020,
      p. 064017-8: "estimated to be around +2.6 MHz/K") via its
      ref [48], Saifi & Cross, PRB 2, 677 (1970) — now in hand, read.
      SC p. 678 §III B (UNANNEALED single crystal) prints the
      modified Curie-Weiss fit, image-verified:

          ε = 40 + (8.5e4)/(T - 40),   "room temperature to 100 K"

      Conditions: bridge at 1 kHz, weak field, gold-electroded [100]
      plates ~4x4x0.4 mm. Self-consistently differentiated (its own
      ε(T) in the denominator) this gives +2.48 MHz/K at 300 K
      (+2.51 at 298 K with W20's f); variant arithmetic — pure-CW log
      slope 1/(T-40), or mixing SC's dε/dT with W20's εr = 312 —
      spans ~+2.5 to +2.9. W20's "around +2.6" is therefore EXPLAINED
      as SC-based RT arithmetic (it sits mid-spread), though W20
      prints no intermediates to pin the exact route. SC does NOT
      enter this constant's value or band: it is a 1 kHz ELECTRODED
      measurement — precisely the electrode-stress artifact class
      Goryachev 2015 identifies — whose absolute εr(300 K) ≈ 367 runs
      ~16% above the canonical microwave 316.3 and whose logarithmic
      slope at 300 K (-3.43e-3 /K) sits ~10% below the microwave
      parameterisations (R&B -3.80e-3, Geyer/Vendik -3.79e-3). Its
      implied +2.48 MHz/K lands at the band's low edge — consistent,
      regime-mismatched, not band-setting. Verdict unchanged:
      DISPLACED-AND-BANDED — W20's rounded figure falls inside the
      band's low half but understates the microwave-sourced 300 K
      local slope by ~5%.
    """

    curie_constant_k: float = 8.25e4
    curie_weiss_t0_k: float = 37.0
    t_validity_floor_k: float = 112.0
    t_ref_k: float = 300.0
    t_window_lo_k: float = 293.0
    t_window_hi_k: float = 323.0
    df_dt_hz_per_k: float = 2.73e6
    df_dt_band_lo_hz_per_k: float = 2.3e6
    df_dt_band_hi_hz_per_k: float = 2.9e6


def cavity_df_dt_hz_per_k(
    temp_k: float,
    *,
    f_hz: float | None = None,
    epsilon_r: float | None = None,
    curie_constant_k: float | None = None,
    curie_weiss_t0_k: float | None = None,
) -> float:
    """SPEC §6T — local cavity frequency-temperature slope at `temp_k`, Hz/K.

    df/dT = -(f/2)·(dεr/dT)/εr with dεr/dT = -C/(T - T0)² (Curie-Weiss;
    Rupprecht & Bell 1962 Eq. (1) — full provenance, grade, and caveats
    on `CavityFreqTempCoefficient`). Defaults resolve at call time to
    the canonical constants: f = `TARGET.f_design_hz`, εr =
    `STO.epsilon_r_real`, C/T0 = the `DF_CAVITY_DT` fields — no fresh
    εr or f literals.

    Raises ValueError below `DF_CAVITY_DT.t_validity_floor_k` (the
    112 K phase transition; the paraelectric Curie-Weiss form is
    invalid there). This is a LOCAL slope — see the dataclass caveats
    before using it away from room temperature or across large ΔT.
    """
    if f_hz is None:
        f_hz = TARGET.f_design_hz
    if epsilon_r is None:
        epsilon_r = STO.epsilon_r_real
    if curie_constant_k is None:
        curie_constant_k = DF_CAVITY_DT.curie_constant_k
    if curie_weiss_t0_k is None:
        curie_weiss_t0_k = DF_CAVITY_DT.curie_weiss_t0_k
    if temp_k < DF_CAVITY_DT.t_validity_floor_k:
        raise ValueError(
            f"temp_k = {temp_k} K is below the "
            f"{DF_CAVITY_DT.t_validity_floor_k} K phase transition; the "
            "paraelectric Curie-Weiss form (and this local slope) is "
            "invalid there (SPEC §6T, CavityFreqTempCoefficient)."
        )
    d_eps_dt = -curie_constant_k / (temp_k - curie_weiss_t0_k) ** 2
    return -(f_hz / 2.0) * d_eps_dt / epsilon_r


@dataclass(frozen=True)
class PTerphenylThermalConductivity:
    """SPEC §6T — thermal conductivity of crystalline p-terphenyl (the host).

    THE PARAMETER UNDER TEST in the §7.T5 check-3a identifiability sweep
    (`cavity.thermal.identifiability`): the CW calibration observable
    constrains k in the conduction-dominated regime (steady-state
    ΔT ∝ 1/k), and this is exactly where the open literature gap sits.

    Provenance floor: Hedley, Milnes & Yanko, J. Chem. Eng. Data 15, 122
    (1970) — *liquid* p-terphenyl k ≈ 0.134–0.136 W m⁻¹ K⁻¹ at
    213–254 °C. The unreferenced ~0.1 W m⁻¹ K⁻¹ crystal figure in the
    Breeze-2018 lineage coincides suspiciously with the liquid value
    (plausible provenance origin). Crystals conduct better than their
    melts, so 0.1 is treated as a FLOOR, and the working band is
    0.1–1.0 W m⁻¹ K⁻¹ (SPEC §6T). ~2× anisotropy is expected for a
    monoclinic molecular crystal; the thermal submodel currently uses an
    isotropic k — the anisotropy is folded into the band, not modelled.

    `k_mid_w_m_k` is the geometric midpoint of the band (the band is a
    multiplicative ×10 bracket, so the log-midpoint √(0.1·1.0) ≈ 0.316
    is the natural centre); it is the reference denominator of the
    identifiability ratio R in the §7.T5 sweep, not a physical claim.
    """

    k_floor_w_m_k: float = 0.1
    k_band_lo_w_m_k: float = 0.1
    k_band_hi_w_m_k: float = 1.0
    k_mid_w_m_k: float = 0.31622776601683794  # sqrt(lo * hi)
    anisotropy_factor: float = 2.0


@dataclass(frozen=True)
class ParaffinWaxThermal:
    """SPEC §6T — paraffin-wax mounting layer in the Glasgow ODMR rig.

    Mena et al., PRL 133, 120801 (2024), Methods: crystals are "attached
    to a glass slide using paraffin wax before being polished into
    plates". This is the ONLY published mounting for the rig; the Mann
    2025 SI leaves mounting unstated, and nothing confirms it for the
    Cowley-Semple dataset samples (Angus substrate/mounting rider —
    was ask 2, demoted 2026-07-06 when the list was finalised at three;
    SPEC §11 item 5).

    GRADE: GENERIC-HANDBOOK, NOT MEASURED FOR THIS RIG. Nominal
    k = 0.24 W m⁻¹ K⁻¹ is the "paraffin" entry of Incropera & DeWitt,
    Fundamentals of Heat and Mass Transfer (Table A.3, 300 K). Handbook
    values for paraffin waxes span ~0.2–0.3 W m⁻¹ K⁻¹ across grades and
    temperature; the wax grade in the rig is unknown. The bond-line
    thickness `t_wax` is completely unsourced — it is a NUISANCE
    PARAMETER swept over `t_wax_box` in the §7.T5 identifiability sweep
    (1–100 µm brackets hand-applied wax bond lines; an assumption, not a
    measurement). No wax/crystal or wax/glass contact resistance is
    carried: any interface resistance is partially degenerate with
    t_wax/k_wax and is absorbed into the t_wax sweep.
    """

    k_w_m_k: float = 0.24
    k_range_lo_w_m_k: float = 0.2
    k_range_hi_w_m_k: float = 0.3
    t_wax_box_lo_m: float = 1e-6
    t_wax_box_hi_m: float = 100e-6


@dataclass(frozen=True)
class GlassSlideThermal:
    """SPEC §6T — microscope-slide substrate in the Glasgow ODMR rig.

    GRADE: GENERIC-HANDBOOK, MATERIAL UNCONFIRMED. Nominal
    k = 1.14 W m⁻¹ K⁻¹ is the room-temperature borosilicate
    (Corning 7740 / Pyrex-class) value; handbook spread for borosilicate
    is ~1.0–1.4 W m⁻¹ K⁻¹ (Incropera & DeWitt Table A.3 prints 1.4 for
    "Pyrex"; manufacturer datasheets 1.1–1.2). Standard microscope
    slides are frequently SODA-LIME glass (k ≈ 0.9–1.1 W m⁻¹ K⁻¹), and
    the actual slide material is not stated anywhere in the published
    record — folded into the Angus substrate/mounting rider (was ask 2;
    SPEC §11 item 5). The `k_range` below spans both glass families.

    `t_glass_m = 1.0 mm` is the standard-slide assumption (commercial
    slides are 0.8–1.2 mm); SPEC §7.T5 prescribes a ±50% sensitivity
    check rather than a sweep dimension, because glass enters as a
    series term that the sweep shows is not verdict-setting.
    """

    k_w_m_k: float = 1.14
    k_range_lo_w_m_k: float = 0.9
    k_range_hi_w_m_k: float = 1.4
    t_glass_m: float = 1.0e-3
    t_glass_sensitivity_frac: float = 0.5


@dataclass(frozen=True)
class PTerphenylSurfaceEmissivity:
    """SPEC §7.T7 — thermal-IR emissivity of the p-terphenyl crystal surface.

    Feeds the linearised radiative loss h_rad = 4εσT³ that folds into the
    layered model's switchable Robin `h_top`
    (`cavity.thermal.radiation.h_rad_linearized`; §7.T7 first
    implementation slot, Oxborrow-verbal 2026-07-06 rung). ε must never be
    baked into solver code — the solver takes only the composed scalar
    `h_top`; callers pull ε from here.

    GRADE: CLASS-GENERIC BAND, RATIFIED AS-IS (Oxborrow-verbal,
    2026-07-08), UNSOURCED for Pc:PTP. No primary measurement of the
    emissivity of a doped p-terphenyl crystal surface exists in the
    project files or, to current knowledge, in print. The band 0.80–0.95
    is the generic total-hemispherical class for nonmetallic organic
    solids (plastics, paints, molecular solids) at ~300 K thermal IR
    (Incropera & DeWitt Table A.11-class entries) — cited as the CLASS,
    not as a material measurement. `eps_nominal = 0.90` is the
    conventional organic-solid handbook point value, sitting in the
    band's upper half — a convenience reference, not a band midpoint and
    not a physical claim. The 2026-07-08 ratification covers the band
    AS-IS — band, nominal, and caveats unchanged; it does not convert
    the class-generic band into a material measurement. ε thereby
    LEAVES the §11 item-10 Oxborrow bundle; the additive h_conv + h_rad
    composition and the fixed-ambient T³ REMAIN in it (ratified
    internally 2026-07-07, still pending Oxborrow).

    Caveats:
    - Semi-transparency: a 0.5-mm organic plate may be partially
      transparent in bands of the thermal IR, so the effective emitting
      surface is partly the stack below (glass, itself ε ≈ 0.9-class) —
      the band absorbs this; do not sharpen to a point value without a
      measurement on the actual sample form.
    - ε enters h_rad linearly, so the band maps directly onto
      h_rad ≈ 4.9–5.8 W m⁻² K⁻¹ at 300 K (4σT³ = 6.12 at ε = 1).
    - Band applies at ~300 K surface temperature; re-derive h_rad, not ε,
      for other operating points (T³ carries the temperature dependence).
    """

    eps_band_lo: float = 0.80
    eps_band_hi: float = 0.95
    eps_nominal: float = 0.90


@dataclass(frozen=True)
class FreeConvectionAir:
    """SPEC §7.T4/§7T — free-convection coefficient band, small bodies in still air.

    The convective half of the Robin boundary coefficient h that the
    thermal submodel's free surfaces carry (composed with the radiative
    half via `cavity.thermal.radiation.h_top_with_radiation`,
    h_eff = h_conv + h_rad).

    GRADE: PLANNING-ASSUMPTION BAND, CLASS-GENERIC — label unchanged by
    the 2026-07-08 reframe below: what was ratified is the REGIME
    FRAMING, not a measured value. The band is free convection from
    small bodies in OPEN STILL AIR — Incropera & DeWitt, Fundamentals
    of Heat and Mass Transfer, Ch. 9-class gas free convection,
    2–25 W m⁻² K⁻¹ — narrowed here to the 5–20 W m⁻² K⁻¹ scale this
    repo already uses (the `layered.py` module-docstring "h ~ 5–20"
    scale and the h = 20 sensitivity knob of the §7.T5 identifiability
    report, `identifiability.robin_h20_frac_drop`). No primary
    measurement exists for this rig or cavity.

    Regime reframe (Oxborrow-verbal, 2026-07-08): BOTH real geometries
    likely sit BELOW the open-air band — the Glasgow rig's enclosure is
    unknown (Angus ask, §11 item 5 rider: a housing suppresses free
    circulation), and the maser crystal sits in the semi-enclosed STO
    bore (suppressed circulation). Treat 5–20 as a plausible CEILING;
    h → 0 remains the floor via the switchable Robin BC (insulated
    limit).

    Forced-air variant (Oxborrow suggestion, verbal, 2026-07-08 — NOT
    adopted): forced-air cooling as a device design option would move h
    into the forced-gas class (~25–250 W m⁻² K⁻¹). Recorded as a
    flagged FUTURE SWEEP only — not a current modelling target; no
    constant carries a forced-air value.

    Existing consumers are NOT retrofitted: `layered.py`'s docstring
    scale and `identifiability.py`'s bare h = 20 stay as written; this
    constant single-sources the band for NEW consumers (the
    maser-cylinder anchor's tests and worked example, §7.T1).
    """

    h_band_lo_w_m2_k: float = 5.0
    h_band_hi_w_m2_k: float = 20.0


@dataclass(frozen=True)
class PumpAbsorptionLength:
    """SPEC §6T — optical absorption length of the 520–590 nm pump in Pc:PTP.

    GRADE: UNSOURCED-SCOPING. There is NO provenance-grade absorption
    length for the Cowley-Semple dataset samples (0.01–0.1% Pc-d14 in
    PTP-d14, pump 520 nm diode or 532 nm Nd:YAG depending on rig — §11
    item 5, asks 2/3 in the 2026-07-06 numbering). The grid below exists
    only to scope the §7.T5 check-3a volumetric-source sensitivity (does
    burying the near-spot source move the k–w degeneracy?); it brackets
    plausible 520–590 nm penetration in 0.01–0.1% doped material across
    ~1.5 orders of magnitude. None of these numbers may be used as a
    physical input to an absolute ΔT prediction.

    Likely primary when this becomes load-bearing: the Takeda 2002
    zero-field-ESR-era optical characterisation of Pc:PTP and/or the
    Breeze-thesis-era light-penetration discussion of pump absorption in
    doped p-terphenyl. NEITHER has been pulled and read for this number
    — deliberately NOT cited as a source here; obtain and grade before
    promoting any value out of scoping status (same discipline as the
    rest of §6T: no fabricated provenance).

    Nominal-doping caveat — CONFIRMED WITH DIRECTION (Oxborrow, verbal,
    in-person meeting 2026-07-06; previously an unsourced-scoping flag):
    Bridgman growth zone-refines, so actual [Pc] sits BELOW nominal by
    an unknown factor. Consequence for this constant: any l_abs computed
    from nominal doping OVERSTATES absorption and UNDERSTATES the
    penetration depth — a bias in a known direction. The "prefer
    measured penetration data over nominal-doping arithmetic" rule
    (SPEC §7.T5 volumetric rider) is therefore supervisor-backed, not
    merely prudent. See also `Crystal.doping_mol_frac` and the §7.T5
    check-3b concentration-ratio caveat.
    """

    l_abs_scoping_grid_m: tuple[float, ...] = (
        5e-6,
        10e-6,
        20e-6,
        50e-6,
        100e-6,
        200e-6,
    )


@dataclass(frozen=True)
class RigSampleGeometry:
    """SPEC §7.T5 — Glasgow-rig sample forms and pump-spot sweep box.

    Two sample forms, run SEPARATELY in the identifiability sweep (the
    per-sample form is Angus ask 1 — the single most load-bearing
    unknown for check 3a):

    - PLATE: t = 0.5 mm. Mena 2024 Methods (0.01% crystals polished into
      plates against 0.5 mm silicon guide plates); re-corroborated by
      the Mann 2025 JACS SI.
    - FILM: t = 100 nm. The only published 0.1% Pc:PTP is a 100 nm OMBD
      evaporated film on glass (Mann 2025, "for maximal contrast, we use
      thin films").

    Spot-radius box (1/e² radius w), set by the two-optic record of SPEC
    §7.T5 / §11 item 5 — no spot size is published for either rig
    configuration:

    - LOWER, 1 µm: diffraction-limited spot of the Mann 2025 cw+pulsed
      optic (Thorlabs C061TMD-A molded aspheric, f = 11.0 mm, NA 0.24,
      catalogue values checked 2026-07-04): filled-aperture Gaussian
      waist w ≈ λ/(π·NA) ≈ 0.7 µm at 532 nm, rounded up.
    - UPPER, 500 µm: the Mena 2024 cw optic (AC254-030-AB f = 30 mm
      achromatic doublet) with a fibre-coupled diode is tens-of-µm
      class; 500 µm covers an unfocused/misaligned doublet worst case
      with margin. (Extends the ~100 µm figure quoted in SPEC §7.T5's
      first pass; the sweep box deliberately over-covers.)
    """

    t_plate_m: float = 0.5e-3
    t_film_m: float = 100e-9
    w_box_lo_m: float = 1e-6
    w_box_hi_m: float = 500e-6


STO = STOSingleCrystal()
COPPER = Copper()
CRYSTAL = Crystal()
GEOM = NominalGeometry()
GEOM_BOOTH_TE01D = BoothTE01DeltaGeometry()
TARGET = TargetMode()
TOL = TolRanges()
EXTRACTION_TOL = ExtractionTolerances()
F_M_BENCHMARK = FMBenchmarkRange()
WALL_LOSS_THRESHOLDS = WallLossThresholds()
DF_SPIN_DT = SpinFreqTempCoefficient()
KAPPA_S = SpinResonanceLinewidth()
DF_CAVITY_DT = CavityFreqTempCoefficient()
K_PTP = PTerphenylThermalConductivity()
WAX = ParaffinWaxThermal()
GLASS_SLIDE = GlassSlideThermal()
EMISSIVITY_PTP = PTerphenylSurfaceEmissivity()
H_CONV_AIR = FreeConvectionAir()
RIG_GEOMETRY = RigSampleGeometry()
L_ABS_PUMP = PumpAbsorptionLength()

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


BOOTH_TABLE8_REVOLUTION_FACTOR: float = 225.0 / 360.0
"""Booth Table 8's mode-volume normalisation factor — her printed
V_mode values are this fraction of the true full-revolution integral
(SPEC §5a finding 2026-07-11, the V_mode forensic pass).

Mechanism, read from the supervisor-supplied Booth-tradition file
refs/comsol/booth/2D Resonator Lossy.mph (a readable zip; dmodel.xml
results tree, in-repo, inspectable): the result node "Mode Volume
Numerator" (op IntVolume, expression emw.normH*emw.normH, unit m*A^2)
evaluates on dataset rev1 = Revolution 2D at COMSOL's DEFAULT partial
revolution (start angle -90, revolution angle 225 — set verbatim in the
file's creation actions and never changed), while the "Mode volume
Denominator" (op MaxVolume, same expression) is revolution-angle
INVARIANT. Numerator scaled by 225/360, denominator not => printed
V_mode = 0.625 x true.

Grade / rung (the derived anchors below inherit it):
- mechanism CONFIRMED in the ANAPOLE model's node wiring (the one .mph
  in hand);
- the TE01delta row inherits it by UNIFORM-WORKFLOW INFERENCE (same
  results tradition per Table 8 row) plus the quantitative closure:
  own-model V_mode 0.65578 cm^3 x 0.625 = 0.40986 ~ the printed 0.409,
  i.e. own vs Booth-implied true V agrees to +0.21%;
- Booth-side WRITTEN CONFIRMATION PENDING (findings note drafted,
  docs/booth_vmode_findings_note.md; the discrimination ask against the
  numerically degenerate r <= x/2 truncation alias is the 225-degree
  recollection question).

Table 8 is internally consistent per row (printed Q / printed V
reproduces the printed Q/V column, all eight rows), so her Q/V values
inherit the same x1.6; the factor is uniform across the table and her
comparative conclusions survive intact. A maximum does not scale with
the revolved angle, and f/Q/wall-split are revolution-invariant ratios
— which is exactly why only the V_mode row (and F_m through it) failed
the 2026-07-10 §5a run."""


BOOTH_IMPLIED_V_MODE_M3: float = (
    TARGETS.booth.v_mode_m3 / BOOTH_TABLE8_REVOLUTION_FACTOR
)
"""Booth-implied TRUE (full-revolution) V_mode at her TE01delta point:
the Table 8 print corrected by BOOTH_TABLE8_REVOLUTION_FACTOR
(0.409e-6 / 0.625 = 6.544e-7 m^3). The print itself
(TARGETS.booth.v_mode_m3) is UNTOUCHED — provenance keeps prints as
printed; this is the derived comparison anchor the re-based
booth_two_point/v_mode window is built from (gate_targets.py, §11
item 8's reserved path: window-BASIS re-derivation from her actual
definition, never a tolerance widening). Inherits the revolution
factor's grade: anapole-.mph mechanism + uniform-workflow inference +
0.21% quantitative closure; Booth-side written confirmation PENDING.
Print precision: 0.409 is a 3-s.f. print, so the implied value carries
~±0.1% half-ULP — an order below the ±1% window."""


BOOTH_IMPLIED_F_M: float = (
    (3.0 / (2.0 * math.pi) ** 2)
    * (C_LIGHT / TARGETS.booth.f_hz) ** 3
    * TARGETS.booth.q_factor
    / BOOTH_IMPLIED_V_MODE_M3
)
"""Booth-implied F_m at her TE01delta point: the SPEC §3 magnetic
Purcell formula F_m = (3/(2 pi)^2) * lambda^3 * (Q/V) evaluated at the
printed Q = 6,980, the corrected BOOTH_IMPLIED_V_MODE_M3 and the
printed f = 1.45 GHz. ~7.16e6 — order 10^6.85: with the true V, NO
faithful model can satisfy the old [1e7, 1e8) order window at the
Booth point (it was only ever satisfiable through the x1.6-inflated
print, 0.409 => 1.15e7). The Booth-point F_m gate row is therefore a
±1% CONSISTENCY check against this anchor — a TIGHTENING of an
order-of-magnitude window to 1% — and the order-10^7 physics window
moves to the confinement endpoint where its Breeze anchor lives
(gate_targets.py). Inherits BOOTH_IMPLIED_V_MODE_M3's grade.

Fork guard: this inline arithmetic MUST equal
cavity.extraction.purcell.magnetic_purcell_factor(6980,
BOOTH_IMPLIED_V_MODE_M3, 1.45e9) — asserted in
tests/test_validation_gate.py (the inline form exists only because
provenance cannot import extraction without a cycle)."""
