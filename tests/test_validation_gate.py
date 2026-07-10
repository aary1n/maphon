"""SPEC §5 gate: judgment logic on synthetic payloads (no COMSOL).

Every row's pass AND fail branch is exercised here on synthetic
inputs; the live tier (tests/test_gate_comsol.py, requires_comsol)
runs the identical code path on real solves. The Booth Table 8
numerical gate itself stays strict-xfail in test_wall_loss_gate.py —
nothing here weakens it: a synthetic pass of the wall-loss row is a
check of the JUDGMENT, not of the physics.
"""

from __future__ import annotations

import pytest

from cavity.extraction import ExtractionResult
from cavity.provenance import (
    EXTRACTION_TOL,
    GATE_ROWS,
    GEOM,
    STO,
    TARGET,
    TARGETS,
)
from cavity.provenance.gate_targets import BOOTH_TWO_POINT_REL_TOL
from cavity.validation import (
    BoothPayload,
    CheckStatus,
    ConfinementPayload,
    ConfinementPoint,
    EmptyCavityPayload,
    LiveComsolProvider,
    PecLossyPayload,
    StaticProvider,
    Unavailable,
    WallLossPayload,
    decompose_wall_loss,
    f_te_mnp,
    run_gate,
)

ROW_IDS = (
    "analytic_benchmark",
    "f",
    "booth_two_point",
    "confinement_trend",
    "wall_loss_split",
    "f_m",
)

F_TE011 = f_te_mnp(0, 1, 1, GEOM.box_radius_m, GEOM.box_height_m)
PEC_LOSSY_TOL = EXTRACTION_TOL.q_pec_lossy_rel_tol
Q_PEC_EXACT = 1.0 / (0.9 * STO.tan_delta)  # p_e = 0.9 throughout


def make_extraction(
    *,
    f_hz: float = 1.4502e9,
    q: float = 6_980.0,
    p_e: float = 0.9,
    v_mode_global_m3: float = 0.409e-6,
    v_mode_local_m3: float = 0.35e-6,
    f_m_global: float = 3.4e7,
    f_m_local: float = 3.9e7,
) -> ExtractionResult:
    """Synthetic §3 extraction; Q consistent with f'/(2 f'')."""
    return ExtractionResult(
        f_hz=f_hz,
        complex_eigenfrequency_hz=complex(f_hz, f_hz / (2.0 * q)),
        q=q,
        q_emw_cross_check=None,
        v_mode_global_m3=v_mode_global_m3,
        v_mode_local_m3=v_mode_local_m3,
        p_e=p_e,
        f_m_global=f_m_global,
        f_m_local=f_m_local,
    )


def empty_cavity_payload(rel_offset: float = 5.0e-4) -> EmptyCavityPayload:
    return EmptyCavityPayload(
        spectrum_f_real_hz=(
            F_TE011 * (1.0 + rel_offset),
            F_TE011 * 1.3,
            F_TE011 * 0.8,
        ),
        box_radius_m=GEOM.box_radius_m,
        box_height_m=GEOM.box_height_m,
    )


def pec_lossy_payload(rel_error: float = 1.0e-3) -> PecLossyPayload:
    return PecLossyPayload(
        extraction=make_extraction(
            q=Q_PEC_EXACT * (1.0 + rel_error), p_e=0.9
        ),
        tan_delta=STO.tan_delta,
    )


def booth_payload(
    q: float = 6_980.0,
    v_mode_global_m3: float = 0.409e-6,
    f_hz: float = 1.4502e9,
    f_m_global: float = 3.4e7,
    epsilon_r_real: float | None = TARGETS.booth.epsilon_r_real,
) -> BoothPayload:
    return BoothPayload(
        extraction=make_extraction(
            f_hz=f_hz,
            q=q,
            v_mode_global_m3=v_mode_global_m3,
            f_m_global=f_m_global,
        ),
        epsilon_r_real=epsilon_r_real,
    )


def confinement_payload(*points: tuple[float, float]) -> ConfinementPayload:
    return ConfinementPayload(
        points=tuple(ConfinementPoint(v, q) for v, q in points)
    )


