# Deuteration identifiability / experiment design (WS3, 2026-07-20)

**Status: EXPERIMENT-DESIGN ANALYSIS — NOT evidence of deuteration.**
**No claim that deuteration is detected unless the model comparison genuinely discriminates it.**
Regenerate: `python -m calibration.deuteration_design`. NON-TRANSFERABLE rig analysis (SPEC §7.T5).

- measured ratio (T3, digitized grade): 1.343 ± 0.132 (σ_rel = 0.098)
- all bands computed on the ratified T2 grid (thickness 0.2-1.0 mm per-sample, spot 300-500 um, h_sub 1e2-1e5, k 0.1-1.0, mapping band) — Angus-pending unknowns SWEPT, never fixed
- **Current verdict: INSUFFICIENTLY IDENTIFIABLE at current metadata: the model ratio band brackets the measured ratio from both sides (T4 verdict geometry-sufficient, low discriminating power). No claim that deuteration is detected unless the model comparison genuinely discriminates it.**

## Statistical structure

Under the T4 cancellation conditions (shared η_abs — valid only under near-total absorption; shared df/dT — deuteration-transfer caveat riding), the slope RATIO carries essentially all the X-information: while the power plane and η_abs are unresolved, absolute slopes constrain only the product η_abs·Θ, and their one hard implication (η_abs ≤ 1) trims ~1–2% of the nuisance box (T5: 98–99% of the sweep admits η_abs ≤ 1). X is identifiable only to the model-ratio band ρ ∈ [ρ_lo, ρ_hi]:

    X_det = ρ_hi / (ρ_lo · (1 − 2σ_rel))     (enhancement)
    1/X  > ρ_hi · (1 + 2σ_rel) / ρ_lo        (suppression — NOT
                                              the reciprocal: the
                                              σ term flips sign)

