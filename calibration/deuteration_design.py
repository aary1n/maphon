"""Deuteration identifiability / experiment-design study (WS3, 2026-07-20).

EXPERIMENT-DESIGN ANALYSIS, NOT EVIDENCE. This module quantifies what
WOULD discriminate the pre-registered model set of
docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md §6 —
M0 = shared transport + per-sample geometry; M1 = M0 × one intrinsic
per-sample multiplier X (on Θ or df/dT, deliberately undecomposed) — and
what the current dataset cannot discriminate. It makes NO detection
claim, and its committed artifacts carry the plan's sentence verbatim:

    "No claim that deuteration is detected unless the model comparison
    genuinely discriminates it."

Statistical structure (stated, tested): with shared η_abs and shared
df/dT (the T4 cancellation conditions), the slope RATIO
r = s_d14/s_h14 = X·ρ(nuisances) carries essentially all the
X-information; while the power-measurement plane and η_abs remain
unresolved, absolute slopes constrain only η_abs·Θ, and their one hard
implication (η_abs ≤ 1) trims ~1–2% of the nuisance box (T5). X is
identifiable only to within the model-ratio band of ρ:

    X_det(scenario, σ_rel) = ρ_hi / (ρ_lo · (1 − 2 σ_rel))

is the smallest intrinsic multiplier GUARANTEED to produce the
pre-registered intrinsic-effect-required verdict (measured r outside the
±2σ-inflated band on one side) wherever the true nuisances sit in the
scenario's remaining band. Symmetrically for suppression (1/X).

Angus-pending unknowns stay SWEPT, exactly as the ratified T2 grid:
thickness 0.2–1.0 mm per-sample independent, spot 300–500 µm, h_sub
1e2–1e5 W/m²/K, k over the §6T band, radius mapping over its band.
Nothing here fixes a pending metadata value; "pinning" a nuisance below
means evaluating the band collapse a FUTURE measurement would deliver,
reported over every candidate true value (min–max), never at one
assumed value.

Everything is NON-TRANSFERABLE rig analysis (SPEC §7.T5).
Regenerate: python -m calibration.deuteration_design [--out calibration/reports]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from calibration.constants import DIGITIZED_SIGMA_MHZ, EXCITATION
from calibration.lineshape import D6_MIN_DELTA_AICC
from calibration.ratio_test import model_ratio_grid
from calibration.rig_model import SweepResult, sweep_sample
from calibration.samples import D14, H14, SweepGrid, default_grid
from calibration.slope_fit import fit_all

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = _PACKAGE_DIR / "reports"

NON_DETECTION_SENTENCE = (
    "No claim that deuteration is detected unless the model comparison "
    "genuinely discriminates it"
)

#: Raw-grade relative-σ scoping grid for σ(r)/r. The digitized value is
#: computed from the live T3 fit; these are TARGETS a raw re-fit might
#: reach, labelled scoping — not measurements.
SIGMA_REL_SCOPING: tuple[float, ...] = (0.05, 0.02, 0.01)


def x_det(rho_lo: float, rho_hi: float, sigma_rel: float) -> float:
    """Smallest guaranteed-detectable intrinsic ENHANCEMENT multiplier
    (see module docstring). Diverges as σ_rel → 0.5 (the ±2σ interval
    swallows the ratio); refuse beyond it."""
    if not 0 <= sigma_rel < 0.5:
        raise ValueError(f"sigma_rel {sigma_rel} outside [0, 0.5)")
    return rho_hi / (rho_lo * (1.0 - 2.0 * sigma_rel))


def x_det_suppression(rho_lo: float, rho_hi: float, sigma_rel: float) -> float:
    """Guaranteed-detectable SUPPRESSION, expressed as the factor 1/X > 1:
    detection requires X·ρ_true < r − 2σ at the worst true ρ = ρ_hi, i.e.
    1/X > ρ_hi·(1 + 2σ_rel)/ρ_lo. NOT the reciprocal of the enhancement
    condition — the σ term enters with the opposite sign
    (adversarial-review correction, 2026-07-20)."""
    if not 0 <= sigma_rel < 0.5:
        raise ValueError(f"sigma_rel {sigma_rel} outside [0, 0.5)")
    return rho_hi * (1.0 + 2.0 * sigma_rel) / rho_lo


def x_compatibility_range(
    rho_lo: float, rho_hi: float, measured: float, sigma: float
) -> tuple[float, float]:
    """ENVELOPE-DERIVED COMPATIBILITY RANGE for X, not a confidence
    interval (independent-derivation fold-in, 2026-07-20): every X in
    [(r − 2σ)/ρ_hi, (r + 2σ)/ρ_lo] can reproduce the measured ratio for
    SOME admissible nuisance setting. Sweep grids are bounds, not priors
    — no probabilistic reading (including Bayes factors over the sweep
    box, or the T4 feed's descriptive fraction_within_2sigma) survives
    reparameterisation of the grid."""
    return ((measured - 2.0 * sigma) / rho_hi, (measured + 2.0 * sigma) / rho_lo)


@dataclass(frozen=True)
class ScenarioBand:
    """The model-ratio band remaining under one metadata scenario.

    For 'pin' scenarios the band depends on where the true value sits, so
    the width is reported over every candidate: `width_best`/`width_worst`
    are the ln-band factors (ρ_hi/ρ_lo) at the most and least favourable
    true values; X_det uses the WORST case (guaranteed detection)."""

    name: str
    description: str
    width_best: float
    width_worst: float
    rho_lo_worst: float
    rho_hi_worst: float

    def x_det_at(self, sigma_rel: float) -> float:
        return x_det(self.rho_lo_worst, self.rho_hi_worst, sigma_rel)


def _band(values: np.ndarray) -> tuple[float, float, float]:
    lo = float(np.min(values))
    hi = float(np.max(values))
    return lo, hi, hi / lo


def _shared_axis_arrays(result: SweepResult):
    axes = np.array(result.shared_axes())  # (n_shared, 4): w, h, k, f
    return axes[:, 0], axes[:, 1], axes[:, 2], axes[:, 3]


def _pin_scenario(
    name: str,
    description: str,
    ratios: np.ndarray,
    subset_iter,
) -> ScenarioBand:
    """Band over each candidate true value (subsets are
    (shared_mask, j_d, j_h) index triples); keeps best/worst widths and
    the worst-case band edges."""
    bands = []
    for shared_mask, j_d, j_h in subset_iter:
        values = np.ravel(ratios[shared_mask, j_d, j_h])
        if values.size == 0:
            continue
        bands.append(_band(values))
    widths = [b[2] for b in bands]
    worst = bands[int(np.argmax(widths))]
    return ScenarioBand(
        name=name,
        description=description,
        width_best=float(np.min(widths)),
        width_worst=float(np.max(widths)),
        rho_lo_worst=worst[0],
        rho_hi_worst=worst[1],
    )


@dataclass(frozen=True)
class DesignStudy:
    """Everything the report and JSON serialise."""

    measured_ratio: float
    measured_sigma: float
    sigma_rel_digitized: float
    scenarios: tuple[ScenarioBand, ...]
    matched_glue_full_width: float
    matched_glue_one_decade_width: float
    matched_glue_half_decade_width: float
    power_grid_table: tuple[dict, ...]
    visits_at_n8: tuple[dict, ...]
    aicc_thresholds_n8: dict
    verdict: str
    grid_note: str


def cross_sample_glue_band(
    result_d14: SweepResult,
    result_h14: SweepResult,
    max_decades: float,
) -> tuple[float, float]:
    """The FULL M0 confusion band when per-sample mounting is allowed to
    differ: Θ_d14/Θ_h14 over pairs of shared-axis configs identical in
    (w, k, f) but with |log10 h_d − log10 h_h| ≤ max_decades, thickness
    per-sample free. The T4 sweep SHARES h_sub by convention (its
    committed verdict criterion); this band is the honest identifiability
    envelope once the documented glue confound is admitted as
    M0-compatible."""
    w_d, h_d, k_d, f_d = _shared_axis_arrays(result_d14)
    theta_d = result_d14.theta_k_per_w
    theta_h = result_h14.theta_k_per_w
    groups: dict[tuple[float, float, float], list[int]] = {}
    for i in range(theta_d.shape[0]):
        groups.setdefault((w_d[i], k_d[i], f_d[i]), []).append(i)
    lo, hi = math.inf, 0.0
    for members in groups.values():
        idx = np.array(members)
        logh = np.log10(h_d[idx])
        for a_pos, a in enumerate(idx):
            close = idx[np.abs(logh - logh[a_pos]) <= max_decades + 1e-12]
            if close.size == 0:
                continue
            den = theta_h[close, :]  # (n_close, n_t_h)
            # all (t_d, t_h) combinations against every close-h config
            ratios = theta_d[a][None, :, None] / den[:, None, :]
            lo = min(lo, float(np.min(ratios)))
            hi = max(hi, float(np.max(ratios)))
    return lo, hi


def matched_glue_band(
    result: SweepResult, max_decades: float
) -> float:
    """ρ-band factor from glue asymmetry ALONE at fully matched geometry:
    pairs of shared-axis configs identical except h_sub, with
    |log10 h1 − log10 h2| ≤ max_decades, at equal thickness."""
    w_arr, h_arr, k_arr, f_arr = _shared_axis_arrays(result)
    theta = result.theta_k_per_w  # (n_shared, n_t)
    groups: dict[tuple[float, float, float], list[int]] = {}
    for i in range(theta.shape[0]):
        groups.setdefault((w_arr[i], k_arr[i], f_arr[i]), []).append(i)
    worst = 1.0
    for members in groups.values():
        idx = np.array(members)
        logh = np.log10(h_arr[idx])
        for a_pos, a in enumerate(idx):
            for b_pos, b in enumerate(idx):
                if abs(logh[a_pos] - logh[b_pos]) > max_decades + 1e-12:
                    continue
                for j in range(theta.shape[1]):  # equal thickness
                    ratio = theta[a, j] / theta[b, j]
                    if ratio > worst:
                        worst = float(ratio)
    return worst


def run_design_study(grid: SweepGrid | None = None) -> DesignStudy:
    grid = default_grid() if grid is None else grid
    fits = fit_all()
    measured, sigma = fits.ratio.ratio, fits.ratio.sigma
    sigma_rel = sigma / measured

    result_d14 = sweep_sample(D14, grid)
    result_h14 = sweep_sample(H14, grid)
    ratios = model_ratio_grid(result_d14, result_h14)  # (n_shared, n_t, n_t)
    w_arr, h_arr, k_arr, f_arr = _shared_axis_arrays(result_d14)
    n_t = ratios.shape[1]
    all_shared = np.ones(ratios.shape[0], dtype=bool)

    scenarios: list[ScenarioBand] = []

    lo, hi, width = _band(np.ravel(ratios))
    scenarios.append(
        ScenarioBand(
            name="baseline",
            description=(
                "current metadata: thickness/spot/h_sub/k/mapping all swept "
                "(the T4 band)"
            ),
            width_best=width,
            width_worst=width,
            rho_lo_worst=lo,
            rho_hi_worst=hi,
        )
    )

    scenarios.append(
        _pin_scenario(
            "pin_thickness",
            "per-sample thickness MEASURED (Angus ask 1, top residual gap): "
            "band at each candidate (t_d14, t_h14) pair",
            ratios,
            (
                (all_shared, j_d, j_h)
                for j_d in range(n_t)
                for j_h in range(n_t)
            ),
        )
    )
    scenarios.append(
        _pin_scenario(
            "pin_spot",
            "spot diameter MEASURED (Angus ask 2): band at each candidate w",
            ratios,
            ((w_arr == w, slice(None), slice(None)) for w in grid.spot_diameter_m),
        )
    )
    scenarios.append(
        _pin_scenario(
            "narrow_h_sub_one_decade",
            "underside coupling narrowed to ONE decade (bond-line thickness "
            "+ cement-k literature per plan §4.6, or remount empirics) — "
            "both samples in the same decade, per-sample value still free",
            ratios,
            (
                (
                    (h_arr >= d_lo) & (h_arr <= d_lo * 10.0),
                    slice(None),
                    slice(None),
                )
                for d_lo in (1e2, 1e3, 1e4)
            ),
        )
    )
    scenarios.append(
        _pin_scenario(
            "pin_k",
            "k_PTP pinned by an independent measurement (closes the §6T "
            "band): band at each candidate k",
            ratios,
            ((k_arr == k, slice(None), slice(None)) for k in grid.k_w_m_k),
        )
    )
    scenarios.append(
        _pin_scenario(
            "pin_mapping",
            "square-to-disc mapping systematic resolved (shape metrology): "
            "band at each candidate factor",
            ratios,
            ((f_arr == f, slice(None), slice(None)) for f in grid.radius_factor),
        )
    )
    scenarios.append(
        _pin_scenario(
            "pin_thickness_and_spot",
            "asks 1+2 both answered: thickness pair AND spot pinned",
            ratios,
            (
                (w_arr == w, j_d, j_h)
                for w in grid.spot_diameter_m
                for j_d in range(n_t)
                for j_h in range(n_t)
            ),
        )
    )
    scenarios.append(
        _pin_scenario(
            "all_metadata",
            "thickness + spot + one-decade h_sub + mapping resolved (k still "
            "banded): the realistic best case without new physics data",
            ratios,
            (
                (
                    (w_arr == w)
                    & (f_arr == f)
                    & (h_arr >= d_lo)
                    & (h_arr <= d_lo * 10.0),
                    j_d,
                    j_h,
                )
                for w in grid.spot_diameter_m
                for f in grid.radius_factor
                for d_lo in (1e2, 1e3, 1e4)
                for j_d in range(n_t)
                for j_h in range(n_t)
            ),
        )
    )

    # The honest M0 envelope: the T4 sweep SHARES h_sub by committed
    # convention, but per-sample mounting (the documented glue confound)
    # is M0-compatible — admit it and the identifiability band widens.
    for decades, name, desc in (
        (
            3.0,
            "m0_unconstrained_mounting",
            "per-sample h_sub free across the full decade prior — the "
            "honest M0 envelope while mounting is unconstrained (the T4 "
            "sweep shares h_sub by its committed convention; the glue "
            "confound is the orthogonal axis)",
        ),
        (
            1.0,
            "m0_mounting_within_1_decade",
            "per-sample h_sub differing by <= 1 decade (remount empirics "
            "or bond-line metrology would deliver this)",
        ),
        (
            0.5,
            "m0_mounting_within_half_decade",
            "per-sample h_sub differing by <= 0.5 decade",
        ),
    ):
        g_lo, g_hi = cross_sample_glue_band(result_d14, result_h14, decades)
        scenarios.append(
            ScenarioBand(
                name=name,
                description=desc,
                width_best=g_hi / g_lo,
                width_worst=g_hi / g_lo,
                rho_lo_worst=g_lo,
                rho_hi_worst=g_hi,
            )
        )

    matched_full = matched_glue_band(result_d14, max_decades=3.0)
    matched_one = matched_glue_band(result_d14, max_decades=1.0)
    matched_half = matched_glue_band(result_d14, max_decades=0.5)

    # Power-grid arithmetic (adversarial-review re-derivation,
    # 2026-07-20): for N equally spaced levels spanning ΔP with r
    # independent visits per level, the EXACT endpoint-grid moment is
    #   S_xx = r · ΔP² · N(N+1) / (12(N−1)),
    # σ_slope = σ_point/√S_xx, and the ratio's relative error combines
    # BOTH measured slopes: σ_rel(R)² = σ_slope² · (1/s_d² + 1/s_h²).
    # N is solved exactly with N ≥ 3 enforced (a slope from fewer points
    # has no estimable residual).
    span_mw = max(EXCITATION.powers_h14_mw) - min(EXCITATION.powers_h14_mw)
    slope_d = abs(fits.fits["d14"].slope_mhz_per_mw)
    slope_h = abs(fits.fits["h14"].slope_mhz_per_mw)
    inv_s2 = 1.0 / slope_d**2 + 1.0 / slope_h**2

    def _sxx(n: int, r: int = 1) -> float:
        return r * span_mw**2 * n * (n + 1) / (12.0 * (n - 1))

    def _sigma_rel_ratio(sigma_point: float, n: int, r: int = 1) -> float:
        return math.sqrt(sigma_point**2 / _sxx(n, r) * inv_s2)

    table = []
    for sigma_point_mhz in (DIGITIZED_SIGMA_MHZ, 0.02, 0.01, 0.005):
        for target in SIGMA_REL_SCOPING:
            n_req = next(
                (
                    n
                    for n in range(3, 100_001)
                    if _sigma_rel_ratio(sigma_point_mhz, n) <= target
                ),
                None,
            )
            table.append(
                {
                    "sigma_point_mhz": sigma_point_mhz,
                    "sigma_point_is_digitized_floor": (
                        sigma_point_mhz == DIGITIZED_SIGMA_MHZ
                    ),
                    "target_sigma_rel": target,
                    "n_required": n_req,
                    "d6_note": (
                        "D6 additionally requires >= 8 independent power "
                        "points before ANY nonlinear power model is claimable"
                    ),
                }
            )
    visits = tuple(
        {
            "n_levels": 8,
            "visits_per_level": r,
            "sigma_rel_ratio_at_digitized_floor": _sigma_rel_ratio(
                DIGITIZED_SIGMA_MHZ, 8, r
            ),
        }
        for r in (1, 2, 3)
    )
    # ΔAICc >= 4 translated into required chi-square improvements at the
    # D6 minimum N = 8 (computed from the aicc() convention, not quoted):
    from calibration.lineshape import aicc as _aicc

    def _needed_dchi2(k_alt: int, n: int = 8) -> float:
        # AICc_alt <= AICc_lin - 4 with equal chi2 baseline offsets
        penalty_lin = _aicc(n, 2, chi2=0.0)
        penalty_alt = _aicc(n, k_alt, chi2=0.0)
        return D6_MIN_DELTA_AICC + (penalty_alt - penalty_lin)

    aicc_thresholds = {
        "n": 8,
        "quadratic_dchi2": _needed_dchi2(3),
        "piecewise_searched_breakpoint_dchi2": _needed_dchi2(4),
    }

    return DesignStudy(
        measured_ratio=measured,
        measured_sigma=sigma,
        sigma_rel_digitized=sigma_rel,
        scenarios=tuple(scenarios),
        matched_glue_full_width=matched_full,
        matched_glue_one_decade_width=matched_one,
        matched_glue_half_decade_width=matched_half,
        power_grid_table=tuple(table),
        visits_at_n8=visits,
        aicc_thresholds_n8=aicc_thresholds,
        verdict=(
            "INSUFFICIENTLY IDENTIFIABLE at current metadata: the model "
            "ratio band brackets the measured ratio from both sides "
            "(T4 verdict geometry-sufficient, low discriminating power). "
            + NON_DETECTION_SENTENCE
            + "."
        ),
        grid_note=(
            "all bands computed on the ratified T2 grid (thickness 0.2-1.0 "
            "mm per-sample, spot 300-500 um, h_sub 1e2-1e5, k 0.1-1.0, "
            "mapping band) — Angus-pending unknowns SWEPT, never fixed"
        ),
    )


def to_json(study: DesignStudy) -> str:
    payload = {
        "workstream": "deuteration-identifiability-design",
        "status": (
            "experiment-design analysis, NOT evidence of deuteration; "
            "non-transferable rig analysis (SPEC 7.T5)"
        ),
        "non_detection_sentence": NON_DETECTION_SENTENCE,
        "verdict": study.verdict,
        "grid_note": study.grid_note,
        "measured": {
            "ratio_d14_over_h14": study.measured_ratio,
            "sigma": study.measured_sigma,
            "sigma_rel": study.sigma_rel_digitized,
            "grade": "graph-digitized-provisional; superseded_by_raw_data=True",
        },
        "x_range_semantics": (
            "x_compat = envelope-derived compatibility range, NOT a "
            "confidence interval; x_det/x_det_suppression = smallest "
            "GUARANTEED-detectable enhancement / suppression factors. "
            "Sweep grids are bounds, not priors: no probabilistic reading "
            "(Bayes factors over the sweep box, or the T4 feed's "
            "descriptive fraction_within_2sigma) survives grid "
            "reparameterisation."
        ),
        "scenarios": [
            {
                **asdict(s),
                "x_det_at_digitized_sigma": s.x_det_at(
                    min(study.sigma_rel_digitized, 0.49)
                ),
                "x_det_suppression_at_digitized_sigma": x_det_suppression(
                    s.rho_lo_worst,
                    s.rho_hi_worst,
                    min(study.sigma_rel_digitized, 0.49),
                ),
                "x_det_at_scoping_sigma": {
                    str(sr): s.x_det_at(sr) for sr in SIGMA_REL_SCOPING
                },
                "x_compat_at_digitized_sigma": x_compatibility_range(
                    s.rho_lo_worst,
                    s.rho_hi_worst,
                    study.measured_ratio,
                    study.measured_sigma,
                ),
            }
            for s in study.scenarios
        ],
        "power_grid_visits_at_n8": list(study.visits_at_n8),
        "aicc_thresholds_at_n8": study.aicc_thresholds_n8,
        "statistical_structure_notes": [
            "profile-likelihood framing: the common scale A (power plane x "
            "shared absorption x shared |df/dT|) profiles out analytically, "
            "leaving ONE scale-free contrast from the two slopes; M0 "
            "carries ~7-8 effective unknowns against it (M1 adds one "
            "identifiable relative multiplier X)",
            "matched-pair design inequality: a factor X is "
            "design-resolvable only if |log X| > eps_g + 2*sigma_ell "
            "(hard geometry-mismatch bound + statistical error); no number "
            "of power points rescues a failed geometry condition",
        ],
        "matched_sample_analysis": {
            "glue_only_band_full_prior": study.matched_glue_full_width,
            "glue_only_band_one_decade": study.matched_glue_one_decade_width,
            "glue_only_band_half_decade": study.matched_glue_half_decade_width,
            "reading": (
                "at FULLY matched geometry the residual band is glue "
                "asymmetry alone; remounting the SAME crystal n times "
                "converts the h_sub prior into a measured spread (the only "
                "way to shrink this band empirically), whereas a second "
                "unmatched d14/h14 pair adds a new ratio with its own "
                "unconstrained glue asymmetry and does NOT shrink it"
            ),
        },
        "power_grid": list(study.power_grid_table),
    }
    return json.dumps(payload, indent=2)


def render_report(study: DesignStudy) -> str:
    s_dig = min(study.sigma_rel_digitized, 0.49)
    lines = [
        "# Deuteration identifiability / experiment design (WS3, 2026-07-20)",
        "",
        "**Status: EXPERIMENT-DESIGN ANALYSIS — NOT evidence of deuteration.**",
        f"**{NON_DETECTION_SENTENCE}.**",
        "Regenerate: `python -m calibration.deuteration_design`. "
        "NON-TRANSFERABLE rig analysis (SPEC §7.T5).",
        "",
        f"- measured ratio (T3, digitized grade): {study.measured_ratio:.3f} "
        f"± {study.measured_sigma:.3f} (σ_rel = {study.sigma_rel_digitized:.3f})",
        f"- {study.grid_note}",
        f"- **Current verdict: {study.verdict}**",
        "",
        "## Statistical structure",
        "",
        "Under the T4 cancellation conditions (shared η_abs — valid only "
        "under near-total absorption; shared df/dT — deuteration-transfer "
        "caveat riding), the slope RATIO carries essentially all the "
        "X-information: while the power plane and η_abs are unresolved, "
        "absolute slopes constrain only the product η_abs·Θ, and their one "
        "hard implication (η_abs ≤ 1) trims ~1–2% of the nuisance box "
        "(T5: 98–99% of the sweep admits η_abs ≤ 1). X is identifiable "
        "only to the model-ratio band ρ ∈ [ρ_lo, ρ_hi]:",
        "",
        "    X_det = ρ_hi / (ρ_lo · (1 − 2σ_rel))     (enhancement)",
        "    1/X  > ρ_hi · (1 + 2σ_rel) / ρ_lo        (suppression — NOT",
        "                                              the reciprocal: the",
        "                                              σ term flips sign)",
        "",
        "is the smallest multiplier GUARANTEED to force the pre-registered "
        "intrinsic-effect-required verdict wherever the true nuisances sit. "
        "The complementary X_compat = [(r−2σ)/ρ_hi, (r+2σ)/ρ_lo] is the "
        "ENVELOPE-DERIVED COMPATIBILITY RANGE — not a confidence interval: "
        "sweep grids are bounds, not priors, and no probabilistic reading "
        "(Bayes factors over the sweep box, or T4's descriptive "
        "fraction_within_2sigma) survives grid reparameterisation.",
        "",
        "Profile-likelihood framing (independent-derivation fold-in, "
        "2026-07-20): the common scale A (power plane × shared absorption × "
        "shared |df/dT|) profiles out analytically, leaving ONE scale-free "
        "contrast from the two slopes against M0's ~7–8 effective unknowns; "
        "M1 adds one identifiable relative multiplier X.",
        "",
        "## Scenario ladder — what each future measurement buys",
        "",
        "| scenario | band factor ρ_hi/ρ_lo (best–worst over true values) | "
        "X_det @ digitized σ | X_det @ σ_rel=0.02 | X_compat @ digitized σ |",
        "|---|---|---|---|---|",
    ]
    for s in study.scenarios:
        compat = x_compatibility_range(
            s.rho_lo_worst,
            s.rho_hi_worst,
            study.measured_ratio,
            study.measured_sigma,
        )
        lines.append(
            f"| {s.name} | {s.width_best:.2f} – {s.width_worst:.2f} | "
            f"{s.x_det_at(s_dig):.2f} | {s.x_det_at(0.02):.2f} | "
            f"[{compat[0]:.3f}, {compat[1]:.3f}] |"
        )
    dominant = max(
        (
            s
            for s in study.scenarios
            if s.name
            in ("pin_thickness", "pin_spot", "narrow_h_sub_one_decade", "pin_k", "pin_mapping")
        ),
        key=lambda s: study.scenarios[0].width_best / s.width_best,
    )
    m0_env = next(
        s for s in study.scenarios if s.name == "m0_unconstrained_mounting"
    )
    lines += [
        "",
        "**The binding limiter is MOUNTING, not metadata:** the T4 band "
        "above shares h_sub between samples by its committed convention; "
        "admitting the documented glue confound (per-sample mounting, "
        "M0-compatible) widens the honest identifiability envelope to "
        f"×{m0_env.width_worst:.1f} — no plausible intrinsic factor is "
        "guaranteed-detectable while mounting is unconstrained. Mounting "
        "control (remount empirics / bond-line metrology) is therefore the "
        "gateway measurement, ahead of every metadata pin.",
        "",
        f"**Dominant single METADATA nuisance (largest best-case band "
        f"collapse when measured): `{dominant.name}`** — baseline factor "
        f"{study.scenarios[0].width_best:.2f} → best-case "
        f"{dominant.width_best:.2f}, worst-case {dominant.width_worst:.2f} "
        "(worst case = least favourable true values; the guarantee "
        "criterion X_det uses the worst case).",
        "",
        "## Matched-sample geometry",
        "",
        "DEFINITION (disambiguated 2026-07-20): the numbers below are "
        "SAME-CRYSTAL mounting-pair ratios, computed on the d14 geometry — "
        "Θ(d14, mount 1)/Θ(d14, mount 2) at equal everything except h_sub. "
        "This is the matched-pair LIMIT: what glue asymmetry alone can "
        "manufacture when geometry is perfectly matched. (The CURRENT "
        "unequal pair with per-sample mounting is the m0_* scenario rows "
        "above — a different, wider object.)",
        "",
        f"- glue-only band, full h_sub prior (3 decades): "
        f"×{study.matched_glue_full_width:.2f}",
        f"- constrained to 1 decade (remount empirics / bond-line data): "
        f"×{study.matched_glue_one_decade_width:.2f}",
        f"- constrained to 0.5 decade: "
        f"×{study.matched_glue_half_decade_width:.2f}",
        "",
        "Matched-pair design inequality (independent-derivation fold-in): a "
        "factor X is design-resolvable only if |log X| > ε_g + 2σ_ℓ, with "
        "ε_g the hard residual geometry/absorption-mismatch bound and σ_ℓ "
        "the statistical error on the log contrast — no number of power "
        "points rescues a failed geometry condition.",
        "",
        "**Remount-same-crystal vs a second unmatched pair:** CONTROLLED "
        "remounting/cross-over of the same crystal(s) over standardised "
        "mount positions measures the h_sub spread directly — the only "
        "route that shrinks the glue confound φ empirically (an "
        "uncontrolled remount merely resamples it). A second unmatched "
        "d14/h14 pair adds one more ratio carrying its own unconstrained "
        "φ′ and does not shrink the confound. Controlled repetition under "
        "different mounting conditions is therefore MORE informative than "
        "an additional unmatched pair for the M0/M1 question. "
        "Time-resolved heating/cooling traces rank immediately behind it: "
        "the normalised transient removes the unknown amplitude and "
        "constrains h_i/diffusivity/settling orthogonally to the steady "
        "slope (introducing ρc_p; check 3c).",
        "",
        "## Power grid (per sample)",
        "",
        "Exact endpoint-grid WLS arithmetic across the current span "
        f"({min(EXCITATION.powers_h14_mw):.2f}–"
        f"{max(EXCITATION.powers_h14_mw):.2f} mW): "
        "S_xx = r·ΔP²·N(N+1)/(12(N−1)), σ_slope = σ_point/√S_xx, and "
        "σ_rel(R)² combines BOTH measured slopes "
        "(re-derived 2026-07-20; the earlier draft's span/√12 single-slope "
        "shortcut and N<3 rows are retired). Required N (one visit per "
        "level, N ≥ 3 enforced):",
        "",
        "| σ_point (MHz) | target σ_rel | N required | note |",
        "|---|---|---|---|",
    ]
    for row in study.power_grid_table:
        note = "digitized floor" if row["sigma_point_is_digitized_floor"] else ""
        n_txt = str(row["n_required"]) if row["n_required"] else "unreachable"
        lines.append(
            f"| {row['sigma_point_mhz']:.3f} | {row['target_sigma_rel']:.2f} "
            f"| {n_txt} | {note} |"
        )
    lines += [
        "",
        "Repeat visits at the D6 minimum grid (N = 8 levels, digitized "
        "floor):",
        "",
    ]
    for v in study.visits_at_n8:
        lines.append(
            f"- r = {v['visits_per_level']} visit(s)/level → σ_rel(R) ≈ "
            f"{v['sigma_rel_ratio_at_digitized_floor']:.3f} (nominal 1/√r; "
            "correlated drift/hysteresis prevents the full gain)"
        )
    lines += [
        "",
        f"ΔAICc ≥ {D6_MIN_DELTA_AICC:g} at N = 8 translates to required "
        "χ² improvements over linear of "
        f"≥ {study.aicc_thresholds_n8['quadratic_dchi2']:.1f} (quadratic) "
        "and ≥ "
        f"{study.aicc_thresholds_n8['piecewise_searched_breakpoint_dchi2']:.2f} "
        "(piecewise with a searched breakpoint, k = 4).",
        "",
        "Acquisition protocol riders: D6 (user-ratified 2026-07-20) "
        "requires ≥ 8 independent power LEVELS (repeats at one level do "
        "not count) AND ΔAICc ≥ 4 before any nonlinear power model is "
        "claimable. Acquire THREE blocks — one ascending, one descending, "
        "one randomised/interleaved — with d14 and h14 interleaved and the "
        "settling duration chosen from a MEASURED time trace, so monotone "
        "drift separates from direction-dependent hysteresis (plan §6 "
        "steady-state check). Time-resolved traces additionally decide "
        "check 3c, orthogonal to this table.",
        "",
        "## What this study does NOT do",
        "",
        "- It does not detect, suggest, or exclude a deuteration effect "
        "(the T4 verdict — geometry-sufficient, low discriminating power, "
        "'not required and not excluded' — stands verbatim).",
        "- It does not fix any Angus-pending metadata value (all swept).",
        "- It does not decompose M1's multiplier into k-isotope vs df/dT-"
        "deuteration (indistinguishable here by design, plan §6).",
        "- Its numbers do not transfer to the maser geometry.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="python -m calibration.deuteration_design"
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT), type=Path)
    args = parser.parse_args(argv)
    study = run_design_study()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "deuteration_design.md").write_text(
        render_report(study), encoding="utf-8", newline="\n"
    )
    (out_dir / "deuteration_design.json").write_text(
        to_json(study), encoding="utf-8", newline="\n"
    )
    print(render_report(study))
    print(f"[written to {out_dir}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
