# Deuteration identifiability / experiment design (WS3, 2026-07-20)

**Status: EXPERIMENT-DESIGN ANALYSIS — NOT evidence of deuteration.**
**No claim that deuteration is detected unless the model comparison genuinely discriminates it.**
Regenerate: `python -m calibration.deuteration_design`. NON-TRANSFERABLE rig analysis (SPEC §7.T5).

- measured ratio (T3, digitized grade): 1.343 ± 0.132 (σ_rel = 0.098)
- all bands computed on the ratified T2 grid (thickness 0.2-1.0 mm per-sample, spot 300-500 um, h_sub 1e2-1e5, k 0.1-1.0, mapping band) — Angus-pending unknowns SWEPT, never fixed
- **Current verdict: INSUFFICIENTLY IDENTIFIABLE at current metadata: the model ratio band brackets the measured ratio from both sides (T4 verdict geometry-sufficient, low discriminating power). No claim that deuteration is detected unless the model comparison genuinely discriminates it.**

## Statistical structure

Under the T4 cancellation conditions (shared η_abs — valid only under near-total absorption; shared df/dT — deuteration-transfer caveat riding), the slope RATIO carries essentially all the X-information: while the power plane and η_abs are unresolved, absolute slopes constrain only the product η_abs·Θ, and their one hard implication (η_abs ≤ 1) trims ~1–2% of the nuisance box (T5: 98–99% of the sweep admits η_abs ≤ 1). X is identifiable only to the model-ratio band ρ ∈ [ρ_lo, ρ_hi]:

    X_det = ρ_hi / (ρ_lo · (1 − 2σ_rel))

is the smallest multiplier GUARANTEED to force the pre-registered intrinsic-effect-required verdict wherever the true nuisances sit.

## Scenario ladder — what each future measurement buys

| scenario | band factor ρ_hi/ρ_lo (best–worst over true values) | X_det @ digitized σ | X_det @ σ_rel=0.02 |
|---|---|---|---|
| baseline | 3.99 – 3.99 | 4.96 | 4.16 |
| pin_thickness | 1.81 – 3.88 | 4.83 | 4.04 |
| pin_spot | 2.90 – 3.99 | 4.96 | 4.16 |
| narrow_h_sub_one_decade | 3.24 – 3.99 | 4.96 | 4.16 |
| pin_k | 3.81 – 3.98 | 4.96 | 4.15 |
| pin_mapping | 3.25 – 3.99 | 4.96 | 4.16 |
| pin_thickness_and_spot | 1.62 – 3.88 | 4.83 | 4.04 |
| all_metadata | 1.00 – 3.24 | 4.03 | 3.37 |
| m0_unconstrained_mounting | 114.45 – 114.45 | 142.38 | 119.22 |
| m0_mounting_within_1_decade | 21.63 – 21.63 | 26.90 | 22.53 |
| m0_mounting_within_half_decade | 8.27 – 8.27 | 10.28 | 8.61 |

**The binding limiter is MOUNTING, not metadata:** the T4 band above shares h_sub between samples by its committed convention; admitting the documented glue confound (per-sample mounting, M0-compatible) widens the honest identifiability envelope to ×114.5 — no plausible intrinsic factor is guaranteed-detectable while mounting is unconstrained. Mounting control (remount empirics / bond-line metrology) is therefore the gateway measurement, ahead of every metadata pin.

**Dominant single METADATA nuisance (largest best-case band collapse when measured): `pin_thickness`** — baseline factor 3.99 → best-case 1.81, worst-case 3.88 (worst case = least favourable true values; the guarantee criterion X_det uses the worst case).

## Matched-sample geometry

At FULLY matched geometry (equal thickness, equal lateral size, same mapping, same spot) the residual band is per-sample glue asymmetry alone:

- glue-only band, full h_sub prior (3 decades): ×15.67
- constrained to 1 decade (remount empirics / bond-line data): ×5.84
- constrained to 0.5 decade: ×2.62

**Remount-same-crystal vs a second unmatched pair:** remounting the SAME crystal n times measures the h_sub spread directly — it is the only route that shrinks the glue confound φ empirically. A second unmatched d14/h14 pair adds one more ratio carrying its own unconstrained φ′ and does not shrink the confound. Repetition under different mounting conditions is therefore MORE informative than an additional unmatched pair for the M0/M1 question.

## Power grid (per sample)

WLS arithmetic on a uniform grid across the current span (3.81–14.39 mW): required N per (per-point σ, target σ_rel on the ratio):

| σ_point (MHz) | target σ_rel | N required | note |
|---|---|---|---|
| 0.050 | 0.05 | 22 | digitized floor |
| 0.050 | 0.02 | 135 | digitized floor |
| 0.050 | 0.01 | 537 | digitized floor |
| 0.020 | 0.05 | 4 |  |
| 0.020 | 0.02 | 22 |  |
| 0.020 | 0.01 | 86 |  |
| 0.010 | 0.05 | 1 |  |
| 0.010 | 0.02 | 6 |  |
| 0.010 | 0.01 | 22 |  |
| 0.005 | 0.05 | 1 |  |
| 0.005 | 0.02 | 2 |  |
| 0.005 | 0.01 | 6 |  |

Riders: D6 (user-ratified 2026-07-20) requires ≥ 8 independent power points AND ΔAICc ≥ 4 before any nonlinear power model is claimable; acquire interleaved ascending/descending with ≥ 2 repeats at an anchor power so drift/hysteresis (settling, plan §6) is testable. Time-resolved traces decide check 3c, orthogonal to this table.

## What this study does NOT do

- It does not detect, suggest, or exclude a deuteration effect (the T4 verdict — geometry-sufficient, low discriminating power, 'not required and not excluded' — stands verbatim).
- It does not fix any Angus-pending metadata value (all swept).
- It does not decompose M1's multiplier into k-isotope vs df/dT-deuteration (indistinguishable here by design, plan §6).
- Its numbers do not transfer to the maser geometry.
