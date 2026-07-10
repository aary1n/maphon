"""SPEC §5a checkpoint record — regeneration pin (CI tier, no COMSOL).

The committed `booth_5a_checkpoint.md` must be exactly what
`render_checkpoint_markdown` produces from the committed
`checkpoint_manifest.json` — both plain JSON/markdown, so this pin
needs neither a licence nor LFS content. The manifest records the
runtime facts (git commit at solve time, COMSOL version); the renderer
invents none.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cavity.validation.report_5a import (
    CHECKPOINT_FILENAME,
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    render_checkpoint_markdown,
)

RUN_5A_DIR = (
    Path(__file__).resolve().parent.parent
    / "refs"
    / "gate_runs"
    / "20260710T083340Z_live_comsol"
)


def _manifest() -> dict:
    path = RUN_5A_DIR / MANIFEST_FILENAME
    if not path.is_file():
        pytest.skip(
            f"§5a checkpoint manifest not present at {path} — "
            "refs/gate_runs missing from this checkout"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_schema_and_identity():
    manifest = _manifest()
    assert manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["kind"] == "booth_5a_checkpoint"
    assert manifest["run_dir"] == RUN_5A_DIR.name
    # both branches present with both arms and full ladders
    for branch in ("faithful", "canonical"):
        arms = manifest["branches"][branch]["arms"]
        for arm in ("impedance", "pec"):
            assert len(arms[arm]["levels"]) == 5
            assert arms[arm]["finest"]["record_hash"]


def test_checkpoint_record_regenerates_byte_identical():
    manifest = _manifest()
    committed = (RUN_5A_DIR / CHECKPOINT_FILENAME).read_text(
        encoding="utf-8"
    )
    assert committed == render_checkpoint_markdown(manifest)
