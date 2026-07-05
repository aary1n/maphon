# Check 3a appendix — volumetric (Beer-Lambert) source: does burial move the k–w degeneracy?

**Date:** 2026-07-05 · **Scope:** PLATE only (the FILM verdict never depended on k_PTP). Appendix to `identifiability_3a.md` — that report and its pins are untouched.
**Question protected:** the PLATE verdict rests on the exact spreading-regime degeneracy ΔT ∝ 1/(k·w) (log-slopes −1.00/−1.00), and the "w known to ×2.3–×3.2 de-confounds" requirement — the number the Angus-email "a rough rig ID suffices" argument leans on — is computed FROM that scaling. The solver deposited heat as a surface flux; the real pump is absorbed along the beam. If l_abs ≳ w the near-spot source is a buried cylinder, not a surface disk.
**Engine:** `layered.delta_t_gaussian_volumetric` (Gaussian × truncated-renormalised exponential depth profile in the PTP layer; derivation + quadrature choice in the `layered.py` docstring). Anchored BEFORE use (§8 discipline, `tests/test_thermal_volumetric.py`): l_abs → 0 reproduces the validated surface-flux engine to ≤1e-4 at the named points; l_abs ≫ t recovers the two-region uniform-generation slab closed form incl. its discriminating t₁/(2k₁) half-thickness term; base outflow = P to 1e-6 for all l_abs.
**Reproduce:** `python -m cavity.thermal.report_3a_volumetric --out thermal/reports` (deterministic). Computed tables: `identifiability_3a_volumetric_computed.md`; grids: `identifiability_3a_volumetric_grids.npz`.
**l_abs status:** the grid {5, 10, 20, 50, 100, 200} µm is UNSOURCED-SCOPING (§6T `PumpAbsorptionLength`) — brackets plausible 520–590 nm penetration in 0.01–0.1 % Pc:PTP; no provenance-grade value exists for the dataset samples and none is claimed.

## 1. Table (D.1) — PLATE named points, σ = 10 % ×-factor

| point | l_abs | ∂lnΔT/∂ln k | ∂lnΔT/∂ln w | R | w-prior ×-factor (σ=10%) |
|---|---|---|---|---|---|
| focused_thin_wax (w = 3.16 µm) | surface | −1.000 | −1.001 | 2.845 | ×2.87 |
| | 5 µm | −0.999 | −0.502 | 2.843 | ×5.39 |
| | 10 µm | −0.999 | −0.415 | 2.842 | ×7.40 |
| | 20 µm | −0.998 | −0.345 | 2.840 | ×10.15 |
| | 50 µm | −0.996 | −0.276 | 2.833 | ×15.47 |
| | 100 µm | −0.993 | −0.238 | 2.824 | ×21.21 |
| | 200 µm | −0.987 | −0.212 | 2.809 | ×23.57 |
| doublet_mid_wax (w = 100 µm) | surface | −0.986 | −1.041 | 2.804 | ×2.87 |
| | 5 µm | −0.985 | −0.972 | 2.801 | ×2.87 |
| | 10 µm | −0.984 | −0.920 | 2.798 | ×2.87 |
| | 20 µm | −0.982 | −0.844 | 2.792 | ×2.87 |
| | 50 µm | −0.976 | −0.717 | 2.776 | ×3.19 |
| | 100 µm | −0.967 | −0.618 | 2.750 | ×3.93 |
| | 200 µm | −0.954 | −0.535 | 2.709 | ×3.93 |

(Same stencil as the headline sweep — multiplicative central differences ×1.2/÷1.2; ×-factors by the identical `w_prior_factor_to_deconfound` machinery, l_abs held known, t_wax free; σ = 5/20 % columns and box-confounding fractions in the computed tables.)

## 2. Verdict (D.2)

