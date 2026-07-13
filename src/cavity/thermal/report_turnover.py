"""SPEC §7.T4 turnover map — the 2026-07-13 two-linewidth object.

This report replaces the bare -1/2 Q-margin exponent with the general
pulled-oscillator law

    Delta_f_max = ((kappa_c + kappa_s)/2) * sqrt(C0 - 1).

The turnover map is drawn at FIXED G and kappa_s: C0 = c*Q_L, with c
calibrated so C0 = `PLANNING_C0` at the planning Q_L. By contrast, the
planning-point report imports C0 directly and does not recompute it from
kappa_s. The own-model Q0 x DELOAD_K -> kappa_c composition is
single-sourced via `report_margin.own_model_point()` (ratified amendment
B: one kappa_c, one f).

Usage:  python -m cavity.thermal.report_turnover [--out thermal/reports]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from cavity.provenance.constants import KAPPA_S, TARGET
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.detuning import (
    Q_MARGIN_RUNG,
    delta_f_max_hz,
    q_loaded,
    q_margin_exponent,
)
from cavity.thermal.report_margin import (
    PLANNING_C0,
    REJUDGE_RUN_DIR,
    own_model_point,
)

PASS_DATE = "2026-07-13"

_REPO_ROOT = Path(__file__).resolve().parents[3]
_Q_L_GRID = (
    32.0,
    56.0,
    100.0,
    178.0,
    316.0,
    562.0,
    1000.0,
    1778.0,
    3162.0,
    10000.0,
    31623.0,
    100000.0,
    1000000.0,
)


def _turnover_roots(
    f_hz: float, kappa_s_hz: float, c_per_q: float
) -> tuple[float, float] | None:
    """Closed-form Q_L roots, or None when the discriminant is negative."""
    a = f_hz / kappa_s_hz
    discriminant = a * a - 8.0 * a / c_per_q
    if discriminant < 0.0:
        return None
    root = math.sqrt(discriminant)
    return (0.5 * (a - root), 0.5 * (a + root))


def build_report() -> str:
    """Return the deterministic SPEC §7.T4 turnover report."""
    own = own_model_point()
    f_hz = TARGET.f_design_hz
    q0 = own["q0_canonical"]
    q_l = q_loaded(q0)
    kappa_c = resonance_linewidth_hz(f_hz, q_l)
    kappa_s = KAPPA_S.kappa_s_hz
    c_per_q = PLANNING_C0 / q_l
    c0_at_symmetric = c_per_q * f_hz / kappa_s

    roots = _turnover_roots(f_hz, kappa_s, c_per_q)
    if roots is None:  # guarded by the ratified planning-point inputs
        raise ValueError("planning turnover map has no real crossings")
    q_minus, q_plus = roots
    operating_exponent = q_margin_exponent(PLANNING_C0, kappa_c, kappa_s)

    rows = []
    for q_value in sorted((*_Q_L_GRID, q_l)):
        row_kappa_c = resonance_linewidth_hz(f_hz, q_value)
        row_c0 = c_per_q * q_value
        if row_c0 <= 1.0:
            df_text = "—"
            exponent_text = "—"
        else:
            df_text = (
                f"{delta_f_max_hz(row_c0, row_kappa_c, kappa_s)/1e6:.4f}"
            )
            exponent_text = f"{q_margin_exponent(row_c0, row_kappa_c, kappa_s):+.4f}"
        rows.append(
            f"| {q_value:.4f} | {row_kappa_c/kappa_s:.6f} | "
            f"{row_c0:.6f} | {df_text} | {exponent_text} |"
        )

    band_lines = []
    for band_kappa_s in (
        KAPPA_S.kappa_s_band_lo_hz,
        KAPPA_S.kappa_s_band_hi_hz,
    ):
        # Fixed G: c = 4G^2/(f*kappa_s), so c rescales inversely with
        # kappa_s away from the nominal calibration point.
        band_c = c_per_q * kappa_s / band_kappa_s
        band_roots = _turnover_roots(f_hz, band_kappa_s, band_c)
        if band_roots is None:
            crossing_text = "no real crossings"
        else:
            crossing_text = (
                f"Q_- = {band_roots[0]:.4g}, Q_+ = {band_roots[1]:.4g}"
            )
        band_lines.append(
            f"- kappa_s = {band_kappa_s/1e6:.3f} MHz: {crossing_text} "
            "(fixed-G rescaling of c)."
        )

    lines = [
        f"# SPEC §7.T4 — Q-margin turnover map ({PASS_DATE})",
        "",
        "**Status: deterministic two-linewidth turnover map — the new "
        "§7.T4 object replacing the bare -1/2 exponent.** Regenerate with "
        "`python -m cavity.thermal.report_turnover`.",
        "",
        "## Parameters",
        "",
        f"- f = {f_hz/1e9:.2f} GHz (`TARGET.f_design_hz`).",
        f"- Q0 = {q0:.4f} (OWN-MODEL canonical branch, re-based §5a "
        f"record `refs/gate_runs/{REJUDGE_RUN_DIR}/`, record hash "
        f"`{own['record_hash']}`).",
        f"- Q_L = Q0/(1 + k) = {q_l:.4f}.",
        f"- kappa_c = f/Q_L = {kappa_c/1e3:.3f} kHz (CYCLIC-Hz FWHM).",
        f"- kappa_s = {kappa_s/1e6:.3f} MHz (`KAPPA_S`, CYCLIC-Hz FWHM; "
        f"band [{KAPPA_S.kappa_s_band_lo_hz/1e6:.3f}, "
        f"{KAPPA_S.kappa_s_band_hi_hz/1e6:.3f}] MHz).",
        f"- c = PLANNING_C0/Q_L = {c_per_q:.9f}, calibrated so C0 = "
        f"{PLANNING_C0:g} at the planning Q_L.",
        "",
        f"## Derivation summary ({PASS_DATE})",
        "",
        "- Eigenvalue threshold: C0 = 1 + "
        "4*Delta^2/(kappa_c+kappa_s)^2.",
        "- Pulled frequency: omega = "
        "(kappa_c*omega_s + kappa_s*omega_c)/(kappa_c+kappa_s).",
        "- Threshold margin: Delta_f_max = "
        "((kappa_c+kappa_s)/2)*sqrt(C0-1).",
        "- Fixed-G, fixed-kappa_s exponent under kappa_c = f/Q_L and "
        "C0 = c*Q_L: E = -kappa_c/(kappa_c+kappa_s) + "
        "C0/(2*(C0-1)).",
        "- Turnover: Q_L^2 - (f/kappa_s)*Q_L + "
        "2*(f/kappa_s)/c = 0; real roots exist iff C0 evaluated at "
        "kappa_c = kappa_s is >= 8.",
        "",
        "## Q_L map",
        "",
        "| Q_L | kappa_c/kappa_s | C0 = c*Q_L | Delta_f_max (MHz) | E |",
        "|---:|---:|---:|---:|---:|",
        *rows,
        "",
        "Rows with C0 <= 1 are below threshold and print an em-dash for "
        "Delta_f_max and E.",
        "",
        "## Crossings",
        "",
        f"- Closed-form roots (4 s.f.): Q_- = {q_minus:.4g}, "
        f"Q_+ = {q_plus:.4g}.",
        f"- Large-C0 reference: f/kappa_s = {f_hz/kappa_s:.4g}.",
        f"- Existence condition: C0 at kappa_c = kappa_s is "
        f"{c0_at_symmetric:.4f} >= 8, so both roots are real.",
        f"- Operating point: Q_L = {q_l:.4f}, E = "
        f"{operating_exponent:+.4f}, kappa_c/kappa_s = "
        f"{kappa_c/kappa_s:.3f}; far side of the turnover - the "
        "committed -1/2 scaling's regime is kappa_c >> kappa_s.",
        "",
        "## kappa_s-band sensitivity",
        "",
        *band_lines,
        "",
        "## Status notes",
        "",
        f"- {Q_MARGIN_RUNG}.",
        "- FIXED-G vs C0-IMPORT: this map varies Q_L at fixed G and "
        "kappa_s (C0 = c*Q_L); the planning-point report imports C0 = "
        "190 directly. The joint C0/kappa_c/kappa_s dependence on the "
        "geometry DOFs is Layer A (SPEC section 11 item 9) - not derived "
        "here.",
        "- SIGN-INVERSION FINDING (derived 2026-07-13, UNRATIFIED - needs "
        "supervisor ratification before headline use): at the operating "
        "point the Q-margin exponent is ~ +0.35, not -1/2; the committed "
        "1/sqrt(Q) law is the kappa_s -> 0 limit.",
        "- KAPPA_S is the static, T-independent planning branch; thermal "
        "kappa_s(Delta_T) feedback remains outside this turnover map.",
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
    out_path = out_dir / "q_margin_turnover.md"
    out_path.write_text(build_report(), encoding="utf-8", newline="\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