def wall_loss_payload(
    q_total: float = 6_980.0, q_diel: float = 9_300.0
) -> WallLossPayload:
    # Reuse the real §4 decomposition — the payload is its output.
    return WallLossPayload(
        decomposition=decompose_wall_loss(
            impedance_result=make_extraction(q=q_total),
            pec_result=make_extraction(q=q_diel),
            sigma_q_impedance=20.0,
            sigma_q_pec=20.0,
        )
    )


def full_pass_provider() -> StaticProvider:
    return StaticProvider(
        empty_cavity_payload=empty_cavity_payload(),
        pec_lossy_payload=pec_lossy_payload(),
        booth_payload=booth_payload(),
        confinement_payload=confinement_payload(
            (0.409e-6, 6_980.0), (0.30e-6, 8_500.0), (0.21e-6, 9_800.0)
        ),
        wall_loss_payload=wall_loss_payload(),
    )


def rows_by_id(report):
    return {row.row_id: row for row in report.rows}


def check_by_name(report, name):
    for row in report.rows:
        for check in row.checks:
            if check.name == name:
                return check
    raise KeyError(name)


class TestGateConfig:
    """gate_targets: verbatim SPEC rows, single-sourced windows."""

    def test_six_rows_in_spec_order(self):
        assert tuple(r.row_id for r in GATE_ROWS) == ROW_IDS

    def test_row_text_verbatim(self):
        by_id = {r.row_id: r for r in GATE_ROWS}
        assert by_id["analytic_benchmark"].check_text == (
            "Analytic benchmark passes"
        )
        assert by_id["analytic_benchmark"].target_text == (
            "empty-cavity TE011 < 0.1% error"
        )
        assert by_id["f"].target_text == "1.45 GHz, ≥4 s.f."
        assert by_id["booth_two_point"].source_text == (
            "Booth Table 8 + App. A"
        )
        assert by_id["wall_loss_split"].target_text == (
            "Q_diel ≈ 9–10k, wall fraction ~23–27%"
        )
        assert by_id["f_m"].target_text == "order 10⁷ via §3 formula"
        assert by_id["confinement_trend"].source_text == "Breeze Table 1"

    def test_windows_reference_constants_not_retyped(self):
        checks = {
            c.check_id: c for r in GATE_ROWS for c in r.checks
        }
        assert checks["analytic_benchmark/te011"].window.hi == (
            TARGETS.empty_cavity_rel_error_max
        )
        assert checks["analytic_benchmark/pec_lossy_q"].window.hi == (
            EXTRACTION_TOL.q_pec_lossy_rel_tol
        )
        assert checks["f/f_at_booth_geometry"].target_value == (
            TARGET.f_design_hz
        )
        assert checks["booth_two_point/q"].window.lo == pytest.approx(
            TARGETS.booth.q_factor * (1 - BOOTH_TWO_POINT_REL_TOL)
        )
        assert checks["booth_two_point/v_mode"].target_value == (
            TARGETS.booth.v_mode_m3
        )
        assert checks["wall_loss_split/q_diel"].window.lo == (
            TARGETS.q_diel_lo
        )
        assert checks["wall_loss_split/q_diel"].window.hi == (
            TARGETS.q_diel_hi
        )
        assert checks["wall_loss_split/wall_fraction"].window.lo == (
            TARGETS.wall_loss_fraction_lo
        )
        assert checks["wall_loss_split/wall_fraction"].window.hi == (
            TARGETS.wall_loss_fraction_hi
        )

    def test_every_check_carries_rationale_and_provenance(self):
        for row in GATE_ROWS:
            assert row.requires_comsol
            for check in row.checks:
                assert check.tolerance_rationale.strip()
                assert check.provenance.strip()

    def test_f_row_rationale_scope_clauses(self):
        f_check = next(
            c
            for r in GATE_ROWS
            for c in r.checks
            if c.check_id == "f/f_at_booth_geometry"
        )
        assert "presupposes a converged f" in f_check.tolerance_rationale
        assert "eps_r" in f_check.tolerance_rationale
        assert (
            "not a material-uncertainty tolerance"
            in f_check.tolerance_rationale
        )


