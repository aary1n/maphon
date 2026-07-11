"""F5 — thermal-margin budget waterfall at the planning point.

Data source: recomputed at figure-build time through the committed
functions (`detuning.q_loaded`, `broadening.resonance_linewidth_hz`,
`detuning.delta_f_max_hz`, `detuning.delta_t_max_k`) with inputs exactly
as `cavity.thermal.report_margin` (RE-BASED 2026-07-11) — Q₀ and p_e =
the OWN-MODEL canonical-branch walls-on finest values read from the
re-based §5a record's manifest via `report_margin.own_model_point()`
(`refs/gate_runs/20260711T132705Z_rejudge/`), k = `DELOAD_K`,
f = `TARGET.f_design_hz`, C₀ = 190 (SPEC revision-note planning value,
never a measured constant). Cross-checked in tests/test_figures.py
against the byte-pinned `thermal/reports/q_margin_planning_point.md`
values. Five stages carry different units, so five mini-panels — no
shared bar axis.
"""

from __future__ import annotations

from pathlib import Path

from cavity.provenance.constants import (
    DELOAD_K,
    DF_CAVITY_DT,
    DF_SPIN_DT,
    TARGET,
)
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.detuning import delta_f_max_hz, delta_t_max_k, q_loaded
from cavity.thermal.report_margin import (
    PLANNING_C0,
    REJUDGE_RUN_DIR,
    own_model_point,
)

CAPTION = (
    "Thermal-margin budget at the planning point, regenerated through the same "
    "committed functions as the byte-pinned report (`thermal/reports/q_margin_planning_point.md`, "
    "re-based 2026-07-11): Q₀ = 6,764.6 — OWN-MODEL, the canonical-branch walls-on finest value from "
    "the re-based §5a record (`refs/gate_runs/20260711T132705Z_rejudge`; supersedes the cross-build "
    "composite's Booth-print 6,980, which is now the comparison anchor) → Q_L = 5,637 under de-loading "
    "k = 0.2 (Breeze 2017; Wu's coupling unstated — flagged; Booth p. 8 states no coupling, so κc is "
    "COMPOSED, not fully own-model) → κc = f/Q_L = 257.2 kHz (CYCLIC-Hz FWHM, never the angular "
    "2πf/Q_L — the provenance table's verified W20 angular-'Hz' trap) → Δf_max = (κc/2)√(C₀−1) = "
    "1.77 MHz at C₀ = 190 (the SPEC revision-note planning value, never a measured constant — the §5a "
    "checkpoint delivers only the κc/Q arm) → ΔT_max = 0.603 K, whiskers = the §6T coefficient band "
    "[0.585, 0.748] K. BRANCH ATTRIBUTION: gate-passage is established on the FAITHFUL branch "
    "(Q₀ = 6,981.3, +0.02% vs Booth's 6,980); the canonical Q₀ has NOT itself passed the Booth window "
    "(branch delta −3.10% as measured). Riders: p_e = 0.99750 is now the own-model walls-on canonical "
    "value (retires the PEC-anchor placeholder); the two arms compose under the common-ΔT planning "
    "convention D8 (direction conservative — overstates detuning, understates ΔT_max); the probe weight "
    "is a uniform-over-crystal placeholder, so spin-arm content inherits UNRATIFIED-w_s status doubly "
    "(gain mask = STO fallback until Phase 1b). The Q-margin QUESTION is supervisor-endorsed (verbal, "
    "2026-07-06); the RESULT remains unratified — this is a planning point, not a claim."
)


def build_data() -> dict:
    """The five stage values through the committed functions (pure)."""
    f_hz = TARGET.f_design_hz
    t_base = DF_CAVITY_DT.t_window_lo_k  # 293 K
    own = own_model_point()
    p_e, record_hash = own["p_e"], own["record_hash"]

    q0 = own["q0_canonical"]
    q_l = q_loaded(q0)
    kappa_c = resonance_linewidth_hz(f_hz, q_l)
    df_max = delta_f_max_hz(PLANNING_C0, kappa_c)
    dt_max = delta_t_max_k(df_max, t_base, f_hz=f_hz, p_e=p_e)

    # band: linear arithmetic across the two §6T coefficient bands (the
    # sub-K regime), exactly as report_margin
    diff_lo = DF_CAVITY_DT.df_dt_band_lo_hz_per_k + abs(
        DF_SPIN_DT.df_dt_band_hi_hz_per_k
    )
    diff_hi = DF_CAVITY_DT.df_dt_band_hi_hz_per_k + abs(
        DF_SPIN_DT.df_dt_band_lo_hz_per_k
    )
    return {
        "q0": q0,
        "q_l": q_l,
        "kappa_c_hz": kappa_c,
        "df_max_hz": df_max,
        "dt_max_k": dt_max,
        "dt_max_band_k": (df_max / diff_hi, df_max / diff_lo),
        "p_e": p_e,
        "p_e_record_hash": record_hash,
        "c0": PLANNING_C0,
        "deload_k": DELOAD_K,
    }


