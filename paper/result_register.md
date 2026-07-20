# Result register — every quantitative result currently citable

**Status: PLANNING ARTIFACT (paper spine, 2026-07-20).** One row per number
the manuscript could cite today, at its grade. Values are QUOTED from the
committed pinned artifacts named in each row — this register never computes;
if a value here disagrees with its artifact, the artifact wins and this file
is stale (guard: `tests/test_paper_spine.py` cross-checks a sample of rows
against the live artifacts). Claim IDs per `paper/claim_evidence_matrix.md`.

Grade key: L = literature print; D = derived; F = fitted; P = planning/
scoping; U = supervisor-unratified rider. "digitized" = graph-digitized-
provisional, superseded_by_raw_data=True.

## Validation anchors (C3, C3b, C17)

| Result | Value | Grade | Artifact (source of record) |
|---|---|---|---|
| Booth-point f (faithful branch) | 1450.382 MHz (4 s.f. vs 1.45 GHz) | D | `refs/gate_runs/20260711T132705Z_rejudge/booth_5a_checkpoint.md` |
| Booth-point Q₀ (faithful branch) | 6981.32 vs 6,980 (+0.02%) | D | same |
| Canonical-branch Q₀ | 6764.59 (branch delta −3.10%) | D | same + `checkpoint_manifest.json` |
| V_mode own vs Booth-implied | 0.6558 vs 0.6544 cm³ (+0.21%) | D | same |
| Booth revolution factor | 225/360 = 0.625 | D/U (Booth confirmation pending) | `provenance.BOOTH_TABLE8_REVOLUTION_FACTOR` |
| Wall fraction / Q_diel | 0.266 / 9511.5 | D | rejudge record |
| §8 PEC+lossy residual | 5.64e-5 (~1.1% of tolerance) | D | `provenance.ExtractionTolerances` docstring + gate run 20260706 |
| Gate tallies | 5 pass / 0 fail / 1 deferred; phase1_complete = false | D | rejudge `gate_report.json` |

## Modelled-build constants (C14, C15)

| Result | Value | Grade | Source |
|---|---|---|---|
| Wu ring I.D. / O.D. | 4.05 / 12.0 mm | L | `GEOM_WU_STO_RING`; archived PDFs |
| Ring height | FORKED {8.5, 8.6} mm — no float exists | L (two-sided) | `STO_HEIGHT_FORK` (Q13) |
| Wu coupling / Q₀ | k = 1 stated ⇒ Q₀ = 7200 | L | `TARGETS.wu_ring` |
| tanδ ceiling | 1.4e-4 (= 2 s.f. of 1/7200) | D | `TOL.tan_delta_max` |
| Wu V_mode (SM print) | ≈0.32 cm³ — RECORDED, gate-held (W2) | L/P | `TARGETS.wu_ring.v_mode_m3` |
| Pump beam ellipse | ~2 × 1.2 mm; A_p ~1.9 mm² | L (tilde precision) | `WU_PUMP_BEAM` |
| Crystal εr (Q11) | 3.0, band [2.4, 4.1] | P | `RESOLUTION_Q11` |
| Crystal planning dims | 3 × 8 mm (cross-build flag riding) | P | `provenance.CRYSTAL` |

## Thermal coefficients (C11, C12, C13)

| Result | Value | Grade | Source |
|---|---|---|---|
| df_cavity/dT | +2.73 MHz/K @300 K; band [+2.3, +2.9] over 293–323 K | D (model-only arm) | `DF_CAVITY_DT`; `tests/test_provenance_df_cavity_dt.py` |
| df_spin/dT | −109 kHz/K; band [−120, −64] kHz/K | F (raw grade; axis branch = band) | `DF_SPIN_DT`; `refs/singh_2025_raw/fit_report.md` |
| κs | 1.4 MHz; band [0.55, 1.75] MHz (cyclic-Hz FWHM) | P (branch choice; best-per-host caveat) | `KAPPA_S` |
| κc (planning composition) | 257.222 kHz = f/Q_L, Q_L = 6764.59/1.2 | D/P (k = 0.2 import) | `thermal/reports/q_margin_turnover.md` |
| k (p-terphenyl) | band 0.1–1.0 W/m/K (0.1 = liquid-value floor) | P | `K_PTP` |
| c_p (300 K) | ≈1225 J/kg/K (Chang 1983; 0.94·T J/K/mol) | L | SPEC §6T (ρ still unsourced — open pull) |
| Emissivity | 0.80–0.95 (nominal 0.90), class-generic | P (band ratified as-is) | `EMISSIVITY_PTP` |
| h free convection | 5–20 W/m²/K ceiling; h → 0 floor | P (regime framing ratified) | `H_CONV_AIR` |

