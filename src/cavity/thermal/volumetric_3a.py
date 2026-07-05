"""SPEC §7.T5 check 3a, volumetric-source appendix — does burying the
near-spot source move the k–w degeneracy the PLATE verdict rests on?

The 3a sweep (`identifiability`, report identifiability_3a.md) found the
PLATE verdict CONDITIONAL on an exact k–w degeneracy: in the spreading
regime ΔT ∝ 1/(k·w) with log-slopes −1.00/−1.00, and the de-confounding
requirement ("w known to ×2.3–×3.2") is computed FROM that scaling. But
that sweep deposits the pump as a SURFACE flux, while the real pump is
absorbed volumetrically (Beer-Lambert). If l_abs ≳ w the near-spot
source is a buried cylinder, not a surface disk, and the w-slope can
deviate from −1.00 — shifting the ×-factor the Angus-email argument
leans on. This module quantifies exactly that, PLATE only (the FILM
verdict never depended on k_PTP).

Scope discipline:
- Same observable as the headline sweep: beam-centre SURFACE rise
  ΔT(0,0)/P. The ODMR probe in truth averages over the emitting
  (absorbing) volume, not the surface — a stated limitation of the
  appendix, not silently changed here.
- Same stencil as the headline sweep: multiplicative central
  differences at ×1.2 / ÷1.2 (`identifiability.log_sensitivities`).
- l_abs is held FIXED AND KNOWN inside the de-confounding search: the
  ×-factor measures how the k–w degeneracy deforms under a volumetric
  kernel, not the extra nuisance of an unknown l_abs (that question is
  the D.3 branch of the appendix report).
- l_abs values are §6T `PumpAbsorptionLength` SCOPING values
  (UNSOURCED-SCOPING grade) — they bracket plausibility, they are not
  provenance-grade inputs.

Engine: `layered.delta_t_gaussian_volumetric` (anchored in
tests/test_thermal_volumetric.py before this sweep ran — §8 discipline).
"""

from __future__ import annotations

import math

import numpy as np

from cavity.provenance.constants import GLASS_SLIDE, K_PTP, L_ABS_PUMP
from cavity.thermal.identifiability import (
    FORMS,
    K_BAND,
    NAMED_POINTS,
    FormSweep,
    SweepConfig,
    rig_stack,
)
from cavity.thermal.layered import delta_t_gaussian_volumetric

L_ABS_GRID = L_ABS_PUMP.l_abs_scoping_grid_m

# The surface-flux w-slope band of decision rule D.2: SCALING ROBUST iff
# the volumetric w-slope stays inside it across the whole l_abs grid.
W_SLOPE_ROBUST_BAND = (-1.1, -0.9)


def delta_t_center_volumetric(
    t_ptp_m: float,
    k_ptp: float,
    w_m: float,
    t_wax_m: float,
    l_abs_m: float,
    t_glass_m: float = GLASS_SLIDE.t_glass_m,
    h_top: float = 0.0,
) -> float:
    """ΔT(0,0) per watt absorbed (K/W), volumetric source in the PTP layer."""
    return delta_t_gaussian_volumetric(
        0.0, rig_stack(t_ptp_m, k_ptp, t_wax_m, t_glass_m), 1.0, w_m, l_abs_m, h_top
    )


def r_ratio_volumetric(
    t_ptp_m: float, w_m: float, t_wax_m: float, l_abs_m: float, **kw
) -> float:
    """Identifiability ratio R with the volumetric kernel (same definition)."""
    lo, mid, hi = (
        delta_t_center_volumetric(t_ptp_m, k, w_m, t_wax_m, l_abs_m, **kw)
        for k in K_BAND
    )
    return (lo - hi) / mid


def log_slopes_volumetric(
    form: str,
    w_m: float,
    t_wax_m: float,
    l_abs_m: float,
    rel_step: float = 0.2,
) -> dict[str, float]:
    """∂lnΔT/∂ln{k, w, t_wax} at k_mid — same stencil as the headline sweep
    (`identifiability.log_sensitivities`: central differences, ×1.2 / ÷1.2)."""
    t_ptp = FORMS[form]
    k_mid = K_PTP.k_mid_w_m_k

    def dt(k=k_mid, w=w_m, t_wax=t_wax_m, l_abs=l_abs_m):
        return delta_t_center_volumetric(t_ptp, k, w, t_wax, l_abs)

    def log_deriv(f_hi: float, f_lo: float) -> float:
        s = 1.0 + rel_step
        return math.log(f_hi / f_lo) / math.log(s / (1 / s))

    s = 1.0 + rel_step
    return {
        "dlnT_dlnk": log_deriv(dt(k=k_mid * s), dt(k=k_mid / s)),
        "dlnT_dlnw": log_deriv(dt(w=w_m * s), dt(w=w_m / s)),
        "dlnT_dlntwax": log_deriv(dt(t_wax=t_wax_m * s), dt(t_wax=t_wax_m / s)),
        # the D.3 input: how strong a lever an UNKNOWN l_abs would be
        "dlnT_dlnlabs": log_deriv(dt(l_abs=l_abs_m * s), dt(l_abs=l_abs_m / s)),
    }


def run_form_volumetric(
    form: str, l_abs_m: float, config: SweepConfig = SweepConfig()
) -> FormSweep:
    """ΔT grids for one form at one FIXED l_abs (the expensive step).

    Returns the same `FormSweep` artefact as the surface sweep, so the
    confounding machinery (`confounding_mismatch`,
    `w_prior_factor_to_deconfound`) applies verbatim — deliberate: the
    ×-factor is then computed by the identical code path as the headline
    ×2.3–×3.2 numbers it is being compared against.
    """
    t_ptp = FORMS[form]
    w = config.w_grid()
    t_wax = config.t_wax_grid()
    delta_t = np.empty((3, config.n_w, config.n_t_wax))
    for q, k_ptp in enumerate(K_BAND):
        for i, w_i in enumerate(w):
            for j, t_j in enumerate(t_wax):
                delta_t[q, i, j] = delta_t_center_volumetric(
                    t_ptp, k_ptp, w_i, t_j, l_abs_m, config.t_glass_m, config.h_top
                )
    return FormSweep(form, t_ptp, w, t_wax, delta_t)


def named_point_row(point: str, l_abs_m: float) -> dict[str, float]:
    """One C.2 table row: slopes + R at a PLATE named point and one l_abs."""
    w, t_wax = NAMED_POINTS[point]
    slopes = log_slopes_volumetric("PLATE", w, t_wax, l_abs_m)
    return {
        "l_abs_m": l_abs_m,
        "r": r_ratio_volumetric(FORMS["PLATE"], w, t_wax, l_abs_m),
        **slopes,
    }
