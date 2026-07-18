"""L2 sweep driver — per-draw pipeline + RAW training-row store + CLI.

Per draw: geometry build → eigensolve (backend) → schema-v1 bundle
(`cavity.export.writer.export_bundle`) → RAW summary-row extraction per
`REQUIRED_SUMMARY_KEYS` → append to `raw_rows.jsonl`.

THE ROW STORE IS RAW SCHEMA-v1 QUANTITIES ONLY (design doc §5,
law-agnosticism): a row carries exactly the REQUIRED_SUMMARY_KEYS
columns plus design/audit metadata (θ, block, seed, row hash, bundle
path). No derived quantity — κc, C₀, Δf_max, anything composed — may
enter a raw row; the writer enforces this with an allowlist AND an
explicit derived-key deny-list, and refuses loudly. Derived artifacts
live in `cavity.sweep.compose`'s separate namespace, carrying their
composition conventions alongside the values.

CLI (python -m cavity.sweep.driver):
  --mock    dry-run tier — full pipeline shape end to end on a small
            mock design (bundles → raw rows → composed derived rows →
            PCE fit → composed-space CV-gate report → R4 projection
            report). Zero COMSOL. Mock designs can never become
            solve-ready (enforced upstream).
  --comsol  the licensed path: constructs ComsolBackend, whose
            constructor enforces the Q2/Q9/Q11 gate — today this
            REFUSES, by design, naming the unresolved questions.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from cavity.export.schema import REQUIRED_SUMMARY_KEYS, META_FILENAME
from cavity.export.writer import export_bundle
from cavity.forward_model.persistence import utc_timestamp
from cavity.provenance import GEOM_WU_STO_RING
from cavity.sweep.backend import (
    ComsolBackend,
    DrawSolveSpec,
    MockBackend,
    SolveBackend,
    draw_solve_spec,
)
from cavity.sweep.design import (
    DesignBlock,
    DesignMatrix,
    generate_design,
)
from cavity.sweep.dofs import (
    DesignMode,
    ResolutionContext,
    UnresolvedTodoTraceError,
    mock_resolutions,
)

RAW_ROWS_FILENAME = "raw_rows.jsonl"
DESIGN_MANIFEST_FILENAME = "design_manifest.json"
BUNDLES_DIRNAME = "bundles"

#: Design/audit keys a raw row carries alongside the schema columns.
DESIGN_ROW_KEYS = (
    "design_mode",
    "design_block",
    "design_seed",
    "design_draw_index",
    "design_row_hash",
    "design_mock",
    "bundle_dir",
)

_THETA_KEY_PATTERN = re.compile(r"^theta_[a-z0-9_]+$")

#: Derived quantities that must NEVER appear in a raw row. The
#: allowlist below already excludes them; this explicit list exists so
#: the refusal can say WHY (law-agnosticism, design doc §5), and so a
#: future summary-key addition cannot silently legitimise one.
DERIVED_KEY_DENYLIST = (
    "kappa_c",
    "kappa_c_hz",
    "kappa_s",
    "kappa_s_hz",
    "q_loaded",
    "q_l",
    "c0",
    "c0_anchored",
    "cooperativity",
    "g2",
    "g2_relative",
    "g2_absolute",
    "delta_f_max_hz",
    "delta_t_max_k",
    "p_max_w",
)


class RawRowContractError(ValueError):
    """A raw row violated the raw-only contract (message says how)."""


def validate_raw_row(row: dict) -> None:
    """Allowlist + deny-list enforcement for one raw row."""
    for key in row:
        if key.lower() in DERIVED_KEY_DENYLIST:
            raise RawRowContractError(
                f"derived quantity {key!r} refused in a RAW training "
                "row: rows store raw schema-v1 quantities ONLY (design "
                "doc §5 law-agnosticism); compose it downstream in "
                "cavity.sweep.compose's derived namespace"
            )
        if (
            key not in REQUIRED_SUMMARY_KEYS
            and key not in DESIGN_ROW_KEYS
            and not _THETA_KEY_PATTERN.match(key)
        ):
            raise RawRowContractError(
                f"key {key!r} is outside the raw-row contract "
                "(REQUIRED_SUMMARY_KEYS + design/audit keys + theta_*)"
            )
    missing = [k for k in REQUIRED_SUMMARY_KEYS if k not in row]
    if missing:
        raise RawRowContractError(
            f"raw row missing schema columns: {missing}"
        )
    for key in DESIGN_ROW_KEYS:
        if key not in row:
            raise RawRowContractError(f"raw row missing audit key {key!r}")


def append_raw_row(path: Path, row: dict) -> None:
    validate_raw_row(row)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def load_raw_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    for row in rows:
        validate_raw_row(row)
    return rows


@dataclass(frozen=True)
class SweepRunResult:
    out_root: Path
    raw_rows_path: Path
    manifest_path: Path
    bundle_dirs: tuple[Path, ...]
    n_rows: int


def run_sweep(
    design: DesignMatrix,
    backend: SolveBackend,
    out_root: Path,
    *,
    context: ResolutionContext | None = None,
) -> SweepRunResult:
    """Run every design row through the per-draw pipeline.

    Mock designs route through `mock_rows()` (shape tier); real designs
    require `context` and pass the Q2/Q9/Q11 gate in `solve_rows`.
    """
    if design.any_mock:
        rows = design.mock_rows()
    else:
        if context is None:
            raise ValueError(
                "a real (non-mock) design needs its ResolutionContext "
                "so solve_rows can apply the Q2/Q9/Q11 gate"
            )
        rows = design.solve_rows(context)

    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / DESIGN_MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(
            {
                "design": design.manifest(),
                "backend": type(backend).__name__,
                "started_at_utc": utc_timestamp(),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    raw_rows_path = out_root / RAW_ROWS_FILENAME
    if raw_rows_path.exists():
        raw_rows_path.unlink()  # a run owns its row file

    bundle_dirs: list[Path] = []
    for row in rows:
        theta = row["theta"]
        # Explicit fallback: harmless in d = 8 (θ carries p_tune, which
        # wins), load-bearing in DEGRADED_D7 and mock dry-runs — the
        # as-operated internal height, never a silent module default.
        spec: DrawSolveSpec = draw_solve_spec(
            theta,
            box_height_fallback_m=(
                GEOM_WU_STO_RING.box_internal_height_asoperated_m
            ),
        )
        result = backend.solve(spec)
        bundle_dir = (
            out_root / BUNDLES_DIRNAME / row["row_hash"]
        )
        export_bundle(result.record, bundle_dir)
        meta = json.loads(
            (bundle_dir / META_FILENAME).read_text(encoding="utf-8")
        )
        summary = meta["summary"]
        raw_row = {
            key: summary[key] for key in REQUIRED_SUMMARY_KEYS
        }
        raw_row.update(
            {
                "design_mode": design.mode.value,
                "design_block": design.block.value,
                "design_seed": design.seed,
                "design_draw_index": row["draw_index"],
                "design_row_hash": row["row_hash"],
                "design_mock": design.any_mock,
                "bundle_dir": str(
                    bundle_dir.relative_to(out_root)
                ).replace("\\", "/"),
            }
        )
        raw_row.update(
            {f"theta_{name}": float(v) for name, v in theta.items()}
        )
        append_raw_row(raw_rows_path, raw_row)
        bundle_dirs.append(bundle_dir)

    return SweepRunResult(
        out_root=out_root,
        raw_rows_path=raw_rows_path,
        manifest_path=manifest_path,
        bundle_dirs=tuple(bundle_dirs),
        n_rows=len(bundle_dirs),
    )


# ---------------------------------------------------------------------------
# Dry-run tier (the L2 requirement: full pipeline shape, zero COMSOL)
# ---------------------------------------------------------------------------


def run_mock_dry_run(
    out_root: Path,
    *,
    mode: DesignMode = DesignMode.BASELINE_D8,
    n_training: int = 24,
    n_held_out: int = 8,
    seed: int = 20260715,
) -> dict:
    """End-to-end dry run: mock sweep → raw rows → derived rows → PCE
    → composed-space CV-gate report → R4 projection report.

    Everything it writes is labelled mock; the gate report is exercise
    of the machinery, not a statement about any surrogate. Returns the
    dry-run report (also written to `dry_run_report.json`).
    """
    # Deferred imports: orchestration only — keeps sweep/surrogate
    # module graphs acyclic.
    from cavity.surrogate.cv_gate import GateThresholds, evaluate_cv_gate
    from cavity.surrogate.pce import PCESurrogate
    from cavity.sweep.compose import (
        AnchorPoint,
        compose_derived_rows,
        projection_invariance_report,
        write_derived_rows,
    )

    import numpy as np

    ctx = mock_resolutions()
    out_root = Path(out_root)
    train = generate_design(
        mode, DesignBlock.TRAINING, ctx, seed=seed, n_draws=n_training
    )
    held = generate_design(
        mode, DesignBlock.HELD_OUT, ctx, seed=seed + 1, n_draws=n_held_out
    )
    backend = MockBackend()
    train_run = run_sweep(train, backend, out_root / "training")
    held_run = run_sweep(held, backend, out_root / "held_out")

    train_rows = load_raw_rows(train_run.raw_rows_path)
    held_rows = load_raw_rows(held_run.raw_rows_path)

    # Anchor: mock bundles are fallback-mask (pre-Phase 1b), so the
    # anchor is constructible only through the diagnostic override —
    # exactly the honest path for a dry run.
    anchor = AnchorPoint.from_raw_row(
        train_rows[0], diagnostic_only=True
    )
    derived_path = out_root / "derived_rows.jsonl"
    derived = compose_derived_rows(
        train_rows + held_rows, anchor=anchor
    )
    write_derived_rows(derived_path, derived)

    # Raw-basis surrogates (Q7): f, ln Q0, ln eta_H, p_e over θ.
    dims = train.dims
    order = 2 if len(train_rows) > len(dims) * (len(dims) + 3) // 2 else 1
    x_train = np.array(
        [[r[f"theta_{d.name}"] for d in dims] for r in train_rows]
    )
    x_held = np.array(
        [[r[f"theta_{d.name}"] for d in dims] for r in held_rows]
    )
    outputs = {
        "f_hz": lambda r: r["f_real_hz"],
        "ln_q0": lambda r: np.log(r["q"]),
        "ln_eta_h": lambda r: np.log(r["magnetic_filling_factor"]),
        "p_e": lambda r: r["p_e"],
    }
    surrogates = {}
    predictions = {}
    for name, getter in outputs.items():
        y = np.array([getter(r) for r in train_rows])
        s = PCESurrogate.fit(dims, x_train, y, order=order)
        surrogates[name] = s
        predictions[name] = s.predict(x_held)

    gate = evaluate_cv_gate(
        truth_rows=held_rows,
        f_pred_hz=predictions["f_hz"],
        ln_q0_pred=predictions["ln_q0"],
        ln_eta_h_pred=predictions["ln_eta_h"],
        anchor=anchor,
        thresholds=GateThresholds(),
    )

    corner_bundles = [
        train_run.bundle_dirs[0],
        train_run.bundle_dirs[-1],
        held_run.bundle_dirs[0],
        held_run.bundle_dirs[-1],
    ]
    r4 = projection_invariance_report(
        corner_bundles, escalation_threshold=GateThresholds().delta_f_max_frac_of_p5
    )

    report = {
        "tier": "MOCK DRY RUN — pipeline shape only, zero COMSOL",
        "mode": mode.value,
        "n_training": len(train_rows),
        "n_held_out": len(held_rows),
        "pce_order": order,
        "pce_q2": {k: s.q2 for k, s in surrogates.items()},
        "cv_gate": gate,
        "r4_projection_invariance": r4,
        "derived_rows_path": str(derived_path),
    }
    (out_root / "dry_run_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cavity.sweep.driver",
        description=(
            "Layer A sweep driver. --mock runs the zero-COMSOL dry-run "
            "tier; --comsol is the licensed path and REFUSES while the "
            "Q2/Q9/Q11 sentinels are unresolved (by design)."
        ),
    )
    tier = parser.add_mutually_exclusive_group(required=True)
    tier.add_argument("--mock", action="store_true")
    tier.add_argument("--comsol", action="store_true")
    parser.add_argument(
        "--mode", choices=["d8", "d7"], default="d8",
        help="baseline d=8 (θ,p) or the recorded d=7 degraded fallback",
    )
    parser.add_argument("--n", type=int, default=24,
                        help="mock training draws (mock tier only)")
    parser.add_argument("--n-held-out", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    mode = (
        DesignMode.BASELINE_D8 if args.mode == "d8"
        else DesignMode.DEGRADED_D7
    )

    if args.comsol:
        try:
            ComsolBackend(ResolutionContext(), mode)
        except UnresolvedTodoTraceError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        # Unreachable until Q2/Q9/Q11 resolve AND Phase 1b geometry
        # exists (SPEC §5b); the licensed sweep is a later pass.
        print(
            "ComsolBackend constructed — licensed sweep wiring is a "
            "later pass.",
            file=sys.stderr,
        )
        return 0

    out = args.out or (
        _repo_root()
        / "runs"
        / "layer_a"
        / f"{utc_timestamp().replace(':', '')}_mock_dryrun"
    )
    report = run_mock_dry_run(
        out,
        mode=mode,
        n_training=args.n,
        n_held_out=args.n_held_out,
        seed=args.seed,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
