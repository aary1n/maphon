"""SPEC §7.T4 — Voigt/multi-packet sensitivity report (2026-07-20).

Renders `thermal/reports/q_margin_voigt_sensitivity.md`: the exact-FWHM
(f_L -> margin, exponent) sensitivity map of the two-linewidth planning
margin under the multi-packet threshold
(`cavity.thermal.ensemble_threshold`), under BOTH G^2 normalisations,
with the E = 0 sign contour and the handoff-scenario reproduction.
Deterministic output (fixed pass date, fixed formatting) byte-pinned in
`tests/test_thermal_ensemble_threshold.py` — the report_margin
precedent, text-only.

Inputs are single-sourced: PLANNING_C0 / own_model_point from
`report_margin` (ratified amendment B: one kappa_c, one f), kappa_s
from `KAPPA_S`. No fresh physics literals.

Usage:  python -m cavity.thermal.report_voigt [--out thermal/reports]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from cavity.provenance.constants import KAPPA_S, TARGET
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.detuning import (
    Q_MARGIN_RUNG,
    delta_f_max_hz,
    q_loaded,
    q_margin_exponent,
)
from cavity.thermal.ensemble_threshold import (
    g2_fixed_import_preserving,
    make_voigt_s_spin,
    margin_fixed_g2,
    margin_onres_ratio,
    q_margin_exponent_numeric,
    threshold_g2,
    voigt_sigma_g_mhz,
)
from cavity.thermal.report_margin import (
    PLANNING_C0,
    REJUDGE_RUN_DIR,
    own_model_point,
)

PASS_DATE = "2026-07-20"

# The audited decomposition grid: homogeneous packet FWHM f_L (cyclic
# MHz); f_L = 1.40 is the pure-Lorentzian repo branch (sigma_g = 0).
SWEEP_F_L_MHZ = (0.05, 0.10, 0.20, 0.35, 0.50, 0.70, 1.00, 1.20, 1.40)

_EXPONENT_H_LOG = 0.02
_CONTOUR_HALF_WIDTH_MHZ = 1e-4

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _branch_label(root) -> str:
    """Root-branch record for a table row: selected/total, '!' when the
    tangential/merger guard produced any candidate."""
    flag = "!" if root.tangential_candidates else ""
    return f"{root.selected_index + 1}/{root.n_candidates}{flag}"


def _exponent_for(anchoring: str, f_l: float, kappa_c: float, g2_imp: float):
    sigma = voigt_sigma_g_mhz(f_l, KAPPA_S.kappa_s_hz / 1e6)
    s_v = make_voigt_s_spin(f_l, sigma)
    if anchoring == "fixed":
        g2 = g2_imp
    else:
        g2 = PLANNING_C0 * threshold_g2(0.0, kappa_c, s_v).g2_th
    return q_margin_exponent_numeric(
        g2, kappa_c, s_v, h_log=_EXPONENT_H_LOG
    ).exponent


def _bisect_e_zero(
    anchoring: str,
    lo: float,
    hi: float,
    e_lo: float,
    e_hi: float,
    kappa_c: float,
    g2_imp: float,
) -> tuple[float, float]:
    """Bisect one E sign change on [lo, hi] to half-width
    _CONTOUR_HALF_WIDTH_MHZ; returns the final bracket."""
    assert e_lo * e_hi < 0.0
    while hi - lo > 2.0 * _CONTOUR_HALF_WIDTH_MHZ:
        mid = 0.5 * (lo + hi)
        e_mid = _exponent_for(anchoring, mid, kappa_c, g2_imp)
        if e_mid == 0.0:
            return (mid, mid)
        if (e_mid < 0.0) == (e_lo < 0.0):
            lo, e_lo = mid, e_mid
        else:
            hi, e_hi = mid, e_mid
    return (lo, hi)


def build_report() -> str:
    """The full markdown report as a deterministic string."""
    f_hz = TARGET.f_design_hz
    own = own_model_point()
    q0 = own["q0_canonical"]
    q_l = q_loaded(q0)
    kappa_c = resonance_linewidth_hz(f_hz, q_l) / 1e6  # cyclic MHz FWHM
    kappa_s = KAPPA_S.kappa_s_hz / 1e6
    g2_imp = g2_fixed_import_preserving(PLANNING_C0, kappa_c, kappa_s)
    committed_mhz = (
        delta_f_max_hz(PLANNING_C0, kappa_c * 1e6, kappa_s * 1e6) / 1e6
    )
    committed_exponent = q_margin_exponent(
        PLANNING_C0, kappa_c * 1e6, kappa_s * 1e6
    )
    half_widths = math.sqrt(PLANNING_C0 - 1.0)

    # --- sweep under both normalisations ---
    rows: dict[float, dict] = {}
    for f_l in SWEEP_F_L_MHZ:
        sigma = voigt_sigma_g_mhz(f_l, kappa_s)
        s_v = make_voigt_s_spin(f_l, sigma)
        m_fixed = margin_fixed_g2(g2_imp, kappa_c, s_v)
        e_fixed = q_margin_exponent_numeric(
            g2_imp, kappa_c, s_v, h_log=_EXPONENT_H_LOG
        ).exponent
        m_ratio = margin_onres_ratio(PLANNING_C0, kappa_c, s_v)
        e_ratio = q_margin_exponent_numeric(
            m_ratio.g2, kappa_c, s_v, h_log=_EXPONENT_H_LOG
        ).exponent
        rows[f_l] = {
            "sigma": sigma,
            "fixed": (m_fixed, e_fixed),
            "ratio": (m_ratio, e_ratio),
        }

    def sweep_table(anchoring: str) -> list[str]:
        lines = [
            "| f_L (MHz) | sigma_g (MHz) | Δf_max (MHz) | vs committed "
            "| omega_root (MHz) | root branch | E (h = 0.02) |",
            "|---|---|---|---|---|---|---|",
        ]
        for f_l in SWEEP_F_L_MHZ:
            margin, exponent = rows[f_l][anchoring]
            rel = (margin.delta_f_max_mhz / committed_mhz - 1.0) * 100.0
            if abs(rel) < 0.05:  # avoid the float "-0.0%" artifact
                rel = 0.0
            lines.append(
                f"| {f_l:.2f} | {rows[f_l]['sigma']:.6f} | "
                f"{margin.delta_f_max_mhz:.4f} | {rel:+.1f}% | "
                f"{margin.root.omega_mhz:.4f} | "
                f"{_branch_label(margin.root)} | {exponent:+.4f} |"
            )
        return lines

    def minimum_row(anchoring: str) -> tuple[float, float]:
        f_min = min(
            SWEEP_F_L_MHZ,
            key=lambda f_l: rows[f_l][anchoring][0].delta_f_max_mhz,
        )
        return f_min, rows[f_min][anchoring][0].delta_f_max_mhz

    # --- E = 0 sign contour, per normalisation (computed, not assumed) ---
    contour_lines = []
    for anchoring, label in (
        ("fixed", "import-preserving fixed-G^2"),
        ("ratio", "on-res ratio"),
    ):
        exponents = [rows[f_l][anchoring][1] for f_l in SWEEP_F_L_MHZ]
        crossings = []
        for i in range(len(SWEEP_F_L_MHZ) - 1):
            if exponents[i] * exponents[i + 1] < 0.0:
                lo, hi = _bisect_e_zero(
                    anchoring,
                    SWEEP_F_L_MHZ[i],
                    SWEEP_F_L_MHZ[i + 1],
                    exponents[i],
                    exponents[i + 1],
                    kappa_c,
                    g2_imp,
                )
                crossings.append(0.5 * (lo + hi))
        if crossings:
            text = ", ".join(
                f"f_L* = {c:.4f} MHz (bisected to ±{_CONTOUR_HALF_WIDTH_MHZ:g} MHz)"
                for c in crossings
            )
            contour_lines.append(f"- {label}: {text}.")
        else:
            contour_lines.append(
                f"- {label}: no E = 0 crossing in the swept range "
                f"[{SWEEP_F_L_MHZ[0]:.2f}, {SWEEP_F_L_MHZ[-1]:.2f}] MHz "
                "— the numbers show none; none is assumed."
            )

    # --- handoff-scenario reproduction (their formulation, this solver) ---
    kc_handoff = 0.257  # their rounded kappa_c, verbatim
    s_a = make_voigt_s_spin(1.40, 0.0)
    s_b = make_voigt_s_spin(0.10, 1.39 / 2.35482)  # their O-L sizing
    s_c = make_voigt_s_spin(0.50, 1.00 / 2.35482)
    m_a = margin_onres_ratio(190.0, kc_handoff, s_a).delta_f_max_mhz
    m_b = margin_onres_ratio(190.0, kc_handoff, s_b).delta_f_max_mhz
    m_c = margin_onres_ratio(190.0, kc_handoff, s_c).delta_f_max_mhz
    eps = 0.05

    def their_exponent(s_spin) -> float:
        margins = [
            margin_onres_ratio(
                190.0 * (1.0 + e), kc_handoff / (1.0 + e), s_spin
            ).delta_f_max_mhz
            for e in (-eps, +eps)
        ]
        return (math.log(margins[1]) - math.log(margins[0])) / (
            2.0 * math.log(1.0 + eps)
        )

    e_a_theirs = their_exponent(s_a)
    e_b_theirs = their_exponent(s_b)

    fixed_at_010 = rows[0.10]["fixed"][0].delta_f_max_mhz
    ratio_at_010 = rows[0.10]["ratio"][0].delta_f_max_mhz
    f_min_fixed, m_min_fixed = minimum_row("fixed")
    f_min_ratio, m_min_ratio = minimum_row("ratio")

    lines = [
        f"# SPEC §7.T4 — Voigt/multi-packet sensitivity of the "
        f"two-linewidth margin ({PASS_DATE})",
        "",
        "**Status: sensitivity AUDIT of the committed law's "
        "single-packet mapping — NOT a claim, NOT a kappa_s re-grade, "
        "and NOT a resolution of the open D4 decomposition.** "
        "Regenerate with `python -m cavity.thermal.report_voigt`; "
        "pinned byte-for-byte in "
        "`tests/test_thermal_ensemble_threshold.py` (anchors V1-V10).",
        "",
        "## Status notes",
        "",
        f"- {Q_MARGIN_RUNG}.",
        "- WHAT THIS AUDITS: the committed margin law maps the measured "
        "composite ODMR FWHM (kappa_s = 1.4 MHz) onto ONE homogeneous "
        "Lorentzian packet — a threshold-MODEL assumption (`KAPPA_S` "
        "caveat; SPEC §6T/§7.T4). The hom/inhom decomposition of that "
        "composite is UNKNOWN (the open D4 conjunction, "
        "`docs/plans/cowley_semple_reply_ingestion_and_calibration_"
        "rebase.md`). Every f_L row below is a SCENARIO PROBE across "
        "that unknown, exactly sized so the composite Voigt FWHM "
        "equals 1.400 MHz — none is a calibrated decomposition of the "
        "real line.",
        "- MODEL ASSUMPTIONS (multi-packet threshold, "
        "`cavity.thermal.ensemble_threshold`): class-A / quasi-static "
        "clamped inversion; packet weights = the inversion- and "
        "coupling^2-weighted distribution of packet CENTRES — under "
        "the uniform-inversion/uniform-coupling assumption adopted "
        "here, the Gaussian centre distribution itself (std sigma_g). "
        "The composite Voigt line is the RESULTING susceptibility "
        "(Re S_spin = pi x the area-normalised composite profile), "
        "NOT itself the weight distribution. Common homogeneous width "
        "across packets; free-running oscillator ruling; STATIC "
        "kappa_s (no kappa_s(ΔT) feedback); single cavity mode.",
        "- NORMALISATION CONVENTIONS — both computed, every number "
        "labelled: PRIMARY = the REPO-CONSISTENT IMPORT-PRESERVING "
        "FIXED-G^2 anchoring (ratified amendment C, "
        "`report_margin.py` C0-import convention): G^2 = "
        "C0·kappa_c·kappa_s_composite/4 with C0 = 190 imported, held "
        "fixed across line shapes and Q perturbations — this G^2 is "
        "an ALGEBRAIC IMPORT CONVENTION, not an independently "
        "measured or microscopically grounded coupling. SECONDARY = "
        "the on-resonance threshold ratio G^2_th(Δ)/G^2_th(0) = C0 — "
        "the handoff's convention; it anchors to the line PEAK "
        "rather than the composite FWHM, so it parts from the primary "
        "on every non-Lorentzian row (identical on the sigma_g = 0 "
        "branch).",
        f"- FAR-WING CAVEAT: at C0 = {PLANNING_C0:g} the margin sits "
        f"sqrt(C0−1) ≈ {half_widths:.2f} combined half-widths from "
        "line centre. ALL rows — including the committed pure-"
        "Lorentzian row — carry the margin on far LORENTZIAN packet "
        "tails (Re S_spin → a_s/omega^2 there; verified V6). No "
        "measurement in hand constrains the real line 10+ widths out; "
        "the entire table inherits that assumption.",
        "- ROOT-BRANCH RECORDING: thresholds are min-over-roots of "
        "Im S = 0 with Re S > 0; the scan guards tangential/merger "
        "roots and each table row records the selected root "
        "(omega_root, selected/total, '!' if any tangential candidate "
        "was involved) so branch switches are visible. Every row "
        "below sits on a single clean branch (1/1).",
        "- HANDOFF PROVENANCE: the audited hypotheses come from the "
        "UNTRUSTED session record "
        "`docs/reviews/two_linewidth_falsification_handoff.md` "
        "(out-of-repo sandbox numerics, preserved unedited). Its "
        "operating-point margins used the SECONDARY normalisation and "
        "Olivero-Longbothum approximate sizing (composite ≈ 1.44 / "
        "1.29 MHz, not 1.400); reproduction below is under ITS "
        "formulation, labelled. Its packet weighting (Gaussian centre "
        "distribution) matches this module's — no weighting "
        "difference to label.",
        "- FINDINGS-NOTE IMPLICATION — RECOMMENDATION ONLY, no edit "
        "made: the unratified findings-note headline (higher-Q builds "
        "have MORE thermal margin, E ≈ +0.35) is CONDITIONAL on the "
        "Lorentzian-composite branch of the D4 unknown. On "
        "inhomogeneity-dominated decompositions the exponent sign "
        "inverts under BOTH normalisations (table below; sign contour "
        "f_L* ≈ 0.26 MHz). The note should carry this as an explicit "
        "conditionality before any headline use; deciding that edit "
        "is Oxborrow-routed, not this pass's.",
        "",
        "## Parameters",
        "",
        f"- f = {f_hz / 1e9:.2f} GHz (`TARGET.f_design_hz`); Q0 = "
        f"{q0:.4f} (own-model canonical, re-based §5a record "
        f"`refs/gate_runs/{REJUDGE_RUN_DIR}/`) → Q_L = {q_l:.2f}; "
        f"kappa_c = f/Q_L = {kappa_c:.6f} MHz — CYCLIC-Hz FWHM, "
        "never angular (provenance-table trap 1).",
        f"- kappa_s composite = {kappa_s:.3f} MHz (`KAPPA_S`, 0.1% "
        "d14 branch choice; band "
        f"[{KAPPA_S.kappa_s_band_lo_hz / 1e6:.3f}, "
        f"{KAPPA_S.kappa_s_band_hi_hz / 1e6:.3f}] MHz NOT swept here "
        "— this audit varies the decomposition at fixed composite).",
        f"- C0 = {PLANNING_C0:g} (SPEC revision-note planning import, "
        "`PLANNING_C0`); primary anchoring G^2 = "
        f"C0·kappa_c·kappa_s/4 = {g2_imp:.6f} (matched-unit amplitude-"
        "rate^2, MHz^2).",
        f"- Committed single-packet reference: Δf_max = "
        f"{committed_mhz:.4f} MHz, E = {committed_exponent:+.4f} "
        "(`delta_f_max_hz`, `q_margin_exponent`).",
        "- Units: matched cyclic-MHz-FWHM (amplitude rates = FWHM/2; "
        "exact by degree-1 homogeneity). Exponents: fixed-G^2 "
        "log-symmetric central difference, Q·e^{±h}, h = "
        f"{_EXPONENT_H_LOG:g} (Lorentzian control reproduces the "
        "analytic exponent to ≤ 1e-4 relative — anchor V7).",
        "",
        "## Exact-FWHM sweep — PRIMARY: repo-consistent "
        "import-preserving fixed-G^2",
        "",
        *sweep_table("fixed"),
        "",
        f"Sweep-grid minimum: Δf_max = {m_min_fixed:.4f} MHz at f_L = "
        f"{f_min_fixed:.2f} ({(m_min_fixed / committed_mhz - 1.0) * 100.0:+.1f}% "
        "vs the committed row). The committed +0.35 exponent survives "
        "only on the f_L ≳ 0.26 MHz side of the contour below.",
        "",
        "## Exact-FWHM sweep — SECONDARY: on-resonance threshold "
        "ratio (handoff convention)",
        "",
        *sweep_table("ratio"),
        "",
        f"Sweep-grid minimum: Δf_max = {m_min_ratio:.4f} MHz at f_L = "
        f"{f_min_ratio:.2f} ({(m_min_ratio / committed_mhz - 1.0) * 100.0:+.1f}% "
        "vs the committed row).",
        "",
        "## E = 0 sign contour (assessed per normalisation)",
        "",
        *contour_lines,
        "",
        "## Handoff-scenario reproduction (their formulation, this "
        "solver)",
        "",
        "Their kc = 0.257 MHz (rounded), their sizing (sigma_g = "
        "1.39/2.35482 and 1.00/2.35482 — composite ≈ 1.44/1.29 MHz), "
        "on-res-ratio normalisation, and their asymmetric eps = 0.05 "
        "exponent formula:",
        "",
        "| scenario | this pass | handoff §6 |",
        "|---|---|---|",
        f"| (a) Lorentzian 1.40 margin | {m_a:.4f} MHz | 11.39 |",
        f"| (b) Voigt 0.10 + 1.39 margin | {m_b:.4f} MHz | 7.77 |",
        f"| (c) Voigt 0.50 + 1.00 margin | {m_c:.4f} MHz | 7.51 |",
        f"| (a) exponent, their eps-form | {e_a_theirs:+.4f} | +0.356 |",
        f"| (b) exponent, their eps-form | {e_b_theirs:+.4f} | −0.160 |",
        "",
        "REPRODUCED, including the exponent SIGN FLIP (anchor V9). "
        "Formulation differences, labelled: (i) exact-FWHM sizing "
        "moves their scenario (b) from "
        f"{m_b:.4f} to {ratio_at_010:.4f} MHz under the same "
        "(secondary) normalisation — their −32% margin headline "
        "carries ≈ 1 point of O-L sizing bias; (ii) under the PRIMARY "
        "import-preserving fixed-G^2 anchoring the same decomposition "
        f"gives {fixed_at_010:.4f} MHz "
        f"({(fixed_at_010 / committed_mhz - 1.0) * 100.0:+.1f}% vs "
        "committed) — the margin shrink is normalisation-dependent; "
        "(iii) their exponent formula divides by 2·ln(1+eps) over "
        "asymmetric (1±eps) points (their Lorentzian control read "
        f"{e_a_theirs:+.3f} vs the analytic "
        f"{committed_exponent:+.3f}); the sweep tables use the "
        "log-symmetric form instead. The SIGN conclusions are "
        "invariant to all three.",
        "",
        "## Committed-law cross-check",
        "",
        f"The f_L = {kappa_s:.2f} row (sigma_g = 0) IS the committed "
        "single-packet law: both normalisations reproduce "
        f"Δf_max = {committed_mhz:.4f} MHz "
        f"(`delta_f_max_hz`) and E = {committed_exponent:+.4f} "
        "(`q_margin_exponent`) — anchors V1/V7; the ensemble route "
        "adds no new physics on that branch, only the audit axis.",
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
    out_path = out_dir / "q_margin_voigt_sensitivity.md"
    out_path.write_text(build_report(), encoding="utf-8", newline="\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
