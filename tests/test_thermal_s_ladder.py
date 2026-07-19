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


# --- S4 bracket pair + the report artifact -----------------------------------


@pytest.fixture(scope="module")
def report_text() -> str:
    from cavity.thermal.report_s_ladder import build_report

    return build_report()


def test_s4_upper_bracket_exceeds_m0_lower_across_grid():
    """The spot upper bracket (larger member per l_abs) exceeds the m = 0
    lower bracket's insulated-side equatorial peak — the structural
    bracket ordering, per l_abs."""
    from cavity.thermal.report_s_ladder import (
        K_MID,
        R_M,
        s4_lower_cell,
        upper_disc_center_k_per_w,
        upper_volumetric_k_per_w,
    )

    disc = upper_disc_center_k_per_w(K_MID, 2.0 * R_M)
    for l_abs in (5e-6, 200e-6, math.inf):
        lower = s4_lower_cell(l_abs, side_dirichlet=False)["peak_eq"]
        members = [disc]
        if not math.isinf(l_abs):
            members.append(upper_volumetric_k_per_w(K_MID, 2.0 * R_M, l_abs))
        assert max(members) > lower


def test_spot_estimate_anchored_to_half_space_closed_form():
    """layered.py members against the half-space closed forms: uniform-flux
    disc centre P/(π·a·k) and Gaussian centre P/(√(2π)·a·k) — thick-slab
    agreement ≤0.1%, and the 2R slab sits BELOW (cold far face only
    removes resistance)."""
    from cavity.thermal.layered import Layer, delta_t_disk_center, delta_t_gaussian
    from cavity.thermal.report_s_ladder import A_EQ, K_MID, R_M

    thick = [Layer(0.5, K_MID)]
    disc_ref = 1.0 / (math.pi * A_EQ * K_MID)
    disc = delta_t_disk_center(thick, 1.0, A_EQ, n_zeros=2000)
    assert abs(disc - disc_ref) / disc_ref < 1e-3
    gauss_ref = 1.0 / (math.sqrt(2.0 * math.pi) * A_EQ * K_MID)
    gauss = float(delta_t_gaussian(0.0, thick, 1.0, A_EQ))
    assert abs(gauss - gauss_ref) / gauss_ref < 1e-3
    assert delta_t_disk_center([Layer(2.0 * R_M, K_MID)], 1.0, A_EQ) < disc


def test_report_regenerates_byte_identical(report_text):
    """The committed artifact IS the generator's output (content-exact pin,
    the report_margin precedent)."""
    from pathlib import Path

    committed = (
        Path(__file__).resolve().parents[1]
        / "thermal"
        / "reports"
        / "s_ladder_ballpark.md"
    ).read_text(encoding="utf-8")
    assert committed == report_text


def test_report_numbers_match_independent_recomputation(report_text):
    """Key pinned numbers re-derived from the graded constants by
    independent arithmetic (scoping-numbers-are-computed rule)."""
    r = CRYSTAL.diameter_m / 2.0
    length = CRYSTAL.height_m
    k_mid = K_PTP.k_mid_w_m_k
    g_mid = k_mid * math.pi * r**2 / length
    assert f"{g_mid:.4e}" in report_text  # 2.7941e-04 W/K
    assert f"{0.01 / g_mid:.3g}" in report_text  # 35.8 K @ 10 mW
    a_eq = math.sqrt((2.0e-3 / 2.0) * (1.2e-3 / 2.0))  # SM prints, re-keyed
    assert f"{1.0 / (math.pi * a_eq * k_mid):.0f} K/W" in report_text
    assert f"{1.0 / (math.sqrt(2.0 * math.pi) * a_eq * k_mid):.0f} K/W" in report_text
    assert f"a_eq = sqrt((h_b/2)(w_b/2)) = {a_eq*1e3:.3f} mm" in report_text


def test_report_carries_verbatim_s4_systematic_sentence(report_text):
    from cavity.thermal.report_s_ladder import S4_SYSTEMATIC

    assert S4_SYSTEMATIC.startswith(
        "In side-fire the heat source and the gain region are the same "
        "illuminated prism;"
    )
    assert "structural LOWER bracket on gain-weighted heating" in S4_SYSTEMATIC
    assert S4_SYSTEMATIC in report_text


def test_report_reserves_s3_and_defers_s5_and_states_steady_reading(report_text):
    assert "S3: label RESERVED" in report_text
    assert "S5: logged-DEFERRED" in report_text
    assert "NO SHOT REPETITION RATE IS IN PRINT" in report_text
    assert "steady-state" in report_text
    assert "UNSOURCED-SCOPING" in report_text
