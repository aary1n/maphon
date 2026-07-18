"""Ratified (non-mock) sentinel resolutions — cavity.sweep.resolutions.

The first non-mock SentinelResolution (Q11, resolved 2026-07-17 at
planning grade): payload discipline (point inside band, below the
published bound), rung/mock discipline, provenance chain markers, and
the acceptance check that a ratified-Q11-only context still refuses
every solve-ready exit naming Q2/Q9 per mode.
"""

from __future__ import annotations

import pytest

from cavity.provenance import CRYSTAL
from cavity.sweep.backend import ComsolBackend
from cavity.sweep.design import materialise_dims
from cavity.sweep.dofs import (
    DesignMode,
    Rung,
    UnresolvedTodoTraceError,
)
from cavity.sweep.resolutions import RESOLUTION_Q11, ratified_resolutions


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


def test_ratified_context_resolves_q11_while_q2_q9_q13_remain():
    ctx = ratified_resolutions()
    assert not ctx.any_mock
    assert ctx.get("Q11") is RESOLUTION_Q11
    assert ctx.unresolved(DesignMode.BASELINE_D8) == ("Q2", "Q9", "Q13")
    assert ctx.unresolved(DesignMode.DEGRADED_D7) == ("Q9", "Q13")


def test_solve_ready_exits_still_refuse_naming_q2_q9_q13():
    ctx = ratified_resolutions()
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ctx.assert_solveable(DesignMode.BASELINE_D8, what="test")
    assert exc.value.question_ids == ("Q2", "Q9", "Q13")
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        materialise_dims(DesignMode.BASELINE_D8, ctx)
    assert exc.value.question_ids == ("Q2", "Q9", "Q13")
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ComsolBackend(ctx, DesignMode.DEGRADED_D7)
    assert exc.value.question_ids == ("Q9", "Q13")
