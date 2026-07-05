# Check 3a — can the Cowley-Semple slope calibrate k_PTP? Identifiability sweep, decision report

**Date:** 2026-07-04 · **Scope:** SPEC §7.T5 check 3a, the §7T calibration branch (pure Python, COMSOL-free, not gated on §5).
**Engine:** `src/cavity/thermal/layered.py` (Hankel-transform layered medium), anchored by `tests/test_thermal_layered.py`; sweep in `src/cavity/thermal/identifiability.py`.
**Reproduce:** `python -m cavity.thermal.report_3a --out thermal/reports` (deterministic — no RNG). Computed tables: `identifiability_3a_computed.md`; raw grids: `identifiability_3a_grids.npz`.

---

## 1. Verdict (D.1)

**PLATE (0.5 mm polished plate — the published form of the 0.01% crystals): CONDITIONAL.**
3a is identifiable **if and only if the spot radius is pinned**; the condition is mild.

- Signal is never the problem: R = [ΔT(k=0.1) − ΔT(k=1.0)] / ΔT(k_mid) sits in **[2.58, 2.85] over the entire (w, t_wax) box** — the k band swings the observable by ~2.8× the mid-band signal, i.e. R > 2σ_rel at **100 %** of the box even at σ_rel = 20 %.
- The problem is an *exact* k–w degeneracy: in the spreading-dominated regime ΔT ∝ 1/(k·w), and the sweep measures ∂lnΔT/∂ln k = −1.00, ∂lnΔT/∂ln w = −1.00 everywhere. With w free inside the two-optic box (1–500 µm), **100 % of the box is CONFOUNDED at every σ_rel** — a wrong k anywhere in the band is perfectly compensated by a plausible w.
- Pinning w at its true value de-confounds **the entire box (0 % confounded, every σ_rel)**. Pinning t_wax instead rescues **nothing** (100 % confounded — t_wax is invisible under a plate, ∂lnΔT/∂ln t_wax ≤ 0.003).
- How well must w be known? Multiplicative half-width **×2.3 (σ=20 %) to ×3.2 (σ=5 %)** around the true value (grid-search estimate, ~11 % factor resolution). The theoretical limit is √(k_hi/k_lo) = √10 ≈ 3.16: to distinguish the band edges from the midpoint, the w-prior must be tighter than the k-compensation each edge needs. **Any measured spot, or even a solid rig identification with beam-geometry arithmetic good to ×2, meets this.**

**FILM (100 nm OMBD film on glass — the only published form of the 0.1 % material): UNIDENTIFIABLE.**
A film measurement calibrates the wax + glass stack, not k_PTP.

- R exceeds 2σ_rel only in a focused-spot corner: **w ≤ 12 µm (σ=5 %), ≤ 5.5 µm (σ=10 %), ≤ 2.2 µm (σ=20 %)** — reachable only by the diffraction-limited aspheric, not the doublet. At the doublet-class named point R = 0.012: two orders of magnitude below PLATE.
- Confounding kills even that corner: with both nuisances free, **100 %** of the box is confounded at every σ_rel; **even with w pinned exactly, 93–99 % remains confounded**, because the film's small k lever (∂lnΔT/∂ln k between −0.11 and −0.004) is overwhelmed by t_wax (+0.20 to +0.41). No optic choice rescues the film.

| form | σ_rel | R-verdict over box | confounded, both free | confounded, w pinned | confounded, t_wax pinned |
|---|---|---|---|---|---|
| PLATE | 5 % | IDENT 100 % | 100 % | **0 %** | 100 % |
| PLATE | 10 % | IDENT 100 % | 100 % | **0 %** | 100 % |
| PLATE | 20 % | IDENT 100 % | 100 % | **0 %** | 100 % |
| FILM | 5 % | IDENT 38 % / PART 12 % / UNID 50 % | 100 % | 93 % | 100 % |
| FILM | 10 % | IDENT 26 % / PART 13 % / UNID 62 % | 100 % | 95 % | 100 % |
| FILM | 20 % | IDENT 13 % / PART 13 % / UNID 74 % | 100 % | 99 % | 100 % |

**Regime map (C.4):** w/t_PTP = 1 falls exactly on the PLATE box's right edge (t_plate = 500 µm = w_max), so the **entire PLATE box is on the w ≤ t spreading side** — 3a there genuinely probes the material, exactly as SPEC §7.T5 anticipated. The FILM box is w ≫ t everywhere (w ≥ 10× t even at w = 1 µm): the anticipated inversion, now quantified.

---

## 2. The Angus-email consequence (D.2) — asks ranked by information value

Numbers referenced: named-point sensitivity table in `identifiability_3a_computed.md`.

