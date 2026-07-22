"""W2 dual-geometry session — zero-licence tests (2026-07-22).

Pins: the coded windows against the ratified doc values
(docs/w2_wu_anchor_windows.md, 2026-07-19 — no window revision at
solve time); the Run B diagnostic O.D. as a labelled input that never
touches the carried value; the pre-registered W2.4-first judgment
order; the geometry/material assembly (heights and eps_r enter ONLY
via the Q13/Q11 resolution payloads); and the precondition refusals.
"""

from __future__ import annotations

import pytest

from cavity.provenance import GEOM_WU_STO_RING, TARGETS
from cavity.validation.report_w2 import (
    W2_F_REL_TOL,
    W2_F_TARGET_HZ,
    W2_Q0_REL_TOL,
    W2_Q0_TARGET,
    W2_RATIO_TOL,
    W2_RUN_B_MEASURED_OD_M,
    W2_V_MODE_REPORT_M3,
    judge_run_a,
)
from cavity.validation.run_w2 import (
    w2_resolved_inputs,
    wu_w2_geometry,
    wu_w2_materials,
)


class TestWindowsMatchRatifiedDoc:
    """The coded windows ARE the 2026-07-19 ratified planning choices —
    numeric identity, derived from provenance where the doc derives
    them (Q0 target via the stated k = 1 de-load, never a bare 7200)."""

    def test_w2_1_f_window(self):
        assert W2_F_TARGET_HZ == 1.4495e9
        assert W2_F_TARGET_HZ == TARGETS.wu_ring.f_hz
        assert W2_F_REL_TOL == 0.015

    def test_w2_2_q0_window_derived_from_stated_coupling(self):
        assert TARGETS.wu_ring.stated_coupling_k == 1.0
        assert W2_Q0_TARGET == TARGETS.wu_ring.q_factor * 2.0
        assert W2_Q0_TARGET == 7200.0
        assert W2_Q0_REL_TOL == 0.25

    def test_w2_3_report_only_value(self):
        assert W2_V_MODE_REPORT_M3 == 0.32e-6
        assert W2_V_MODE_REPORT_M3 == TARGETS.wu_ring.v_mode_m3

    def test_w2_4_ratio_window(self):
        assert W2_RATIO_TOL == 0.10


class TestRunBDiagnosticInput:
    """The measured O.D. is a LABELLED diagnostic input of this session
    only — the carried value is untouched (treatment (i); no branch
    selection in any carried value)."""

    def test_measured_od_value_and_label(self):
        assert W2_RUN_B_MEASURED_OD_M == 12.2e-3

    def test_carried_print_untouched(self):
        assert GEOM_WU_STO_RING.sto_outer_radius_m == 6.0e-3
        assert 2.0 * GEOM_WU_STO_RING.sto_outer_radius_m == 12.0e-3
        assert W2_RUN_B_MEASURED_OD_M != (
            2.0 * GEOM_WU_STO_RING.sto_outer_radius_m
        )


def _finest(f_hz, q, v_local, v_global, p_e=0.99):
    return {
        "f_hz": f_hz,
        "q": q,
        "v_mode_local_m3": v_local,
        "v_mode_global_m3": v_global,
        "p_e": p_e,
    }


class TestJudgeOrder:
    """Pre-registered order (the 225/360 lesson): W2.4 first; its
    failure leaves W2.1/W2.2 NOT JUDGED and W2.3 meaningless."""

    def test_all_pass(self):
        v = judge_run_a(_finest(1.4495e9, 7200.0, 0.30e-6, 0.30e-6))
        assert v["w2_4_ok"] and v["passed"]
        names = [c["name"] for c in v["checks"]]
        assert names[0] == "W2.4/v_mode_local_over_global"
        by = {c["name"]: c for c in v["checks"]}
        assert by["W2.1/f"]["status"] == "pass"
        assert by["W2.2/q0"]["status"] == "pass"
        assert by["W2.3/v_mode_local"]["status"] == "report_only"

    def test_convention_failure_stops_window_judgment(self):
        v = judge_run_a(_finest(1.4495e9, 7200.0, 0.20e-6, 0.30e-6))
        assert not v["w2_4_ok"] and not v["passed"]
        by = {c["name"]: c for c in v["checks"]}
        assert by["W2.4/v_mode_local_over_global"]["status"] == "fail"
        assert by["W2.1/f"]["status"] == "not_judged"
        assert by["W2.2/q0"]["status"] == "not_judged"
        assert (
            by["W2.3/v_mode_local"]["status"]
            == "meaningless_convention_failed"
        )

    def test_f_window_edges(self):
        lo = 1.4495e9 * (1.0 - 0.015)
        hi = 1.4495e9 * (1.0 + 0.015)
        for f, ok in ((lo, True), (hi, True), (lo * 0.999, False),
                      (hi * 1.001, False)):
            v = judge_run_a(_finest(f, 7200.0, 0.3e-6, 0.3e-6))
            assert v["passed"] is ok, f

    def test_q0_window_edges(self):
        for q, ok in ((5400.0, True), (9000.0, True), (5399.0, False),
                      (9001.0, False)):
            v = judge_run_a(_finest(1.4495e9, q, 0.3e-6, 0.3e-6))
            assert v["passed"] is ok, q

    def test_w2_3_never_gates(self):
        # v_mode wildly off the printed 0.32 cm^3 must not fail the run
        v = judge_run_a(_finest(1.4495e9, 7200.0, 5.0e-6, 5.0e-6))
        assert v["passed"]


