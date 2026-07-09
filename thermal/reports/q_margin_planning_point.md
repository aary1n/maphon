# SPEC §7.T4 — Q-margin planning point (2026-07-09)

**Status: planning-point evaluation of the §7.T4 budget maps (`cavity.thermal.detuning`) — NOT a claim.** Regenerate with `python -m cavity.thermal.report_margin`; pinned byte-for-byte in `tests/test_thermal_detuning.py`.

## Status notes

- SPEC §7.T4 rung: the Q-margin QUESTION is supervisor-endorsed (Oxborrow-verbal 2026-07-06); the RESULT is unratified — these are budget maps and a planning point, not the joint C0/kappa_c DOF derivation (Layer A; SPEC §11 item 9).
- CROSS-BUILD COMPOSITE: this point composes Booth's Q0 = 6980 (Booth Table 8) with Breeze's de-loading k = 0.2 (Breeze 2017; Wu's coupling unstated, SPEC §11 item 3). The resulting Δf_max ≈ 1.71 MHz is NEITHER build's number — it is a planning composite and must not be quoted as Booth's or Breeze's margin.
- §5a GATE (R5): no own-model C0/kappa_c exists — the §5 gate is not passed (frozen gate report: `phase1_complete: false`; the only frozen solve is the §8 PEC convention-check anchor). The §5a checkpoint run supersedes every number here before any §7.T4 statement becomes a claim.
- LAYER-A BOUNDARY: the joint C0/kappa_c dependence on the geometry DOFs (the §7.T4 headline requirement, SPEC §11 item 9) is NOT derived here — these are the per-draw maps and one composite point.
- COMMON-DELTA-T TWO-ARMS CONVENTION (D8, planning assumption — proposed for the SPEC §11 item-10 bundle): both arms evaluated at the crystal's probe-weighted mean temperature rise because the crystal->STO thermal path is unmodelled (D7). Direction conservative — overstates detuning, understates ΔT_max/P_max; magnitude unmodelled; retires via D7 or a ruled ΔT_STO/ΔT_crystal ratio.
- probe weight is a UNIFORM-OVER-CRYSTAL PLACEHOLDER, not the SPEC §7.T5(b) gain-region w_s (Phase 1b bore + crystal unbuilt; crystal-frame co-registration pending) — spin-arm numbers inherit UNRATIFIED-w_s status doubly until Phase 1b supplies w_s.

## Planning point

- f = 1.45 GHz (`TARGET.f_design_hz`); T_base = 293 K (§6T window floor).
- Q0 = 6980 -> Q_L = Q0/(1 + k) = 5816.67.
- kappa_c = f/Q_L = 249.284 kHz — CYCLIC-Hz FWHM linewidth, never the angular 2*pi*f/Q_L (the provenance table's verified W20 angular-"Hz" trap; guarded in anchor A6).
- p_e = 0.9976566720273174 from the frozen §8 gate export bundle (record hash `888536d768e0fba1`) — a PEC anchor-solve value (3.14 GHz, a/L = 0.5 puck), the pre-Phase-1b placeholder for Booth-geometry p_e; it moves these numbers by ~0.2%.

## Δf_max = (kappa_c/2)·sqrt(C0 − 1)

| C0 (planning) | Δf_max (MHz) |
|---|---|
| 50 | 0.8725 |
| 190 | 1.7135 |
| 500 | 2.7843 |

C0 = 190 is the SPEC revision-note planning value ("Breeze's build runs C ~ 190") — never a measured constant (provenance table: N assumed, g_s derived, kappa_s fitted). The sqrt(C0 − 1) insensitivity is the point of the bracket rows: x10 in C0 moves Δf_max by ~x3.2.

## ΔT_max at C0 = 190

- Adopted map (integrated-CW cavity arm + linear spin arm, common-ΔT convention D8): **ΔT_max = 0.5843 K**.
- Band across the §6T coefficient bands (linear arithmetic — the sub-K regime): [0.567, 0.725] K.
- Committed-point-slope companion (`cavity_df_dt_hz_per_k(293)`·p_e + |df_spin/dT|): 0.5735 K — the documented <=2% eps_r-mixing branch between the self-consistent-CW map and the canonical-eps_r point function (detuning.py docstring; anchor C3).
- Nonlinearity at this scale is negligible (<0.1%): the integrated form earns its keep across the ruled 30 K envelope (anchor A10: +0.7% vs the 300 K point slope x 30, +6.6% vs the first-order integral of the committed slope, -4.6% vs the 293 K slope x 30), not at the sub-K budget point.
- Reproduces the revision-note margin story ("order ~0.5 K kills it") through committed functions instead of Wu-coefficient arithmetic.

## P_max

Deferred to a BC-ruled instance: `p_max_w` exists (exact by the transport core's linearity in P) but a headline number would stack the D1 BC planning assumptions plus the k_PTP band and l_abs scoping values — a distinct assumption stack from this point. No number is quoted here.
