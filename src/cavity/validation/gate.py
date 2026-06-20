"""SPEC §5 Phase-1 validation gate.

Targets (must all pass before Phase 2 is touched):

  - f                 1.45 GHz to >=4 s.f.                   (Booth, Breeze)
  - Booth two-point   Q approx 6980, V_mode approx 0.409 cm^3 at Booth geom
  - Confinement trend tightening toward V_mode = 0.2 cm^3 raises Q to ~10,000
  - Wall-loss split   Q_diel approx 9-10k; wall fraction 23-27%   (SPEC §4)
  - F_m               order 1e7 via SPEC §3 formula             (Breeze 3.6e7)

Depends on the COMSOL forward model + extraction. Not yet implemented.
"""