class TestDeferredGate:
    """An empty provider yields all six rows, all deferred."""

    def test_all_rows_present_and_deferred(self):
        report = run_gate(StaticProvider())
        assert tuple(r.row_id for r in report.rows) == ROW_IDS
        for row in report.rows:
            assert row.status is CheckStatus.DEFERRED
            for check in row.checks:
                assert check.status is CheckStatus.DEFERRED
                assert check.measured is None
                assert check.margin is None
                assert "deferred:" in check.notes
        assert not report.phase1_complete
        assert report.n_deferred == 6
        assert report.n_pass == report.n_fail == 0

    def test_deferred_notes_carry_provider_reason_and_blocker(self):
        reason = "no cached walls-on Booth-geometry record supplied"
        provider = StaticProvider(booth_payload=Unavailable(reason))
        report = run_gate(provider)
        check = check_by_name(report, "booth_two_point/q")
        assert reason in check.notes
        # gap #1 CLOSED 2026-07-10 (geometry recovery,
        # refs/booth_geometry_recovery.md): the Booth rows no longer
        # carry a blocked_on ride-along — a deferred note is just the
        # provider's reason now.
        assert "gap #1" not in check.notes
        assert "row blocked on" not in check.notes
        # the one remaining blocked row still rides its blocker along
        conf = check_by_name(report, "confinement_trend/monotonic")
        assert "row blocked on" in conf.notes
        assert "confinement sweep" in conf.notes

    def test_status_serialises_to_required_literal(self):
        report = run_gate(StaticProvider())
        assert report.rows[0].status.value == "deferred_requires_comsol"


class TestAnalyticBenchmarkRow:
    def test_te011_pass_with_margin(self):
        report = run_gate(
            StaticProvider(empty_cavity_payload=empty_cavity_payload(5e-4))
        )
        check = check_by_name(report, "analytic_benchmark/te011")
        assert check.status is CheckStatus.PASS
        assert check.measured == pytest.approx(5e-4, rel=1e-6)
        assert check.margin == pytest.approx(0.5, rel=1e-6)
        assert check.inputs["f_analytic_te011_hz"] == pytest.approx(F_TE011)

    def test_te011_fail_outside_tenth_percent(self):
        report = run_gate(
            StaticProvider(empty_cavity_payload=empty_cavity_payload(2e-3))
        )
        check = check_by_name(report, "analytic_benchmark/te011")
        assert check.status is CheckStatus.FAIL
        assert check.margin < 0.0

    def test_pec_lossy_pass_margin_is_headroom(self):
        report = run_gate(
            StaticProvider(pec_lossy_payload=pec_lossy_payload(1e-3))
        )
        check = check_by_name(report, "analytic_benchmark/pec_lossy_q")
        assert check.status is CheckStatus.PASS
        assert check.measured == pytest.approx(1e-3, rel=1e-6)
        assert check.margin == pytest.approx(
            (PEC_LOSSY_TOL - 1e-3) / PEC_LOSSY_TOL, rel=1e-6
        )
        assert "numerical-residual headroom" in check.notes
        assert "not a statement of Q-convention correctness" in check.notes

    def test_pec_lossy_threshold_is_the_guard_constant(self):
        # 0.9x the guard tolerance passes; 1.1x fails — same constant,
        # no forked threshold.
        passing = run_gate(
            StaticProvider(
                pec_lossy_payload=pec_lossy_payload(0.9 * PEC_LOSSY_TOL)
            )
        )
        failing = run_gate(
            StaticProvider(
                pec_lossy_payload=pec_lossy_payload(1.1 * PEC_LOSSY_TOL)
            )
        )
        assert (
            check_by_name(passing, "analytic_benchmark/pec_lossy_q").status
            is CheckStatus.PASS
        )
        fail_check = check_by_name(
            failing, "analytic_benchmark/pec_lossy_q"
        )
        assert fail_check.status is CheckStatus.FAIL
        assert "assert_pec_lossy_q_consistency raised" in fail_check.notes

    def test_row_deferred_when_only_te011_supplied(self):
        # A half-supplied benchmark row must not read as green.
        report = run_gate(
            StaticProvider(empty_cavity_payload=empty_cavity_payload())
        )
        row = rows_by_id(report)["analytic_benchmark"]
        assert row.status is CheckStatus.DEFERRED


