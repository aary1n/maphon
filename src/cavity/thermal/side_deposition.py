"""SPEC 2026-07-16 outcome 5, S4 — chord-averaged side-fire deposition (m = 0).

The azimuthally-smeared radial profile of a horizontal, near-collimated side
beam traversing the crystal cylinder along Beer-Lambert-absorbing chords —
extension (A) of the scenario ladder: the m = 0 azimuthal average ONLY. The
m > 0 harmonics of the true (azimuthally localised) prism are DEFERRED with
a decision gate (eccentricity-route discipline; SPEC outcome 5). Consumed by
`cavity.thermal.cylinder` as the `side_chord` radial form; the axial factor
(a band at beam height) lives in the solver, not here.

Geometry and conventions
------------------------
Dimensionless radius ρ = r/R. Rays travel in the +x direction, entering the
unit disc at x = −√(1 − y²); the in-crystal path to the point (x, y) is
s = x + √(1 − y²) ∈ [0, 2]. Beer-Lambert deposition per unit length is
∝ e^(−s/ℓ) with ℓ = l_abs/R (constant prefactors are absorbed by the
normalisation). The beam is uniform across its width w_b (planning
assumption — the PRL SM prints dims only; `provenance.WU_PUMP_BEAM`), so a
point (ρ, φ) is illuminated iff |ρ sin φ| ≤ β, β = w_b/(2R). The m = 0
profile is the azimuthal average (half-range by the φ → −φ symmetry; the
φ → π − φ symmetry is broken by the entry/exit asymmetry of s):

    I(ρ) = (1/π) ∫₀^π 1{ρ sin φ ≤ β} · e^(−s(ρ, φ)/ℓ) dφ

ℓ = math.inf is the BLEACHED OPTICALLY-THIN limit (Wu PRL SM Eq. S2→S3
regime statement): deposition uniform along chords, closed form

    I_∞(ρ) = 1 for ρ ≤ β;  (2/π)·arcsin(β/ρ) for ρ > β

(the azimuthal beam fraction), used as the quadrature anchor. The finite-ℓ
integral has no closed form (exponential of a square root); it is evaluated
by fixed Gauss-Legendre quadrature split EXACTLY at the indicator kinks
φ₁ = arcsin(β/ρ) — the same fixed-quadrature convention as the Gaussian
radial form in `cylinder.py`.

Normalisation (D4-consistent): the solver's radial factor is
f̂(ρ) = C·I(ρ) with 2∫₀¹ f̂ ρ dρ = 1 — truncated-RENORMALISED, so the
deposited power is exactly P = ABSORBED power, identical in meaning to the
end-fire Beer-Lambert convention. The incident→absorbed mapping (chord
absorbed fractions) is a report diagnostic, never a solver input.

Radial quadrature: the profile develops a shell of width ~ℓ at ρ = 1 as
ℓ → 0 (deposition hugs the entry rim), and a derivative kink at ρ = β.
`radial_nodes` therefore grades the Gauss-Legendre panels: a split at β,
plus dyadic refinement panels over the last ~48ℓ before ρ = 1 when ℓ is
small. Node counts follow the x_max-scaled rule of `_radial_projection`
(resolve J₀(x_max·ρ)); adequacy is asserted against adaptive quadrature in
tests/test_thermal_s_ladder.py, and solve-level convergence is gated by
`tail_estimate_rel` + the `boundary_power_w` deficit as usual.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import j0

_PHI_NODES = 48  # fixed G-L nodes per smooth azimuthal panel (doubling-tested)


def chord_path_length(rho: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """In-crystal path s(ρ, φ) = ρ·cosφ + √(1 − ρ²sin²φ), broadcast."""
    rho = np.asarray(rho, dtype=float)
    phi = np.asarray(phi, dtype=float)
    sin2 = np.sin(phi) ** 2
    return rho * np.cos(phi) + np.sqrt(np.clip(1.0 - rho**2 * sin2, 0.0, None))


def thin_limit_profile(rho: np.ndarray, beta: float) -> np.ndarray:
    """Closed-form ℓ = ∞ profile I_∞(ρ): the azimuthal beam fraction."""
    rho = np.asarray(rho, dtype=float)
    out = np.ones_like(rho)
    outside = rho > beta
    out[outside] = (2.0 / math.pi) * np.arcsin(beta / rho[outside])
    return out


def azimuthal_average(rho: np.ndarray, beta: float, ell: float) -> np.ndarray:
    """I(ρ) at the given ρ points (unnormalised; ell = math.inf allowed)."""
    if not beta > 0.0:
        raise ValueError("beam half-width fraction beta must be positive")
    if not ell > 0.0:
        raise ValueError("dimensionless absorption length ell must be positive")
    rho = np.atleast_1d(np.asarray(rho, dtype=float))
    if math.isinf(ell):
        return thin_limit_profile(rho, beta)
    nodes, weights = np.polynomial.legendre.leggauss(_PHI_NODES)
    out = np.empty_like(rho)
    for i, r in enumerate(rho):
        if r <= beta:
            panels = [(0.0, math.pi)]
        else:
            phi1 = math.asin(beta / r)
            panels = [(0.0, phi1), (math.pi - phi1, math.pi)]
        total = 0.0
        for lo, hi in panels:
            phi = 0.5 * (hi - lo) * (nodes + 1.0) + lo
            wts = 0.5 * (hi - lo) * weights
            total += float(
                np.sum(wts * np.exp(-chord_path_length(r, phi) / ell))
            )
        out[i] = total / math.pi
    return out


def radial_nodes(
    x_max: float, beta: float, ell: float
) -> tuple[np.ndarray, np.ndarray]:
    """Graded Gauss-Legendre nodes/weights on ρ ∈ [0, 1]: panel breaks at the
    β kink and (finite ℓ only) dyadic shell panels over the last ~16ℓ before
    ρ = 1; per-panel counts follow the x_max-scaled J₀-resolution rule."""
    breaks = {0.0, 1.0}
    if 0.0 < beta < 1.0:
        breaks.add(beta)
    if not math.isinf(ell):
        # deepest panel edge at 48ℓ: the tail beyond it is O(e⁻⁴⁸) of the
        # shell peak — negligible on the coarse interior panel (16ℓ was not:
        # an O(e⁻¹⁶) ≈ 1e-7 tail under-resolved there fails the 1e-8 anchor)
        for scale in (48.0, 32.0, 16.0, 8.0, 4.0, 2.0, 1.0):
            edge = 1.0 - scale * ell
            if 0.0 < edge < 1.0:
                breaks.add(edge)
    edges = sorted(breaks)
    all_nodes, all_wts = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        n = max(24, int(0.5 * x_max * (hi - lo)) + 24)
        nodes, weights = np.polynomial.legendre.leggauss(n)
        if lo == beta:
            # the profile has a √(ρ−β) derivative cusp at the beam edge
            # (sharpest in the ℓ = ∞ arcsin form); ρ = β + u² renders the
            # panel analytic in u — dρ = 2u du folded into the weights
            u_hi = math.sqrt(hi - lo)
            u = 0.5 * u_hi * (nodes + 1.0)
            all_nodes.append(lo + u**2)
            all_wts.append(0.5 * u_hi * weights * 2.0 * u)
        else:
            all_nodes.append(0.5 * (hi - lo) * (nodes + 1.0) + lo)
            all_wts.append(0.5 * (hi - lo) * weights)
    return np.concatenate(all_nodes), np.concatenate(all_wts)


def side_projection(
    x: np.ndarray, n_hat: np.ndarray, beta: float, ell: float
) -> np.ndarray:
    """Dimensionless projections f̂ₙ = (1/N̂ₙ)∫₀¹ f̂(ρ) J₀(xₙρ) ρ dρ of the
    renormalised chord-averaged profile, for the positive radial modes.
    (The constant-mode projection is f̂₀ = 1 exactly, by normalisation —
    carried by the solver, not here.)"""
    x = np.asarray(x, dtype=float)
    x_max = float(x[-1]) if x.size else 0.0
    rho, wts = radial_nodes(x_max, beta, ell)
    profile = azimuthal_average(rho, beta, ell)
    norm = 2.0 * float(np.sum(wts * profile * rho))  # 2∫ I ρ dρ ⇒ C = 1/norm
    kern = (profile / norm) * rho * wts  # f̂(ρ)·ρ·w with f̂ = C·I
    return (j0(np.outer(x, rho)) @ kern) / n_hat
