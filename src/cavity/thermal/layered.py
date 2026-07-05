"""SPEC §7T / §7.T5 — steady-state Gaussian-spot heating of a layered medium.

Axisymmetric steady conduction in a stack of homogeneous layers
(PTP / wax / glass in the Glasgow-rig instance), heated from above by a
prescribed surface heat flux and grounded from below by an isothermal
base at bath temperature. Solved by zeroth-order Hankel transform; this
is the "Gaussian-spot spreading resistance on a layered medium" anchor
that SPEC §7.T1/§7.T5 assigns to the calibration-rig geometry.

Geometry and conventions
------------------------
z increases DOWNWARD from the heated surface z = 0. Layer i has
thickness t_i and conductivity k_i; the base of the last layer is held
at the bath temperature (ΔT = 0). ΔT(r, z) below is the steady rise
above bath. The top surface carries the absorbed optical flux q(r)
plus an optional Robin loss term (heat transfer coefficient h to an
ambient at bath temperature); h = 0 is the insulated-top default.

The insulated-top default is an idealisation, not a theorem: free
convection + linearised radiation give h ~ 5–20 W m⁻² K⁻¹, and for a
mm-thick low-k stack the integrated top loss is not Biot-trivially
zero. It is therefore kept SWITCHABLE and quantified as a sensitivity
in the §7.T5 sweep report rather than argued away.

Hankel-transform solution
-------------------------
With θ(ξ, z) = ∫₀^∞ ΔT(r, z) J₀(ξr) r dr, Laplace's equation in each
layer becomes θ'' = ξ²θ. Writing the downward flux transform
φ = −k ∂θ/∂z, each layer maps (θ, φ) top→bottom by the standard
transfer matrix; equivalently (and numerically stably, since tanh
saturates instead of cosh overflowing) the stack is a transmission
line with per-layer characteristic impedance Z₀ = 1/(kξ) and
propagation constant ξ:

    Z_in = Z₀ · (Z_load + Z₀ tanh(ξt)) / (Z₀ + Z_load tanh(ξt))

recursed bottom-up from Z_load = 0 at the isothermal base (a
semi-infinite layer terminates the recursion with Z_in = Z₀). The
surface temperature transform is then

    θ(ξ, 0) = q̂(ξ) · Z_in(ξ) / (1 + h · Z_in(ξ))

and ΔT(r, 0) = ∫₀^∞ θ(ξ, 0) J₀(ξr) ξ dξ (inverse Hankel).

At ξ → 0, Z_in → Σ t_i/k_i (the 1-D series resistance); at ξ → ∞,
Z_in → 1/(k₁ξ) (the top layer looks semi-infinite). Those two limits
are exactly the anchors of tests/test_thermal_layered.py.

Flux transforms (both normalised to total power P):

    Gaussian, 1/e² radius w:  q(r) = (2P/πw²) exp(−2r²/w²)
                              q̂(ξ) = (P/2π) exp(−ξ²w²/8)
    Uniform disk, radius a:   q(r) = P/(πa²), r < a
                              q̂(ξ) = P J₁(ξa) / (πaξ)

Closed-form anchors (derivations; cited forms)
----------------------------------------------
Semi-infinite single layer (Z_in = 1/(kξ)):

1. Uniform-disk flux, centre:  ΔT(0,0) = ∫ q̂/(kξ)·ξ dξ
   = P/(πak) ∫₀^∞ J₁(x)/x dx = **P/(πak)**.
2. Uniform-disk flux, disk-average:
   ΔT̄ = (2P/(πa²)) ∫ Z_in J₁(ξa)²/ξ dξ = (2P/(πa²k)) ∫ J₁(x)²/x² dx·a
   = **8P/(3π²ka)**  (∫₀^∞ J₁(x)²x⁻² dx = 4/(3π)).
   Both are the classical spreading-resistance results for flux-
   specified contacts: Carslaw & Jaeger, *Conduction of Heat in
   Solids*, 2nd ed., §8.2; Yovanovich & Antonetti's spreading-
   resistance reviews. NOTE the ISOTHERMAL-disk form ΔT = P/(4ka)
   (Carslaw & Jaeger §8.2, constant-temperature disk) is a DIFFERENT
   boundary condition: 8P/(3π²ka) = (32/3π²)·P/(4ka) ≈ 1.081·P/(4ka),
   the classical 8% isoflux/isothermal constriction gap. The anchor
   test asserts the exact isoflux forms and the 1.081 ratio, not
   equality with P/(4ka).
3. Gaussian flux, centre:  ΔT(0,0) = (P/2πk) ∫₀^∞ e^{−ξ²w²/8} dξ
   = (P/2πk)·√(2π)/w = **P/(√(2π)·k·w)**.
   Full surface profile, using ∫₀^∞ e^{−βξ²} J₀(ξr) dξ
   = (√π / 2√β) e^{−r²/8β} I₀(r²/8β) with β = w²/8:
   **ΔT(r,0) = ΔT(0,0) · e^{−r²/w²} I₀(r²/w²)**.
   This is the Gaussian-source analogue of the disk result — same
   family as Lax, J. Appl. Phys. 48, 3919 (1977) (beware Lax's 1/e
   beam-radius convention; the forms above are derived self-
   contained for the 1/e² radius w and asserted numerically).

Thin-stack / 1-D limit (w ≫ all thicknesses): the Gaussian support in
ξ is ≲ 3/w, where tanh(ξt) ≈ ξt, so Z_in ≈ Σt_i/k_i uniformly and
ΔT(0,0) → (2P/πw²)·Σ t_i/k_i = q(0)·ΣR_i — the series-resistance slab
formula under the local flux at r = 0.

Volumetric (Beer-Lambert) source — the buried-source extension
---------------------------------------------------------------
The surface-flux model above deposits the pump at z = 0; the real pump
is absorbed volumetrically along the beam. `delta_t_gaussian_volumetric`
models that: the source density is

    q̇(r, z) = P · (2/(πw²)) e^{−2r²/w²} · g(z),   0 ≤ z ≤ t₁ (top layer),

with the depth profile a TRUNCATED, RENORMALISED exponential

    g(z) = e^{−z/l_abs} / [ l_abs · (1 − e^{−t₁/l_abs}) ],

zero below the top layer. Renormalisation statement: the exponential is
cut at the bottom of the top (PTP) layer and rescaled so ∫₀^{t₁} g dz = 1
exactly — the fraction e^{−t₁/l_abs} that would be transmitted into the
substrate is folded back onto the layer rather than lost, so the total
absorbed power is exactly P for EVERY (w, l_abs). This is a modelling
choice (no absorption in wax/glass, no transmitted remainder), stated
here so the energy anchor is meaningful. The radial profile is taken
depth-independent (collimated beam over t₁; no divergence/refraction).

Hankel-space kernel: a source sheet of unit power at depth z′ inside
the top layer produces the surface temperature transform G(ξ, z′)·q̂(ξ).
In the transmission-line picture the sheet injects current at node z′,
which sees the upward line (length z′, terminated by the Robin load
1/h at z = 0 — open circuit when h = 0) in parallel with the downward
line (length t₁ − z′, terminated by the sub-stack impedance Z_sub);
the surface temperature follows from the upward-line voltage transfer.
Collapsing (Z_up ∥ Z_down)·T_up gives the single stable form

    G(ξ, z′) = Z₀·Z_dn / [ cosh(ξz′)·Z₀(1 + h·Z_dn)
                           + sinh(ξz′)·(h·Z₀² + Z_dn) ],

Z₀ = 1/(k₁ξ), Z_dn = impedance looking down from z′. Checks: z′ → 0
recovers the surface kernel Z_in/(1 + h·Z_in) exactly (incl. Robin);
a single layer on an isothermal base at h = 0 collapses to the
Sturm-Liouville Green's function sinh(ξ(t−z′))/(k ξ cosh(ξt)).

Depth integral K(ξ) = ∫₀^{t₁} g(z′) G(ξ, z′) dz′ — evaluated by
QUADRATURE, not the closed-form transfer-matrix integral: the closed
form is elementary only for a half-space below the source
(G = Z₀e^{−ξz′} ⇒ K = Z₀·(1−e^{−μt₁})/(μ·l_abs·(1−e^{−t₁/l_abs})),
μ = 1/l_abs + ξ); for a finite stack Z_dn(z′) makes the antiderivative
a non-elementary mix of exponentials with incommensurate rates. The
quadrature substitutes v = (1−e^{−μz′})/(1−e^{−μt₁}), which absorbs
both decay scales (absorption and ξ) into the measure; the transformed
integrand e^{ξz′}G(ξ, z′) is bounded, slowly varying, and EXACTLY
constant in the half-space case, so a fixed 64-node Gauss-Legendre
rule resolves it far below the outer quadrature tolerance.

Limits (the pytest anchors in tests/test_thermal_volumetric.py):
l_abs → 0 recovers the surface-flux solution (regression bridge);
l_abs ≫ t₁ approaches the uniform-generation slab, whose 1-D two-region
closed form is derived at `anchor_one_dimensional_uniform_generation`;
w ≫ thicknesses at ANY l_abs matches the general 1-D closed form at
`anchor_one_dimensional_volumetric`; and the power crossing the
isothermal base equals P (ξ → 0 Hankel limit), closing the energy
budget of the renormalised source.

Surface-flux caveat, superseded in part: for the §7.T5 identifiability
sweep the surface-flux deposition remains the headline model; the
volumetric extension exists to CHECK the k-w degeneracy against burial
of the near-spot source (SPEC §7.T5 3a appendix,
thermal/reports/identifiability_3a_volumetric.md), and for absolute ΔT
prediction once §6T's illumination model pins l_abs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import quad
from scipy.special import j0, j1, jn_zeros


@dataclass(frozen=True)
class Layer:
    """One homogeneous layer: thickness (m, may be math.inf) and k (W/m/K)."""

    thickness_m: float
    k_w_m_k: float

    def __post_init__(self) -> None:
        if not self.thickness_m > 0:
            raise ValueError("layer thickness must be positive")
        if not self.k_w_m_k > 0:
            raise ValueError("layer conductivity must be positive")


def series_resistance(layers: tuple[Layer, ...]) -> float:
    """1-D series resistance Σ t_i/k_i (m² K / W). Infinite for a half-space."""
    return sum(layer.thickness_m / layer.k_w_m_k for layer in layers)


def _tanh_over_x(x: np.ndarray | float) -> np.ndarray | float:
    """tanh(x)/x, stable at x -> 0 (limit 1)."""
    x = np.asarray(x, dtype=float)
    small = x < 1e-8
    safe = np.where(small, 1.0, x)
    return np.where(small, 1.0, np.tanh(safe) / safe)


def surface_impedance(
    xi: np.ndarray | float, layers: tuple[Layer, ...], h_top: float = 0.0
) -> np.ndarray | float:
    """Hankel-space surface response G(ξ) with θ(ξ,0) = G(ξ)·q̂(ξ).

    Bottom-up transmission-line recursion from the isothermal base
    (Z = 0); a layer with infinite thickness terminates the stack as a
    half-space (Z = 1/(kξ), layers below it are unreachable). The Robin
    coefficient `h_top` (W/m²/K, ambient at bath temperature) folds in
    as G = Z/(1 + h·Z); h_top = 0 is the insulated top.
    """
    xi = np.asarray(xi, dtype=float)
    z = np.zeros_like(xi)
    for layer in reversed(layers):
        t, k = layer.thickness_m, layer.k_w_m_k
        if math.isinf(t):
            with np.errstate(divide="ignore"):
                z = np.where(xi > 0, 1.0 / (k * xi), np.inf)
            continue
        tanh_xt = np.tanh(xi * t)
        # Z0*tanh(xi*t) = (t/k)*tanh(xi*t)/(xi*t), stable at xi -> 0
        z0_tanh = (t / k) * _tanh_over_x(xi * t)
        z = (z + z0_tanh) / (1.0 + z * k * xi * tanh_xt)
    if h_top != 0.0:
        z = z / (1.0 + h_top * z)
    return z


def gaussian_flux_hankel(
    xi: np.ndarray | float, p_w: float, w_m: float
) -> np.ndarray | float:
    """q̂(ξ) of a Gaussian surface flux, total power P, 1/e² radius w."""
    xi = np.asarray(xi, dtype=float)
    return (p_w / (2.0 * math.pi)) * np.exp(-(xi**2) * w_m**2 / 8.0)


def disk_flux_hankel(
    xi: np.ndarray | float, p_w: float, a_m: float
) -> np.ndarray | float:
    """q̂(ξ) of a uniform disk flux, total power P, radius a."""
    xi = np.asarray(xi, dtype=float)
    small = xi * a_m < 1e-8
    safe = np.where(small, 1.0, xi)
    # J1(x)/x -> 1/2 as x -> 0
    ratio = np.where(small, 0.5 * a_m, j1(safe * a_m) / safe)
    return (p_w / (math.pi * a_m)) * ratio


def delta_t_gaussian(
    r_m: float,
    layers: tuple[Layer, ...],
    p_w: float,
    w_m: float,
    h_top: float = 0.0,
) -> float:
    """Surface temperature rise ΔT(r, 0) under a Gaussian spot (K).

    The Gaussian factor exp(−ξ²w²/8) cuts the inverse-Hankel integrand
    off exponentially; integrate on [0, ξmax] with ξmax chosen so the
    dropped tail is < 1e-16 of the flux transform. Breakpoints at the
    inverse layer thicknesses steer the adaptive rule onto the scales
    where Z(ξ) turns over.
    """
    if w_m <= 0:
        raise ValueError("spot radius w must be positive")
    xi_max = math.sqrt(8.0 * 37.0) / w_m  # exp(-37) ~ 8e-17
    breakpoints = sorted(
        {1.0 / layer.thickness_m for layer in layers if math.isfinite(layer.thickness_m)}
        | {1.0 / w_m}
    )
    points = [b for b in breakpoints if 0.0 < b < xi_max]

    def integrand(xi: float) -> float:
        return (
            float(gaussian_flux_hankel(xi, p_w, w_m))
            * float(surface_impedance(xi, layers, h_top))
            * xi
            * j0(xi * r_m)
        )

    value, _ = quad(integrand, 0.0, xi_max, points=points, limit=400)
    return value


def _sum_between_bessel_zeros(
    integrand, zeros: np.ndarray, n_average: int = 6
) -> float:
    """∫₀^∞ of an oscillatory-decaying integrand, split at Bessel zeros.

    Integrates each interval between consecutive sign-change breakpoints
    with `quad`, then accelerates the alternating-tail partial sums by
    iterated pairwise averaging (Euler transform), which converges fast
    for the J-Bessel envelope decay.
    """
    edges = np.concatenate(([0.0], zeros))
    pieces = np.array(
        [quad(integrand, lo, hi, limit=200)[0] for lo, hi in zip(edges[:-1], edges[1:])]
    )
    partial = np.cumsum(pieces)
    tail = partial[-(2**n_average + 1) :]
    for _ in range(n_average):
        tail = 0.5 * (tail[:-1] + tail[1:])
    return float(tail[-1])


def delta_t_disk_center(
    layers: tuple[Layer, ...],
    p_w: float,
    a_m: float,
    h_top: float = 0.0,
    n_zeros: int = 200,
) -> float:
    """ΔT(0, 0) under a uniform disk flux of radius a (K).

    The integrand (P/πa)·J₁(ξa)·G(ξ) decays only algebraically
    (∝ ξ^{−3/2} on a half-space), so the inverse Hankel is summed
    between consecutive zeros of J₁(ξa) with Euler acceleration.
    """
    zeros = jn_zeros(1, n_zeros) / a_m

    def integrand(xi: float) -> float:
        return (
            float(disk_flux_hankel(xi, p_w, a_m))
            * float(surface_impedance(xi, layers, h_top))
            * xi
        )

    return _sum_between_bessel_zeros(integrand, zeros)


def delta_t_disk_average(
    layers: tuple[Layer, ...],
    p_w: float,
    a_m: float,
    h_top: float = 0.0,
    n_zeros: int = 400,
) -> float:
    """Disk-averaged surface rise ΔT̄ under a uniform disk flux (K).

    Averaging J₀(ξr) over the disk gives 2J₁(ξa)/(ξa), so
    ΔT̄ = (2P/πa²) ∫ G(ξ) J₁(ξa)²/ξ dξ — a NON-NEGATIVE integrand
    (∝ ξ^{−3} envelope on a half-space), summed to n_zeros half-cycles;
    the dropped tail is O(n_zeros^{−2}) relative.
    """
    zeros = jn_zeros(1, n_zeros) / a_m

    def integrand(xi: float) -> float:
        if xi <= 0.0:
            return 0.0
        return (
            (2.0 * p_w / (math.pi * a_m**2))
            * float(surface_impedance(xi, layers, h_top))
            * j1(xi * a_m) ** 2
            / xi
        )

    edges = np.concatenate(([0.0], zeros))
    return float(
        sum(quad(integrand, lo, hi, limit=200)[0] for lo, hi in zip(edges[:-1], edges[1:]))
    )


# ---------------------------------------------------------------------------
# Volumetric (Beer-Lambert) source in the top layer — see the module
# docstring section "Volumetric (Beer-Lambert) source" for the derivation,
# the truncation/renormalisation statement, and the quadrature choice.
# ---------------------------------------------------------------------------

_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(64)
_V_NODES = 0.5 * (_GL_NODES + 1.0)  # Gauss-Legendre on (0, 1)
_V_WEIGHTS = 0.5 * _GL_WEIGHTS


def volumetric_depth_pdf(
    z_m: np.ndarray | float, t_top_m: float, l_abs_m: float
) -> np.ndarray | float:
    """g(z): truncated exponential depth profile, renormalised to ∫g dz = 1.

    Support is [0, t_top]; the transmitted fraction e^{−t_top/l_abs} is
    rescaled onto the layer so the absorbed power stays exactly P.
    """
    if not l_abs_m > 0:
        raise ValueError("absorption length l_abs must be positive")
    z = np.asarray(z_m, dtype=float)
    norm = l_abs_m * (-math.expm1(-t_top_m / l_abs_m))
    return np.where((z >= 0.0) & (z <= t_top_m), np.exp(-z / l_abs_m) / norm, 0.0)


def _impedance_below_depth(
    xi: float, layers: tuple[Layer, ...], z_prime: np.ndarray
) -> np.ndarray:
    """Z looking down from depth z′ inside layers[0] (scalar ξ > 0, array z′)."""
    t1, k1 = layers[0].thickness_m, layers[0].k_w_m_k
    if math.isinf(t1):
        return np.full_like(z_prime, 1.0 / (k1 * xi))
    z_sub = float(surface_impedance(xi, layers[1:]))
    d = t1 - z_prime
    return (z_sub + (d / k1) * _tanh_over_x(xi * d)) / (
        1.0 + z_sub * k1 * xi * np.tanh(xi * d)
    )


def _buried_sheet_gtilde(
    xi: float, layers: tuple[Layer, ...], z_prime: np.ndarray, h_top: float
) -> np.ndarray:
    """e^{ξz′}·G(ξ, z′): the overflow-free surface response of a unit-power
    sheet at depth z′ (module docstring: cosh/sinh recast with e^{−2ξz′})."""
    k1 = layers[0].k_w_m_k
    z0 = 1.0 / (k1 * xi)
    z_dn = _impedance_below_depth(xi, layers, z_prime)
    a = z0 * (1.0 + h_top * z_dn)
    b = h_top * z0**2 + z_dn
    return z0 * z_dn / (0.5 * (a + b) + 0.5 * (a - b) * np.exp(-2.0 * xi * z_prime))


def volumetric_kernel(
    xi: float, layers: tuple[Layer, ...], l_abs_m: float, h_top: float = 0.0
) -> float:
    """K(ξ) = ∫₀^{t₁} g(z′) G(ξ, z′) dz′ with θ(ξ, 0) = K(ξ)·q̂(ξ).

    Substitution v = (1−e^{−μz′})/(1−e^{−μt₁}), μ = 1/l_abs + ξ, then a
    fixed 64-node Gauss-Legendre rule on the bounded, slowly-varying
    integrand e^{ξz′}G(ξ, z′) (constant in the half-space limit).
    """
    t1 = layers[0].thickness_m
    mu = 1.0 / l_abs_m + xi
    c_mu = -math.expm1(-mu * t1)  # 1 − e^{−μt₁}; → 1 for a half-space
    c_l = -math.expm1(-t1 / l_abs_m)
    z_prime = -np.log1p(-_V_NODES * c_mu) / mu
    gtilde = _buried_sheet_gtilde(xi, layers, z_prime, h_top)
    return float(np.dot(_V_WEIGHTS, gtilde)) * c_mu / (mu * l_abs_m * c_l)


def delta_t_gaussian_volumetric(
    r_m: float,
    layers: tuple[Layer, ...],
    p_w: float,
    w_m: float,
    l_abs_m: float,
    h_top: float = 0.0,
) -> float:
    """Surface rise ΔT(r, 0) (K) for the Gaussian × truncated-exponential
    volumetric source of total power P absorbed in the top layer.

    Same outer inverse-Hankel treatment as `delta_t_gaussian` (the radial
    transform is unchanged), with the surface kernel replaced by the
    depth-integrated K(ξ) and an extra breakpoint at 1/l_abs.
    """
    if w_m <= 0:
        raise ValueError("spot radius w must be positive")
    if not l_abs_m > 0:
        raise ValueError("absorption length l_abs must be positive")
    xi_max = math.sqrt(8.0 * 37.0) / w_m
    breakpoints = sorted(
        {1.0 / layer.thickness_m for layer in layers if math.isfinite(layer.thickness_m)}
        | {1.0 / w_m, 1.0 / l_abs_m}
    )
    points = [b for b in breakpoints if 0.0 < b < xi_max]

    def integrand(xi: float) -> float:
        if xi <= 0.0:
            return 0.0
        return (
            float(gaussian_flux_hankel(xi, p_w, w_m))
            * volumetric_kernel(xi, layers, l_abs_m, h_top)
            * xi
            * j0(xi * r_m)
        )

    value, _ = quad(integrand, 0.0, xi_max, points=points, limit=400)
    return value


def volumetric_base_power(
    layers: tuple[Layer, ...],
    p_w: float,
    l_abs_m: float,
    xi_scale: float = 1e-4,
) -> float:
    """Total power crossing the isothermal base (W) — the energy anchor.

    In steady state with an insulated top, every watt of the renormalised
    volumetric source must exit through the base: the r-integrated base
    flux is 2π·φ̂_base(ξ→0), with φ̂_base built from the current divider at
    the source sheet (down-fraction Z_up/(Z_up + Z_dn)) chained through the
    per-layer current transfer 1/(cosh(ξt) + (Z_load/Z₀)sinh(ξt)) down to
    the short. Independent algebra from `volumetric_kernel` — a genuine
    conservation check, not a restatement. Evaluated at
    ξ = xi_scale / Σt_i (finite-ξ error is O((ξ·Σt)²) ≈ 1e-8 at default).
    Requires a fully finite stack and h_top = 0 (else power exits the top).

    The spot radius does not appear: the radial transform carries total
    power exactly for ANY normalised profile (q̂(0) = P/2π, pinned by
    test_flux_transforms_carry_total_power), so the energy budget is a
    pure depth/network statement — the renormalised g plus current
    conservation through the stack.
    """
    if any(math.isinf(layer.thickness_m) for layer in layers):
        raise ValueError("energy anchor needs a finite stack (isothermal base)")
    total_t = sum(layer.thickness_m for layer in layers)
    xi = xi_scale / total_t
    t1, k1 = layers[0].thickness_m, layers[0].k_w_m_k
    z0 = 1.0 / (k1 * xi)

    mu = 1.0 / l_abs_m + xi
    c_mu = -math.expm1(-mu * t1)
    c_l = -math.expm1(-t1 / l_abs_m)
    z_prime = -np.log1p(-_V_NODES * c_mu) / mu

    z_dn = _impedance_below_depth(xi, layers, z_prime)
    z_up = z0 / np.tanh(xi * z_prime)  # insulated top: open-circuit line
    down_fraction = z_up / (z_up + z_dn)

    # current transfer from the bottom of layer 1 through the passive layers
    d = t1 - z_prime
    z_sub = float(surface_impedance(xi, layers[1:]))
    transfer = 1.0 / (np.cosh(xi * d) + z_sub * k1 * xi * np.sinh(xi * d))
    for i, layer in enumerate(layers[1:], start=1):
        t, k = layer.thickness_m, layer.k_w_m_k
        z_load = float(surface_impedance(xi, layers[i + 1 :]))
        transfer = transfer / (math.cosh(xi * t) + z_load * k * xi * math.sinh(xi * t))

    # ∫ g(z′)·e^{−μz′}-weighted sheet contributions, same v-substitution;
    # here the g weight is carried by the substitution measure directly.
    weighted = float(np.dot(_V_WEIGHTS, down_fraction * transfer * np.exp(xi * z_prime)))
    frac = weighted * c_mu / (mu * l_abs_m * c_l)
    return p_w * frac


# ---------------------------------------------------------------------------
# Closed-form anchors (SPEC §8 discipline) — the exact expressions the
# solver must reproduce in tests/test_thermal_layered.py.
# ---------------------------------------------------------------------------


def anchor_half_space_disk_center(p_w: float, k: float, a_m: float) -> float:
    """Semi-infinite solid, uniform disk flux: centre rise P/(πka)."""
    return p_w / (math.pi * k * a_m)


def anchor_half_space_disk_average(p_w: float, k: float, a_m: float) -> float:
    """Semi-infinite solid, uniform disk flux: disk-average rise 8P/(3π²ka).

    Equals (32/3π²) ≈ 1.081 × the isothermal-disk form P/(4ka) — the
    classical isoflux/isothermal constriction-resistance gap.
    """
    return 8.0 * p_w / (3.0 * math.pi**2 * k * a_m)


def anchor_half_space_gaussian_center(p_w: float, k: float, w_m: float) -> float:
    """Semi-infinite solid, Gaussian flux (1/e² radius w): P/(√(2π)kw)."""
    return p_w / (math.sqrt(2.0 * math.pi) * k * w_m)


def anchor_half_space_gaussian_profile(
    r_m: np.ndarray | float, p_w: float, k: float, w_m: float
) -> np.ndarray | float:
    """Semi-infinite solid, Gaussian flux: ΔT(r,0) = ΔT₀·e^{−r²/w²}I₀(r²/w²)."""
    from scipy.special import i0e

    x = np.asarray(r_m, dtype=float) ** 2 / w_m**2
    return anchor_half_space_gaussian_center(p_w, k, w_m) * i0e(x)


def anchor_one_dimensional_center(
    p_w: float, w_m: float, layers: tuple[Layer, ...]
) -> float:
    """w ≫ all thicknesses: ΔT(0,0) → q(0)·Σt_i/k_i = (2P/πw²)·Σt_i/k_i."""
    return (2.0 * p_w / (math.pi * w_m**2)) * series_resistance(layers)


def anchor_one_dimensional_uniform_generation(
    p_w: float, w_m: float, layers: tuple[Layer, ...]
) -> float:
    """w ≫ thicknesses, l_abs ≫ t₁: the 1-D two-region slab with UNIFORM
    internal generation in the top layer over passive layers.

    Derivation (elementary): per unit area the local absorbed flux at the
    beam centre is q₀ = q(0) = 2P/πw², deposited uniformly as q₀/t₁ over
    0 ≤ z ≤ t₁. Insulated top ⇒ the downward flux grows linearly,
    φ(z) = q₀·z/t₁, and all of q₀ crosses the passive layers to the base:
    T(t₁) = q₀·Σ_{i≥2} t_i/k_i. Inside the generating layer
    T(0) − T(t₁) = ∫₀^{t₁} φ/k₁ dz = q₀·t₁/(2k₁). Hence

        ΔT(0,0) → q₀ · [ t₁/(2k₁) + Σ_{i≥2} t_i/k_i ].

    The HALF-thickness term t₁/(2k₁) (vs t₁/k₁ for a surface flux) is the
    signature of uniform generation — the discriminating anchor.
    """
    top = layers[0]
    r_below = series_resistance(layers[1:])
    q0 = 2.0 * p_w / (math.pi * w_m**2)
    return q0 * (top.thickness_m / (2.0 * top.k_w_m_k) + r_below)


def anchor_one_dimensional_volumetric(
    p_w: float, w_m: float, layers: tuple[Layer, ...], l_abs_m: float
) -> float:
    """w ≫ thicknesses, ANY l_abs: 1-D slab with the truncated-exponential
    generation profile g(z) of `volumetric_depth_pdf` in the top layer.

    Derivation: φ(z) = q₀·∫₀^z g = q₀·(1−e^{−z/l})/c with c = 1−e^{−t₁/l};
    T(0) − T(t₁) = (q₀/k₁c)·∫₀^{t₁}(1−e^{−z/l})dz = (q₀/k₁c)·[t₁ − l·c], so

        ΔT(0,0) → q₀ · [ (t₁ − l·c)/(k₁·c) + Σ_{i≥2} t_i/k_i ].

    Limits: l → 0 gives t₁/k₁ (surface flux, full slab resistance);
    l ≫ t₁ gives t₁/(2k₁) (the uniform-generation anchor above). The
    l ≫ t₁ evaluation cancels t₁/c against l; float cancellation stays
    below ~2·(l/t₁)·eps — negligible for any physical l_abs.
    """
    top = layers[0]
    t1, k1 = top.thickness_m, top.k_w_m_k
    c = -math.expm1(-t1 / l_abs_m)
    r_gen = (t1 - l_abs_m * c) / (k1 * c)
    q0 = 2.0 * p_w / (math.pi * w_m**2)
    return q0 * (r_gen + series_resistance(layers[1:]))