1. **Per-sample form + thickness (§11 ask 1) — confirmed top, now with teeth.** It flips 3a between CONDITIONAL and UNIDENTIFIABLE; no other metadata matters until it is answered. If the 0.1 % dataset sample is the published-style 100 nm film, 3a cannot constrain k_PTP under any measurement of the other nuisances.
2. **Which rig + spot size (§11 ask 3) — promoted to the decisive ask for the plate case.** w to within ×3 multiplicative is the entire difference between "k_PTP constrained to the band" and "rig calibration only." A rig identification (Mena diode + f=30 mm doublet vs Mann Finesse + f=11 mm aspheric) plus beam arithmetic probably already meets ×3; a measured spot to ×2 settles it. This ask is cheap for Angus and worth the most per word.
3. **Laser power at sample (§11 ask 4) — unchanged in rank, sharpened in role.** R is power-independent by construction (P normalises out), so 3a's *identifiability* doesn't need it. But the absolute-k inference multiplies in the power calibration and the df_spin/dT band (−50…−101 kHz/K, a ×2 spread; §6T) — with w pinned these two remain the floor on k precision (~×2–3). With power calibrated, 3a upgrades from band-test to the effective-k measurement §6T flags as the stretch framing.
4. **Mounting / wax bond line (§11 ask 2) — demoted for plates.** Under a 0.5 mm plate the wax is invisible (∂lnΔT/∂ln t_wax ≤ 0.003, t_glass ±50 % → ≤1 %). It matters only if the sample is a film — where it is co-dominant and 3a is dead anyway. Keep in the list; don't lead with it.
5. **Slide material/thickness — no ask needed.** ±50 % t_glass moves ΔT by ≤1 %; borosilicate-vs-soda-lime spread is smaller than that.

Time-resolved traces (ask 5) and raw ν(I) (ask 6) are untouched by this sweep — they gate 3c and error bars, not 3a's regime.

---

## 3. FILM vs PLATE and what it does to 3b (D.3)

The inversion is qualitative, as expected: PLATE is PTP-spreading-dominated (k and w each enter with log-slope −1, wax/glass negligible), FILM is substrate-stack-dominated (k nearly absent, w log-slope −1.2 to −1.4, t_wax +0.2 to +0.4).

Consequence for **3b (concentration-ratio check)**: 3b's power-cancellation argument implicitly assumes both samples share the thermal transfer function Θ = ΔT/P_abs. If both are 0.5 mm plates, Θ cancels in the ratio and 3b stays the clean, nearly-metadata-free q̇ ∝ [Pc] test — SPEC's "first to implement" status stands. If the 0.1 % sample is a film while the 0.01 % is a plate, **Θ_plate/Θ_film spans 0.78–3.36 over the nuisance box** — the rig no longer cancels, and 3b becomes model-dependent through the full stack, inheriting the same w and t_wax unknowns as 3a *plus* the per-sample thickness in the absorbed-fraction (∝ concentration × thickness). Ask 1 therefore protects both 3a and 3b at once — worth saying explicitly in the email.

---

## 4. Anchors (A.2) — all pass before the sweep ran

`tests/test_thermal_layered.py`, 14 tests. Closed forms and citations:

| anchor | closed form | source | status |
|---|---|---|---|
| (a) semi-infinite, uniform-disk flux, centre | ΔT = P/(πka) | Carslaw & Jaeger, *Conduction of Heat in Solids* 2nd ed., §8.2 | pass (rel 1e-6) |
| (a) semi-infinite, uniform-disk flux, disk-average | ΔT̄ = 8P/(3π²ka) | C&J §8.2 / Yovanovich spreading-resistance reviews | pass (rel 1e-5) |
| (a) relation to the isothermal-disk form P/(4ka) | ΔT̄ = (32/3π²)·P/(4ka) ≈ 1.081× | C&J §8.2 | asserted exactly — the brief named the isothermal-disk closed form; the solver is flux-specified (correct-physics choice, see §6) |
| (a) semi-infinite, Gaussian flux, centre | ΔT = P/(√(2π)·k·w) | derived in `layered.py` docstring (Hankel); same family as Lax, JAP 48, 3919 (1977) | pass (rel 1e-8) |
| (a) semi-infinite, Gaussian flux, radial profile | ΔT(r) = ΔT₀·e^(−r²/w²)·I₀(r²/w²) | derived ibid. | pass at r/w ∈ {0.5, 1, 2, 4} (rel 1e-7) |
| (b) 1-D / thin-layer limit | ΔT → (2P/πw²)·Σtᵢ/kᵢ | series-resistance slab | pass, monotone convergence from below, <1e-3 at w = 100·Σt |
| (c) layer collapse | merge equal-k layers; 5-way split | transfer-matrix identity | pass (rel 1e-10) |
| Robin top | ΔT monotone ↓ in h; h = 20 W/m²K worst case | — | pass; effect ≤ 0.8 % at named points (see §5) |
| conventions | q̂(0) = P/2π both fluxes; Z(ξ→0) = Σt/k; Z(ξ→∞) = 1/(k₁ξ) | — | pass |