class TestFRow:
    def test_pass_inside_half_megahertz(self):
        report = run_gate(
            StaticProvider(booth_payload=booth_payload(f_hz=1.4502e9))
        )
        check = check_by_name(report, "f/f_at_booth_geometry")
        assert check.status is CheckStatus.PASS
        assert check.margin == pytest.approx(0.6, rel=1e-9)

    def test_fail_outside_window(self):
        report = run_gate(
            StaticProvider(booth_payload=booth_payload(f_hz=1.4506e9))
        )
        check = check_by_name(report, "f/f_at_booth_geometry")
        assert check.status is CheckStatus.FAIL
        assert check.margin < 0.0


class TestBoothTwoPointRow:
    def test_pass_at_table_8_values(self):
        report = run_gate(StaticProvider(booth_payload=booth_payload()))
        row = rows_by_id(report)["booth_two_point"]
        assert row.status is CheckStatus.PASS
        q_check = check_by_name(report, "booth_two_point/q")
        assert q_check.margin == pytest.approx(1.0, rel=1e-9)

    def test_q_outside_one_percent_fails(self):
        report = run_gate(
            StaticProvider(booth_payload=booth_payload(q=7_200.0))
        )
        assert (
            check_by_name(report, "booth_two_point/q").status
            is CheckStatus.FAIL
        )

    def test_v_mode_judged_on_global_variant(self):
        report = run_gate(
            StaticProvider(
                booth_payload=booth_payload(v_mode_global_m3=0.5e-6)
            )
        )
        v_check = check_by_name(report, "booth_two_point/v_mode")
        assert v_check.status is CheckStatus.FAIL
        assert v_check.inputs["v_mode_global_m3"] == pytest.approx(0.5e-6)
        assert "v_mode_local_m3" in v_check.inputs

    def test_material_mismatch_fails_all_booth_anchored_checks(self):
        # In-window numbers at the WRONG eps_r must not pass: pairing
        # a target with the other paper's eps_r chases a phantom
        # ~14 MHz shift (provenance/constants.py).
        report = run_gate(
            StaticProvider(
                booth_payload=booth_payload(epsilon_r_real=318.0)
            )
        )
        for name in (
            "f/f_at_booth_geometry",
            "booth_two_point/q",
            "booth_two_point/v_mode",
            "f_m/order_of_magnitude",
        ):
            check = check_by_name(report, name)
            assert check.status is CheckStatus.FAIL
            assert "material mismatch" in check.notes


class TestConfinementTrendRow:
    def test_monotone_trend_reaching_breeze_point_passes(self):
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.30e-6, 8_500.0),
                    (0.21e-6, 9_800.0),
                )
            )
        )
        assert (
            rows_by_id(report)["confinement_trend"].status
            is CheckStatus.PASS
        )

    def test_non_monotone_fails(self):
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.30e-6, 9_900.0),
                    (0.21e-6, 9_800.0),
                )
            )
        )
        assert (
            check_by_name(report, "confinement_trend/monotonic").status
            is CheckStatus.FAIL
        )

    def test_two_points_are_not_a_trend(self):
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0), (0.21e-6, 9_800.0)
                )
            )
        )
        row = rows_by_id(report)["confinement_trend"]
        assert row.status is CheckStatus.FAIL
        assert any(
            "not two unrelated points" in c.notes for c in row.checks
        )

    def test_sweep_not_reaching_breeze_point_fails_endpoint(self):
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.35e-6, 8_000.0),
                    (0.30e-6, 9_500.0),
                )
            )
        )
        check = check_by_name(report, "confinement_trend/endpoint_q")
        assert check.status is CheckStatus.FAIL
        assert "did not reach the Breeze confinement point" in check.notes

    def test_endpoint_q_below_window_fails(self):
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.30e-6, 7_500.0),
                    (0.21e-6, 8_500.0),
                )
            )
        )
        assert (
            check_by_name(report, "confinement_trend/endpoint_q").status
            is CheckStatus.FAIL
        )


