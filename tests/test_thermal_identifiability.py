"""SPEC §7.T5 check 3a — identifiability-sweep regression + logic tests.

The four named-point R values are REGRESSION PINS: they encode the
verdict-setting numbers of thermal/reports/identifiability_3a.md, so a
future refactor of the layered solver or the sweep cannot silently
shift the check-3a verdicts. If a deliberate physics change moves them,
re-run `python -m cavity.thermal.report_3a`, re-read the verdicts, and
update the pins together with the report — never the pins alone.
"""

from __future__ import annotations

import math

import numpy as np

from cavity.provenance.constants import GLASS_SLIDE, K_PTP, RIG_GEOMETRY, WAX
from cavity.thermal.identifiability import (
    FORMS,
    IDENTIFIABLE,
    PARTIAL,
    UNIDENTIFIABLE,
    NAMED_POINTS,
    SweepConfig,
    confounding_mismatch,
    r_ratio,
    verdict_map,
)

# Direct (grid-free) R at the named points, adaptive quadrature at
# epsrel ~1e-8; pinned at 8 significant figures with 1e-6 slack.
R_PINS = {
    ("PLATE", "focused_thin_wax"): 2.8449522,
    ("PLATE", "doublet_mid_wax"): 2.8042784,
    ("FILM", "focused_thin_wax"): 0.29179459,
    ("FILM", "doublet_mid_wax"): 0.011839604,
}


def test_r_map_regression_pins():
    for (form, point), pinned in R_PINS.items():
        w, t_wax = NAMED_POINTS[point]
        got = r_ratio(FORMS[form], w, t_wax)
        assert math.isclose(got, pinned, rel_tol=1e-6), (form, point, got)


def test_regime_inversion_plate_vs_film():
    """§7.T5's anticipated inversion, now quantified: the PLATE (w ≪ t,
    PTP-spreading-dominated) observable swings ~2.8× the signal across
    the k band; the FILM (w ≫ t, substrate-dominated) observable barely
    moves at doublet-class spots."""
    r_plate = R_PINS[("PLATE", "doublet_mid_wax")]
    r_film = R_PINS[("FILM", "doublet_mid_wax")]
    assert r_plate > 100 * r_film
    assert r_film < 2 * 0.05  # UNIDENTIFIABLE even at the tightest sigma


def test_verdict_thresholds():
    r = np.array([[0.05, 0.11], [0.21, 0.9]])
    got = verdict_map(r, sigma_rel=0.10)
    want = np.array([[UNIDENTIFIABLE, PARTIAL], [IDENTIFIABLE, IDENTIFIABLE]])
    np.testing.assert_array_equal(got, want)


def _synthetic_delta_t(mid: np.ndarray, lo_fac: float, hi_fac: float) -> np.ndarray:
    return np.stack([mid * lo_fac, mid, mid * hi_fac])


def test_confounding_bracketing_detected():
    """If a band edge crosses the data value along a nuisance path, the
    point is confounded (mismatch 0) even when no grid node lands on it."""
    mid = np.outer(np.geomspace(1, 10, 5), np.ones(4))
    delta_t = _synthetic_delta_t(mid, lo_fac=1.5, hi_fac=0.6)
    # lo-edge values at other w mimic mid data: 1.5*mid[i'] crosses mid[i]
    mm = confounding_mismatch(delta_t, "both_free")
    assert np.all(mm[1:-1, :] == 0.0)


def test_confounding_pinned_nuisances_resolve():
    """With ALL nuisances pinned to truth (constant-ΔT rows/columns so no
    path can bracket), the mismatch equals the band-edge offset itself."""
    mid = np.full((3, 3), 2.0)
    delta_t = _synthetic_delta_t(mid, lo_fac=1.3, hi_fac=0.8)
    for scenario in ("w_pinned", "t_wax_pinned"):
        mm = confounding_mismatch(delta_t, scenario)
        np.testing.assert_allclose(mm, 0.2)  # closer edge (hi) is 20% off


def test_sweep_config_boxes_come_from_provenance():
    """B-task boxes must single-source from §6T (no re-typed numbers)."""
    config = SweepConfig()
    assert config.w_lo_m == RIG_GEOMETRY.w_box_lo_m == 1e-6
    assert config.w_hi_m == RIG_GEOMETRY.w_box_hi_m == 500e-6
    assert config.t_wax_lo_m == WAX.t_wax_box_lo_m == 1e-6
    assert config.t_wax_hi_m == WAX.t_wax_box_hi_m == 100e-6
    assert config.t_glass_m == GLASS_SLIDE.t_glass_m == 1e-3
    assert FORMS["PLATE"] == RIG_GEOMETRY.t_plate_m == 0.5e-3
    assert FORMS["FILM"] == RIG_GEOMETRY.t_film_m == 100e-9
    assert K_PTP.k_band_lo_w_m_k == 0.1 and K_PTP.k_band_hi_w_m_k == 1.0
    assert math.isclose(K_PTP.k_mid_w_m_k, math.sqrt(0.1))
