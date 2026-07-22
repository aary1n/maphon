"""W2 Wu-anchor record builder — dual-geometry session (2026-07-22).

Two pieces, the `report_5a` pattern:

- `build_w2_manifest(...)` — assembles `checkpoint_manifest.json` from
  the two live wall-loss studies (Run A = print O.D., Run B = measured
  O.D.), the W2 verdicts, and §1 metadata (git commit at solve time).
  Runtime facts are RECORDED here, at solve time — the renderer never
  invents any.
- `render_w2_markdown(manifest)` — a DETERMINISTIC pure function of the
  committed manifest: regenerating the committed `wu_anchor_w2.md` from
  the committed manifest must be byte-identical (pinned in
  tests/test_report_w2.py once the record is committed).

Windows (RATIFIED 2026-07-19, `docs/w2_wu_anchor_windows.md`; restated
here as code with the doc as source — the pin test asserts the numeric
identity; NO window is revised at solve time under any outcome):

  W2.1  f  = TARGETS.wu_ring.f_hz (1.4495 GHz)  ± 1.5 %   GATE
  W2.2  Q0 = (1 + k) * Q_L = 7,200 (k = 1 stated) ± 25 %  GATE
  W2.3  v_mode_local vs 0.32 cm^3               report-only
  W2.4  v_mode_local / v_mode_global within 10 % of 1     GATE

Judgment ORDER (pre-registered, 2026-07-22 addendum — the 225/360
lesson): W2.4 is judged FIRST; a W2.4 failure indicts the gain mask or
field solution, W2.1/W2.2 are NOT judged for that record, and the W2.3
number is declared meaningless. Run A binds the gates; Run B is
DIAGNOSTIC only — it binds no gate, creates no anchor record, and
selects no branch regardless of result.
"""

from __future__ import annotations

import json
from pathlib import Path

from cavity.provenance import GEOM_WU_STO_RING, STO, TARGET, TARGETS
from cavity.validation.report_5a import _arm_dict, _finest_summary, _git_state

W2_MANIFEST_FILENAME = "checkpoint_manifest.json"
W2_GATE_REPORT_FILENAME = "gate_report.json"
W2_RECORD_FILENAME = "wu_anchor_w2.md"
W2_MANIFEST_SCHEMA_VERSION = 1

#: W2.1 — f window (docs/w2_wu_anchor_windows.md, ratified 2026-07-19).
W2_F_TARGET_HZ: float = TARGETS.wu_ring.f_hz
W2_F_REL_TOL: float = 0.015

#: W2.2 — Q0 window. Target derived from the anchor's STATED coupling
#: (k = 1, Wu 2020 print; PRL SM corroboration "Q_0 ~= 2 Q_L = 7200"),
#: never a bare literal.
W2_Q0_TARGET: float = TARGETS.wu_ring.q_factor * (
    1.0 + TARGETS.wu_ring.deload_k
)
W2_Q0_REL_TOL: float = 0.25

#: W2.3 — report-only comparison value (PRL SM COMSOL estimate;
#: convention INFERRED, not stated — hence no gate).
W2_V_MODE_REPORT_M3: float = TARGETS.wu_ring.v_mode_m3

#: W2.4 — build-specific convention gate.
W2_RATIO_TOL: float = 0.10

#: Run B diagnostic O.D. — the 2026-07-21 in-person caliper measurement
#: of the (reportedly same) ring: 12.2 mm vs the carried print 12.0 mm.
#: Provenance corrected 2026-07-22 (docs/commit_errata_2026-07-22.md):
#: a FIRST-HAND in-person caliper measurement, live in situ during the
#: meeting; written confirmation from Oxborrow PENDING; the claim that
#: the measured ring IS the Wu 2020 build's ring is Oxborrow-VERBAL.
#: Single reading, NO measurement band. This constant is a LABELLED
#: DIAGNOSTIC INPUT of the W2 dual-geometry session ONLY (2026-07-22
#: pre-registered addendum, docs/w2_wu_anchor_windows.md): it is not a
#: carried geometry value, it binds no gate, creates no anchor record,
#: and selects no branch. The carried value remains
#: GEOM_WU_STO_RING.sto_outer_radius_m (the Wu 2020 print, 12.0 mm).
W2_RUN_B_MEASURED_OD_M: float = 12.2e-3


