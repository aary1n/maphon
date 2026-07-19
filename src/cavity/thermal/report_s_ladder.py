"""SPEC 2026-07-16 outcome 5 — S-ladder ballpark report (2026-07-19).

Renders `thermal/reports/s_ladder_ballpark.md`: the scenario ladder
S0/S1/S4 on the maser-crystal cylinder (`cavity.thermal.cylinder` +
`side_deposition`), at BALLPARK tier, zero-licence — "think deep, not
about details. Ballpark estimates" (Oxborrow-VERBAL 2026-07-16,
late-recorded outcome 5; archived notes
calibration/data/raw/oxborrow_meeting_notes_2026-07-16/). Deterministic
output; pinned content-exact in tests/test_thermal_s_ladder.py (the
report_margin precedent).

Every number's source and rung, single-sourced from
`provenance/constants.py`:
- geometry: `CRYSTAL` planning dims (Breeze 2017; the Wu
  cross-build-transfer flag rides — five published indicators lean
  toward a ~4 mm bore-filling crystal, and the SM's pump path "<= 4 mm"
  vs the planning chord 2R = 3 mm sits inside the same flag);
- k axis: `K_PTP` band 0.1-1.0 W/m/K, geometric mid (floor-reading
  provenance; isotropic D6, the ~2x anisotropy stays folded in the band);
- l_abs axis: `L_ABS_PUMP` scoping grid (UNSOURCED-SCOPING — never an
  absolute-DT input) PLUS the optically-thin limit column (the Wu PRL SM's
  own bleached/optically-thin regime statement, Eq. S2->S3 — a regime
  reading, not a number);
- beam/prism: `WU_PUMP_BEAM` (PRL SM p. 1, LITERATURE, proof copy;
  uniform-over-ellipse intensity and the z_b = L/2 band-centre reading
  are that constant's recorded planning caveats);
- power axis: ABSORBED watts, a stated scoping grid — the solver is
  exactly linear in P. Steady-state reading STATED: no shot repetition
  rate is in print (searched), so no time-averaged CW power is derivable
  from Wu's per-shot energetics without a duty assumption.

Usage:  python -m cavity.thermal.report_s_ladder [--out thermal/reports]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from cavity.provenance.constants import CRYSTAL, K_PTP, L_ABS_PUMP, WU_PUMP_BEAM
from cavity.thermal.cylinder import CylinderSpec, PumpSource, SurfaceBC, solve
from cavity.thermal.layered import (
    Layer,
    delta_t_disk_center,
    delta_t_gaussian_volumetric,
)

PASS_DATE = "2026-07-19"

# The S4 systematic, carried VERBATIM into every S4 output (ratified
# scoping, 2026-07-19 plan checkpoint):
S4_SYSTEMATIC = (
    "In side-fire the heat source and the gain region are the same "
    "illuminated prism; the g^2-weighted observable samples exactly the "
    "hot spot, and the azimuthal smear dilutes it — the m = 0 result is "
    "a structural LOWER bracket on gain-weighted heating, not a neutral "
    "approximation."
)

R_M = CRYSTAL.diameter_m / 2.0
L_M = CRYSTAL.height_m
K_MID = K_PTP.k_mid_w_m_k
K_GRID = (K_PTP.k_band_lo_w_m_k, K_MID, K_PTP.k_band_hi_w_m_k)
P_GRID_W = (0.01, 0.1, 1.0)  # stated scoping grid, absorbed watts
L_ABS_AXIS = (*L_ABS_PUMP.l_abs_scoping_grid_m, math.inf)

H_B = WU_PUMP_BEAM.beam_height_m  # band height (major axis, vertical)
W_B = WU_PUMP_BEAM.beam_width_m  # chord width (minor axis, horizontal)
Z_B = L_M / 2.0  # band centre: the SM's equatorial reading (planning)
BAND = (Z_B - H_B / 2.0, Z_B + H_B / 2.0)
A_EQ = math.sqrt((H_B / 2.0) * (W_B / 2.0))  # equal-area disc radius

N_MODES_S1 = 256
N_MODES_S4 = 1024

_REPO_ROOT = Path(__file__).resolve().parents[3]


def g_s0_w_per_k(k: float) -> float:
    """S0 axial conductance, closed form: G = k·πR²/L."""
    return k * math.pi * R_M**2 / L_M


def s0_solver_deviation_k() -> float:
    """Max |solver − closed 1-D form| over a grid, per kelvin of drive —
    the ladder's analytic anchor, expected at machine precision (the
    Bi_s = 0 drive expansion is exactly the constant mode)."""
    spec = CylinderSpec(
        R_M,
        L_M,
        K_MID,
        SurfaceBC.robin(0.0),
        SurfaceBC.dirichlet(1.0),
        SurfaceBC.dirichlet(),
    )
    sol = solve(spec, n_modes=16)
    dev = 0.0
    for zf in np.linspace(0.0, 1.0, 9):
        for rf in (0.0, 0.5, 1.0):
            dev = max(
                dev, abs(float(sol.delta_t(rf * R_M, zf * L_M)) - (1.0 - zf))
            )
    return dev


def s1_field_ratios() -> dict[str, float]:
    """S1 per-kelvin field ratios (imposed hot top, cold sides+base)."""
    spec = CylinderSpec(
        R_M,
        L_M,
        K_MID,
        SurfaceBC.dirichlet(),
        SurfaceBC.dirichlet(1.0),
        SurfaceBC.dirichlet(),
    )
    sol = solve(spec, n_modes=N_MODES_S1)
    return {
        "centre_mid": float(sol.delta_t(0.0, L_M / 2.0)),
        "vol_avg": sol.volume_average_k(),
        "band_avg": sol.volume_average_k(z_lo_m=BAND[0], z_hi_m=BAND[1]),
    }


def s1b_per_watt(k: float) -> dict[str, float]:
    """S1b flux-conjugate companion (EXISTING machinery): top-face flood
    flux P = 1 W, cold side+base — per-watt ΔT plus the documented
    Dirichlet-side flood energy deficit at this N."""
    spec = CylinderSpec(
        R_M,
        L_M,
        k,
        SurfaceBC.dirichlet(),
        SurfaceBC.robin(0.0),
        SurfaceBC.dirichlet(),
    )
    sol = solve(spec, PumpSource(1.0, "surface", "flood"), n_modes=N_MODES_S4)
    bp = sol.boundary_power_w()
    return {
        "peak": sol.peak_k,
        "vol_avg": sol.volume_average_k(),
        "deficit": 1.0 - bp["total"],
    }


def s4_side_spec(k: float, side_dirichlet: bool) -> CylinderSpec:
    side = SurfaceBC.dirichlet() if side_dirichlet else SurfaceBC.robin(0.0)
    return CylinderSpec(
        R_M, L_M, k, side, SurfaceBC.dirichlet(), SurfaceBC.dirichlet()
    )


def s4_source(l_abs: float) -> PumpSource:
    return PumpSource(
        1.0,
        "band",
        "side_chord",
        l_abs_m=l_abs,
        band_lo_m=BAND[0],
        band_hi_m=BAND[1],
        beam_width_m=W_B,
    )


def s4_lower_cell(l_abs: float, side_dirichlet: bool) -> dict[str, float]:
    """m = 0 lower-bracket observables per absorbed watt at k_mid."""
    sol = solve(
        s4_side_spec(K_MID, side_dirichlet), s4_source(l_abs), n_modes=N_MODES_S4
    )
    r_grid = np.linspace(0.0, R_M, 481)
    eq = sol.delta_t(r_grid, Z_B)
    bp = sol.boundary_power_w()
    return {
        "peak_eq": float(np.max(eq)),
        "band_avg": sol.volume_average_k(z_lo_m=BAND[0], z_hi_m=BAND[1]),
        "vol_avg": sol.volume_average_k(),
        "deficit": abs(1.0 - bp["total"]),
        "tail": sol.tail_estimate_rel("volume_average"),
    }


def upper_disc_center_k_per_w(k: float, thickness_m: float) -> float:
    """Spot upper member, surface branch: uniform-flux equal-area disc on
    a single-layer slab grounded at the far face (`layered.py`, EXISTING
    3a-adjacent machinery)."""
    return delta_t_disk_center([Layer(thickness_m, k)], 1.0, A_EQ)


def upper_volumetric_k_per_w(k: float, thickness_m: float, l_abs: float) -> float:
    """Spot upper member, buried branch: Gaussian spot (w = a_eq stated as
    the equal-area equivalence), truncated-renormalised Beer-Lambert in
    depth (`layered.py`)."""
    return float(
        delta_t_gaussian_volumetric(0.0, [Layer(thickness_m, k)], 1.0, A_EQ, l_abs)
    )


def _fmt_l(l_abs: float) -> str:
    return "inf (thin)" if math.isinf(l_abs) else f"{l_abs*1e6:.0f} um"


def build_report() -> str:
    dev = s0_solver_deviation_k()
    g_rows = [
        f"| {k:.4g} | {g_s0_w_per_k(k):.4e} | "
        + " | ".join(f"{p / g_s0_w_per_k(k):.3g}" for p in P_GRID_W)
        + " |"
        for k in K_GRID
    ]
    s1 = s1_field_ratios()
    s1b = s1b_per_watt(K_MID)
    lower_rows = []
    max_def_ins = 0.0
    max_def_dir = 0.0
    max_tail = 0.0
    for l_abs in L_ABS_AXIS:
        ins = s4_lower_cell(l_abs, side_dirichlet=False)
        dir_ = s4_lower_cell(l_abs, side_dirichlet=True)
        max_def_ins = max(max_def_ins, ins["deficit"])
        max_def_dir = max(max_def_dir, dir_["deficit"])
        max_tail = max(max_tail, ins["tail"], dir_["tail"])
        lower_rows.append(
            f"| {_fmt_l(l_abs)} | {ins['peak_eq']:.1f} | {ins['band_avg']:.1f} "
            f"| {ins['vol_avg']:.1f} | {dir_['peak_eq']:.1f} "
            f"| {dir_['band_avg']:.1f} |"
        )
    disc_slab = upper_disc_center_k_per_w(K_MID, 2.0 * R_M)
    half_space_disc = 1.0 / (math.pi * A_EQ * K_MID)
    half_space_gauss = 1.0 / (math.sqrt(2.0 * math.pi) * A_EQ * K_MID)
    upper_rows = [
        f"| {_fmt_l(l_abs)} | "
        f"{upper_volumetric_k_per_w(K_MID, 2.0 * R_M, l_abs):.0f} |"
        for l_abs in L_ABS_PUMP.l_abs_scoping_grid_m
    ]
    lines = [
        f"# SPEC 2026-07-16 outcome 5 — S-ladder ballpark report ({PASS_DATE})",
        "",
        "**Status: BALLPARK-tier scenario ladder — NOT device predictions.**",
        "Regenerate with `python -m cavity.thermal.report_s_ladder`; pinned",
        "content-exact in tests/test_thermal_s_ladder.py.",
        "",
        "## Status notes",
        "",
        "- Authority: SPEC 2026-07-16 meeting block outcome 5 (late-recorded"
        " 2026-07-19), Oxborrow-VERBAL — \"think deep, not about details."
        " Ballpark estimates.\" Zero-licence: no COMSOL anywhere in this"
        " block.",
        "- Modelled body: the HOMOGENEOUS crystal cylinder at planning dims"
        f" (`CRYSTAL`, Breeze 2017: R = {R_M*1e3:.2g} mm, L = {L_M*1e3:.2g}"
        " mm), cross-build-transfer flag riding (five published Wu-side"
        " indicators lean ~4 mm bore-filling; the SM pump path \"<= 4 mm\""
        " vs the planning chord 2R = 3 mm rides the same flag). Composite"
        " crystal+STO+spacer bodies are ABOVE ballpark tier — out of scope,"
        " recorded.",
        "- Steady-state reading, STATED: all numbers are steady-state ΔT for"
        " a continuously-ABSORBED power P; the solver is exactly linear in"
        " P, so every cell rescales exactly. Wu per-shot energetics are"
        " context only: 2.4 J/shot over three 150 us pulses at 500 us"
        " intervals (PRL SM; ~5.3 kW instantaneous incident during pulses ="
        " 2.4 J / 450 us), single-pulse example ~300 us / 250 mJ (PRL Fig."
        " 2). NO SHOT REPETITION RATE IS IN PRINT — no time-averaged CW"
        " power is derivable from the published record without a duty"
        " assumption, so the power axis below is a stated scoping grid, not"
        " a Wu-derived operating point. Pulse-train transients are out of"
        " ladder scope (steady solver, no heat capacity; rho is the one"
        " open §6T pull — SPEC §11 item 7).",
        "- k axis: `K_PTP` band [0.1, 1.0] W/m/K, geometric mid"
        f" {K_MID:.4g} (floor-reading provenance; isotropic D6, ~2x"
        " anisotropy folded in the band, not swept). All ladder BCs are"
        " Dirichlet/insulated, so source-driven ΔT scales EXACTLY as 1/k"
        " and drive-driven field RATIOS are k-independent — band-edge"
        " values are exact arithmetic on the k_mid tables"
        " (x3.162 at the 0.1 floor, x0.3162 at 1.0).",
        "- l_abs axis: `L_ABS_PUMP` scoping grid"
        " {5, 10, 20, 50, 100, 200} um — UNSOURCED-SCOPING, never an"
        " absolute-DT input — PLUS the optically-thin limit (l_abs = inf):"
        " the Wu SM's own bleached/optically-thin regime statement"
        " (Eq. S2->S3). The two ends carry different physics readings: the"
        " um grid = unbleached small-signal penetration scoping; the inf"
        " column = the Wu operating-regime reading. Bleaching is"
        " intensity-dependent; the ladder stays linear-in-P, so l_abs is a"
        " swept PARAMETER, never a computed function of P.",
        "- Beam/prism: `WU_PUMP_BEAM` (PRL SM p. 1, LITERATURE, proof copy):"
        f" band height h_b = {H_B*1e3:.2g} mm (major axis, vertical), chord"
        f" width w_b = {W_B*1e3:.2g} mm (minor axis); band centre z_b = L/2"
        " (the SM's \"half way up the inner cylindrical wall\" read onto"
        " the planning crystal — crystal axial placement itself Q9-open)."
        " Uniform-over-ellipse intensity is that constant's recorded"
        " planning assumption.",
        "- Band averages are UNWEIGHTED sub-cylinder averages"
        " (`volume_average_k` over the band window) — the gain-region"
        " H-weighting of §7.T2 stays the consumer's job (module doctrine);"
        " the band average is the stated stand-in at ballpark tier.",
        "",
        f"## S0 — 1D anchor (insulated sides, imposed T_top/T_base)",
        "",
        "The exact branch: with Bi_s = 0 the imposed-constant drive expands"
        " into the constant mode ONLY (J1 vanishes at its own zeros), so the"
        " solver reproduces the closed 1-D form ΔT = ΔT_hot·(1 − z/L) with"
        " zero truncation error.",
        "",
        f"- Analytic cross-check, computed this pass: max |solver − closed"
        f" form| = {dev:.2e} K per K of drive (machine precision; asserted"
        " in CI).",
        "- Conductance G_S0 = k·πR²/L, and the implied hot-face rise"
        " ΔT_hot = P/G_S0 at the power grid:",
        "",
        "| k (W/m/K) | G_S0 (W/K) | ΔT_hot @ 10 mW (K) | @ 100 mW (K) |"
        " @ 1 W (K) |",
        "|---|---|---|---|---|",
        *g_rows,
        "",
        "At the band mid-point, ~10 mW of conducted power already implies a"
        f" ~{0.01/g_s0_w_per_k(K_MID):.0f} K axial contrast — the meeting's"
        " \"20-50 K likely buoyancy-enhanced\" class (`H_CONV_AIR` append,"
        " 2026-07-16) is reached at tens of mW, not watts.",
        "",
        "## S1 — 3D end-fired (hot imposed top; cold imposed sides+bottom)",
        "",
        "BC configuration, not a source extension (blown-air imposed-T"
        " limit: forced air fast enough that the outer crust sits at air"
        " temperature — archived notes). Field ratios per kelvin of top"
        f" drive (k-independent; N = {N_MODES_S1}):",
        "",
        f"- ΔT(0, L/2)/ΔT_hot = {s1['centre_mid']:.4f}",
        f"- volume average /ΔT_hot = {s1['vol_avg']:.4f}",
        f"- band-window average /ΔT_hot = {s1['band_avg']:.4f}"
        f" (z in [{BAND[0]*1e3:.0f}, {BAND[1]*1e3:.0f}] mm)",
        "",
        "Sharp-corner caveat, stated in advance: the imposed-T idealisation"
        " is discontinuous along the top rim, so the TOTAL top inflow is"
        " log-divergent — the classic mixed-boundary edge singularity."
        " Normalisation, dimensional (module Λ = (L/R)·sqrt(k_r/k_z), not"
        " its reciprocal): per mode |p_top,n| ≈ 4πR·sqrt(k_r·k_z)·ΔT_hot/xₙ"
        " W, so each mode-doubling adds ≈ 4·R·sqrt(k_r·k_z)·ΔT_hot·ln 2 W,"
        " approached from below at finite N — absolutely pinned in CI. A"
        " total conductance is NOT a well-posed observable of sharp S1;"
        " power coupling rides S0's exact G or the S1b flux conjugate"
        " below. Interior/integrated observables converge and are what S1"
        " reports.",
        "",
        "Cold-bottom realisability rider (SPEC outcome 5): the as-built"
        " seat is INSULATING cross-linked polystyrene with no paste"
        " (Oxborrow-WRITTEN 2026-07-17 supersession) — an imposed-cold"
        " BOTTOM is a blown-air/forced-contact idealisation, not the"
        " current build's seat.",
        "",
        "### S1b — flux-conjugate companion (existing machinery)",
        "",
        "Top-face flood deposition of absorbed power P, cold side+base —"
        " the \"certain mW absorbed in the top few hundred microns; where"
        " does the heat flow\" reading of the archived notes. Per absorbed"
        f" watt at k_mid = {K_MID:.4g} (exact 1/k band scaling;"
        f" N = {N_MODES_S4}, Dirichlet-side flood energy deficit"
        f" {s1b['deficit']*100:.2f}% — the documented ~1/N class):",
        "",
        f"- peak (top-face centre) = {s1b['peak']:.0f} K/W"
        f" -> {s1b['peak']*0.01:.1f} K @ 10 mW",
        f"- volume average = {s1b['vol_avg']:.0f} K/W"
        f" -> {s1b['vol_avg']*0.01:.1f} K @ 10 mW",
        "",
        "## S4 — side-fired, extension (A): azimuthally-smeared m = 0",
        "",
        f"> {S4_SYSTEMATIC}",
        "",
        "Stakes (carried): the Wu build itself is SIDE-FIRED — PRL SM: pump"
        " through the 3-mm hole in the copper wall, illuminated prism"
        " across the bore at the equator — so S4 is the pump geometry of"
        " the modelled build and carries future validation weight, not"
        " ladder-completeness only.",
        "",
        "Deposition: Beer-Lambert along horizontal chords, azimuthally"
        " averaged (m = 0), times a uniform axial band at beam height"
        " (NOT exponential-from-top); truncated-renormalised so P ="
        " absorbed power exactly (D4-consistent). BCs: cold imposed top"
        " and base (outcome 5 \"cooled top and bottom\"); side INSULATED"
        " as the headline (conservative-hot) with the side-Dirichlet"
        " maximal-side-cooling column bounding the unmodelled crystal->STO"
        " side path (D7).",
        "",
        f"### Lower bracket — m = 0 smear, per absorbed watt at k_mid"
        f" (N = {N_MODES_S4})",
        "",
        "| l_abs | peak@equator (K/W) | band avg (K/W) | vol avg (K/W) |"
        " peak@eq, side-cold | band avg, side-cold |",
        "|---|---|---|---|---|---|",
        *lower_rows,
        "",
        "Convergence bookkeeping (no silent cap): insulated-side columns —"
        f" max energy deficit {max_def_ins:.1e} (the constant mode carries"
        " the deposited power EXACTLY under an insulated side); side-cold"
        f" columns — max deficit {max_def_dir:.1e}, at the sharpest l_abs,"
        " scaling ~(R/x_max)/l_abs: power deposited inside the unresolved"
        " ~R/x_max sliver at the cold wall exits without registering in"
        " the truncated basis. The bounding COLUMN's reading (maximal side"
        " cooling => near-cold interior) is unaffected in kind; its values"
        " understate interior ΔT by at most that class. Max 3-mode tail"
        f" {max_tail:.1e} across all cells.",
        "",
        "### Upper bracket — spot estimate (3a-adjacent `layered.py`"
        " machinery)",
        "",
        "The illuminated entry patch on a single-layer slab of thickness"
        f" 2R = {2*R_M*1e3:.2g} mm grounded cold at the far face, patch"
        f" scale a_eq = sqrt((h_b/2)(w_b/2)) = {A_EQ*1e3:.3f} mm"
        " (equal-area equivalence). Assumptions at planning rung: planar"
        " slab vs curved wall; ALL absorbed P through one patch"
        " (single-sided — the azimuthal smear is absent, which is exactly"
        " what makes it an upper member); adiabatic elsewhere. Two patch"
        " SHAPES are carried — they are not interchangeable (a Gaussian of"
        " 1/e² radius a_eq concentrates more power on-axis than a uniform"
        " disc of radius a_eq, so its centre rise is higher); for a FIXED"
        " shape, burial only lowers the peak, so each shape's surface"
        " limit upper-bounds its buried variants:",
        "",
        f"- Uniform-disc surface member (`delta_t_disk_center`):"
        f" {disc_slab:.0f} K/W -> {disc_slab*0.01:.0f} K @ 10 mW at k_mid"
        " (exact 1/k scaling). Half-space closed-form anchor"
        f" P/(π·a_eq·k) = {half_space_disc:.0f} K/W — the slab value sits"
        " below it (the cold far face only removes resistance; asserted"
        " in CI).",
        "- Gaussian buried member (`delta_t_gaussian_volumetric`,"
        " w = a_eq), per absorbed watt at k_mid — monotone-decreasing"
        " with burial depth, bounded by the half-space Gaussian surface"
        f" closed form P/(sqrt(2π)·a_eq·k) = {half_space_gauss:.0f} K/W:",
        "",
        "| l_abs | ΔT_peak (K/W) |",
        "|---|---|",
        *upper_rows,
        "",
        "For l_abs = inf (bleached), burial along the chord only lowers"
        " the peak further: the surface limits above remain the bound.",
        "",
        "### Bracket reading",
        "",
        "The true gain-weighted heating lies BETWEEN the m = 0 lower"
        " bracket and the spot upper bracket — a structural bracket pair,"
        " not an error bar. The smear dilutes the prism over 2π azimuth"
        " (lower); the spot concentrates all P at one patch (upper). The"
        " upper bracket at each l_abs is the LARGER of the two members"
        " (they cross near the top of the scoping grid); asserted above"
        " the lower bracket's insulated-side peak in CI, per l_abs.",
        "",
        "m > 0 azimuthal harmonics: DEFERRED (logged; same discipline as"
        " the eccentricity route — averaged main result now, bounded"
        " side-study + decision gate before heavier machinery). Recorded"
        " here and beside D2 in `cavity.thermal.cylinder`.",
        "",
        "## S2 / S3 / S5",
        "",
        "- S2: no such rung appears anywhere in the notes (the numbering"
        " gap is part of the S3/S4 numbering ask).",
        "- S3: label RESERVED — bare heading in the archived notes, content"
        " not captured; numbering (typed S4-for-side-fire vs sketch S3)"
        " rides the Oxborrow Email B ask. Nothing planned, nothing"
        " computed.",
        "- S5: logged-DEFERRED (SPEC outcome 5) — the \"steam engine\""
        " coolant-channel brainstorm; out of scope (§9 cooling-channel"
        " exclusion). Nothing computed.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(_REPO_ROOT / "thermal" / "reports"),
        help="output directory (default: thermal/reports at repo root)",
    )
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "s_ladder_ballpark.md"
    out_path.write_text(build_report(), encoding="utf-8", newline="\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