Order-of-magnitude sanity vs the thread (validation check 2, illustrative only): ΔT/P ≈ 1.1×10⁴ K/W at the doublet-class point (k_mid) means the thread's inferred 10–20 K rise at 50–100 mA needs ~1–2 mW absorbed — comfortable for a 10–100 mW-class diode with percent-level absorption in a 0.5 mm 0.1 % crystal. The model and Oxborrow's "several tens of Celsius" inference coexist without strain.

---

## 5. Choices record (B) — every knob, stated

- **Grid:** w ∈ [1, 500] µm, 41 points log-spaced (two-optic record, §6T `RigSampleGeometry`: ~0.7 µm diffraction limit of the C061TMD-A f=11 mm NA 0.24 aspheric at 532 nm → 1 µm floor; AC254-030-AB f=30 mm doublet unfocused/misaligned worst case → 500 µm with margin; extends the ~100 µm figure in SPEC §7.T5's first pass — deliberate over-coverage). t_wax ∈ [1, 100] µm, 25 points log-spaced (unsourced bracket — assumption, flagged in §6T). k_PTP ∈ {0.1, √0.1 ≈ 0.316, 1.0} W/m/K — band edges + **geometric midpoint** (the band is a ×10 multiplicative bracket; log-midpoint is the natural reference for R's denominator).
- **Forms, run separately:** PLATE t = 0.5 mm; FILM t = 100 nm (§6T). Fixed t_glass = 1.0 mm (standard slide; ±50 % sensitivity: ≤1 % on ΔT — reported, not swept). k_wax = 0.24, k_glass = 1.14 W/m/K (§6T, generic-handbook grade).
- **Observable:** ΔT(r=0, z=0)/P — beam-centre surface rise per absorbed watt. P normalised out (enters linearly; R is power-independent). Probe volume = illuminated spot (co-located excitation/collection, SPEC §7.T5 observable (a)).
- **BCs:** isothermal base at bath; top insulated (h = 0) by default, with the Robin variant switchable — h = 20 W/m²K (free convection + linearised radiation scale) lowers ΔT by ≤0.8 % at the named points (worst: wide spot on low-k plate). Insulated-top is thus quantified as safe, not assumed by a Biot hand-wave.
- **Thresholds (C.2):** IDENTIFIABLE R > 2σ_rel, PARTIAL R > σ_rel, else UNIDENTIFIABLE; σ_rel ∈ {5, 10, 20} % (Angus's error bars unknown — bracketed).
- **Confounding (C.3):** grid-search profile-likelihood proxy: a point is CONFOUNDED at σ_rel if either band-edge k reproduces the k_mid observable within σ_rel with nuisances free in their box. Sign-change bracketing between adjacent grid nodes counts as an exact match (continuity), so grid resolution cannot fake identifiability. Three nuisance scenarios: both free / w pinned / t_wax pinned. No MCMC, no surrogate — scoping calc per the brief.

---

## 6. Assumptions and flags NOT in `provenance/constants.py`

- **Surface-flux deposition.** Pump heat enters as a surface flux at z = 0; the real source is volumetric along the beam. Nil for the film; for a 0.5 mm optically-thin plate it biases absolute ΔT high at the surface. Second-order for R (a ratio), load-bearing for absolute ΔT prediction — the absorption profile belongs to the §6T illumination model when 3a moves from identifiability to actual calibration.
- **Isotropic k_PTP.** SPEC §6T's ~2× anisotropy is folded into the band, not modelled.
- **No wax contact resistance.** Any interface resistance is partially degenerate with t_wax/k_wax and is absorbed into the t_wax box.
- **Robin h values {0, 10, 20} W/m²K** — generic free-convection + radiation magnitudes, not measured for the rig; ambient assumed at bath temperature.
- **P/(4ka) wording guard:** the brief named the **isothermal-disk** (constant-temperature) closed form ΔT = P/(4ka); the solver is **flux-specified**, whose exact closed forms are P/(πka) (centre) and 8P/(3π²ka) (disk average) — a different boundary condition, not a different answer to the same one. The tests assert the exact isoflux forms and pin the known (32/3π²) ≈ 1.081 ratio between the two BCs — a correct-physics choice, not a shortcut: "verify against P/(4ka)" is honoured in the only sense that is physically exact.
- **De-confound factors are grid-search approximate** (~11 % factor resolution) and evaluated with t_wax left free.
- **Multiplicative confounders outside the sweep:** absolute power calibration and the df_spin/dT band (×2 spread, §6T) multiply the measured slope exactly as 1/k does in the spreading regime. R is immune by construction; absolute k is not — they set the precision floor stated in §2 item 3.

## 7. Files (D.4)

- `r_map_plate.png`, `r_map_film.png` — R maps, 2σ contours, named points, regime annotation.
- `verdict_map_plate.png`, `verdict_map_film.png` — three-σ verdict panels, CONFOUNDED hatched (both-nuisances-free scenario).
- `identifiability_3a_computed.md` — machine-generated tables (regenerated on each run).
- `identifiability_3a_grids.npz` — raw ΔT/R/mismatch grids.
- Regression pins: `tests/test_thermal_identifiability.py` (4 named-point R values; verdicts cannot silently shift).
