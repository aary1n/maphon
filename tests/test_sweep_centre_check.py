"""L5 sweep-centre verification — import-only pins against the rejudge
gate record, the itemised 5-solve block, Q9/Q11 gating, and the W1
unjudged-window discipline (rider R2).
"""

from __future__ import annotations

import pytest

from cavity.forward_model.study import WallBC
from cavity.provenance import DELOAD_K
from cavity.sweep.backend import (
    MockBackend,
    SWEEP_MESH_COARSER,
    SWEEP_MESH_FINEST,
)
from cavity.sweep.centre_check import (
    GATE_RECORD_HASH,
    GATE_RUN_DIR,
    PINNED_CENTRE,
    SWEEP_CENTRE_DEFINITION,
    centre_verification_report,
    centre_verification_specs,
    judge_centre_verification,
    read_gate_record_values,
    run_centre_verification,
)
from cavity.sweep.dofs import (
    MockResolutionError,
    ResolutionContext,
    Rung,
    SentinelResolution,
    UnresolvedTodoTraceError,
    mock_resolutions,
)


def _real_q9_q11_context() -> ResolutionContext:
    return ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q9",
                payload={
                    # MOCK axial-offset values (hypothetical, test only)
                    "crystal_axial_offset_nominal_m": 0.5e-3,
                    "crystal_axial_offset_band_m": (0.45e-3, 0.55e-3),
                    "centring_tolerance_m": 50e-6,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
            SentinelResolution(
                question_id="Q11",
                payload={"crystal_epsilon_r": 2.9},
                rung=Rung.LITERATURE_CONFIRMED,
                provenance="hypothetical (test only)",
            ),
        )
    )


# ---------------------------------------------------------------------------
# Import-only pins — re-read the gate record and assert equality
# ---------------------------------------------------------------------------


def test_pinned_centre_reproduces_the_rejudge_record_verbatim():
    """The drift detector: PinnedCentre must equal the canonical arm of
    refs/gate_runs/20260711T132705Z_rejudge/checkpoint_manifest.json
    exactly — import-only, zero re-derivation."""
    record = read_gate_record_values()
    assert record["record_hash"] == GATE_RECORD_HASH == "823e67969516bcf2"
    assert PINNED_CENTRE.record_hash == record["record_hash"]
    assert PINNED_CENTRE.q0 == record["q"]
    assert PINNED_CENTRE.p_e == record["p_e"]
    assert PINNED_CENTRE.f_hz == record["f_hz"]


def test_gate_run_dir_exists_in_repo():
    assert GATE_RUN_DIR.is_dir()
    assert (GATE_RUN_DIR / "checkpoint_manifest.json").is_file()


def test_q_l_is_a_convention_application_not_a_literal():
    assert PINNED_CENTRE.q_l == PINNED_CENTRE.q0 / (1.0 + DELOAD_K)
    # Design doc §1 print: Q_L = 5637.1544 (4 d.p. of the derived value).
    assert PINNED_CENTRE.q_l == pytest.approx(5637.1544, abs=5e-4)


def test_sweep_centre_definition_is_the_design_doc_sentence():
    # Wording updated 2026-07-16 with the Q9 reframe (formerly
    # "no-bore/no-crystal limit") — design doc §1 rider carries the
    # dated wording-change note.
    assert "no-crystal limit" in SWEEP_CENTRE_DEFINITION
    assert "823e67969516bcf2" in SWEEP_CENTRE_DEFINITION


# ---------------------------------------------------------------------------
# The itemised 5-solve block
# ---------------------------------------------------------------------------


def test_block_is_exactly_the_corrected_itemisation():
    specs = centre_verification_specs(mock_resolutions())
    assert len(specs) == 5  # 4 + 1 PEC arm; the draft's 6 over-counted
    on_off = [
        (s.crystal_on, s.mesh_level, s.wall_bc) for s in specs
    ]
    assert on_off.count((True, "finest", WallBC.IMPEDANCE)) == 1
    assert on_off.count((False, "finest", WallBC.IMPEDANCE)) == 1
    assert on_off.count((True, "coarser", WallBC.IMPEDANCE)) == 1
    assert on_off.count((False, "coarser", WallBC.IMPEDANCE)) == 1
    assert on_off.count((True, "finest", WallBC.PEC)) == 1
    assert len({s.label for s in specs}) == 5


