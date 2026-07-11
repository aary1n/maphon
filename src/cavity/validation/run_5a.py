"""SPEC §5a live checkpoint driver — run once per licence session.

Runs the full §5a solve inventory (2 material branches x 2 wall arms x
5 ladder levels + the printed-2.46 sensitivity solve, cache-deduped),
judges the committed §5 gate windows on the FAITHFUL branch, and
archives everything under `refs/gate_runs/<UTC>_live_comsol/`:

    gate_report.json           §5 gate verdicts (live provider)
    solves/<hash>/...          every §1 SolveRecord (npz via LFS)
    mph/<hash>.mph             finest gated-arm + sensitivity raw models
    checkpoint_manifest.json   structured §5a summary (plain JSON)
    booth_5a_checkpoint.md     rendered checkpoint record (report_5a)

JUDGE discipline (pre-registered): any gated FAIL or a non-asymptotic
ladder (`ConvergenceError`) => the archive is still written, the
rendered record documents the failure, exit code is non-zero, and the
downstream steps (xfail resolution, margin-report rewrite, export
re-mint) MUST NOT run. No geometry retuning, no tolerance widening, no
branch re-picking.

RE-JUDGMENT mode (`--rejudge-from <archived run dir>`, added for the
2026-07-11 V_mode re-base — SPEC §5a finding): re-runs the §5 gate
JUDGMENT over the archived solve records under the CURRENT committed
windows and writes a NEW dated record directory (gate_report.json +
checkpoint_manifest.json + rendered markdown, no solves/ — every
record hash cites the source archive, which is immutable). Needs no
COMSOL licence: every payload is assembled from the archived §1
records (extraction re-runs from persisted raw fields; ladder sigmas
via the cache-hit wall-loss study path). A cache MISS raises out —
a re-judgment must never trigger a solve.

Usage:  python -m cavity.validation.run_5a [--runs-root refs/gate_runs]
                                           [--run-dir <existing dir>]
                                           [--rejudge-from <run dir>]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _rejudge(source: Path, runs_root: Path) -> int:
    """Re-judge an archived §5a run under the current committed windows.

    No COMSOL, no new solves: payloads are assembled from the source
    archive's §1 records (a cache miss raises), and the new record dir
    contains judgments only — every record hash cites the source
    archive. Added 2026-07-11 for the V_mode re-base (SPEC §5a
    finding: window-basis re-derivation per §11 item 8)."""
    import json
    import time

    import numpy as np

    from cavity.extraction import extract
    from cavity.forward_model.persistence import load_solve_record
    from cavity.forward_model.runner import (
        material_spec_for,
        run_forward_model,
        run_wall_loss_study,
    )
    from cavity.forward_model.mesh import refinement_ladder
    from cavity.forward_model.study import EigenStudyConfig, WallBC
    from cavity.provenance import GEOM, GEOM_BOOTH_TE01D, TARGET
    from cavity.validation.gate import run_gate
    from cavity.validation.providers import (
        BOOTH_LADDER_BASE_MESH,
        BOOTH_LADDER_N_LEVELS,
        BOOTH_STUDY_N_MODES,
        EmptyCavityPayload,
        BoothPayload,
        PecLossyPayload,
        ReproducibilityMetadata,
        StaticProvider,
        Unavailable,
        WallLossPayload,
        booth_faithful_materials,
        booth_recovered_geometry,
    )
    from cavity.validation.report import write_gate_report
    from cavity.validation.report_5a import (
        CHECKPOINT_FILENAME,
        build_manifest,
        gate_dict_from_report,
        render_checkpoint_markdown,
        write_manifest,
    )

    src_solves = source / "solves"
    if not src_solves.is_dir():
        print(f"[run_5a] no solves/ under {source}", flush=True)
        return 5
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = runs_root / f"{stamp}_rejudge"
    run_dir.mkdir(parents=True, exist_ok=True)
    pass_date = time.strftime("%Y-%m-%d", time.gmtime())
    print(f"[run_5a] re-judgment record dir: {run_dir}", flush=True)
    print(f"[run_5a] source archive (read-only): {source}", flush=True)

    src_manifest = json.loads(
        (source / "checkpoint_manifest.json").read_text(encoding="utf-8")
    )
    src_gate_report = json.loads(
        (source / "gate_report.json").read_text(encoding="utf-8")
    )

    geom = booth_recovered_geometry()
    study = EigenStudyConfig(
        wall_bc=WallBC.IMPEDANCE,
        search_hz=TARGET.f_design_hz,
        n_modes=BOOTH_STUDY_N_MODES,
    )
    # cache-hit reconstruction (client=None: a miss raises rather than
    # solving — the re-judgment invariant)
    faithful = run_wall_loss_study(
        geom,
        study,
        materials=booth_faithful_materials(),
        base_mesh=BOOTH_LADDER_BASE_MESH,
        n_levels=BOOTH_LADDER_N_LEVELS,
        client=None,
        cache_root=src_solves,
    )
    canonical = run_wall_loss_study(
        geom,
        study,
        materials=None,
        base_mesh=BOOTH_LADDER_BASE_MESH,
        n_levels=BOOTH_LADDER_N_LEVELS,
        client=None,
        cache_root=src_solves,
    )
    finest_mesh = refinement_ladder(
        BOOTH_LADDER_BASE_MESH, BOOTH_LADDER_N_LEVELS
    )[-1]
    sensitivity = run_forward_model(
        booth_recovered_geometry(GEOM_BOOTH_TE01D.printed_minor_radius_m),
        study,
        material_spec_for(study, booth_faithful_materials()),
        finest_mesh,
        client=None,
        cache_root=src_solves,
    )

    # §8 payloads from the archived records
    empty_npz = np.load(src_solves / "empty_cavity_te011.npz")
    empty_payload = EmptyCavityPayload(
        spectrum_f_real_hz=tuple(
            float(f) for f in empty_npz["f_real_hz"]
        ),
        box_radius_m=GEOM.box_radius_m,
        box_height_m=GEOM.box_height_m,
    )
    pec_payload: PecLossyPayload | Unavailable = Unavailable(
        "no archived §8 PEC+lossy record found in the source archive"
    )
    for record_hash in src_gate_report["reproducibility"][
        "solve_record_hashes"
    ]:
        record = load_solve_record(src_solves, record_hash)
        if record is None:
            continue
        if record.fingerprint["geometry"].get("shape") == "puck":
            pec_payload = PecLossyPayload(
                extraction=extract(record.field_sample),
                tan_delta=record.fingerprint["materials"][
                    "sto_tan_delta"
                ],
            )
            break

    booth_finest = faithful.impedance.finest
    provider = StaticProvider(
        kind="rejudged_archive",
        empty_cavity_payload=empty_payload,
        pec_lossy_payload=pec_payload,
        booth_payload=BoothPayload(
            extraction=booth_finest.extraction,
            epsilon_r_real=booth_finest.record.fingerprint["materials"][
                "sto_epsilon_r_real"
            ],
        ),
        wall_loss_payload=WallLossPayload(
            decomposition=faithful.decomposition
        ),
        repro=ReproducibilityMetadata(
            rng_seed=None,
            comsol_version=booth_finest.record.comsol_version,
            mesh_settings=None,
            mesh_element_counts=(),
            solve_record_hashes=tuple(
                src_gate_report["reproducibility"]["solve_record_hashes"]
            ),
            cache_root=str(src_solves),
            notes=(
                f"RE-JUDGMENT of archived run {source.name} under the "
                "current committed windows (SPEC §5a finding "
                "2026-07-11: V window re-based on "
                "BOOTH_IMPLIED_V_MODE_M3, F_m re-scoped to Booth "
                "consistency); no new solves — extraction re-run from "
                "the persisted raw fields; no stochastic stage in the "
                "§5 gate"
            ),
        ),
    )

    report = run_gate(provider)
    out = write_gate_report(report, run_dir=run_dir)
    gate = gate_dict_from_report(report)
    print(
        f"[run_5a] gate report: {out} (n_pass={report.n_pass}, "
        f"n_fail={report.n_fail}, n_deferred={report.n_deferred})",
        flush=True,
    )

    judgment = {
        "mode": "rejudged_from_archive",
        "source_run_dir": source.name,
        "source_git_commit": src_manifest["provenance"]["git_commit"],
        "basis": (
            "SPEC §5a finding 2026-07-11 — booth_two_point/v_mode "
            "window re-based on BOOTH_IMPLIED_V_MODE_M3 (Table 8 "
            "print corrected for the 225/360 partial-revolution "
            "factor, BOOTH_TABLE8_REVOLUTION_FACTOR); F_m row "
            "re-scoped to ±1% consistency vs BOOTH_IMPLIED_F_M "
            "(order-10^7 window moved to the confinement endpoint, "
            "deferred). Window BASIS re-derivation per §11 item 8 — "
            "tolerances unchanged."
        ),
    }
    manifest = build_manifest(
        pass_date=pass_date,
        faithful=faithful,
        canonical=canonical,
        sensitivity=sensitivity,
        gate=gate,
        run_dir_name=run_dir.name,
        comsol_version=booth_finest.record.comsol_version,
        repo_root=_REPO_ROOT,
        judgment=judgment,
    )
    write_manifest(manifest, run_dir)
    (run_dir / CHECKPOINT_FILENAME).write_text(
        render_checkpoint_markdown(manifest),
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[run_5a] checkpoint record: {run_dir / CHECKPOINT_FILENAME}",
        flush=True,
    )

    if gate["n_fail"] > 0:
        failed = [
            c["name"] for c in gate["checks"] if c["status"] == "fail"
        ]
        print(
            "[run_5a] GATED FAIL — checks: " + ", ".join(failed),
            flush=True,
        )
        return 2
    print("[run_5a] GREEN — all live-judged rows pass.", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        default=str(_REPO_ROOT / "refs" / "gate_runs"),
        help="archive root (default: refs/gate_runs)",
    )
    parser.add_argument(
        "--run-dir",
        default=None,
        help=(
            "reuse an existing run directory (resume: solves are "
            "cache-deduped against its solves/)"
        ),
    )
    parser.add_argument(
        "--rebuild-only",
        action="store_true",
        help=(
            "re-mint checkpoint_manifest.json + booth_5a_checkpoint.md "
            "from an existing --run-dir WITHOUT re-solving or "
            "re-judging: every solve must cache-hit against its "
            "solves/, and the gate section is read from the archived "
            "gate_report.json verbatim. Needs no COMSOL licence."
        ),
    )
    parser.add_argument(
        "--rejudge-from",
        default=None,
        help=(
            "re-judge an archived run directory's records under the "
            "CURRENT committed windows into a NEW dated record dir "
            "(no solves, no licence; the source archive is read-only)"
        ),
    )
    args = parser.parse_args(argv)
    if args.rebuild_only and args.run_dir is None:
        parser.error("--rebuild-only requires --run-dir")
    if args.rejudge_from is not None and (
        args.rebuild_only or args.run_dir is not None
    ):
        parser.error(
            "--rejudge-from is exclusive with --rebuild-only/--run-dir"
        )
    if args.rejudge_from is not None:
        return _rejudge(Path(args.rejudge_from), Path(args.runs_root))

    import json

    from cavity.forward_model.convergence import ConvergenceError
    from cavity.forward_model.mesh import refinement_ladder
    from cavity.forward_model.mode_id import ModeIdentificationError
    from cavity.forward_model.runner import (
        material_spec_for,
        run_forward_model,
        run_wall_loss_study,
    )
    from cavity.forward_model.study import EigenStudyConfig, WallBC
    from cavity.provenance import GEOM_BOOTH_TE01D, TARGET
    from cavity.validation.gate import run_gate
    from cavity.validation.providers import (
        BOOTH_LADDER_BASE_MESH,
        BOOTH_LADDER_N_LEVELS,
        BOOTH_STUDY_N_MODES,
        LiveComsolProvider,
        Unavailable,
        booth_faithful_materials,
        booth_recovered_geometry,
    )
    from cavity.validation.report import write_gate_report
    from cavity.validation.report_5a import (
        CHECKPOINT_FILENAME,
        build_manifest,
        gate_dict_from_json,
        gate_dict_from_report,
        render_checkpoint_markdown,
        write_manifest,
    )

    if args.run_dir is not None:
        run_dir = Path(args.run_dir)
    else:
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        run_dir = Path(args.runs_root) / f"{stamp}_live_comsol"
    run_dir.mkdir(parents=True, exist_ok=True)
    solves = run_dir / "solves"
    mph_dir = run_dir / "mph"
    pass_date = time.strftime("%Y-%m-%d", time.gmtime())

    print(f"[run_5a] archive: {run_dir}", flush=True)
    if args.rebuild_only:
        # cache-hits only: build_model is never reached, no licence.
        client = None
    else:
        import mph

        client = mph.start()
    provider = LiveComsolProvider(
        client, solve_root=solves, save_mph_dir=mph_dir
    )

    def _stop_convergence(stage: str, exc: Exception) -> int:
        msg = (
            f"# SPEC §5a FAILURE — {stage} ({pass_date})\n\n"
            "**STOP condition (pre-registered): the mesh ladder is not "
            "in the asymptotic regime or the TE01delta mode could not "
            "be identified — no sigma fabricated, no gate judged on "
            "unconverged numbers.**\n\n"
            f"Exception:\n\n```\n{exc}\n```\n\n"
            f"All §1 SolveRecords produced so far are under `solves/` "
            "in this directory for diagnosis. Downstream steps (xfail "
            "resolution, margin-report rewrite, export re-mint) were "
            "NOT run.\n"
        )
        (run_dir / "failure_report.md").write_text(
            msg, encoding="utf-8", newline="\n"
        )
        print(f"[run_5a] STOP ({stage}): {exc}", flush=True)
        return 3

    geom = booth_recovered_geometry()
    study = EigenStudyConfig(
        wall_bc=WallBC.IMPEDANCE,
        search_hz=TARGET.f_design_hz,
        n_modes=BOOTH_STUDY_N_MODES,
    )

    # --- 1. the gate (faithful branch drives the Booth rows) ----------
    if args.rebuild_only:
        gate = gate_dict_from_json(
            json.loads(
                (run_dir / "gate_report.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        print(
            "[run_5a] rebuild-only: gate verdicts read from the "
            "archived gate_report.json "
            f"(n_pass={gate['n_pass']}, n_fail={gate['n_fail']}, "
            f"n_deferred={gate['n_deferred']})",
            flush=True,
        )
        try:
            faithful = run_wall_loss_study(
                geom,
                study,
                materials=booth_faithful_materials(),
                base_mesh=BOOTH_LADDER_BASE_MESH,
                n_levels=BOOTH_LADDER_N_LEVELS,
                client=client,
                cache_root=solves,
            )
        except (ConvergenceError, ModeIdentificationError) as exc:
            return _stop_convergence("rebuild / faithful ladder", exc)
    else:
        print("[run_5a] running §5 gate (faithful branch ladder)...",
              flush=True)
        try:
            report = run_gate(provider)
        except (ConvergenceError, ModeIdentificationError) as exc:
            return _stop_convergence("gate / faithful ladder", exc)
        out = write_gate_report(report, run_dir=run_dir)
        gate = gate_dict_from_report(report)
        print(f"[run_5a] gate report: {out} (n_pass={report.n_pass}, "
              f"n_fail={report.n_fail}, "
              f"n_deferred={report.n_deferred})",
              flush=True)

        faithful = provider.booth_study
        if faithful is None:
            booth = provider.booth_walls_on()
            reason = (
                booth.reason
                if isinstance(booth, Unavailable)
                else "unknown"
            )
            print(f"[run_5a] Booth study unavailable: {reason}",
                  flush=True)
            return 4

    # --- 2. canonical companion branch --------------------------------
    print("[run_5a] running canonical companion branch ladder...",
          flush=True)
    try:
        canonical = run_wall_loss_study(
            geom,
            study,
            materials=None,  # canonical SPEC §2 STO (tan_delta 1.1e-4)
            base_mesh=BOOTH_LADDER_BASE_MESH,
            n_levels=BOOTH_LADDER_N_LEVELS,
            client=client,
            cache_root=solves,
        )
    except (ConvergenceError, ModeIdentificationError) as exc:
        return _stop_convergence("canonical ladder", exc)

    # --- 3. printed-2.46 sensitivity solve (faithful, walls-on,
    #        finest mesh) ----------------------------------------------
    print("[run_5a] running printed-2.46 sensitivity solve...",
          flush=True)
    finest_mesh = refinement_ladder(
        BOOTH_LADDER_BASE_MESH, BOOTH_LADDER_N_LEVELS
    )[-1]
    sens_geom = booth_recovered_geometry(
        GEOM_BOOTH_TE01D.printed_minor_radius_m
    )
    try:
        sensitivity = run_forward_model(
            sens_geom,
            study,
            material_spec_for(study, booth_faithful_materials()),
            finest_mesh,
            client=client,
            cache_root=solves,
            save_mph_dir=mph_dir,
        )
    except (ConvergenceError, ModeIdentificationError) as exc:
        return _stop_convergence("sensitivity solve", exc)

    # --- 4. manifest + rendered checkpoint record ----------------------
    manifest = build_manifest(
        pass_date=pass_date,
        faithful=faithful,
        canonical=canonical,
        sensitivity=sensitivity,
        gate=gate,
        run_dir_name=run_dir.name,
        comsol_version=faithful.impedance.finest.record.comsol_version,
        repo_root=_REPO_ROOT,
    )
    write_manifest(manifest, run_dir)
    (run_dir / CHECKPOINT_FILENAME).write_text(
        render_checkpoint_markdown(manifest),
        encoding="utf-8",
        newline="\n",
    )
    print(f"[run_5a] checkpoint record: {run_dir / CHECKPOINT_FILENAME}",
          flush=True)

    # --- 5. JUDGE ------------------------------------------------------
    if gate["n_fail"] > 0:
        failed = [
            c["name"] for c in gate["checks"] if c["status"] == "fail"
        ]
        print(
            "[run_5a] GATED FAIL — checks: "
            + ", ".join(failed)
            + ". Archive written; downstream steps MUST NOT run "
            "(pre-registered failure discipline).",
            flush=True,
        )
        return 2

    print("[run_5a] GREEN — all live-judged rows pass.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
