"""Layer B calibration constants — Cowley-Semple 2026-07-14 rig and samples.

Single-source discipline exactly as `cavity/provenance/constants.py`: no
numeric value below may be duplicated elsewhere in `calibration/`; import
from this module. **EVERY entry is NON-TRANSFERABLE to the maser cavity
model** (SPEC §7.T5: rig ΔT numbers and rig parameters do not transfer
between geometries; the transport model and dν/dT do). Nothing here may
migrate to `cavity/provenance/constants.py`.

Primary source: the archived 2026-07-14 email from Angus Cowley-Semple
(calibration/data/raw/cowley_semple_2026-07-14/thermal.md; MANIFEST-pinned,
verified by `calibration.integrity` in CI). Grades used:

- COLLABORATOR-CONFIRMED — stated by Angus in the archived email.
- COLLABORATOR-SUGGESTED — offered by Angus as an assumption, not a
  measurement ("You could assume the spot size is 400 um?").
- FIGURE-STATED — read from an archived attachment (e.g. a spectra title).
- PLANNING-ASSUMPTION — ours, pending collaborator metadata.

Shared machinery imported, never copied: `K_PTP` (p-terphenyl k band),
`DF_SPIN_DT` (spin-arm coefficient), `H_CONV_AIR`, `EMISSIVITY_PTP`,
`GLASS_SLIDE` from `cavity.provenance.constants` — those grades live there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AmbientConditions:
    """COLLABORATOR-CONFIRMED (email, 2026-07-14). "The experiment is run at
    ambient condition. Temperature: 20 degrees Celsius." and "The experiment
    is in an enclosure so there shouldn't any drafts hitting the sample."

    The enclosure statement lands the §7.T4 convection reframe empirically
    for THIS rig: it sits at/below the bottom of the open-still-air
    `H_CONV_AIR` band (5–20 W m⁻² K⁻¹), which is why `ExposedFaceCoupling`
    pins h = 5 rather than the band midpoint. NON-TRANSFERABLE (the maser
    bore is a different enclosure class)."""

    t_inf_k: float = 293.15
    enclosed: bool = True


@dataclass(frozen=True)
class ExcitationSource:
    """COLLABORATOR-CONFIRMED (email, 2026-07-14): "15 mW 520nm pigtail
    laser" = Thorlabs LP520-SF15A — the diode of the Mena-2024 cw rig,
    settling the two-rig ambiguity (SPEC §11 item 5 ask 2) for THIS dataset.

    Per-trace powers are the graph-legend values (COLLABORATOR-CONFIRMED;
    digitization recovered them to <0.02 mW — CSV header validation line).

    **Power-measurement plane: UNKNOWN — open Angus ask.** The legend mW
    values are assumed to be optical power AT the sample (plausible under a
    15 mW pigtail with short delivery, and 14.39 mW < 15 mW); if they are
    diode-output instead, delivery losses fold into η_abs, so the ΔT/P fits
    are unchanged and only η_abs's interpretation moves (plan assumption 4,
    ratified with this cross-reference). NON-TRANSFERABLE."""

    wavelength_nm: float = 520.0
    part: str = "Thorlabs LP520-SF15A"
    max_power_mw: float = 15.0
    powers_d14_mw: tuple[float, ...] = (3.81, 6.06, 10.16, 14.39)
    powers_h14_mw: tuple[float, ...] = (3.81, 6.06, 8.05, 10.16, 12.33, 14.39)
    power_plane: str = "assumed-at-sample (measurement plane = open Angus ask)"


@dataclass(frozen=True)
class SpotGeometry:
    """COLLABORATOR-SUGGESTED (email, 2026-07-14): "You could assume the
    spot size is 400 um?" — an offered assumption, NOT a measurement.

    Model: TOP-HAT disc (fibre-core image at unit magnification — the
    multimode-pigtail image is flat-topped, NOT Gaussian; ratified plan T2),
    diameter swept 300–500 µm for defocus/magnification slack, deposited as
    a surface flux (the l_abs ≪ t headline branch; Beer-Lambert is the
    sensitivity variant). NON-TRANSFERABLE (maser pump is end-fire flood,
    different optic)."""

    diameter_m: float = 400e-6
    diameter_sweep_lo_m: float = 300e-6
    diameter_sweep_hi_m: float = 500e-6

    @property
    def radius_m(self) -> float:
        return self.diameter_m / 2.0


@dataclass(frozen=True)
class SampleLateralSize:
    """COLLABORATOR-CONFIRMED with stated difficulty (email, 2026-07-14):
    d14 "measured at 1.12mm", h14 "measured at 1.79mm" (caliper photos
    archived); "It's quite difficult to measure; I tried with the calipers."
    Shape: "somewhere between a square and a circle" — hence the
    `RadiusMapping` band below rather than a single disc radius.

    Reading assumption (plan assumption 2, flagged): the caliper value is a
    FACE WIDTH (across-flats), not a diagonal — the archived photos show the
    jaws across the crystal face. NON-TRANSFERABLE."""

    d14_lateral_m: float = 1.12e-3
    h14_lateral_m: float = 1.79e-3


@dataclass(frozen=True)
class RadiusMapping:
    """PLANNING-ASSUMPTION (invented, flagged — plan assumption 1). The
    crystals are "between a square and a circle"; the axisymmetric solver
    needs a disc radius. Point mapping: EQUAL-AREA square→disc,
    R = s/√π ≈ 0.5642·s. Band: inscribed (circle of the stated width,
    R = 0.5·s) to circumscribed (square's circumcircle, R = s/√2 ≈
    0.7071·s). Both samples share the mapping (same shape class), so the
    systematic partially cancels in the T4 ratio; it is swept anyway."""

    factor_point: float = 1.0 / math.sqrt(math.pi)
    factor_lo: float = 0.5
    factor_hi: float = 1.0 / math.sqrt(2.0)


@dataclass(frozen=True)
class CrystalThickness:
    """PLANNING-ASSUMPTION — the one geometry number the 2026-07-14 email
    does NOT give (per-sample thickness remains the top residual metadata
    gap; SPEC §11 item 5 ask 1). Bounded unknown 0.2–1.0 mm, per-sample
    INDEPENDENT: the published protonated plates are 0.5 mm, these
    deuterated crystals are visibly chunkier in the photos, and nothing
    pins either. Swept, never fixed. NON-TRANSFERABLE."""

    lo_m: float = 0.2e-3
    hi_m: float = 1.0e-3


@dataclass(frozen=True)
class UndersideCoupling:
    """PLANNING-ASSUMPTION — effective Robin coefficient h_sub on the
    crystal underside, lumping everything below it: the rubber-cement bond
    (Elmer's, per the email's link — k and bond-line thickness unsourced),
    the glass substrate, the HASL/Cu/FR-4 PCB, and the enclosure floor. The
    Cu plane is a near-isothermal spreader, which is what makes a single
    Robin-to-T_inf lump defensible; everything unknown about the glue is
    absorbed into the DECADE sweep 1e2–1e5 W m⁻² K⁻¹ (a 1-mm glass slide
    alone is ~1.1e3; a thin cement bond line pushes down toward 1e2; near-
    perfect contact up toward 1e5). Per-sample glue contact does NOT cancel
    in the T4 ratio — the documented residual confound. NON-TRANSFERABLE."""

    h_sub_lo_w_m2_k: float = 1e2
    h_sub_hi_w_m2_k: float = 1e5


@dataclass(frozen=True)
class ExposedFaceCoupling:
    """PLANNING-ASSUMPTION, collaborator-supported direction: h = 5
    W m⁻² K⁻¹ natural convection on all faces except the glued underside —
    the BOTTOM of the `H_CONV_AIR` open-still-air band, chosen because the
    rig is enclosed (AmbientConditions; the §7.T4 reframe says enclosures
    sit at/below the band floor).

    Radiation branch (ratified as FLAGGED BRANCH, not headline): the
    linearised h_rad from `EMISSIVITY_PTP` at 293 K is ~5 W m⁻² K⁻¹ —
    comparable to h_conv, so §7.T7 forbids assuming it small. The branch
    adds h_rad via `cavity.thermal.radiation.h_top_with_radiation` on
    exposed faces; the headline stays convection-only per ratified T2."""

    h_w_m2_k: float = 5.0


@dataclass(frozen=True)
class NominalConcentration:
    """Nominal pentacene doping of the two dataset samples.

    d14: COLLABORATOR-CONFIRMED — the email names "the 0.1% d14-pentacene:
    d14 PTP". h14: FIGURE-STATED (ratification upgrade, 2026-07-14) — the
    archived h14 spectra title reads "0.1% Pc:PTP"; the email text itself
    never restates h14's concentration.

    Zone-refining caveat rides both (Oxborrow-verbal 2026-07-06, graded in
    SPEC §6T): Bridgman growth incorporates BELOW nominal by an unknown,
    growth-specific factor, so equal nominals do not guarantee equal actual
    [Pc] — one reason η_abs sharing in T4 is an assumption with a stated
    condition, not a fact. NON-TRANSFERABLE (the maser crystal is 0.053%
    protonated)."""

    d14_nominal: float = 1e-3
    h14_nominal: float = 1e-3
    d14_grade: str = "collaborator-confirmed"
    h14_grade: str = "figure-stated (h14 spectra title '0.1% Pc:PTP')"


AMBIENT = AmbientConditions()
EXCITATION = ExcitationSource()
SPOT = SpotGeometry()
LATERAL = SampleLateralSize()
RADIUS_MAPPING = RadiusMapping()
THICKNESS = CrystalThickness()
UNDERSIDE = UndersideCoupling()
EXPOSED = ExposedFaceCoupling()
CONCENTRATION = NominalConcentration()

DIGITIZED_SIGMA_MHZ: float = 0.05
"""Per-point error floor of the digitized CSV (its header's stated error
model: ±0.05 MHz from the 0.1 MHz plot quantization). Kept here so the
slope-fit module and its tests share one literal; superseded together with
the CSV when raw trace data lands (superseded_by_raw_data=True)."""
