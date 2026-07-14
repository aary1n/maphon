"""T4 — ratio discrimination: does geometry alone explain d14 vs h14?

Compares the MEASURED d14/h14 slope ratio (T3; shared η_abs and shared
df/dT cancel in the ratio by construction) against the MODEL dT/dP ratio
Θ_d14/Θ_h14 over the T2 sweep with SHARED interface parameters (k, h_sub,
spot, radius mapping common to both samples; per-sample thickness free).

Cancellation condition, stated: shared η_abs additionally requires
near-total absorption in both crystals (l_abs ≪ t — supported by the
`L_ABS_PUMP` scoping band at 0.1% nominal; the zone-refining caveat means
actual [Pc] may differ per growth, which would land in the intrinsic
branch). Per-sample GLUE CONTACT does NOT cancel — quantified below as
the h_sub ratio that would reproduce the measured ratio at matched
geometry (the documented residual confound).

Three-way verdict, criteria fixed at ratification (plan T4):
- geometry-sufficient    — some swept θ puts the model ratio within 2σ of
                           the measured ratio;
- intrinsic-effect-required — every swept point falls outside measured±2σ
                           on ONE side (the sweep cannot reach the data);
- indeterminate          — swept points straddle the ±2σ interval without
                           landing inside (grid too coarse to discriminate).

The intrinsic branch is deliberately NOT decomposed: it covers both
k_d14 ≠ k_h14 (isotope effect on phonon conduction) and
df/dT_d14 ≠ df/dT_h14 (deuteration of the spin coefficient); this dataset
cannot separate them.

COMSOL contingency trigger (licence discipline, fixed in advance): fires
only if the verdict is indeterminate AND flips across the radius-mapping
band edges — i.e. the square-planform systematic, not the swept physics,
is what blocks discrimination.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from calibration.constants import RADIUS_MAPPING, SPOT, THICKNESS
from calibration.rig_model import RigConfig, SweepResult, sweep_sample, theta_probe_k_per_w
from calibration.samples import D14, H14, SweepGrid, default_grid
from calibration.slope_fit import fit_all
from cavity.provenance.constants import K_PTP

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPORT = _PACKAGE_DIR / "reports" / "ratio_test_digitized.md"

GEOMETRY_SUFFICIENT = "geometry-sufficient"
INTRINSIC_REQUIRED = "intrinsic-effect-required"
INDETERMINATE = "indeterminate"


def classify(model_ratios: np.ndarray, measured: float, sigma: float) -> str:
    """The ratified three-way rule on a set of swept model ratios."""
    lo, hi = measured - 2.0 * sigma, measured + 2.0 * sigma
    inside = np.any((model_ratios >= lo) & (model_ratios <= hi))
    if inside:
        return GEOMETRY_SUFFICIENT
    below = np.any(model_ratios < lo)
    above = np.any(model_ratios > hi)
    if below and above:
        return INDETERMINATE
    return INTRINSIC_REQUIRED


@dataclass(frozen=True)
class RatioTestResult:
    verdict: str
    measured_ratio: float
    measured_sigma: float
    model_ratio_min: float
    model_ratio_max: float
    fraction_within_2sigma: float
    n_ratio_points: int
    verdict_by_radius_factor: dict[float, str]
    comsol_trigger: bool
    glue_confound_factor: dict[float, float | None]  # h_sub_h14 -> h_sub_d14/h_sub_h14
    provenance: str


def model_ratio_grid(
    result_d14: SweepResult, result_h14: SweepResult
) -> np.ndarray:
    """Θ_d14/Θ_h14 for every (shared config, t_d14, t_h14) triple —
    shape (n_shared, n_t, n_t). Shared flat index pairs the two sweeps."""
    if result_d14.grid is not result_h14.grid and result_d14.grid != result_h14.grid:
        raise ValueError("both sweeps must run on the same grid")
    return result_d14.theta_k_per_w[:, :, None] / result_h14.theta_k_per_w[:, None, :]


def glue_confound_factor(
    measured_ratio: float,
    h_sub_h14_w_m2_k: float,
    thickness_m: float | None = None,
) -> float | None:
    """MATCHED geometry (equal mid-band everything), UNEQUAL glue: the
    factor φ = h_sub_d14/h_sub_h14 that reproduces the measured ratio.

    Θ is strictly decreasing in h_sub (pinned in the rig-model tests), so
    the root in log₁₀(h_sub_d14) is unique if it exists in the scanned
    bracket [1e0, 1e8] W/m²/K; None means even that bracket cannot reach
    the measured ratio at this h_sub_h14."""
    t = 0.5 * (THICKNESS.lo_m + THICKNESS.hi_m) if thickness_m is None else thickness_m

    def _theta(sample, h_sub):
        return theta_probe_k_per_w(
            RigConfig(
                sample=sample,
                thickness_m=t,
                spot_diameter_m=SPOT.diameter_m,
                h_sub_w_m2_k=h_sub,
                k_w_m_k=K_PTP.k_mid_w_m_k,
                radius_factor=RADIUS_MAPPING.factor_point,
            )
        )

    theta_h14 = _theta(H14, h_sub_h14_w_m2_k)

    def objective(log10_h_sub_d14: float) -> float:
        return _theta(D14, 10.0**log10_h_sub_d14) / theta_h14 - measured_ratio

    lo, hi = 0.0, 8.0
    if objective(lo) * objective(hi) > 0:
        return None
    log10_root = brentq(objective, lo, hi, xtol=1e-10)
    return 10.0**log10_root / h_sub_h14_w_m2_k


def run_ratio_test(grid: SweepGrid | None = None) -> RatioTestResult:
    grid = default_grid() if grid is None else grid
    fits = fit_all()
    measured, sigma = fits.ratio.ratio, fits.ratio.sigma

    result_d14 = sweep_sample(D14, grid)
    result_h14 = sweep_sample(H14, grid)
    ratios = model_ratio_grid(result_d14, result_h14)

    verdict = classify(ratios.ravel(), measured, sigma)
    lo, hi = measured - 2.0 * sigma, measured + 2.0 * sigma
    fraction = float(np.mean((ratios >= lo) & (ratios <= hi)))

    factors = np.array([axes[3] for axes in result_d14.shared_axes()])
    verdict_by_factor = {
        f: classify(ratios[factors == f].ravel(), measured, sigma)
        for f in grid.radius_factor
    }
    edge_verdicts = {verdict_by_factor[grid.radius_factor[0]], verdict_by_factor[grid.radius_factor[-1]]}
    comsol_trigger = verdict == INDETERMINATE and len(edge_verdicts) > 1

    confound = {
        h_ref: glue_confound_factor(measured, h_ref)
        for h_ref in (1e2, 1e3, 1e4, 1e5)
    }

    return RatioTestResult(
        verdict=verdict,
        measured_ratio=measured,
        measured_sigma=sigma,
        model_ratio_min=float(ratios.min()),
        model_ratio_max=float(ratios.max()),
        fraction_within_2sigma=fraction,
        n_ratio_points=int(ratios.size),
        verdict_by_radius_factor=verdict_by_factor,
        comsol_trigger=comsol_trigger,
        glue_confound_factor=confound,
        provenance=fits.ratio.provenance,
    )


def render_report(result: RatioTestResult) -> str:
    lines = [
        "# T4 — ratio discrimination test (d14/h14, Cowley-Semple 2026-07-14)",
        "",
        f"**VERDICT: {result.verdict.upper()}**",
        "",
        f"- measured slope ratio (T3, {result.provenance}): "
        f"{result.measured_ratio:.3f} ± {result.measured_sigma:.3f}",
        f"- model ratio band over the shared-parameter sweep: "
        f"[{result.model_ratio_min:.3f}, {result.model_ratio_max:.3f}] "
        f"({result.n_ratio_points} (shared θ, t_d14, t_h14) points)",
        f"- fraction of swept points inside measured ± 2σ: "
        f"{100 * result.fraction_within_2sigma:.1f}%",
        "",
        "Shared axes (cancel by construction): η_abs and df/dT — VALID ONLY under",
        "near-total absorption in both crystals (l_abs ≪ t; zone-refining caveat",
        "means per-growth [Pc] differences land in the intrinsic branch). Interface",
        "parameters k, h_sub, spot, radius mapping SHARED; thickness per-sample free.",
        "",
        "## Verdict by radius-mapping factor (COMSOL contingency input)",
        "",
    ]
    for f, v in result.verdict_by_radius_factor.items():
        lines.append(f"- factor {f:.4f}: {v}")
    lines += [
        "",
        f"COMSOL contingency trigger (indeterminate AND edge-flip): "
        f"**{'FIRED' if result.comsol_trigger else 'not fired'}** — licence discipline holds."
        if not result.comsol_trigger
        else "COMSOL contingency trigger: **FIRED** — escalate per plan.",
        "",
        "## Residual confound: per-sample glue contact (does NOT cancel)",
        "",
        "φ = h_sub(d14)/h_sub(h14) required to reproduce the measured ratio at",
        "MATCHED geometry (equal mid-band thickness/k/spot/mapping):",
        "",
    ]
    for h_ref, phi in result.glue_confound_factor.items():
        phi_txt = f"{phi:.3g}" if phi is not None else "unreachable in [1e0, 1e8]"
        lines.append(f"- h_sub(h14) = {h_ref:.0e} W/m²/K → φ = {phi_txt}")
    lines += [
        "",
        "Interpretation: a φ of this size is an ALTERNATIVE explanation the ratio",
        "test cannot exclude — the d14 crystal merely being glued worse than h14.",
        "",
        "## Scope of the intrinsic branch (deliberately not decomposed)",
        "",
        "If the verdict is intrinsic-effect-required, this dataset cannot separate",
        "k_d14 ≠ k_h14 (isotope effect on phonon conduction) from",
        "df/dT_d14 ≠ df/dT_h14 (deuterated spin coefficient) — both are 'intrinsic'.",
        "This is the quantitative form of Angus's 'can you include whether it's",
        "deuterated' question; a geometry-sufficient verdict means the data does",
        "not require a deuteration effect to be explained.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # cp1252 console
    result = run_ratio_test()
    report = render_report(result)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"[written to {DEFAULT_REPORT}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
