"""SPEC §7.T4 — Q-margin planning-point report (2026-07-09).

Renders `thermal/reports/q_margin_planning_point.md`: the single labeled
numeric instance of the §7.T4 budget maps (`cavity.thermal.detuning`).
Deterministic output (fixed pass date, fixed formatting) so the
committed report is pinned byte-for-byte in
tests/test_thermal_detuning.py — the report_3a.py precedent, text-only.

Provenance of every input (RE-BASED 2026-07-11 — the §5a re-judgment
is GREEN, `refs/gate_runs/20260711T132705Z_rejudge/`, so the
pre-registered own-model rebase is licensed):
- Q0 = the OWN-MODEL canonical-branch walls-on finest Q0 read from the
  re-based §5a checkpoint manifest (record hash cited in the report) —
  the SPEC §2 model Phase 2 runs. Branch attribution (amendment
  wording, carried verbatim): gate-passage is established on the
  FAITHFUL branch; the canonical Q0 has NOT itself passed the Booth
  window (branch delta -3.10% as measured).
- k = `DELOAD_K`, f = `TARGET.f_design_hz` (single-sourced §6
  constants); kappa_c stays COMPOSED (own-model Q0 x Breeze's k = 0.2
  — Booth states no coupling; SPEC §11 item 3);
- p_e = the own-model walls-on canonical p_e from the same manifest —
  retires the 3.14 GHz PEC-anchor placeholder this report previously
  carried;
- C0 rows are SPEC-cited planning values (revision note: "Breeze's
  build runs C ~ 190") — deliberately NOT graduated into
  `provenance/constants.py`: no measured C0 exists (the provenance
  table's ingredients are N assumed, g_s derived, kappa_s fitted); the
  §5a checkpoint delivers only the kappa_c/Q arm of "Booth's own C0".

Usage:  python -m cavity.thermal.report_margin [--out thermal/reports]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cavity.provenance.constants import (
    DELOAD_K,
    DF_CAVITY_DT,
    DF_SPIN_DT,
    TARGET,
)
from cavity.provenance.constants import cavity_df_dt_hz_per_k
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.detuning import (
    COMMON_DELTA_T_NOTE,
    Q_MARGIN_RUNG,
    UNIFORM_PLACEHOLDER_RUNG,
    delta_f_max_hz,
    delta_t_max_k,
    q_loaded,
)

PASS_DATE = "2026-07-11"

# SPEC revision-note planning values ("Breeze's build runs C ~ 190");
# 50 / 500 bracket the sqrt(C0 - 1) insensitivity. Never measured — see
# module docstring for why no provenance constant exists.
PLANNING_C0_ROWS = (50.0, 190.0, 500.0)
PLANNING_C0 = 190.0

_REPO_ROOT = Path(__file__).resolve().parents[3]
# The re-based §5a record (GREEN, 5/0/1 — SPEC §5a finding 2026-07-11);
# its manifest carries the own-model canonical-branch numbers verbatim
# from the archived solves.
REJUDGE_RUN_DIR = "20260711T132705Z_rejudge"
REJUDGE_MANIFEST = (
    _REPO_ROOT
    / "refs"
    / "gate_runs"
    / REJUDGE_RUN_DIR
    / "checkpoint_manifest.json"
)


def own_model_point() -> dict:
    """Own-model canonical-branch numbers from the re-based §5a record.

    Returns q0_canonical, q0_faithful (for the branch-attribution
    line), p_e (walls-on canonical), the canonical record hash, and
    the gate tallies — all read from the committed manifest, never
    re-typed."""
    with REJUDGE_MANIFEST.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    can = manifest["branches"]["canonical"]["arms"]["impedance"]["finest"]
    fai = manifest["branches"]["faithful"]["arms"]["impedance"]["finest"]
    gate = manifest["gate"]
    return {
        "q0_canonical": float(can["q"]),
        "q0_faithful": float(fai["q"]),
        "p_e": float(can["p_e"]),
        "record_hash": str(can["record_hash"]),
        "n_pass": gate["n_pass"],
        "n_fail": gate["n_fail"],
        "n_deferred": gate["n_deferred"],
        "phase1_complete": gate["phase1_complete"],
    }


def build_report() -> str:
    """The full markdown report as a deterministic string."""
    f_hz = TARGET.f_design_hz
    t_base = DF_CAVITY_DT.t_window_lo_k  # 293 K — the operating baseline
    own = own_model_point()
    p_e, record_hash = own["p_e"], own["record_hash"]
    q0 = own["q0_canonical"]
    branch_delta_pct = (own["q0_canonical"] / own["q0_faithful"] - 1.0) * 100.0

    q_l = q_loaded(q0)
    kappa_c = resonance_linewidth_hz(f_hz, q_l)

    rows = []
    for c0 in PLANNING_C0_ROWS:
        df_max = delta_f_max_hz(c0, kappa_c)
        rows.append(f"| {c0:g} | {df_max / 1e6:.4f} |")

    df_max_headline = delta_f_max_hz(PLANNING_C0, kappa_c)
    dt_max = delta_t_max_k(df_max_headline, t_base, f_hz=f_hz, p_e=p_e)

    # band: linear arithmetic across the two §6T coefficient bands
    # (sub-K regime — the nonlinearity is <0.1% here, stated below)
    diff_lo = DF_CAVITY_DT.df_dt_band_lo_hz_per_k + abs(
        DF_SPIN_DT.df_dt_band_hi_hz_per_k
    )
    diff_hi = DF_CAVITY_DT.df_dt_band_hi_hz_per_k + abs(
        DF_SPIN_DT.df_dt_band_lo_hz_per_k
    )
    dt_max_hi = df_max_headline / diff_lo
    dt_max_lo = df_max_headline / diff_hi

    # committed-point-slope companion (the ≤2% mixing branch, anchor C3)
    diff_committed = cavity_df_dt_hz_per_k(t_base) * p_e + abs(
        DF_SPIN_DT.df_dt_hz_per_k
    )
    dt_max_committed = df_max_headline / diff_committed

    lines = [
        f"# SPEC §7.T4 — Q-margin planning point ({PASS_DATE})",
        "",
        "**Status: planning-point evaluation of the §7.T4 budget maps "
        "(`cavity.thermal.detuning`) — NOT a claim.** Regenerate with "
        "`python -m cavity.thermal.report_margin`; pinned byte-for-byte "
        "in `tests/test_thermal_detuning.py`.",
        "",
        "## Status notes",
        "",
        f"- {Q_MARGIN_RUNG}.",
        "- OWN-MODEL Q0, COMPOSED kappa_c (re-based 2026-07-11, "
        "superseding the cross-build composite): Q0 = "
        f"{q0:.2f} is the OWN-MODEL canonical-branch walls-on finest "
        "value from the re-based §5a record "
        f"(`refs/gate_runs/{REJUDGE_RUN_DIR}/`, record hash "
        f"`{record_hash}`) — the SPEC §2 model Phase 2 runs. BRANCH "
        "ATTRIBUTION (amendment wording): gate-passage is established "
        "on the FAITHFUL branch (tan_delta = BOOTH_MPH_TAN_DELTA, Q0 = "
        f"{own['q0_faithful']:.2f}, +0.02% vs Booth's 6,980); the "
        "canonical Q0 has NOT itself passed the Booth window (branch "
        f"delta {branch_delta_pct:+.2f}% as measured). kappa_c stays "
        f"COMPOSED: own-model Q0 x Breeze's k = {DELOAD_K:g} (Breeze "
        "2017; Booth p. 8 uses unloaded Q throughout and states no "
        "coupling; Wu's coupling unstated, SPEC §11 item 3) — the "
        "resulting Δf_max ≈ "
        f"{df_max_headline / 1e6:.2f} MHz is NOT fully own-model and "
        "must not be quoted as a measured margin.",
        "- §5a GATE (R5): the §5a benchmark is PASSED as re-based "
        f"2026-07-11 ({own['n_pass']} pass / {own['n_fail']} fail / "
        f"{own['n_deferred']} deferred — SPEC §5a finding: V window "
        "re-based on the 225/360-corrected Booth print, F_m tightened "
        "to ±1% consistency; tolerances unchanged). `phase1_complete` "
        f"remains {str(own['phase1_complete']).lower()} on the "
        "deferred confinement row — §5a benchmark PASS is NOT phase "
        "completion, and Phase 2 claim levels still gate on §7.T5.",
        "- LAYER-A BOUNDARY: the joint C0/kappa_c dependence on the "
        "geometry DOFs (the §7.T4 headline requirement, SPEC §11 "
        "item 9) is NOT derived here — these are the per-draw maps and "
        "one composite point.",
        f"- {COMMON_DELTA_T_NOTE}",
        f"- {UNIFORM_PLACEHOLDER_RUNG}.",
        "",
        "## Planning point",
        "",
        f"- f = {f_hz / 1e9:.2f} GHz (`TARGET.f_design_hz`); "
        f"T_base = {t_base:g} K (§6T window floor).",
        f"- Q0 = {q0:.4f} (OWN-MODEL, canonical branch — Booth Table "
        "8's 6,980 is now the comparison anchor, not the input) -> "
        f"Q_L = Q0/(1 + k) = {q_l:.2f}.",
        f"- kappa_c = f/Q_L = {kappa_c / 1e3:.3f} kHz — CYCLIC-Hz FWHM "
        "linewidth, never the angular 2*pi*f/Q_L (the provenance "
        "table's verified W20 angular-\"Hz\" trap; guarded in anchor "
        "A6).",
        f"- p_e = {p_e!r} — OWN-MODEL walls-on canonical value at the "
        "Booth point from the re-based §5a record (record hash "
        f"`{record_hash}`); retires the 3.14 GHz PEC-anchor "
        "placeholder this report previously carried.",
        "",
        "## Δf_max = (kappa_c/2)·sqrt(C0 − 1)",
        "",
        "| C0 (planning) | Δf_max (MHz) |",
        "|---|---|",
        *rows,
        "",
        f"C0 = {PLANNING_C0:g} is the SPEC revision-note planning value "
        "(\"Breeze's build runs C ~ 190\") — never a measured constant "
        "(provenance table: N assumed, g_s derived, kappa_s fitted). "
        "The sqrt(C0 − 1) insensitivity is the point of the bracket "
        "rows: x10 in C0 moves Δf_max by ~x3.2.",
        "",
        f"## ΔT_max at C0 = {PLANNING_C0:g}",
        "",
        f"- Adopted map (integrated-CW cavity arm + linear spin arm, "
        f"common-ΔT convention D8): **ΔT_max = {dt_max:.4f} K**.",
        f"- Band across the §6T coefficient bands (linear arithmetic — "
        f"the sub-K regime): [{dt_max_lo:.3f}, {dt_max_hi:.3f}] K.",
        f"- Committed-point-slope companion "
        f"(`cavity_df_dt_hz_per_k({t_base:g})`·p_e + |df_spin/dT|): "
        f"{dt_max_committed:.4f} K — the documented <=2% eps_r-mixing "
        "branch between the self-consistent-CW map and the canonical-"
        "eps_r point function (detuning.py docstring; anchor C3).",
        "- Nonlinearity at this scale is negligible (<0.1%): the "
        "integrated form earns its keep across the ruled 30 K envelope "
        "(anchor A10: +0.7% vs the 300 K point slope x 30, +6.6% vs "
        "the first-order integral of the committed slope, -4.6% vs the "
        "293 K slope x 30), not at the sub-K budget point.",
        "- Reproduces the revision-note margin story (\"order ~0.5 K "
        "kills it\") through committed functions instead of "
        "Wu-coefficient arithmetic.",
        "",
        "## P_max",
        "",
        "Deferred to a BC-ruled instance: `p_max_w` exists (exact by the "
        "transport core's linearity in P) but a headline number would "
        "stack the D1 BC planning assumptions plus the k_PTP band and "
        "l_abs scoping values — a distinct assumption stack from this "
        "point. No number is quoted here.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(_REPO_ROOT / "thermal" / "reports"),
        help="output directory (default: thermal/reports at repo root)",
    )
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "q_margin_planning_point.md"
    out_path.write_text(build_report(), encoding="utf-8", newline="\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
