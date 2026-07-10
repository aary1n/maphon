"""SPEC §5 validation gate row for the wall-loss split.

The §5 table requires:
  Q_diel in [9_000, 10_000] and wall_fraction in [0.23, 0.27] at
  Booth's published geometry.

STATUS AFTER THE 2026-07-10 §5a PASS (red; failure record:
refs/gate_runs/20260710T083340Z_live_comsol/booth_5a_checkpoint.md):
the live §4 split at the RECOVERED Booth TE01δ geometry
(refs/booth_geometry_recovery.md — the old "1.82×-scaled variant"
reading of the supervisor .mph was a misidentification, corrected
there) landed INSIDE both windows (Q_diel = 9511.5, wall fraction =
0.26601, faithful branch). But the §5a pass as a whole is a GATED
FAIL (V_mode global-max ×1.60 high; F_m below 1e7 as its arithmetic
consequence), and the pre-registered failure discipline forbids the
green-path rewrite of this test: the xfail STAYS until a green §5a
pass licenses loading the archived records and asserting the TARGETS
windows here. The live verdicts themselves are already pinned in the
requires_comsol tier (test_gate_comsol.py re-judges the frozen
records through the live gate path).

The marker remains strict=True: this placeholder body always raises,
and the reason above records exactly what unblocks it.
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(
    strict=True,
    reason=(
        "§5a 2026-07-10 run is a GATED FAIL (V_mode/F_m; failure "
        "record refs/gate_runs/20260710T083340Z_live_comsol/"
        "booth_5a_checkpoint.md) — the wall-loss split itself landed "
        "inside both §4 windows (Q_diel = 9511.5, wall fraction = "
        "0.26601), but the pre-registered failure discipline forbids "
        "the green-path rewrite until a §5a pass is green. When it "
        "is: remove this xfail and rewrite to load the archived §5a "
        "records (load_solve_record on the committed run dir, "
        "skip-if-LFS-pointer) and assert "
        "TARGETS.q_diel_lo <= Q_diel <= TARGETS.q_diel_hi and "
        "TARGETS.wall_loss_fraction_lo <= wall_fraction <= "
        "TARGETS.wall_loss_fraction_hi."
    ),
)
def test_booth_table_8_wall_loss_split():
    """SPEC §5 row: Q_diel ~ 9-10k, wall fraction 23-27% at Booth."""
    raise NotImplementedError(
        "SPEC §5 wall-loss gate row: green-path rewrite blocked by the "
        "2026-07-10 §5a GATED FAIL (see the xfail reason and "
        "refs/gate_runs/20260710T083340Z_live_comsol/)."
    )
