"""SPEC §7.T5 check 3a — k_PTP identifiability sweep (the decision engine).

Decides, BEFORE the Angus introduction, whether the Cowley-Semple
spin-shift-vs-laser-power slope can calibrate k_PTP at all, or whether
the two unknown rig nuisances — pump-spot radius w and wax bond-line
thickness t_wax — dominate the temperature rise so that the fitted
slope calibrates the rig, not the material.

Design choices (all recorded in the generated report):

- Observable: the steady-state centre-spot temperature rise per unit
  absorbed power, ΔT(0,0)/P. P enters linearly and is normalised out;
  the identifiability metric R is therefore independent of the
  (uncalibrated) absolute laser power. ΔT is evaluated at the beam
  centre — the ODMR-probed volume is the illuminated spot (SPEC §7.T5
  observable (a): excitation/collection co-located).
- Stack: PTP layer (t_PTP per sample form, k_PTP the band under test)
  on paraffin wax (t_wax nuisance) on a glass slide (t_glass = 1 mm),
  slide base at bath temperature, top surface insulated (h = 0 default;
  the Robin sensitivity is reported, not assumed away).
- Sweep box (§6T constants): w ∈ [1, 500] µm log-spaced (two-optic
  record, `RigSampleGeometry`), t_wax ∈ [1, 100] µm log-spaced
  (unsourced bracket, `ParaffinWaxThermal`), k_PTP ∈ {0.1, √0.1, 1.0}
  W/m/K — band edges plus geometric midpoint (`k_mid` — the band is a
  ×10 multiplicative bracket, so the log-midpoint is the natural
  reference).
- Identifiability ratio, per (w, t_wax) grid point:
      R = [ΔT(k=0.1) − ΔT(k=1.0)] / ΔT(k_mid)
  IDENTIFIABLE where R > 2σ_rel, PARTIAL where R > σ_rel, else
  UNIDENTIFIABLE, at σ_rel ∈ {5, 10, 20}% (bracketing unknown error
  bars).
- Confounding (profile-likelihood-style, grid search — a scoping calc,
  not Layer C): a point is CONFOUNDED at σ_rel if a band-EDGE k, with
  the nuisances free inside their box, can reproduce the k_mid
  observable within σ_rel. Because ΔT is continuous in (w, t_wax), a
  sign change of ΔT_edge − ΔT_data between adjacent grid nodes proves
  an exact match exists between them; the grid search counts such
  bracketings as mismatch zero, so grid resolution cannot fake
  identifiability. Three nuisance scenarios rank the Angus asks:
  both free / w pinned at truth / t_wax pinned at truth.

The multiplicative confounders NOT in this sweep (flagged, §6T): the
df_spin/dT band (−50…−101 kHz/K, a ×2 spread) and the absolute
laser-power calibration multiply the measured slope exactly like 1/k
does in the spreading regime. R is immune to them by construction, but
any absolute k inference inherits them on top of the (w, t_wax) story.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from cavity.provenance.constants import GLASS_SLIDE, K_PTP, RIG_GEOMETRY, WAX
from cavity.thermal.layered import Layer, delta_t_gaussian

UNIDENTIFIABLE, PARTIAL, IDENTIFIABLE = 0, 1, 2
VERDICT_NAMES = {0: "UNIDENTIFIABLE", 1: "PARTIAL", 2: "IDENTIFIABLE"}

SIGMA_REL = (0.05, 0.10, 0.20)

K_BAND = (K_PTP.k_band_lo_w_m_k, K_PTP.k_mid_w_m_k, K_PTP.k_band_hi_w_m_k)

FORMS = {
    "PLATE": RIG_GEOMETRY.t_plate_m,
    "FILM": RIG_GEOMETRY.t_film_m,
}

# Named grid points: regression pins (tests/test_thermal_identifiability.py)
# and the local-sensitivity / Angus-ask analysis. (w_m, t_wax_m).
NAMED_POINTS = {
    "focused_thin_wax": (3.16e-6, 3.16e-6),
    "doublet_mid_wax": (100e-6, 31.6e-6),
}


@dataclass(frozen=True)
class SweepConfig:
    """Grid resolution + boxes. Boxes come from §6T; do not re-type them."""

    n_w: int = 41
    n_t_wax: int = 25
    w_lo_m: float = RIG_GEOMETRY.w_box_lo_m
    w_hi_m: float = RIG_GEOMETRY.w_box_hi_m
    t_wax_lo_m: float = WAX.t_wax_box_lo_m
    t_wax_hi_m: float = WAX.t_wax_box_hi_m
    t_glass_m: float = GLASS_SLIDE.t_glass_m
    h_top: float = 0.0

    def w_grid(self) -> np.ndarray:
        return np.logspace(math.log10(self.w_lo_m), math.log10(self.w_hi_m), self.n_w)

    def t_wax_grid(self) -> np.ndarray:
        return np.logspace(
            math.log10(self.t_wax_lo_m), math.log10(self.t_wax_hi_m), self.n_t_wax
        )


def rig_stack(
    t_ptp_m: float,
    k_ptp: float,
    t_wax_m: float,
    t_glass_m: float = GLASS_SLIDE.t_glass_m,
) -> tuple[Layer, ...]:
    """PTP / wax / glass stack, slide base at bath (SPEC §7.T5 rig model)."""
    return (
        Layer(t_ptp_m, k_ptp),
        Layer(t_wax_m, WAX.k_w_m_k),
        Layer(t_glass_m, GLASS_SLIDE.k_w_m_k),
    )


def delta_t_center(
    t_ptp_m: float,
    k_ptp: float,
    w_m: float,
    t_wax_m: float,
    t_glass_m: float = GLASS_SLIDE.t_glass_m,
    h_top: float = 0.0,
) -> float:
    """ΔT(0,0) per watt absorbed (K/W) for one rig configuration."""
    return delta_t_gaussian(
        0.0, rig_stack(t_ptp_m, k_ptp, t_wax_m, t_glass_m), 1.0, w_m, h_top
    )


def r_ratio(t_ptp_m: float, w_m: float, t_wax_m: float, **kw) -> float:
    """Identifiability ratio R at one point (direct, grid-free)."""
    lo, mid, hi = (delta_t_center(t_ptp_m, k, w_m, t_wax_m, **kw) for k in K_BAND)
    return (lo - hi) / mid


@dataclass
class FormSweep:
    """All sweep artefacts for one sample form."""

    form: str
    t_ptp_m: float
    w_m: np.ndarray
    t_wax_m: np.ndarray
    # delta_t[q, i, j]: k index q in (lo, mid, hi), spot i, wax j — K/W
    delta_t: np.ndarray
    r_map: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        lo, mid, hi = self.delta_t
        self.r_map = (lo - hi) / mid


def run_form(form: str, config: SweepConfig = SweepConfig()) -> FormSweep:
    """Evaluate the ΔT grids for one sample form (the expensive step)."""
    t_ptp = FORMS[form]
    w = config.w_grid()
    t_wax = config.t_wax_grid()
    delta_t = np.empty((3, config.n_w, config.n_t_wax))
    for q, k_ptp in enumerate(K_BAND):
        for i, w_i in enumerate(w):
            for j, t_j in enumerate(t_wax):
                delta_t[q, i, j] = delta_t_center(
                    t_ptp, k_ptp, w_i, t_j, config.t_glass_m, config.h_top
                )
    return FormSweep(form, t_ptp, w, t_wax, delta_t)


def verdict_map(r_map: np.ndarray, sigma_rel: float) -> np.ndarray:
    """C.2 threshold rule: R > 2σ IDENTIFIABLE, R > σ PARTIAL, else UNIDENT."""
    out = np.full(r_map.shape, UNIDENTIFIABLE, dtype=int)
    out[r_map > sigma_rel] = PARTIAL
    out[r_map > 2.0 * sigma_rel] = IDENTIFIABLE
    return out


def _min_mismatch(candidates: np.ndarray, data: float) -> float:
    """Best relative reproduction of `data` achievable on a candidate set.

    `candidates` is a 1-D array of ΔT values reachable by moving the
    nuisances along a CONTINUOUS path through adjacent grid nodes (a
    grid row/column, or a row-major sweep of the full grid). Any sign
    change of (candidate − data) between adjacent nodes brackets an
    exact match, so the mismatch there is zero by continuity.
    """
    resid = candidates / data - 1.0
    best = float(np.min(np.abs(resid)))
    if best > 0.0 and np.any(np.diff(np.sign(resid)) != 0):
        return 0.0
    return best


def confounding_mismatch(
    delta_t: np.ndarray, scenario: str
) -> np.ndarray:
    """Worst-case (over both band edges) confounding mismatch map.

    For each grid point (i, j) taken as the truth at k_mid, returns the
    smaller of the two band edges' minimum reproduction mismatch over
    the allowed nuisance set:

      - "both_free":   (w, t_wax) anywhere in the box,
      - "w_pinned":    w fixed at truth, t_wax free,
      - "t_wax_pinned": t_wax fixed at truth, w free.

    CONFOUNDED at σ_rel wherever the returned mismatch < σ_rel (either
    band edge mimics the data ⇒ the band is not resolved).
    """
    _, mid, _ = delta_t
    n_w, n_t = mid.shape
    out = np.empty((n_w, n_t))
    for i in range(n_w):
        for j in range(n_t):
            data = mid[i, j]
            per_edge = []
            for edge in (delta_t[0], delta_t[2]):
                if scenario == "both_free":
                    # Scan every grid column (continuous in w) and row
                    # (continuous in t_wax) so a bracketing between any
                    # pair of adjacent nodes in either direction counts.
                    mm = min(
                        min(_min_mismatch(edge[:, jj], data) for jj in range(n_t)),
                        min(_min_mismatch(edge[ii, :], data) for ii in range(n_w)),
                    )
                elif scenario == "w_pinned":
                    mm = _min_mismatch(edge[i, :], data)
                elif scenario == "t_wax_pinned":
                    mm = _min_mismatch(edge[:, j], data)
                else:
                    raise ValueError(f"unknown scenario {scenario!r}")
                per_edge.append(mm)
            out[i, j] = min(per_edge)
    return out


def confounded_map(
    delta_t: np.ndarray, sigma_rel: float, scenario: str
) -> np.ndarray:
    """Boolean CONFOUNDED map (C.3) for one scenario at one σ_rel."""
    return confounding_mismatch(delta_t, scenario) < sigma_rel


def w_prior_factor_to_deconfound(
    sweep: FormSweep, i: int, j: int, sigma_rel: float, factor_grid=None
) -> float | None:
    """How tightly must the spot radius be known to rescue check 3a?

    Smallest multiplicative half-width s such that restricting the
    w-nuisance to [w*/s, w*·s] (t_wax still fully free) removes the
    confounding at grid point (i, j) — i.e. both band edges then miss
    the k_mid observable by ≥ σ_rel. Returns None if even exact
    knowledge of w (s = 1) leaves the point confounded (t_wax alone
    compensates), and math.inf if no restriction is needed.
    """
    if factor_grid is None:
        factor_grid = np.geomspace(1.0, 500.0, 60)
    w = sweep.w_m
    data = sweep.delta_t[1, i, j]

    def mismatch_with_halfwidth(s: float) -> float:
        mask = (w >= w[i] / s) & (w <= w[i] * s)
        idx = np.where(mask)[0]
        per_edge = []
        for edge in (sweep.delta_t[0], sweep.delta_t[2]):
            mm = min(
                _min_mismatch(edge[idx, jj], data)
                for jj in range(len(sweep.t_wax_m))
            )
            per_edge.append(mm)
        return min(per_edge)

    if mismatch_with_halfwidth(factor_grid[-1]) >= sigma_rel:
        return math.inf
    if mismatch_with_halfwidth(1.0) < sigma_rel:
        return None
    for s_lo, s_hi in zip(factor_grid[:-1], factor_grid[1:]):
        if mismatch_with_halfwidth(s_hi) < sigma_rel <= mismatch_with_halfwidth(s_lo):
            return float(s_lo)
    return float(factor_grid[0])


def log_sensitivities(
    form: str, w_m: float, t_wax_m: float, rel_step: float = 0.2
) -> dict[str, float]:
    """Local log-derivatives ∂lnΔT/∂ln(param) at k_mid — the D.2 ranking input.

    Central differences with multiplicative step (1 ± rel_step ≈
    ×1.2 / ÷1.2). `t_glass` uses the ±50% step SPEC §7.T5 prescribes.
    Also reports the fractional ΔT drop from an h = 20 W/m²K Robin top
    (the insulated-top sensitivity, not a log-derivative).
    """
    t_ptp = FORMS[form]
    k_mid = K_PTP.k_mid_w_m_k

    def dt(k=k_mid, w=w_m, t_wax=t_wax_m, t_glass=GLASS_SLIDE.t_glass_m, h=0.0):
        return delta_t_center(t_ptp, k, w, t_wax, t_glass, h)

    def log_deriv(f_hi: float, f_lo: float, x_hi: float, x_lo: float) -> float:
        return math.log(f_hi / f_lo) / math.log(x_hi / x_lo)

    s = 1.0 + rel_step
    out = {
        "dlnT_dlnk": log_deriv(dt(k=k_mid * s), dt(k=k_mid / s), s, 1 / s),
        "dlnT_dlnw": log_deriv(dt(w=w_m * s), dt(w=w_m / s), s, 1 / s),
        "dlnT_dlntwax": log_deriv(
            dt(t_wax=t_wax_m * s), dt(t_wax=t_wax_m / s), s, 1 / s
        ),
    }
    g = GLASS_SLIDE.t_glass_sensitivity_frac
    out["dlnT_dlntglass"] = log_deriv(
        dt(t_glass=GLASS_SLIDE.t_glass_m * (1 + g)),
        dt(t_glass=GLASS_SLIDE.t_glass_m * (1 - g)),
        1 + g,
        1 - g,
    )
    base = dt()
    out["robin_h20_frac_drop"] = (base - dt(h=20.0)) / base
    return out
