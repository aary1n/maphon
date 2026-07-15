"""Surrogate layer — SPEC §7-expanded §7.5 / design doc §9.

ZERO-LICENCE tier implemented per docs/plans/ticklish-possum.md
(ratified 2026-07-15): PCE on the RAW output basis (Q7 ruling — f,
ln Q₀, ln η_H, ln V_mode, p_e; C₀/κc composed downstream in
`cavity.sweep.compose`) and the composed-space CV gate carrying the
ratified Q8 thresholds (5% of P5 Δf_max; f RMSE ≤ 10% of the
population-minimum κc — thresholds recompute from the sweep's own
population; every gate report prints its κs branch).

Later passes (stated, not silent): LARS order-3 sparse enrichment
(rider R3 deferral), the GP cross-check + active learning, and
Sobol-from-coefficients.
"""

from cavity.surrogate.pce import (
    PCESurrogate,
    legendre_orthonormal_1d,
    n_basis_terms,
    total_degree_indices,
)
from cavity.surrogate.cv_gate import (
    GateThresholds,
    Q8_RATIFICATION,
    evaluate_cv_gate,
    planning_threshold_pins,
)

__all__ = [
    "GateThresholds",
    "PCESurrogate",
    "Q8_RATIFICATION",
    "evaluate_cv_gate",
    "legendre_orthonormal_1d",
    "n_basis_terms",
    "planning_threshold_pins",
    "total_degree_indices",
]
