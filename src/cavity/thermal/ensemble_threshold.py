"""SPEC §7.T4 sensitivity audit — multi-packet / Voigt lasing threshold.

Context and scope
=================
The committed two-linewidth margin law (`detuning.delta_f_max_hz`,
re-derived 2026-07-13) maps the measured ODMR FWHM onto ONE homogeneous
Lorentzian spin packet (kappa_s = the composite 1.4 MHz). That mapping
is a threshold-MODEL assumption, flagged as such everywhere it rides
(`KAPPA_S` docstring, SPEC §6T/§7.T4, the q_margin reports); its
resolution is the open D4 conjunction (the hom/inhom decomposition of
the composite line is UNKNOWN). This module quantifies the SENSITIVITY
of the margin and of the Q-margin exponent to that decomposition by
solving the class-A multi-packet threshold exactly for a Voigt line —
a Gaussian distribution (std sigma_g) of Lorentzian packets of common
homogeneous FWHM f_L, sized so the composite FWHM equals the graded
kappa_s. It is an AUDIT: no constant is re-graded, no claim is made,
and nothing here resolves D4.

Model and threshold condition
=============================
Linearised cavity + N spin packets (class-A: inversion adiabatically
clamped, quasi-static), cavity amplitude decay a_c, common packet
amplitude decay a_s, packet centres omega_j (spin line centred at 0,
cavity at detuning Delta), rotating frame:

    da/dt       = -(a_c + i*Delta)*a - i*sum_j g_j*sigma_j
    dsigma_j/dt = -(a_s + i*omega_j)*sigma_j + i*g_j*Sz_j*a

Eigenvalue lambda of the coupled system: (lambda + a_c + i*Delta) =
sum_j g_j^2*Sz_j/(lambda + a_s + i*omega_j). With G^2 = sum_j g_j^2*
Sz_j and weights w_j = g_j^2*Sz_j/G^2, a marginal eigenvalue
lambda = -i*omega (omega real) gives

    1 = G^2 * S(omega),
    S(omega)      = S_spin(omega) / (a_c + i*(Delta - omega)),
    S_spin(omega) = sum_j w_j / (a_s + i*(omega_j - omega)).

PACKET WEIGHTS (ruling for this pass, superseding an earlier draft
wording): w_j is the INVERSION- AND COUPLING^2-WEIGHTED distribution of
packet CENTRES; under the uniform-inversion / uniform-coupling
assumption adopted here it is the Gaussian centre distribution itself
(std sigma_g). The composite Voigt line is the RESULTING
susceptibility — Re S_spin(omega) = pi * (area-normalised composite
profile)(omega) — it is NOT itself the weight distribution.

Threshold = min over the real roots omega_0 of Im S = 0 with
Re S > 0 of G^2_th = 1/Re S(omega_0). Minimum argument: at G^2 = 0
every eigenvalue (-(a_c + i*Delta), -(a_s + i*omega_j)) has Re < 0;
eigenvalues move continuously with G^2 and can reach the right
half-plane only through the imaginary axis; any axis crossing at real
omega satisfies 1 = G^2*S(omega), which requires Im S(omega_0) = 0 and
G^2 = 1/Re S(omega_0) > 0. Hence no crossing exists for G^2 below
min{1/Re S(omega_0)} and a marginal mode exists exactly there — the
smallest such G^2 is the threshold.

Exact Voigt susceptibility (no grids, no truncation)
====================================================
For a Gaussian centre density rho(nu) = exp(-nu^2/(2*sigma_g^2)) /
(sqrt(2*pi)*sigma_g):

    S_spin(omega) = integral rho(nu) / (a_s + i*(nu - omega)) d nu.

Write a_s + i*(nu - omega) = i*(nu - z) with z = omega + i*a_s
(Im z > 0); substituting nu = sqrt(2)*sigma_g*t gives
(1/i)*Z(zeta)/(sqrt(2)*sigma_g) with the plasma dispersion function
Z(zeta) = (1/sqrt(pi)) integral e^{-t^2}/(t - zeta) dt =
i*sqrt(pi)*w(zeta) for Im zeta > 0 (w = the Faddeeva function,
`scipy.special.wofz`):

    S_spin(omega) = sqrt(pi/2)/sigma_g * w((omega + i*a_s) /
                                           (sqrt(2)*sigma_g)).

sigma_g = 0 is the closed-form single-packet branch S_spin =
1/(a_s - i*omega) (the large-|zeta| limit w ~ i/(sqrt(pi)*zeta)
reproduces it). Consistency: Re S_spin = pi*V with V the
area-normalised Voigt profile, so at Delta = 0 the on-resonance
threshold is G^2_th(0) = a_c/(pi*V(0)).

Units
=====
Matched cyclic-MHz-FWHM units throughout: all frequency inputs/outputs
are cyclic-Hz-convention quantities expressed in MHz, with amplitude
decay rates = FWHM/2 in the same numeric units (a_c = kappa_c/2,
a_s = f_L/2); sigma_g is the Gaussian STD in MHz (Gaussian FWHM =
2*sqrt(2*ln 2)*sigma_g). The threshold relation is homogeneous of
degree 1 in (Delta, rates, widths) and both G^2 normalisations are
invariant under uniform rescaling, so the FWHM/2 shortcut is EXACT, no
2*pi ever appears, and margins come out directly in MHz (the
provenance-table W20 angular-"Hz" trap cannot enter this API).

Normalisation conventions (both live here, labelled)
====================================================
- PRIMARY — "repo-consistent import-preserving fixed-G^2" (the
  ratified amendment-C C0-import convention, `report_margin.py` /
  SPEC §7.T4 re-derivation block): C0 = 190 is the imported algebraic
  resonant cooperativity 4*G^2/(kappa_c*kappa_s_composite), never
  recomputed; hence G^2 = C0*kappa_c*kappa_s_composite/4
  (`g2_fixed_import_preserving`), held fixed while the line shape or Q
  varies. G^2 under this convention is an ALGEBRAIC IMPORT — it is NOT
  independently measured and NOT microscopically grounded.
- SECONDARY — on-resonance threshold ratio: solve
  G^2_th(Delta)/G^2_th(0) = C0 (`margin_onres_ratio`) — the untrusted
  handoff's check-6 convention, kept for comparability and labelled
  wherever used.
On the sigma_g = 0 single-packet branch the two coincide exactly
(G^2_th(0) = a_c*a_s) and both reproduce `detuning.delta_f_max_hz`.

Far-wing caveat (rides every number computed downstream)
========================================================
At the planning C0 = 190 the margin sits sqrt(C0 - 1) ~ 13.7 combined
half-widths from line centre. ALL cases — including the committed
single-Lorentzian law — carry the margin on far LORENTZIAN packet
tails there (Re S_spin -> a_s/omega^2); the line-shape branch only
decides how much width contributes tails. No measurement in hand
constrains the real line's behaviour 10+ widths out.

Root finding (amended discipline — sign scans alone are not trusted)
====================================================================
Im S = 0 is root-found on the numerator
F(omega) = a_c*Im S_spin(omega) - (Delta - omega)*Re S_spin(omega)
(the denominator |a_c + i*(Delta - omega)|^2 is strictly positive).
For Delta > 0 all roots lie in (0, Delta): F(0) < 0, F(Delta) > 0, and
both F terms share one sign outside [0, Delta] for a symmetric
unimodal line. Beyond the sign-change scan + brentq, exact grid-node
zeros are kept, and a tangential-root guard inspects interior local
minima of |F| without sign change (parabolic vertex refinement;
near-zero double roots are admitted as candidates and flagged) — root
mergers near branch switches are the known hazard. Every threshold
records ALL candidate roots and which one was selected, so branch
switches stay visible in any table built on top. Delta = 0 uses the
exact omega = 0 root (PRECONDITION: frequency-symmetric unimodal
centre distribution — for the Gaussian-of-Lorentzians line,
Im S_spin(omega) = c * integral_0^inf [e^{-(omega-u)^2/2 sigma^2} -
e^{-(omega+u)^2/2 sigma^2}] * u/(u^2 + a_s^2) du > 0 strictly for
omega > 0, so omega = 0 is the unique root; a numeric symmetry check
guards the entry).

Free-running ruling (carried from §7.T4): the threshold is an
eigenvalue crossing of the free-running system; no injected signal
fixes omega. Class-A/quasi-static inversion, single cavity mode,
static kappa_s (no kappa_s(Delta_T) feedback) — the §7.T4 assumption
stack applies unchanged.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.optimize import brentq
from scipy.special import wofz

# FWHM of a unit-std Gaussian: 2*sqrt(2*ln 2).
GAUSSIAN_FWHM_PER_SIGMA = 2.0 * math.sqrt(2.0 * math.log(2.0))

FIXED_G2_LABEL = (
    "repo-consistent import-preserving fixed-G^2 "
    "(amendment-C C0-import convention; PRIMARY)"
)
ONRES_RATIO_LABEL = (
    "on-resonance threshold ratio G^2_th(Delta)/G^2_th(0) = C0 "
    "(handoff convention; SECONDARY)"
)

# Tangential-root guard: investigate interior |F| minima below
# _TANGENT_FILTER_REL of the local term scale; admit a parabola-vertex
# double root below _TANGENT_ROOT_REL of that scale.
_TANGENT_FILTER_REL = 1e-3
_TANGENT_ROOT_REL = 1e-9

SSpin = Callable[[np.ndarray | float], np.ndarray | complex]


def make_voigt_s_spin(f_l_mhz: float, sigma_g_mhz: float) -> SSpin:
    """Exact Voigt spin susceptibility S_spin (module docstring).

    `f_l_mhz` = homogeneous packet FWHM (cyclic MHz; amplitude rate
    a_s = f_L/2), `sigma_g_mhz` = std of the Gaussian packet-centre
    distribution. sigma_g = 0 returns the closed-form single-packet
    branch. f_L must be positive: the Lorentzian packet tails carry
    the far-wing gain (a_s = 0 has no threshold at planning
    detunings).
    """
    if not f_l_mhz > 0.0:
        raise ValueError(
            "homogeneous FWHM f_L must be positive (the Lorentzian "
            "packet tails carry the far-wing gain)"
        )
    if sigma_g_mhz < 0.0:
        raise ValueError("sigma_g must be non-negative")
    a_s = 0.5 * f_l_mhz
    if sigma_g_mhz == 0.0:

        def s_spin_single(omega):
            return 1.0 / (a_s - 1j * np.asarray(omega, dtype=float))

        return s_spin_single

    pref = math.sqrt(math.pi / 2.0) / sigma_g_mhz
    scale = math.sqrt(2.0) * sigma_g_mhz

    def s_spin_voigt(omega):
        zeta = (np.asarray(omega, dtype=float) + 1j * a_s) / scale
        return pref * wofz(zeta)

    return s_spin_voigt


def voigt_profile_per_mhz(
    x_mhz: np.ndarray | float, f_l_mhz: float, sigma_g_mhz: float
) -> np.ndarray | float:
    """Area-normalised composite line profile V(x) (1/MHz).

    Identity used throughout: Re S_spin(x) = pi * V(x). sigma_g = 0 is
    the Lorentzian branch; f_L = 0 with sigma_g > 0 is the pure
    Gaussian (admitted here for sizing limits, NOT for thresholds).
    """
    if f_l_mhz < 0.0 or sigma_g_mhz < 0.0:
        raise ValueError("widths must be non-negative")
    a_s = 0.5 * f_l_mhz
    x = np.asarray(x_mhz, dtype=float)
    if sigma_g_mhz == 0.0:
        if a_s == 0.0:
            raise ValueError("f_L and sigma_g cannot both be zero")
        return a_s / (math.pi * (x * x + a_s * a_s))
    zeta = (x + 1j * a_s) / (math.sqrt(2.0) * sigma_g_mhz)
    return np.real(wofz(zeta)) / (sigma_g_mhz * math.sqrt(2.0 * math.pi))


def olivero_longbothum_fwhm_mhz(f_l_mhz: float, f_g_mhz: float) -> float:
    """O-L approximate Voigt FWHM (diagnostic only — never sizing)."""
    return 0.5346 * f_l_mhz + math.sqrt(
        0.2166 * f_l_mhz * f_l_mhz + f_g_mhz * f_g_mhz
    )


def voigt_fwhm_mhz(f_l_mhz: float, sigma_g_mhz: float) -> float:
    """Exact composite FWHM: solve V(x) = V(0)/2 (unimodal, even)."""
    if sigma_g_mhz == 0.0:
        return f_l_mhz
    if f_l_mhz == 0.0:
        return GAUSSIAN_FWHM_PER_SIGMA * sigma_g_mhz
    v0 = float(voigt_profile_per_mhz(0.0, f_l_mhz, sigma_g_mhz))
    hi = 1.5 * olivero_longbothum_fwhm_mhz(
        f_l_mhz, GAUSSIAN_FWHM_PER_SIGMA * sigma_g_mhz
    )

    def half_deficit(x: float) -> float:
        return float(voigt_profile_per_mhz(x, f_l_mhz, sigma_g_mhz)) - 0.5 * v0

    return 2.0 * brentq(half_deficit, 0.0, hi, xtol=1e-13)


def voigt_sigma_g_mhz(f_l_mhz: float, f_composite_mhz: float) -> float:
    """EXACT composite-FWHM sizing: sigma_g such that the Voigt FWHM
    equals `f_composite_mhz` at homogeneous FWHM `f_l_mhz` (retires the
    handoff's Olivero-Longbothum ~1.44/1.29 MHz sizing imprecision).
    f_L = f_composite returns exactly 0.0 (the pure-Lorentzian repo
    branch)."""
    if not 0.0 < f_l_mhz <= f_composite_mhz:
        raise ValueError("need 0 < f_L <= composite FWHM")
    if f_l_mhz == f_composite_mhz:
        return 0.0
    hi = f_composite_mhz / GAUSSIAN_FWHM_PER_SIGMA

    def fwhm_deficit(sigma: float) -> float:
        return voigt_fwhm_mhz(f_l_mhz, sigma) - f_composite_mhz

    # sigma -> 0+: FWHM -> f_L < composite; sigma = hi: the Voigt FWHM
    # strictly exceeds the pure-Gaussian FWHM (= composite) for f_L > 0.
    return brentq(fwhm_deficit, 1e-12 * hi, hi, xtol=1e-13)


@dataclass(frozen=True)
class ThresholdRoot:
    """One threshold evaluation with its FULL root-branch record.

    `candidate_omegas_mhz` / `candidate_g2` list every Im S = 0 root
    with Re S > 0 (sorted by omega); `selected_index` points at the
    minimal-G^2 (threshold) branch. `tangential_candidates` is True
    when any candidate came from the tangential/merger guard rather
    than a clean sign change — branch switches stay visible in any
    table built on these records."""

    g2_th: float
    omega_mhz: float
    selected_index: int
    n_candidates: int
    candidate_omegas_mhz: tuple[float, ...]
    candidate_g2: tuple[float, ...]
    tangential_candidates: bool


def _re_s(a_c: float, delta: float, omega: float, s_val: complex) -> float:
    """Re S at omega from S_spin(omega) (module-docstring algebra)."""
    d = delta - omega
    return (a_c * s_val.real + d * s_val.imag) / (a_c * a_c + d * d)


def threshold_g2(
    delta_mhz: float,
    kappa_c_fwhm_mhz: float,
    s_spin: SSpin,
    *,
    window_mhz: float = 30.0,
    n_scan: int = 3001,
) -> ThresholdRoot:
    """Multi-packet threshold G^2_th at cavity detuning Delta.

    Scan window = [min(0, Delta) - window, max(0, Delta) + window];
    all margins downstream must be invariant under window/n_scan
    doubling (pinned in the anchor file). Delta = 0 takes the exact
    omega = 0 branch (symmetric-line precondition, module docstring),
    guarded by a numeric symmetry check.
    """
    if not kappa_c_fwhm_mhz > 0.0:
        raise ValueError("kappa_c must be positive (cyclic FWHM, f/Q_L)")
    if n_scan < 16:
        raise ValueError("n_scan too small to scan root branches")
    a_c = 0.5 * kappa_c_fwhm_mhz

    if delta_mhz == 0.0:
        s0 = complex(s_spin(0.0))
        if abs(s0.imag) > 1e-9 * abs(s0.real):
            raise ValueError(
                "Delta = 0 analytic branch requires a frequency-"
                "symmetric line (Im S_spin(0) != 0 numerically)"
            )
        if not s0.real > 0.0:
            raise ValueError("Re S_spin(0) must be positive")
        g2 = a_c / s0.real
        return ThresholdRoot(g2, 0.0, 0, 1, (0.0,), (g2,), False)

    lo = min(0.0, delta_mhz) - window_mhz
    hi = max(0.0, delta_mhz) + window_mhz
    grid = np.linspace(lo, hi, n_scan)
    s_vals = np.asarray(s_spin(grid))
    f_vals = a_c * s_vals.imag - (delta_mhz - grid) * s_vals.real

    def f_scalar(w: float) -> float:
        sw = complex(s_spin(w))
        return a_c * sw.imag - (delta_mhz - w) * sw.real

    roots: list[float] = []
    tangential = False
    for i in range(n_scan - 1):
        fi = f_vals[i]
        if fi == 0.0:
            roots.append(float(grid[i]))
            continue
        if fi * f_vals[i + 1] < 0.0:
            roots.append(
                brentq(f_scalar, float(grid[i]), float(grid[i + 1]), xtol=1e-12)
            )
    if f_vals[-1] == 0.0:
        roots.append(float(grid[-1]))

    # Tangential/merger guard: interior local minima of |F| with no
    # sign change, small against the local term scale.
    term_scale = a_c * np.abs(s_vals.imag) + np.abs(
        delta_mhz - grid
    ) * np.abs(s_vals.real)
    abs_f = np.abs(f_vals)
    is_min = (abs_f[1:-1] < abs_f[:-2]) & (abs_f[1:-1] <= abs_f[2:])
    no_change = (f_vals[:-2] * f_vals[1:-1] > 0.0) & (
        f_vals[1:-1] * f_vals[2:] > 0.0
    )
    small = abs_f[1:-1] < _TANGENT_FILTER_REL * term_scale[1:-1]
    for i in (np.nonzero(is_min & no_change & small)[0] + 1):
        x0, x1, x2 = grid[i - 1], grid[i], grid[i + 1]
        f0, f1, f2 = f_vals[i - 1], f_vals[i], f_vals[i + 1]
        curvature = f0 - 2.0 * f1 + f2
        if curvature == 0.0:
            continue
        x_v = x1 + 0.5 * (f0 - f2) / curvature * (x1 - x0)
        if not x0 < x_v < x2:
            continue
        f_v = f_scalar(float(x_v))
        if f_v == 0.0:
            roots.append(float(x_v))
            tangential = True
        elif f_v * f1 < 0.0:
            # The dip does cross: two roots hide between the scan nodes.
            roots.append(brentq(f_scalar, float(x0), float(x_v), xtol=1e-12))
            roots.append(brentq(f_scalar, float(x_v), float(x2), xtol=1e-12))
        else:
            sv = complex(s_spin(float(x_v)))
            local_scale = a_c * abs(sv.imag) + abs(delta_mhz - x_v) * abs(
                sv.real
            )
            if abs(f_v) < _TANGENT_ROOT_REL * local_scale:
                roots.append(float(x_v))
                tangential = True

    roots.sort()
    merged: list[float] = []
    min_sep = 1e-9 * (hi - lo)
    for r in roots:
        if not merged or r - merged[-1] > min_sep:
            merged.append(r)

    candidates: list[tuple[float, float]] = []
    for w0 in merged:
        re_s = _re_s(a_c, delta_mhz, w0, complex(s_spin(w0)))
        if re_s > 0.0:
            candidates.append((w0, 1.0 / re_s))
    if not candidates:
        raise RuntimeError(
            "no Im S = 0 root with Re S > 0 in the scan window — widen "
            "window_mhz / raise n_scan"
        )
    candidates.sort()
    g2_list = tuple(c[1] for c in candidates)
    selected = int(np.argmin(g2_list))
    return ThresholdRoot(
        g2_th=g2_list[selected],
        omega_mhz=candidates[selected][0],
        selected_index=selected,
        n_candidates=len(candidates),
        candidate_omegas_mhz=tuple(c[0] for c in candidates),
        candidate_g2=g2_list,
        tangential_candidates=tangential,
    )


@dataclass(frozen=True)
class MarginResult:
    """A solved detuning margin, carrying its normalisation label and
    the threshold root record AT the solved margin (branch audit)."""

    delta_f_max_mhz: float
    g2: float
    g2_th_onres: float
    normalisation: str
    root: ThresholdRoot


def g2_fixed_import_preserving(
    c0: float, kappa_c_fwhm_mhz: float, kappa_s_composite_fwhm_mhz: float
) -> float:
    """G^2 = C0*kappa_c*kappa_s_composite/4 — the repo-consistent
    import-preserving fixed-G^2 anchoring (amendment C: C0 is the
    IMPORTED algebraic resonant cooperativity 4G^2/(kappa_c*kappa_s),
    never recomputed). This G^2 is an algebraic import convention —
    NOT an independently measured or microscopically grounded
    coupling."""
    if not (c0 > 0.0 and kappa_c_fwhm_mhz > 0.0):
        raise ValueError("need C0 > 0 and kappa_c > 0")
    if not kappa_s_composite_fwhm_mhz > 0.0:
        raise ValueError("composite kappa_s must be positive")
    return 0.25 * c0 * kappa_c_fwhm_mhz * kappa_s_composite_fwhm_mhz


def margin_fixed_g2(
    g2: float,
    kappa_c_fwhm_mhz: float,
    s_spin: SSpin,
    *,
    window_mhz: float = 30.0,
    n_scan: int = 3001,
    bracket_hi_mhz: float = 60.0,
    bracket_cap_mhz: float = 1.0e4,
    xtol_mhz: float = 1e-10,
    normalisation: str = FIXED_G2_LABEL,
) -> MarginResult:
    """Detuning margin at fixed G^2: solve G^2_th(Delta) = G^2, Delta > 0.

    Mirrors `delta_f_max_hz`'s C0 <= 1 convention: at or below the
    on-resonance threshold the margin is 0.0. The crossing bracket
    expands geometrically from `bracket_hi_mhz` (G^2_th grows without
    bound on Lorentzian packet tails); exceeding `bracket_cap_mhz`
    raises rather than reporting a fictitious margin.
    """
    if not g2 > 0.0:
        raise ValueError("G^2 must be positive")
    onres = threshold_g2(
        0.0, kappa_c_fwhm_mhz, s_spin, window_mhz=window_mhz, n_scan=n_scan
    )
    if g2 <= onres.g2_th:
        return MarginResult(0.0, g2, onres.g2_th, normalisation, onres)

    def crossing(delta: float) -> float:
        if delta == 0.0:
            return onres.g2_th - g2
        return (
            threshold_g2(
                delta,
                kappa_c_fwhm_mhz,
                s_spin,
                window_mhz=window_mhz,
                n_scan=n_scan,
            ).g2_th
            - g2
        )

    hi = bracket_hi_mhz
    while crossing(hi) < 0.0:
        hi *= 2.0
        if hi > bracket_cap_mhz:
            raise RuntimeError(
                f"no threshold crossing below {bracket_cap_mhz} MHz — "
                "report as no-crossing-in-swept-range, do not extrapolate"
            )
    delta_star = brentq(crossing, 0.0, hi, xtol=xtol_mhz)
    root = threshold_g2(
        delta_star,
        kappa_c_fwhm_mhz,
        s_spin,
        window_mhz=window_mhz,
        n_scan=n_scan,
    )
    return MarginResult(delta_star, g2, onres.g2_th, normalisation, root)


def margin_onres_ratio(
    c0: float,
    kappa_c_fwhm_mhz: float,
    s_spin: SSpin,
    *,
    window_mhz: float = 30.0,
    n_scan: int = 3001,
    bracket_hi_mhz: float = 60.0,
    bracket_cap_mhz: float = 1.0e4,
    xtol_mhz: float = 1e-10,
) -> MarginResult:
    """Detuning margin under the SECONDARY (handoff) normalisation:
    solve G^2_th(Delta)/G^2_th(0) = C0. Coincides with the fixed-G^2
    route on the single-packet branch; differs for Voigt lines because
    G^2_th(0) depends on the line PEAK, not the composite FWHM."""
    if not c0 > 1.0:
        raise ValueError("on-res-ratio margin requires C0 > 1")
    onres = threshold_g2(
        0.0, kappa_c_fwhm_mhz, s_spin, window_mhz=window_mhz, n_scan=n_scan
    )
    return margin_fixed_g2(
        c0 * onres.g2_th,
        kappa_c_fwhm_mhz,
        s_spin,
        window_mhz=window_mhz,
        n_scan=n_scan,
        bracket_hi_mhz=bracket_hi_mhz,
        bracket_cap_mhz=bracket_cap_mhz,
        xtol_mhz=xtol_mhz,
        normalisation=ONRES_RATIO_LABEL,
    )


@dataclass(frozen=True)
class ExponentResult:
    """Numeric fixed-G^2 Q-margin exponent with its evaluation record."""

    exponent: float
    h_log: float
    margin_q_hi_mhz: float  # margin at Q_L * e^{+h} (kappa_c * e^{-h})
    margin_q_lo_mhz: float  # margin at Q_L * e^{-h} (kappa_c * e^{+h})
    root_q_hi: ThresholdRoot
    root_q_lo: ThresholdRoot


def q_margin_exponent_numeric(
    g2: float,
    kappa_c_fwhm_mhz: float,
    s_spin: SSpin,
    *,
    h_log: float = 0.02,
    window_mhz: float = 30.0,
    n_scan: int = 3001,
    xtol_mhz: float = 1e-10,
) -> ExponentResult:
    """E = d ln Delta_f_max / d ln Q_L at fixed G^2 and fixed spin line.

    kappa_c = f/Q_L, so Q_L * e^{+-h} means kappa_c * e^{-+h} —
    LOG-SYMMETRIC perturbations with the exact central log-difference
    /(2h): bias is O(h^2) only. (The handoff's (1 +- eps) points over
    2*ln(1+eps) carry an O(eps) asymmetry artifact and are reproduced
    ONLY inside the V9 handoff-reproduction anchor, never here.) The
    G^2 anchoring — import-preserving or on-res-ratio-derived — is the
    caller's, via `g2`; C0 = G^2/(a_c*a_s) then scales as Q_L, the
    napkin C proportional-to-Q assumption of the closed-form exponent.
    """
    if not h_log > 0.0:
        raise ValueError("h_log must be positive")
    m_hi = margin_fixed_g2(
        g2,
        kappa_c_fwhm_mhz * math.exp(-h_log),
        s_spin,
        window_mhz=window_mhz,
        n_scan=n_scan,
        xtol_mhz=xtol_mhz,
    )
    m_lo = margin_fixed_g2(
        g2,
        kappa_c_fwhm_mhz * math.exp(+h_log),
        s_spin,
        window_mhz=window_mhz,
        n_scan=n_scan,
        xtol_mhz=xtol_mhz,
    )
    if m_hi.delta_f_max_mhz <= 0.0 or m_lo.delta_f_max_mhz <= 0.0:
        raise ValueError(
            "exponent undefined: a perturbed point sits at/below the "
            "on-resonance threshold"
        )
    exponent = (
        math.log(m_hi.delta_f_max_mhz) - math.log(m_lo.delta_f_max_mhz)
    ) / (2.0 * h_log)
    return ExponentResult(
        exponent=exponent,
        h_log=h_log,
        margin_q_hi_mhz=m_hi.delta_f_max_mhz,
        margin_q_lo_mhz=m_lo.delta_f_max_mhz,
        root_q_hi=m_hi.root,
        root_q_lo=m_lo.root,
    )
