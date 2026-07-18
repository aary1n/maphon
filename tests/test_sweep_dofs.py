"""L1 DOF table — docs/plans/ticklish-possum.md / layer_a_sweep_design.md §2.

Table integrity (every committed nominal/band pinned against its
provenance constant), sentinel bookkeeping (Q2/Q9/Q11/Q13 question IDs
on the right rows), rung discipline, and the resolution-refusal pairs
that make the solve gate code, not convention. Re-based 2026-07-18 to
the Wu-ring rows (geometry re-base; box_height_m row invalidated — it
became the p_tune control).
"""

from __future__ import annotations

import pytest

from cavity.provenance import (
    CRYSTAL,
    GEOM_WU_STO_RING,
    STO,
    STO_HEIGHT_FORK,
    TOL,
)
from cavity.sweep.dofs import (
    LAYER_A_DOFS,
    SENTINEL_Q2,
    SENTINEL_Q9,
    SENTINEL_Q11,
    SENTINEL_Q13,
    SENTINEL_W1,
    SOLVE_GATE_QUESTIONS,
    DesignMode,
    DistributionKind,
    DofKind,
    DofSpec,
    ForkTrace,
    MockResolutionError,
    ResolutionContext,
    Rung,
    SentinelResolution,
    TodoTrace,
    UnresolvedTodoTraceError,
    dof_by_name,
    mock_resolutions,
    sweep_dimension_names,
)


# ---------------------------------------------------------------------------
# Table integrity: nine rows, committed values pinned to provenance
# ---------------------------------------------------------------------------


def test_table_has_nine_rows_in_design_doc_order():
    assert [d.name for d in LAYER_A_DOFS] == [
        "box_radius_m",
        "sto_outer_radius_m",
        "sto_inner_radius_m",
        "sto_height_m",
        "crystal_axial_offset_m",
        "crystal_eccentricity_m",
        "epsilon_r",
        "tan_delta",
        "p_tune",
    ]


@pytest.mark.parametrize(
    "name, nominal",
    [
        ("box_radius_m", GEOM_WU_STO_RING.box_inner_radius_m),
        ("sto_outer_radius_m", GEOM_WU_STO_RING.sto_outer_radius_m),
        ("sto_inner_radius_m", GEOM_WU_STO_RING.sto_inner_radius_m),
        ("epsilon_r", STO.epsilon_r_real),
        ("tan_delta", STO.tan_delta),
    ],
)
def test_committed_nominals_import_from_provenance(name, nominal):
    assert dof_by_name(name).nominal == nominal


@pytest.mark.parametrize(
    "name",
    ["box_radius_m", "sto_outer_radius_m", "sto_inner_radius_m"],
)
def test_geometry_bands_are_nominal_plus_minus_machining_tol(name):
    spec = dof_by_name(name)
    assert isinstance(spec.nominal, float)
    assert spec.band == (
        spec.nominal - TOL.machining_tol_m,
        spec.nominal + TOL.machining_tol_m,
    )
    # The ±25 µm band is the committed PLACEHOLDER — planning rung.
    assert spec.band_rung is Rung.PLANNING_ASSUMPTION
    assert spec.distribution is DistributionKind.TRUNC_GAUSSIAN_3SIGMA


def test_epsilon_r_band_is_tol_312_318_per_q4_ruling():
    spec = dof_by_name("epsilon_r")
    assert spec.band == (TOL.epsilon_r_min, TOL.epsilon_r_max)
    assert spec.band == (312.0, 318.0)
    assert spec.distribution is DistributionKind.UNIFORM
    # Q4 ruling recorded in the row's provenance, not just the plan.
    assert "Q4" in spec.provenance


def test_tan_delta_band_is_tol_span():
    spec = dof_by_name("tan_delta")
    assert spec.band == (TOL.tan_delta_min, TOL.tan_delta_max)
    # Upper endpoint re-derived 2026-07-18 at Wu's stated k = 1:
    # 1/(3600*2) = 1.389e-4 -> 2 s.f. 1.4e-4 (was 2.3e-4 at assumed 0.2).
    assert spec.band == (1.0e-4, 1.4e-4)
    assert spec.distribution is DistributionKind.UNIFORM


# ---------------------------------------------------------------------------
# Sentinel rows carry the right open-question IDs
# ---------------------------------------------------------------------------


def test_crystal_axial_offset_row_is_q9_todo_trace():
    spec = dof_by_name("crystal_axial_offset_m")
    assert isinstance(spec.nominal, TodoTrace)
    assert isinstance(spec.band, TodoTrace)
    assert spec.sentinel is SENTINEL_Q9
    assert spec.nominal_rung is Rung.TODO_TRACE
    # The 2026-07-16 coordinate definition rides the provenance note.
    assert "equatorial plane" in spec.provenance
    assert "provenance.CRYSTAL" in spec.provenance


