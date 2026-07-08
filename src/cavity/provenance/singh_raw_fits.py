"""SPEC §6T — reproducible fits of the Singh 2025 raw Fig. 2B data.

Single quantitative route from the archived raw files
(refs/singh_2025_raw/, byte-for-byte as received 2026-07-07 from
Harpreet Singh, first author — see PROVENANCE.md there) to the graded
`SpinFreqTempCoefficient` fields in `cavity.provenance.constants`.
Ordinary least squares per window; slope uncertainty from residuals
(sigma^2 = SSR/(n-2)); the 0.1 MHz frequency quantisation enters as an
explicit per-point floor sigma_q = 0.1/sqrt(12) MHz and a
quantisation-only slope SE reported per window.

Everything here is deterministic and file-driven: no interactive
state, no RNG, numpy only. The emitted report is committed at
refs/singh_2025_raw/fit_report.md; regenerating it must be
byte-identical. Window fits are pinned in
tests/test_provenance_df_spin_dt.py, which also asserts the graded
constant equals `point_window_fit()` (band endpoints are checked
THROUGH `band_lo_window_fit()` / `band_hi_window_fit()` at test time,
never against stored endpoint literals — same discipline as the
df_cavity/dT guards).

Temperature-axis convention (load-bearing, SPEC §6T): all windows are
on the FILE axis. The published Fig. 2B(iii) axis relates to it by an
exact affine map (`affine_map_vs_extraction`); which side carries the
calibrated sensor reading is UNRESOLVED pending Harpreet metadata —
do not treat either axis as settled.

Usage:  python -m cavity.provenance.singh_raw_fits [--out refs/singh_2025_raw]
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "refs" / "singh_2025_raw"
XZ_FILE = DATA_DIR / "Fig2B_(iii)XZ_xztemp.txt"
XY_FILE = DATA_DIR / "Fig2B(i)_XY_XYdata.txt"
YZ_FILE = DATA_DIR / "Fig2B(ii)_YZ_YZdata.txt"
EXTRACTION_CSV = REPO_ROOT / "refs" / "singh_fig2biii_vector_extraction.csv"

# Frequency values in all three files sit on a 0.1 MHz grid (verified:
# every consecutive difference is a multiple). Uniform-quantisation
# noise model: sigma_q = LSB / sqrt(12).
FREQ_QUANTUM_MHZ = 0.1
SIGMA_QUANT_MHZ = FREQ_QUANTUM_MHZ / math.sqrt(12.0)

# The paper identifies the triclinic->monoclinic transition at 193 K
# absolute; its location in the raw XZ series (largest positive
# frequency jump) anchors the cold-finger-branch offset.
T_TRANSITION_ABS_K = 193.0

# Operating-temperature window on the FILE axis (face-value branch).
# The numerals matched CavityFreqTempCoefficient's then-293-310 K
# planning envelope at grading time (2026-07-07); the cavity envelope
# has since widened to 293-323 K (Oxborrow-verbal, 2026-07-08) — this
# fit window is a raw-data grading choice and deliberately unchanged.
# Under the cold-finger branch the same actual window maps down by
# `coldfinger_offset_k()`.
T_WINDOW_LO_K = 293.0
T_WINDOW_HI_K = 310.0

# Steepest defensible operating-adjacent window: from the operating
# floor to the top of the data (sliding-window slopes are monotone
# steepening, so this bounds the local slope from below/steep side).
BAND_LO_WINDOW_K = (290.0, 330.0)


@dataclass(frozen=True)
class WindowFit:
    """OLS slope of frequency vs temperature over [t_lo_k, t_hi_k]."""

    label: str
    t_lo_k: float
    t_hi_k: float
    slope_khz_per_k: float
    se_khz_per_k: float          # residual-based (includes quantisation)
    se_quant_khz_per_k: float    # quantisation-only floor
    rmse_khz: float
    n: int

    @property
    def slope_hz_per_k(self) -> float:
        return self.slope_khz_per_k * 1e3


@dataclass(frozen=True)
class AffineAxisMap:
    """Affine relation between the Fig. 2B(iii) figure axis and the
    raw-file axis, from rank-order pairing of the two 197-point sets.

    t_fig = scale * t_raw + offset_k. Which axis is the calibrated
    sensor reading is UNRESOLVED (see PROVENANCE.md) — this map states
    that the two DIFFER, not which is right.
    """

    scale: float
    offset_k: float
    rms_resid_k: float           # about the affine map (temperature)
    freq_resid_mean_khz: float   # figure minus raw, frequency
    freq_resid_rms_khz: float
    n: int

    @property
    def slope_inflation(self) -> float:
        """Factor by which figure-axis slopes exceed raw-axis slopes."""
        return 1.0 / self.scale

    def fig_to_raw(self, t_fig_k: float) -> float:
        return (t_fig_k - self.offset_k) / self.scale


def load_series(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Two whitespace-separated columns; '#' header and blank lines skipped."""
    temps, freqs = [], []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) == 2:
            temps.append(float(parts[0]))
            freqs.append(float(parts[1]))
    return np.asarray(temps), np.asarray(freqs)


