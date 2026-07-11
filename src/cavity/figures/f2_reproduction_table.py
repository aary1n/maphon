"""F2 — Booth reproduction table-as-figure (the honesty table).

Data source (disk): the RE-BASED §5a record's
`checkpoint_manifest.json` (`refs/gate_runs/20260711T132705Z_rejudge/`
— branches, gate checks + re-based windows, `diagnostic_mode_volumes`,
tallies; every solve record cites the immutable 2026-07-10 source
archive) — verbatim values, render-time compute is ratios/deltas only.
Booth prints come from `TARGETS.booth`; the corrected anchors from
`BOOTH_IMPLIED_V_MODE_M3` / `BOOTH_TABLE8_REVOLUTION_FACTOR` (SPEC §5a
finding 2026-07-11: her printed V is 225/360 of the true integral —
partial-revolution dataset, mechanism read from the tradition .mph).
One additional diagnostics row is computed at figure-build time from
the SAME archived finest-level grid F1 loads (canonical record
`823e67969516bcf2`): the DIELECTRIC-RESTRICTED magnetic integral
∭_torus |H|² dV / |H|²_max, torus mask taken from the geometry
fingerprint (centre r = 6.14 mm, minor radius 2.456 mm) — retained as
forensic evidence that no computed convention variant reproduces the
raw print; only the 225/360 factor does.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cavity.extraction.quadrature import axisymmetric_volume_integral
from cavity.figures.f1_mode_maps import (
    CANONICAL_RECORD_HASH,
    archive_provenance,
    load_archive_record,
)
from cavity.provenance.constants import (
    BOOTH_IMPLIED_F_M,
    BOOTH_IMPLIED_V_MODE_M3,
    BOOTH_TABLE8_REVOLUTION_FACTOR,
    TARGETS,
)

REJUDGE_RUN_DIR = "20260711T132705Z_rejudge"
REJUDGE_MANIFEST_PATH = (
    Path(__file__).resolve().parents[3]
    / "refs"
    / "gate_runs"
    / REJUDGE_RUN_DIR
    / "checkpoint_manifest.json"
)

CAPTION = (
    "Booth reproduction at the recovered TE01δ torus (`refs/booth_geometry_recovery.md`), §5a "
    "re-based 2026-07-11 (re-judgment record `refs/gate_runs/20260711T132705Z_rejudge`; solves from the "
    "immutable 2026-07-10 archive `refs/gate_runs/20260710T083340Z_live_comsol`, gated record "
    "`2b276c4424e49bb9` — no new solve): own-model values on the FAITHFUL material branch (tanδ = "
    "1.054×10⁻⁴, the .mph-exact unrounded Debye value, `BOOTH_MPH_TAN_DELTA`) judged against the "
    "re-based §5 windows — ALL LIVE-JUDGED ROWS PASS. The 2026-07-10 V_mode FAIL (×1.60) is RESOLVED: "
    "Booth's printed 0.409 cm³ is 225/360 = 0.625 of the true integral — her mode-volume numerator was "
    "evaluated on a Revolution-2D dataset left at COMSOL's default 225° partial revolution while the "
    "max-denominator is angle-invariant (mechanism read from the tradition .mph's results tree, "
    "`refs/comsol/booth/2D Resonator Lossy.mph`; anapole model in hand, TE01δ row by uniform-workflow "
    "inference; Booth-side written confirmation PENDING — `docs/booth_vmode_findings_note.md`). "
    "Corrected, the Booth-implied true V_mode = 0.409/0.625 = 0.6544 cm³ vs own-model 0.6558 — +0.21%, "
    "PASS inside the UNCHANGED ±1% tolerance (window BASIS re-derived per §11 item 8, never widened); "
    "her Table 8 is internally consistent per row, the factor is uniform, and her comparative "
    "conclusions survive intact. F_m re-scoped (a TIGHTENING): the Booth point now takes ±1% "
    "consistency vs the corrected Booth-implied F_m = 7.164×10⁶ (own 7.144×10⁶, −0.27%, PASS — the old "
    "order-10⁷ window there was satisfiable only through the inflated print and moves to the "
    "confinement endpoint, deferred). f (4 s.f.), Q₀ (+0.02% vs 6.98×10³), Q_diel and the wall-loss "
    "fraction PASS as before. The variant diagnostics (local-max identical; E-based 0.859 / 0.480 cm³; "
    "dielectric-restricted 0.181 cm³, from the same archived finest-level grid F1 loads) stand as the "
    "forensic record that no convention variant reproduces the raw print — only the 225/360 factor "
    "does (committed × 0.625 = 0.4099 ≈ 0.409). Branch discipline unchanged: gate-passage is a "
    "faithful-branch statement; the canonical companion (tanδ = 1.1×10⁻⁴, Q₀ = 6764.6, the SPEC §2 "
    "model Phase 2 runs — now the margin report's own-model headline) was never judged against the ±1% "
    "window; branch delta AS MEASURED −3.10%. Tallies 5 pass / 0 fail / 1 deferred (confinement trend — "
    "Breeze-side sweep); `phase1_complete` remains false on that deferred row: §5a benchmark PASS is "
    "not phase completion."
)


def dielectric_restricted_v_mode_m3() -> float:
    """∭_torus |H|² dV / |H|²_max (global max) — the amendment diagnostic.

    Computed from the same archived finest-level canonical grid F1
    loads; the torus mask comes from the geometry FINGERPRINT (centre
    r = 6.14 mm at the box mid-plane, minor radius 2.456 mm), not from
    any new geometry input. Figure diagnostic only — NOT a §3 output,
    NOT a gate row.
    """
    record = load_archive_record(CANONICAL_RECORD_HASH)
    fields = record.field_sample
    geom = record.fingerprint["geometry"]
    h_sq = np.real(np.sum(fields.h_complex * np.conj(fields.h_complex), axis=1))
    mask = (fields.r_m - geom["dielectric_radius_m"]) ** 2 + (
        fields.z_m - geom["box_height_m"] / 2.0
    ) ** 2 <= geom["dielectric_minor_radius_m"] ** 2
    integral = float(
        np.real(
            axisymmetric_volume_integral(
                np.where(mask, h_sq, 0.0), fields.r_m, fields.weights_m2
            )
        )
    )
    return integral / float(np.max(h_sq))


def build_data() -> dict:
    """Manifest-verbatim values + ratios/deltas + the forensic rows (pure)."""
    with REJUDGE_MANIFEST_PATH.open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    faithful = manifest["branches"]["faithful"]
    canonical = manifest["branches"]["canonical"]
    fin = faithful["arms"]["impedance"]["finest"]
    checks = {c["name"]: c for c in manifest["gate"]["checks"]}
    booth = TARGETS.booth

    def verdict(name: str) -> str:
        return "PASS" if checks[name]["status"] == "pass" else "FAIL"

    f_hz = fin["f_hz"]
    q0_faithful = fin["q"]
    q0_canonical = canonical["arms"]["impedance"]["finest"]["q"]
    v_mode_m3 = fin["v_mode_global_m3"]
    f_m = fin["f_m_global"]
    q_diel = faithful["wall_loss"]["q_diel"]
    wall_fraction = faithful["wall_loss"]["wall_fraction"]
    diag_v = manifest["diagnostic_mode_volumes"]
    v_check = checks["booth_two_point/v_mode"]
    v_window = (v_check["lo"], v_check["hi"])
    v_diel_restricted = dielectric_restricted_v_mode_m3()

    def cm3(v: float) -> float:
        return v * 1e6

    rows = [
        {
            "quantity": "f (MHz)",
            "target": "1450 · window ±0.5 MHz",
            "own": f"{f_hz / 1e6:.3f}",
            "delta": f"+{(f_hz - booth.f_hz) / booth.f_hz * 100:.3f}%",
            "verdict": verdict("f/f_at_booth_geometry"),
        },
        {
            "quantity": "Q₀ (walls on)",
            "target": "6,980 · window ±1%",
            "own": f"{q0_faithful:.2f}",
            "delta": f"+{(q0_faithful - booth.q_factor) / booth.q_factor * 100:.2f}%",
            "verdict": verdict("booth_two_point/q"),
        },
        {
            "quantity": "Q_diel (PEC arm)",
            "target": "window [9,000, 10,000]",
            "own": f"{q_diel:.1f}",
            "delta": "in window",
            "verdict": verdict("wall_loss_split/q_diel"),
        },
        {
            "quantity": "Wall-loss fraction",
            "target": "window [0.23, 0.27]",
            "own": f"{wall_fraction:.5f}",
            "delta": "in window",
            "verdict": verdict("wall_loss_split/wall_fraction"),
        },
        {
            "quantity": "V_mode, magnetic global-max (cm³)",
            "target": "0.6544 implied (0.409/(225/360)) · window ±1%",
            "own": f"{cm3(v_mode_m3):.4f}",
            "delta": (
                f"+{(v_mode_m3 / BOOTH_IMPLIED_V_MODE_M3 - 1) * 100:.2f}%"
            ),
            "verdict": verdict("booth_two_point/v_mode"),
        },
        {
            "quantity": "F_m (magnetic Purcell)",
            "target": "7.164×10⁶ implied · window ±1%",
            "own": f"{f_m:.3e}",
            "delta": f"{(f_m / BOOTH_IMPLIED_F_M - 1) * 100:.2f}%",
            "verdict": verdict("f_m/booth_consistency"),
        },
    ]

    diagnostics = [
        {
            "label": "|H|² global-max (the §3 convention)",
            "value_cm3": cm3(v_mode_m3),
            "ratio": f"×{v_mode_m3 / booth.v_mode_m3:.2f}",
        },
        {
            "label": "|H|² local-max (dielectric)",
            "value_cm3": cm3(fin["v_mode_local_m3"]),
            "ratio": "identical",
        },
        {
            "label": "E-based (∭|E|²dV / |E|²_max)",
            "value_cm3": cm3(diag_v["v_e_m3"]),
            "ratio": f"×{diag_v['v_e_m3'] / booth.v_mode_m3:.2f}",
        },
        {
            "label": "ε-weighted E",
            "value_cm3": cm3(diag_v["v_e_eps_m3"]),
            "ratio": f"×{diag_v['v_e_eps_m3'] / booth.v_mode_m3:.2f}",
        },
        {
            "label": "dielectric-restricted magnetic (∭_torus|H|²dV / |H|²_max)",
            "value_cm3": cm3(v_diel_restricted),
            "ratio": f"×{v_diel_restricted / booth.v_mode_m3:.2f}",
        },
        {
            "label": "committed × 225/360 (Booth's partial-revolution emulation)",
            "value_cm3": cm3(v_mode_m3 * BOOTH_TABLE8_REVOLUTION_FACTOR),
            "ratio": (
                f"×{v_mode_m3 * BOOTH_TABLE8_REVOLUTION_FACTOR / booth.v_mode_m3:.4f}"
            ),
        },
    ]

    gate = manifest["gate"]
    return {
        "rows": rows,
        "diagnostics": diagnostics,
        "v_diel_restricted_m3": v_diel_restricted,
        "v_diel_in_window": v_window[0] <= v_diel_restricted <= v_window[1],
        "v_window_m3": tuple(v_window),
        "q0_faithful": q0_faithful,
        "q0_canonical": q0_canonical,
        "branch_delta_pct": (q0_canonical / q0_faithful - 1.0) * 100.0,
        "n_pass": gate["n_pass"],
        "n_fail": gate["n_fail"],
        "n_deferred": gate["n_deferred"],
        "phase1_complete": gate["phase1_complete"],
        "gated_record_hash": "2b276c4424e49bb9",
        "rejudge_run_dir": manifest["run_dir"],
        "source_run_dir": manifest["judgment"]["source_run_dir"],
        **archive_provenance(),
    }


def render(data: dict):
    from cavity.figures import _style

    _style.apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(8.8, 5.6), constrained_layout=True)
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0.055, 1)

    cols = (0.01, 0.33, 0.56, 0.72, 0.87)
    headers = (
        "Quantity",
        "Booth print / §5 window",
        "Own (faithful)",
        "Δ or ratio",
        "Verdict",
    )
    y = 0.97
    ax.text(
        0.01, y,
        "Booth reproduction — §5a re-based 2026-07-11 (faithful branch; "
        "solves = archived 2026-07-10 run, no new solve)",
        fontsize=10.5, fontweight="bold", color=_style.INK,
    )
    y -= 0.055
    for x, h in zip(cols, headers):
        ax.text(x, y, h, fontsize=8.0, fontweight="bold", color=_style.INK_MUTED)
    y -= 0.012
    ax.plot([0.0, 1.0], [y, y], color=_style.INK_MUTED, lw=0.8)

    row_h = 0.052
    for row in data["rows"]:
        y -= row_h
        if row["verdict"].startswith("FAIL"):
            ax.add_patch(
                Rectangle(
                    (0.0, y - 0.014), 1.0, row_h,
                    facecolor=_style.FAIL_RED, alpha=0.14, edgecolor="none",
                )
            )
        # the long parenthetical becomes a starred footnote under the table
        verdict = "FAIL*" if "(" in row["verdict"] else row["verdict"]
        cells = (row["quantity"], row["target"], row["own"], row["delta"], verdict)
        for x, cell in zip(cols, cells):
            bold = cell.startswith(("PASS", "FAIL"))
            colour = (
                _style.FAIL_RED
                if cell.startswith("FAIL")
                else (_style.GREEN if cell.startswith("PASS") else _style.INK)
            )
            ax.text(
                x, y, cell, fontsize=8.0,
                fontweight="bold" if bold else "normal", color=colour,
            )
    y -= 0.014
    ax.plot([0.0, 1.0], [y, y], color=_style.INK_MUTED, lw=0.8)
    y -= 0.032
    ax.text(
        0.01, y,
        "V/F_m windows re-based on the corrected Booth-implied anchors (×360/225 — "
        "finding 2026-07-11); tolerances unchanged at ±1%.",
        fontsize=7.0, color=_style.INK_MUTED,
    )

    y -= 0.05
    ax.text(
        0.01, y,
        "V_mode variants (forensic diagnostics, not §3 outputs) — ratios vs the raw print 0.409 cm³; "
        "only the 225/360 factor resolves it",
        fontsize=8.5, fontweight="bold", color=_style.INK,
    )
    for d in data["diagnostics"]:
        y -= 0.042
        ax.text(0.03, y, d["label"], fontsize=8.0, color=_style.INK)
        ax.text(0.60, y, f"{d['value_cm3']:.4f} cm³", fontsize=8.0, color=_style.INK)
        ax.text(0.76, y, d["ratio"], fontsize=8.0, color=_style.INK_MUTED)
    y -= 0.028
    ax.plot([0.0, 1.0], [y, y], color=_style.GRID, lw=0.8)

    y -= 0.045
    ax.text(
        0.01, y,
        "×1.60 RESOLVED (finding 2026-07-11): Booth’s printed V is 225/360 = 0.625 of the true integral — "
        "partial-revolution dataset numerator,",
        fontsize=7.6, color=_style.INK,
    )
    y -= 0.035
    ax.text(
        0.01, y,
        "angle-invariant max denominator (mechanism in the tradition .mph’s results tree). Booth-implied true "
        "V = 0.6544 cm³; own +0.21%. Written confirmation pending.",
        fontsize=7.6, color=_style.INK,
    )

    y -= 0.05
    ax.text(
        0.01, y,
        f"Branches: faithful Q₀ = {data['q0_faithful']:.2f} (gated) / canonical Q₀ = "
        f"{data['q0_canonical']:.2f} (SPEC §2 model; feeds Phase 2) — delta as measured "
        f"{data['branch_delta_pct']:.2f}%.",
        fontsize=7.6, color=_style.INK_MUTED,
    )
    y -= 0.035
    ax.text(
        0.01, y,
        f"Gate tallies: {data['n_pass']} pass / {data['n_fail']} fail / {data['n_deferred']} deferred · "
        f"phase1_complete = {str(data['phase1_complete']).lower()}",
        fontsize=7.6, color=_style.INK_MUTED,
    )

    dirty = " (dirty)" if data["archive_dirty"] else ""
    _style.provenance_footer(
        fig,
        f"verdicts refs/gate_runs/{data['rejudge_run_dir']} · solves refs/gate_runs/{data['source_run_dir']} · "
        f"gated record {data['gated_record_hash']} · archive commit {data['archive_commit'][:7]}{dirty} · "
        f"diagnostic variant from record {CANONICAL_RECORD_HASH}",
    )
    return fig


def main(out_dir: Path | None = None) -> list[Path]:
    from cavity.figures import _style

    fig = render(build_data())
    paths = _style.save_figure(fig, "f2_reproduction_table", out_dir)
    for p in paths:
        print(f"wrote {p}")
    return paths


if __name__ == "__main__":
    main()