class TestWallLossRow:
    def test_pass_inside_section_4_windows(self):
        report = run_gate(
            StaticProvider(wall_loss_payload=wall_loss_payload())
        )
        row = rows_by_id(report)["wall_loss_split"]
        assert row.status is CheckStatus.PASS
        f_check = check_by_name(report, "wall_loss_split/wall_fraction")
        assert f_check.measured == pytest.approx(0.2494, abs=1e-3)

    def test_q_diel_outside_window_fails(self):
        report = run_gate(
            StaticProvider(
                wall_loss_payload=wall_loss_payload(q_diel=12_000.0)
            )
        )
        assert (
            check_by_name(report, "wall_loss_split/q_diel").status
            is CheckStatus.FAIL
        )

    def test_below_resolution_fails_wall_fraction(self):
        from cavity.validation import WallLossDecomposition

        payload = WallLossPayload(
            decomposition=WallLossDecomposition(
                q_total=6_980.0,
                q_diel=9_300.0,
                q_wall=27_975.0,
                sigma_q_wall=20_000.0,
                wall_fraction=0.25,
                below_resolution=True,
            )
        )
        report = run_gate(StaticProvider(wall_loss_payload=payload))
        check = check_by_name(report, "wall_loss_split/wall_fraction")
        assert check.status is CheckStatus.FAIL
        assert "below_resolution" in check.notes


class TestFmRow:
    def test_order_1e7_passes(self):
        report = run_gate(
            StaticProvider(booth_payload=booth_payload(f_m_global=3.4e7))
        )
        assert (
            check_by_name(report, "f_m/order_of_magnitude").status
            is CheckStatus.PASS
        )

    @pytest.mark.parametrize("f_m", [5.0e6, 2.0e8])
    def test_wrong_order_fails(self, f_m):
        report = run_gate(
            StaticProvider(booth_payload=booth_payload(f_m_global=f_m))
        )
        assert (
            check_by_name(report, "f_m/order_of_magnitude").status
            is CheckStatus.FAIL
        )


