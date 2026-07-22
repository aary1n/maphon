"""Ratified (non-mock) sentinel resolutions — cavity.sweep.resolutions.

The first non-mock SentinelResolution (Q11, resolved 2026-07-17 at
planning grade): payload discipline (point inside band, below the
published bound), rung/mock discipline, provenance chain markers, and
the acceptance check that a ratified-Q11-only context still refuses
every solve-ready exit naming Q2/Q9 per mode.

2026-07-21 continuation: Q13 + Q2 joined the register — first-hand
in-person caliper measurements made live during the 2026-07-21
meeting (provenance corrected 2026-07-22, initially under-graded as
verbally-reported; notes + photos archived; written confirmation
pending; the ring-identity claim stays Oxborrow-verbal) —
payload/provenance discipline for both, the
nominal-at-band-edge convention (Q2), and the acceptance check that
the ratified context now refuses every solve-ready exit naming Q9
alone.
"""

from __future__ import annotations

import pytest

from cavity.provenance import CRYSTAL, GEOM_WU_STO_RING
from cavity.sweep.backend import ComsolBackend
from cavity.sweep.design import materialise_dims
from cavity.sweep.dofs import (
    DesignMode,
    Rung,
    UnresolvedTodoTraceError,
)
from cavity.sweep.resolutions import (
    RATIFIED_RESOLUTIONS,
    RESOLUTION_Q2,
    RESOLUTION_Q11,
    RESOLUTION_Q13,
    ratified_resolutions,
)

ARCHIVE = "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/"


def test_ratified_q11_is_non_mock_planning_assumption():
    assert RESOLUTION_Q11.question_id == "Q11"
    assert RESOLUTION_Q11.mock is False
    assert RESOLUTION_Q11.rung is Rung.PLANNING_ASSUMPTION


def test_ratified_q11_point_inside_band_and_below_published_bound():
    point = RESOLUTION_Q11.payload["crystal_epsilon_r"]
    lo, hi = RESOLUTION_Q11.payload["crystal_epsilon_r_band"]
    assert lo < point < hi
    # The (iii) consistency bound, pinned: band AND point sit below
    # the published Breeze "eps_r < 5" bound by construction.
    assert hi < CRYSTAL.epsilon_r_upper_bound
    assert point < CRYSTAL.epsilon_r_upper_bound


def test_ratified_q11_provenance_carries_chain_and_negative_space():
    p = RESOLUTION_Q11.provenance
    assert "Cummins" in p
    assert "WNLM2C8X" in p
    assert "OPTICAL" in p  # optical-frequency caveat, not static
    assert "NOT FOUND" in p  # negative-space record
    assert "REJECTED" in p
    assert "KCDCRN4C" in p


def test_resolution_q13_payload_and_provenance():
    """Q13: ring height 8.6e-3 m (METRES), first-hand in-person
    caliper measurement (provenance corrected 2026-07-22),
    archive-cited, no band key (the ±25 µm placeholder route)."""
    assert RESOLUTION_Q13.question_id == "Q13"
    assert RESOLUTION_Q13.mock is False
    assert RESOLUTION_Q13.rung is Rung.SUPERVISOR_CONFIRMED
    assert RESOLUTION_Q13.payload["sto_height_m"] == 8.6e-3
    # No measured band was obtained — the placeholder-band route in
    # design.materialise_dims must fire, so the key must be ABSENT.
    assert "sto_height_band_m" not in RESOLUTION_Q13.payload
    assert ARCHIVE in RESOLUTION_Q13.payload["selection_evidence"]
    assert ARCHIVE in RESOLUTION_Q13.provenance
    assert "written confirmation pending" in RESOLUTION_Q13.provenance
    assert "caliper" in RESOLUTION_Q13.payload["selection_evidence"]
    # 2026-07-22 provenance correction pinned: the measurement is a
    # first-hand in-person caliper reading, and the verbal grade
    # attaches to the ring-identity claim only.
    assert "first-hand" in RESOLUTION_Q13.provenance
    assert "not independently verified" in RESOLUTION_Q13.provenance


def test_resolution_q2_payload_nominal_at_band_edge():
    """Q2: travel band [15, 25] mm (METRES); the nominal is the
    as-operated 15 mm sitting AT the lower edge — the accepted
    convention (no validator requires strict interiority)."""
    assert RESOLUTION_Q2.question_id == "Q2"
    assert RESOLUTION_Q2.mock is False
    assert RESOLUTION_Q2.rung is Rung.SUPERVISOR_CONFIRMED
    assert RESOLUTION_Q2.payload["p_tune_min"] == 15e-3
    assert RESOLUTION_Q2.payload["p_tune_max"] == 25e-3
    assert (
        RESOLUTION_Q2.payload["p_tune_nominal"]
        == RESOLUTION_Q2.payload["p_tune_min"]
        == GEOM_WU_STO_RING.box_internal_height_asoperated_m
    )
    # The gap-depth rider stays open: the optional key must be ABSENT.
    assert "piston_gap_depth_m" not in RESOLUTION_Q2.payload
    assert ARCHIVE in RESOLUTION_Q2.payload["mechanism"]
    assert ARCHIVE in RESOLUTION_Q2.provenance
    assert "written confirmation pending" in RESOLUTION_Q2.provenance
    # 2026-07-22 provenance correction pinned: first-hand in-person
    # measurement, not a verbal report.
    assert "first-hand" in RESOLUTION_Q2.provenance


def test_ratified_context_resolves_q2_q11_q13_while_q9_remains():
    # The register itself: three entries, question order.
    assert tuple(r.question_id for r in RATIFIED_RESOLUTIONS) == (
        "Q2",
        "Q11",
        "Q13",
    )
    ctx = ratified_resolutions()
    assert not ctx.any_mock
    assert ctx.get("Q2") is RESOLUTION_Q2
    assert ctx.get("Q11") is RESOLUTION_Q11
    assert ctx.get("Q13") is RESOLUTION_Q13
    assert ctx.unresolved(DesignMode.BASELINE_D8) == ("Q9",)
    assert ctx.unresolved(DesignMode.DEGRADED_D7) == ("Q9",)


def test_solve_ready_exits_still_refuse_naming_q9():
    ctx = ratified_resolutions()
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ctx.assert_solveable(DesignMode.BASELINE_D8, what="test")
    assert exc.value.question_ids == ("Q9",)
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        materialise_dims(DesignMode.BASELINE_D8, ctx)
    assert exc.value.question_ids == ("Q9",)
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ComsolBackend(ctx, DesignMode.DEGRADED_D7)
    assert exc.value.question_ids == ("Q9",)
