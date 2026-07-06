"""SPEC §7.T2 output 3 — inhomogeneous thermal line observable (2026-07-06).

The gain/probed volume is not isothermal: the steady ΔT(r, z) field puts
different sub-volumes at different temperatures, so the local spin
transition frequency (via df_spin/dT, §6T) varies across the probed
volume. The ensemble line is therefore both SHIFTED (by the weighted
mean of ΔT) and BROADENED (by the weighted spread), on top of the
intrinsic linewidth. This module maps a weighted temperature
distribution to that pair of observables and expresses both in the
reporting unit Oxborrow asked for (verbal, 2026-07-06): UNITS OF THE
RESONANCE LINEWIDTH — shift/linewidth, equivalently Δf·Q/f. Absolute
Hz is secondary.

Linkage (§7.T4): this is the same quantity as the Q-margin question.
"Margin" is how many linewidths of detuning fit before the system falls
off resonance; the inhomogeneous width is that displacement made
observable. The 1/√Q derivation and this observable share this module's
linewidth unit.

Structure — observable map vs geometry instance
-----------------------------------------------
`line_observable_from_samples` is geometry-agnostic: any (ΔT, weight)
sample set — a depth-resolved field, a COMSOL export, the future maser
cylinder core — maps to the observable without touching this module.

`gaussian_spot_line_observable` is the concrete instance on the
existing §7.T5 rig machinery: the surface field ΔT(r, 0) of
`layered.delta_t_gaussian` (or its volumetric variant), probe-weighted
by the pump intensity — SPEC §7.T5 observable (a): excitation and
collection are co-located, so the ODMR-probed measure is the
illuminated spot. Scope statement (accuracy boundary, not hidden): the
surface radial profile captures the RADIAL temperature spread only;
the spread over the probed DEPTH (z ≲ l_abs) is not yet included —
the transport core exposes surface values, and extending it is a
§7.T1 matter, not this module's. Plug depth-resolved samples into
`line_observable_from_samples` when they exist.

Width convention: `inhom_width_hz` is the probe-weighted RMS (standard
deviation) of the local frequency, |df_spin/dT|·σ_T — an RMS width,
not a FWHM (the T-distribution is not Gaussian in general; for a
Gaussian line FWHM = 2√(2ln2)·σ ≈ 2.355σ). How it composes with the
intrinsic linewidth depends on both shapes; this module reports the
inhomogeneous moment only and does not claim a convolution model.

Probe-weighted surface moments (the rig instance)
-------------------------------------------------
Probe measure on the surface: p(r) dA ∝ e^{−2r²/w²}·2πr dr. In
s = 2r²/w² this is exactly e^{−s} ds on (0, ∞); the moments are
evaluated by Gauss-Legendre on the CDF map u = 1 − e^{−s} (exact
weight, no truncation), with the ΔT profile evaluated once at the
mapped nodes and both moments taken as dot products. Accuracy is
pinned by the closed-form anchors below, not asserted here.

Closed-form anchors (§8 discipline; tests/test_thermal_broadening.py)
---------------------------------------------------------------------
1. Uniform T ⇒ ZERO inhomogeneous width, pure shift — exactly (the
   limit check Oxborrow's ask is anchored on; enforced identically,
   not to rounding, in `line_observable_from_samples`).
2. Half-space, Gaussian spot: ΔT(r,0)/ΔT₀ = e^{−x}I₀(x), x = r²/w²
   (layered.py anchor 3). With the pump-probe weight and
   ∫₀^∞ e^{−pt}I₀(t) dt = 1/√(p²−1),
   ∫₀^∞ e^{−pt}I₀(t)² dt = (2/πp)·K(k=2/p) (Laplace transforms;
   K = complete elliptic integral, modulus convention):
       ⟨ΔT⟩  = ΔT₀/√2,
       ⟨ΔT²⟩ = ΔT₀²·K(k=1/2)/π   [scipy: ellipk(m=1/4)].
3. 1-D limit (w ≫ all thicknesses): ΔT(r) → q(r)·Σtᵢ/kᵢ ∝ e^{−2r²/w²},
   so ⟨ΔT⟩ = ΔT₀/2 and ⟨ΔT²⟩ = ΔT₀²/3 (σ = ΔT₀/(2√3)) — regime
   constants distinct from the half-space pair, so the two anchors
   discriminate.
4. Hankel-Parseval identity for the mean (independent algebra): with
   probe p̂(ξ) = (1/2π)e^{−ξ²w²/8} and θ(ξ,0) = G(ξ)q̂(ξ),
   ⟨ΔT⟩ = 2π∫ p̂ G q̂ ξ dξ = (P/2π)∫ G e^{−ξ²(√2w)²/8} ξ dξ
        = delta_t_gaussian(0, layers, P, √2·w)
   — the probe-weighted mean equals the centre rise of a √2-wider
   spot, for ANY stack, Robin top, and the volumetric kernel alike.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cavity.thermal.layered import (
    Layer,
    delta_t_gaussian,
    delta_t_gaussian_volumetric,
)

_N_PROBE_NODES = 96
_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(_N_PROBE_NODES)
_U_NODES = 0.5 * (_GL_NODES + 1.0)  # Gauss-Legendre on (0, 1)
_U_WEIGHTS = 0.5 * _GL_WEIGHTS


@dataclass(frozen=True)
class ThermalLineObservable:
    """Mean shift + inhomogeneous width of the spin line from a ΔT field.

    `mean_delta_t_k` / `rms_delta_t_k` are the probe-weighted mean and
    standard deviation of the temperature rise; `mean_shift_hz` /
    `inhom_width_hz` are their images under df_spin/dT (shift keeps the
    coefficient's sign; the width is non-negative by construction).
    """

    mean_delta_t_k: float
    rms_delta_t_k: float
    df_dt_hz_per_k: float

    @property
    def mean_shift_hz(self) -> float:
        return self.df_dt_hz_per_k * self.mean_delta_t_k

    @property
    def inhom_width_hz(self) -> float:
        return abs(self.df_dt_hz_per_k) * self.rms_delta_t_k

    def shift_in_linewidths(self, linewidth_hz: float) -> float:
        """Signed mean shift / resonance linewidth — the headline unit."""
        _require_positive_linewidth(linewidth_hz)
        return self.mean_shift_hz / linewidth_hz

    def width_in_linewidths(self, linewidth_hz: float) -> float:
        """Inhomogeneous RMS width / resonance linewidth (non-negative)."""
        _require_positive_linewidth(linewidth_hz)
        return self.inhom_width_hz / linewidth_hz


def _require_positive_linewidth(linewidth_hz: float) -> None:
    if not linewidth_hz > 0:
        raise ValueError("linewidth must be positive")


def resonance_linewidth_hz(f_hz: float, q_loaded: float) -> float:
    """Linewidth f/Q_L — makes 'in linewidths' ≡ Δf·Q/f explicit."""
    if not (f_hz > 0 and q_loaded > 0):
        raise ValueError("f and Q must be positive")
    return f_hz / q_loaded


def line_observable_from_samples(
    delta_t_k: np.ndarray,
    weights: np.ndarray,
    df_dt_hz_per_k: float,
) -> ThermalLineObservable:
    """Geometry-agnostic observable map: weighted ΔT samples → line pair.

    `weights` is the probe measure of each sample (volume × probe
    density — gain-region H weighting for the maser, illumination for
    the rig); only its normalisation-free shape matters. The uniform-T
    limit is enforced identically: a constant field returns
    `rms_delta_t_k == 0.0` exactly, not to rounding.
    """
    dt = np.asarray(delta_t_k, dtype=float)
    wt = np.asarray(weights, dtype=float)
    if dt.shape != wt.shape or dt.size == 0:
        raise ValueError("delta_t and weights must be same-shape, non-empty")
    if np.any(wt < 0) or not np.sum(wt) > 0:
        raise ValueError("weights must be non-negative with positive sum")
    mean = float(np.average(dt, weights=wt))
    if np.all(dt == dt.flat[0]):
        rms = 0.0
    else:
        rms = math.sqrt(max(float(np.average((dt - mean) ** 2, weights=wt)), 0.0))
    return ThermalLineObservable(mean, rms, df_dt_hz_per_k)


def probe_weighted_surface_moments(
    profile_delta_t_k, w_m: float
) -> tuple[float, float]:
    """(⟨ΔT⟩, ⟨ΔT²⟩) of a surface profile under the pump-probe measure.

    `profile_delta_t_k` is a callable r → ΔT(r, 0). The probe measure
    e^{−2r²/w²}·2πr dr becomes e^{−s} ds under s = 2r²/w²; the CDF map
    u = 1 − e^{−s} carries the exact weight, so the fixed
    Gauss-Legendre rule needs no truncation correction. Accuracy is
    pinned by the closed-form anchors (module docstring, items 2–4).
    """
    if not w_m > 0:
        raise ValueError("spot radius w must be positive")
    s = -np.log1p(-_U_NODES)
    r = w_m * np.sqrt(0.5 * s)
    vals = np.array([float(profile_delta_t_k(r_i)) for r_i in r])
    m1 = float(np.dot(_U_WEIGHTS, vals))
    m2 = float(np.dot(_U_WEIGHTS, vals**2))
    return m1, m2


def gaussian_spot_line_observable(
    layers: tuple[Layer, ...],
    p_w: float,
    w_m: float,
    df_dt_hz_per_k: float,
    h_top: float = 0.0,
    l_abs_m: float | None = None,
) -> ThermalLineObservable:
    """Rig instance (§7.T5 observable (a)): line pair from the surface field.

    Evaluates ΔT(r, 0) of the layered engine (surface flux by default;
    the volumetric Beer-Lambert source when `l_abs_m` is given) under
    the co-located pump/probe weighting. Radial spread only — see the
    module docstring's scope statement on depth weighting.
    """

    def profile(r_m: float) -> float:
        if l_abs_m is None:
            return delta_t_gaussian(r_m, layers, p_w, w_m, h_top)
        return delta_t_gaussian_volumetric(r_m, layers, p_w, w_m, l_abs_m, h_top)

    m1, m2 = probe_weighted_surface_moments(profile, w_m)
    rms = math.sqrt(max(m2 - m1 * m1, 0.0))
    return ThermalLineObservable(m1, rms, df_dt_hz_per_k)