## Margin planning points (C1, C2) — ALL planning-grade, UNRATIFIED

| Result | Value | Grade | Source |
|---|---|---|---|
| Δf_max (two-linewidth) | 11.3915 MHz | P/U | `thermal/reports/q_margin_planning_point.md` / turnover map |
| ΔT_max | 3.90 K (coefficient envelope ≈1.8–5.8 K) | P/U | same |
| Q-margin exponent at operating point | E ≈ +0.3474; κc/κs ≈ 0.184 | D/U | `thermal/reports/q_margin_turnover.md` |
| Turnover crossings (fixed-G) | Q_− = 63.19, Q_+ = 972.5 (κs band → Q_+ ∈ [746, 2613]) | D/U (convention objects) | same |
| C₀ | 190 — IMPORTED planning value; ungraded literal (`report_margin.PLANNING_C0`) | P | claim-trace 2026-07-20; flagged in C1/C2 chains |
| Superseded κs→0 values | Δf_max 1.77 MHz / ΔT_max 0.60 K (historical) | D (history) | SPEC §7.T4 dated blocks |

## Calibration (C4, C8, C18) — digitized grade throughout

| Result | Value | Grade | Source |
|---|---|---|---|
| T3 slopes | d14 −0.1000 ± 0.0062; h14 −0.0745 ± 0.0057 MHz/mW | F digitized | `calibration/reports/slope_fit_digitized.md` |
| Ratio | 1.343 ± 0.132 | F digitized | same |
| T4 verdict | GEOMETRY-SUFFICIENT; model band [0.584, 2.329]; 53.9% inside ±2σ; "not required and not excluded" | F digitized | `calibration/reports/ratio_test_digitized.md` + feed |
| Glue confound φ | 1.49 → 0.008 across h_ref 1e2→1e5 | F digitized | same |
| η_abs·R_int | 917 [781, 1659] (d14); 683 [573, 1252] K/W (h14) | F digitized | `calibration/reports/absolute_fit_digitized.md` + feed |
| Probe-inferred heating @14.39 mW | 13.2 K (d14) / 9.8 K (h14); bands [12.0, 22.5] / [8.9, 16.7] | F digitized (η_abs-free) | `observable_a_feed.json` |
| η_abs at nominal config | 0.168 / 0.160 (plane-dependent interpretation) | F digitized | same |
| h14 step test | z = −1.93 (does NOT exceed floor at 2σ); h14 χ²/dof = 3.67 | F digitized | same |
| Identifiability plate | k·w product; w-prior ×2.3–3.2 (→ ×23.6 buried) | D/P | `thermal/reports/identifiability_3a_computed.md`, `_volumetric_computed.md` |
| Identifiability film | ∂lnΔT/∂ln k ∈ [−0.11, −0.004] — no lever | D/P | same |

## S-ladder (C6) — ballpark tier, per absorbed watt at k_mid unless stated

| Result | Value | Source |
|---|---|---|
| S0 conductance | G = 2.79e-4 W/K (k_mid) ⇒ 35.8 K @10 mW hot-face | `thermal/reports/s_ladder_ballpark.md` |
| S0 anchor residual | 8.88e-16 K per K drive (machine precision) | same |
| S1 field ratios | centre 0.0026; vol avg 0.0607; band avg 0.0017 per K of top drive | same |
| S1b flux conjugate | peak 359 K/W; vol avg 16 K/W | same |
| S4 lower bracket (m=0) | peak@eq 816–842 K/W (l_abs grid); band avg 745.6 | same |
| S4 upper bracket | disc 1184 K/W (half-space anchor 1299); Gaussian buried 1088–1497 | same |

Not citable (no artifact yet): any broadening/line-shape prediction (C7);
any W2/Wu-anchor agreement number (C5); any population/distribution quantity
(C1/C9/C10).
