"""Wu anchor pinned record — import-only equality pins (2026-07-22).

`cavity.sweep.wu_anchor` mirrors the `centre_check.PinnedCentre`
doctrine: no quantity is re-derived; this test re-reads the archived
W2 manifest and asserts the pinned constants equal it exactly.
"""

from __future__ import annotations

import pytest

from cavity.sweep.wu_anchor import (
    WU_ANCHOR,
    WU_ANCHOR_RUN_DIR,
    WU_OD_SENSITIVITY_DF_DOD_HZ_PER_M,
    WU_OD_SENSITIVITY_DQ0_DOD_PER_M,
    read_wu_anchor_record_values,
)


def _values() -> dict:
    if not (WU_ANCHOR_RUN_DIR / "checkpoint_manifest.json").is_file():
        pytest.skip("W2 archive missing from this checkout")
    return read_wu_anchor_record_values()


def test_pins_equal_the_archived_record_exactly():
    values = _values()
    assert values["passed"] is True  # only a passing Run A mints
    assert WU_ANCHOR.record_hash == values["record_hash"]
    assert WU_ANCHOR.f_hz == values["f_hz"]
    assert WU_ANCHOR.q0 == values["q0"]
    assert WU_ANCHOR.p_e == values["p_e"]
    assert WU_ANCHOR.v_mode_local_m3 == values["v_mode_local_m3"]
    assert WU_ANCHOR.v_mode_global_m3 == values["v_mode_global_m3"]
    assert WU_ANCHOR.q_diel == values["q_diel"]
    assert WU_ANCHOR.wall_fraction == values["wall_fraction"]


def test_diagnostic_sensitivities_pinned():
    values = _values()
    assert WU_OD_SENSITIVITY_DF_DOD_HZ_PER_M == values["df_dod_hz_per_m"]
    assert WU_OD_SENSITIVITY_DQ0_DOD_PER_M == values["dq0_dod_per_m"]


def test_booth_centre_untouched_by_the_mint():
    """H4 discipline: the Booth pinned centre and its meaning strings
    stay Booth-shaped; the Wu mint must not have re-pointed them."""
    from cavity.sweep.centre_check import (
        GATE_RECORD_HASH,
        PINNED_CENTRE,
        SWEEP_CENTRE_DEFINITION,
    )

    assert GATE_RECORD_HASH == "823e67969516bcf2"
    assert PINNED_CENTRE.record_hash == "823e67969516bcf2"
    assert "823e67969516bcf2" in SWEEP_CENTRE_DEFINITION


def test_anchor_inside_the_ratified_windows():
    """Consistency (not a re-judgment): the pinned values sit inside
    the coded W2 windows the archive was judged by."""
    from cavity.validation.report_w2 import (
        W2_F_REL_TOL,
        W2_F_TARGET_HZ,
        W2_Q0_REL_TOL,
        W2_Q0_TARGET,
        W2_RATIO_TOL,
    )

    assert abs(WU_ANCHOR.f_hz / W2_F_TARGET_HZ - 1.0) <= W2_F_REL_TOL
    assert abs(WU_ANCHOR.q0 / W2_Q0_TARGET - 1.0) <= W2_Q0_REL_TOL
    assert abs(WU_ANCHOR.v_mode_ratio - 1.0) <= W2_RATIO_TOL
