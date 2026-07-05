"""SPEC §7.T5 check 3a — sweep runner + decision report (D.1–D.4).

Runs the identifiability sweep for both sample forms, renders the R and
verdict maps, and writes the decision-shaped markdown report. Pure
post-processing on `cavity.thermal.identifiability`; matplotlib is
imported here only, so the pytest layer stays dependency-light.

Usage:  python -m cavity.thermal.report_3a [--out thermal/reports]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from cavity.provenance.constants import DF_SPIN_DT, GLASS_SLIDE, K_PTP, RIG_GEOMETRY, WAX
from cavity.thermal.identifiability import (
    FORMS,
    IDENTIFIABLE,
    K_BAND,
    NAMED_POINTS,
    PARTIAL,
    SIGMA_REL,
    UNIDENTIFIABLE,
    FormSweep,
    SweepConfig,
    confounding_mismatch,
    log_sensitivities,
    run_form,
    verdict_map,
    w_prior_factor_to_deconfound,
)

SCENARIOS = ("both_free", "w_pinned", "t_wax_pinned")

# Dataviz reference palette (light mode), validated ordinal blue ramp.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SEQ_BLUE = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
ORDINAL3 = ["#86b6ef", "#2a78d6", "#104281"]  # UNIDENT -> PARTIAL -> IDENT


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.xaxis.label.set_color(INK_2)
    ax.yaxis.label.set_color(INK_2)


def _named_point_markers(ax, sweep: FormSweep) -> None:
    for name, (w, t_wax) in NAMED_POINTS.items():
        ax.plot(
            w * 1e6, t_wax * 1e6, "o", ms=6, mfc="white", mec=INK, mew=1.2, zorder=5
        )
        ax.annotate(
            name.replace("_", " "),
            (w * 1e6, t_wax * 1e6),
            xytext=(6, 5),
            textcoords="offset points",
            fontsize=7,
            color=INK_2,
        )


def plot_r_map(sweep: FormSweep, out_dir: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, LogNorm

    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)
    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    _style(ax)

    w_um = sweep.w_m * 1e6
    t_um = sweep.t_wax_m * 1e6
    r_clip = np.clip(sweep.r_map, 1e-3, None)
    mesh = ax.pcolormesh(
        w_um, t_um, r_clip.T, cmap=cmap, norm=LogNorm(vmin=1e-3, vmax=3.0),
        shading="gouraud", rasterized=True,
    )
    cbar = fig.colorbar(mesh, ax=ax, pad=0.02)
    cbar.set_label("R  (k-band swing / mid-band signal)", color=INK_2, fontsize=8)
    cbar.ax.tick_params(colors=MUTED, labelsize=8)
    cbar.outline.set_edgecolor(GRID)

    levels = [2 * s for s in SIGMA_REL]
    cs = ax.contour(
        w_um, t_um, sweep.r_map.T, levels=levels, colors=INK, linewidths=0.9,
        linestyles=["solid", "dashed", "dotted"],
    )
    fmt = {lvl: f"R={lvl:g} (2σ@{lvl / 2:.0%})" for lvl in levels}
    ax.clabel(cs, fmt=fmt, fontsize=7, colors=INK)

    # regime overlay (C.4): w/t_PTP = 1
    if sweep.w_m[0] <= sweep.t_ptp_m <= sweep.w_m[-1]:
        ax.axvline(sweep.t_ptp_m * 1e6, color=INK, lw=1.0, ls=(0, (4, 3)))
        ax.annotate(
            "w = t_PTP\n(w<t left: PTP spreading)",
            (sweep.t_ptp_m * 1e6, t_um[0] * 1.4),
            xytext=(-8, 0), textcoords="offset points",
            fontsize=7, color=INK_2, ha="right",
        )
    else:
        side = "w ≫ t_PTP everywhere (substrate-dominated)" if (
            sweep.w_m[0] > sweep.t_ptp_m
        ) else "w ≪ t_PTP everywhere (PTP spreading-dominated)"
        ax.set_title(
            f"{sweep.form} (t_PTP = {sweep.t_ptp_m * 1e9:.0f} nm) — {side}",
            fontsize=9, color=INK,
        )

    if sweep.form == "PLATE":
        ax.set_title(
            f"PLATE (t_PTP = {sweep.t_ptp_m * 1e3:.1f} mm) — "
            "w ≤ t_PTP across the whole box",
            fontsize=9, color=INK,
        )

    _named_point_markers(ax, sweep)
    ax.text(
        0.02, 0.03,
        f"R ∈ [{sweep.r_map.min():.3g}, {sweep.r_map.max():.3g}] over the box",
        transform=ax.transAxes, fontsize=8, color=INK,
        bbox=dict(fc="white", ec=GRID, alpha=0.85, boxstyle="round,pad=0.25"),
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("spot radius w (µm, 1/e²)", fontsize=9)
    ax.set_ylabel("wax thickness t_wax (µm)", fontsize=9)
    fig.tight_layout()
    path = out_dir / f"r_map_{sweep.form.lower()}.png"
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)
    return path


def plot_verdicts(
    sweep: FormSweep, mismatch_both_free: np.ndarray, out_dir: Path
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap
    from matplotlib.patches import Patch

    cmap = ListedColormap(ORDINAL3)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)
    w_um = sweep.w_m * 1e6
    t_um = sweep.t_wax_m * 1e6

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.8), dpi=200, sharey=True)
    fig.patch.set_facecolor(SURFACE)
    for ax, sigma in zip(axes, SIGMA_REL):
        _style(ax)
        verdicts = verdict_map(sweep.r_map, sigma)
        ax.pcolormesh(
            w_um, t_um, verdicts.T, cmap=cmap, norm=norm, shading="nearest",
            rasterized=True,
        )
        confounded = mismatch_both_free < sigma
        if confounded.any():
            ax.contourf(
                w_um, t_um, confounded.T.astype(float), levels=[0.5, 1.5],
                colors="none", hatches=["////"],
            )
            ax.contour(
                w_um, t_um, confounded.T.astype(float), levels=[0.5],
                colors=INK, linewidths=0.7,
            )
        if sweep.w_m[0] <= sweep.t_ptp_m <= sweep.w_m[-1]:
            ax.axvline(sweep.t_ptp_m * 1e6, color=INK, lw=0.8, ls=(0, (4, 3)))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"σ_rel = {sigma:.0%}", fontsize=9, color=INK)
        ax.set_xlabel("w (µm)", fontsize=9)
    axes[0].set_ylabel("t_wax (µm)", fontsize=9)

    legend = [
        Patch(fc=ORDINAL3[0], label="UNIDENTIFIABLE (R ≤ σ)"),
        Patch(fc=ORDINAL3[1], label="PARTIAL (σ < R ≤ 2σ)"),
        Patch(fc=ORDINAL3[2], label="IDENTIFIABLE (R > 2σ)"),
        Patch(fc="none", ec=INK, hatch="////", label="CONFOUNDED (nuisances mimic k)"),
    ]
    fig.legend(
        handles=legend, loc="upper center", ncol=4, frameon=False, fontsize=8,
        bbox_to_anchor=(0.5, 1.02), labelcolor=INK_2,
    )
    fig.suptitle(
        f"{sweep.form}: threshold verdicts with both nuisances free in the box",
        y=1.10, fontsize=10, color=INK,
    )
    fig.tight_layout()
    path = out_dir / f"verdict_map_{sweep.form.lower()}.png"
    fig.savefig(path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return path


def _fractions(arr: np.ndarray) -> dict[int, float]:
    return {v: float(np.mean(arr == v)) for v in (UNIDENTIFIABLE, PARTIAL, IDENTIFIABLE)}


def _nearest_index(grid: np.ndarray, value: float) -> int:
    return int(np.argmin(np.abs(np.log(grid) - math.log(value))))


def build_report(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    config = SweepConfig()

    sweeps: dict[str, FormSweep] = {}
    mismatches: dict[tuple[str, str], np.ndarray] = {}
    for form in FORMS:
        print(f"[3a] sweeping {form} ({config.n_w}x{config.n_t_wax}x3) ...")
        sweeps[form] = run_form(form, config)
        for scenario in SCENARIOS:
            mismatches[(form, scenario)] = confounding_mismatch(
                sweeps[form].delta_t, scenario
            )

    figures = []
    for form, sweep in sweeps.items():
        figures.append(plot_r_map(sweep, out_dir))
        figures.append(plot_verdicts(sweep, mismatches[(form, "both_free")], out_dir))

    np.savez_compressed(
        out_dir / "identifiability_3a_grids.npz",
        k_band=np.array(K_BAND),
        sigma_rel=np.array(SIGMA_REL),
        **{f"{f.lower()}_w_m": s.w_m for f, s in sweeps.items()},
        **{f"{f.lower()}_t_wax_m": s.t_wax_m for f, s in sweeps.items()},
        **{f"{f.lower()}_delta_t": s.delta_t for f, s in sweeps.items()},
        **{f"{f.lower()}_r_map": s.r_map for f, s in sweeps.items()},
        **{
            f"{f.lower()}_mismatch_{sc}": mismatches[(f, sc)]
            for f in FORMS
            for sc in SCENARIOS
        },
    )

    lines: list[str] = []
    add = lines.append
    add("# Check 3a identifiability sweep — decision report")
    add("")
    add("Generated by `python -m cavity.thermal.report_3a` (deterministic, no RNG).")
    add("Engine: `cavity/thermal/layered.py` (Hankel-transform layered medium),")
    add("anchored by `tests/test_thermal_layered.py` before this sweep was run.")
    add("Raw grids: `identifiability_3a_grids.npz` in this directory.")
    add("")

    # ---- verdict summary (D.1) ----
    add("## D.1 Verdicts")
    add("")
    add("| form | σ_rel | R-threshold verdict over the (w, t_wax) box | "
        "confounded (both nuisances free) | confounded (w pinned) | "
        "confounded (t_wax pinned) |")
    add("|---|---|---|---|---|---|")
    for form, sweep in sweeps.items():
        for sigma in SIGMA_REL:
            fr = _fractions(verdict_map(sweep.r_map, sigma))
            cf = {
                sc: float(np.mean(mismatches[(form, sc)] < sigma)) for sc in SCENARIOS
            }
            add(
                f"| {form} | {sigma:.0%} | "
                f"IDENT {fr[IDENTIFIABLE]:.0%} / PART {fr[PARTIAL]:.0%} / "
                f"UNID {fr[UNIDENTIFIABLE]:.0%} | "
                f"{cf['both_free']:.0%} | {cf['w_pinned']:.0%} | "
                f"{cf['t_wax_pinned']:.0%} |"
            )
    add("")

    # ---- named-point detail ----
    add("## Named grid points (regression-pinned in "
        "`tests/test_thermal_identifiability.py`)")
    add("")
    add("| form | point | w | t_wax | ΔT/P at k_mid (K/W) | R | "
        "∂lnΔT/∂ln k | ∂lnΔT/∂ln w | ∂lnΔT/∂ln t_wax | ∂lnΔT/∂ln t_glass | "
        "Robin h=20 drop | w-prior ×factor to de-confound (σ=10%) |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for form, sweep in sweeps.items():
        for name, (w, t_wax) in NAMED_POINTS.items():
            i = _nearest_index(sweep.w_m, w)
            j = _nearest_index(sweep.t_wax_m, t_wax)
            r = sweep.r_map[i, j]
            dt_mid = sweep.delta_t[1, i, j]
            sens = log_sensitivities(form, w, t_wax)
            s_fac = w_prior_factor_to_deconfound(sweep, i, j, 0.10)
            s_txt = (
                "n/a (not confounded)" if s_fac == math.inf
                else "unrescuable by w alone" if s_fac is None
                else f"×{s_fac:.2f}"
            )
            add(
                f"| {form} | {name} | {w * 1e6:.2f} µm | {t_wax * 1e6:.1f} µm | "
                f"{dt_mid:.3e} | {r:.4f} | {sens['dlnT_dlnk']:+.3f} | "
                f"{sens['dlnT_dlnw']:+.3f} | {sens['dlnT_dlntwax']:+.3f} | "
                f"{sens['dlnT_dlntglass']:+.3f} | "
                f"{sens['robin_h20_frac_drop']:.2%} | {s_txt} |"
            )
    add("")

    # ---- auxiliary decision numbers ----
    add("## Auxiliary numbers")
    add("")
    film = sweeps["FILM"]
    for sigma in SIGMA_REL:
        ident = film.r_map > 2.0 * sigma
        if ident.any():
            w_max = film.w_m[ident.any(axis=1)].max()
            add(
                f"- FILM R-identifiable window at σ={sigma:.0%}: "
                f"w ≤ {w_max * 1e6:.1f} µm (some t_wax)."
            )
        else:
            add(f"- FILM R-identifiable window at σ={sigma:.0%}: empty.")
    theta_ratio = sweeps["PLATE"].delta_t[1] / film.delta_t[1]
    add(
        f"- PLATE/FILM mid-band transfer-function ratio Θ_plate/Θ_film over the "
        f"box: {theta_ratio.min():.2f} – {theta_ratio.max():.2f} "
        "(3b's rig-cancellation fails wherever this ≠ 1 if the two samples "
        "differ in form)."
    )
    plate = sweeps["PLATE"]
    for name, (w, t_wax) in NAMED_POINTS.items():
        i = _nearest_index(plate.w_m, w)
        j = _nearest_index(plate.t_wax_m, t_wax)
        facs = []
        for sigma in SIGMA_REL:
            f = w_prior_factor_to_deconfound(plate, i, j, sigma)
            facs.append(
                "exact-only" if f is None else "none needed" if f == math.inf
                else f"×{f:.2f}"
            )
        add(
            f"- PLATE {name}: w-prior half-width to de-confound at "
            f"σ = 5/10/20%: {facs[0]} / {facs[1]} / {facs[2]}."
        )
    for form in FORMS:
        t_ptp = FORMS[form]
        from cavity.thermal.identifiability import delta_t_center

        w, t_wax = NAMED_POINTS["doublet_mid_wax"]
        k_mid = K_BAND[1]
        g = GLASS_SLIDE.t_glass_sensitivity_frac
        hi = delta_t_center(t_ptp, k_mid, w, t_wax, GLASS_SLIDE.t_glass_m * (1 + g))
        lo = delta_t_center(t_ptp, k_mid, w, t_wax, GLASS_SLIDE.t_glass_m * (1 - g))
        base = delta_t_center(t_ptp, k_mid, w, t_wax)
        add(
            f"- {form} doublet_mid_wax, t_glass ±{g:.0%}: ΔT swings "
            f"{lo / base - 1:+.2%} to {hi / base - 1:+.2%} (not verdict-setting)."
        )
    add("")

    add("## Figures (D.4)")
    add("")
    for fig in figures:
        add(f"- `{fig.name}`")
    add("")

    (out_dir / "identifiability_3a_computed.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(f"[3a] wrote {out_dir / 'identifiability_3a_computed.md'}")
    print(f"[3a] figures: {[f.name for f in figures]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="thermal/reports", type=Path)
    args = parser.parse_args()
    build_report(args.out)


if __name__ == "__main__":
    main()