def judge_run_a(finest: dict) -> dict:
    """Judge Run A's finest impedance-arm summary against the ratified
    W2 windows, in the pre-registered order (W2.4 FIRST).

    `finest` is a `_finest_summary`-shaped dict. Returns the W2 verdict
    block: per-row checks with measured/lo/hi/status, the pre-gate
    convention verdict, and the overall `passed` flag. A W2.4 failure
    marks W2.1/W2.2 `not_judged` (pre-registered stop-and-triage) and
    declares the W2.3 report meaningless for this record.
    """
    ratio = finest["v_mode_local_m3"] / finest["v_mode_global_m3"]
    ratio_ok = abs(ratio - 1.0) <= W2_RATIO_TOL
    checks = [
        {
            "name": "W2.4/v_mode_local_over_global",
            "measured": ratio,
            "lo": 1.0 - W2_RATIO_TOL,
            "hi": 1.0 + W2_RATIO_TOL,
            "status": "pass" if ratio_ok else "fail",
            "kind": "gate",
        }
    ]
    if ratio_ok:
        f_lo = W2_F_TARGET_HZ * (1.0 - W2_F_REL_TOL)
        f_hi = W2_F_TARGET_HZ * (1.0 + W2_F_REL_TOL)
        f_ok = f_lo <= finest["f_hz"] <= f_hi
        q_lo = W2_Q0_TARGET * (1.0 - W2_Q0_REL_TOL)
        q_hi = W2_Q0_TARGET * (1.0 + W2_Q0_REL_TOL)
        q_ok = q_lo <= finest["q"] <= q_hi
        checks += [
            {
                "name": "W2.1/f",
                "measured": finest["f_hz"],
                "lo": f_lo,
                "hi": f_hi,
                "status": "pass" if f_ok else "fail",
                "kind": "gate",
            },
            {
                "name": "W2.2/q0",
                "measured": finest["q"],
                "lo": q_lo,
                "hi": q_hi,
                "status": "pass" if q_ok else "fail",
                "kind": "gate",
            },
            {
                "name": "W2.3/v_mode_local",
                "measured": finest["v_mode_local_m3"],
                "lo": None,
                "hi": None,
                "status": "report_only",
                "kind": "diagnostic",
            },
        ]
    else:
        checks += [
            {
                "name": "W2.1/f",
                "measured": finest["f_hz"],
                "lo": None,
                "hi": None,
                "status": "not_judged",
                "kind": "gate",
            },
            {
                "name": "W2.2/q0",
                "measured": finest["q"],
                "lo": None,
                "hi": None,
                "status": "not_judged",
                "kind": "gate",
            },
            {
                "name": "W2.3/v_mode_local",
                "measured": finest["v_mode_local_m3"],
                "lo": None,
                "hi": None,
                "status": "meaningless_convention_failed",
                "kind": "diagnostic",
            },
        ]
    n_fail = sum(1 for c in checks if c["status"] == "fail")
    n_not_judged = sum(1 for c in checks if c["status"] == "not_judged")
    return {
        "order": "W2.4 first (pre-registered, 2026-07-22 addendum)",
        "checks": checks,
        "w2_4_ok": ratio_ok,
        "n_fail": n_fail,
        "n_not_judged": n_not_judged,
        "passed": ratio_ok and n_fail == 0,
    }


def _wall_loss_dict(study) -> dict:
    d = study.decomposition
    return {
        "q_total": d.q_total,
        "q_diel": d.q_diel,
        "q_wall": d.q_wall,
        "sigma_q_wall": d.sigma_q_wall,
        "wall_fraction": d.wall_fraction,
        "below_resolution": d.below_resolution,
    }


def _run_dict(study, sto_outer_radius_m: float, label: str, role: str) -> dict:
    return {
        "label": label,
        "role": role,
        "sto_outer_radius_m": sto_outer_radius_m,
        "sto_outer_diameter_m": 2.0 * sto_outer_radius_m,
        "arms": {
            "impedance": _arm_dict(study.impedance),
            "pec": _arm_dict(study.pec),
        },
        "wall_loss": _wall_loss_dict(study),
    }


