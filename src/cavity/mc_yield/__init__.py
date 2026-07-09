"""Monte Carlo thermal-robustness aggregation — SPEC §7 (Layer C).

Latin-hypercube / Sobol sampling of the Layer A surrogate, with the
RETARGETED output layer (SPEC §7/§10, 2026-07-09 docstring sync): no
thresholding at C0 > 1 — per draw, compute Δf_max = (κc/2)·√(C0 − 1)
and the ΔT_max / P_max inversions (the per-draw maps live in
`cavity.thermal.detuning`; a below-threshold draw simply has zero
margin), then report the distributions p(Δf_max), p(ΔT_max), p(P_max)
plus Sobol sensitivity indices for the tolerance budget. The old
static-yield outputs (f-detuning vs tuner range, untunable C > 1
fraction) are superseded.

Ports the SiPhON infrastructure. Not yet implemented — blocked on
Layer A (the surrogate over the DOF space), not on the per-draw maps.
Rename candidate (`robustness/` / `thermal_margin/`) flagged in SPEC
§10; undecided, supervisor call.
"""
