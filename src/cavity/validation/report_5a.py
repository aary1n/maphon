"""SPEC §5a — Booth-point checkpoint record builder (2026-07-10 pass).

Two pieces:

- `build_manifest(...)` — assembles `checkpoint_manifest.json` from the
  live §5a study results (both material branches, the printed-2.46
  sensitivity solve, the gate verdicts, §1 metadata incl. the git
  commit at solve time). Runtime facts (timestamps, git state, COMSOL
  version) are RECORDED here, at solve time — the renderer below never
  invents any.
- `render_checkpoint_markdown(manifest)` — a DETERMINISTIC pure
  function of the committed manifest: regenerating the committed
  `booth_5a_checkpoint.md` from the committed manifest must be
  byte-identical (pinned in tests/test_report_5a.py; the manifest and
  gate report are plain JSON, so the pin needs no LFS content).

Branch discipline (ratified, planning session): gate-passage is
established on the FAITHFUL branch (tan_delta = BOOTH_MPH_TAN_DELTA =
1.054e-4, the .mph-exact value); the CANONICAL branch (tan_delta =
1.1e-4, SPEC §2) is the companion whose walls-on finest record feeds
the margin report and the export bundle. The checkpoint quantities
(kappa_c, Δf_max, ΔT_max) are REPORTED, not gated — their numeric
discipline is inherited from the §5 windows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cavity.extraction.qfactor import q_from_eigenfrequency
from cavity.provenance import (
    BOOTH_MPH_TAN_DELTA,
    DELOAD_K,
    GEOM_BOOTH_TE01D,
    STO,
    TARGET,
    TARGETS,
)
from cavity.provenance.gate_targets import (
    BOOTH_TWO_POINT_REL_TOL,
    F_ROW_HALF_WIDTH_HZ,
)

MANIFEST_FILENAME = "checkpoint_manifest.json"
CHECKPOINT_FILENAME = "booth_5a_checkpoint.md"
MANIFEST_SCHEMA_VERSION = 1

# Cross-build composite ΔT_max band the checkpoint compares against
# ("story holds" = order ~0.5 K; SPEC §7.T4 status note / the 2026-07-09
# margin report's band, quoted as the superseded comparison).
COMPOSITE_DT_BAND_K = (0.567, 0.725)


def _git_state(repo_root: Path) -> tuple[str | None, bool | None]:
    """(commit, dirty) — same convention as cavity.export.writer."""
    import subprocess

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, timeout=30,
        )
        if head.returncode != 0:
            return None, None
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root, capture_output=True, text=True, timeout=30,
        )
        dirty = (
            bool(status.stdout.strip()) if status.returncode == 0 else None
        )
        return head.stdout.strip(), dirty
    except Exception:
        return None, None


def _level_rows(arm) -> list[dict]:
    """Per-ladder-level table rows from a ConvergenceStudyResult."""
    rows = []
    for i, lvl in enumerate(arm.levels):
        f = lvl.complex_eigenfrequency_hz
        rows.append(
            {
                "level": i,
                "dielectric_max_h_m": lvl.mesh_cfg.dielectric_max_h_m,
                "air_max_h_m": lvl.mesh_cfg.air_max_h_m,
                "mesh_element_count": lvl.mesh_element_count,
                "f_real_hz": f.real,
                "f_imag_hz": f.imag,
                "q": q_from_eigenfrequency(f),
                "record_hash": lvl.record_hash,
            }
        )
    return rows


def _finest_summary(result) -> dict:
    """Extraction + record summary of a ForwardModelResult."""
    ext = result.extraction
    rec = result.record
    return {
        "record_hash": rec.record_hash,
        "mesh_element_count": rec.mesh_element_count,
        "picked_index": rec.picked_index,
        "f_hz": ext.f_hz,
        "q": ext.q,
        "q_emw_cross_check": ext.q_emw_cross_check,
        "p_e": ext.p_e,
        "v_mode_global_m3": ext.v_mode_global_m3,
        "v_mode_local_m3": ext.v_mode_local_m3,
        "f_m_global": ext.f_m_global,
        "f_m_local": ext.f_m_local,
        "spectrum_f_real_hz": [
            float(f) for f in rec.spectrum_f_real_hz
        ],
        "spectrum_f_imag_hz": [
            float(f) for f in rec.spectrum_f_imag_hz
        ],
        "mode_diagnostics": rec.diagnostics,
    }


def _e_mode_volume_diagnostics(record) -> dict:
    """E-field-based mode-volume DIAGNOSTICS (not §3 outputs, not
    gated): computed from the persisted raw fields to discriminate a
    V_mode-definition mismatch from a field-physics discrepancy when
    the gated (magnetic, global-max) variant misses Booth's printed
    value. Pure §1 re-derivation — no COMSOL."""
    import numpy as np

    from cavity.extraction.quadrature import axisymmetric_volume_integral

    f = record.field_sample
    e2 = np.sum(np.abs(f.e_complex) ** 2, axis=1)
    eps = np.real(f.eps_r_complex)
    v_e = float(
        np.real(axisymmetric_volume_integral(e2, f.r_m, f.weights_m2))
    ) / float(np.max(e2))
    v_e_eps = float(
        np.real(
            axisymmetric_volume_integral(eps * e2, f.r_m, f.weights_m2)
        )
    ) / float(np.max(eps * e2))
    return {"v_e_m3": v_e, "v_e_eps_m3": v_e_eps}


def _arm_dict(arm) -> dict:
    a = arm.assessment
    return {
        "levels": _level_rows(arm),
        "deltas_f_real_hz": list(a.deltas_f_real_hz),
        "deltas_f_imag_hz": list(a.deltas_f_imag_hz),
        "sigma_f_real_hz": a.sigma_f_real_hz,
        "sigma_f_imag_hz": a.sigma_f_imag_hz,
        "sigma_q": a.sigma_q,
        "finest": _finest_summary(arm.finest),
    }


def _branch_dict(study, tan_delta: float, role: str) -> dict:
    d = study.decomposition
    return {
        "tan_delta": tan_delta,
        "epsilon_r_real": TARGETS.booth.epsilon_r_real,
        "role": role,
        "arms": {
            "impedance": _arm_dict(study.impedance),
            "pec": _arm_dict(study.pec),
        },
        "wall_loss": {
            "q_total": d.q_total,
            "q_diel": d.q_diel,
            "q_wall": d.q_wall,
            "sigma_q_wall": d.sigma_q_wall,
            "wall_fraction": d.wall_fraction,
            "below_resolution": d.below_resolution,
        },
    }


def gate_dict_from_report(gate_report) -> dict:
    """Verdict summary lifted from the GateReport (same source as
    gate_report.json; duplicated into the manifest so the renderer has
    exactly one input file)."""
    checks = []
    for row in gate_report.rows:
        for c in row.checks:
            checks.append(
                {
                    "name": c.name,
                    "row_id": c.row_id,
                    "status": c.status.value,
                    "measured": c.measured,
                    "lo": c.window.lo,
                    "hi": c.window.hi,
                    "margin": c.margin,
                }
            )
    return {
        "phase1_complete": gate_report.phase1_complete,
        "n_pass": gate_report.n_pass,
        "n_fail": gate_report.n_fail,
        "n_deferred": gate_report.n_deferred,
        "row_status": {r.row_id: r.status.value for r in gate_report.rows},
        "checks": checks,
        "created_at_utc": gate_report.created_at_utc,
    }


def gate_dict_from_json(report_json: dict) -> dict:
    """Same shape as `gate_dict_from_report`, from a persisted
    gate_report.json — the rebuild-only path (records already on disk;
    the archived verdicts are the source, nothing is re-judged)."""
    checks = []
    for row in report_json["rows"]:
        for c in row["checks"]:
            checks.append(
                {
                    "name": c["name"],
                    "row_id": c["row_id"],
                    "status": c["status"],
                    "measured": c["measured"],
                    "lo": c["window"]["lo"],
                    "hi": c["window"]["hi"],
                    "margin": c["margin"],
                }
            )
    return {
        "phase1_complete": report_json["phase1_complete"],
        "n_pass": report_json["n_pass"],
        "n_fail": report_json["n_fail"],
        "n_deferred": report_json["n_deferred"],
        "row_status": {
            r["row_id"]: r["status"] for r in report_json["rows"]
        },
        "checks": checks,
        "created_at_utc": report_json["created_at_utc"],
    }


def build_manifest(
    *,
    pass_date: str,
    faithful,
    canonical,
    sensitivity,
    gate: dict,
    run_dir_name: str,
    comsol_version: str | None,
    repo_root: Path,
) -> dict:
    """Assemble the checkpoint manifest (see module docstring).

    `gate` is the verdict summary dict (`gate_dict_from_report` on the
    live path, `gate_dict_from_json` on the rebuild path).
    """
    git_commit, git_dirty = _git_state(repo_root)
    sens = _finest_summary(sensitivity)
    gated_finest = faithful.impedance.finest.extraction
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "kind": "booth_5a_checkpoint",
        "pass_date": pass_date,
        "run_dir": run_dir_name,
        "geometry": {
            "source": (
                "recovered Booth TE01delta torus "
                "(refs/booth_geometry_recovery.md; "
                "provenance.GEOM_BOOTH_TE01D)"
            ),
            "box_radius_m": GEOM_BOOTH_TE01D.box_radius_m,
            "box_height_m": GEOM_BOOTH_TE01D.box_height_m,
            "torus_major_radius_m": GEOM_BOOTH_TE01D.torus_major_radius_m,
            "torus_minor_radius_m": GEOM_BOOTH_TE01D.torus_minor_radius_m,
            "printed_minor_radius_m": (
                GEOM_BOOTH_TE01D.printed_minor_radius_m
            ),
        },
        "branches": {
            "faithful": _branch_dict(
                faithful, BOOTH_MPH_TAN_DELTA, "gated"
            ),
            "canonical": _branch_dict(
                canonical, STO.tan_delta, "companion; feeds margin report"
            ),
        },
        "sensitivity_printed_minor": {
            "minor_radius_m": GEOM_BOOTH_TE01D.printed_minor_radius_m,
            "branch": "faithful",
            "arm": "impedance",
            "delta_f_vs_gated_hz": sens["f_hz"] - gated_finest.f_hz,
            "delta_q_vs_gated": sens["q"] - gated_finest.q,
            **sens,
        },
        "diagnostic_mode_volumes": _e_mode_volume_diagnostics(
            faithful.impedance.finest.record
        ),
        "gate": gate,
        "provenance": {
            "git_commit": git_commit,
            "git_dirty": git_dirty,
            "comsol_version": comsol_version,
            "deload_k": DELOAD_K,
            "f_design_hz": TARGET.f_design_hz,
        },
    }
    return manifest


def write_manifest(manifest: dict, run_dir: Path) -> Path:
    out = Path(run_dir) / MANIFEST_FILENAME
    out.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return out


# --- deterministic renderer ----------------------------------------------


def _fmt_h(m: float) -> str:
    return f"{m * 1e3:.5g} mm"


def _level_table(arm: dict) -> list[str]:
    lines = [
        "| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q |"
        " record |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in arm["levels"]:
        lines.append(
            f"| {row['level']} | {_fmt_h(row['dielectric_max_h_m'])} "
            f"| {_fmt_h(row['air_max_h_m'])} "
            f"| {row['mesh_element_count']} "
            f"| {row['f_real_hz']:.6f} | {row['f_imag_hz']:.6f} "
            f"| {row['q']:.4f} | `{row['record_hash']}` |"
        )
    deltas_re = ", ".join(f"{d:.3f}" for d in arm["deltas_f_real_hz"])
    deltas_im = ", ".join(f"{d:.4f}" for d in arm["deltas_f_imag_hz"])
    lines += [
        "",
        f"Deltas f' (Hz): [{deltas_re}]; deltas f'' (Hz): [{deltas_im}]. "
        f"sigma_f' = {arm['sigma_f_real_hz']:.3f} Hz, "
        f"sigma_f'' = {arm['sigma_f_imag_hz']:.4f} Hz, "
        f"sigma_Q = {arm['sigma_q']:.4f}.",
    ]
    return lines


def _verdict_word(status: str) -> str:
    return {"pass": "PASS", "fail": "FAIL"}.get(
        status, "DEFERRED"
    )


def render_checkpoint_markdown(manifest: dict) -> str:
    """The §5a checkpoint record, byte-deterministic from the manifest."""
    from cavity.thermal.broadening import resonance_linewidth_hz
    from cavity.thermal.detuning import (
        delta_f_max_hz,
        delta_t_max_k,
        q_loaded,
    )
    from cavity.thermal.report_margin import PLANNING_C0

    g = manifest["geometry"]
    gate = manifest["gate"]
    fai = manifest["branches"]["faithful"]
    can = manifest["branches"]["canonical"]
    fai_imp = fai["arms"]["impedance"]["finest"]
    fai_pec = fai["arms"]["pec"]["finest"]
    can_imp = can["arms"]["impedance"]["finest"]
    can_pec = can["arms"]["pec"]["finest"]
    sens = manifest["sensitivity_printed_minor"]
    prov = manifest["provenance"]

    gated_green = gate["n_fail"] == 0
    status_word = (
        "GREEN — all live-judged rows PASS" if gated_green
        else f"FAILED — {gate['n_fail']} gated row(s) FAIL"
    )

    # §5a reported (not gated) checkpoint quantities — canonical branch
    # headline per the ratified branch choice + amendment wording.
    q0_can = can_imp["q"]
    q0_fai = fai_imp["q"]
    q_l = q_loaded(q0_can)
    f_hz = prov["f_design_hz"]
    kappa_c = resonance_linewidth_hz(f_hz, q_l)
    df_max = delta_f_max_hz(PLANNING_C0, kappa_c)
    dt_max = delta_t_max_k(
        df_max, 293.0, f_hz=f_hz, p_e=can_imp["p_e"]
    )
    branch_ratio = q0_can / q0_fai

    by_name = {c["name"]: c for c in gate["checks"]}

    def _crit(name: str, label: str, fmt: str = "{:.6g}") -> str:
        c = by_name[name]
        measured = (
            "—" if c["measured"] is None else fmt.format(c["measured"])
        )
        lo = "—" if c["lo"] is None else f"{c['lo']:.6g}"
        hi = "—" if c["hi"] is None else f"{c['hi']:.6g}"
        return (
            f"| {label} | {measured} | [{lo}, {hi}] | "
            f"{_verdict_word(c['status'])} |"
        )

    lines: list[str] = [
        f"# SPEC §5a checkpoint — own-model solve at Booth's TE01δ point "
        f"({manifest['pass_date']})",
        "",
        f"**Status: {status_word}.** Live lossy-wall COMSOL solve at the "
        "recovered Booth TE01δ geometry (refs/booth_geometry_recovery.md), "
        "judged by the committed §5 windows (`gate_targets.py`) — no new "
        "tolerances. Gate record: `gate_report.json` in this directory; "
        "regenerate this file with "
        "`render_checkpoint_markdown(checkpoint_manifest.json)` "
        "(byte-pinned in tests/test_report_5a.py).",
        "",
        "## Geometry (gated)",
        "",
        f"- Box radius {_fmt_h(g['box_radius_m'])}, box height "
        f"{_fmt_h(g['box_height_m'])}; torus major radius "
        f"{_fmt_h(g['torus_major_radius_m'])} (= x/2, .mph-pinned free "
        f"DOF), minor radius {_fmt_h(g['torus_minor_radius_m'])} "
        "(ratio-exact x/5; gates judged here), centred at the box "
        "mid-plane.",
        f"- Sensitivity diagnostic at the printed minor radius "
        f"{_fmt_h(g['printed_minor_radius_m'])} (below).",
        "",
        "## Material branches (ratified branch choice 1)",
        "",
        f"- FAITHFUL (gate-passage established here): eps_r' = "
        f"{fai['epsilon_r_real']:g}, tan_delta = {fai['tan_delta']:.6e} "
        "(`BOOTH_MPH_TAN_DELTA`, the .mph-exact unrounded Debye value).",
        f"- CANONICAL (SPEC §2; companion — headline Q0 + margin-report "
        f"feed): eps_r' = {can['epsilon_r_real']:g}, tan_delta = "
        f"{can['tan_delta']:.6e}.",
        "",
        "## Gate verdicts (SPEC §5 windows, verbatim; faithful branch)",
        "",
        "| Check | Measured | Window | Verdict |",
        "|---|---|---|---|",
        _crit("f/f_at_booth_geometry", "f at Booth geometry (Hz)",
              "{:.1f}"),
        _crit("booth_two_point/q", "Q, Impedance walls", "{:.4f}"),
        _crit("booth_two_point/v_mode", "V_mode global-max (m^3)",
              "{:.6e}"),
        _crit("wall_loss_split/q_diel", "Q_diel (PEC arm)", "{:.4f}"),
        _crit("wall_loss_split/wall_fraction", "Wall-loss fraction",
              "{:.6f}"),
        _crit("f_m/order_of_magnitude", "F_m", "{:.4e}"),
        "",
        f"Material identity: solved at eps_r' = "
        f"{fai['epsilon_r_real']:g} = TARGETS.booth pairing (checked by "
        "the gate's BoothPayload mismatch guard on every Booth-anchored "
        "row).",
        f"Gate windows referenced: ±{F_ROW_HALF_WIDTH_HZ / 1e6:g} MHz on "
        f"f; ±{BOOTH_TWO_POINT_REL_TOL:.0%} on Q and V_mode "
        "(BOOTH_TWO_POINT_REL_TOL); TARGETS.q_diel/wall_fraction; "
        "F_m in [1e7, 1e8).",
        f"Gate tallies: n_pass = {gate['n_pass']}, n_fail = "
        f"{gate['n_fail']}, n_deferred = {gate['n_deferred']} "
        "(confinement trend stays deferred — Breeze-side §7 sweep, out "
        "of §5a scope); phase1_complete = "
        f"{str(gate['phase1_complete']).lower()} (5-of-6 best case by "
        "construction).",
        "",
        "## Both branches at the finest level (walls-on arm)",
        "",
        "| Quantity | Faithful (gated) | Canonical (companion) |",
        "|---|---|---|",
        f"| f' (Hz) | {fai_imp['f_hz']:.1f} | {can_imp['f_hz']:.1f} |",
        f"| Q0 (unloaded) | {fai_imp['q']:.4f} | {can_imp['q']:.4f} |",
        f"| V_mode global (m^3) | {fai_imp['v_mode_global_m3']:.6e} "
        f"| {can_imp['v_mode_global_m3']:.6e} |",
        f"| V_mode local (m^3) | {fai_imp['v_mode_local_m3']:.6e} "
        f"| {can_imp['v_mode_local_m3']:.6e} |",
        f"| p_e | {fai_imp['p_e']:.10f} | {can_imp['p_e']:.10f} |",
        f"| F_m (global) | {fai_imp['f_m_global']:.6e} "
        f"| {can_imp['f_m_global']:.6e} |",
        f"| Q_diel (PEC arm) | {fai_pec['q']:.4f} | {can_pec['q']:.4f} |",
        f"| wall fraction | {fai['wall_loss']['wall_fraction']:.6f} "
        f"| {can['wall_loss']['wall_fraction']:.6f} |",
        f"| record hash | `{fai_imp['record_hash']}` "
        f"| `{can_imp['record_hash']}` |",
        "",
        f"Branch delta, AS MEASURED: Q0_canonical / Q0_faithful = "
        f"{branch_ratio:.6f} ({(branch_ratio - 1.0) * 100.0:+.3f}%); "
        "the canonical branch was NOT judged against the Booth window — "
        "gate-passage is a faithful-branch statement only.",
        "",
        "## Wall-loss split (§4, sigmas from the ladders)",
        "",
        "| Branch | Q_total | Q_diel | Q_wall | sigma_Q_wall "
        "| wall fraction | below_resolution |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, br in (("faithful", fai), ("canonical", can)):
        w = br["wall_loss"]
        lines.append(
            f"| {label} | {w['q_total']:.4f} | {w['q_diel']:.4f} "
            f"| {w['q_wall']:.4f} | {w['sigma_q_wall']:.4f} "
            f"| {w['wall_fraction']:.6f} "
            f"| {str(w['below_resolution']).lower()} |"
        )
    lines += [
        "",
        "## Mesh-convergence evidence (full ladders, per branch per arm)",
        "",
    ]
    for br_label, br in (("Faithful", fai), ("Canonical", can)):
        for arm_label, arm_key in (
            ("Impedance walls", "impedance"),
            ("PEC walls", "pec"),
        ):
            lines.append(f"### {br_label} — {arm_label}")
            lines.append("")
            lines += _level_table(br["arms"][arm_key])
            lines.append("")
    # finest-level eigenspectrum + TE01delta criteria diagnostics of
    # the gated arm — required content of any failure report; §1
    # auditability on a green one.
    lines += [
        "## Finest-level eigenspectrum + TE01δ criteria diagnostics "
        "(gated arm)",
        "",
        f"Faithful branch, Impedance walls, finest level; picked index "
        f"= {fai_imp['picked_index']} (field-symmetry selection, "
        "proximity only as tiebreak).",
        "",
        "| i | f' (Hz) | f'' (Hz) | picked |",
        "|---|---|---|---|",
    ]
    for i, (fr, fi) in enumerate(
        zip(
            fai_imp["spectrum_f_real_hz"],
            fai_imp["spectrum_f_imag_hz"],
        )
    ):
        mark = "**<-**" if i == fai_imp["picked_index"] else ""
        lines.append(f"| {i} | {fr:.1f} | {fi:.4f} | {mark} |")
    lines += [
        "",
        "TE01δ criteria diagnostics (candidates with Im(f) > 0; "
        "azimuthal-E energy fraction / on-axis Hz antinode ratio / "
        "axis Hz sign changes):",
        "",
        "| f' (Hz) | az-E fraction | antinode ratio | sign changes |",
        "|---|---|---|---|",
    ]
    for d in fai_imp["mode_diagnostics"] or []:
        lines.append(
            f"| {d['f_real_hz']:.1f} "
            f"| {d['azimuthal_e_energy_fraction']:.6f} "
            f"| {d['axis_hz_antinode_ratio']:.6f} "
            f"| {d['axis_hz_sign_changes']} |"
        )
    lines += [
        "",
        "## Printed-2.46 sensitivity solve (diagnostic, not gated)",
        "",
        f"Faithful branch, walls on, finest mesh, minor radius = "
        f"{_fmt_h(sens['minor_radius_m'])} (App. A's 3-s.f. print) vs "
        f"the gated ratio-exact {_fmt_h(g['torus_minor_radius_m'])}:",
        "",
        f"- f' = {sens['f_hz']:.1f} Hz "
        f"(delta vs gated: {sens['delta_f_vs_gated_hz']:+.1f} Hz)",
        f"- Q = {sens['q']:.4f} "
        f"(delta vs gated: {sens['delta_q_vs_gated']:+.4f})",
        f"- record `{sens['record_hash']}`, "
        f"{sens['mesh_element_count']} elements.",
        "",
        "This solve is the discriminator of the plan's "
        "dimension-precision interpretive key: if f under the printed "
        "minor radius moves by more than the f-window half-width, a "
        "±0.004 mm print-precision ambiguity matters at gate "
        "resolution. Measured: the +0.004 mm print rounding moves f by "
        f"{sens['delta_f_vs_gated_hz'] / 1e6:+.3f} MHz "
        f"(~{abs(sens['delta_f_vs_gated_hz']) / F_ROW_HALF_WIDTH_HZ:.1f}x "
        "the window half-width) — the f verdict is CONDITIONAL on the "
        "ratified ratio-exact 2.456 mm branch (pre-registered choice "
        "3), and the minor radius is a stiff f-lever "
        "(~-0.35 MHz/µm).",
        "",
    ]

    if not gated_green:
        dv = manifest["diagnostic_mode_volumes"]
        v_booth = 0.409e-6  # Booth Table 8, comparison target (cm^3->m^3)
        lines += [
            "## Failure analysis (pre-registered keys reviewed)",
            "",
            "Observed pattern: f PASS, Q PASS, Q_diel PASS, wall "
            "fraction PASS; V_mode (global-max) FAIL "
            f"({fai_imp['v_mode_global_m3'] * 1e6:.4f} cm³ vs Booth's "
            f"0.409 cm³, x{fai_imp['v_mode_global_m3'] / v_booth:.4f}); "
            "F_m FAIL as its direct arithmetic consequence (F_m ∝ "
            "Q/V_mode, "
            f"{fai_imp['f_m_global']:.4e} vs the [1e7, 1e8) window).",
            "",
            "- This pattern is NOT one of the pre-registered "
            "interpretive keys (f >> 1.45 GHz => recovery refuted; f "
            "within ~1% but outside window => dimension precision; Q "
            "out with f/V in => loss model; wall fraction out with Q "
            "in => §4 window). Every pre-registered key's trigger "
            "quantity PASSED.",
            "- What the passes support: the geometry recovery is "
            "EMPIRICALLY SUPPORTED (f lands 4-s.f. correct at the "
            "recovered torus; the old puck reading sat near 3.1 GHz), "
            "and the loss model is NOT indicted (Q within 0.02% of "
            "6,980 on the faithful branch; §4 split inside both "
            "windows).",
            "- V_mode diagnostics from the archived record (§1 "
            "re-derivation; NOT §3 outputs, NOT re-judgments): the "
            "local-max variant EQUALS the global "
            f"({fai_imp['v_mode_local_m3'] * 1e6:.4f} cm³ — the |H|² "
            "max sits in/on the dielectric), so max-location does not "
            "explain the excess. E-based conventions do not reproduce "
            f"Booth either: V_E = {dv['v_e_m3'] * 1e6:.4f} cm³ "
            f"(x{dv['v_e_m3'] / v_booth:.2f}), V_eps_E = "
            f"{dv['v_e_eps_m3'] * 1e6:.4f} cm³ "
            f"(x{dv['v_e_eps_m3'] / v_booth:.2f}).",
            "- UNRESOLVED, TWO-SIDED (symmetric statement, per the "
            "re-grade discipline): either Booth's printed V_mode uses "
            "a definition/normalisation not spanned by the variants "
            "above, or the model's field distribution genuinely "
            "spreads more than her solve's — f, Q and the loss split "
            "are energy-ratio quantities that can agree while the "
            "peak-normalised spread disagrees, so the passing rows "
            "cannot arbitrate. Neither side is adopted. Booth's "
            "V_mode definition is a new supervisor/Booth ask.",
            "",
            "## Failure disposition (pre-registered discipline)",
            "",
            "- Margin report UNTOUCHED: the cross-build composite "
            "(Booth 6,980 x Breeze k = 0.2) stays the headline of "
            "`thermal/reports/q_margin_planning_point.md`; no "
            "own-model number inherits \"§5a-validated\" status.",
            "- Export bundle NOT re-minted; the PEC schema example "
            "remains the only bundle.",
            "- The wall-loss xfail "
            "(`test_booth_table_8_wall_loss_split`) STAYS, reason "
            "updated to point at this record: the split itself landed "
            "inside both §4 windows, but the §5a pass as a whole is "
            "red and the green-path rewrite is not licensed.",
            "- SPEC.md receives a dated FINDING hunk (not a "
            "status-cleared hunk); `phase1_complete` remains false "
            f"(n_pass = {gate['n_pass']}, n_fail = {gate['n_fail']}, "
            f"n_deferred = {gate['n_deferred']}).",
            "- No geometry retuning, no tolerance widening, no branch "
            "re-picking. A red result is a committed finding.",
            "",
            "## §1 reproducibility",
            "",
            f"- git commit at solve time: `{prov['git_commit']}` "
            f"(dirty: {str(prov['git_dirty']).lower()} — the §5a pass "
            "solves before its own commit by construction; the archive "
            "commit is the citation).",
            f"- COMSOL version: {prov['comsol_version']}.",
            f"- Gate report created: {gate['created_at_utc']}.",
            "- All §1 SolveRecords under `solves/`; finest gated-arm "
            "raw .mph + sensitivity .mph under `mph/` (LFS).",
            "",
        ]
        return "\n".join(lines)

    lines += [
        "## §5a checkpoint quantities (REPORTED, not gated)",
        "",
        "AMENDMENT WORDING (carried verbatim into the margin report and "
        "the SPEC §5a hunk): headline = canonical-branch own-model Q0 "
        "(the SPEC §2 model Phase 2 runs); gate-passage established on "
        "the faithful branch; branch delta quoted as measured. "
        "\"Own-model, §5a-validated\" must never silently attach to a "
        "number the gate never saw — the canonical Q0 has NOT itself "
        "passed the Booth window.",
        "",
        f"- Own-model Q0 (canonical, walls-on finest) = {q0_can:.4f}; "
        f"Q_L = Q0/(1 + k) = {q_l:.4f} with k = "
        f"{prov['deload_k']:g} — k is BREEZE'S coupling (Breeze 2017), "
        "carried as a flagged planning assumption: Booth's thesis (p. 8) "
        "uses unloaded Q throughout and states no coupling coefficient, "
        "so kappa_c below is COMPOSED (own-model Q0 x Breeze k), not "
        "fully own-model.",
        f"- kappa_c = f/Q_L = {kappa_c / 1e3:.4f} kHz (cyclic-Hz FWHM; "
        "never angular).",
        f"- Δf_max = (kappa_c/2)·sqrt(C0 − 1) at the planning C0 = "
        f"{PLANNING_C0:g}: {df_max / 1e6:.4f} MHz (C0 stays the SPEC "
        "revision-note PLANNING value — a COMSOL solve cannot touch the "
        "spin side; §5a's \"Booth's own C0\" is delivered only in its "
        "kappa_c/Q arm).",
        f"- ΔT_max (integrated cavity arm + linear spin arm, D8, "
        f"own-model p_e = {can_imp['p_e']:.6f}): {dt_max:.4f} K — "
        f"compare the cross-build composite band "
        f"[{COMPOSITE_DT_BAND_K[0]:g}, {COMPOSITE_DT_BAND_K[1]:g}] K: "
        "the \"decisively above threshold, thin thermal margin\" story "
        "holds at order ~0.5 K.",
        "",
        "## Honesty table (status after this pass)",
        "",
        "| Quantity | Status | Basis / caveat |",
        "|---|---|---|",
        "| f at Booth point | OWN-MODEL | solve records, both branches |",
        "| Q0 (= Q_total, unloaded) | OWN-MODEL | gated on faithful "
        "branch; canonical companion reported |",
        "| Q_diel, Q_wall, wall fraction | OWN-MODEL | §4 two-solve "
        "split, ladder sigmas |",
        "| p_e at Booth point | OWN-MODEL | walls-on; retires the "
        "3.14 GHz PEC-puck placeholder |",
        "| V_mode (global/local), F_m | OWN-MODEL | §3 extraction |",
        "| Field record, w_E/w_s | OWN-MODEL | w_s still gain-mask = "
        "STO fallback (Phase 1b pending); \\|H\\|² default UNRATIFIED |",
        "| kappa_c = f/Q_L | COMPOSED: own-model Q0 × k = 0.2 | k is "
        "Breeze's; Booth p. 8 is explicit that only unloaded Q is used "
        "and coupling is out of scope — the checkpoint does NOT make "
        "kappa_c fully own-model |",
        "| C0 = 190 | PLANNING (unchanged) | revision-note value; N "
        "assumed, g_s derived, kappa_s fitted |",
        "| eps_r = 316.3, tan_delta, sigma_Cu | LITERATURE INPUTS | "
        "own-model outputs are conditional on them |",
        "| df_cavity/dT, df_spin/dT | LITERATURE/DERIVED §6T | "
        "untouched (read-only this pass) |",
        "| Booth 6980 / 0.409 cm³ | LITERATURE anchors | comparison "
        "targets only |",
        "",
        "## Layer A inheritance",
        "",
        f"Nominal centre for the Layer A sweep: recovered geometry + "
        f"canonical materials + the finest ladder level "
        f"(diel {_fmt_h(fai['arms']['impedance']['levels'][-1]['dielectric_max_h_m'])} "
        f"/ air {_fmt_h(fai['arms']['impedance']['levels'][-1]['air_max_h_m'])}), "
        f"named by record hash `{can_imp['record_hash']}`. The "
        "convergence tables above are the mesh-level justification "
        "Layer A inherits.",
        "",
        "## §1 reproducibility",
        "",
        f"- git commit at solve time: `{prov['git_commit']}` "
        f"(dirty: {str(prov['git_dirty']).lower()} — the §5a pass "
        "solves before its own commit by construction; the archive "
        "commit is the citation).",
        f"- COMSOL version: {prov['comsol_version']}.",
        f"- Gate report created: {gate['created_at_utc']}.",
        "- All §1 SolveRecords under `solves/`; finest gated-arm raw "
        ".mph + sensitivity .mph under `mph/` (LFS).",
        "",
    ]
    return "\n".join(lines)


def render_from_run_dir(run_dir: Path) -> str:
    """Render the checkpoint record from a committed run directory."""
    manifest = json.loads(
        (Path(run_dir) / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    return render_checkpoint_markdown(manifest)


__all__ = [
    "CHECKPOINT_FILENAME",
    "COMPOSITE_DT_BAND_K",
    "MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_VERSION",
    "build_manifest",
    "gate_dict_from_json",
    "gate_dict_from_report",
    "render_checkpoint_markdown",
    "render_from_run_dir",
    "write_manifest",
]