def input_provenance(sto_height_m: float, crystal_epsilon_r: float) -> dict:
    """Every solve input, citing its constant / resolution — including
    the confirmation-pending caveats on 8.6 mm and 12.2 mm (STEP 4 of
    the session protocol). Recorded in the manifest verbatim."""
    return {
        "sto_outer_radius_run_a": (
            "6.0e-3 m = GEOM_WU_STO_RING.sto_outer_radius_m — Wu 2020 "
            "SEC. III.C 'O.D. = 12.0 mm', the CARRIED print. The "
            "2026-07-21 in-person caliper reads 12.2 mm against it "
            "(written confirmation pending; ring-identity claim "
            "Oxborrow-verbal); unresolved two-sided discrepancy, no "
            "branch selected — Run B below is the diagnostic."
        ),
        "sto_outer_radius_run_b": (
            "6.1e-3 m = W2_RUN_B_MEASURED_OD_M/2 — the 2026-07-21 "
            "IN-PERSON CALIPER measurement (provenance corrected "
            "2026-07-22, docs/commit_errata_2026-07-22.md; single "
            "reading, no band; written confirmation PENDING; the "
            "ring-identity claim is Oxborrow-VERBAL). LABELLED "
            "DIAGNOSTIC INPUT only: binds no gate, creates no anchor, "
            "selects no branch."
        ),
        "sto_inner_radius": (
            "2.025e-3 m = GEOM_WU_STO_RING.sto_inner_radius_m — Wu "
            "2020 'I.D. = 4.05 mm' (the SM's '4-mm bore' is a round)."
        ),
        "sto_height": (
            f"{sto_height_m!r} m via RESOLUTION_Q13 (in-person caliper "
            "2026-07-21, provenance corrected 2026-07-22; WRITTEN "
            "CONFIRMATION PENDING — rides the confirmation email; no "
            "measured band, the +/-25 um machining placeholder applies "
            "at the DOF layer; the {8.5, 8.6} print fork object "
            "remains the record)."
        ),
        "box_inner_radius": (
            "14.0e-3 m = GEOM_WU_STO_RING.box_inner_radius_m — Wu 2020 "
            "Fig. 6 caption; CAVEAT: nominal 28-mm end-feed fitting, "
            "true bore may differ by the fitting tolerance."
        ),
        "box_internal_height": (
            "15e-3 m = GEOM_WU_STO_RING.box_internal_height_asoperated_m "
            "— the as-operated/as-simulated print nominal (Wu 2020 "
            "Fig. 6; PRL SM '~15 mm'), = RESOLUTION_Q2's nominal at "
            "the [15, 25] mm travel band's lower edge (in-person "
            "caliper 2026-07-21, written confirmation pending). Flat "
            "ceiling — no piston step (matches Wu's own Fig. 6 "
            "simulation region; gap-depth rider open)."
        ),
        "deck_clearance": (
            "3.0e-3 m = GEOM_WU_STO_RING.deck_clearance_m — Wu 2020 "
            "'raises the STO ring 3 mm'; PRL SM '~3 mm above the PCB'."
        ),
        "spacer": (
            "ON (ratified default — Wu's own COMSOL includes it, "
            "Fig. 6): stepped annular seat, figure-derived dims "
            "+/-~0.3 mm (GEOM_WU_STO_RING.spacer_*, "
            "refs/wu_fig6_spacer_digitization.md); CLPS eps_r 2.53 "
            "DATASHEET-CLASS-ANALOG, tan_delta deliberately ungraded "
            "= 0."
        ),
        "crystal_dims": (
            "3.0 x 8.0 mm = GEOM_WU_STO_RING.crystal_diameter_m/"
            "crystal_height_m — PLANNING-ASSUMPTION (Breeze 2017 "
            "import, provenance.CRYSTAL) with the CROSS-BUILD-TRANSFER "
            "FLAG riding (five published Wu-side indicators lean "
            "toward a ~4 mm bore-filling crystal; ask in the Oxborrow "
            "email queue)."
        ),
        "crystal_epsilon_r": (
            f"{crystal_epsilon_r!r} via RESOLUTION_Q11 "
            "(PLANNING_ASSUMPTION grade; band [2.4, 4.1] rides the "
            "payload unconsumed); crystal tan_delta deliberately "
            "ungraded = 0 (the spacer precedent, "
            "forward_model.materials.CrystalDielectric)."
        ),
        "crystal_placement": (
            "on-axis (eccentricity nominal CENTRED — "
            "supervisor-confirmed design nominal 2026-07-16; the m = 0 "
            "axisymmetric solve can represent nothing else), axially "
            "centred on the ring mid-height plane — a LABELLED "
            "PLANNING PLACEMENT; Q9 (axial band + centring tolerance) "
            "remains UNRESOLVED and placement is not a W2 gate row."
        ),
        "sto_material": (
            "CANONICAL branch: eps_r' 316.3, tan_delta 1.1e-4 "
            "(provenance.STO); copper sigma 6.0e7 S/m via Impedance "
            "BC; PEC companion arm for the wall split."
        ),
    }


