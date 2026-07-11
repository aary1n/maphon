"""SPEC §5 wall-loss split green path.

The re-based §5a record is green (5 pass / 0 fail / 1 deferred;
`refs/gate_runs/20260711T132705Z_rejudge/`).  The judged values below
come from its checkpoint manifest's faithful-wall-loss branch, which
re-judges the immutable archived 2026-07-10 solves.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cavity.provenance import TARGETS


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_RUN_DIR = REPO_ROOT / "refs" / "gate_runs" / "20260710T083340Z_live_comsol"
REJUDGE_MANIFEST = (
    REPO_ROOT
    / "refs"
    / "gate_runs"
    / "20260711T132705Z_rejudge"
    / "checkpoint_manifest.json"
)
FAITHFUL_RECORD_HASH = "2b276c4424e49bb9"
_LFS_POINTER_PREFIX = b"version https://git-lfs"


def _source_archive_or_skip() -> None:
    """Use the standard archived-record LFS guard before judgment."""
    fields_npz = SOURCE_RUN_DIR / "solves" / FAITHFUL_RECORD_HASH / "fields.npz"
    if not fields_npz.is_file():
        pytest.skip(
            f"archived §5a record not present at {fields_npz} — "
            "refs/gate_runs missing from this checkout"
        )
    with fields_npz.open("rb") as fh:
        if fh.read(len(_LFS_POINTER_PREFIX)).startswith(_LFS_POINTER_PREFIX):
            pytest.skip(
                "refs/gate_runs fields.npz is an unsmudged git-lfs pointer — "
                "run `git lfs pull` to materialise the §5a archive"
            )


def test_booth_table_8_wall_loss_split():
    """Archived §5a faithful branch satisfies the Section 4 windows."""
    _source_archive_or_skip()
    manifest = json.loads(REJUDGE_MANIFEST.read_text(encoding="utf-8"))
    wall_loss = manifest["branches"]["faithful"]["wall_loss"]
    q_diel = wall_loss["q_diel"]
    wall_fraction = wall_loss["wall_fraction"]

    assert TARGETS.q_diel_lo <= q_diel <= TARGETS.q_diel_hi
    assert (
        TARGETS.wall_loss_fraction_lo
        <= wall_fraction
        <= TARGETS.wall_loss_fraction_hi
    )
