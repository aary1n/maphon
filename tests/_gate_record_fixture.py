"""Shared access to the frozen 2026-07-06 gate SolveRecord (LFS npz).

Underscore-prefixed so pytest does not collect this file. The frozen
licence-session artifact refs/gate_runs/20260706T211615Z_live_comsol
(SPEC §8 / `ExtractionTolerances` citation) is git-tracked with the npz
routed through Git LFS, so a clone without `git lfs pull` holds a text
pointer instead of the archive: tests that consume the record must skip
with a clear reason in that case, not fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cavity.forward_model.persistence import SolveRecord, load_solve_record

GATE_RUN_DIR = (
    Path(__file__).resolve().parent.parent
    / "refs"
    / "gate_runs"
    / "20260706T211615Z_live_comsol"
)
GATE_SOLVES_ROOT = GATE_RUN_DIR / "solves"
GATE_RECORD_HASH = "888536d768e0fba1"

# p_e recorded in gate_report.json analytic_benchmark/pec_lossy_q inputs
# (the "0.9977" of provenance/constants.py prose, full precision).
GATE_P_E = 0.9976566720273174

_LFS_POINTER_PREFIX = b"version https://git-lfs"


def gate_record_or_skip() -> SolveRecord:
    """Load the frozen gate SolveRecord, or skip with the exact reason."""
    fields_npz = GATE_SOLVES_ROOT / GATE_RECORD_HASH / "fields.npz"
    if not fields_npz.is_file():
        pytest.skip(
            f"frozen gate record not present at {fields_npz} — "
            "refs/gate_runs missing from this checkout"
        )
    with open(fields_npz, "rb") as fh:
        head = fh.read(len(_LFS_POINTER_PREFIX))
    if head.startswith(_LFS_POINTER_PREFIX):
        pytest.skip(
            "refs/gate_runs fields.npz is an unsmudged git-lfs pointer — "
            "run `git lfs pull` to materialise the frozen gate record"
        )
    record = load_solve_record(GATE_SOLVES_ROOT, GATE_RECORD_HASH)
    if record is None:
        pytest.skip(
            "frozen gate record failed to load (incomplete or "
            "schema-mismatched) — re-fetch refs/gate_runs"
        )
    return record