class TestWindowEdges:
    """Margin sign flips at every window edge, pec-boundary style
    (0.9x/1.1x of the tolerance, or ±0.1 half-widths for fixed
    windows). Pins the gate_targets windows and the margin arithmetic;
    gate logic and windows themselves are unchanged by this class.

    The f row's edge pair lives in TestFRow (already just-outside with
    margin-sign assertions).
    """

    @pytest.mark.parametrize("side", [+1, -1])
    def test_booth_q_edge(self, side):
        tol = BOOTH_TWO_POINT_REL_TOL
        target = TARGETS.booth.q_factor
        inside = run_gate(
            StaticProvider(
                booth_payload=booth_payload(
                    q=target * (1 + side * 0.9 * tol)
                )
            )
        )
        outside = run_gate(
            StaticProvider(
                booth_payload=booth_payload(
                    q=target * (1 + side * 1.1 * tol)
                )
            )
        )
        c_in = check_by_name(inside, "booth_two_point/q")
        c_out = check_by_name(outside, "booth_two_point/q")
        assert c_in.status is CheckStatus.PASS
        assert c_in.margin == pytest.approx(0.1, rel=1e-6)
        assert c_out.status is CheckStatus.FAIL
        assert c_out.margin == pytest.approx(-0.1, rel=1e-6)

    @pytest.mark.parametrize("side", [+1, -1])
    def test_booth_v_mode_edge(self, side):
        tol = BOOTH_TWO_POINT_REL_TOL
        target = TARGETS.booth.v_mode_m3
        inside = run_gate(
            StaticProvider(
                booth_payload=booth_payload(
                    v_mode_global_m3=target * (1 + side * 0.9 * tol)
                )
            )
        )
        outside = run_gate(
            StaticProvider(
                booth_payload=booth_payload(
                    v_mode_global_m3=target * (1 + side * 1.1 * tol)
                )
            )
        )
        c_in = check_by_name(inside, "booth_two_point/v_mode")
        c_out = check_by_name(outside, "booth_two_point/v_mode")
        assert c_in.status is CheckStatus.PASS
        assert c_in.margin == pytest.approx(0.1, rel=1e-6)
        assert c_out.status is CheckStatus.FAIL
        assert c_out.margin == pytest.approx(-0.1, rel=1e-6)

    def test_confinement_endpoint_edge(self):
        # Window [9,000, 10,500], half-width 750: lo ± 0.1 half-widths.
        # Trend stays monotone and reaches the Breeze point in both, so
        # the endpoint window is the only discriminant.
        inside = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.30e-6, 8_000.0),
                    (0.21e-6, 9_075.0),
                )
            )
        )
        outside = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.30e-6, 8_000.0),
                    (0.21e-6, 8_925.0),
                )
            )
        )
        for report in (inside, outside):
            assert (
                check_by_name(report, "confinement_trend/monotonic").status
                is CheckStatus.PASS
            )
        c_in = check_by_name(inside, "confinement_trend/endpoint_q")
        c_out = check_by_name(outside, "confinement_trend/endpoint_q")
        assert c_in.status is CheckStatus.PASS
        assert c_in.margin == pytest.approx(0.1, rel=1e-6)
        assert c_out.status is CheckStatus.FAIL
        assert c_out.margin == pytest.approx(-0.1, rel=1e-6)

    def test_q_diel_edge(self):
        # Window [9,000, 10,000], half-width 500: hi ± 0.1 half-widths.
        # Judged at check level — the coupled wall_fraction moves too
        # and is out of window at these q_diel; that must not leak into
        # the q_diel verdict.
        inside = run_gate(
            StaticProvider(wall_loss_payload=wall_loss_payload(q_diel=9_950.0))
        )
        outside = run_gate(
            StaticProvider(wall_loss_payload=wall_loss_payload(q_diel=10_050.0))
        )
        c_in = check_by_name(inside, "wall_loss_split/q_diel")
        c_out = check_by_name(outside, "wall_loss_split/q_diel")
        assert c_in.status is CheckStatus.PASS
        assert c_in.margin == pytest.approx(0.1, rel=1e-6)
        assert c_out.status is CheckStatus.FAIL
        assert c_out.margin == pytest.approx(-0.1, rel=1e-6)

    def test_wall_fraction_edge_isolated_from_q_diel(self):
        # wall_fraction = 1 - q_total/q_diel exactly (the reciprocal
        # subtraction telescopes), so q_diel places wf at
        # 0.27 ± 0.1 half-widths (half-width 0.02) while q_diel itself
        # stays inside its own window — a clean single-check fail.
        q_total = 6_980.0
        inside = run_gate(
            StaticProvider(
                wall_loss_payload=wall_loss_payload(
                    q_total=q_total, q_diel=q_total / (1.0 - 0.268)
                )
            )
        )
        outside = run_gate(
            StaticProvider(
                wall_loss_payload=wall_loss_payload(
                    q_total=q_total, q_diel=q_total / (1.0 - 0.272)
                )
            )
        )
        c_in = check_by_name(inside, "wall_loss_split/wall_fraction")
        c_out = check_by_name(outside, "wall_loss_split/wall_fraction")
        assert c_in.status is CheckStatus.PASS
        assert c_in.margin == pytest.approx(0.1, rel=1e-6)
        assert c_out.status is CheckStatus.FAIL
        assert c_out.margin == pytest.approx(-0.1, rel=1e-6)
        # q_diel passed in the failing report: wf is the sole culprit.
        assert (
            check_by_name(outside, "wall_loss_split/q_diel").status
            is CheckStatus.PASS
        )

    @pytest.mark.parametrize(
        "f_m, expected_margin",
        [
            (1.01e7, +1.0 / 450.0),  # just inside the lower edge
            (0.99e7, -1.0 / 450.0),  # just outside the lower edge
            (1.01e8, -1.0 / 45.0),  # just outside the upper edge
        ],
    )
    def test_f_m_edges(self, f_m, expected_margin):
        report = run_gate(
            StaticProvider(booth_payload=booth_payload(f_m_global=f_m))
        )
        check = check_by_name(report, "f_m/order_of_magnitude")
        expected_status = (
            CheckStatus.PASS if expected_margin > 0 else CheckStatus.FAIL
        )
        assert check.status is expected_status
        assert check.margin == pytest.approx(expected_margin, rel=1e-6)

    # -- confinement structural fails (distinct from the endpoint
    # -- window edge above: the row must fail for the structural
    # -- reason, not because the endpoint missed its window)

    def test_two_point_payload_fails_structurally(self):
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0), (0.21e-6, 9_800.0)
                )
            )
        )
        row = rows_by_id(report)["confinement_trend"]
        assert row.status is CheckStatus.FAIL
        for check in row.checks:
            assert check.status is CheckStatus.FAIL
            assert "not two unrelated points" in check.notes
            # Never window-judged: the rejection is structural.
            assert check.measured is None
            assert check.margin is None

    def test_non_monotone_fails_structurally_endpoint_in_window(self):
        # Endpoint (0.21e-6, 9,800) is inside its window and reaches
        # the Breeze point — the ONLY failure is the broken trend.
        report = run_gate(
            StaticProvider(
                confinement_payload=confinement_payload(
                    (0.409e-6, 6_980.0),
                    (0.30e-6, 9_900.0),
                    (0.21e-6, 9_800.0),
                )
            )
        )
        row = rows_by_id(report)["confinement_trend"]
        assert row.status is CheckStatus.FAIL
        mono = check_by_name(report, "confinement_trend/monotonic")
        endpoint = check_by_name(report, "confinement_trend/endpoint_q")
        assert mono.status is CheckStatus.FAIL
        assert mono.measured < 0.0  # the negative Q increment
        assert endpoint.status is CheckStatus.PASS


