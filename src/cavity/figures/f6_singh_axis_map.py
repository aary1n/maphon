"""F6 — provenance of the spin-arm coefficient (Singh two-axis map).

Data source (disk — the raw data IS in the repo):
`refs/singh_2025_raw/Fig2B_(iii)XZ_xztemp.txt` (SHA-256-pinned) +
`refs/singh_fig2biii_vector_extraction.csv`, both loaded through
`cavity.provenance.singh_raw_fits` (`load_xz`, `ols_slope`,
`point/band_lo/band_hi_window_fit`, `affine_map_vs_extraction`). The
affine-map parameters (0.9316 / 16.56 K) are COMPUTED at figure-build
time, never hard-coded; the 197 re-digitised figure points are mapped
through the INVERSE affine map onto the raw axis.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from cavity.provenance.constants import DF_SPIN_DT
from cavity.provenance.singh_raw_fits import (
    EXTRACTION_CSV,
    affine_map_vs_extraction,
    band_hi_window_fit,
    band_lo_window_fit,
    load_xz,
    ols_slope,
    point_window_fit,
)

PRINTED_SLOPE_KHZ_PER_K = -101.0  # Singh main text p. 3 / SI Table S1 (bare)

CAPTION = (
    "Provenance of the spin-arm coefficient: the Singh et al., Nat. Commun. 16, "
    "10530 (2025) Fig. 2B(iii) X–Z series exists in two temperature axes related by an exact affine map, "
    "T_fig = 0.9316·T_raw + 16.56 K (rms 0.09 K; recomputed at render time by "
    "`cavity.provenance.singh_raw_fits` from the two committed point sets). Left: the raw point series "
    "(`refs/singh_2025_raw/`, byte-for-byte as received from the first author, SHA-256-pinned; "
    "plotted-point exports, not raw acquisition; 0.1 MHz quantisation) with window fits; overlaid, the "
    "197 re-digitised figure points (`refs/singh_fig2biii_vector_extraction.csv`) mapped through the "
    "affine map — coincident at the quantisation floor. Right: slope vs fit window — the paper's printed "
    "−101 kHz/K agrees with its own raw data to ~1% (raw OLS −102.3 ± 1.1 over file-axis 254–324 K, the "
    "drawn red line's span; the paper prints no uncertainty anywhere), while the earlier digitised "
    "−112 kHz/K was a faithful reading of the FIGURE, whose axis inflates slopes ×1.073 — the "
    "printed-vs-digitised discrepancy is localised entirely to the figure/file axis boundary. Which axis "
    "carries the calibrated sensor reading is UNRESOLVED (top ask to the authors); that systematic IS "
    "the carried band [−1.2×10⁵, −6.4×10⁴] Hz/K (shaded), with the graded point −1.09×10⁵ Hz/K = the "
    "conservative face-value branch over 293–310 K — a documented branch choice, not a best estimate. "
    "Deuteration-transfer caveat retained (protonated Singh crystal vs the dataset's Pc-d₁₄:PTP-d₁₄)."
)


def _load_extraction() -> tuple[np.ndarray, np.ndarray]:
    """(T_fig, f_MHz) marker centres from the archived vector extraction."""
    rows = [
        line.split(",")
        for line in EXTRACTION_CSV.read_text().splitlines()[1:]
        if line.strip()
    ]
    arr = np.array([(float(a), float(b)) for a, b in rows])
    return arr[:, 0], arr[:, 1]


def _fit_dict(fit) -> dict:
    return {
        "label": fit.label,
        "t_lo_k": fit.t_lo_k,
        "t_hi_k": fit.t_hi_k,
        "slope_khz_per_k": fit.slope_khz_per_k,
        "se_khz_per_k": fit.se_khz_per_k,
    }


def build_data() -> dict:
    """Raw series, mapped extraction, window fits, affine map (pure)."""
    t_raw, f_raw = load_xz()
    amap = affine_map_vs_extraction()
    t_fig, f_fig = _load_extraction()
    t_fig_on_raw = np.array([amap.fig_to_raw(t) for t in t_fig])

    drawn = ols_slope(t_raw, f_raw, 254.0, 324.0, "drawn-red-line span 254–324")
    fits = [
        _fit_dict(drawn),
        _fit_dict(point_window_fit()),
        _fit_dict(band_lo_window_fit()),
        _fit_dict(band_hi_window_fit()),
    ]
    return {
        "t_raw_k": t_raw,
        "f_raw_mhz": f_raw,
        "t_fig_on_raw_k": t_fig_on_raw,
        "f_fig_mhz": f_fig,
        "affine_scale": amap.scale,
        "affine_offset_k": amap.offset_k,
        "affine_rms_k": amap.rms_resid_k,
        "freq_resid_rms_khz": amap.freq_resid_rms_khz,
        "slope_inflation": amap.slope_inflation,
        "fits": fits,
        "printed_khz_per_k": PRINTED_SLOPE_KHZ_PER_K,
        "digitised_fig_axis_khz_per_k": drawn.slope_khz_per_k
        * amap.slope_inflation,
        "band_khz_per_k": (
            DF_SPIN_DT.df_dt_band_lo_hz_per_k / 1e3,
            DF_SPIN_DT.df_dt_band_hi_hz_per_k / 1e3,
        ),
        "graded_point_khz_per_k": DF_SPIN_DT.df_dt_hz_per_k / 1e3,
    }


def render(data: dict):
    from cavity.figures import _style

    _style.apply_style()
    import matplotlib.pyplot as plt

    fig, (ax_l, ax_r) = plt.subplots(
        1, 2, figsize=(9.4, 4.4), width_ratios=(1.15, 1.0),
        constrained_layout=True,
    )

    # --- left: the two point sets on ONE (raw) axis + window fits ---------
    ax_l.grid(True, axis="both")
    ax_l.scatter(
        data["t_raw_k"], data["f_raw_mhz"], s=11, color=_style.BLUE,
        label="raw file points (as received)", zorder=3,
    )
    ax_l.scatter(
        data["t_fig_on_raw_k"], data["f_fig_mhz"], s=26,
        facecolors="none", edgecolors=_style.ORANGE, linewidths=0.9,
        label="figure extraction, inverse-affine-mapped", zorder=4,
    )
    fit_colours = (_style.VIOLET, _style.GREEN, _style.INK_MUTED, _style.INK_MUTED)
    fit_styles = ("-", "--", ":", ":")
    t_all, f_all = data["t_raw_k"], data["f_raw_mhz"]
    for fit, colour, style in zip(data["fits"], fit_colours, fit_styles):
        lo, hi = fit["t_lo_k"], fit["t_hi_k"]
        mask = (t_all >= lo) & (t_all <= hi)
        slope_mhz = fit["slope_khz_per_k"] / 1e3
        t_mid = t_all[mask].mean()
        f_mid = f_all[mask].mean()
        tt = np.array([lo, hi])
        ax_l.plot(
            tt, f_mid + slope_mhz * (tt - t_mid), color=colour,
            linestyle=style, linewidth=1.4, zorder=5,
        )
        ax_l.text(
            hi, f_mid + slope_mhz * (hi - t_mid),
            f" {fit['slope_khz_per_k']:.1f}", fontsize=6.6, color=colour,
            va="center",
        )
    ax_l.set_xlabel("T, file axis (K)")
    ax_l.set_ylabel("f (MHz)")
    ax_l.set_title(
        "X–Z series: raw vs re-digitised, one axis\n"
        f"affine map T_fig = {data['affine_scale']:.4f}·T_raw + "
        f"{data['affine_offset_k']:.2f} K (rms {data['affine_rms_k']:.2f} K)",
        fontsize=8.5,
    )
    ax_l.legend(loc="lower left", fontsize=6.8)

    # --- right: slope vs fit window (forest plot) --------------------------
    band_lo, band_hi = data["band_khz_per_k"]
    ax_r.axvspan(band_lo, band_hi, color=_style.BAND_GREY, alpha=0.55,
                 label="carried §6T band [−120, −64]")
    ax_r.axvline(data["graded_point_khz_per_k"], color=_style.INK,
                 linewidth=1.0, linestyle="--",
                 label="graded point −109 (branch choice)")

    entries = [
        ("printed −101 (no ± in print)", data["printed_khz_per_k"], None,
         _style.INK),
        ("digitised, FIGURE axis", data["digitised_fig_axis_khz_per_k"], None,
         _style.ORANGE),
    ] + [
        (f["label"], f["slope_khz_per_k"], f["se_khz_per_k"], _style.BLUE)
        for f in data["fits"]
    ]
    y_pos = np.arange(len(entries))[::-1]
    for y, (label, slope, se, colour) in zip(y_pos, entries):
        if se is None:
            ax_r.plot([slope], [y], marker="D", markersize=5, color=colour)
        else:
            ax_r.errorbar(
                [slope], [y], xerr=[se], fmt="o", markersize=5,
                color=colour, capsize=3, linewidth=1.2,
            )
    ax_r.set_yticks(y_pos)
    ax_r.set_yticklabels([e[0] for e in entries], fontsize=7.0)
    ax_r.set_xlim(-130.0, -54.0)
    ax_r.set_ylim(-0.7, len(entries) - 0.3)
    ax_r.set_xlabel("df/dT (kHz/K)")
    ax_r.set_title("slope vs fit window", fontsize=8.5)
    ax_r.grid(True, axis="x")

    # the ×1.073 inflation arrow across the figure/file axis boundary
    y_dig = y_pos[1]
    y_drawn = y_pos[2]
    ax_r.annotate(
        "",
        xy=(data["fits"][0]["slope_khz_per_k"], y_drawn),
        xytext=(data["digitised_fig_axis_khz_per_k"], y_dig),
        arrowprops={"arrowstyle": "->", "color": _style.ORANGE, "lw": 1.0},
    )
    ax_r.text(
        (data["digitised_fig_axis_khz_per_k"]
         + data["fits"][0]["slope_khz_per_k"]) / 2.0,
        (y_dig + y_drawn) / 2.0 + 0.15,
        f"×{data['slope_inflation']:.3f} figure-axis inflation",
        fontsize=6.6, color=_style.ORANGE, ha="center",
    )
    ax_r.legend(loc="upper right", fontsize=6.6)

    _style.provenance_footer(
        fig,
        "inputs: refs/singh_2025_raw/Fig2B_(iii)XZ_xztemp.txt (SHA-256-pinned, byte-for-byte as received) "
        "+ refs/singh_fig2biii_vector_extraction.csv · all fits and the affine map recomputed at "
        "figure-build time by cavity.provenance.singh_raw_fits · temperature-axis identity UNRESOLVED",
    )
    return fig


def main(out_dir: Path | None = None) -> list[Path]:
    from cavity.figures import _style

    fig = render(build_data())
    paths = _style.save_figure(fig, "f6_singh_axis_map", out_dir)
    for p in paths:
        print(f"wrote {p}")
    return paths


if __name__ == "__main__":
    main()
