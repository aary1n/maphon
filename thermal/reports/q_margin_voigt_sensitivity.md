# SPEC §7.T4 — Voigt/multi-packet sensitivity of the two-linewidth margin (2026-07-20)

**Status: sensitivity AUDIT of the committed law's single-packet mapping — NOT a claim, NOT a kappa_s re-grade, and NOT a resolution of the open D4 decomposition.** Regenerate with `python -m cavity.thermal.report_voigt`; pinned byte-for-byte in `tests/test_thermal_ensemble_threshold.py` (anchors V1-V10).

## Status notes

- SPEC §7.T4 rung: the Q-margin QUESTION is supervisor-endorsed (Oxborrow-verbal 2026-07-06); the RESULT is unratified — these are budget maps and a planning point, not the joint C0/kappa_c DOF derivation (Layer A; SPEC §11 item 9).
- WHAT THIS AUDITS: the committed margin law maps the measured composite ODMR FWHM (kappa_s = 1.4 MHz) onto ONE homogeneous Lorentzian packet — a threshold-MODEL assumption (`KAPPA_S` caveat; SPEC §6T/§7.T4). The hom/inhom decomposition of that composite is UNKNOWN (the open D4 conjunction, `docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md`). Every f_L row below is a SCENARIO PROBE across that unknown, exactly sized so the composite Voigt FWHM equals 1.400 MHz — none is a calibrated decomposition of the real line.
- MODEL ASSUMPTIONS (multi-packet threshold, `cavity.thermal.ensemble_threshold`): class-A / quasi-static clamped inversion; packet weights = the inversion- and coupling^2-weighted distribution of packet CENTRES — under the uniform-inversion/uniform-coupling assumption adopted here, the Gaussian centre distribution itself (std sigma_g). The composite Voigt line is the RESULTING susceptibility (Re S_spin = pi x the area-normalised composite profile), NOT itself the weight distribution. Common homogeneous width across packets; free-running oscillator ruling; STATIC kappa_s (no kappa_s(ΔT) feedback); single cavity mode.
- NORMALISATION CONVENTIONS — both computed, every number labelled: PRIMARY = the REPO-CONSISTENT IMPORT-PRESERVING FIXED-G^2 anchoring (ratified amendment C, `report_margin.py` C0-import convention): G^2 = C0·kappa_c·kappa_s_composite/4 with C0 = 190 imported, held fixed across line shapes and Q perturbations — this G^2 is an ALGEBRAIC IMPORT CONVENTION, not an independently measured or microscopically grounded coupling. SECONDARY = the on-resonance threshold ratio G^2_th(Δ)/G^2_th(0) = C0 — the handoff's convention; it anchors to the line PEAK rather than the composite FWHM, so it parts from the primary on every non-Lorentzian row (identical on the sigma_g = 0 branch).
- FAR-WING CAVEAT: at C0 = 190 the margin sits sqrt(C0−1) ≈ 13.75 combined half-widths from line centre. ALL rows — including the committed pure-Lorentzian row — carry the margin on far LORENTZIAN packet tails (Re S_spin → a_s/omega^2 there; verified V6). No measurement in hand constrains the real line 10+ widths out; the entire table inherits that assumption.
- ROOT-BRANCH RECORDING: thresholds are min-over-roots of Im S = 0 with Re S > 0; the scan guards tangential/merger roots and each table row records the selected root (omega_root, selected/total, '!' if any tangential candidate was involved) so branch switches are visible. Every row below sits on a single clean branch (1/1).
- HANDOFF PROVENANCE: the audited hypotheses come from the UNTRUSTED session record `docs/reviews/two_linewidth_falsification_handoff.md` (out-of-repo sandbox numerics, preserved unedited). Its operating-point margins used the SECONDARY normalisation and Olivero-Longbothum approximate sizing (composite ≈ 1.44 / 1.29 MHz, not 1.400); reproduction below is under ITS formulation, labelled. Its packet weighting (Gaussian centre distribution) matches this module's — no weighting difference to label.
- FINDINGS-NOTE IMPLICATION — RECOMMENDATION ONLY, no edit made: the unratified findings-note headline (higher-Q builds have MORE thermal margin, E ≈ +0.35) is CONDITIONAL on the Lorentzian-composite branch of the D4 unknown. On inhomogeneity-dominated decompositions the exponent sign inverts under BOTH normalisations (table below; sign contour f_L* ≈ 0.26 MHz). The note should carry this as an explicit conditionality before any headline use; deciding that edit is Oxborrow-routed, not this pass's.

## Parameters

- f = 1.45 GHz (`TARGET.f_design_hz`); Q0 = 6764.5852 (own-model canonical, re-based §5a record `refs/gate_runs/20260711T132705Z_rejudge/`) → Q_L = 5637.15; kappa_c = f/Q_L = 0.257222 MHz — CYCLIC-Hz FWHM, never angular (provenance-table trap 1).
- kappa_s composite = 1.400 MHz (`KAPPA_S`, 0.1% d14 branch choice; band [0.550, 1.750] MHz NOT swept here — this audit varies the decomposition at fixed composite).
- C0 = 190 (SPEC revision-note planning import, `PLANNING_C0`); primary anchoring G^2 = C0·kappa_c·kappa_s/4 = 17.105262 (matched-unit amplitude-rate^2, MHz^2).
- Committed single-packet reference: Δf_max = 11.3915 MHz, E = +0.3474 (`delta_f_max_hz`, `q_margin_exponent`).
- Units: matched cyclic-MHz-FWHM (amplitude rates = FWHM/2; exact by degree-1 homogeneity). Exponents: fixed-G^2 log-symmetric central difference, Q·e^{±h}, h = 0.02 (Lorentzian control reproduces the analytic exponent to ≤ 1e-4 relative — anchor V7).

