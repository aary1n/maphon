"""T3 — weighted slope fits of the digitized ODMR shift-vs-power points.

Input is EXCLUSIVELY the derived CSV
(calibration/data/derived/odmr_shift_vs_power_digitized.csv). Its
provenance header is load-bearing: this module refuses to run unless the
header carries a Grade line and the ±0.05 MHz error model, and every
output it produces re-stamps `graph-digitized-provisional;
superseded_by_raw_data=True` so the grade cannot launder off downstream.
Do NOT re-derive points from the archived PNGs (ratified plan T3).

Model: per-sample weighted least squares f = f0 + s·P with the uniform
per-point floor σ = 0.05 MHz (`calibration.constants.DIGITIZED_SIGMA_MHZ`
— the CSV's own stated error model, 0.1 MHz plot quantization). With
uniform weights the WLS point estimates coincide with OLS and the
parameter covariance is the textbook σ²-propagated one (NOT residual-
scaled: σ is a stated floor, so χ²/dof is reported as a lack-of-fit
statistic instead of being absorbed into the errors).

Outputs (`fit_all` / CLI report):
- slope ± σ per sample (MHz/mW),
- d14/h14 slope ratio ± σ (first-order propagation),
- the h14 nonlinearity check: the single 0.3 MHz step at 10.16→12.33 mW
  against the linear prediction, plus the global lack-of-fit χ²/dof.
  The step z-score treats the observed step and the fitted slope as
  independent (they share points, so the z is approximate — stated in
  the report; the χ² is the primary statistic).

The archive integrity gate (`calibration.integrity.require_intact`) runs
before any data is read.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from calibration.constants import DIGITIZED_SIGMA_MHZ
from calibration.integrity import require_intact

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = _PACKAGE_DIR / "data" / "derived" / "odmr_shift_vs_power_digitized.csv"
DEFAULT_REPORT = _PACKAGE_DIR / "reports" / "slope_fit_digitized.md"

REQUIRED_HEADER_FRAGMENTS = (
    "Grade: graph-digitized-provisional",
    "superseded_by_raw_data=True",
    "+/-0.05 MHz",
)
PROVENANCE_STAMP = "graph-digitized-provisional; superseded_by_raw_data=True"

# One string, two sinks: the T3 report and the observable-a feed both carry
# this caveat verbatim so they cannot drift apart.
QUANTIZATION_CAVEAT = (
    "A 0.1 MHz-quantized plot can manufacture steps "
    "of this size — treat as provisional until raw traces land."
)

# The h14 step the task singles out (MHz step at these two trace powers).
H14_STEP_POWERS_MW = (10.16, 12.33)


@dataclass(frozen=True)
class PowerSeries:
    sample: str
    powers_mw: np.ndarray
    f_peak_mhz: np.ndarray
    sigma_mhz: float
    provenance: str


@dataclass(frozen=True)
class SlopeFit:
    sample: str
    slope_mhz_per_mw: float
    slope_sigma_mhz_per_mw: float
    intercept_mhz: float
    intercept_sigma_mhz: float
    chi2: float
    dof: int
    n_points: int
    provenance: str

    @property
    def chi2_per_dof(self) -> float:
        return self.chi2 / self.dof


@dataclass(frozen=True)
class StepTest:
    """The h14 10.16→12.33 mW step vs the linear prediction."""

    observed_step_mhz: float
    predicted_step_mhz: float
    excess_mhz: float
    sigma_mhz: float
    z_score: float

    @property
    def exceeds_floor_2sigma(self) -> bool:
        return abs(self.z_score) > 2.0


@dataclass(frozen=True)
class RatioResult:
    ratio: float  # d14/h14 slope ratio
    sigma: float
    provenance: str


def load_digitized(csv_path: Path = DEFAULT_CSV) -> dict[str, PowerSeries]:
    """Parse the CSV, enforcing its provenance header. The archive gate runs
    first: derived data is only trusted while raw/ verifies."""
    require_intact()
    text = csv_path.read_text(encoding="utf-8")
    header_lines = [ln for ln in text.splitlines() if ln.startswith("#")]
    header = "\n".join(header_lines)
    for fragment in REQUIRED_HEADER_FRAGMENTS:
        if fragment not in header:
            raise ValueError(
                f"{csv_path.name}: provenance header missing {fragment!r} — "
                "refusing to fit ungraded data"
            )

    rows: dict[str, list[tuple[float, float]]] = {}
    data_lines = [ln for ln in text.splitlines() if ln and not ln.startswith("#")]
    if data_lines[0].strip() != "sample,power_mW,f_peak_MHz":
        raise ValueError(f"{csv_path.name}: unexpected column header {data_lines[0]!r}")
    for line in data_lines[1:]:
        sample, power, freq = line.split(",")
        rows.setdefault(sample, []).append((float(power), float(freq)))

    series = {}
    for sample, pairs in rows.items():
        pairs.sort()
        powers, freqs = zip(*pairs)
        series[sample] = PowerSeries(
            sample=sample,
            powers_mw=np.asarray(powers),
            f_peak_mhz=np.asarray(freqs),
            sigma_mhz=DIGITIZED_SIGMA_MHZ,
            provenance=PROVENANCE_STAMP,
        )
    return series


def wls_line(x: np.ndarray, y: np.ndarray, sigma: float):
    """WLS straight line under a uniform per-point σ (closed form).

    Returns (slope, intercept, slope_sigma, intercept_sigma, chi2, dof).
    Parameter errors are σ-propagated, not residual-scaled (module
    docstring): σ_slope = σ/√Sxx, σ_intercept = σ·√(1/n + x̄²/Sxx).
    """
    n = len(x)
    if n < 3:
        raise ValueError("need at least 3 points for a slope + lack-of-fit dof")
    x_bar, y_bar = float(np.mean(x)), float(np.mean(y))
    dx = x - x_bar
    s_xx = float(np.dot(dx, dx))
    slope = float(np.dot(dx, y - y_bar) / s_xx)
    intercept = y_bar - slope * x_bar
    residuals = y - (intercept + slope * x)
    chi2 = float(np.dot(residuals, residuals) / sigma**2)
    slope_sigma = sigma / math.sqrt(s_xx)
    intercept_sigma = sigma * math.sqrt(1.0 / n + x_bar**2 / s_xx)
    return slope, intercept, slope_sigma, intercept_sigma, chi2, n - 2


def fit_sample(series: PowerSeries) -> SlopeFit:
    slope, intercept, slope_sigma, intercept_sigma, chi2, dof = wls_line(
        series.powers_mw, series.f_peak_mhz, series.sigma_mhz
    )
    return SlopeFit(
        sample=series.sample,
        slope_mhz_per_mw=slope,
        slope_sigma_mhz_per_mw=slope_sigma,
        intercept_mhz=intercept,
        intercept_sigma_mhz=intercept_sigma,
        chi2=chi2,
        dof=dof,
        n_points=len(series.powers_mw),
        provenance=series.provenance,
    )


def slope_ratio(fit_d14: SlopeFit, fit_h14: SlopeFit) -> RatioResult:
    """d14/h14 slope ratio with first-order error propagation."""
    ratio = fit_d14.slope_mhz_per_mw / fit_h14.slope_mhz_per_mw
    rel = math.hypot(
        fit_d14.slope_sigma_mhz_per_mw / fit_d14.slope_mhz_per_mw,
        fit_h14.slope_sigma_mhz_per_mw / fit_h14.slope_mhz_per_mw,
    )
    return RatioResult(ratio=ratio, sigma=abs(ratio) * rel, provenance=PROVENANCE_STAMP)


def step_test(series: PowerSeries, fit: SlopeFit, step_powers_mw=H14_STEP_POWERS_MW) -> StepTest:
    """The single-step nonlinearity check (h14, 10.16→12.33 mW by default)."""
    p_lo, p_hi = step_powers_mw
    idx_lo = int(np.argmin(np.abs(series.powers_mw - p_lo)))
    idx_hi = int(np.argmin(np.abs(series.powers_mw - p_hi)))
    if not (
        math.isclose(series.powers_mw[idx_lo], p_lo)
        and math.isclose(series.powers_mw[idx_hi], p_hi)
    ):
        raise ValueError(f"step powers {step_powers_mw} not in the {series.sample} trace")
    observed = float(series.f_peak_mhz[idx_hi] - series.f_peak_mhz[idx_lo])
    delta_p = p_hi - p_lo
    predicted = fit.slope_mhz_per_mw * delta_p
    # two digitized points + the slope's own uncertainty over ΔP; the
    # step/fit correlation is neglected (approximate — see module docstring)
    sigma = math.sqrt(
        2.0 * series.sigma_mhz**2 + (delta_p * fit.slope_sigma_mhz_per_mw) ** 2
    )
    excess = observed - predicted
    return StepTest(
        observed_step_mhz=observed,
        predicted_step_mhz=predicted,
        excess_mhz=excess,
        sigma_mhz=sigma,
        z_score=excess / sigma,
    )


@dataclass(frozen=True)
class SlopeFitResults:
    fits: dict[str, SlopeFit]
    ratio: RatioResult
    h14_step: StepTest


def fit_all(csv_path: Path = DEFAULT_CSV) -> SlopeFitResults:
    series = load_digitized(csv_path)
    fits = {name: fit_sample(s) for name, s in series.items()}
    return SlopeFitResults(
        fits=fits,
        ratio=slope_ratio(fits["d14"], fits["h14"]),
        h14_step=step_test(series["h14"], fits["h14"]),
    )


def render_report(results: SlopeFitResults) -> str:
    r, step = results.ratio, results.h14_step
    lines = [
        "# T3 — digitized ODMR slope fits (Cowley-Semple 2026-07-14 dataset)",
        "",
        f"**Provenance: {PROVENANCE_STAMP}** — re-fit from raw traces when they land.",
        f"Error model: uniform ±{DIGITIZED_SIGMA_MHZ} MHz per point (0.1 MHz plot",
        "quantization); parameter errors are floor-propagated, not residual-scaled.",
        "",
        "| sample | n | slope (MHz/mW) | χ²/dof |",
        "|---|---|---|---|",
    ]
    for name in ("d14", "h14"):
        f = results.fits[name]
        lines.append(
            f"| {name} | {f.n_points} | {f.slope_mhz_per_mw:+.4f} ± "
            f"{f.slope_sigma_mhz_per_mw:.4f} | {f.chi2:.2f}/{f.dof} = {f.chi2_per_dof:.2f} |"
        )
    lines += [
        "",
        f"**Slope ratio d14/h14 = {r.ratio:.3f} ± {r.sigma:.3f}** (first-order propagation).",
        "",
        "## h14 nonlinearity check (single step, 10.16 → 12.33 mW)",
        "",
        f"- observed step: {step.observed_step_mhz:+.2f} MHz",
        f"- linear prediction: {step.predicted_step_mhz:+.3f} MHz",
        f"- excess: {step.excess_mhz:+.3f} MHz at σ_step = {step.sigma_mhz:.3f} MHz "
        f"⇒ z = {step.z_score:+.2f}",
        f"- verdict: the step **{'EXCEEDS' if step.exceeds_floor_2sigma else 'does NOT exceed'}** "
        "the ±0.05 MHz error floor at 2σ. The z-score neglects the step/fit "
        "correlation (approximate); the per-sample χ²/dof above is the primary "
        f"lack-of-fit statistic. {QUANTIZATION_CAVEAT}",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # cp1252 console
    args = list(sys.argv[1:] if argv is None else argv)
    csv_path = Path(args[0]) if args else DEFAULT_CSV
    results = fit_all(csv_path)
    report = render_report(results)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"[written to {DEFAULT_REPORT}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
