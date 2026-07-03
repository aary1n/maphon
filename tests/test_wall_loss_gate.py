"""SPEC §5 validation gate row for the wall-loss split.

The §5 table requires:
  Q_diel in [9_000, 10_000] and wall_fraction in [0.23, 0.27] at
  Booth's published geometry.

This is the numerical gate that closes SPEC §11 gap #1 from the
physics side. It depends on Booth's published-paper .mph (currently
outstanding) plus the §2 forward-model build/solve being live. The
supervisor .mph already in `refs/comsol/booth/` is the 1.82x-scaled
torus variant; running §4 on that is a smoke-test of the protocol,
not a gate against Booth Table 8.

The test is marked xfail with strict=True: when paper-geom arrives
and §4 lands inside both intervals, the xfail becomes an UNEXPECTED
PASS and pytest will flag it, prompting removal of the marker and
wiring the real assertion. Without strict=True an actual pass would
be silently absorbed by the xfail and the gate would still read as
"pending" long after it had passed.
"""

from __future__ import annotations

import pytest


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Pending Booth published-paper .mph geometry (SPEC §11 gap #1). "
        "The supervisor .mph in refs/comsol/booth/ is the 1.82x-scaled "
        "torus variant; it is a smoke-test of the §4 protocol, not a "
        "numerical gate against Booth Table 8. When paper-geom arrives, "
        "remove this xfail and wire decompose_wall_loss against the "
        "two-solve outputs, asserting "
        "TARGETS.q_diel_lo <= Q_diel <= TARGETS.q_diel_hi and "
        "TARGETS.wall_loss_fraction_lo <= wall_fraction <= "
        "TARGETS.wall_loss_fraction_hi."
    ),
)
def test_booth_table_8_wall_loss_split():
    """SPEC §5 row: Q_diel ~ 9-10k, wall fraction 23-27% at Booth."""
    raise NotImplementedError(
        "SPEC §5 wall-loss gate: requires Booth published-paper .mph "
        "and the §2 forward-model build/solve to be live. See SPEC "
        "§11 gap #1 and refs/comsol/README.md."
    )