def test_crystal_eccentricity_is_not_a_sweep_dim_and_q9_banded():
    spec = dof_by_name("crystal_eccentricity_m")
    assert spec.kind is DofKind.NOISE_NOT_A_SWEEP_DIM
    assert spec.nominal == 0.0  # CENTRED
    # 2026-07-16 verbal partial resolution: nominal rung upgraded with
    # the numeric nominal unchanged; the band stays TODO-trace (Q9).
    assert spec.nominal_rung is Rung.SUPERVISOR_CONFIRMED
    assert isinstance(spec.band, TodoTrace)
    assert spec.band.question_id == "Q9"
    # Never folded into machining_tol_m (TolRanges docstring guard).
    assert "machining_tol_m" in spec.provenance


def test_p_tune_row_is_q2_control():
    spec = dof_by_name("p_tune")
    assert spec.kind is DofKind.CONTROL
    assert spec.sentinel is SENTINEL_Q2
    assert spec.distribution is DistributionKind.CONTROL_ROOT_SOLVED
    # 2026-07-18 semantics: p_tune IS the box internal height (metres);
    # mechanism identified, travel still the open Q2 ask.
    assert "INTERNAL HEIGHT" in SENTINEL_Q2.description
    assert "travel" in SENTINEL_Q2.description


def test_sto_height_row_is_q13_fork_trace():
    spec = dof_by_name("sto_height_m")
    assert isinstance(spec.nominal, ForkTrace)
    assert isinstance(spec.band, ForkTrace)
    assert spec.sentinel is SENTINEL_Q13
    assert spec.nominal_rung is Rung.TODO_TRACE
    assert spec.band_rung is Rung.TODO_TRACE
    assert "8.5" in spec.provenance and "8.6" in spec.provenance


def test_fork_trace_requires_two_candidates_and_favoured_membership():
    with pytest.raises(ValueError, match=">= 2 candidates"):
        ForkTrace(
            question_id="Q13",
            description="x",
            routes_to="y",
            candidates=(1.0,),
            evidence_favoured=1.0,
        )
    with pytest.raises(ValueError, match="one of the candidates"):
        ForkTrace(
            question_id="Q13",
            description="x",
            routes_to="y",
            candidates=(1.0, 2.0),
            evidence_favoured=3.0,
        )


def test_fork_trace_is_not_arithmetic():
    with pytest.raises(TypeError):
        SENTINEL_Q13 + 1.0  # a fork must never quietly become a number
    with pytest.raises(TypeError):
        float(SENTINEL_Q13)


def test_fork_candidates_import_from_provenance_fork():
    # The sweep sentinel machine-reads the provenance fork record —
    # one source of truth for the candidate set and the favoured branch.
    assert SENTINEL_Q13.candidates == STO_HEIGHT_FORK.candidates == (
        8.5e-3,
        8.6e-3,
    )
    assert (
        SENTINEL_Q13.evidence_favoured
        == STO_HEIGHT_FORK.evidence_favoured
        == 8.6e-3
    )


def test_sentinel_question_ids():
    assert SENTINEL_Q2.question_id == "Q2"
    assert SENTINEL_Q9.question_id == "Q9"
    assert SENTINEL_Q11.question_id == "Q11"
    assert SENTINEL_Q13.question_id == "Q13"
    assert SENTINEL_W1.question_id == "W1"


def test_todo_trace_rejects_malformed_question_ids():
    with pytest.raises(ValueError, match="question_id"):
        TodoTrace(question_id="banana", description="x", routes_to="y")


def test_todo_trace_is_not_arithmetic():
    with pytest.raises(TypeError):
        SENTINEL_Q9 + 1.0  # a sentinel must never quietly become a number


# ---------------------------------------------------------------------------
# Rung discipline on the table itself
# ---------------------------------------------------------------------------


def test_todo_trace_slots_must_carry_todo_rung():
    with pytest.raises(ValueError, match="TODO_TRACE rung"):
        DofSpec(
            name="bad",
            kind=DofKind.NOISE,
            nominal=SENTINEL_Q9,
            band=(0.0, 1.0),
            distribution=DistributionKind.UNIFORM,
            nominal_rung=Rung.PLANNING_ASSUMPTION,  # lies about the slot
            band_rung=Rung.PLANNING_ASSUMPTION,
            provenance="x",
        )


def test_nominal_outside_band_refused():
    with pytest.raises(ValueError, match="outside band"):
        DofSpec(
            name="bad",
            kind=DofKind.NOISE,
            nominal=2.0,
            band=(0.0, 1.0),
            distribution=DistributionKind.UNIFORM,
            nominal_rung=Rung.PLANNING_ASSUMPTION,
            band_rung=Rung.PLANNING_ASSUMPTION,
            provenance="x",
        )


# ---------------------------------------------------------------------------
# Sweep dimensions per mode + the critical-path partition
# ---------------------------------------------------------------------------


def test_d8_baseline_dimensions():
    names = sweep_dimension_names(DesignMode.BASELINE_D8)
    assert len(names) == 8
    assert names[-1] == "p_tune"
    assert "crystal_eccentricity_m" not in names  # breaks m = 0


def test_d7_degraded_dimensions():
    names = sweep_dimension_names(DesignMode.DEGRADED_D7)
    assert len(names) == 7
    assert "p_tune" not in names
    # the crystal axial offset IS one of the seven noise dims — which
    # is why the d = 7 fallback relieves only Q2, never Q9/Q11.
    assert "crystal_axial_offset_m" in names


