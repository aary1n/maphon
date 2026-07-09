"""SPEC §7T — analytical thermal submodel (Layer B engine).

Two anchor geometries (SPEC §7.T1 geometry split):

- `layered`: Gaussian-spot spreading resistance on a layered medium
  (Hankel transform) — the Glasgow calibration-rig anchor (§7.T5).
- `cylinder`: finite-cylinder Bessel/Robin conduction — the maser-crystal
  anchor (§7.T5 observable (b), 2026-07-07). Per-surface Robin/Dirichlet
  BCs, volumetric Beer-Lambert / uniform / surface-flux deposition, flood
  / sub-disc / Gaussian radial profiles, native k_r ≠ k_z; closed-form
  axial solutions (no axial truncation error). Anchor only: no
  observable-(b) prediction runs live here.

`identifiability` runs the §7.T5 check-3a sweep on top of `layered`.
`volumetric_3a` re-checks the PLATE k–w degeneracy with the volumetric
(Beer-Lambert) source (`layered.delta_t_gaussian_volumetric`) — the
appendix to the 3a decision report.
`broadening` is the §7.T2 output-3 layer (2026-07-06): it maps a
weighted ΔT distribution through df_spin/dT to the mean line shift plus
the inhomogeneous width, reported in linewidths — geometry-agnostic
map + a Gaussian-spot rig instance on `layered`'s surface field.
`radiation` is the §7.T7 first implementation slot (2026-07-07): the
linearised radiative coefficient h_rad = 4εσT³ and its additive
composition into `layered`'s Robin `h_top` (h_eff = h_conv + h_rad).
`detuning` is the §7.T5(b) integration layer (2026-07-09): the
maser-cylinder ΔT(r,z) field composed with a probe measure into
Δf_spin + inhomogeneous width (the §7.T2 output-3 maser instance,
via `broadening` unchanged) and the integrated Curie-Weiss cavity
arm into Δf_cavity, plus the §7.T4 budget maps
Δf_max = (κc/2)√(C0−1) and the closed-form ΔT_max / P_max inversions.
Probe weight is a uniform-over-crystal placeholder pending Phase 1b
w_s co-registration; both arms compose under the common-ΔT planning
convention (D8, §11 item-10 bundle). Planning point committed at
thermal/reports/q_margin_planning_point.md (`report_margin`).
All physical constants come from `cavity.provenance.constants` (§6T).
"""
