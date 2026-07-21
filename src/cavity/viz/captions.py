"""Committed status-flag tokens for the viz bundles (viz/PLAN.md, R4).

DERIVED AND SUBORDINATE (R4 condition b): every token below is a
verbatim substring of its source figure CAPTION — `FLAG_SOURCES` maps
each token to the module whose committed CAPTION carries it — and the
cross-pin test (tests/test_viz_bundles.py::test_captions_cross_pin)
fails on any orphan token with no caption source, so this list can
never drift ahead of the captions. On any conflict the CAPTIONs win
and the token list changes here — never the reverse.

Bundle emitters import these constants; flag strings are never retyped
inline (R4 condition a). Emission order of any flag list is the
declaration order below (`FLAG_ORDER`).
"""

from __future__ import annotations

# source caption for the V1 heatmap view tokens
F3_MODULE = "cavity.figures.f3_delta_t_map"

FLAG_ILLUSTRATIVE = "ILLUSTRATIVE"
FLAG_UNSOURCED_SCOPING = "UNSOURCED-SCOPING"
FLAG_PLANNING_ASSUMPTIONS = (
    "planning assumptions pending Oxborrow (§11 item-10 bundle)"
)
FLAG_LINEAR_IN_P = "ΔT is strictly linear in P — rescale freely"
FLAG_FLOOD_D3 = "flood radial profile (D3)"
FLAG_END_FIRE_D2 = (
    "END-FIRE axial Beer-Lambert deposition (D2 — supervisor-preferred, "
    "Oxborrow-verbal 2026-07-08; side-fire structurally outside the "
    "axisymmetric eigenbasis)"
)
FLAG_NOMINAL_DOPING = (
    "nominal-doping arithmetic would overstate absorption — "
    "Oxborrow-verbal 2026-07-06"
)
FLAG_K_FLOOR_LIQUID = "the 0.1 floor's provenance is a liquid-phase value"
FLAG_H_CONV_CEILING = (
    "free-convection ceiling — both real geometries likely sit below the "
    "5–20 band"
)
FLAG_H_RAD_BAND = (
    "linearised radiation at ε = 0.90 of the ratified 0.80–0.95 band"
)
FLAG_BASE_DIRICHLET_D1 = "Dirichlet base ('substrate at room temperature')"

# token → module exposing the CAPTION that carries it verbatim (the
# cross-pin registry; a token missing here, or whose source CAPTION does
# not contain it, fails the R4 test)
FLAG_SOURCES: dict[str, str] = {
    FLAG_ILLUSTRATIVE: F3_MODULE,
    FLAG_UNSOURCED_SCOPING: F3_MODULE,
    FLAG_PLANNING_ASSUMPTIONS: F3_MODULE,
    FLAG_LINEAR_IN_P: F3_MODULE,
    FLAG_FLOOD_D3: F3_MODULE,
    FLAG_END_FIRE_D2: F3_MODULE,
    FLAG_NOMINAL_DOPING: F3_MODULE,
    FLAG_K_FLOOR_LIQUID: F3_MODULE,
    FLAG_H_CONV_CEILING: F3_MODULE,
    FLAG_H_RAD_BAND: F3_MODULE,
    FLAG_BASE_DIRICHLET_D1: F3_MODULE,
}

# canonical emission order = declaration order
FLAG_ORDER: tuple[str, ...] = tuple(FLAG_SOURCES)


def ordered_flags(flags) -> list[str]:
    """Deduplicate and sort a flag collection into FLAG_ORDER; reject any
    string that is not a registered token (the never-retyped-inline
    guarantee, enforced structurally)."""
    unique = set(flags)
    unknown = unique - set(FLAG_ORDER)
    if unknown:
        raise ValueError(f"unregistered flag tokens: {sorted(unknown)}")
    return [f for f in FLAG_ORDER if f in unique]