is the smallest multiplier GUARANTEED to force the pre-registered intrinsic-effect-required verdict wherever the true nuisances sit. The complementary X_compat = [(r−2σ)/ρ_hi, (r+2σ)/ρ_lo] is the ENVELOPE-DERIVED COMPATIBILITY RANGE — not a confidence interval: sweep grids are bounds, not priors, and no probabilistic reading (Bayes factors over the sweep box, or T4's descriptive fraction_within_2sigma) survives grid reparameterisation.

Profile-likelihood framing (independent-derivation fold-in, 2026-07-20): the common scale A (power plane × shared absorption × shared |df/dT|) profiles out analytically, leaving ONE scale-free contrast from the two slopes against M0's ~7–8 effective unknowns; M1 adds one identifiable relative multiplier X.

## Scenario ladder — what each future measurement buys

| scenario | band factor ρ_hi/ρ_lo (best–worst over true values) | X_det @ digitized σ | X_det @ σ_rel=0.02 | X_compat @ digitized σ |
|---|---|---|---|---|
| baseline | 3.99 – 3.99 | 4.96 | 4.16 | [0.463, 2.751] |
| pin_thickness | 1.81 – 3.88 | 4.83 | 4.04 | [0.477, 2.751] |
| pin_spot | 2.90 – 3.99 | 4.96 | 4.16 | [0.463, 2.751] |
| narrow_h_sub_one_decade | 3.24 – 3.99 | 4.96 | 4.16 | [0.463, 2.751] |
| pin_k | 3.81 – 3.98 | 4.96 | 4.15 | [0.464, 2.751] |
| pin_mapping | 3.25 – 3.99 | 4.96 | 4.16 | [0.463, 2.751] |
| pin_thickness_and_spot | 1.62 – 3.88 | 4.83 | 4.04 | [0.477, 2.751] |
| all_metadata | 1.00 – 3.24 | 4.03 | 3.37 | [0.477, 2.297] |
| m0_unconstrained_mounting | 114.45 – 114.45 | 142.38 | 119.22 | [0.069, 11.674] |
| m0_mounting_within_1_decade | 21.63 – 21.63 | 26.90 | 22.53 | [0.135, 4.349] |
| m0_mounting_within_half_decade | 8.27 – 8.27 | 10.28 | 8.61 | [0.224, 2.758] |

**The binding limiter is MOUNTING, not metadata:** the T4 band above shares h_sub between samples by its committed convention; admitting the documented glue confound (per-sample mounting, M0-compatible) widens the honest identifiability envelope to ×114.5 — no plausible intrinsic factor is guaranteed-detectable while mounting is unconstrained. Mounting control (remount empirics / bond-line metrology) is therefore the gateway measurement, ahead of every metadata pin.

**Dominant single METADATA nuisance (largest best-case band collapse when measured): `pin_thickness`** — baseline factor 3.99 → best-case 1.81, worst-case 3.88 (worst case = least favourable true values; the guarantee criterion X_det uses the worst case).

## Matched-sample geometry

DEFINITION (disambiguated 2026-07-20): the numbers below are SAME-CRYSTAL mounting-pair ratios, computed on the d14 geometry — Θ(d14, mount 1)/Θ(d14, mount 2) at equal everything except h_sub. This is the matched-pair LIMIT: what glue asymmetry alone can manufacture when geometry is perfectly matched. (The CURRENT unequal pair with per-sample mounting is the m0_* scenario rows above — a different, wider object.)

- glue-only band, full h_sub prior (3 decades): ×15.67
- constrained to 1 decade (remount empirics / bond-line data): ×5.84
- constrained to 0.5 decade: ×2.62

Matched-pair design inequality (independent-derivation fold-in): a factor X is design-resolvable only if |log X| > ε_g + 2σ_ℓ, with ε_g the hard residual geometry/absorption-mismatch bound and σ_ℓ the statistical error on the log contrast — no number of power points rescues a failed geometry condition.

**Remount-same-crystal vs a second unmatched pair:** CONTROLLED remounting/cross-over of the same crystal(s) over standardised mount positions measures the h_sub spread directly — the only route that shrinks the glue confound φ empirically (an uncontrolled remount merely resamples it). A second unmatched d14/h14 pair adds one more ratio carrying its own unconstrained φ′ and does not shrink the confound. Controlled repetition under different mounting conditions is therefore MORE informative than an additional unmatched pair for the M0/M1 question. Time-resolved heating/cooling traces rank immediately behind it: the normalised transient removes the unknown amplitude and constrains h_i/diffusivity/settling orthogonally to the steady slope (introducing ρc_p; check 3c).

## Power grid (per sample)

Exact endpoint-grid WLS arithmetic across the current span (3.81–14.39 mW): S_xx = r·ΔP²·N(N+1)/(12(N−1)), σ_slope = σ_point/√S_xx, and σ_rel(R)² combines BOTH measured slopes (re-derived 2026-07-20; the earlier draft's span/√12 single-slope shortcut and N<3 rows are retired). Required N (one visit per level, N ≥ 3 enforced):

| σ_point (MHz) | target σ_rel | N required | note |
|---|---|---|---|
| 0.050 | 0.05 | 28 | digitized floor |
| 0.050 | 0.02 | 186 | digitized floor |
| 0.050 | 0.01 | 750 | digitized floor |
| 0.020 | 0.05 | 3 |  |
| 0.020 | 0.02 | 28 |  |
| 0.020 | 0.01 | 119 |  |
| 0.010 | 0.05 | 3 |  |
| 0.010 | 0.02 | 6 |  |
| 0.010 | 0.01 | 28 |  |
| 0.005 | 0.05 | 3 |  |
| 0.005 | 0.02 | 3 |  |
| 0.005 | 0.01 | 6 |  |

Repeat visits at the D6 minimum grid (N = 8 levels, digitized floor):

- r = 1 visit(s)/level → σ_rel(R) ≈ 0.085 (nominal 1/√r; correlated drift/hysteresis prevents the full gain)
- r = 2 visit(s)/level → σ_rel(R) ≈ 0.060 (nominal 1/√r; correlated drift/hysteresis prevents the full gain)
- r = 3 visit(s)/level → σ_rel(R) ≈ 0.049 (nominal 1/√r; correlated drift/hysteresis prevents the full gain)

ΔAICc ≥ 4 at N = 8 translates to required χ² improvements over linear of ≥ 9.6 (quadratic) and ≥ 18.93 (piecewise with a searched breakpoint, k = 4).

Acquisition protocol riders: D6 (user-ratified 2026-07-20) requires ≥ 8 independent power LEVELS (repeats at one level do not count) AND ΔAICc ≥ 4 before any nonlinear power model is claimable. Acquire THREE blocks — one ascending, one descending, one randomised/interleaved — with d14 and h14 interleaved and the settling duration chosen from a MEASURED time trace, so monotone drift separates from direction-dependent hysteresis (plan §6 steady-state check). Time-resolved traces additionally decide check 3c, orthogonal to this table.

## What this study does NOT do

- It does not detect, suggest, or exclude a deuteration effect (the T4 verdict — geometry-sufficient, low discriminating power, 'not required and not excluded' — stands verbatim).
- It does not fix any Angus-pending metadata value (all swept).
- It does not decompose M1's multiplier into k-isotope vs df/dT-deuteration (indistinguishable here by design, plan §6).
- Its numbers do not transfer to the maser geometry.
