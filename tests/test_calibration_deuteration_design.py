"""Deuteration identifiability / experiment-design guards
(calibration/deuteration_design.py).

The load-bearing assertions: the study REFUSES detection language
(verbatim sentence everywhere), keeps Angus-pending unknowns swept, and
its numbers cross-pin against independent computations — the baseline
band against the committed T4 feed record, X_det against by-hand
arithmetic, the power-grid rows against the closed WLS form."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from calibration.constants import DIGITIZED_SIGMA_MHZ
from calibration.deuteration_design import (
    NON_DETECTION_SENTENCE,
    SIGMA_REL_SCOPING,
    render_report,
    run_design_study,
    to_json,
    x_det,
)

REPO = Path(__file__).resolve().parent.parent
FEED = REPO / "calibration" / "reports" / "observable_a_feed.json"
COMMITTED_MD = REPO / "calibration" / "reports" / "deuteration_design.md"
COMMITTED_JSON = REPO / "calibration" / "reports" / "deuteration_design.json"


@pytest.fixture(scope="module")
def study():
    return run_design_study()


@pytest.fixture(scope="module")
def by_name(study):
    return {s.name: s for s in study.scenarios}


class TestRefusals:
    def test_non_detection_sentence_verbatim_everywhere(self, study):
        assert NON_DETECTION_SENTENCE == (
            "No claim that deuteration is detected unless the model "
            "comparison genuinely discriminates it"
        )
        assert NON_DETECTION_SENTENCE in study.verdict
        assert NON_DETECTION_SENTENCE in render_report(study)
        assert NON_DETECTION_SENTENCE in to_json(study)

    def test_verdict_is_insufficiently_identifiable(self, study):
        assert study.verdict.startswith("INSUFFICIENTLY IDENTIFIABLE")

    def test_report_carries_non_transfer_and_swept_statements(self, study):
        text = render_report(study)
        assert "NON-TRANSFERABLE" in text
        assert "SWEPT, never fixed" in text
        assert "NOT evidence of deuteration" in text

    def test_x_det_refuses_sigma_beyond_half(self):
        with pytest.raises(ValueError):
            x_det(1.0, 2.0, 0.5)


class TestCrossPins:
    def test_baseline_band_matches_committed_t4_feed(self, by_name):
        """The baseline scenario must reproduce the committed T4 model
        ratio band exactly (same ratified grid, independent record)."""
        feed = json.loads(FEED.read_text(encoding="utf-8"))
        lo, hi = feed["t4_ratio_test"]["model_ratio_band"]
        base = by_name["baseline"]
        assert base.rho_lo_worst == pytest.approx(lo, rel=1e-9)
        assert base.rho_hi_worst == pytest.approx(hi, rel=1e-9)

    def test_x_det_closed_form_by_hand(self, study, by_name):
        base = by_name["baseline"]
        sigma_rel = study.sigma_rel_digitized
        by_hand = base.rho_hi_worst / (
            base.rho_lo_worst * (1.0 - 2.0 * sigma_rel)
        )
        assert base.x_det_at(sigma_rel) == pytest.approx(by_hand, rel=1e-12)

    def test_x_det_monotone_in_sigma(self, by_name):
        base = by_name["baseline"]
        assert base.x_det_at(0.01) < base.x_det_at(0.05) < base.x_det_at(0.20)

    def test_power_grid_row_recomputed_exact_sxx(self, study):
        """One row re-derived by hand from the EXACT endpoint-grid form
        (adversarial-review re-derivation): S_xx = ΔP²·N(N+1)/(12(N−1)),
        σ_rel(R)² = σ_point²/S_xx · (1/s_d² + 1/s_h²), both live slopes."""
        from calibration.constants import EXCITATION
        from calibration.slope_fit import fit_all

        row = next(
            r
            for r in study.power_grid_table
            if r["sigma_point_is_digitized_floor"]
            and r["target_sigma_rel"] == SIGMA_REL_SCOPING[0]
        )
        span = max(EXCITATION.powers_h14_mw) - min(EXCITATION.powers_h14_mw)
        fits = fit_all()
        inv_s2 = (
            1.0 / fits.fits["d14"].slope_mhz_per_mw ** 2
            + 1.0 / fits.fits["h14"].slope_mhz_per_mw ** 2
        )

        def sigma_rel(n):
            sxx = span**2 * n * (n + 1) / (12.0 * (n - 1))
            return math.sqrt(DIGITIZED_SIGMA_MHZ**2 / sxx * inv_s2)

        target = row["target_sigma_rel"]
        n = row["n_required"]
        assert n >= 3
        assert sigma_rel(n) <= target
        assert n == 3 or sigma_rel(n - 1) > target
        # cross-pin against the independent derivation (2026-07-20):
        # digitized floor, targets 0.05/0.02/0.01 -> N = 28/186/750
        floors = {
            r["target_sigma_rel"]: r["n_required"]
            for r in study.power_grid_table
            if r["sigma_point_is_digitized_floor"]
        }
        assert floors == {0.05: 28, 0.02: 186, 0.01: 750}

    def test_visits_at_n8_scale_as_inverse_sqrt_r(self, study):
        v = {row["visits_per_level"]: row for row in study.visits_at_n8}
        s1 = v[1]["sigma_rel_ratio_at_digitized_floor"]
        s3 = v[3]["sigma_rel_ratio_at_digitized_floor"]
        assert s3 == pytest.approx(s1 / math.sqrt(3.0), rel=1e-12)
        # absolute cross-pin vs the independent derivation: sigma_R =
        # sigma_rel * R = 0.115 / 0.0663 at r = 1 / 3
        assert s1 * study.measured_ratio == pytest.approx(0.115, abs=0.001)
        assert s3 * study.measured_ratio == pytest.approx(0.0663, abs=0.001)

    def test_aicc_thresholds_at_n8(self, study):
        th = study.aicc_thresholds_n8
        assert th["n"] == 8
        assert th["quadratic_dchi2"] == pytest.approx(9.6, abs=0.01)
        assert th["piecewise_searched_breakpoint_dchi2"] == pytest.approx(
            18.93, abs=0.01
        )

    def test_suppression_is_not_reciprocal_of_enhancement(self, study):
        from calibration.deuteration_design import (
            x_det,
            x_det_suppression,
        )

        lo, hi, sr = 0.584, 2.329, 0.098
        assert x_det_suppression(lo, hi, sr) == pytest.approx(
            hi * (1 + 2 * sr) / lo
        )
        assert x_det_suppression(lo, hi, sr) != pytest.approx(x_det(lo, hi, sr))

    def test_x_compat_matches_independent_derivation(self, by_name, study):
        from calibration.deuteration_design import x_compatibility_range

        base = by_name["baseline"]
        lo, hi = x_compatibility_range(
            base.rho_lo_worst,
            base.rho_hi_worst,
            study.measured_ratio,
            study.measured_sigma,
        )
        # independent-derivation values: [0.463, 2.751]
        assert lo == pytest.approx(0.463, abs=0.001)
        assert hi == pytest.approx(2.751, abs=0.001)


class TestStructure:
    def test_pinning_never_widens(self, study, by_name):
        base_w = by_name["baseline"].width_worst
        for s in study.scenarios:
            assert s.width_best <= s.width_worst + 1e-12, s.name
            if s.name.startswith(("pin_", "narrow_", "all_")):
                assert s.width_worst <= base_w + 1e-9, (
                    f"{s.name}: a measurement cannot widen the band"
                )

    def test_glue_envelope_ordering(self, by_name):
        """Admitting mounting asymmetry only ever widens; constraining
        it narrows monotonically back toward the shared-h baseline."""
        assert (
            by_name["m0_unconstrained_mounting"].width_worst
            > by_name["m0_mounting_within_1_decade"].width_worst
            > by_name["m0_mounting_within_half_decade"].width_worst
            > by_name["baseline"].width_worst
        )

    def test_matched_glue_ordering(self, study):
        assert (
            study.matched_glue_full_width
            > study.matched_glue_one_decade_width
            > study.matched_glue_half_decade_width
            > 1.0
        )

    def test_mounting_is_the_binding_limiter(self, study, by_name):
        """The honest M0 envelope with unconstrained mounting dwarfs
        every metadata-pin scenario — the study's design conclusion."""
        m0 = by_name["m0_unconstrained_mounting"].width_worst
        for s in study.scenarios:
            if s.name.startswith(("pin_", "narrow_", "all_")) or s.name == "baseline":
                assert m0 > 5.0 * s.width_worst

    def test_report_states_remount_over_second_pair(self, study):
        text = render_report(study)
        assert "MORE informative than an additional unmatched pair" in text

    def test_d6_rider_present(self, study):
        assert any(
            "D6" in row["d6_note"] or ">= 8" in row["d6_note"]
            for row in study.power_grid_table
        )
        assert "ΔAICc ≥ 4" in render_report(study)


class TestCommittedArtifacts:
    def test_committed_report_regenerates_identically(self, study):
        committed = COMMITTED_MD.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        assert render_report(study) == committed

    def test_committed_json_regenerates_identically(self, study):
        committed = COMMITTED_JSON.read_text(encoding="utf-8").replace(
            "\r\n", "\n"
        )
        assert to_json(study) == committed

    def test_json_schema_keys(self):
        payload = json.loads(COMMITTED_JSON.read_text(encoding="utf-8"))
        assert payload["workstream"] == "deuteration-identifiability-design"
        assert payload["non_detection_sentence"] == NON_DETECTION_SENTENCE
        assert {"measured", "scenarios", "matched_sample_analysis", "power_grid"} <= set(
            payload
        )
        for s in payload["scenarios"]:
            assert {"name", "width_best", "width_worst", "x_det_at_digitized_sigma"} <= set(s)