**SCALING SOFTENS — in the argument's favour.** The w-slope leaves [−1.1, −0.9] at the focused point for *every* scoping l_abs (−0.50 already at 5 µm, −0.21 at 200 µm) and at the doublet point for l_abs ≥ 20 µm. But the two quantities the email argument actually uses move the safe way:

- **The k lever is intact:** ∂lnΔT/∂ln k stays in [−1.00, −0.95] and R ∈ [2.39, 2.84] over the whole (w, t_wax) box at every l_abs — identifiable-by-signal at 100 % of the box, unchanged from the surface sweep.
- **The de-confound requirement only loosens.** Worst case (harmful sense = tightest requirement) over the entire scoping grid at σ = 10 % is **×2.87 — identical to the surface-flux value**, occurring exactly where burial is negligible (doublet point, l_abs ≤ 20 µm ≪ w). Everywhere burial actually bites, the factor grows, up to ×23.6 (focused, 200 µm): a flattened w-slope means w must travel *further* to mimic a band-edge k. Across σ = 5/10/20 % the floor is ×2.87/×2.87/×2.32 — the surface-flux **×2.3–×3.2 stands as the conservative floor**, and "rough rig ID suffices" survives (≥ ×2 everywhere plausible, with margin).

## 3. What burial does expose (D.3): l_abs becomes its own nuisance

The ×-factor machinery holds l_abs known. Unknown, it is a k-compensator the surface model could not see: ∂lnΔT/∂ln l_abs reaches −0.75 (focused, 100 µm), and the scoping grid spans ×40 — enough to mimic a band-edge k if l_abs floats freely. First-order slope arithmetic (computed table, not a grid search): with the email's existing ×2.3 w-prior, de-confounding at σ = 10 % additionally needs **l_abs known to ×3.0 (worst case over both points and the grid)**.

That knowledge is cheap and does **not** need a new top Angus ask: l_abs ≈ 1/(ε ln10 · c) from the per-sample nominal doping (already inside asks 1/6) plus pump wavelength (already ask 3/4), with ε(520/532 nm) from the Takeda-2002 / Breeze-thesis-era literature — a §6T pull on us, flagged in `PumpAbsorptionLength`. The dominant residual is the never-assayed actual doping (the O12 "actual concentration may have been somewhat lower" caveat); a ×3 bracket survives that unless true doping is off nominal by >3×. **Priority: rider on existing asks, below asks 1–3.**

## 4. Limitations (stated, not hidden)

- **Observable unchanged:** beam-centre *surface* rise, as in the headline sweep. The ODMR probe really averages over the emitting (absorbed) volume; a probe-weighted readout is a bounded variant of the same buried-source physics and is deliberately not introduced here — it belongs to the absolute-calibration model, not the identifiability scoping.
- **Truncation renormalisation:** the transmitted fraction e^(−t₁/l_abs) (8 % at l_abs = 200 µm under a 0.5 mm plate) is rescaled onto the layer so absorbed power stays P — a modelling choice, stated in the engine docstring.
- **Grid economy:** ×-factor sweeps ran at n_t_wax = 7 (t_wax is invisible under a plate, ≤ +0.01 log-slope across the grid); validated at the worst case against the full 41×25 grid (×23.57 = ×23.57, ×3.93 = ×3.93) and the surface baseline on the thinned grid reproduces the headline ×2.87.
- The mild k-slope drift to −0.95 at l_abs = 200 µm is the source approaching the wax/glass — second-order, absorbed in the numbers above.

## 5. Files + tests (E)

- Engine: `src/cavity/thermal/layered.py` (volumetric extension + 1-D anchors); sweep: `src/cavity/thermal/volumetric_3a.py`; runner: `report_3a_volumetric.py`.
- Anchors + 2 volumetric regression pins (R and w-slope at focused/5 µm and doublet/200 µm): `tests/test_thermal_volumetric.py`.
- Suite: **254 passed / 14 skipped / 1 xfailed** (was 241/14/1; +13, all new). Surface-flux pins, sweep results and `identifiability_3a.md` untouched.
