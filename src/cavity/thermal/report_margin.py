"""SPEC §7.T4 — Q-margin planning-point report (2026-07-09).

Renders `thermal/reports/q_margin_planning_point.md`: the single labeled
numeric instance of the §7.T4 budget maps (`cavity.thermal.detuning`).
Deterministic output (fixed pass date, fixed formatting) so the
committed report is pinned byte-for-byte in
tests/test_thermal_detuning.py — the report_3a.py precedent, text-only.

Provenance of every input:
- Q0 = `TARGETS.booth.q_factor`, k = `DELOAD_K`, f = `TARGET.f_design_hz`
  (single-sourced §6 constants);
- p_e read from the committed frozen §8 gate export bundle
  (`refs/exports/...` — record hash cited in the report), NOT a fresh
  literal;
- C0 rows are SPEC-cited planning values (revision note: "Breeze's
  build runs C ~ 190") — deliberately NOT graduated into
  `provenance/constants.py`: no measured C0 exists (the provenance
  table's ingredients are N assumed, g_s derived, kappa_s fitted), and
  the constant slot belongs to the §5a own-model checkpoint.

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
    TARGETS,
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

PASS_DATE = "2026-07-09"

# SPEC revision-note planning values ("Breeze's build runs C ~ 190");
# 50 / 500 bracket the sqrt(C0 - 1) insensitivity. Never measured — see
# module docstring for why no provenance constant exists.
PLANNING_C0_ROWS = (50.0, 190.0, 500.0)
PLANNING_C0 = 190.0

_REPO_ROOT = Path(__file__).resolve().parents[3]
GATE_BUNDLE_META = (
    _REPO_ROOT
    / "refs"
    / "exports"
    / "20260709T160320Z_gate_888536d768e0fba1"
    / "export_meta.json"
)


def _gate_p_e() -> tuple[float, str]:
    """(p_e, record_hash) from the committed frozen gate export bundle."""
    with GATE_BUNDLE_META.open(encoding="utf-8") as fh:
        meta = json.load(fh)
    return float(meta["summary"]["p_e"]), str(meta["summary"]["record_hash"])


def build_report() -> str:
    """The full markdown report as a deterministic string."""
    f_hz = TARGET.f_design_hz
    t_base = DF_CAVITY_DT.t_window_lo_k  # 293 K — the operating baseline
    p_e, record_hash = _gate_p_e()

    q_l = q_loaded(TARGETS.booth.q_factor)
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
        "- CROSS-BUILD COMPOSITE: this point composes Booth's Q0 = "
        f"{TARGETS.booth.q_factor:g} (Booth Table 8) with Breeze's "
        f"de-loading k = {DELOAD_K:g} (Breeze 2017; Wu's coupling "
        "unstated, SPEC §11 item 3). The resulting "
        f"Δf_max ≈ {df_max_headline / 1e6:.2f} MHz is NEITHER build's "
        "number — it is a planning composite and must not be quoted as "
        "Booth's or Breeze's margin.",
        "- §5a GATE (R5): no own-model C0/kappa_c exists — the §5 gate "
        "is not passed (frozen gate report: `phase1_complete: false`; "
        "the only frozen solve is the §8 PEC convention-check anchor). "
        "The §5a checkpoint run supersedes every number here before any "
        "§7.T4 statement becomes a claim.",
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
        f"- Q0 = {TARGETS.booth.q_factor:g} -> Q_L = Q0/(1 + k) = "
        f"{q_l:.2f}.",
        f"- kappa_c = f/Q_L = {kappa_c / 1e3:.3f} kHz — CYCLIC-Hz FWHM "
        "linewidth, never the angular 2*pi*f/Q_L (the provenance "
        "table's verified W20 angular-\"Hz\" trap; guarded in anchor "
        "A6).",
        f"- p_e = {p_e!r} from the frozen §8 gate export bundle "
        f"(record hash `{record_hash}`) — a PEC anchor-solve value "
        "(3.14 GHz, a/L = 0.5 puck), the pre-Phase-1b placeholder for "
        "Booth-geometry p_e; it moves these numbers by ~0.2%.",
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
