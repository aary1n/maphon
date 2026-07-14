"""T5 — absolute fits: η_abs·R_int per sample and the observable-a feed.

Chain (all magnitudes; signs are both negative and cancel):

    |slope|  =  |df_spin/dT| · η_abs · Θ        [Hz/W]

with Θ = dT/dP_abs from the T2 rig model (R_int, the rig thermal
resistance seen by the ODMR probe) and η_abs the absorbed fraction of the
trace-labelled power. The measured product is therefore

    η_abs · R_int  =  |slope| / |df_spin/dT|    [K/W]

— the FEASIBLE dT/dP band per sample once |df_spin/dT| is pinned.

df_spin/dT source (RATIFICATION CONDITION 3, 2026-07-14): the graded
`provenance.DF_SPIN_DT` — point −109 kHz/K, band [−120, −64] kHz/K
(raw-data re-grade 2026-07-07, SPEC §6T). The task prompt's
"−50 to −108 kHz/K" band was OVERRULED as a stale quote: −50 kHz/K was
retired from band duty (outside the graded band), and −108 is ≈ the
face-value point, not an edge.

Band composition, stated: the coefficient band dominates (×1.875 across
it) over the slope's ~8% relative error; the feasible band below is the
coefficient-band envelope evaluated at slope ∓1σ (band_lo uses
|slope|−σ with the steep coefficient edge, band_hi uses |slope|+σ with
the shallow edge).

Deuteration asymmetry (carried per sample): Singh's crystal is PROTONATED
— the h14 fit is the clean one; d14 inherits the deuteration-transfer
caveat (df/dT transfer to Pc-d₁₄:PTP-d₁₄ assumed, unverified by any
measurement in hand; SPEC §6T). The T4 geometry-sufficient verdict is
consistent with a small deuteration effect but does not prove it absent.

η_abs feasibility: η_abs = (η_abs·R_int)/Θ ≤ 1 requires Θ ≥ η_abs·R_int —
each T2 sweep configuration either admits a physical absorbed fraction or
is excluded; the feasible fraction of the sweep is reported.

Output: markdown report + `observable_a_feed.json`, the machine-readable
block SPEC §7.T5(a) consumes, grades stamped throughout.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from calibration.ratio_test import run_ratio_test
from calibration.rig_model import sweep_sample
from calibration.samples import SAMPLES, default_grid
from calibration.slope_fit import fit_all
from cavity.provenance.constants import DF_SPIN_DT

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_REPORT = _PACKAGE_DIR / "reports" / "absolute_fit_digitized.md"
DEFAULT_JSON = _PACKAGE_DIR / "reports" / "observable_a_feed.json"

MHZ_PER_MW_TO_HZ_PER_W = 1e9  # 1 MHz/mW = 1e6 Hz / 1e-3 W

DF_DT_SOURCE_NOTE = (
    "provenance.DF_SPIN_DT (raw-data re-grade 2026-07-07): point -109 kHz/K, "
    "band [-120, -64] kHz/K. Prompt band '-50 to -108 kHz/K' overruled as "
    "stale (ratification condition 3, 2026-07-14)."
)


@dataclass(frozen=True)
class AbsoluteFit:
    """η_abs·R_int (= feasible dT/dP of absorbed... see docstring) for one sample."""

    sample: str
    slope_hz_per_w: float
    slope_sigma_hz_per_w: float
    eta_r_point_k_per_w: float  # |slope| / |df_dt point|
    eta_r_band_lo_k_per_w: float  # (|slope|-sigma) / |df_dt band-steep edge|
    eta_r_band_hi_k_per_w: float  # (|slope|+sigma) / |df_dt band-shallow edge|
    heating_at_max_power_k: float  # probe-inferred ΔT at the trace maximum:
    # |slope|·P_max/|df_dt| — the triplet-thermometer reading, η_abs-FREE
    # (the measured product is what enters; no absorption assumption)
    feasible_sweep_fraction: float  # share of T2 configs with eta_abs <= 1
    eta_abs_at_nominal_config: float
    deuteration_caveat: str


def absolute_fit_sample(name: str, fit, theta_grid: np.ndarray) -> AbsoluteFit:
    slope = abs(fit.slope_mhz_per_mw) * MHZ_PER_MW_TO_HZ_PER_W
    sigma = fit.slope_sigma_mhz_per_mw * MHZ_PER_MW_TO_HZ_PER_W
    df_point = abs(DF_SPIN_DT.df_dt_hz_per_k)
    df_steep = abs(DF_SPIN_DT.df_dt_band_lo_hz_per_k)  # -120 kHz/K edge
    df_shallow = abs(DF_SPIN_DT.df_dt_band_hi_hz_per_k)  # -64 kHz/K edge

    point = slope / df_point
    band_lo = (slope - sigma) / df_steep
    band_hi = (slope + sigma) / df_shallow

    max_power_w = max(SAMPLES[name].powers_mw) * 1e-3
    # eta_abs <= 1 feasibility across the sweep, judged at the point value
    eta_abs = point / theta_grid
    feasible = float(np.mean(eta_abs <= 1.0))
    # nominal config = the grid's central Theta (median as the robust centre)
    eta_nominal = float(point / np.median(theta_grid))

    caveat = (
        "clean: protonated sample matches the protonated Singh crystal"
        if not SAMPLES[name].deuterated
        else "deuteration-transfer caveat: df/dT measured on protonated Pc:PTP, "
        "applied to Pc-d14:PTP-d14 (assumed transferable, unverified; SPEC 6T)"
    )
    return AbsoluteFit(
        sample=name,
        slope_hz_per_w=slope,
        slope_sigma_hz_per_w=sigma,
        eta_r_point_k_per_w=point,
        eta_r_band_lo_k_per_w=band_lo,
        eta_r_band_hi_k_per_w=band_hi,
        heating_at_max_power_k=point * max_power_w,
        feasible_sweep_fraction=feasible,
        eta_abs_at_nominal_config=eta_nominal,
        deuteration_caveat=caveat,
    )


@dataclass(frozen=True)
class ObservableAFeed:
    """The deliverable block for SPEC §7.T5 observable (a)."""

    provenance: str
    df_dt_source: str
    fits: dict[str, AbsoluteFit]
    t4_verdict: str
    t4_measured_ratio: float
    t4_measured_sigma: float

    def to_json(self) -> str:
        payload = {
            "workstream": "layer-b-calibration/observable-a",
            "dataset": "cowley_semple_2026-07-14 (digitized)",
            "provenance": self.provenance,
            "df_dt_source": self.df_dt_source,
            "samples": {name: asdict(fit) for name, fit in self.fits.items()},
            "t4_ratio_test": {
                "verdict": self.t4_verdict,
                "measured_ratio_d14_over_h14": self.t4_measured_ratio,
                "measured_sigma": self.t4_measured_sigma,
            },
            "units": {
                "slope": "Hz/W (trace-labelled power; measurement plane = open Angus ask)",
                "eta_r": "K/W (eta_abs x R_int; feasible dT/dP of labelled power)",
                "heating_at_max_power": "K (probe-inferred dT at the trace maximum, eta_abs-free)",
            },
        }
        return json.dumps(payload, indent=2)


def run_absolute_fits() -> ObservableAFeed:
    fits = fit_all()
    grid = default_grid()
    ratio_result = run_ratio_test(grid)
    out: dict[str, AbsoluteFit] = {}
    for name in ("d14", "h14"):
        theta = sweep_sample(SAMPLES[name], grid).theta_k_per_w
        out[name] = absolute_fit_sample(name, fits.fits[name], theta.ravel())
    return ObservableAFeed(
        provenance=fits.ratio.provenance,
        df_dt_source=DF_DT_SOURCE_NOTE,
        fits=out,
        t4_verdict=ratio_result.verdict,
        t4_measured_ratio=ratio_result.measured_ratio,
        t4_measured_sigma=ratio_result.measured_sigma,
    )


def render_report(feed: ObservableAFeed) -> str:
    lines = [
        "# T5 — absolute fits: η_abs·R_int per sample (observable-a feed)",
        "",
        f"**Provenance: {feed.provenance}**",
        "",
        f"df_spin/dT: {feed.df_dt_source}",
        "",
        "| sample | slope (Hz/W) | η_abs·R_int point (K/W) | feasible band (K/W) | "
        "probe-inferred ΔT at max trace power (K) | sweep feasible (η_abs ≤ 1) | caveat |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in ("d14", "h14"):
        f = feed.fits[name]
        lines.append(
            f"| {name} | {f.slope_hz_per_w:.3g} ± {f.slope_sigma_hz_per_w:.2g} | "
            f"{f.eta_r_point_k_per_w:.0f} | [{f.eta_r_band_lo_k_per_w:.0f}, "
            f"{f.eta_r_band_hi_k_per_w:.0f}] | {f.heating_at_max_power_k:.1f} | "
            f"{100 * f.feasible_sweep_fraction:.0f}% | {f.deuteration_caveat.split(':')[0]} |"
        )
    lines += [
        "",
        "Band composition: coefficient-band envelope (×1.875 across the §6T band)",
        "evaluated at slope ∓1σ — the coefficient dominates the slope error.",
        "",
        "The ΔT column is the PROBE-INFERRED heating at the trace maximum",
        "(|slope|·P_max/|df_dt| — the triplet-thermometer reading, no absorption",
        "assumption enters): the 'several tens of K' class of Oxborrow's in-thread",
        "inference is reproduced at order of magnitude, not tuned to (13–24 K",
        "across the coefficient band at 14.39 mW).",
        "",
        f"## T4 verdict carried into the feed: **{feed.t4_verdict}**",
        "",
        f"(measured d14/h14 ratio {feed.t4_measured_ratio:.3f} ± "
        f"{feed.t4_measured_sigma:.3f}; see ratio_test_digitized.md)",
        "",
        "Deuteration asymmetry: h14 is the CLEAN absolute fit (protonated, matches",
        "the Singh crystal); d14 carries the deuteration-transfer caveat in full.",
        "",
        "Machine-readable feed: observable_a_feed.json (same directory).",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # cp1252 console
    feed = run_absolute_fits()
    report = render_report(feed)
    DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT.write_text(report, encoding="utf-8")
    DEFAULT_JSON.write_text(feed.to_json(), encoding="utf-8")
    print(report)
    print(f"[written to {DEFAULT_REPORT} and {DEFAULT_JSON}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