def build_w2_manifest(
    *,
    pass_date: str,
    run_a,
    run_b,
    sto_height_m: float,
    crystal_epsilon_r: float,
    run_dir_name: str,
    comsol_version: str | None,
    repo_root: Path,
    deviations: list[str] | None = None,
) -> dict:
    """Assemble the W2 checkpoint manifest (see module docstring).

    `run_a` / `run_b` are `WallLossStudyResult`s at the print and
    measured O.D. respectively. Judgment (Run A only) happens here via
    `judge_run_a`; Run B receives the diagnostic block — deltas,
    implied local O.D. sensitivities, and the informational
    which-geometry-fits statement.
    """
    git_commit, git_dirty = _git_state(repo_root)
    a_finest = _finest_summary(run_a.impedance.finest)
    b_finest = _finest_summary(run_b.impedance.finest)
    verdict = judge_run_a(a_finest)

    d_od_m = W2_RUN_B_MEASURED_OD_M - 2.0 * GEOM_WU_STO_RING.sto_outer_radius_m
    diagnostic = {
        "delta_f_hz": b_finest["f_hz"] - a_finest["f_hz"],
        "delta_q0": b_finest["q"] - a_finest["q"],
        "delta_v_mode_local_m3": (
            b_finest["v_mode_local_m3"] - a_finest["v_mode_local_m3"]
        ),
        "delta_v_mode_global_m3": (
            b_finest["v_mode_global_m3"] - a_finest["v_mode_global_m3"]
        ),
        "delta_od_m": d_od_m,
        "df_dod_hz_per_m": (b_finest["f_hz"] - a_finest["f_hz"]) / d_od_m,
        "dq0_dod_per_m": (b_finest["q"] - a_finest["q"]) / d_od_m,
        "f_residual_run_a_hz": a_finest["f_hz"] - W2_F_TARGET_HZ,
        "f_residual_run_b_hz": b_finest["f_hz"] - W2_F_TARGET_HZ,
        "q0_residual_run_a": a_finest["q"] - W2_Q0_TARGET,
        "q0_residual_run_b": b_finest["q"] - W2_Q0_TARGET,
    }

    # First-order eps_r sensitivity for the W2.1 residual statement
    # (windows doc: a residual reachable inside eps_r [312, 318] is
    # non-alarming and must be stated WITH the sensitivity). Standard
    # perturbation estimate df/deps ~= -f * p_e / (2 eps), evaluated
    # with Run A's own p_e at the canonical eps_r' = 316.3.
    eps = STO.epsilon_r_real
    df_deps = -a_finest["f_hz"] * a_finest["p_e"] / (2.0 * eps)
    eps_band = (312.0, 318.0)
    f_reach = sorted(
        (
            a_finest["f_hz"] + df_deps * (eps_band[0] - eps),
            a_finest["f_hz"] + df_deps * (eps_band[1] - eps),
        )
    )
    eps_sensitivity = {
        "eps_r_canonical": eps,
        "eps_r_band": list(eps_band),
        "df_deps_hz_per_unit": df_deps,
        "f_reach_lo_hz": f_reach[0],
        "f_reach_hi_hz": f_reach[1],
        "target_reachable_inside_band": (
            f_reach[0] <= W2_F_TARGET_HZ <= f_reach[1]
        ),
    }

    return {
        "schema_version": W2_MANIFEST_SCHEMA_VERSION,
        "kind": "wu_anchor_w2",
        "pass_date": pass_date,
        "run_dir": run_dir_name,
        "deviations": list(deviations) if deviations else [],
        "protocol": {
            "windows_doc": "docs/w2_wu_anchor_windows.md",
            "windows_ratified": "2026-07-19",
            "pre_registration": (
                "docs/w2_wu_anchor_windows.md — addendum 2026-07-22, "
                "committed BEFORE any solve: dual-geometry protocol; "
                "the 2e19187 O.D. hold lifted by user decision of "
                "2026-07-22 (not by absorbing or dismissing the "
                "discrepancy); Run A (print 12.0 mm) binds the gates, "
                "Run B (measured 12.2 mm) is diagnostic only; no "
                "window revision at solve time under any outcome."
            ),
            "windows": {
                "W2.1": {
                    "target_hz": W2_F_TARGET_HZ,
                    "rel_tol": W2_F_REL_TOL,
                },
                "W2.2": {
                    "target": W2_Q0_TARGET,
                    "rel_tol": W2_Q0_REL_TOL,
                },
                "W2.3": {
                    "report_value_m3": W2_V_MODE_REPORT_M3,
                    "gate": False,
                },
                "W2.4": {"target": 1.0, "rel_tol": W2_RATIO_TOL},
            },
        },
        "input_provenance": input_provenance(
            sto_height_m, crystal_epsilon_r
        ),
        "runs": {
            "run_a": _run_dict(
                run_a,
                GEOM_WU_STO_RING.sto_outer_radius_m,
                "Run A — print O.D. 12.0 mm (carried value)",
                "GATED",
            ),
            "run_b": _run_dict(
                run_b,
                0.5 * W2_RUN_B_MEASURED_OD_M,
                "Run B — measured O.D. 12.2 mm (2026-07-21 caliper, "
                "written confirmation pending)",
                "DIAGNOSTIC",
            ),
        },
        "verdict": verdict,
        "diagnostic": diagnostic,
        "eps_sensitivity": eps_sensitivity,
        "provenance": {
            "git_commit": git_commit,
            "git_dirty": git_dirty,
            "comsol_version": comsol_version,
            "f_design_hz": TARGET.f_design_hz,
            "sto_height_m": sto_height_m,
            "crystal_epsilon_r": crystal_epsilon_r,
        },
    }


