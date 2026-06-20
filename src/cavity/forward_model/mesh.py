"""SPEC §2 — mesh strategy for the eigenfrequency study.

Edge-element FEA mishandles sharp corners on the dielectric (Booth flags
this explicitly); the dielectric boundary must be **fully curved** for
any trusted Q. We run a convergence study refining the dielectric mesh
until f and Q stabilise to the SPEC §5 significant-figure targets.

Pure Python config. The runner (lazy-imports MPh) lives with
`build.py` / `solve.py`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MeshConfig:
    """Mesh settings for one solve.

    `dielectric_max_h_m` / `air_max_h_m`: maximum element size in each
    region (m). Booth's recipe is "extremely fine" inside the puck; the
    convergence runner shrinks these until f / Q stabilise.

    `curved_dielectric_boundary`: must be True for any trusted Q (SPEC
    §2). Exposed only so the convergence runner can flip it for the
    diagnostic comparison that demonstrates why straight segments here
    poison Q.
    """

    dielectric_max_h_m: float = 1.0e-4
    air_max_h_m: float = 5.0e-4
    curved_dielectric_boundary: bool = True

    def __post_init__(self) -> None:
        if self.dielectric_max_h_m <= 0 or self.air_max_h_m <= 0:
            raise ValueError("mesh element sizes must be positive")


@dataclass(frozen=True)
class ConvergenceCriterion:
    """Stop the convergence study when f and Q are stable to this many s.f.

    Targets follow SPEC §5: f to >=4 s.f. (Booth localises to 5 s.f.);
    Q to ~3 s.f. (Booth quotes 6,980 = 4 s.f., but mesh-limited stability
    at the third figure is the realistic stopping criterion).
    """

    f_sig_figs: int = 4
    q_sig_figs: int = 3
    max_refinements: int = 6

    def __post_init__(self) -> None:
        if self.f_sig_figs < 1 or self.q_sig_figs < 1:
            raise ValueError("significant-figure targets must be >= 1")
        if self.max_refinements < 1:
            raise ValueError("max_refinements must be >= 1")
