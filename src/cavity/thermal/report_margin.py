"""SPEC §7.T4 — Q-margin planning-point report (2026-07-13).

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
  (REVERSED 2026-07-21: C0 is now GRADUATED — `C0_PLANNING` = 200.0,
  ELICITED / supervisor-verbal 2026-07-21, notes archived at
  calibration/data/raw/oxborrow_meeting_notes_2026-07-21/, written
  confirmation pending. Still not measured — the "no measured C0"
  clause above stays true; the not-graduated rationale is what the
  elicitation superseded. The 190 era is preserved as a dated prior
  value in the constant's docstring. Guard, verbatim: Oxborrow's
  C0 = 200 grades the planning cooperativity only; it is NOT
  ratification of the two-linewidth threshold law, the turnover
  result, or the margin framing, which remain UNRATIFIED pending the
  findings note.)

Usage:  python -m cavity.thermal.report_margin [--out thermal/reports]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cavity.provenance.constants import (
    C0_PLANNING,
    DELOAD_K,
    DF_CAVITY_DT,
    DF_SPIN_DT,
    KAPPA_S,
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

PASS_DATE = "2026-07-13"

# The graduated planning cooperativity (`C0_PLANNING`, ELICITED /
# supervisor-verbal 2026-07-21 — 190-era record in its docstring);
# 50 / 500 bracket the sqrt(C0 - 1) insensitivity. Still never
# measured. The module-level name is kept: report_turnover.py and the
# test layer import PLANNING_C0 from here.
PLANNING_C0 = C0_PLANNING.c0
PLANNING_C0_ROWS = (50.0, PLANNING_C0, 500.0)

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
    kappa_s = KAPPA_S.kappa_s_hz

    rows = []
    for c0 in PLANNING_C0_ROWS:
        df_max = delta_f_max_hz(c0, kappa_c, kappa_s)
        rows.append(f"| {c0:g} | {df_max / 1e6:.4f} |")

    df_max_headline = delta_f_max_hz(PLANNING_C0, kappa_c, kappa_s)
    df_lo = delta_f_max_hz(
        PLANNING_C0, kappa_c, KAPPA_S.kappa_s_band_lo_hz
    )
    df_hi = delta_f_max_hz(
        PLANNING_C0, kappa_c, KAPPA_S.kappa_s_band_hi_hz
    )
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
    ratio = dt_max / (
        df_max_headline
        / (
            f_hz
            * p_e
            / (2.0 * (t_base - DF_CAVITY_DT.curie_weiss_t0_k))
            + abs(DF_SPIN_DT.df_dt_hz_per_k)
        )
    )

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
        "- TWO-LINEWIDTH LAW (re-derived 2026-07-13, the "
        "steady-crossing-linewidths pass): Δf_max = "
        "((kappa_c + kappa_s)/2)·sqrt(C0 − 1) — the linearised two-mode "
        "threshold with frequency pulling (oscillation at the "
        "linewidth-weighted mean); the previously committed "
        "(kappa_c/2)·sqrt(C0 − 1) is its kappa_s -> 0 limit and "
        "understated the margin x6.4 here. At this operating point "
        "kappa_c/kappa_s ≈ 0.18 — the far side of the "
        "kappa_c ≈ kappa_s turnover — so the §7.T4 1/sqrt(Q) hypothesis "
        "INVERTS SIGN: the Q-margin exponent is ≈ +0.35, not −1/2 "
        "(`thermal/reports/q_margin_turnover.md`). FINDING UNRATIFIED — "
        "needs Oxborrow before headline use (findings note drafted, "
        "not sent).",
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
        f"- kappa_s rung: the graded STATIC planning branch (`KAPPA_S`, "
        "provenance/constants.py) — Cowley-Semple linewidth table "
        "(scraped thread, 2026-06-26), 0.1% Pc-d14:PTP-d14 branch "
        f"choice; band [{KAPPA_S.kappa_s_band_lo_hz/1e6:.3f}, "
        f"{KAPPA_S.kappa_s_band_hi_hz/1e6:.3f}] MHz spans the Pc:PTP "
        "host rows only. Caveats carried: best-per-host at differing "
        "MW/laser powers — NOT a controlled comparison; the ODMR FWHM "
        "folds homogeneous + inhomogeneous + power broadening into one "
        "number (the single-packet mapping is a threshold-model "
        "assumption); the maser crystal itself (0.053% protonated) "
        "matches no table row. kappa_s is temperature-dependent in "
        "reality — the kappa_s(ΔT) feedback via "
        "`cavity.thermal.broadening` is the flagged follow-on, NOT "
        "implemented.",
        f"- C0-IMPORT CONVENTION: C0 = {PLANNING_C0:g} is imported as "
        "the resonant cooperativity and NOT recomputed from kappa_s (no "
        "G^2 exists — Phase 1b). Direction of bias (ratified amendment "
        "C): sweeping "
        "kappa_s at fixed imported C0 holds G^2/kappa_c fixed; at fixed "
        "G the growth is ~sqrt(kappa_s), so the kappa_s-hi edge of the "
        "Δf_max band below is OVERSTATED under the import convention — "
        "the band is not convention-independent. At fixed imported C0, "
        "SMALLER kappa_s is the conservative side (the superseded "
        "kappa_s -> 0 law was the maximally conservative member).",
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
        f"- kappa_s = {kappa_s/1e6:.3f} MHz - spin-line FWHM, CYCLIC Hz "
        "(`KAPPA_S`; Cowley-Semple linewidth table, 0.1% d14 branch; "
        f"band [{KAPPA_S.kappa_s_band_lo_hz/1e6:.3f}, "
        f"{KAPPA_S.kappa_s_band_hi_hz/1e6:.3f}] MHz).",
        f"- p_e = {p_e!r} — OWN-MODEL walls-on canonical value at the "
        "Booth point from the re-based §5a record (record hash "
        f"`{record_hash}`); retires the 3.14 GHz PEC-anchor "
        "placeholder this report previously carried.",
        "",
        "## Δf_max = ((kappa_c + kappa_s)/2)·sqrt(C0 − 1)",
        "",
        "| C0 (planning) | Δf_max (MHz) |",
        "|---|---|",
        *rows,
        "",
        f"C0 = {PLANNING_C0:g} is the ELICITED planning value "
        "(`C0_PLANNING`: Oxborrow-verbal 2026-07-21, quoted with his "
        "stated best-case condition, notes archived at "
        "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/, "
        "written confirmation pending; supersedes the 2026-07-13-era "
        "SPEC revision-note reading \"Breeze's build runs C ~ 190\", "
        "preserved as the dated prior value) — still never a measured "
        "constant (provenance table: N assumed, g_s derived, kappa_s "
        "fitted). NOT ratification of the two-linewidth law, the "
        "turnover result, or the margin framing (UNRATIFIED, findings "
        "note pending). "
        "The sqrt(C0 − 1) insensitivity is the point of the bracket "
        "rows: x10 in C0 moves Δf_max by ~x3.2.",
        f"- kappa_s band on Δf_max at C0 = {PLANNING_C0:g}: "
        f"[{df_lo/1e6:.4f}, {df_hi/1e6:.4f}] MHz (linear in kappa_s).",
        "",
        f"## ΔT_max at C0 = {PLANNING_C0:g}",
        "",
        f"- Adopted map (integrated-CW cavity arm + linear spin arm, "
        f"common-ΔT convention D8): **ΔT_max = {dt_max:.4f} K**.",
        f"- Band across the §6T coefficient bands (linear arithmetic, "
        f"at point-kappa_s): [{dt_max_lo:.3f}, {dt_max_hi:.3f}] K.",
        f"- Combined kappa_s x coefficient outer envelope: "
        f"[{df_lo/diff_hi:.3f}, {df_hi/diff_lo:.3f}] K "
        "(kappa_s-lo x coefficient-hi ... kappa_s-hi x "
        "coefficient-lo).",
        f"- Committed-point-slope companion "
        f"(`cavity_df_dt_hz_per_k({t_base:g})`·p_e + |df_spin/dT|): "
        f"{dt_max_committed:.4f} K — the documented <=2% eps_r-mixing "
        "branch between the self-consistent-CW map and the canonical-"
        "eps_r point function (detuning.py docstring; anchor C3).",
        "- Linear band arithmetic retained as the band convention; the "
        "true-inversion vs pure-CW-linear discrepancy at this O(4 K) "
        f"scale is {(ratio-1)*100:.2f}% (was <0.1% in the superseded "
        "sub-K regime), invisible against the kappa_s-band and "
        "coefficient-band systematics. Envelope-scale context unchanged "
        "(anchor A10).",
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