def test_solve_gate_partition_matches_design_doc():
    # Q13 (ring-height fork) gates BOTH modes — sto_height_m is a noise
    # dim no geometry can be built without (2026-07-18 re-base).
    assert SOLVE_GATE_QUESTIONS[DesignMode.BASELINE_D8] == (
        "Q2", "Q9", "Q11", "Q13",
    )
    assert SOLVE_GATE_QUESTIONS[DesignMode.DEGRADED_D7] == (
        "Q9", "Q11", "Q13",
    )


# ---------------------------------------------------------------------------
# Resolution machinery — refusal pairs
# ---------------------------------------------------------------------------


def _q11_resolution(**overrides) -> SentinelResolution:
    kwargs = dict(
        question_id="Q11",
        payload={"crystal_epsilon_r": 2.9},
        rung=Rung.LITERATURE_CONFIRMED,
        provenance="hypothetical literature trace (test)",
    )
    kwargs.update(overrides)
    return SentinelResolution(**kwargs)


def test_resolution_accepts_a_well_formed_answer():
    res = _q11_resolution()
    assert res.payload["crystal_epsilon_r"] == 2.9
    assert not res.mock


def test_resolution_refuses_todo_trace_rung():
    with pytest.raises(ValueError, match="not a resolution"):
        _q11_resolution(rung=Rung.TODO_TRACE)


def test_resolution_refuses_unknown_question():
    with pytest.raises(ValueError, match="unknown"):
        SentinelResolution(
            question_id="Q4",  # resolved by ruling, not by payload
            payload={},
            rung=Rung.PLANNING_ASSUMPTION,
            provenance="x",
        )


def test_resolution_refuses_missing_payload_keys():
    with pytest.raises(ValueError, match="missing keys"):
        SentinelResolution(
            question_id="Q9",
            payload={"crystal_axial_offset_nominal_m": 0.5e-3},
            rung=Rung.PLANNING_ASSUMPTION,
            provenance="x",
        )


def test_resolution_refuses_blank_provenance():
    with pytest.raises(ValueError, match="provenance"):
        _q11_resolution(provenance="   ")


def test_mock_resolution_must_stay_planning_rung():
    with pytest.raises(ValueError, match="provenance lie"):
        _q11_resolution(mock=True, rung=Rung.SUPERVISOR_CONFIRMED)


def test_context_refuses_duplicate_resolutions():
    with pytest.raises(ValueError, match="duplicate"):
        ResolutionContext(
            resolutions=(_q11_resolution(), _q11_resolution())
        )


# ---------------------------------------------------------------------------
# The gate itself
# ---------------------------------------------------------------------------


def test_empty_context_refuses_both_modes_naming_question_ids():
    ctx = ResolutionContext()
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ctx.assert_solveable(DesignMode.BASELINE_D8, what="test")
    assert exc.value.question_ids == ("Q2", "Q9", "Q11", "Q13")
    assert "Q2" in str(exc.value) and "Q13" in str(exc.value)

    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ctx.assert_solveable(DesignMode.DEGRADED_D7, what="test")
    assert exc.value.question_ids == ("Q9", "Q11", "Q13")


def test_partial_context_names_only_the_missing_questions():
    ctx = ResolutionContext(resolutions=(_q11_resolution(),))
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ctx.assert_solveable(DesignMode.DEGRADED_D7, what="test")
    assert exc.value.question_ids == ("Q9", "Q13")


def test_mock_context_is_never_solveable():
    ctx = mock_resolutions()
    assert ctx.any_mock
    for mode in DesignMode:
        with pytest.raises(MockResolutionError, match="MOCK"):
            ctx.assert_solveable(mode, what="test")


def test_mock_context_resolves_all_four_questions_for_shape():
    ctx = mock_resolutions()
    assert ctx.unresolved(DesignMode.BASELINE_D8) == ()
    assert ctx.unresolved(DesignMode.DEGRADED_D7) == ()
    # And the axial-offset mock stays inside the geometric bound
    # (crystal must fit axially inside the Wu box at the as-operated
    # internal height).
    q9 = ctx.get("Q9")
    assert q9 is not None
    max_offset_m = (
        GEOM_WU_STO_RING.box_internal_height_asoperated_m
        - CRYSTAL.height_m
    ) / 2.0
    assert abs(q9.payload["crystal_axial_offset_nominal_m"]) <= max_offset_m
    q11 = ctx.get("Q11")
    assert q11 is not None
    assert q11.payload["crystal_epsilon_r"] < CRYSTAL.epsilon_r_upper_bound
    # The Q13 mock selects the evidence-favoured branch EXPLICITLY and
    # says so — the sanctioned labelled read of the fork.
    q13 = ctx.get("Q13")
    assert q13 is not None and q13.mock
    assert q13.payload["sto_height_m"] == SENTINEL_Q13.evidence_favoured
    assert "MOCK" in q13.payload["selection_evidence"]


def test_dof_by_name_unknown_row():
    with pytest.raises(KeyError, match="unknown DOF"):
        dof_by_name("plate_angle")