def load_xz() -> tuple[np.ndarray, np.ndarray]:
    return load_series(XZ_FILE)


def load_xy() -> tuple[np.ndarray, np.ndarray]:
    return load_series(XY_FILE)


def load_yz() -> tuple[np.ndarray, np.ndarray]:
    return load_series(YZ_FILE)


def quantisation_se_khz_per_k(t_k: np.ndarray) -> float:
    """Slope SE if the only noise were the 0.1 MHz quantisation."""
    n = len(t_k)
    sd = float(np.std(t_k))
    return SIGMA_QUANT_MHZ / (sd * math.sqrt(n)) * 1e3


def ols_slope(
    t_k: np.ndarray,
    f_mhz: np.ndarray,
    t_lo_k: float,
    t_hi_k: float,
    label: str = "",
) -> WindowFit:
    mask = (t_k >= t_lo_k) & (t_k <= t_hi_k)
    t, f = t_k[mask], f_mhz[mask]
    n = len(t)
    if n < 3:
        raise ValueError(f"window [{t_lo_k}, {t_hi_k}] has n={n} < 3 points")
    design = np.vstack([t, np.ones(n)]).T
    coef, *_ = np.linalg.lstsq(design, f, rcond=None)
    resid = f - design @ coef
    s2 = float(resid @ resid) / (n - 2)
    cov = s2 * np.linalg.inv(design.T @ design)
    return WindowFit(
        label=label,
        t_lo_k=t_lo_k,
        t_hi_k=t_hi_k,
        slope_khz_per_k=float(coef[0]) * 1e3,
        se_khz_per_k=float(np.sqrt(cov[0, 0])) * 1e3,
        se_quant_khz_per_k=quantisation_se_khz_per_k(t),
        rmse_khz=float(np.sqrt(np.mean(resid**2))) * 1e3,
        n=n,
    )


def transition_midpoint_k(t_k: np.ndarray, f_mhz: np.ndarray) -> float:
    """Midpoint of the largest positive frequency jump below 200 K —
    the triclinic->monoclinic feature (XZ: +0.9 MHz at 130.4-133.6)."""
    low = t_k < 200.0
    t, f = t_k[low], f_mhz[low]
    jumps = np.diff(f)
    i = int(np.argmax(jumps))
    return float((t[i] + t[i + 1]) / 2.0)


def coldfinger_offset_k() -> float:
    """Laser-heating offset ON THE FILE AXIS, conditional on the
    paper's abs-193 K identification of the transition holding and on
    the file axis being a cold-finger-class sensor (the unresolved
    branch): offset = 193 - (file-axis transition midpoint) at the
    stated 110 mW cw."""
    t, f = load_xz()
    return T_TRANSITION_ABS_K - transition_midpoint_k(t, f)


