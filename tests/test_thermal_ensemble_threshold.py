"""SPEC §7.T4 — multi-packet/Voigt ensemble-threshold anchors V0-V10 (§8 discipline).

Audits the single-packet mapping of the committed two-linewidth law
(`ensemble_threshold` module; the D4 hom/inhom decomposition stays
OPEN — every Voigt case is a scenario probe). Anchor map:

V0  domain guards + the Delta = 0 symmetric-line precondition guard.
V1  single-packet ensemble route reproduces `delta_f_max_hz` and the
    pulled frequency (closed form, rel <= 1e-9), both normalisations.
V2  degenerate sigma_g -> 0 Voigt == single packet (A12/A13-family
    continuity).
V3  Lorentzian-distribution identity (the gate): discrete quantile
    ensemble == single-packet kappa_s_eff = kappa_hom + 2*Gamma law,
    rel <= 1e-4 (handoff §7.4 acceptance identity, reproduced in-repo).
V4  exact Voigt-FWHM sizing: solved composite == KAPPA_S to 1e-10;
    f_L = 1.4 => sigma_g = 0 exactly; f_L -> 0 => pure-Gaussian FWHM
    identity; Olivero-Longbothum agreement <= 1e-3 (diagnostic only);
    scipy.special.voigt_profile convention cross-check.
V5  normalisation identity on the Lorentzian branch (import-preserving
    fixed-G^2 == on-res ratio == closed form) + strict Voigt ordering:
    the fixed-G^2 margin exceeds the on-res-ratio margin because the
    Voigt peak exceeds the same-FWHM Lorentzian peak.
V6  discrete-Gaussian-grid-vs-wofz agreement at the pinned margins:
    the uniform-grid packet sum sits at its trapezoid-exponential-
    accuracy floor (<= 1e-9 asserted, ~1e-13 observed), INVARIANT
    under node AND span doubling — the plan's <= 1e-3-improving-under-
    doubling requirement is met at double-precision saturation. Scan
    window/resolution invariance of margins <= 1e-9.
V7  fixed-G^2 exponent control (AMENDED discipline): LOG-SYMMETRIC
    Q*e^{+-h} perturbations with exact /(2h) log-difference; the
    Lorentzian control reproduces the analytic `q_margin_exponent` to
    rel <= 1e-4 at h = 0.02; h = 0.05 consistency.
V8  target-proportional-to-Q substitution identity for symmetric lines
    (validates the handoff check-7 shortcut, exp form, rel <= 1e-9).
V9  handoff reproduction, THEIR formulation as-is (their O-L sizing
    sigma = 1.39/2.35482 and 1.00/2.35482 — NOT exact-FWHM sizing;
    their kc = 0.257; on-res-ratio normalisation; their asymmetric
    eps = 0.05 exponent formula /(2 ln(1+eps))): margins 11.39 / 7.77 /
    7.51 and E_a ~ +0.356, E_b ~ -0.160. THE SIGN FLIP (E_b < 0) IS
    THE GATE — its non-reproduction is a plan stop-and-report trigger.
    Packet weights are identical between their formulation and this
    module (Gaussian centre distribution); no weighting difference to
    label beyond the report note.
V10 regression pins on the exact-FWHM sweep under BOTH normalisations
    (values cross-checked in-session by the independent packet-sum
    route before pinning — scoping-numbers discipline), the in-CI
    packet-sum cross-check at the pinned margins (node/span-doubled),
    the E = 0 sign-change bracket per normalisation, and the
    q_margin_voigt_sensitivity.md byte-pin.

UNITS in every pin: cyclic-Hz-FWHM linewidths expressed in MHz
(matched units: amplitude rates = FWHM/2 numerically); margins are
cyclic MHz; G^2 values are in (MHz amplitude-rate)^2 under the matched
convention. NORMALISATION is stated per pin: "fixed-G^2" = the
repo-consistent import-preserving fixed-G^2 anchoring
G^2 = C0*kappa_c*kappa_s_composite/4 (amendment C; an algebraic import,
not a measured coupling); "on-res ratio" = G^2_th(Delta)/G^2_th(0) = C0
(the handoff's convention).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from scipy.special import ndtri, voigt_profile

from cavity.provenance.constants import KAPPA_S, TARGET
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.detuning import (
    delta_f_max_hz,
    q_loaded,
    q_margin_exponent,
)
from cavity.thermal.ensemble_threshold import (
    FIXED_G2_LABEL,
    GAUSSIAN_FWHM_PER_SIGMA,
    ONRES_RATIO_LABEL,
    g2_fixed_import_preserving,
    make_voigt_s_spin,
    margin_fixed_g2,
    margin_onres_ratio,
    olivero_longbothum_fwhm_mhz,
    q_margin_exponent_numeric,
    threshold_g2,
    voigt_fwhm_mhz,
    voigt_profile_per_mhz,
    voigt_sigma_g_mhz,
)
from cavity.thermal.report_margin import PLANNING_C0, own_model_point
from cavity.thermal.report_voigt import SWEEP_F_L_MHZ, build_report

F_HZ = TARGET.f_design_hz
KAPPA_S_MHZ = KAPPA_S.kappa_s_hz / 1e6  # 1.4, cyclic-FWHM


def _kappa_c_mhz() -> float:
    """The one composed kappa_c (own-model Q0 x DELOAD_K), in MHz."""
    own = own_model_point()
    return resonance_linewidth_hz(F_HZ, q_loaded(own["q0_canonical"])) / 1e6


def _discrete_s_spin(centers, weights, f_hom_fwhm_mhz, chunk=256):
    """Generic packet-sum susceptibility (E2 form) — the wofz-free
    validation route. Vectorised in chunks to bound memory."""
    c = np.asarray(centers, dtype=float)
    w = np.asarray(weights, dtype=float)
    a_s = 0.5 * f_hom_fwhm_mhz

    def s_spin(omega):
        om = np.atleast_1d(np.asarray(omega, dtype=float))
        out = np.empty(om.shape, dtype=complex)
        for i0 in range(0, om.size, chunk):
            blk = om[i0 : i0 + chunk]
            denom = a_s + 1j * (c[None, :] - blk[:, None])
            out[i0 : i0 + chunk] = (w[None, :] / denom).sum(axis=1)
        return out if np.ndim(omega) else complex(out[0])

    return s_spin


def _grid_gaussian_s_spin(sigma, f_hom_fwhm, npts, span):
    """Handoff-style discrete Gaussian ensemble: uniform grid
    x in [-span, span] sigma-units, weights prop exp(-x^2/2),
    normalised (their `wt /= wt.sum()`)."""
    x = np.linspace(-span, span, npts)
    w = np.exp(-0.5 * x * x)
    return _discrete_s_spin(sigma * x, w / w.sum(), f_hom_fwhm)


def _quantile_lorentzian_s_spin(gamma_hwhm, f_hom_fwhm, n=4001, cut=60.0):
    """Handoff check-4 ensemble: deterministic Lorentzian quantile
    sampling, equal UNRENORMALISED 1/n weights after the |c| < cut*Gamma
    tail truncation (the truncated tails' contribution at the evaluation
    frequencies is negligible; their WEIGHT is not — renormalising
    would misweight the core)."""
    q = (np.arange(n) + 0.5) / n
    c = gamma_hwhm * np.tan(np.pi * (q - 0.5))
    keep = np.abs(c) < cut * gamma_hwhm
    return _discrete_s_spin(
        c[keep], np.full(int(keep.sum()), 1.0 / n), f_hom_fwhm
    )


# --- V0: domain + precondition guards ----------------------------------------


def test_v0_domain_guards():
    with pytest.raises(ValueError, match="f_L must be positive"):
        make_voigt_s_spin(0.0, 0.5)
    with pytest.raises(ValueError, match="non-negative"):
        make_voigt_s_spin(1.0, -0.1)
    with pytest.raises(ValueError, match="0 < f_L"):
        voigt_sigma_g_mhz(1.5, 1.4)
    with pytest.raises(ValueError, match="0 < f_L"):
        voigt_sigma_g_mhz(0.0, 1.4)
    with pytest.raises(ValueError, match="kappa_c"):
        threshold_g2(1.0, 0.0, make_voigt_s_spin(1.4, 0.0))
    with pytest.raises(ValueError, match="C0 > 1"):
        margin_onres_ratio(1.0, 0.257, make_voigt_s_spin(1.4, 0.0))
    with pytest.raises(ValueError, match="positive"):
        g2_fixed_import_preserving(190.0, 0.257, 0.0)


def test_v0_delta_zero_symmetry_guard():
    # An asymmetric two-packet line must NOT silently take the
    # omega = 0 analytic branch at Delta = 0.
    s_asym = _discrete_s_spin([0.0, 2.0], [0.5, 0.5], 0.4)
    with pytest.raises(ValueError, match="symmetric"):
        threshold_g2(0.0, 0.257, s_asym)


# --- V1: single-packet route == committed law --------------------------------


def test_v1_single_packet_reproduces_committed_law_and_pulling():
    kappa_c = _kappa_c_mhz()
    s_lor = make_voigt_s_spin(KAPPA_S_MHZ, 0.0)
    g2 = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    expected_mhz = (
        delta_f_max_hz(PLANNING_C0, kappa_c * 1e6, KAPPA_S_MHZ * 1e6) / 1e6
    )

    m_fixed = margin_fixed_g2(g2, kappa_c, s_lor)
    assert m_fixed.delta_f_max_mhz == pytest.approx(expected_mhz, rel=1e-9)
    assert m_fixed.normalisation == FIXED_G2_LABEL
    # pulled frequency: omega_0 = Delta * a_s/(a_c + a_s), the
    # linewidth-weighted mean of the two-mode law
    a_c, a_s = 0.5 * kappa_c, 0.5 * KAPPA_S_MHZ
    assert m_fixed.root.omega_mhz == pytest.approx(
        m_fixed.delta_f_max_mhz * a_s / (a_c + a_s), rel=1e-9
    )
    # exactly one Im S = 0 branch on the single-packet line
    assert m_fixed.root.n_candidates == 1
    assert m_fixed.root.tangential_candidates is False

    m_ratio = margin_onres_ratio(PLANNING_C0, kappa_c, s_lor)
    assert m_ratio.delta_f_max_mhz == pytest.approx(expected_mhz, rel=1e-9)
    assert m_ratio.normalisation == ONRES_RATIO_LABEL
    # single-packet identity: the two G^2 anchorings coincide exactly
    assert m_ratio.g2 == pytest.approx(g2, rel=1e-12)


# --- V2: sigma_g -> 0 continuity ---------------------------------------------


def test_v2_degenerate_sigma_matches_single_packet():
    kappa_c = _kappa_c_mhz()
    g2 = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    base = margin_fixed_g2(
        g2, kappa_c, make_voigt_s_spin(KAPPA_S_MHZ, 0.0)
    ).delta_f_max_mhz
    for sigma, tol in ((1e-6, 1e-9), (1e-8, 1e-12)):
        near = margin_fixed_g2(
            g2, kappa_c, make_voigt_s_spin(KAPPA_S_MHZ, sigma)
        ).delta_f_max_mhz
        assert near == pytest.approx(base, rel=tol)


# --- V3: Lorentzian-distribution identity (the gate) -------------------------


def test_v3_lorentzian_quantile_ensemble_matches_kappa_eff_law():
    # Handoff check-4 point, matched units (amplitude rates x2 = FWHM):
    # kc = 1.0, ks_hom = 0.6, Gamma = 1.7, D = 4.0.
    kc_amp, ks_amp, gamma, delta = 1.0, 0.6, 1.7, 4.0
    s_q = _quantile_lorentzian_s_spin(gamma, 2.0 * ks_amp)
    numeric = threshold_g2(delta, 2.0 * kc_amp, s_q).g2_th
    # Lorentzian centre distribution folds EXACTLY into the packet:
    # ks_eff = ks_hom + Gamma (FWHM composition f_eff = f_hom + 2*Gamma)
    ks_eff = ks_amp + gamma
    closed = kc_amp * ks_eff * (1.0 + delta**2 / (kc_amp + ks_eff) ** 2)
    assert numeric == pytest.approx(closed, rel=1e-4)


# --- V4: exact Voigt-FWHM sizing ---------------------------------------------


def test_v4_exact_fwhm_sizing_and_degenerate_branches():
    for f_l in SWEEP_F_L_MHZ:
        sigma = voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ)
        assert voigt_fwhm_mhz(f_l, sigma) == pytest.approx(
            KAPPA_S_MHZ, abs=1e-10
        )
        # O-L approximation agreement — DIAGNOSTIC of the sizing, and
        # the quantified retirement of the handoff's ~1.44/1.29 MHz
        # sizing imprecision (its formula is off by <= ~2.4e-4 rel at
        # the solved sigma; the handoff applied it in reverse).
        ol = olivero_longbothum_fwhm_mhz(
            f_l, GAUSSIAN_FWHM_PER_SIGMA * sigma
        )
        assert abs(ol - KAPPA_S_MHZ) / KAPPA_S_MHZ < 1e-3
    # pure-Lorentzian repo branch: exactly zero, not small
    assert voigt_sigma_g_mhz(KAPPA_S_MHZ, KAPPA_S_MHZ) == 0.0
    # f_L -> 0: pure-Gaussian FWHM identity
    assert voigt_sigma_g_mhz(1e-9, KAPPA_S_MHZ) == pytest.approx(
        KAPPA_S_MHZ / GAUSSIAN_FWHM_PER_SIGMA, rel=1e-9
    )


def test_v4_profile_convention_matches_scipy():
    # scipy.special.voigt_profile(x, sigma, gamma_HWHM) — pins the
    # sigma-is-std / a_s-is-HWHM convention of the wofz identity.
    for x in (0.0, 0.3, 1.0, 5.0):
        mine = float(voigt_profile_per_mhz(x, 0.2, 0.5))
        assert mine == pytest.approx(voigt_profile(x, 0.5, 0.1), rel=1e-12)
    # Re S_spin = pi * V identity
    s_v = make_voigt_s_spin(0.2, 0.5)
    for x in (0.0, 1.0, 4.0):
        assert complex(s_v(x)).real == pytest.approx(
            math.pi * float(voigt_profile_per_mhz(x, 0.2, 0.5)), rel=1e-12
        )


# --- V5: normalisation identity + strict Voigt ordering ----------------------


def test_v5_lorentzian_identity_and_voigt_ordering():
    kappa_c = _kappa_c_mhz()
    a_c = 0.5 * kappa_c
    s_lor = make_voigt_s_spin(KAPPA_S_MHZ, 0.0)
    g2_imp = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    # Lorentzian branch: G^2_th(0) = a_c*a_s exactly, so the anchorings
    # coincide to float precision.
    onres = threshold_g2(0.0, kappa_c, s_lor)
    assert onres.g2_th == pytest.approx(
        a_c * 0.5 * KAPPA_S_MHZ, rel=1e-12
    )
    assert PLANNING_C0 * onres.g2_th == pytest.approx(g2_imp, rel=1e-12)
    # Voigt rows: the same-FWHM Voigt peak EXCEEDS the Lorentzian peak,
    # so G^2_th(0) is smaller, the ratio-derived G^2 is smaller than
    # the import-preserving G^2, and the margins order strictly.
    for f_l in (0.05, 0.10, 0.50, 1.00):
        sigma = voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ)
        s_v = make_voigt_s_spin(f_l, sigma)
        onres_v = threshold_g2(0.0, kappa_c, s_v)
        assert onres_v.g2_th < onres.g2_th
        m_fixed = margin_fixed_g2(g2_imp, kappa_c, s_v)
        m_ratio = margin_onres_ratio(PLANNING_C0, kappa_c, s_v)
        assert m_ratio.g2 < m_fixed.g2
        assert m_ratio.delta_f_max_mhz < m_fixed.delta_f_max_mhz


# --- V6: discrete-vs-wofz + scan invariance ----------------------------------


def test_v6_scan_window_and_resolution_invariance():
    kappa_c = _kappa_c_mhz()
    f_l = 0.10
    s_v = make_voigt_s_spin(f_l, voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ))
    g2 = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    base = margin_fixed_g2(g2, kappa_c, s_v)
    for window, n_scan in ((60.0, 3001), (30.0, 6001), (60.0, 6001)):
        m = margin_fixed_g2(
            g2, kappa_c, s_v, window_mhz=window, n_scan=n_scan
        )
        assert m.delta_f_max_mhz == pytest.approx(
            base.delta_f_max_mhz, rel=1e-9
        )
        # branch audit: same single root branch under doubling
        assert m.root.n_candidates == base.root.n_candidates == 1
        assert m.root.omega_mhz == pytest.approx(
            base.root.omega_mhz, rel=1e-9
        )


def test_v6_far_wing_asymptotics():
    # Re S_spin -> a_s/omega^2 (Lorentzian packet tails) — the far-wing
    # mechanism every margin in this audit rides on.
    for f_l in (0.10, KAPPA_S_MHZ):
        sigma = voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ)
        s_v = make_voigt_s_spin(f_l, sigma)
        a_s = 0.5 * f_l
        previous = math.inf
        for omega in (10.0, 20.0, 40.0):
            ratio = complex(s_v(omega)).real / (a_s / omega**2)
            assert ratio == pytest.approx(1.0, abs=0.02)
            deviation = abs(ratio - 1.0)
            assert deviation < previous  # monotone approach
            previous = deviation


# --- V7: fixed-G^2 exponent control (amended log-symmetric discipline) -------


def test_v7_lorentzian_exponent_control_tight():
    kappa_c = _kappa_c_mhz()
    s_lor = make_voigt_s_spin(KAPPA_S_MHZ, 0.0)
    g2 = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    closed = q_margin_exponent(
        PLANNING_C0, kappa_c * 1e6, KAPPA_S_MHZ * 1e6
    )
    # Amended target: log-symmetric Q e^{+-h} + exact /(2h) must
    # reproduce the analytic exponent to <= 1e-4 REL at h = 0.02 —
    # not merely "within finite-difference bias".
    e_002 = q_margin_exponent_numeric(g2, kappa_c, s_lor, h_log=0.02)
    assert e_002.exponent == pytest.approx(closed, rel=1e-4)
    # h = 0.05 consistency: O(h^2) bias only (the residual grows
    # ~(0.05/0.02)^2 = 6.25x but stays <= 5e-4 rel).
    e_005 = q_margin_exponent_numeric(g2, kappa_c, s_lor, h_log=0.05)
    assert e_005.exponent == pytest.approx(closed, rel=5e-4)
    assert abs(e_005.exponent - e_002.exponent) < 5e-4


# --- V8: target-prop-Q substitution identity ---------------------------------


def test_v8_target_proportional_to_q_identity_symmetric_lines():
    kappa_c = _kappa_c_mhz()
    h = 0.05
    for f_l in (0.10, KAPPA_S_MHZ):
        sigma = voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ)
        s_v = make_voigt_s_spin(f_l, sigma)
        g0 = threshold_g2(0.0, kappa_c, s_v).g2_th
        # direct fixed-G^2 route at perturbed Q (kappa_c e^{-h}), G^2
        # anchored at the UNPERTURBED on-resonance threshold
        direct = margin_fixed_g2(
            190.0 * g0, kappa_c * math.exp(-h), s_v
        )
        # the handoff-check-7 substitution: scale the ratio target by
        # e^{+h} instead (exact iff G^2_th(0) prop a_c — symmetric lines)
        substituted = margin_onres_ratio(
            190.0 * math.exp(h), kappa_c * math.exp(-h), s_v
        )
        assert direct.delta_f_max_mhz == pytest.approx(
            substituted.delta_f_max_mhz, rel=1e-9
        )


# --- V9: handoff reproduction (their formulation as-is) ----------------------


def test_v9_handoff_scenario_reproduction():
    """Reproduces docs/reviews/two_linewidth_falsification_handoff.md
    §6 operating-point numbers under THEIR formulation: kc = 0.257
    (their rounded kappa_c), their O-L-approximate sizing (composite
    ~1.44/1.29 MHz, NOT 1.400), on-res-ratio normalisation, and their
    asymmetric eps-form exponent. Only the solver is this module's.
    THE SIGN FLIP (E_b < 0) IS THE GATE — if it fails, stop and report
    (plan trigger)."""
    kc = 0.257
    s_a = make_voigt_s_spin(1.40, 0.0)
    s_b = make_voigt_s_spin(0.10, 1.39 / 2.35482)  # their sizing verbatim
    s_c = make_voigt_s_spin(0.50, 1.00 / 2.35482)

    m_a = margin_onres_ratio(190.0, kc, s_a).delta_f_max_mhz
    m_b = margin_onres_ratio(190.0, kc, s_b).delta_f_max_mhz
    m_c = margin_onres_ratio(190.0, kc, s_c).delta_f_max_mhz
    assert m_a == pytest.approx(11.39, abs=5e-3)  # their (a), == closed form
    assert m_a == pytest.approx(
        0.5 * (kc + 1.40) * math.sqrt(189.0), rel=1e-9
    )
    assert m_b == pytest.approx(7.77, abs=2e-2)  # their (b): -32% headline
    assert m_c == pytest.approx(7.51, abs=2e-2)  # their (c)

    eps = 0.05

    def their_exponent(s_spin):
        margins = [
            margin_onres_ratio(
                190.0 * (1.0 + e), kc / (1.0 + e), s_spin
            ).delta_f_max_mhz
            for e in (-eps, +eps)
        ]
        return (math.log(margins[1]) - math.log(margins[0])) / (
            2.0 * math.log(1.0 + eps)
        ), margins

    e_a, margins_a = their_exponent(s_a)
    assert e_a == pytest.approx(+0.356, abs=5e-3)
    assert margins_a[0] == pytest.approx(11.191, abs=2e-2)
    assert margins_a[1] == pytest.approx(11.587, abs=2e-2)

    e_b, margins_b = their_exponent(s_b)
    assert e_b < 0.0  # THE SIGN FLIP — the falsification gate
    assert e_b == pytest.approx(-0.160, abs=5e-3)
    assert margins_b[0] == pytest.approx(7.837, abs=2e-2)
    assert margins_b[1] == pytest.approx(7.716, abs=2e-2)


# --- V10: regression pins, independent cross-checks, byte-pin ----------------

# Exact-FWHM sweep pins. UNITS: f_L / sigma_g / margins in cyclic MHz
# (FWHM convention); E dimensionless. NORMALISATIONS: "fixed" = the
# repo-consistent import-preserving fixed-G^2 anchoring
# G^2 = C0*kappa_c*kappa_s/4 = 17.10526159 (matched-unit amplitude
# rates; an algebraic import — NOT a measured coupling); "ratio" =
# G^2_th(Delta)/G^2_th(0) = 190 (handoff convention). ABSOLUTE margins
# pin the normalisation, not just shapes. Values computed by the wofz
# route and cross-checked in-session against the independent
# discrete packet-sum route (machine-precision agreement; the in-CI
# version of that cross-check is test_v10_independent_packet_sum below).
_V10_PINS = {
    # f_L: (sigma_g, m_fixed, e_fixed, m_ratio, e_ratio)
    0.05: (0.583130229, 10.45605014, -0.1618322, 8.27384366, -0.1210755),
    0.10: (0.571553834, 9.22219546, -0.1938383, 7.66984680, -0.1606463),
    0.20: (0.547813947, 8.40534831, -0.0593215, 7.14581107, -0.0578483),
    0.35: (0.510542814, 8.42621519, +0.0751757, 7.31316107, +0.0747521),
    0.50: (0.470877706, 8.77252480, +0.1587437, 7.77168199, +0.1583036),
    0.70: (0.413116728, 9.35053273, +0.2305044, 8.51598457, +0.2303447),
    1.00: (0.309776765, 10.24915175, +0.2961837, 9.72881026, +0.2962712),
    1.20: (0.217788538, 10.83077858, +0.3252378, 10.56073014, +0.3253293),
    1.40: (0.000000000, 11.39151774, +0.3474269, 11.39151774, +0.3474269),
}


def test_v10_sweep_regression_pins():
    kappa_c = _kappa_c_mhz()
    g2_imp = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    assert g2_imp == pytest.approx(17.10526159, rel=1e-9)
    assert tuple(_V10_PINS) == SWEEP_F_L_MHZ
    for f_l, (sigma_pin, mf_pin, ef_pin, mr_pin, er_pin) in _V10_PINS.items():
        sigma = voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ)
        assert sigma == pytest.approx(sigma_pin, abs=1e-8)
        s_v = make_voigt_s_spin(f_l, sigma)
        m_fixed = margin_fixed_g2(g2_imp, kappa_c, s_v)
        assert m_fixed.delta_f_max_mhz == pytest.approx(mf_pin, rel=1e-6)
        e_fixed = q_margin_exponent_numeric(
            g2_imp, kappa_c, s_v, h_log=0.02
        )
        assert e_fixed.exponent == pytest.approx(ef_pin, abs=1e-5)
        m_ratio = margin_onres_ratio(PLANNING_C0, kappa_c, s_v)
        assert m_ratio.delta_f_max_mhz == pytest.approx(mr_pin, rel=1e-6)
        e_ratio = q_margin_exponent_numeric(
            m_ratio.g2, kappa_c, s_v, h_log=0.02
        )
        assert e_ratio.exponent == pytest.approx(er_pin, abs=1e-5)
        # branch audit: single clean root branch at every pinned row
        assert m_fixed.root.n_candidates == 1
        assert m_ratio.root.n_candidates == 1
        assert not m_fixed.root.tangential_candidates
        assert not m_ratio.root.tangential_candidates


def test_v10_e_zero_sign_change_bracket():
    """The E = 0 contour exists INSIDE the swept f_L range for BOTH
    normalisations (computed, not assumed — the report bisects it:
    f_L* ~ 0.2567 fixed / ~0.2564 ratio). Committed +0.347 requires
    the f_L > f_L* branch."""
    kappa_c = _kappa_c_mhz()
    g2_imp = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    for lo_f_l, hi_f_l in ((0.20, 0.35),):
        for anchoring in ("fixed", "ratio"):
            exponents = []
            for f_l in (lo_f_l, hi_f_l):
                s_v = make_voigt_s_spin(
                    f_l, voigt_sigma_g_mhz(f_l, KAPPA_S_MHZ)
                )
                if anchoring == "fixed":
                    g2 = g2_imp
                else:
                    g2 = PLANNING_C0 * threshold_g2(0.0, kappa_c, s_v).g2_th
                exponents.append(
                    q_margin_exponent_numeric(
                        g2, kappa_c, s_v, h_log=0.02
                    ).exponent
                )
            assert exponents[0] < 0.0 < exponents[1]


def test_v10_independent_packet_sum_cross_check():
    """Amendment-D verification: the pinned margins re-verify through
    the DISCRETE packet-sum route (no wofz anywhere): the threshold at
    the pinned margin detuning must equal the normalisation's G^2
    target. The uniform-grid ensemble sits at its trapezoid-
    exponential-accuracy floor, so node AND span doubling leave the
    check at <= 1e-9 (observed ~1e-13). The equal-weight quantile-
    Gaussian flavour converges only algebraically (its tail packets
    under-resolve the a_s core off-centre) and is asserted at 1e-4 on
    the wider-f_L rows only."""
    kappa_c = _kappa_c_mhz()
    g2_imp = g2_fixed_import_preserving(PLANNING_C0, kappa_c, KAPPA_S_MHZ)
    # Tolerance floor: the 8-decimal margin pins round at ~5e-9 MHz,
    # which maps through d ln G^2/d Delta ~ 0.24/MHz to ~1e-9 relative
    # in G^2 — the check floor is the PIN rounding, not the quadrature
    # (which agrees to ~1e-13).
    for f_l in (0.05, 0.10, 0.50, 1.00):
        sigma_pin, mf_pin, _, mr_pin, _ = _V10_PINS[f_l]
        for npts, span in ((2001, 8.0), (4001, 8.0), (4001, 12.0)):
            s_d = _grid_gaussian_s_spin(sigma_pin, f_l, npts, span)
            g2_at_margin = threshold_g2(mf_pin, kappa_c, s_d).g2_th
            assert g2_at_margin == pytest.approx(g2_imp, rel=5e-8)
            g0_d = threshold_g2(0.0, kappa_c, s_d).g2_th
            g2_at_ratio_margin = threshold_g2(mr_pin, kappa_c, s_d).g2_th
            assert g2_at_ratio_margin == pytest.approx(
                PLANNING_C0 * g0_d, rel=5e-8
            )
    for f_l in (0.50, 1.00):
        sigma_pin, mf_pin, _, _, _ = _V10_PINS[f_l]
        q = (np.arange(4001) + 0.5) / 4001
        s_q = _discrete_s_spin(
            sigma_pin * ndtri(q), np.full(4001, 1.0 / 4001), f_l
        )
        g2_at_margin = threshold_g2(mf_pin, kappa_c, s_q).g2_th
        assert g2_at_margin == pytest.approx(g2_imp, rel=1e-4)


def test_v10_report_byte_pin():
    committed = (
        Path(__file__).resolve().parents[1]
        / "thermal"
        / "reports"
        / "q_margin_voigt_sensitivity.md"
    )
    assert committed.read_text(encoding="utf-8") == build_report()
