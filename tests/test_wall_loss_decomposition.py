"""SPEC §4 wall-loss decomposition: cancellation-spanning synthetic
fixtures + invariants.

The synthetic fixtures span both ends of the SPEC §6 confinement
trend so the linear error propagation is checked against the regime
it has to flag, not just the comfortable middle:

  (a) walls-dominate: Q_total << Q_diel. Easy reciprocal
      subtraction; sigma_Q_wall is small, `below_resolution` False.
  (b) walls-negligible (Breeze regime): Q_total ~ Q_diel. The
      cancellation-prone case; sigma_Q_wall blows up via the
      Q_wall^2 / Q_total^2 amplification factor, and the
      decomposition MUST flag `below_resolution = True` so the
      magnitude is read as "walls are negligible here" rather than
      a confident finite value (SPEC §6).
  (c) Booth mid-trend regime: Q_total = 6,980, Q_diel = 1/tan_delta
      ~ 9,091, so Q_wall ~ 30,000 and wall fraction ~ 23%. With
      mesh-convergence-scale sigmas this is resolved.

The Booth Table 8 numerical gate itself is deferred (see
`tests/test_wall_loss_gate.py`); these tests pin the protocol.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from cavity.extraction import ExtractionResult
from cavity.provenance import WALL_LOSS_THRESHOLDS, WallLossThresholds
from cavity.validation import (
    WallLossDecomposition,
    decompose_wall_loss,
)


def _make_result(q: float, f_real: float = 1.45e9) -> ExtractionResult:
    """Build a minimal ExtractionResult carrying just (q, f_hz) for the
    decomposition layer. wall_loss only reads `q`; the rest are
    populated with physically plausible dummies so the dataclass
    constructs without complaint.
    """
    f_double_prime = f_real / (2.0 * q)
    return ExtractionResult(
        f_hz=f_real,
        complex_eigenfrequency_hz=complex(f_real, f_double_prime),
        q=q,
        q_emw_cross_check=None,
        v_mode_global_m3=0.4e-6,
        v_mode_local_m3=0.4e-6,
        p_e=0.9,
        f_m_global=3.4e7,
        f_m_local=3.4e7,
    )


class TestCancellationSpanningFixtures:
    """The two regime ends of SPEC §6 + Booth mid-trend."""

    def test_walls_dominate_clean_subtraction(self):
        """Q_total=100, Q_diel=10,000. Q_wall ~ 101; sigma small;
        resolved.
        """
        imp = _make_result(q=100.0)
        pec = _make_result(q=10_000.0)
        decomp = decompose_wall_loss(
            imp, pec,
            sigma_q_impedance=0.1,
            sigma_q_pec=10.0,
        )
        expected_q_wall = 1.0 / (1.0 / 100.0 - 1.0 / 10_000.0)
        assert decomp.q_wall == pytest.approx(expected_q_wall, rel=1e-12)
        assert decomp.q_total == 100.0
        assert decomp.q_diel == 10_000.0
        assert decomp.below_resolution is False
        rel_unc = decomp.sigma_q_wall / decomp.q_wall
        assert rel_unc < WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty
        assert decomp.wall_fraction == pytest.approx(0.99, rel=1e-2)

    def test_breeze_regime_walls_negligible_flagged(self):
        """Q_total=9,990, Q_diel=10,000, sigma=100 (1% rel).
        Q_wall ~ 1e6, but rel uncertainty ~ 1.4 (140%): flagged.
        """
        imp = _make_result(q=9_990.0)
        pec = _make_result(q=10_000.0)
        decomp = decompose_wall_loss(
            imp, pec,
            sigma_q_impedance=100.0,
            sigma_q_pec=100.0,
        )
        assert decomp.q_wall > 5.0e5
        assert decomp.below_resolution is True
        rel_unc = decomp.sigma_q_wall / decomp.q_wall
        assert rel_unc > WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty
        assert rel_unc > 1.0

    def test_booth_regime_mid_trend_resolved(self):
        """Q_total=6,980, Q_diel=9,091 (~1/1.1e-4). Q_wall ~ 30,060,
        wall fraction ~ 23.2%; with 0.1%-rel mesh sigmas, resolved.
        """
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        decomp = decompose_wall_loss(
            imp, pec,
            sigma_q_impedance=7.0,
            sigma_q_pec=9.0,
        )
        expected_q_wall = 1.0 / (1.0 / 6_980.0 - 1.0 / 9_091.0)
        assert decomp.q_wall == pytest.approx(expected_q_wall, rel=1e-12)
        assert 0.22 < decomp.wall_fraction < 0.24
        assert decomp.below_resolution is False


class TestErrorPropagationArithmetic:
    """The linear formula sigma_Q_wall = sigma_inv_wall * Q_wall^2
    is the §4 contract. Test it against a hand-computed value.
    """

    def test_linear_propagation_matches_hand_calc(self):
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        s_imp = 7.0
        s_pec = 9.0
        decomp = decompose_wall_loss(imp, pec, s_imp, s_pec)

        # Hand-rolled formula.
        inv_qt = 1.0 / 6_980.0
        inv_qd = 1.0 / 9_091.0
        inv_qw = inv_qt - inv_qd
        qw = 1.0 / inv_qw
        s_inv_qt = s_imp / 6_980.0 ** 2
        s_inv_qd = s_pec / 9_091.0 ** 2
        s_inv_qw = (s_inv_qt ** 2 + s_inv_qd ** 2) ** 0.5
        s_qw_expected = s_inv_qw * qw ** 2

        assert decomp.sigma_q_wall == pytest.approx(s_qw_expected, rel=1e-12)

    def test_zero_sigma_gives_zero_uncertainty(self):
        """If both inputs are exact, sigma_Q_wall == 0 and the case
        is resolved trivially.
        """
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        decomp = decompose_wall_loss(
            imp, pec,
            sigma_q_impedance=0.0,
            sigma_q_pec=0.0,
        )
        assert decomp.sigma_q_wall == 0.0
        assert decomp.below_resolution is False

    def test_amplification_factor_scales_with_q_wall_squared(self):
        """sigma_Q_wall / sigma_Q_input should scale ~ Q_wall^2 / Q^2,
        the textbook propagation factor. Use a clean-regime case so
        the cancellation isn't dominant.
        """
        imp_1 = _make_result(q=1_000.0)
        pec_1 = _make_result(q=10_000.0)
        decomp_1 = decompose_wall_loss(
            imp_1, pec_1, sigma_q_impedance=1.0, sigma_q_pec=0.0,
        )
        # Q_wall = 1/(1e-3 - 1e-4) = 1111.11
        # sigma_Q_wall = 1.0 * (Q_wall/Q_total)^2 = (1111.11/1000)^2
        amp_expected = (decomp_1.q_wall / decomp_1.q_total) ** 2
        assert decomp_1.sigma_q_wall == pytest.approx(amp_expected, rel=1e-12)


class TestPhysicsInvariants:
    """SPEC §4: PEC removes wall loss in a closed cavity, so
    Q_diel (PEC) MUST exceed Q_total (Impedance). The decomposition
    refuses to silently produce a negative Q_wall.
    """

    def test_strict_inequality_equal_q_rejected(self):
        imp = _make_result(q=10_000.0)
        pec = _make_result(q=10_000.0)
        with pytest.raises(ValueError, match=r"Q_diel.*must be > "):
            decompose_wall_loss(imp, pec, 1.0, 1.0)

    def test_inverted_results_rejected_no_silent_negative_q_wall(self):
        """A swap of Impedance and PEC results must fail the strict
        inequality instead of returning a negative Q_wall.
        """
        imp = _make_result(q=10_000.0)
        pec = _make_result(q=6_980.0)
        with pytest.raises(ValueError, match=r"Q_diel.*must be > "):
            decompose_wall_loss(imp, pec, 10.0, 7.0)

    def test_non_positive_q_total_rejected(self):
        good = _make_result(q=9_091.0)
        bad = replace(_make_result(q=6_980.0), q=-5.0)
        with pytest.raises(ValueError, match="must be positive"):
            decompose_wall_loss(bad, good, 1.0, 1.0)

    def test_non_positive_q_diel_rejected(self):
        good = _make_result(q=6_980.0)
        bad = replace(_make_result(q=9_091.0), q=0.0)
        with pytest.raises(ValueError, match="must be positive"):
            decompose_wall_loss(good, bad, 1.0, 1.0)


class TestRequiredInputContract:
    """SPEC §4 + repo convention: input Q uncertainties are required;
    no silent default. Forces the caller to source them honestly from
    §2's mesh-convergence residual.
    """

    def test_sigmas_are_positional_required_no_default(self):
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        with pytest.raises(TypeError):
            decompose_wall_loss(imp, pec)
        with pytest.raises(TypeError):
            decompose_wall_loss(imp, pec, sigma_q_impedance=7.0)
        with pytest.raises(TypeError):
            decompose_wall_loss(imp, pec, sigma_q_pec=9.0)

    def test_negative_sigma_impedance_rejected(self):
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        with pytest.raises(ValueError, match="non-negative"):
            decompose_wall_loss(imp, pec, -1.0, 1.0)

    def test_negative_sigma_pec_rejected(self):
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        with pytest.raises(ValueError, match="non-negative"):
            decompose_wall_loss(imp, pec, 1.0, -1.0)


class TestThresholdSourcing:
    """The below-resolution threshold MUST come from
    `cavity.provenance.WALL_LOSS_THRESHOLDS`, not a literal in
    wall_loss.py. Single-source discipline (same as TARGETS,
    EXTRACTION_TOL, F_M_BENCHMARK).
    """

    def test_threshold_lives_in_provenance(self):
        assert hasattr(WALL_LOSS_THRESHOLDS, "below_resolution_rel_uncertainty")
        assert 0.0 < WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty < 1.0
        assert isinstance(WALL_LOSS_THRESHOLDS.reason, str)
        assert len(WALL_LOSS_THRESHOLDS.reason) > 0

    def test_threshold_change_flips_below_resolution_flag(self, monkeypatch):
        """Reading the threshold freshly at call time (not freezing
        it at module import) is what makes it a knob. Verify by
        tightening the threshold below the observed rel uncertainty
        and re-running.
        """
        imp = _make_result(q=8_000.0)
        pec = _make_result(q=10_000.0)
        s_imp, s_pec = 200.0, 200.0
        decomp_default = decompose_wall_loss(imp, pec, s_imp, s_pec)
        rel_unc = decomp_default.sigma_q_wall / decomp_default.q_wall

        assert rel_unc < (
            WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty
        )
        assert decomp_default.below_resolution is False

        # Tighten the threshold below rel_unc; flag must flip.
        tight = WallLossThresholds(
            below_resolution_rel_uncertainty=rel_unc * 0.5,
            reason="test override",
        )
        monkeypatch.setattr(
            "cavity.validation.wall_loss.WALL_LOSS_THRESHOLDS", tight,
        )
        decomp_tight = decompose_wall_loss(imp, pec, s_imp, s_pec)
        assert decomp_tight.below_resolution is True
        # Magnitudes unchanged: only the classification moved.
        assert decomp_tight.q_wall == decomp_default.q_wall
        assert decomp_tight.sigma_q_wall == decomp_default.sigma_q_wall


class TestReturnContract:
    def test_returns_decomposition_with_all_fields_populated(self):
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        decomp = decompose_wall_loss(imp, pec, 7.0, 9.0)
        assert isinstance(decomp, WallLossDecomposition)
        assert decomp.q_total == 6_980.0
        assert decomp.q_diel == 9_091.0
        assert decomp.q_wall > 0
        assert decomp.sigma_q_wall >= 0
        assert 0 < decomp.wall_fraction < 1
        assert isinstance(decomp.below_resolution, bool)

    def test_wall_fraction_definition(self):
        """wall_fraction = Q_total / Q_wall = (1/Q_wall)/(1/Q_total).
        Booth-regime check.
        """
        imp = _make_result(q=6_980.0)
        pec = _make_result(q=9_091.0)
        decomp = decompose_wall_loss(imp, pec, 7.0, 9.0)
        assert decomp.wall_fraction == pytest.approx(
            decomp.q_total / decomp.q_wall, rel=1e-12
        )