def affine_map_vs_extraction() -> AffineAxisMap:
    """Pair the raw XZ points with the archived vector-extraction
    marker centres by rank order in T and fit t_fig = a*t_raw + b.

    The frequency residual rms sitting at the quantisation floor
    (~29-40 kHz, vs ~450 kHz if the pairing slipped one point in the
    -0.1 MHz/K region) is the internal proof the pairing is correct.
    """
    rows = [
        line.split(",")
        for line in EXTRACTION_CSV.read_text().splitlines()[1:]
        if line.strip()
    ]
    vec = np.array([(float(a), float(b)) for a, b in rows])
    t_raw, f_raw = load_xz()
    if len(vec) != len(t_raw):
        raise ValueError(
            f"extraction N={len(vec)} != raw N={len(t_raw)}; rank pairing invalid"
        )
    order_raw = np.argsort(t_raw)
    order_vec = np.argsort(vec[:, 0])
    tr, fr = t_raw[order_raw], f_raw[order_raw]
    tv, fv = vec[order_vec, 0], vec[order_vec, 1]
    scale, offset = np.polyfit(tr, tv, 1)
    resid_t = tv - (scale * tr + offset)
    resid_f = (fv - fr) * 1e3
    return AffineAxisMap(
        scale=float(scale),
        offset_k=float(offset),
        rms_resid_k=float(np.sqrt(np.mean(resid_t**2))),
        freq_resid_mean_khz=float(np.mean(resid_f)),
        freq_resid_rms_khz=float(np.sqrt(np.mean(resid_f**2))),
        n=len(tr),
    )


def point_window_fit() -> WindowFit:
    """The graded point value's window: file-axis 293-310 K (the
    face-value branch — see SpinFreqTempCoefficient's branch-choice
    note)."""
    t, f = load_xz()
    return ols_slope(t, f, T_WINDOW_LO_K, T_WINDOW_HI_K, "operating 293-310 (point)")


def band_lo_window_fit() -> WindowFit:
    """Steepest operating-adjacent window -> band lo (most negative)."""
    t, f = load_xz()
    return ols_slope(t, f, *BAND_LO_WINDOW_K, "steepest 290-330 (band lo)")


def band_hi_window_fit() -> WindowFit:
    """Cold-finger branch: actual 293-310 K mapped down by the
    file-axis offset -> band hi (least negative)."""
    t, f = load_xz()
    off = coldfinger_offset_k()
    return ols_slope(
        t, f, T_WINDOW_LO_K - off, T_WINDOW_HI_K - off,
        "cold-finger branch (band hi)",
    )


def xz_window_fits() -> list[WindowFit]:
    """The canonical XZ fit table (SPEC §6T; all on the file axis)."""
    t, f = load_xz()
    amap = affine_map_vs_extraction()
    fits = [
        ols_slope(t, f, 150.0, 330.0, "region-III proxy, raw-axis 150-330"),
        ols_slope(
            t, f, amap.fig_to_raw(150.0), amap.fig_to_raw(330.0),
            "figure-axis 150-330 back-mapped",
        ),
        ols_slope(t, f, 254.0, 324.0, "drawn-red-line span 254-324"),
        ols_slope(t, f, 254.0, 330.0, "254-330"),
        ols_slope(t, f, 290.0, 310.0, "operating 290-310"),
        point_window_fit(),
        band_lo_window_fit(),
        band_hi_window_fit(),
    ]
    return fits


def sliding_window_fits(width_k: float = 30.0, step_k: float = 15.0) -> list[WindowFit]:
    t, f = load_xz()
    fits = []
    lo = 150.0
    while lo + width_k <= 330.0 + 1e-9:
        mask = (t >= lo) & (t <= lo + width_k)
        if int(mask.sum()) >= 10:
            fits.append(ols_slope(t, f, lo, lo + width_k, "sliding"))
        lo += step_k
    return fits


def quadratic_local_slopes(
    t_lo_k: float = 254.0, t_hi_k: float = 324.0
) -> dict[str, float]:
    """Quadratic-in-T fit over the red-line span; local slopes (kHz/K)
    at the ends and centre plus the curvature 2a (kHz/K^2)."""
    t, f = load_xz()
    mask = (t >= t_lo_k) & (t <= t_hi_k)
    a, b, _ = np.polyfit(t[mask], f[mask], 2)
    out = {"curvature_2a_khz_per_k2": 2.0 * a * 1e3}
    for at in (t_lo_k, 290.0, t_hi_k):
        out[f"slope_at_{at:.0f}K_khz_per_k"] = (2.0 * a * at + b) * 1e3
    return out


