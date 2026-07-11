"""F4 — Δf_cavity over the ruled 30 K envelope, with the spin arm to scale.

Data source: render-time evaluation of committed functions/constants
only (`cavity.thermal.detuning.cavity_arm_shift_uniform_hz`,
`cavity.provenance.constants.cavity_df_dt_hz_per_k`, `DF_CAVITY_DT`,
`DF_SPIN_DT`, `STO`, `TARGET`) — no disk reads, no fresh literals. The
three cavity-arm curves are exactly the A10 anchor's three comparators
(tests/test_thermal_detuning.py::test_a10_envelope_form_discrepancies_pinned);
the spin arm is drawn on the same axes with its true (negative) sign.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from cavity.provenance.constants import (
    DF_CAVITY_DT,
    DF_SPIN_DT,
    STO,
    TARGET,
    cavity_df_dt_hz_per_k,
)
from cavity.thermal.detuning import cavity_arm_shift_uniform_hz

T_BASE_K = DF_CAVITY_DT.t_window_lo_k  # 293 K
T_TOP_K = DF_CAVITY_DT.t_window_hi_k   # 323 K ("293 + 30 = 323" reading)

CAPTION = (
    "Cavity-arm detuning over the ruled 30 K operating envelope, 293→323 K "
    "('293 + 30 = 323' is our reading of the verbal 30 K ruling — Oxborrow-verbal 2026-07-08 — not his "
    "verbatim range). Three branches of the same §6T constant (Rupprecht & Bell Curie–Weiss parameters "
    "C = 8.25×10⁴ K, T₀ = 37 K; local-slope caveats and the 112 K validity floor as graded): the ADOPTED "
    "integrated closed form (`cavity.thermal.detuning`; +82.6 MHz at the envelope top), the 293 K point "
    "slope × ΔT (+2.885 MHz/K), and the first-order integral of the committed slope. Documented spreads "
    "(CI anchor A10): integrated = +0.7% vs the 300 K point slope × 30 K, +6.6% vs the first-order "
    "integral, −4.6% vs the 293 K slope × 30 K. The spin arm is drawn to the same scale at its §6T band "
    "(−64…−120 kHz/K; graded point −109 kHz/K, the conservative face-value branch): at the envelope top "
    "it reaches only ~2–4% of the cavity arm — that asymmetry is the point — and its sign is OPPOSITE "
    "(cavity blue-shifts, spins red-shift on heating), so the differential detuning ADDS. Spin-arm "
    "caveats ride along: the raw data's temperature-axis definition is UNRESOLVED (it IS the band), "
    "deuteration transfer unverified, local slopes only. p_e ≈ 1 assumed (gate-run p_e = 0.9977, a −0.2% "
    "correction inside the band)."
)


def build_data() -> dict:
    """The three A10 comparator curves + spin band, all committed maths (pure)."""
    t_k = np.linspace(T_BASE_K, T_TOP_K, 301)
    dt = t_k - T_BASE_K
    t0 = DF_CAVITY_DT.curie_weiss_t0_k
    f_hz = TARGET.f_design_hz

    integrated_hz = np.array(
        [cavity_arm_shift_uniform_hz(float(d), T_BASE_K) for d in dt]
    )
    slope_293_hz = cavity_df_dt_hz_per_k(T_BASE_K) * dt
    first_order_hz = (
        (f_hz / (2.0 * STO.epsilon_r_real))
        * DF_CAVITY_DT.curie_constant_k
        * (1.0 / (T_BASE_K - t0) - 1.0 / (t_k - t0))
    )
    spin_point_hz = DF_SPIN_DT.df_dt_hz_per_k * dt
    spin_band_steep_hz = DF_SPIN_DT.df_dt_band_lo_hz_per_k * dt   # −120 kHz/K
    spin_band_shallow_hz = DF_SPIN_DT.df_dt_band_hi_hz_per_k * dt  # −64 kHz/K

    point_300_top = cavity_df_dt_hz_per_k(DF_CAVITY_DT.t_ref_k) * (T_TOP_K - T_BASE_K)
    return {
        "t_k": t_k,
        "integrated_hz": integrated_hz,
        "slope_293_hz": slope_293_hz,
        "first_order_hz": first_order_hz,
        "spin_point_hz": spin_point_hz,
        "spin_band_steep_hz": spin_band_steep_hz,
        "spin_band_shallow_hz": spin_band_shallow_hz,
        "endpoint_integrated_hz": float(integrated_hz[-1]),
        "ratio_vs_point_300": float(integrated_hz[-1] / point_300_top),
        "ratio_vs_first_order": float(integrated_hz[-1] / first_order_hz[-1]),
        "ratio_vs_slope_293": float(integrated_hz[-1] / slope_293_hz[-1]),
        "spin_endpoints_hz": (
            float(spin_band_steep_hz[-1]),
            float(spin_band_shallow_hz[-1]),
        ),
    }


def render(data: dict):
    from cavity.figures import _style

    _style.apply_style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.8, 4.6), constrained_layout=True)
    ax.grid(True, axis="y")
    t = data["t_k"]

    ax.plot(
        t, data["integrated_hz"] / 1e6, color=_style.BLUE,
        label="integrated CW closed form (adopted)",
    )
    ax.plot(
        t, data["slope_293_hz"] / 1e6, color=_style.ORANGE, linestyle="--",
        label="293 K point slope × ΔT (+2.885 MHz/K)",
    )
    ax.plot(
        t, data["first_order_hz"] / 1e6, color=_style.VIOLET, linestyle=":",
        label="first-order integral of committed slope",
    )

    # spin arm, true (negative) sign — a thin band hugging zero
    ax.fill_between(
        t,
        data["spin_band_steep_hz"] / 1e6,
        data["spin_band_shallow_hz"] / 1e6,
        color=_style.BAND_GREY,
        alpha=0.7,
        linewidth=0,
        label="spin arm, §6T band (−64…−120 kHz/K)",
    )
    ax.plot(
        t, data["spin_point_hz"] / 1e6, color=_style.GREEN, linestyle="--",
        linewidth=1.2, label="spin arm, graded point (−109 kHz/K)",
    )
    ax.axhline(0.0, color=_style.INK_MUTED, linewidth=0.7)

    ax.set_xlabel("T (K)")
    ax.set_ylabel("Δf (MHz)")
    ax.set_title("Cavity vs spin arm over the ruled 30 K envelope")
    ax.legend(loc="upper left", fontsize=7.2)

    ax.annotate(
        f"envelope top: +{data['endpoint_integrated_hz'] / 1e6:.1f} MHz\n"
        f"A10 spreads: {100 * (data['ratio_vs_point_300'] - 1):+.1f}% vs 300 K slope · "
        f"{100 * (data['ratio_vs_first_order'] - 1):+.1f}% vs first-order · "
        f"{100 * (data['ratio_vs_slope_293'] - 1):+.1f}% vs 293 K slope",
        xy=(t[-1], data["endpoint_integrated_hz"] / 1e6),
        xytext=(0.98, 0.30),
        textcoords="axes fraction",
        ha="right",
        fontsize=7.2,
        color=_style.INK,
        arrowprops={"arrowstyle": "->", "color": _style.INK_MUTED, "lw": 0.8},
    )
    ax.text(
        0.98,
        0.075,
        "spin arm: opposite sign, ~2–4% of the cavity arm at the top —\n"
        "the differential detuning ADDS (§6T)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.2,
        color=_style.INK_MUTED,
    )
    _style.provenance_footer(
        fig,
        "evaluated at figure-build time from committed constants only: DF_CAVITY_DT (R&B 1962 "
        "C = 8.25e4 K, T0 = 37 K), DF_SPIN_DT (raw-data grading 2026-07-07), STO, TARGET · no disk inputs",
    )
    return fig


def main(out_dir: Path | None = None) -> list[Path]:
    from cavity.figures import _style

    fig = render(build_data())
    paths = _style.save_figure(fig, "f4_cavity_arm_envelope", out_dir)
    for p in paths:
        print(f"wrote {p}")
    return paths


if __name__ == "__main__":
    main()
