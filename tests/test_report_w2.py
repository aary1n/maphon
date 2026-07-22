"""W2 session record — regeneration pin (CI tier, no COMSOL).

The committed `wu_anchor_w2.md` must be exactly what
`render_w2_markdown` produces from the committed
`checkpoint_manifest.json` — both plain JSON/markdown, so this pin
needs neither a licence nor LFS content. The manifest records the
runtime facts (git commit at solve time, COMSOL version, the declared
ladder deviation); the renderer invents none.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cavity.validation.report_w2 import (
    W2_GATE_REPORT_FILENAME,
    W2_MANIFEST_FILENAME,
    W2_MANIFEST_SCHEMA_VERSION,
    W2_RECORD_FILENAME,
    render_from_run_dir,
    render_w2_markdown,
)

W2_RUN_DIR = (
    Path(__file__).resolve().parent.parent
    / "refs"
    / "gate_runs"
    / "20260722T144737Z_wu_anchor_w2"
)
W2_STOPPED_RUN_DIR = W2_RUN_DIR.parent / "20260722T144256Z_wu_anchor_w2"


def _manifest() -> dict:
    path = W2_RUN_DIR / W2_MANIFEST_FILENAME
    if not path.is_file():
        pytest.skip(
            f"W2 manifest not present at {path} — refs/gate_runs "
            "missing from this checkout"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_schema_and_identity():
    manifest = _manifest()
    assert manifest["schema_version"] == W2_MANIFEST_SCHEMA_VERSION
    assert manifest["kind"] == "wu_anchor_w2"
    assert manifest["run_dir"] == W2_RUN_DIR.name
    for run in ("run_a", "run_b"):
        arms = manifest["runs"][run]["arms"]
        for arm in ("impedance", "pec"):
            assert len(arms[arm]["levels"]) == 5
            assert arms[arm]["finest"]["record_hash"]
    # the ladder shift is a DECLARED deviation, never silent
    assert len(manifest["deviations"]) == 1
    assert "DECLARED DEVIATION" in manifest["deviations"][0]


def test_record_regenerates_byte_identical():
    manifest = _manifest()
    committed = (W2_RUN_DIR / W2_RECORD_FILENAME).read_text(
        encoding="utf-8"
    )
    assert committed == render_w2_markdown(manifest)
    assert committed == render_from_run_dir(W2_RUN_DIR)


def test_verdict_pins():
    """The archived verdicts, exact: Run A passed every gated row in
    the pre-registered order (W2.4 first); Run B judged nothing."""
    manifest = _manifest()
    v = manifest["verdict"]
    assert v["passed"] is True
    assert v["w2_4_ok"] is True
    assert (v["n_fail"], v["n_not_judged"]) == (0, 0)
    names = [c["name"] for c in v["checks"]]
    assert names == [
        "W2.4/v_mode_local_over_global",
        "W2.1/f",
        "W2.2/q0",
        "W2.3/v_mode_local",
    ]
    statuses = {c["name"]: c["status"] for c in v["checks"]}
    assert statuses["W2.3/v_mode_local"] == "report_only"
    # gate_report.json carries the same verdict block verbatim
    gate = json.loads(
        (W2_RUN_DIR / W2_GATE_REPORT_FILENAME).read_text(encoding="utf-8")
    )
    assert gate["verdict"] == v


def test_run_b_minted_nothing():
    """Run B is diagnostic: its role string says so and no verdict row
    references it — the O.D. discrepancy stays unresolved two-sided."""
    manifest = _manifest()
    assert manifest["runs"]["run_b"]["role"] == "DIAGNOSTIC"
    assert manifest["runs"]["run_a"]["role"] == "GATED"
    # carried print unchanged in the geometry the gates bound
    assert manifest["runs"]["run_a"]["sto_outer_radius_m"] == 6.0e-3
    assert manifest["runs"]["run_b"]["sto_outer_radius_m"] == 6.1e-3


def test_stopped_attempt_failure_record_stands():
    """The refused first attempt keeps its failure record (byte-kept;
    the STOP is part of the session's committed history)."""
    report = W2_STOPPED_RUN_DIR / "failure_report.md"
    if not report.is_file():
        pytest.skip("stopped-attempt archive missing from this checkout")
    text = report.read_text(encoding="utf-8")
    assert "STOP condition" in text
    assert "asymptotic" in text
