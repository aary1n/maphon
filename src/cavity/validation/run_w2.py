"""W2 Wu-anchor live session driver — dual-geometry protocol (2026-07-22).

Runs the first solve of the Phase 1b Wu-ring model (crystal + spacer
sub-domains) against the ratified acceptance windows in
`docs/w2_wu_anchor_windows.md`, under the dual-geometry protocol
PRE-REGISTERED in that document's 2026-07-22 addendum (committed before
any solve; the 2e19187 O.D. hold lifted by user decision of 2026-07-22):

  Run A — print O.D. 12.0 mm (the carried value) — binds the W2 gates.
  Run B — measured O.D. 12.2 mm — DIAGNOSTIC only: quantifies the f and
          Q0 sensitivity to the O.D. discrepancy; no anchor, no branch.

Each run is a §4 wall-loss study (Impedance + PEC arms, 5-level sqrt(2)
mesh ladder ending at the validated finest level) so Q0, Q_diel and the
wall fraction come with ladder sigmas. Judgment order is pre-registered:
W2.4 (v_mode local/global convention check — the 225/360 lesson) FIRST;
on a W2.4 failure the session STOPS before any window comparison (Run B
is not solved, the archive + failure record are still written).

Archive: `refs/gate_runs/<UTC>_wu_anchor_w2/` in the §4.4 shape —
gate_report.json, solves/<hash>/, mph/<hash>.mph (finest arms),
checkpoint_manifest.json, wu_anchor_w2.md (rendered by the committed
generator `report_w2`, byte-pinned once committed).

Preconditions (enforced here, refusing loudly; the sweep gate is NOT
this gate and is untouched — hidden coupling H3): Q13 and Q11 resolved
with non-mock ratified resolutions. Q2 is not a precondition (the W2
doc does not require it); the box height is the recorded as-operated
nominal, which is also RESOLUTION_Q2's nominal. This module never
reads `STO_HEIGHT_FORK.evidence_favoured` — the height enters ONLY via
`RESOLUTION_Q13.payload`.

JUDGE discipline (pre-registered): any gated FAIL, a W2.4 convention
failure, or a non-asymptotic ladder => the archive is still written,
the record documents the failure, the exit code is non-zero, and no
anchor record is minted. No geometry retuning, no tolerance widening,
no branch re-picking.

Usage:  python -m cavity.validation.run_w2 [--runs-root refs/gate_runs]
                                           [--run-dir <existing dir>]
                                           [--rebuild-only]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]


def w2_resolved_inputs() -> tuple[float, float]:
    """(sto_height_m, crystal_epsilon_r) from the ratified register.

    Refuses (the dofs exceptions) if Q13/Q11 are missing or mock. The
    numbers enter ONLY via the resolution payloads — never from the
    fork object, never from `evidence_favoured`.
    """
    from cavity.sweep.dofs import (
        MockResolutionError,
        UnresolvedTodoTraceError,
    )
    from cavity.sweep.resolutions import ratified_resolutions

    context = ratified_resolutions()
    missing = tuple(
        q for q in ("Q13", "Q11") if context.get(q) is None
    )
    if missing:
        raise UnresolvedTodoTraceError(missing, "W2 Wu-anchor solve")
    mocked = tuple(
        q for q in ("Q13", "Q11") if context.get(q).mock
    )
    if mocked:
        raise MockResolutionError(
            f"W2 Wu-anchor solve refused — question(s) {list(mocked)} "
            "carry MOCK resolutions; W2 burns licence and can never "
            "run on test doubles"
        )
    sto_height_m = float(context.get("Q13").payload["sto_height_m"])
    crystal_epsilon_r = float(
        context.get("Q11").payload["crystal_epsilon_r"]
    )
    return sto_height_m, crystal_epsilon_r


def wu_w2_geometry(sto_outer_radius_m: float, sto_height_m: float):
    """The Phase 1b Wu-ring geometry at the pre-registered W2 inputs.

    `sto_outer_radius_m` is the ONE input the two runs differ in
    (Run A: the carried print; Run B: the labelled diagnostic value).
    Crystal placement: planning dims, axially centred on the ring
    mid-height plane — the LABELLED PLANNING PLACEMENT (Q9 open;
    recorded in the manifest's input_provenance).
    """
    from cavity.forward_model.geometry import (
        CavityGeometry,
        DielectricShape,
        SpacerSpec,
    )
    from cavity.provenance import GEOM_WU_STO_RING as G

    return CavityGeometry(
        box_radius_m=G.box_inner_radius_m,
        box_height_m=G.box_internal_height_asoperated_m,
        dielectric_radius_m=sto_outer_radius_m,
        dielectric_shape=DielectricShape.RING,
        dielectric_height_m=sto_height_m,
        dielectric_inner_radius_m=G.sto_inner_radius_m,
        ring_bottom_z_m=G.deck_clearance_m,
        spacer=SpacerSpec(
            base_inner_radius_m=G.spacer_base_inner_radius_m,
            base_outer_radius_m=G.spacer_base_outer_radius_m,
            base_height_m=G.spacer_base_height_m,
            lip_inner_radius_m=G.spacer_lip_inner_radius_m,
            lip_outer_radius_m=G.spacer_lip_outer_radius_m,
            lip_height_m=G.spacer_lip_height_m,
        ),
        crystal_radius_m=0.5 * G.crystal_diameter_m,
        crystal_height_m=G.crystal_height_m,
        crystal_centre_z_m=G.deck_clearance_m + 0.5 * sto_height_m,
    )


def wu_w2_materials(crystal_epsilon_r: float):
    """Canonical material branch + spacer + crystal (Q11 eps_r).

    Returns a base `MaterialSpec`; the §4 wall_pec switch is re-derived
    per arm by `runner.material_spec_for` (the §5a pattern).
    """
    from cavity.forward_model.materials import (
        CrystalDielectric,
        MaterialSpec,
    )
    from cavity.provenance import CLPS

    return MaterialSpec(
        spacer=CLPS,
        crystal=CrystalDielectric(epsilon_r_real=crystal_epsilon_r),
    )


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
            "re-mint checkpoint_manifest.json + gate_report.json + "
            "wu_anchor_w2.md from an existing --run-dir WITHOUT "
            "re-solving: every solve must cache-hit against its "
            "solves/. Needs no COMSOL licence."
        ),
    )
    parser.add_argument(
        "--ladder-shift",
        type=int,
        default=0,
        help=(
            "refine the pre-registered ladder base by sqrt(2)**N (the "
            "committed ConvergenceError's own 'refine further' remedy: "
            "drop the coarsest level(s), add finer ones). Any nonzero "
            "value is recorded in the manifest as a DECLARED DEVIATION "
            "from the pre-registered base — never a silent change."
        ),
    )
    args = parser.parse_args(argv)
    if args.rebuild_only and args.run_dir is None:
        parser.error("--rebuild-only requires --run-dir")

    from cavity.forward_model.convergence import ConvergenceError
    from cavity.forward_model.mesh import MeshConfig
    from cavity.forward_model.mode_id import ModeIdentificationError
    from cavity.forward_model.runner import run_wall_loss_study
    from cavity.forward_model.study import EigenStudyConfig, WallBC
    from cavity.provenance import GEOM_WU_STO_RING, TARGET
    from cavity.validation.report_5a import _finest_summary
    from cavity.validation.report_w2 import (
        W2_RECORD_FILENAME,
        W2_RUN_B_MEASURED_OD_M,
        build_w2_manifest,
        judge_run_a,
        render_w2_markdown,
        write_w2_gate_report,
        write_w2_manifest,
    )

    # Preconditions first — refuse before any COMSOL contact.
    sto_height_m, crystal_epsilon_r = w2_resolved_inputs()

    if args.run_dir is not None:
        run_dir = Path(args.run_dir)
    else:
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        run_dir = Path(args.runs_root) / f"{stamp}_wu_anchor_w2"
    run_dir.mkdir(parents=True, exist_ok=True)
    solves = run_dir / "solves"
    mph_dir = run_dir / "mph"
    pass_date = time.strftime("%Y-%m-%d", time.gmtime())
    print(f"[run_w2] archive: {run_dir}", flush=True)

    if args.rebuild_only:
        client = None  # cache-hits only; build_model is never reached
    else:
        import mph

        client = mph.start()

    study = EigenStudyConfig(
        wall_bc=WallBC.IMPEDANCE,
        search_hz=TARGET.f_design_hz,
        n_modes=12,
    )
    # Pre-registered ladder (2026-07-22 addendum): the §5a-precedent
    # base, 5 sqrt(2) levels, ending at the validated finest level
    # (dielectric 1.25e-4 / air 5e-4). --ladder-shift N refines the
    # base by sqrt(2)**N (declared deviation, recorded below).
    base_mesh = MeshConfig(dielectric_max_h_m=5.0e-4, air_max_h_m=2.0e-3)
    deviations: list[str] = []
    if args.ladder_shift:
        for _ in range(args.ladder_shift):
            base_mesh = base_mesh.refined(2.0**0.5)
        deviations.append(
            "DECLARED DEVIATION from the pre-registered mesh ladder: "
            f"base refined by sqrt(2)**{args.ladder_shift} to "
            f"(dielectric {base_mesh.dielectric_max_h_m:.6e} m, air "
            f"{base_mesh.air_max_h_m:.6e} m) — the committed "
            "ConvergenceError's own 'refine further' remedy after the "
            "pre-registered base ladder was refused as non-asymptotic "
            "(coarse-end f'' delta wiggle; the refused attempt's "
            "failure record and solves are archived in their own "
            "dated run directory). No convergence criterion was "
            "weakened and no window changed."
        )
    n_levels = 5
    materials = wu_w2_materials(crystal_epsilon_r)

    def _stop(stage: str, exc: Exception) -> int:
        msg = (
            f"# W2 FAILURE — {stage} ({pass_date})\n\n"
            "**STOP condition (pre-registered): the mesh ladder is not "
            "in the asymptotic regime or the TE01delta mode could not "
            "be identified — no sigma fabricated, no window judged on "
            "unconverged numbers.**\n\n"
            f"Exception:\n\n```\n{exc}\n```\n\n"
            "All solve records produced so far are under `solves/` in "
            "this directory for diagnosis. No anchor record is minted; "
            "the failure-triage ladder of "
            "docs/plans/oxborrow_reply_ingestion_and_wu_anchor.md §4.4 "
            "governs.\n"
        )
        (run_dir / "failure_report.md").write_text(
            msg, encoding="utf-8", newline="\n"
        )
        print(f"[run_w2] STOP ({stage}): {exc}", flush=True)
        return 3

    # ------------------------------------------------------------------
    # Run A — print O.D. (GATED)
    # ------------------------------------------------------------------
    print(
        "[run_w2] Run A (GATED): print O.D. 12.0 mm — impedance + PEC "
        "ladders...",
        flush=True,
    )
    try:
        run_a = run_wall_loss_study(
            wu_w2_geometry(
                GEOM_WU_STO_RING.sto_outer_radius_m, sto_height_m
            ),
            study,
            materials=materials,
            base_mesh=base_mesh,
            n_levels=n_levels,
            client=client,
            cache_root=solves,
            save_mph_dir=mph_dir,
        )
    except (ConvergenceError, ModeIdentificationError) as exc:
        return _stop("Run A ladder", exc)

    # STEP 1 (pre-registered order): the W2.4 convention check comes
    # BEFORE any window comparison. A failure stops the session — Run B
    # is not solved on a broken field solution.
    a_finest = _finest_summary(run_a.impedance.finest)
    verdict_probe = judge_run_a(a_finest)
    ratio = a_finest["v_mode_local_m3"] / a_finest["v_mode_global_m3"]
    print(
        f"[run_w2] W2.4 convention check: local/global = {ratio:.6f} "
        f"-> {'PASS' if verdict_probe['w2_4_ok'] else 'FAIL'}",
        flush=True,
    )
    if not verdict_probe["w2_4_ok"]:
        msg = (
            f"# W2 FAILURE — W2.4 convention check ({pass_date})\n\n"
            "**STOP condition (pre-registered, the 225/360 lesson): "
            "v_mode_local / v_mode_global = "
            f"{ratio:.6f} is outside 1 ± 0.10.** A failure here "
            "indicts the gain mask or the field solution — the session "
            "stops BEFORE any window comparison: W2.1/W2.2 are NOT "
            "judged, the W2.3 number is meaningless for this record, "
            "and Run B was NOT solved.\n\n"
            f"Run A finest impedance arm: f = {a_finest['f_hz']:.1f} "
            f"Hz, Q0 = {a_finest['q']:.4f}, v_mode_local = "
            f"{a_finest['v_mode_local_m3']:.6e} m^3, v_mode_global = "
            f"{a_finest['v_mode_global_m3']:.6e} m^3, p_e = "
            f"{a_finest['p_e']:.6f}, record "
            f"`{a_finest['record_hash']}`.\n\n"
            "All solve records under `solves/`. No anchor record is "
            "minted. Triage: gain-mask/field-solution audit "
            "(docs/w2_wu_anchor_windows.md convention finding; "
            "ingestion plan §4.4).\n"
        )
        (run_dir / "failure_report.md").write_text(
            msg, encoding="utf-8", newline="\n"
        )
        print(
            "[run_w2] CONVENTION FAIL — archive written, Run B skipped, "
            "no anchor record.",
            flush=True,
        )
        return 4

    # ------------------------------------------------------------------
    # Run B — measured O.D. (DIAGNOSTIC)
    # ------------------------------------------------------------------
    print(
        "[run_w2] Run B (DIAGNOSTIC): measured O.D. 12.2 mm — "
        "impedance + PEC ladders...",
        flush=True,
    )
    try:
        run_b = run_wall_loss_study(
            wu_w2_geometry(0.5 * W2_RUN_B_MEASURED_OD_M, sto_height_m),
            study,
            materials=materials,
            base_mesh=base_mesh,
            n_levels=n_levels,
            client=client,
            cache_root=solves,
            save_mph_dir=mph_dir,
        )
    except (ConvergenceError, ModeIdentificationError) as exc:
        return _stop("Run B ladder", exc)

    # ------------------------------------------------------------------
    # Records: manifest + gate report + rendered markdown
    # ------------------------------------------------------------------
    comsol_version = run_a.impedance.finest.record.comsol_version
    manifest = build_w2_manifest(
        pass_date=pass_date,
        run_a=run_a,
        run_b=run_b,
        sto_height_m=sto_height_m,
        crystal_epsilon_r=crystal_epsilon_r,
        run_dir_name=run_dir.name,
        comsol_version=comsol_version,
        repo_root=_REPO_ROOT,
        deviations=deviations,
    )
    write_w2_manifest(manifest, run_dir)
    write_w2_gate_report(manifest, run_dir)
    (run_dir / W2_RECORD_FILENAME).write_text(
        render_w2_markdown(manifest), encoding="utf-8", newline="\n"
    )
    print(f"[run_w2] record: {run_dir / W2_RECORD_FILENAME}", flush=True)

    verdict = manifest["verdict"]
    for c in verdict["checks"]:
        print(
            f"[run_w2] {c['name']}: measured={c['measured']:.6g} "
            f"status={c['status']}",
            flush=True,
        )
    diag = manifest["diagnostic"]
    print(
        f"[run_w2] O.D. sensitivity: df/dOD = "
        f"{diag['df_dod_hz_per_m'] / 1e9:.4f} MHz/mm, dQ0/dOD = "
        f"{diag['dq0_dod_per_m'] / 1e3:.4f} /mm",
        flush=True,
    )
    if verdict["passed"]:
        print(
            "[run_w2] PASS — Run A clears every gated row; this archive "
            "is the Wu anchor record (mint the pinned sweep-centre "
            "record in the follow-up zero-licence changeset).",
            flush=True,
        )
        return 0
    print(
        "[run_w2] GATED FAIL — archive written; no anchor record; the "
        "pre-registered failure discipline governs (findings note to "
        "the confirmation email).",
        flush=True,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
