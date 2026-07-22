# SPEC §7.T4 — Q-margin planning point (2026-07-13)

**Status: planning-point evaluation of the §7.T4 budget maps (`cavity.thermal.detuning`) — NOT a claim.** Regenerate with `python -m cavity.thermal.report_margin`; pinned byte-for-byte in `tests/test_thermal_detuning.py`.

## Status notes

- SPEC §7.T4 rung: the Q-margin QUESTION is supervisor-endorsed (Oxborrow-verbal 2026-07-06); the RESULT is unratified — these are budget maps and a planning point, not the joint C0/kappa_c DOF derivation (Layer A; SPEC §11 item 9).
- TWO-LINEWIDTH LAW (re-derived 2026-07-13, the steady-crossing-linewidths pass): Δf_max = ((kappa_c + kappa_s)/2)·sqrt(C0 − 1) — the linearised two-mode threshold with frequency pulling (oscillation at the linewidth-weighted mean); the previously committed (kappa_c/2)·sqrt(C0 − 1) is its kappa_s -> 0 limit and understated the margin x6.4 here. At this operating point kappa_c/kappa_s ≈ 0.18 — the far side of the kappa_c ≈ kappa_s turnover — so the §7.T4 1/sqrt(Q) hypothesis INVERTS SIGN: the Q-margin exponent is ≈ +0.35, not −1/2 (`thermal/reports/q_margin_turnover.md`). FINDING UNRATIFIED — needs Oxborrow before headline use (findings note drafted, not sent).
- OWN-MODEL Q0, COMPOSED kappa_c (re-based 2026-07-11, superseding the cross-build composite): Q0 = 6764.59 is the OWN-MODEL canonical-branch walls-on finest value from the re-based §5a record (`refs/gate_runs/20260711T132705Z_rejudge/`, record hash `823e67969516bcf2`) — the SPEC §2 model Phase 2 runs. BRANCH ATTRIBUTION (amendment wording): gate-passage is established on the FAITHFUL branch (tan_delta = BOOTH_MPH_TAN_DELTA, Q0 = 6981.32, +0.02% vs Booth's 6,980); the canonical Q0 has NOT itself passed the Booth window (branch delta -3.10% as measured). kappa_c stays COMPOSED: own-model Q0 x Breeze's k = 0.2 (Breeze 2017; Booth p. 8 uses unloaded Q throughout and states no coupling; Wu's coupling unstated, SPEC §11 item 3) — the resulting Δf_max ≈ 11.69 MHz is NOT fully own-model and must not be quoted as a measured margin.
- kappa_s rung: the graded STATIC planning branch (`KAPPA_S`, provenance/constants.py) — Cowley-Semple linewidth table (scraped thread, 2026-06-26), 0.1% Pc-d14:PTP-d14 branch choice; band [0.550, 1.750] MHz spans the Pc:PTP host rows only. Caveats carried: best-per-host at differing MW/laser powers — NOT a controlled comparison; the ODMR FWHM folds homogeneous + inhomogeneous + power broadening into one number (the single-packet mapping is a threshold-model assumption); the maser crystal itself (0.053% protonated) matches no table row. kappa_s is temperature-dependent in reality — the kappa_s(ΔT) feedback via `cavity.thermal.broadening` is the flagged follow-on, NOT implemented.
- C0-IMPORT CONVENTION: C0 = 200 is imported as the resonant cooperativity and NOT recomputed from kappa_s (no G^2 exists — Phase 1b). Direction of bias (ratified amendment C): sweeping kappa_s at fixed imported C0 holds G^2/kappa_c fixed; at fixed G the growth is ~sqrt(kappa_s), so the kappa_s-hi edge of the Δf_max band below is OVERSTATED under the import convention — the band is not convention-independent. At fixed imported C0, SMALLER kappa_s is the conservative side (the superseded kappa_s -> 0 law was the maximally conservative member).
- §5a GATE (R5): the §5a benchmark is PASSED as re-based 2026-07-11 (5 pass / 0 fail / 1 deferred — SPEC §5a finding: V window re-based on the 225/360-corrected Booth print, F_m tightened to ±1% consistency; tolerances unchanged). `phase1_complete` remains false on the deferred confinement row — §5a benchmark PASS is NOT phase completion, and Phase 2 claim levels still gate on §7.T5.
- LAYER-A BOUNDARY: the joint C0/kappa_c dependence on the geometry DOFs (the §7.T4 headline requirement, SPEC §11 item 9) is NOT derived here — these are the per-draw maps and one composite point.
- COMMON-DELTA-T TWO-ARMS CONVENTION (D8, planning assumption — proposed for the SPEC §11 item-10 bundle): both arms evaluated at the crystal's probe-weighted mean temperature rise because the crystal->STO thermal path is unmodelled (D7). Direction conservative — overstates detuning, understates ΔT_max/P_max; magnitude unmodelled; retires via D7 or a ruled ΔT_STO/ΔT_crystal ratio.
- probe weight is a UNIFORM-OVER-CRYSTAL PLACEHOLDER, not the SPEC §7.T5(b) gain-region w_s (Phase 1b crystal unbuilt; crystal-frame co-registration pending) — spin-arm numbers inherit UNRATIFIED-w_s status doubly until Phase 1b supplies w_s.

## Planning point

- f = 1.45 GHz (`TARGET.f_design_hz`); T_base = 293 K (§6T window floor).
- Q0 = 6764.5852 (OWN-MODEL, canonical branch — Booth Table 8's 6,980 is now the comparison anchor, not the input) -> Q_L = Q0/(1 + k) = 5637.15.
- kappa_c = f/Q_L = 257.222 kHz — CYCLIC-Hz FWHM linewidth, never the angular 2*pi*f/Q_L (the provenance table's verified W20 angular-"Hz" trap; guarded in anchor A6).
- kappa_s = 1.400 MHz - spin-line FWHM, CYCLIC Hz (`KAPPA_S`; Cowley-Semple linewidth table, 0.1% d14 branch; band [0.550, 1.750] MHz).
- p_e = 0.9974999896719232 — OWN-MODEL walls-on canonical value at the Booth point from the re-based §5a record (record hash `823e67969516bcf2`); retires the 3.14 GHz PEC-anchor placeholder this report previously carried.

## Δf_max = ((kappa_c + kappa_s)/2)·sqrt(C0 − 1)

| C0 (planning) | Δf_max (MHz) |
|---|---|
| 50 | 5.8003 |
| 200 | 11.6890 |
| 500 | 18.5098 |

C0 = 200 is the ELICITED planning value (`C0_PLANNING`: Oxborrow-verbal 2026-07-21, quoted with his stated best-case condition, notes archived at calibration/data/raw/oxborrow_meeting_notes_2026-07-21/, written confirmation pending; supersedes the 2026-07-13-era SPEC revision-note reading "Breeze's build runs C ~ 190", preserved as the dated prior value) — still never a measured constant (provenance table: N assumed, g_s derived, kappa_s fitted). NOT ratification of the two-linewidth law, the turnover result, or the margin framing (UNRATIFIED, findings note pending). The sqrt(C0 − 1) insensitivity is the point of the bracket rows: x10 in C0 moves Δf_max by ~x3.2.
- kappa_s band on Δf_max at C0 = 200: [5.6936, 14.1577] MHz (linear in kappa_s).

## ΔT_max at C0 = 200

- Adopted map (integrated-CW cavity arm + linear spin arm, common-ΔT convention D8): **ΔT_max = 3.9990 K**.
- Band across the §6T coefficient bands (linear arithmetic, at point-kappa_s): [3.871, 4.945] K.
- Combined kappa_s x coefficient outer envelope: [1.885, 5.989] K (kappa_s-lo x coefficient-hi ... kappa_s-hi x coefficient-lo).
- Committed-point-slope companion (`cavity_df_dt_hz_per_k(293)`·p_e + |df_spin/dT|): 3.9130 K — the documented <=2% eps_r-mixing branch between the self-consistent-CW map and the canonical-eps_r point function (detuning.py docstring; anchor C3).
- Linear band arithmetic retained as the band convention; the true-inversion vs pure-CW-linear discrepancy at this O(4 K) scale is 0.38% (was <0.1% in the superseded sub-K regime), invisible against the kappa_s-band and coefficient-band systematics. Envelope-scale context unchanged (anchor A10).
- Reproduces the revision-note margin story ("order ~0.5 K kills it") through committed functions instead of Wu-coefficient arithmetic.

## P_max

Deferred to a BC-ruled instance: `p_max_w` exists (exact by the transport core's linearity in P) but a headline number would stack the D1 BC planning assumptions plus the k_PTP band and l_abs scoping values — a distinct assumption stack from this point. No number is quoted here.