def write_w2_manifest(manifest: dict, run_dir: Path) -> Path:
    out = Path(run_dir) / W2_MANIFEST_FILENAME
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return out


def write_w2_gate_report(manifest: dict, run_dir: Path) -> Path:
    """The §4.4-shape verdict file: the W2 verdict block + enough
    reproducibility context to stand alone (same duplication doctrine
    as the §5a gate_report.json / manifest pair)."""
    out = Path(run_dir) / W2_GATE_REPORT_FILENAME
    payload = {
        "kind": "wu_anchor_w2_gate_report",
        "schema_version": W2_MANIFEST_SCHEMA_VERSION,
        "pass_date": manifest["pass_date"],
        "run_dir": manifest["run_dir"],
        "windows": manifest["protocol"]["windows"],
        "verdict": manifest["verdict"],
        "provenance": manifest["provenance"],
    }
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return out


# --- deterministic renderer ----------------------------------------------


def _fmt_mm(m: float) -> str:
    return f"{m * 1e3:.5g} mm"


def _level_table(arm: dict) -> list[str]:
    lines = [
        "| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q |"
        " record |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in arm["levels"]:
        lines.append(
            f"| {row['level']} | {_fmt_mm(row['dielectric_max_h_m'])} "
            f"| {_fmt_mm(row['air_max_h_m'])} "
            f"| {row['mesh_element_count']} "
            f"| {row['f_real_hz']:.6f} | {row['f_imag_hz']:.6f} "
            f"| {row['q']:.4f} | `{row['record_hash']}` |"
        )
    lines += [
        "",
        f"sigma_f' = {arm['sigma_f_real_hz']:.3f} Hz, "
        f"sigma_f'' = {arm['sigma_f_imag_hz']:.4f} Hz, "
        f"sigma_Q = {arm['sigma_q']:.4f}.",
    ]
    return lines


_STATUS_WORDS = {
    "pass": "PASS",
    "fail": "FAIL",
    "report_only": "REPORT (no gate)",
    "not_judged": "NOT JUDGED (W2.4 failed first)",
    "meaningless_convention_failed": "MEANINGLESS (W2.4 failed)",
}


def render_w2_markdown(manifest: dict) -> str:
    """The W2 session record, byte-deterministic from the manifest."""
    verdict = manifest["verdict"]
    a = manifest["runs"]["run_a"]
    b = manifest["runs"]["run_b"]
    a_imp = a["arms"]["impedance"]["finest"]
    a_pec = a["arms"]["pec"]["finest"]
    b_imp = b["arms"]["impedance"]["finest"]
    b_pec = b["arms"]["pec"]["finest"]
    diag = manifest["diagnostic"]
    eps_s = manifest["eps_sensitivity"]
    prov = manifest["provenance"]
    windows = manifest["protocol"]["windows"]

    if verdict["passed"]:
        status_word = (
            "PASS — Run A clears every gated W2 row; this record is the "
            "Wu anchor record"
        )
    elif not verdict["w2_4_ok"]:
        status_word = (
            "CONVENTION FAIL — W2.4 failed; W2.1/W2.2 not judged "
            "(pre-registered stop-and-triage); no anchor record"
        )
    else:
        status_word = (
            f"GATED FAIL — {verdict['n_fail']} gated row(s) FAIL; "
            "no anchor record"
        )

    lines: list[str] = [
        f"# W2 — Wu-anchor validation, dual-geometry session "
        f"({manifest['pass_date']})",
        "",
        f"**Status: {status_word}.** Live COMSOL solves of the Phase 1b "
        "Wu-ring model (crystal + spacer sub-domains), judged strictly "
        "by the committed windows of `docs/w2_wu_anchor_windows.md` "
        "(ratified 2026-07-19; dual-geometry protocol pre-registered in "
        "the 2026-07-22 addendum BEFORE any solve — the 2e19187 O.D. "
        "hold was lifted by user decision of 2026-07-22, resolved by "
        "solving BOTH geometries, not by selecting a branch). No window "
        "was revised at solve time. Regenerate this file with "
        "`render_w2_markdown(checkpoint_manifest.json)` (byte-pinned in "
        "tests/test_report_w2.py).",
        "",
    ]
    if manifest.get("deviations"):
        lines += ["## Declared deviations", ""]
        for d in manifest["deviations"]:
            lines.append(f"- {d}")
        lines.append("")
    lines += [
        "## The two runs",
        "",
        f"- **Run A (GATED)** — ring O.D. {_fmt_mm(a['sto_outer_diameter_m'])} "
        "= the carried Wu 2020 print (`GEOM_WU_STO_RING`).",
        f"- **Run B (DIAGNOSTIC)** — ring O.D. "
        f"{_fmt_mm(b['sto_outer_diameter_m'])} = the 2026-07-21 in-person "
        "caliper value (provenance corrected 2026-07-22; written "
        "confirmation pending; ring-identity claim Oxborrow-verbal). "
        "Binds no gate, creates no anchor record, selects no branch.",
        "",
        "Identical in every other input (pre-registered): I.D. 4.05 mm; "
        f"height {_fmt_mm(prov['sto_height_m'])} (Q13, caliper, written "
        "confirmation pending); enclosure radius 14 mm; internal height "
        "15 mm as-operated, flat ceiling; deck 3 mm; spacer ON (CLPS "
        "2.53); crystal present, planning dims 3.0 x 8.0 mm, eps_r = "
        f"{prov['crystal_epsilon_r']:g} (Q11), axially centred on the "
        "ring mid-height plane (LABELLED PLANNING PLACEMENT; Q9 open); "
        "canonical materials (eps_r' 316.3, tan_delta 1.1e-4, Cu "
        "6.0e7); 5-level sqrt(2) mesh ladder per arm; full input "
        "provenance in `checkpoint_manifest.json` "
        "(`input_provenance`).",
        "",
        "## W2 verdicts (Run A binds; judged in the pre-registered "
        "order, W2.4 first)",
        "",
        "| Row | Measured | Window | Verdict |",
        "|---|---|---|---|",
    ]
    fmt = {
        "W2.4/v_mode_local_over_global": "{:.6f}",
        "W2.1/f": "{:.1f}",
        "W2.2/q0": "{:.4f}",
        "W2.3/v_mode_local": "{:.6e}",
    }
    for c in verdict["checks"]:
        measured = fmt[c["name"]].format(c["measured"])
        window = (
            f"[{c['lo']:.6g}, {c['hi']:.6g}]"
            if c["lo"] is not None
            else "—"
        )
        if c["name"] == "W2.3/v_mode_local":
            window = f"vs {windows['W2.3']['report_value_m3']:.2e} m^3 (no gate)"
        lines.append(
            f"| {c['name']} | {measured} | {window} | "
            f"{_STATUS_WORDS[c['status']]} |"
        )
    lines += [
        "",
        "W2.3 note (convention grade INFERENCE, ratified doc): "
        "v_mode_local normalises |H|^2 at the gain-region (crystal) "
        "maximum — the Breeze-family per-spin form the SM equations "
        "imply; the printed 0.32 cm^3 carries no stated convention, "
        "hence report-only.",
        "",
        "## W2.1 residual and the eps_r band (stated per the ratified "
        "window)",
        "",
        f"- Run A f residual vs the printed anchor: "
        f"{diag['f_residual_run_a_hz'] / 1e6:+.4f} MHz "
        f"({diag['f_residual_run_a_hz'] / W2_F_TARGET_HZ * 1e2:+.4f} %).",
        f"- First-order eps_r sensitivity at Run A's own p_e = "
        f"{a_imp['p_e']:.6f}: df/deps_r = "
        f"{eps_s['df_deps_hz_per_unit'] / 1e6:.4f} MHz per unit eps_r "
        f"about the canonical {eps_s['eps_r_canonical']:g}.",
        f"- f reachable inside the eps_r band "
        f"[{eps_s['eps_r_band'][0]:g}, {eps_s['eps_r_band'][1]:g}]: "
        f"[{eps_s['f_reach_lo_hz'] / 1e9:.6f}, "
        f"{eps_s['f_reach_hi_hz'] / 1e9:.6f}] GHz — the printed "
        f"1.4495 GHz is "
        + (
            "REACHABLE inside the band (non-alarming per the ratified "
            "window)."
            if eps_s["target_reachable_inside_band"]
            else "NOT reachable inside the band."
        ),
        "",
        "## Both runs at the finest level (walls-on arm)",
        "",
        "| Quantity | Run A (print 12.0) | Run B (measured 12.2) |",
        "|---|---|---|",
        f"| f' (Hz) | {a_imp['f_hz']:.1f} | {b_imp['f_hz']:.1f} |",
        f"| Q0 (unloaded) | {a_imp['q']:.4f} | {b_imp['q']:.4f} |",
        f"| V_mode local (m^3) | {a_imp['v_mode_local_m3']:.6e} "
        f"| {b_imp['v_mode_local_m3']:.6e} |",
        f"| V_mode global (m^3) | {a_imp['v_mode_global_m3']:.6e} "
        f"| {b_imp['v_mode_global_m3']:.6e} |",
        f"| local/global ratio | "
        f"{a_imp['v_mode_local_m3'] / a_imp['v_mode_global_m3']:.6f} "
        f"| {b_imp['v_mode_local_m3'] / b_imp['v_mode_global_m3']:.6f} |",
        f"| p_e | {a_imp['p_e']:.10f} | {b_imp['p_e']:.10f} |",
        f"| Q_diel (PEC arm) | {a_pec['q']:.4f} | {b_pec['q']:.4f} |",
        f"| wall fraction | {a['wall_loss']['wall_fraction']:.6f} "
        f"| {b['wall_loss']['wall_fraction']:.6f} |",
        f"| record hash | `{a_imp['record_hash']}` "
        f"| `{b_imp['record_hash']}` |",
        "",
        "## Run B diagnostic — O.D. sensitivity (a deliverable of the "
        "session regardless of pass/fail)",
        "",
        f"- delta O.D. = {diag['delta_od_m'] * 1e3:+.3g} mm "
        "(print -> measured).",
        f"- delta f = {diag['delta_f_hz'] / 1e6:+.4f} MHz => implied "
        f"local sensitivity d f / d O.D. = "
        f"{diag['df_dod_hz_per_m'] / 1e9:.4f} GHz/m "
        f"= {diag['df_dod_hz_per_m'] / 1e9:.4f} MHz/mm.",
        f"- delta Q0 = {diag['delta_q0']:+.4f} => implied local "
        f"sensitivity d Q0 / d O.D. = {diag['dq0_dod_per_m']:.4f} /m "
        f"= {diag['dq0_dod_per_m'] / 1e3:.4f} /mm.",
        f"- f residuals vs the printed 1.4495 GHz: Run A "
        f"{diag['f_residual_run_a_hz'] / 1e6:+.4f} MHz, Run B "
        f"{diag['f_residual_run_b_hz'] / 1e6:+.4f} MHz. Q0 residuals "
        f"vs 7,200: Run A {diag['q0_residual_run_a']:+.4f}, Run B "
        f"{diag['q0_residual_run_b']:+.4f}.",
        "- INFORMATIONAL (no gate, no branch selection): the geometry "
        "whose f sits nearer the printed anchor is "
        + (
            "**Run A (print 12.0 mm)**."
            if abs(diag["f_residual_run_a_hz"])
            <= abs(diag["f_residual_run_b_hz"])
            else "**Run B (measured 12.2 mm)**."
        ),
        "",
        "## Wall-loss split (both runs, sigmas from the ladders)",
        "",
        "| Run | Q_total | Q_diel | Q_wall | sigma_Q_wall "
        "| wall fraction | below_resolution |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, run in (("A (print)", a), ("B (measured)", b)):
        w = run["wall_loss"]
        lines.append(
            f"| {label} | {w['q_total']:.4f} | {w['q_diel']:.4f} "
            f"| {w['q_wall']:.4f} | {w['sigma_q_wall']:.4f} "
            f"| {w['wall_fraction']:.6f} "
            f"| {str(w['below_resolution']).lower()} |"
        )
    lines += [
        "",
        "## Mesh-convergence evidence (full ladders, per run per arm)",
        "",
    ]
    for run_label, run in (("Run A", a), ("Run B", b)):
        for arm_label, arm_key in (
            ("Impedance walls", "impedance"),
            ("PEC walls", "pec"),
        ):
            lines.append(f"### {run_label} — {arm_label}")
            lines.append("")
            lines += _level_table(run["arms"][arm_key])
            lines.append("")
    lines += [
        "## Finest-level eigenspectrum + TE01delta diagnostics "
        "(Run A, gated arm)",
        "",
        f"Picked index = {a_imp['picked_index']} (field-symmetry "
        "selection, proximity only as tiebreak).",
        "",
        "| i | f' (Hz) | f'' (Hz) | picked |",
        "|---|---|---|---|",
    ]
    for i, (fr, fi) in enumerate(
        zip(a_imp["spectrum_f_real_hz"], a_imp["spectrum_f_imag_hz"])
    ):
        mark = "**<-**" if i == a_imp["picked_index"] else ""
        lines.append(f"| {i} | {fr:.1f} | {fi:.4f} | {mark} |")
    lines += [
        "",
        "## Anchor-record disposition (pre-registered conditions)",
        "",
    ]
    if verdict["passed"]:
        lines += [
            "Run A PASSED every gated row: **this archive is the Wu "
            "anchor record**, and the Wu-build sweep-centre record is "
            "created from it (design-doc 2026-07-19 addendum; pinned "
            "import-only in `cavity.sweep.wu_anchor`). Run B remains "
            "diagnostic: no anchor, no branch — the O.D. question "
            "stays with the confirmation email (which should the model "
            "carry, and is a caliper band available?).",
        ]
    else:
        lines += [
            "Run A did NOT pass: **no anchor record is created**, no "
            "gate row binds `wu_ring`, and nothing downstream moves "
            "(pre-registered failure discipline — no geometry "
            "retuning, no tolerance widening, no branch re-picking). "
            "The result is written up as a finding for the "
            "confirmation email to Oxborrow (already owed, already "
            "carrying the O.D. line item); the anchor question waits "
            "on his written answer.",
        ]
    lines += [
        "",
        "## Reproducibility (SPEC §1)",
        "",
        f"- git commit at solve time: `{prov['git_commit']}` "
        f"(dirty: {str(prov['git_dirty']).lower()} — the session "
        "solves before its own commit by construction; the archive "
        "commit is the citation).",
        f"- COMSOL version: {prov['comsol_version']}.",
        "- All solve records under `solves/` (schema v3 — crystal "
        "fields in the fingerprint); finest-arm raw .mph under `mph/` "
        "(LFS); verdicts in `gate_report.json`; full structured "
        "summary in `checkpoint_manifest.json`.",
        "",
    ]
    return "\n".join(lines)


def render_from_run_dir(run_dir: Path) -> str:
    """Render the W2 record from a committed run directory."""
    manifest = json.loads(
        (Path(run_dir) / W2_MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    return render_w2_markdown(manifest)


__all__ = [
    "W2_F_REL_TOL",
    "W2_F_TARGET_HZ",
    "W2_GATE_REPORT_FILENAME",
    "W2_MANIFEST_FILENAME",
    "W2_MANIFEST_SCHEMA_VERSION",
    "W2_Q0_REL_TOL",
    "W2_Q0_TARGET",
    "W2_RATIO_TOL",
    "W2_RECORD_FILENAME",
    "W2_RUN_B_MEASURED_OD_M",
    "W2_V_MODE_REPORT_M3",
    "build_w2_manifest",
    "input_provenance",
    "judge_run_a",
    "render_from_run_dir",
    "render_w2_markdown",
    "write_w2_gate_report",
    "write_w2_manifest",
]
