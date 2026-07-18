"""Ratified sentinel resolutions — the non-mock register.

Strictly separate from `mock_resolutions()` (dofs.py): every entry
here is a RATIFIED answer on the record, carried at its stated rung
and entering the machinery through `SentinelResolution` — the only
path. Q2/Q9 land here when they resolve. The context this module
builds is PARTIAL by construction (Q11 only, as of 2026-07-17):
Q2/Q9 remain unresolved, so every solve-ready exit still refuses.
"""

from __future__ import annotations

from cavity.sweep.dofs import ResolutionContext, Rung, SentinelResolution

RESOLUTION_Q11 = SentinelResolution(
    question_id="Q11",
    payload={
        "crystal_epsilon_r": 3.0,
        # Nothing consumes the band yet: it rides as an extra key
        # (the validator permits extras) — machine-readable
        # uncertainty metadata for a future Phase 1b eps_r
        # sensitivity check, mirroring Q9's band-carrying pattern.
        "crystal_epsilon_r_band": (2.4, 4.1),
    },
    rung=Rung.PLANNING_ASSUMPTION,
    mock=False,
    provenance=(
        "(i) point 3.0 = round central planning value (band mid 3.25; "
        "anthracene isotropic mean 3.13); band [2.4, 4.1] = principal "
        "optical permittivities of crystalline anthracene, eps_xx 2.42 "
        "/ eps_yy 2.90 / eps_zz 4.07 (±0.05), Cummins & Dunmur 1974, "
        "J. Phys. D: Appl. Phys. 7, 451 (Zotero WNLM2C8X), immersion "
        "method — refractive-index-derived, i.e. OPTICAL-frequency "
        "values. (ii) Three-layer inference chain, each layer "
        "planning-tier: chemical-class analogy anthracene -> "
        "p-terphenyl; optical -> static/microwave extrapolation, "
        "justified only by both crystals being nonpolar rigid "
        "aromatics (no orientational/Debye contribution expected "
        "between optical and microwave); consequence of either layer "
        "failing bounded by Breeze 2017 <1% electric filling. "
        "(iii) Consistency: below CRYSTAL.epsilon_r_upper_bound "
        "(Breeze 'eps_r < 5') by construction. (iv) Negative space: "
        "direct p-terphenyl static/microwave permittivity NOT FOUND, "
        "literature trace 2026-07-17; Selvakumar et al. 2014 (J. Mol. "
        "Struct. 1056-1057, 152, Zotero KCDCRN4C) examined and "
        "REJECTED — eps_r 5760 @ 1 kHz is electrode/Maxwell-Wagner "
        "polarization per the paper's own attribution, unusable at "
        "any grade."
    ),
)

#: Every ratified resolution on record, in question order.
RATIFIED_RESOLUTIONS: tuple[SentinelResolution, ...] = (RESOLUTION_Q11,)


def ratified_resolutions() -> ResolutionContext:
    """Every ratified (non-mock) resolution on record — Q11 only as
    of 2026-07-17. PARTIAL by construction: Q2/Q9 remain unresolved,
    so every solve-ready exit still refuses."""
    return ResolutionContext(resolutions=RATIFIED_RESOLUTIONS)