class TestGeometryAssembly:
    """Inputs enter via the resolution payloads and graded constants;
    the two runs differ ONLY in the ring O.D."""

    def test_resolved_inputs_come_from_the_register(self):
        from cavity.sweep.resolutions import (
            RESOLUTION_Q11,
            RESOLUTION_Q13,
        )

        h, eps = w2_resolved_inputs()
        assert h == RESOLUTION_Q13.payload["sto_height_m"] == 8.6e-3
        assert eps == RESOLUTION_Q11.payload["crystal_epsilon_r"] == 3.0

    def test_run_a_geometry(self):
        h, _ = w2_resolved_inputs()
        g = wu_w2_geometry(GEOM_WU_STO_RING.sto_outer_radius_m, h)
        assert g.dielectric_radius_m == 6.0e-3
        assert g.dielectric_height_m == 8.6e-3
        assert g.box_radius_m == 14.0e-3
        assert g.box_height_m == 15e-3  # as-operated = Q2 nominal
        assert g.ring_bottom_z_m == 3.0e-3
        assert g.spacer is not None
        assert g.piston_radius_m is None  # flat ceiling, pre-registered
        # crystal: planning dims, centred on the ring mid-height plane
        assert g.crystal_radius_m == 1.5e-3
        assert g.crystal_height_m == 8.0e-3
        assert g.crystal_centre_z_m == pytest.approx(
            3.0e-3 + 0.5 * 8.6e-3
        )

    def test_runs_differ_only_in_outer_radius(self):
        h, _ = w2_resolved_inputs()
        a = wu_w2_geometry(GEOM_WU_STO_RING.sto_outer_radius_m, h)
        b = wu_w2_geometry(0.5 * W2_RUN_B_MEASURED_OD_M, h)
        assert b.dielectric_radius_m == 6.1e-3
        for field in (
            "box_radius_m",
            "box_height_m",
            "dielectric_height_m",
            "dielectric_inner_radius_m",
            "ring_bottom_z_m",
            "crystal_radius_m",
            "crystal_height_m",
            "crystal_centre_z_m",
            "spacer",
        ):
            assert getattr(a, field) == getattr(b, field), field

    def test_materials_canonical_with_q11_crystal(self):
        from cavity.provenance import CLPS, STO

        _, eps = w2_resolved_inputs()
        m = wu_w2_materials(eps)
        assert m.sto is STO  # canonical branch
        assert m.spacer is CLPS
        assert m.crystal is not None
        assert m.crystal.epsilon_r_real == 3.0
        assert m.crystal.tan_delta == 0.0  # deliberately ungraded
        assert m.wall_pec is False  # per-arm switch re-derived later


class TestPreconditionRefusals:
    """W2 refuses on missing or mock Q13/Q11 — its own precondition
    list, NOT the sweep gate (H3: never cross-wired)."""

    def test_refuses_empty_register(self, monkeypatch):
        import cavity.sweep.resolutions as res
        from cavity.sweep.dofs import (
            ResolutionContext,
            UnresolvedTodoTraceError,
        )

        monkeypatch.setattr(
            res, "ratified_resolutions", lambda: ResolutionContext()
        )
        with pytest.raises(UnresolvedTodoTraceError):
            w2_resolved_inputs()

    def test_refuses_mock_resolutions(self, monkeypatch):
        import cavity.sweep.resolutions as res
        from cavity.sweep.dofs import (
            MockResolutionError,
            mock_resolutions,
        )

        monkeypatch.setattr(
            res, "ratified_resolutions", mock_resolutions
        )
        with pytest.raises(MockResolutionError):
            w2_resolved_inputs()
