"""Published-anchor de-loading semantics (gap #3 closure, 2026-07-18).

The Wu build's coupling is now literature (k = 1 stated in print), carried
by the new `TARGETS.wu_ring` anchor via `PublishedTarget.stated_coupling_k`;
`TARGETS.wu_measured` is frozen byte-identical as the assumed-k-era record.
Acceptance windows for the new anchor are the queued W2 ratification item —
no gate row may bind it until W2 lands.
"""

from __future__ import annotations

import pytest

from cavity.provenance import DELOAD_K, GATE_ROWS, TARGETS, PublishedTarget


def test_wu_ring_records_stated_coupling_k1_and_print_f_1p4495():
    t = TARGETS.wu_ring
    assert t.kind == "measured_loaded"
    assert t.stated_coupling_k == 1.0
    assert t.f_hz == 1.4495e9  # Wu 2020 print (f_mode = f_XZ)
    assert t.q_factor == 3_600.0
    assert t.epsilon_r_real == 312.0
    # V_mode RECORDED but gate-held (W2): present on the entry only.
    assert t.v_mode_m3 == 0.32e-6


def test_wu_ring_deload_yields_q0_7200():
    t = TARGETS.wu_ring
    assert t.deload_k == 1.0  # the stated print, NOT the assumed DELOAD_K
    assert t.q_factor * (1.0 + t.deload_k) == 7_200.0


def test_wu_measured_frozen_byte_identical_assumed_k_era():
    """Invalidate-don't-rename: the superseded anchor's prints never move."""
    t = TARGETS.wu_measured
    assert t.source == "Wu 2020 cold-cavity loaded Q (coupling unstated, gap #3)"
    assert t.epsilon_r_real == 312.0
    assert t.q_factor == 3_600.0
    assert t.f_hz == 1.4493e9  # record-time B15-lineage reading, documented
    assert t.kind == "measured_loaded"
    assert t.stated_coupling_k is None


def test_stated_coupling_forbidden_on_modelled_kind():
    with pytest.raises(ValueError, match="measured_loaded"):
        PublishedTarget(
            source="x",
            epsilon_r_real=316.3,
            q_factor=1.0e4,
            f_hz=1.45e9,
            kind="modelled",
            stated_coupling_k=1.0,
        )


def test_deload_k_falls_back_to_assumed_constant():
    # Unstated-coupling anchors keep the assumption, with its caveat.
    assert TARGETS.wu_measured.deload_k == DELOAD_K == 0.2
    # Breeze / npj keep k = 0.2 — theirs is stated in their papers, so it
    # is the documented import, not an assumption transfer.
    assert TARGETS.breeze_measured.deload_k == 0.2
    assert TARGETS.npj_measured.deload_k == 0.2


def test_deload_k_refused_on_modelled_targets():
    with pytest.raises(ValueError, match="modelled"):
        TARGETS.booth.deload_k
    with pytest.raises(ValueError, match="modelled"):
        TARGETS.breeze.deload_k


def test_no_gate_row_binds_wu_ring_until_w2():
    """R7: acceptance windows for the Wu anchor are a NEW named
    ratification item (W2) — until it lands, no §5 gate row may
    reference the wu_ring values (Q_L, f, or the gate-held V_mode)."""
    for row in GATE_ROWS:
        for check in row.checks:
            assert "wu_ring" not in check.provenance
            assert check.target_value != TARGETS.wu_ring.v_mode_m3
            assert check.target_value != TARGETS.wu_ring.q_factor
