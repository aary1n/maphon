"""The Wu anchor record — pinned import-only values (minted 2026-07-22).

Created by the first W2-PASSING solve, per the design-doc 2026-07-19
addendum and the pre-registered dual-geometry protocol
(`docs/w2_wu_anchor_windows.md`, addendum 2026-07-22 — the 2e19187 O.D.
hold lifted by user decision of 2026-07-22; Run A at the carried print
O.D. binds the gates, Run B at the measured 12.2 mm is DIAGNOSTIC and
mints nothing).

Archive of record (byte-immutable):
`refs/gate_runs/20260722T144737Z_wu_anchor_w2/` — Run A, walls-on
finest impedance arm, record `b8895aa479464763`. No quantity here is
re-derived; the pin test (`tests/test_sweep_wu_anchor.py`) re-reads
the archived manifest and asserts equality.

Sweep-centre definition (design-doc 2026-07-19 addendum, now
satisfiable): *the Wu Phase 1b model (crystal + spacer sub-domains,
`GEOM_WU_STO_RING` nominals, canonical materials) whose no-crystal
limit reproduces the W2-validated Wu anchor* — THIS record is that
anchor. NOTE (hidden coupling H4, unchanged): `cavity.sweep.
centre_check`'s pinned record and meaning strings remain Booth-shaped
and Booth-true; re-pointing its off-arm wiring to this record is its
own dated changeset, not smuggled in here. No training solve may cite
the Booth centre as the Wu sweep centre.

Provenance riders carried by this anchor (verbatim from the session
record; they do NOT dilute the pass, they scope it):
- ring height 8.6 mm via RESOLUTION_Q13 and box height 15 mm (=
  RESOLUTION_Q2 nominal) — in-person caliper values, Oxborrow WRITTEN
  CONFIRMATION PENDING;
- crystal at planning dims/εr (Q11) and a LABELLED PLANNING axial
  placement (Q9 open);
- the O.D. discrepancy (print 12.0 vs measured 12.2 mm) is UNRESOLVED
  two-sided — this anchor is the PRINT-geometry record by
  pre-registration, not a branch selection; the diagnostic
  sensitivities below quantify the stake.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

WU_ANCHOR_RUN_DIR = (
    _REPO_ROOT / "refs" / "gate_runs" / "20260722T144737Z_wu_anchor_w2"
)
WU_ANCHOR_RECORD_HASH = "b8895aa479464763"


@dataclass(frozen=True)
class WuAnchorRecord:
    """Import-only Run A finest walls-on values (W2 PASS, 2026-07-22).

    Full-precision values from the archived manifest's Run A impedance
    finest arm; the W2 verdicts on them are in the same archive's
    `gate_report.json` (W2.4 ratio 1.058353 PASS, W2.1 f −1.26% PASS,
    W2.2 Q0 −0.67% PASS, W2.3 report-only).
    """

    record_hash: str = WU_ANCHOR_RECORD_HASH
    f_hz: float = 1431191793.1351268
    q0: float = 7152.082241591756
    p_e: float = 0.9976927391908201
    v_mode_local_m3: float = 3.4927002837468873e-07
    v_mode_global_m3: float = 3.300129040708165e-07
    q_diel: float = 9111.952214889496
    wall_fraction: float = 0.21508782389082226

    @property
    def v_mode_ratio(self) -> float:
        return self.v_mode_local_m3 / self.v_mode_global_m3


WU_ANCHOR = WuAnchorRecord()

#: Run B DIAGNOSTIC sensitivities (deliverables of the session; they
#: mint no value and select no branch — the O.D. question rides the
#: owed confirmation email).
WU_OD_SENSITIVITY_DF_DOD_HZ_PER_M = -88314431239.66075
WU_OD_SENSITIVITY_DQ0_DOD_PER_M = -247811.9656785332


def read_wu_anchor_record_values() -> dict:
    """Re-read the Run A finest impedance arm from the archived
    manifest (the pin test's source of truth)."""
    manifest = json.loads(
        (WU_ANCHOR_RUN_DIR / "checkpoint_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    finest = manifest["runs"]["run_a"]["arms"]["impedance"]["finest"]
    wall = manifest["runs"]["run_a"]["wall_loss"]
    diag = manifest["diagnostic"]
    return {
        "record_hash": finest["record_hash"],
        "f_hz": finest["f_hz"],
        "q0": finest["q"],
        "p_e": finest["p_e"],
        "v_mode_local_m3": finest["v_mode_local_m3"],
        "v_mode_global_m3": finest["v_mode_global_m3"],
        "q_diel": wall["q_diel"],
        "wall_fraction": wall["wall_fraction"],
        "passed": manifest["verdict"]["passed"],
        "df_dod_hz_per_m": diag["df_dod_hz_per_m"],
        "dq0_dod_per_m": diag["dq0_dod_per_m"],
    }


__all__ = [
    "WU_ANCHOR",
    "WU_ANCHOR_RECORD_HASH",
    "WU_ANCHOR_RUN_DIR",
    "WU_OD_SENSITIVITY_DF_DOD_HZ_PER_M",
    "WU_OD_SENSITIVITY_DQ0_DOD_PER_M",
    "WuAnchorRecord",
    "read_wu_anchor_record_values",
]
