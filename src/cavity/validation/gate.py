"""SPEC §5 Phase-1 validation gate.

All numerical targets live in `cavity.provenance.TARGETS` — this module
must import them, never re-type them. The §5 table:

  - Analytic benchmark passes      empty-cavity TE_011 < 0.1% error      (SPEC §8)
  - f                              1.45 GHz, >=4 s.f.                    (Booth, Breeze)
  - Booth two-point                Q approx 6,980, V_mode approx 0.409 cm^3
                                   at Booth geometry, walls on           (TARGETS.booth)
  - Confinement trend              tightening toward V_mode = 0.2 cm^3
                                   raises Q toward ~10,000               (TARGETS.breeze)
  - Wall-loss split                Q_diel in [9k, 10k], wall fraction
                                   23-27%                                (SPEC §4, TARGETS.q_diel_*)
  - F_m                            order 1e7 via SPEC §3 formula         (TARGETS.breeze.f_m)

Each modelled target carries its own eps_r — reproducing Breeze's 10,000
uses 318, reproducing Booth's 6,980 uses 316.3. Do not chase one with the
other's eps_r.

Depends on the COMSOL forward model + extraction. Not yet implemented.
"""

from cavity.provenance import TARGETS

__all__ = ["TARGETS"]