def test_specs_carry_resolved_phase1b_values_and_meshes():
    ctx = mock_resolutions()
    specs = centre_verification_specs(ctx)
    q9 = ctx.get("Q9").payload
    q11 = ctx.get("Q11").payload
    for s in specs:
        assert s.crystal_axial_offset_m == q9["crystal_axial_offset_nominal_m"]
        assert s.crystal_epsilon_r == q11["crystal_epsilon_r"]
        assert s.mesh in (SWEEP_MESH_FINEST, SWEEP_MESH_COARSER)
        assert s.study.n_modes == 12
    finest = [s for s in specs if s.mesh_level == "finest"]
    assert all(s.mesh == SWEEP_MESH_FINEST for s in finest)


def test_specs_refuse_unresolved_context_naming_q9_q11():
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        centre_verification_specs(ResolutionContext())
    assert exc.value.question_ids == ("Q9", "Q11")


# ---------------------------------------------------------------------------
# Run gating — three-layer refusal
# ---------------------------------------------------------------------------


def test_run_refuses_unresolved_sentinels():
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        run_centre_verification(MockBackend(), ResolutionContext())
    assert exc.value.question_ids == ("Q9", "Q11")


def test_run_refuses_mock_resolutions():
    with pytest.raises(MockResolutionError, match="licence"):
        run_centre_verification(MockBackend(), mock_resolutions())


def test_run_refuses_missing_phase1b_engine_even_when_resolved():
    with pytest.raises(NotImplementedError, match="SPEC §5b"):
        run_centre_verification(MockBackend(), _real_q9_q11_context())


# ---------------------------------------------------------------------------
# Report — deltas only; judgment refused until W1 (rider R2)
# ---------------------------------------------------------------------------


def _arm(f, q, p_e):
    return {"f_real_hz": f, "q": q, "p_e": p_e}


def test_report_delta_arithmetic():
    off = _arm(PINNED_CENTRE.f_hz + 1.0e5, PINNED_CENTRE.q0 * 1.001,
               PINNED_CENTRE.p_e - 1e-4)
    on = _arm(off["f_real_hz"] - 2.0e6, off["q"] * 0.98,
              off["p_e"] - 5e-4)
    report = centre_verification_report(off, on)
    assert report["pinned_centre"]["import_only"] is True
    assert report["pinned_centre"]["record_hash"] == GATE_RECORD_HASH
    assert report["off_arm_vs_pinned"]["delta_f_hz"] == pytest.approx(1.0e5)
    assert report["off_arm_vs_pinned"]["delta_q0_rel"] == pytest.approx(
        0.001, rel=1e-9
    )
    assert report["phase1b_perturbation"]["delta_f_hz"] == pytest.approx(
        -2.0e6
    )
    assert report["phase1b_perturbation"]["delta_q0_rel"] == pytest.approx(
        -0.02, rel=1e-9
    )


def test_report_judgment_is_unjudged_with_the_w1_sentinel():
    report = centre_verification_report(
        _arm(PINNED_CENTRE.f_hz, PINNED_CENTRE.q0, PINNED_CENTRE.p_e),
        _arm(PINNED_CENTRE.f_hz, PINNED_CENTRE.q0, PINNED_CENTRE.p_e),
    )
    judgment = report["judgment"]
    assert judgment["status"] == "UNJUDGED"
    assert judgment["window"] is None
    assert judgment["window_sentinel"] == "W1"
    assert "Q9 + Q11" in judgment["due"]


def test_judgment_refusal_names_w1():
    report = centre_verification_report(
        _arm(PINNED_CENTRE.f_hz, PINNED_CENTRE.q0, PINNED_CENTRE.p_e),
        _arm(PINNED_CENTRE.f_hz, PINNED_CENTRE.q0, PINNED_CENTRE.p_e),
    )
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        judge_centre_verification(report)
    assert exc.value.question_ids == ("W1",)
    # Handing it a "window" early is also refused — the judging pass
    # arrives with W1's ratification, not before.
    with pytest.raises(NotImplementedError, match="W1"):
        judge_centre_verification(report, window=object())
