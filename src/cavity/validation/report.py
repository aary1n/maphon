"""SPEC §5 gate report — JSON artifact under `runs/` (SPEC §1).

Artifact scheme:

    runs/gate/<UTCstamp>_<provider-kind>/
        gate_report.json    # this module
        solves/             # raw eigen-solutions, when a live solve
                            # actually ran (persisted by the provider
                            # through the existing §1 machinery — no
                            # parallel format)

`runs/` is deliberately gitignored (see .gitignore: solves are re-run
from code, not committed); reports carry the SPEC §1 reproducibility
block (rng seed, COMSOL version, mesh settings, element counts, solve
record hashes) so any number in them can be traced to a re-runnable
solve.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from cavity.validation.gate import (
    GateCheckResult,
    GateReport,
    GateRowResult,
)

REPORT_FILENAME = "gate_report.json"


def _jsonify(value: Any) -> Any:
    """Coerce numpy scalars and containers to JSON-native types."""
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _check_to_dict(check: GateCheckResult) -> dict:
    return {
        "name": check.name,
        "row_id": check.row_id,
        "target": check.target,
        "target_value": _jsonify(check.target_value),
        "measured": _jsonify(check.measured),
        "window": {
            "lo": _jsonify(check.window.lo),
            "hi": _jsonify(check.window.hi),
        },
        "status": check.status.value,
        "margin": _jsonify(check.margin),
        "inputs": _jsonify(check.inputs),
        "provenance": check.provenance,
        "tolerance_rationale": check.tolerance_rationale,
        "notes": check.notes,
    }


def _row_to_dict(row: GateRowResult) -> dict:
    return {
        "row_id": row.row_id,
        "check": row.check_text,
        "target": row.target_text,
        "source": row.source_text,
        "status": row.status.value,
        "checks": [_check_to_dict(c) for c in row.checks],
    }


def report_to_dict(report: GateReport) -> dict:
    return {
        "schema_version": report.schema_version,
        "created_at_utc": report.created_at_utc,
        "provider_kind": report.provider_kind,
        "phase1_complete": report.phase1_complete,
        "n_pass": report.n_pass,
        "n_fail": report.n_fail,
        "n_deferred": report.n_deferred,
        "rows": [_row_to_dict(r) for r in report.rows],
        "reproducibility": _jsonify(asdict(report.reproducibility)),
    }


def create_run_dir(
    runs_root: Path, provider_kind: str, *, _now: float | None = None
) -> Path:
    """Timestamped, collision-safe run directory under
    `<runs_root>/gate/` (Windows-safe stamp: no colons)."""
    stamp = time.strftime(
        "%Y%m%dT%H%M%SZ",
        time.gmtime(_now if _now is not None else time.time()),
    )
    base = Path(runs_root) / "gate" / f"{stamp}_{provider_kind}"
    run_dir = base
    suffix = 2
    while run_dir.exists():
        run_dir = base.with_name(f"{base.name}-{suffix}")
        suffix += 1
    run_dir.mkdir(parents=True)
    return run_dir


def write_gate_report(
    report: GateReport,
    runs_root: Path = Path("runs"),
    *,
    run_dir: Path | None = None,
) -> Path:
    """Write `gate_report.json`; returns the file path.

    Pass `run_dir` when the directory was pre-created (e.g. so a live
    provider could persist its solves under `<run_dir>/solves` before
    the report is written); otherwise a fresh timestamped directory is
    created under `<runs_root>/gate/`.
    """
    if run_dir is None:
        run_dir = create_run_dir(runs_root, report.provider_kind)
    else:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / REPORT_FILENAME
    out.write_text(
        json.dumps(report_to_dict(report), indent=2), encoding="utf-8"
    )
    return out


__all__ = [
    "REPORT_FILENAME",
    "create_run_dir",
    "report_to_dict",
    "write_gate_report",
]
