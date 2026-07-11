# SPEC §7.T4 — Q-margin planning point (2026-07-11)

**Status: planning-point evaluation of the §7.T4 budget maps (`cavity.thermal.detuning`) — NOT a claim.** Regenerate with `python -m cavity.thermal.report_margin`; pinned byte-for-byte in `tests/test_thermal_detuning.py`.

## Status notes

- SPEC §7.T4 rung: the Q-margin QUESTION is supervisor-endorsed (Oxborrow-verbal 2026-07-06); the RESULT is unratified — these are budget maps and a planning point, not the joint C0/kappa_c DOF derivation (Layer A; SPEC §11 item 9).
- OWN-MODEL Q0, COMPOSED kappa_c (re-based 2026-07-11, superseding the cross-build composite): Q0 = 6764.59 is the OWN-MODEL canonical-branch walls-on finest value from the re-based §5a record (`refs/gate_runs/20260711T132705Z_rejudge/`, record hash `823e67969516bcf2`) — the SPEC §2 model Phase 2 runs. BRANCH ATTRIBUTION (amendment wording): gate-passage is established on the FAITHFUL branch (tan_delta = BOOTH_MPH_TAN_DELTA, Q0 = 6981.32, +0.02% vs Booth's 6,980); the canonical Q0 has NOT itself passed the Booth window (branch delta -3.10% as measured). kappa_c stays COMPOSED: own-model Q0 x Breeze's k = 0.2 (Breeze 2017; Booth p. 8 uses unloaded Q throughout and states no coupling; Wu's coupling unstated, SPEC §11 item 3) — the resulting Δf_max ≈ 1.77 MHz is NOT fully own-model and must not be quoted as a measured margin.
- §5a GATE (R5): the §5a benchmark is PASSED as re-based 2026-07-11 (5 pass / 0 fail / 1 deferred — SPEC §5a finding: V window re-based on the 225/360-corrected Booth print, F_m tightened to ±1% consistency; tolerances unchanged). `phase1_complete` remains false on the deferred confinement row — §5a benchmark PASS is NOT phase completion, and Phase 2 claim levels still gate on §7.T5.
- LAYER-A BOUNDARY: the joint C0/kappa_c dependence on the geometry DOFs (the §7.T4 headline requirement, SPEC §11 item 9) is NOT derived here — these are the per-draw maps and one composite point.
- COMMON-DELTA-T TWO-ARMS CONVENTION (D8, planning assumption — proposed for the SPEC §11 item-10 bundle): both arms evaluated at the crystal's probe-weighted mean temperature rise because the crystal->STO thermal path is unmodelled (D7). Direction conservative — overstates detuning, understates ΔT_max/P_max; magnitude unmodelled; retires via D7 or a ruled ΔT_STO/ΔT_crystal ratio.
- probe weight is a UNIFORM-OVER-CRYSTAL PLACEHOLDER, not the SPEC §7.T5(b) gain-region w_s (Phase 1b bore + crystal unbuilt; crystal-frame co-registration pending) — spin-arm numbers inherit UNRATIFIED-w_s status doubly until Phase 1b supplies w_s.

## Planning point

- f = 1.45 GHz (`TARGET.f_design_hz`); T_base = 293 K (§6T window floor).
- Q0 = 6764.5852 (OWN-MODEL, canonical branch — Booth Table 8's 6,980 is now the comparison anchor, not the input) -> Q_L = Q0/(1 + k) = 5637.15.
- kappa_c = f/Q_L = 257.222 kHz — CYCLIC-Hz FWHM linewidth, never the angular 2*pi*f/Q_L (the provenance table's verified W20 angular-"Hz" trap; guarded in anchor A6).
- p_e = 0.9974999896719232 — OWN-MODEL walls-on canonical value at the Booth point from the re-based §5a record (record hash `823e67969516bcf2`); retires the 3.14 GHz PEC-anchor placeholder this report previously carried.

## Δf_max = (kappa_c/2)·sqrt(C0 − 1)

| C0 (planning) | Δf_max (MHz) |
|---|---|
| 50 | 0.9003 |
| 190 | 1.7681 |
| 500 | 2.8730 |

C0 = 190 is the SPEC revision-note planning value ("Breeze's build runs C ~ 190") — never a measured constant (provenance table: N assumed, g_s derived, kappa_s fitted). The sqrt(C0 − 1) insensitivity is the point of the bracket rows: x10 in C0 moves Δf_max by ~x3.2.

## ΔT_max at C0 = 190

- Adopted map (integrated-CW cavity arm + linear spin arm, common-ΔT convention D8): **ΔT_max = 0.6030 K**.
- Band across the §6T coefficient bands (linear arithmetic — the sub-K regime): [0.585, 0.748] K.
- Committed-point-slope companion (`cavity_df_dt_hz_per_k(293)`·p_e + |df_spin/dT|): 0.5919 K — the documented <=2% eps_r-mixing branch between the self-consistent-CW map and the canonical-eps_r point function (detuning.py docstring; anchor C3).
- Nonlinearity at this scale is negligible (<0.1%): the integrated form earns its keep across the ruled 30 K envelope (anchor A10: +0.7% vs the 300 K point slope x 30, +6.6% vs the first-order integral of the committed slope, -4.6% vs the 293 K slope x 30), not at the sub-K budget point.
- Reproduces the revision-note margin story ("order ~0.5 K kills it") through committed functions instead of Wu-coefficient arithmetic.

## P_max

Deferred to a BC-ruled instance: `p_max_w` exists (exact by the transport core's linearity in P) but a headline number would stack the D1 BC planning assumptions plus the k_PTP band and l_abs scoping values — a distinct assumption stack from this point. No number is quoted here.
