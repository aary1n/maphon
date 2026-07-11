"""F3 — steady-state ΔT(r, z) heatmap in the maser crystal.

Data source (module call, computed at figure-build time — closed-form,
no solves in the COMSOL sense): `cavity.thermal.cylinder.solve` at the
COMMITTED worked-example graded-inputs stack
(tests/test_thermal_cylinder.py::test_maser_worked_example_graded_inputs):
CRYSTAL dims (r = 1.5 mm, h = 8 mm), k = `K_PTP` band midpoint, END-FIRE
Beer-Lambert deposition at l_abs = `L_ABS_PUMP` scoping grid[5] = 200 µm
(UNSOURCED-SCOPING), flood radial profile, Dirichlet base + Robin
side/top at h = h_conv,hi + h_rad(ε = 0.90, 300 K). ΔT is strictly
linear in P; P_abs = 50 mW is ILLUSTRATIVE, chosen so the
volume-averaged ΔT ≈ 19 K sits inside Oxborrow's in-thread "several
tens of Celsius" inference (SPEC §11 item 5).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from cavity.provenance.constants import (
    CRYSTAL,
    EMISSIVITY_PTP,
    H_CONV_AIR,
    K_PTP,
    L_ABS_PUMP,
)
from cavity.thermal.cylinder import CylinderSpec, PumpSource, SurfaceBC, solve
from cavity.thermal.radiation import h_top_with_radiation

P_ABS_W = 0.05  # ILLUSTRATIVE pump power (ΔT strictly linear in P)
N_MODES = 64
N_R, N_Z = 121, 161

CAPTION = (
    "Steady-state ΔT(r, z) in the maser crystal (Pc:PTP cylinder, radius 1.5 mm × "
    "height 8 mm; provenance `Crystal`), computed by the licence-free closed-form Bessel/Robin conduction "
    "anchor `cavity.thermal.cylinder` at the committed worked-example stack: END-FIRE axial Beer-Lambert "
    "deposition (D2 — supervisor-preferred, Oxborrow-verbal 2026-07-08; side-fire structurally outside "
    "the axisymmetric eigenbasis), l_abs = 200 µm (UNSOURCED-SCOPING value; nominal-doping arithmetic "
    "would overstate absorption — Oxborrow-verbal 2026-07-06), flood radial profile (D3), k = 0.316 "
    "W m⁻¹K⁻¹ (geometric mid of the 0.1–1 band; the 0.1 floor's provenance is a liquid-phase value), "
    "Dirichlet base ('substrate at room temperature') and Robin side/top at h = h_conv,hi + h_rad ≈ 25.5 "
    "W m⁻²K⁻¹ (free-convection ceiling — both real geometries likely sit below the 5–20 band — plus "
    "linearised radiation at ε = 0.90 of the ratified 0.80–0.95 band). P_abs = 50 mW is ILLUSTRATIVE: "
    "chosen so the volume-averaged ΔT ≈ 19 K sits inside Oxborrow's in-thread 'several tens of Celsius' "
    "inference (~13–30 K at 100 mA drive); ΔT is strictly linear in P — rescale freely. Peak ΔT ≈ 53 K at "
    "the illuminated face; at this ΔT the linearised h_rad under-reads the exact quartic by ~5–16% "
    "(§7.T7). Energy diagnostic: boundary flux = P_abs to solver truncation. All D1–D7 BC/heating details "
    "are parameterised planning assumptions pending Oxborrow (§11 item-10 bundle)."
)


def build_data(p_abs_w: float = P_ABS_W) -> dict:
    """Solve the committed worked-example stack and sample ΔT(r, z) (pure)."""
    h_eff = h_top_with_radiation(
        H_CONV_AIR.h_band_hi_w_m2_k, EMISSIVITY_PTP.eps_nominal, 300.0
    )
    spec = CylinderSpec(
        CRYSTAL.diameter_m / 2.0,
        CRYSTAL.height_m,
        K_PTP.k_mid_w_m_k,
        SurfaceBC.robin(h_eff),
        SurfaceBC.robin(h_eff),
        SurfaceBC.dirichlet(),
    )
    src = PumpSource(
        p_abs_w,
        "beer_lambert",
        "flood",
        l_abs_m=L_ABS_PUMP.l_abs_scoping_grid_m[5],
    )
    sol = solve(spec, src, n_modes=N_MODES)

    r_m = np.linspace(0.0, spec.radius_m, N_R)
    z_m = np.linspace(0.0, spec.height_m, N_Z)
    delta_t = sol.delta_t(r_m[None, :], z_m[:, None])  # (N_Z, N_R)
    bp = sol.boundary_power_w()
    return {
        "r_mm": r_m * 1e3,
        "z_mm": z_m * 1e3,
        "delta_t_k": delta_t,
        "peak_k": sol.peak_k,
        "vol_avg_k": sol.volume_average_k(),
        "boundary_power_w": bp["total"],
        "p_abs_w": p_abs_w,
        "h_eff_w_m2_k": h_eff,
        "l_abs_m": L_ABS_PUMP.l_abs_scoping_grid_m[5],
        "k_w_m_k": K_PTP.k_mid_w_m_k,
        "radius_mm": spec.radius_m * 1e3,
        "height_mm": spec.height_m * 1e3,
    }


def render(data: dict):
    from cavity.figures import _style

    _style.apply_style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4.4, 5.6), constrained_layout=True)
    im = ax.pcolormesh(
        data["r_mm"],
        data["z_mm"],
        data["delta_t_k"],
        cmap=_style.SEQUENTIAL_THERMAL,
        shading="gouraud",
        rasterized=True,
    )
    ax.invert_yaxis()  # z increases downward from the illuminated face
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(_style.INK)
        spine.set_linewidth(1.2)
    ax.set_xlabel("r (mm)")
    ax.set_ylabel("z (mm) — depth below illuminated face")
    ax.set_title("ΔT(r, z), maser crystal — end-fire Beer–Lambert")
    cbar = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.03)
    cbar.set_label("ΔT (K)")
    cbar.outline.set_visible(False)

    ax.annotate(
        "illuminated face (end-fire pump)",
        xy=(data["radius_mm"] * 0.5, 0.0),
        xytext=(data["radius_mm"] * 0.5, data["height_mm"] * 0.09),
        ha="center",
        fontsize=7.5,
        color="white",
        arrowprops={"arrowstyle": "->", "color": "white", "lw": 0.9},
    )
    ax.text(
        0.03,
        0.03,
        f"peak ΔT = {data['peak_k']:.1f} K\n"
        f"⟨ΔT⟩_vol = {data['vol_avg_k']:.1f} K\n"
        f"P_abs = {data['p_abs_w'] * 1e3:.0f} mW (illustrative)",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=7.5,
        color="white",
    )
    _style.provenance_footer(
        fig,
        "computed at figure-build time by cavity.thermal.cylinder (closed form; no solve archive) · "
        "committed worked-example stack: CRYSTAL, K_PTP.k_mid, H_CONV_AIR.h_band_hi + EMISSIVITY_PTP "
        "@300 K, L_ABS_PUMP grid[5] · D1–D7 planning assumptions pending (§11 item-10 bundle)",
    )
    return fig


def main(out_dir: Path | None = None) -> list[Path]:
    from cavity.figures import _style

    fig = render(build_data())
    paths = _style.save_figure(fig, "f3_delta_t_map", out_dir)
    for p in paths:
        print(f"wrote {p}")
    return paths


if __name__ == "__main__":
    main()