## Exact-FWHM sweep — PRIMARY: repo-consistent import-preserving fixed-G^2

| f_L (MHz) | sigma_g (MHz) | Δf_max (MHz) | vs committed | omega_root (MHz) | root branch | E (h = 0.02) |
|---|---|---|---|---|---|---|
| 0.05 | 0.583130 | 10.4561 | -8.2% | 2.2721 | 1/1 | -0.1618 |
| 0.10 | 0.571554 | 9.2222 | -19.0% | 2.7874 | 1/1 | -0.1938 |
| 0.20 | 0.547814 | 8.4053 | -26.2% | 3.7728 | 1/1 | -0.0593 |
| 0.35 | 0.510543 | 8.4262 | -26.0% | 4.9034 | 1/1 | +0.0752 |
| 0.50 | 0.470878 | 8.7725 | -23.0% | 5.8189 | 1/1 | +0.1587 |
| 0.70 | 0.413117 | 9.3505 | -17.9% | 6.8514 | 1/1 | +0.2305 |
| 1.00 | 0.309777 | 10.2492 | -10.0% | 8.1570 | 1/1 | +0.2962 |
| 1.20 | 0.217789 | 10.8308 | -4.9% | 8.9209 | 1/1 | +0.3252 |
| 1.40 | 0.000000 | 11.3915 | +0.0% | 9.6234 | 1/1 | +0.3474 |

Sweep-grid minimum: Δf_max = 8.4053 MHz at f_L = 0.20 (-26.2% vs the committed row). The committed +0.35 exponent survives only on the f_L ≳ 0.26 MHz side of the contour below.

## Exact-FWHM sweep — SECONDARY: on-resonance threshold ratio (handoff convention)

| f_L (MHz) | sigma_g (MHz) | Δf_max (MHz) | vs committed | omega_root (MHz) | root branch | E (h = 0.02) |
|---|---|---|---|---|---|---|
| 0.05 | 0.583130 | 8.2738 | -27.4% | 2.1120 | 1/1 | -0.1211 |
| 0.10 | 0.571554 | 7.6698 | -32.7% | 2.4342 | 1/1 | -0.1606 |
| 0.20 | 0.547814 | 7.1458 | -37.3% | 3.2413 | 1/1 | -0.0578 |
| 0.35 | 0.510543 | 7.3132 | -35.8% | 4.2694 | 1/1 | +0.0748 |
| 0.50 | 0.470878 | 7.7717 | -31.8% | 5.1616 | 1/1 | +0.1583 |
| 0.70 | 0.413117 | 8.5160 | -25.2% | 6.2424 | 1/1 | +0.2303 |
| 1.00 | 0.309777 | 9.7288 | -14.6% | 7.7434 | 1/1 | +0.2963 |
| 1.20 | 0.217789 | 10.5607 | -7.3% | 8.6985 | 1/1 | +0.3253 |
| 1.40 | 0.000000 | 11.3915 | +0.0% | 9.6234 | 1/1 | +0.3474 |

Sweep-grid minimum: Δf_max = 7.1458 MHz at f_L = 0.20 (-37.3% vs the committed row).

## E = 0 sign contour (assessed per normalisation)

- import-preserving fixed-G^2: f_L* = 0.2566 MHz (bisected to ±0.0001 MHz).
- on-res ratio: f_L* = 0.2565 MHz (bisected to ±0.0001 MHz).

## Handoff-scenario reproduction (their formulation, this solver)

Their kc = 0.257 MHz (rounded), their sizing (sigma_g = 1.39/2.35482 and 1.00/2.35482 — composite ≈ 1.44/1.29 MHz), on-res-ratio normalisation, and their asymmetric eps = 0.05 exponent formula:

| scenario | this pass | handoff §6 |
|---|---|---|
| (a) Lorentzian 1.40 margin | 11.3900 MHz | 11.39 |
| (b) Voigt 0.10 + 1.39 margin | 7.7745 MHz | 7.77 |
| (c) Voigt 0.50 + 1.00 margin | 7.5053 MHz | 7.51 |
| (a) exponent, their eps-form | +0.3563 | +0.356 |
| (b) exponent, their eps-form | -0.1596 | −0.160 |

REPRODUCED, including the exponent SIGN FLIP (anchor V9). Formulation differences, labelled: (i) exact-FWHM sizing moves their scenario (b) from 7.7745 to 7.6698 MHz under the same (secondary) normalisation — their −32% margin headline carries ≈ 1 point of O-L sizing bias; (ii) under the PRIMARY import-preserving fixed-G^2 anchoring the same decomposition gives 9.2222 MHz (-19.0% vs committed) — the margin shrink is normalisation-dependent; (iii) their exponent formula divides by 2·ln(1+eps) over asymmetric (1±eps) points (their Lorentzian control read +0.356 vs the analytic +0.347); the sweep tables use the log-symmetric form instead. The SIGN conclusions are invariant to all three.

## Committed-law cross-check

The f_L = 1.40 row (sigma_g = 0) IS the committed single-packet law: both normalisations reproduce Δf_max = 11.3915 MHz (`delta_f_max_hz`) and E = +0.3474 (`q_margin_exponent`) — anchors V1/V7; the ensemble route adds no new physics on that branch, only the audit axis.