class TestAggregation:
    def test_full_synthetic_pass(self):
        report = run_gate(full_pass_provider())
        assert report.phase1_complete
        assert report.n_pass == 6
        assert report.n_fail == report.n_deferred == 0

    def test_one_failing_row_blocks_phase1(self):
        provider = full_pass_provider()
        provider.booth_payload = booth_payload(q=7_200.0)
        report = run_gate(provider)
        assert not report.phase1_complete
        assert rows_by_id(report)["booth_two_point"].status is (
            CheckStatus.FAIL
        )
        # The shared Booth payload still passes f and F_m on their
        # own windows — a Q miss must not contaminate other rows.
        assert rows_by_id(report)["f"].status is CheckStatus.PASS


class TestProviders:
    def test_live_provider_importable_and_deferrable_without_mph(self):
        # Since the 2026-07-10 geometry recovery, empty_cavity(),
        # pec_lossy(), booth_walls_on() and wall_loss_split() are ALL
        # live arms — not called here (they would start a licence
        # session; MPh is installed on this host). Only the
        # confinement-trend row still defers unconditionally.
        provider = LiveComsolProvider(client=None)
        conf = provider.confinement_trend()
        assert isinstance(conf, Unavailable)
        assert "confinement sweep" in conf.reason
        repro = provider.reproducibility()
        assert repro.comsol_version is None
        assert repro.rng_seed is None

    def test_live_provider_through_gate_defers_blocked_rows(self):
        # Same single code path, no live solves (need a licence):
        # patch the four wired arms out with Unavailable to keep this
        # tier pure. booth_walls_on/wall_loss_split are live since the
        # 2026-07-10 recovery and must be patched like the §8 arms.
        provider = LiveComsolProvider(client=None)
        for arm in (
            "empty_cavity",
            "pec_lossy",
            "booth_walls_on",
            "wall_loss_split",
        ):
            setattr(
                provider,
                arm,
                lambda: Unavailable("not called in the no-licence tier"),
            )
        report = run_gate(provider)
        assert report.provider_kind == "live_comsol"
        assert report.n_deferred == 6

    def test_booth_recovered_geometry_matches_provenance(self):
        from cavity.forward_model.geometry import DielectricShape
        from cavity.provenance import GEOM_BOOTH_TE01D
        from cavity.validation.providers import (
            booth_faithful_materials,
            booth_recovered_geometry,
        )

        geom = booth_recovered_geometry()
        assert geom.dielectric_shape is DielectricShape.TORUS
        assert geom.box_radius_m == GEOM_BOOTH_TE01D.box_radius_m
        assert geom.box_height_m == GEOM_BOOTH_TE01D.box_height_m
        assert (
            geom.dielectric_radius_m
            == GEOM_BOOTH_TE01D.torus_major_radius_m
        )
        assert (
            geom.dielectric_minor_radius_m
            == GEOM_BOOTH_TE01D.torus_minor_radius_m
        )
        sens = booth_recovered_geometry(
            GEOM_BOOTH_TE01D.printed_minor_radius_m
        )
        assert (
            sens.dielectric_minor_radius_m
            == GEOM_BOOTH_TE01D.printed_minor_radius_m
        )
        mats = booth_faithful_materials()
        from cavity.provenance import BOOTH_MPH_TAN_DELTA

        assert mats.sto.tan_delta == BOOTH_MPH_TAN_DELTA
        assert mats.sto.epsilon_r_real == 316.3
        assert mats.wall_pec is False  # arm switch derived per-arm
