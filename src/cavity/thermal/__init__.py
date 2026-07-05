"""SPEC §7T — analytical thermal submodel (Layer B engine).

Two anchor geometries (SPEC §7.T1 geometry split):

- `layered`: Gaussian-spot spreading resistance on a layered medium
  (Hankel transform) — the Glasgow calibration-rig anchor (§7.T5).
- (future) cylinder Bessel/Robin — the maser-crystal anchor.

`identifiability` runs the §7.T5 check-3a sweep on top of `layered`.
`volumetric_3a` re-checks the PLATE k–w degeneracy with the volumetric
(Beer-Lambert) source (`layered.delta_t_gaussian_volumetric`) — the
appendix to the 3a decision report.
All physical constants come from `cavity.provenance.constants` (§6T).
"""