def render(data: dict):
    from cavity.figures import _style

    _style.apply_style()
    import matplotlib.pyplot as plt

    stages = (
        ("$Q_0$", data["q0"], f"{data['q0']:,.0f}", "own-model (canonical)"),
        ("$Q_L$", data["q_l"], f"{data['q_l']:,.0f}", "de-loaded"),
        ("$\\kappa_c$ (kHz)", data["kappa_c_hz"] / 1e3,
         f"{data['kappa_c_hz'] / 1e3:.1f}", "cyclic-Hz FWHM"),
        ("$\\Delta f_{max}$ (MHz)", data["df_max_hz"] / 1e6,
         f"{data['df_max_hz'] / 1e6:.2f}", f"$C_0$ = {data['c0']:g} (planning)"),
        ("$\\Delta T_{max}$ (K)", data["dt_max_k"],
         f"{data['dt_max_k']:.3f}", "common-ΔT (D8)"),
    )
    transforms = (
        f"÷(1 + k), k = {data['deload_k']:g}",
        "f / $Q_L$",
        "(κ$_c$/2)·√($C_0$−1)",
        "common-ΔT inversion",
    )

    fig, axes = plt.subplots(1, 5, figsize=(9.2, 3.6))
    for i, (ax, (label, value, text, note)) in enumerate(zip(axes, stages)):
        ax.bar([0.0], [value], width=0.5, color=_style.BLUE)
        if i == len(stages) - 1:  # §6T coefficient-band whiskers
            lo, hi = data["dt_max_band_k"]
            ax.vlines(0.0, lo, hi, color=_style.INK, linewidth=1.4)
            ax.hlines([lo, hi], -0.12, 0.12, color=_style.INK, linewidth=1.4)
            ax.text(
                0.18, hi, f"[{lo:.3f}, {hi:.3f}] K",
                fontsize=6.8, color=_style.INK_MUTED, va="center",
            )
        ax.set_xlim(-0.6, 0.6)
        ax.set_ylim(0.0, value * 1.35)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(_style.INK_MUTED)
        ax.set_title(label, fontsize=9.0)
        ax.text(0.0, value * 1.04, text, ha="center", fontsize=9.0,
                fontweight="bold", color=_style.INK)
        ax.text(0.0, -0.09, note, ha="center", va="top", fontsize=6.8,
                color=_style.INK_MUTED, transform=ax.get_xaxis_transform())

    for i, label in enumerate(transforms):
        x = (i + 1) / 5.0
        fig.text(x, 0.56, "→", ha="center", fontsize=13, color=_style.INK_MUTED)
        fig.text(x, 0.48, label, ha="center", fontsize=6.6,
                 color=_style.INK_MUTED)

    fig.suptitle(
        "Q-margin budget, planning point — OWN-MODEL Q₀, COMPOSED κc (not a claim)",
        fontsize=10.0,
    )
    fig.subplots_adjust(left=0.03, right=0.97, top=0.82, bottom=0.16, wspace=0.55)
    _style.provenance_footer(
        fig,
        "recomputed at figure-build time by cavity.thermal.detuning/broadening · cross-pinned to "
        "thermal/reports/q_margin_planning_point.md (2026-07-11) · Q₀/p_e own-model from "
        f"refs/gate_runs/{REJUDGE_RUN_DIR} (record {data['p_e_record_hash']})",
    )
    return fig


def main(out_dir: Path | None = None) -> list[Path]:
    from cavity.figures import _style

    fig = render(build_data())
    paths = _style.save_figure(fig, "f5_margin_waterfall", out_dir)
    for p in paths:
        print(f"wrote {p}")
    return paths


if __name__ == "__main__":
    main()