def _fit_rows(fits: list[WindowFit]) -> str:
    lines = [
        "| window (file axis, K) | slope (kHz/K) | ±SE | quant-only SE | RMSE (kHz) | n |",
        "|---|---|---|---|---|---|",
    ]
    for w in fits:
        lines.append(
            f"| {w.t_lo_k:.1f}–{w.t_hi_k:.1f} — {w.label} | {w.slope_khz_per_k:+.1f} "
            f"| {w.se_khz_per_k:.1f} | {w.se_quant_khz_per_k:.2f} "
            f"| {w.rmse_khz:.0f} | {w.n} |"
        )
    return "\n".join(lines)


def fit_report_markdown() -> str:
    amap = affine_map_vs_extraction()
    t_xz, f_xz = load_xz()
    t_xy, f_xy = load_xy()
    t_yz, f_yz = load_yz()
    off = coldfinger_offset_k()
    mid = transition_midpoint_k(t_xz, f_xz)
    quad = quadratic_local_slopes()
    point = point_window_fit()
    lo = band_lo_window_fit()
    hi = band_hi_window_fit()

    sliding = "\n".join(
        f"| {w.t_lo_k:.0f}–{w.t_hi_k:.0f} | {w.slope_khz_per_k:+.1f} ± {w.se_khz_per_k:.1f} | {w.n} |"
        for w in sliding_window_fits()
    )

    xy_fits = [
        ols_slope(t_xy, f_xy, 150.0, 330.0, "region-III proxy"),
        ols_slope(t_xy, f_xy, 254.0, 324.0, "red-line-span equivalent"),
    ]
    yz_fits = [
        ols_slope(t_yz, f_yz, 150.0, 306.0, "150-306 (top of data)"),
        ols_slope(t_yz, f_yz, 254.0, 306.0, "254-306"),
    ]

    return f"""# Singh 2025 raw Fig. 2B — fit report

Generated by `python -m cavity.provenance.singh_raw_fits` (deterministic; regeneration
must be byte-identical). Data: the archived raw files in this directory (see
PROVENANCE.md — byte-for-byte as received 2026-07-07, SHA-256-pinned in
`tests/test_provenance_df_spin_dt.py`). Method: ordinary least squares per window,
slope SE from residuals (σ² = SSR/(n−2)). All windows on the FILE temperature axis;
which axis (file vs published figure) carries the calibrated sensor reading is
UNRESOLVED — see the affine-map section below and PROVENANCE.md.

**Frequency quantisation:** all files sit on a {FREQ_QUANTUM_MHZ:.1f} MHz grid ⇒
per-point floor σ_q = {SIGMA_QUANT_MHZ * 1e3:.1f} kHz. It enters the fit uncertainty
through the residuals (narrow-window RMSE sits just above this floor); the
quantisation-only slope SE is tabulated per window. Statistical + quantisation
uncertainty is 1–3 kHz/K throughout — dwarfed by the axis-branch/window systematic.

## X–Z (1.45 GHz, the maser transition) — canonical window fits

{_fit_rows(xz_window_fits())}

## X–Z curvature

Quadratic over 254–324: local slope {quad['slope_at_254K_khz_per_k']:+.1f} (254 K) →
{quad['slope_at_290K_khz_per_k']:+.1f} (290 K) → {quad['slope_at_324K_khz_per_k']:+.1f} (324 K) kHz/K;
curvature 2a = {quad['curvature_2a_khz_per_k2']:+.2f} kHz/K².

30 K sliding windows (monotone steepening — never use any single window as a global fit):

| window (K) | slope (kHz/K) | n |
|---|---|---|
{sliding}

## Figure-axis ↔ file-axis affine map (symmetric — neither side settled)

Rank-order pairing of the {amap.n} raw X–Z points with the {amap.n} vector-extraction
marker centres (`../singh_fig2biii_vector_extraction.csv`):

- **T_fig = {amap.scale:.4f}·T_raw + {amap.offset_k:.2f} K** (rms residual {amap.rms_resid_k:.2f} K).
- Frequency residuals (fig − raw): mean {amap.freq_resid_mean_khz:+.1f} kHz, rms
  {amap.freq_resid_rms_khz:.1f} kHz ≈ the quantisation floor — the pairing is correct
  (a one-point slip in the −0.1 MHz/K region would read ~450 kHz).
- Slopes in figure-axis units are inflated ×{amap.slope_inflation:.3f} relative to the
  file axis. This reconciles the three-way dispute: printed −101 ≈ raw OLS over the
  red-line span ({[w for w in xz_window_fits() if w.label.startswith('drawn')][0].slope_khz_per_k:+.1f} ± 1.1);
  the re-digitised −112 is a faithful reading of the figure whose axis differs from the
  file's by the map above. **The two axes differ by an exact affine map; which side
  carries the calibrated sensor reading is unresolved** (Harpreet ask — PROVENANCE.md).

## Cold-finger-branch offset (conditional)

Largest positive frequency jump in the raw X–Z series (the 193 K-absolute transition):
midpoint T_file = {mid:.1f} K ⇒ offset = {off:.1f} K at 110 mW cw, **conditional on**
(i) the paper's abs-193 K identification and (ii) the file axis being a
cold-finger-class sensor (the unresolved branch).

## Graded-constant derivation (SpinFreqTempCoefficient, SPEC §6T)

- **Point** = {point.slope_khz_per_k:+.1f} ± {point.se_khz_per_k:.1f} kHz/K over file-axis
  {point.t_lo_k:.0f}–{point.t_hi_k:.0f} K → stored −1.09e5 Hz/K (3 s.f.). **Branch choice,
  not a best estimate**: takes the file axis at face value (conservative branch —
  steeper ⇒ smaller thermal margin).
- **Band lo** = steepest operating-adjacent window, {lo.t_lo_k:.0f}–{lo.t_hi_k:.0f}:
  {lo.slope_khz_per_k:+.1f} ± {lo.se_khz_per_k:.1f} → stored −1.2e5 Hz/K (outward, 2 s.f.).
- **Band hi** = cold-finger branch, file-axis {hi.t_lo_k:.1f}–{hi.t_hi_k:.1f}
  (= actual 293–310 K under the +{off:.0f} K offset): {hi.slope_khz_per_k:+.1f} ±
  {hi.se_khz_per_k:.1f} → stored −6.4e4 Hz/K (outward, 2 s.f.).

## X–Y and Y–Z (archived + audited; NO constants derive from these)

X–Y (~107 MHz): {xy_fits[0].slope_khz_per_k:+.1f} ± {xy_fits[0].se_khz_per_k:.1f} kHz/K over 150–330
(n={xy_fits[0].n}); {xy_fits[1].slope_khz_per_k:+.1f} ± {xy_fits[1].se_khz_per_k:.1f} over 254–324. Consistent with SI
Table S1's footnoted +8.7 high-T sub-slope after axis-map correction.

Y–Z (~1.34 GHz): {yz_fits[0].slope_khz_per_k:+.1f} ± {yz_fits[0].se_khz_per_k:.1f} kHz/K over 150–306
(n={yz_fits[0].n}); {yz_fits[1].slope_khz_per_k:+.1f} ± {yz_fits[1].se_khz_per_k:.1f} over 254–306. Visibly noisier
(RMSE {yz_fits[1].rmse_khz:.0f} kHz; median per-0.1 MHz-bin temperature span ≈ 21 K near RT);
no data above {t_yz.max():.1f} K.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=DATA_DIR,
        help="output directory for fit_report.md (default: the archive dir)",
    )
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / "fit_report.md"
    path.write_text(fit_report_markdown(), encoding="utf-8", newline="\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
