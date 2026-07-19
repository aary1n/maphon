"""SPEC 2026-07-16 outcome 5 — S-ladder anchors (§8 discipline, no COMSOL).

Profile block: the chord-averaged m = 0 side-fire deposition
(`cavity.thermal.side_deposition`) against independent quadrature and its
closed-form optically-thin limit. Bracket/report block: the S4 lower/upper
bracket ordering, the layered-spot half-space anchor, and the
`thermal/reports/s_ladder_ballpark.md` exact-content pin with
independently recomputed numbers (scoping-numbers-are-computed rule).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.integrate import quad
from scipy.special import j0, j1, jn_zeros

from cavity.provenance.constants import CRYSTAL, K_PTP, L_ABS_PUMP
from cavity.thermal.side_deposition import (
    azimuthal_average,
    chord_path_length,
    radial_nodes,
    side_projection,
    thin_limit_profile,
)

R = CRYSTAL.diameter_m / 2.0  # 1.5e-3 m — planning dims, transfer flag riding
BETA = 1.2e-3 / (2.0 * R)  # w_b/(2R): PRL SM beam minor width 1.2 mm → 0.4


# --- side-deposition profile -------------------------------------------------


def test_f_side_normalisation_exact_across_grid():
    """Module node set integrates the profile as well as adaptive quadrature:
    2∫₀¹ I ρ dρ agrees with scipy.quad across the l_abs scoping grid ∪ ∞."""
    for l_abs in (*L_ABS_PUMP.l_abs_scoping_grid_m, math.inf):
        ell = l_abs / R
        rho, wts = radial_nodes(60.0, BETA, ell)
        fixed = 2.0 * float(np.sum(wts * azimuthal_average(rho, BETA, ell) * rho))
        pts = [BETA]
        if not math.isinf(ell):
            pts += [
                1.0 - s * ell
                for s in (48.0, 16.0, 4.0, 1.0)
                if s * ell < 1.0
            ]
        adaptive, _ = quad(
            lambda r: float(azimuthal_average(np.array([r]), BETA, ell)[0]) * r,
            0.0,
            1.0,
            points=sorted(pts),
            limit=400,
        )
        assert abs(fixed - 2.0 * adaptive) < 1e-8 * abs(2.0 * adaptive)


def test_f_side_thin_limit_matches_arcsin_closed_form():
    """Finite-ℓ quadrature → the closed-form azimuthal beam fraction as
    ℓ → ∞ (e^(−s/ℓ) → 1; s ≤ 2 so the relative error is O(2/ℓ)). Chord
    geometry pinned first: the closed form stands on s(ρ, φ)."""
    # s(ρ, φ): entry rim s = 0 at (1, π); full diameter s = 2 at (1, 0);
    # centre s = 1 for every φ
    assert chord_path_length(np.array(1.0), np.array(math.pi)) == pytest.approx(
        0.0, abs=1e-12
    )
    assert chord_path_length(np.array(1.0), np.array(0.0)) == pytest.approx(2.0)
    phis = np.linspace(0.0, math.pi, 9)
    assert np.allclose(chord_path_length(np.zeros_like(phis), phis), 1.0)
    rho = np.linspace(0.01, 0.999, 41)
    huge = azimuthal_average(rho, BETA, 1e8)
    closed = thin_limit_profile(rho, BETA)
    assert np.max(np.abs(huge - closed)) < 1e-6
    # and the ℓ = ∞ branch IS the closed form (plus the ρ ≤ β plateau = 1)
    assert np.allclose(azimuthal_average(rho, BETA, math.inf), closed)
    assert closed[rho <= BETA].min() == 1.0


def test_f_side_projection_matches_independent_quadrature():
    """f̂ₙ from the graded fixed-node projection vs an independent adaptive
    route (scipy.quad numerator and normalisation), at a mid-grid l_abs."""
    ell = 50e-6 / R
    x = jn_zeros(0, 24)
    n_hat = 0.5 * (j0(x) ** 2 + j1(x) ** 2)
    proj = side_projection(x, n_hat, BETA, ell)
    pts = sorted([BETA] + [1.0 - s * ell for s in (16.0, 8.0, 4.0, 2.0, 1.0)])

    def profile(r: float) -> float:
        return float(azimuthal_average(np.array([r]), BETA, ell)[0])

    norm, _ = quad(lambda r: profile(r) * r, 0.0, 1.0, points=pts, limit=400)
    for n in (0, 4, 23):
        num, _ = quad(
            lambda r: profile(r) * j0(x[n] * r) * r,
            0.0,
            1.0,
            points=pts,
            limit=400,
        )
        ref = num / (2.0 * norm) / n_hat[n]
        assert abs(proj[n] - ref) < 1e-7 * max(1.0, abs(ref))


def test_f_side_centroid_moves_outward_as_l_abs_shrinks():
    """Sharper absorption hugs the entry rim: the profile's mean radius
    2∫ f̂ ρ² dρ / (2∫ f̂ ρ dρ) increases monotonically as l_abs decreases
    through the scoping grid from the ∞ (optically-thin) limit."""
    centroids = []
    for l_abs in (math.inf, *reversed(L_ABS_PUMP.l_abs_scoping_grid_m)):
        ell = l_abs / R
        rho, wts = radial_nodes(60.0, BETA, ell)
        prof = azimuthal_average(rho, BETA, ell)
        centroids.append(
            float(np.sum(wts * prof * rho**2) / np.sum(wts * prof * rho))
        )
    assert all(b > a for a, b in zip(centroids, centroids[1:]))
    # entry-rim shell: at the sharpest grid point the centroid is near ρ = 1
    assert centroids[-1] > 0.9
