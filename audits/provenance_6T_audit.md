# SPEC §6T Thermal-Block Provenance Audit

**Verdict: 19 constants audited, 0 fully clean, 6 flagged.**
(fully clean = locator VERIFIED + Stage-2 CONFIRMED + error bar in print + no unresolved
transfer caveat. The remaining 13 are honestly self-declared UNSOURCED/ASSUMED nuisance,
scoping, or bracket parameters — not integrity flags, but not literature-verified either.)

Stage 0 enumeration → Stage 1 trace (per-field, primary PDFs) → Stage 2 refute
(fresh clean-context agent, repo-blind, per Stage-1-VERIFIED claim only). Style rule
applied: **a slope read off a figure is FITTED, never MEASURED, however the source phrases it.**

---

## 1. Constant table

| # | Constant | Value | Class | Locator verified? | Stage-2 verdict | Error bar | Transfer caveats (condensed) |
|---|---|---|---|---|---|---|---|
| 1 | `SpinFreqTempCoefficient.df_dt_hz_per_k` | −101e3 Hz/K | **FITTED** | VERIFIED (Singh 2025 main text p.3; SI Table S1 XZ row; Fig. 2B(iii)) | **REFUTED** | **NONE IN PRINT** | Cold-finger not sample T (≈+55 K laser offset, unquantified in paper); protonated Pc:PTP not Pc-d14:PTP-d14; bulk crystal not 0.5 mm plate / 100 nm film; sign never printed |
| 2 | `SpinFreqTempCoefficient.df_dt_band_lo_hz_per_k` | −101e3 Hz/K | **FITTED** | VERIFIED (same Singh region-III slope as #1) | **REFUTED** | **NONE IN PRINT** | Same as #1; band-edge role; ensemble corroboration (W20, Lang) disputed — see FLAGS |
| 3 | `SpinFreqTempCoefficient.df_dt_band_hi_hz_per_k` | −50e3 Hz/K | ASSUMED | **SOURCE_MISSING** (Oxborrow in-thread quote; locator NONE) | REFUTED group / **AMBIGUOUS** (unverifiable) | N/A | No document exists; nature of number (measured/fit/recollection) unknown; deuteration unverified |
| 4 | `PTerphenylThermalConductivity.k_floor_w_m_k` | 0.1 W/m/K | DERIVED | **NOT_AT_CLAIMED_LOCATOR** (data on p.125 Table X / Eq.20, not cited "p.122") | skipped (locator not VERIFIED) | **NONE IN PRINT** | Hedley value is LIQUID p-terphenyl 0.134–0.136 at 213–254 °C (486–527 K); 0.1 is a ~25% round-down floor, not printed; ~150–200 °C phase/T extrapolation |
| 5 | `PTerphenylThermalConductivity.k_band_lo_w_m_k` | 0.1 W/m/K | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Self-declared engineering floor; "Breeze-2018 lineage" untraceable (library Breeze paper is NV-diamond) |
| 6 | `PTerphenylThermalConductivity.k_band_hi_w_m_k` | 1.0 W/m/K | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | ×10 bracket top; no solid-crystal PTP k in library at all; anisotropy folded in |
| 7 | `PTerphenylThermalConductivity.k_mid_w_m_k` | 0.31622776601683794 | DERIVED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | √(0.1·1.0) arithmetic centre; verified exact; explicitly "NOT a physical claim" (R denominator) |
| 8 | `PTerphenylThermalConductivity.anisotropy_factor` | 2.0 | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Generic monoclinic-crystal expectation; no PTP-specific k-anisotropy source in library; not applied as tensor |
| 9 | `ParaffinWaxThermal.k_w_m_k` | 0.24 W/m/K | ASSUMED | **SOURCE_MISSING** (Incropera & DeWitt Table A.3 not in library) | skipped | N/A | Generic-handbook, not measured for rig; wax grade unknown; mounting unconfirmed (Mena 2024 only; Mann 2025 SI silent) |
| 10 | `ParaffinWaxThermal.k_range_lo_w_m_k` | 0.2 W/m/K | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Handbook band low edge; source absent |
| 11 | `ParaffinWaxThermal.k_range_hi_w_m_k` | 0.3 W/m/K | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Handbook band high edge; source absent |
| 12 | `ParaffinWaxThermal.t_wax_box_lo_m` | 1e-6 m | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Nuisance sweep param; no bond-line thickness in any library PDF; interface resistance absorbed into sweep |
| 13 | `ParaffinWaxThermal.t_wax_box_hi_m` | 100e-6 m | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Nuisance sweep param; hand-applied assumption |
| 14 | `GlassSlideThermal.k_w_m_k` | 1.14 W/m/K | ASSUMED | **SOURCE_MISSING** (Incropera & DeWitt not in library) | skipped | N/A | Generic-handbook; material unconfirmed (borosilicate vs soda-lime 0.9–1.1); docstring's own Pyrex quote is 1.4 ≠ coded 1.14 (~19% gap) |
| 15 | `GlassSlideThermal.k_range_lo_w_m_k` | 0.9 W/m/K | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Soda-lime low edge; material identity unresolved |
| 16 | `GlassSlideThermal.k_range_hi_w_m_k` | 1.4 W/m/K | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Borosilicate high edge; spans two glass families |
| 17 | `GlassSlideThermal.t_glass_m` | 1.0e-3 m | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED) | skipped | N/A | Standard-slide assumption; Mann 2025 SI says "glass substrates" but gives no thickness |
| 18 | `GlassSlideThermal.t_glass_sensitivity_frac` | 0.5 | ASSUMED | NO_LOCATOR_CLAIMED (SPEC §7.T5) | skipped | N/A | Internal ±50% sensitivity knob, not a physical constant; glass shown non-verdict-setting |
| 19 | `PumpAbsorptionLength.l_abs_scoping_grid_m` | (5,10,20,50,100,200)e-6 m | ASSUMED | NO_LOCATOR_CLAIMED (UNSOURCED-SCOPING) | skipped | N/A | Fabricated log-spaced bracket for check-3a only; caveats forbid use in absolute ΔT; Takeda 2002 / Breeze thesis not yet read |

---

## 2. FLAGS

Each flag cites a locator. Six constants carry an integrity flag; several carry more than one category.

### A. FITTED value that the registry/source presents as if MEASURED
- **#1 `df_dt_hz_per_k` = −101e3 Hz/K.** Singh 2025 main text p.3 states it as an *observed* "variation of … 101 kHz/K for Txz in region III (red line in Fig. 2B(iii))," and SI Table S1 prints a bare "101" — phrasing that reads as a measurement. It is the slope of a fit line drawn through ODMR-peak data, i.e. **FITTED**. Locator verified, but see C/D.
- **#2 `df_dt_band_lo_hz_per_k` = −101e3 Hz/K.** Same Singh region-III fitted slope re-used as the band lower edge; same FITTED-presented-as-observed status.

### B. SOURCE_MISSING
- **#3 `df_dt_band_hi_hz_per_k` = −50e3 Hz/K.** Claimed source is an Oxborrow in-thread/private quote, locator NONE; no document, note, or attachment exists in the library (author search "Oxborrow" → only published articles, none a −50 kHz/K RT source). Unverifiable in principle.
- **#9 `ParaffinWaxThermal.k_w_m_k` = 0.24 W/m/K.** Claimed Incropera & DeWitt Table A.3 (300 K) not in Zotero (queries "Incropera","DeWitt","Fundamentals of Heat and Mass Transfer","wax" → 0 hits). Cell cannot be inspected.
- **#14 `GlassSlideThermal.k_w_m_k` = 1.14 W/m/K.** Same absent handbook. Extra internal inconsistency: docstring says "Table A.3 prints 1.4 for Pyrex" yet codes 1.14 (~19% lower) — 1.14 matches no single stated cell.

### C. REFUTED or AMBIGUOUS Stage-2 verdict
- **#1 `df_dt_hz_per_k`: REFUTED.** Stage 2 (repo-blind, fresh) independently vector-extracted Fig. 2B(iii), calibrated on tick-mark segments, and found the drawn red line = **−112 kHz/K over T≈254–323 K**; −101 reproduces only an **unstated** ~230–330 K sub-window; the full source-defined region III (Tm>150 K) gives ≈ **−70 kHz/K**. Also: sign never printed anywhere (even NV-diamond dD/dT printed unsigned despite known negative Acosta 2010 value). Value matches neither the drawn line nor the nominal region-III window.
- **#2 `df_dt_band_lo_hz_per_k`: REFUTED** (verdict stands on the Singh grounds of #1, which is the same −101 value; one refute sub-claim corrected below). Two genuine ensemble findings: **(i) Lang 2007 prints no "−70 kHz/K average over 230–296 K" anywhere in prose** — its only printed slope is 300 kHz/K over ≈183–193 K; the −70 figure attributed to "Lang 2007 Fig. 4" is a figure-derived estimate with no in-print locator (Stage 1's rough pixel read of that branch gives ≈ −50 to −65 kHz/K, so even the read is questionable). **(ii) Wu 2020 (PRApplied 14, 064017, p.8) prints "−80 kHz/K" verbatim, citing "Fig. 4 of Ref. [38]" = Lang 2007** — this **confirms** the registry's "W20 prints −80 kHz/K off the same figure" attribution (verified independently by Stage 1 and Stage 2). *Orchestrator correction:* the Stage-2 refuter, repo-blind by design, mis-read the condensed locator as claiming W20 corroborates −101 and reported that sub-point as a refutation; the registry makes no such claim, so that sub-point is struck. The REFUTED verdict itself is unaffected (grounds: −101 matches neither the drawn −112 line nor the −70 full-region fit, and the Lang −70/230–296 K attribution is unprinted).
- **#3 `df_dt_band_hi_hz_per_k`: AMBIGUOUS** (group REFUTED). No document to open; unverifiable, not confirmable.

### D. NONE-IN-PRINT error bar on a load-bearing constant
- **#1 / #2 `df_dt_*` (−101e3 Hz/K).** No ± anywhere in Singh main text, Table 1, or SI Table S1 for any df/dT entry. This is the load-bearing spin-frequency temperature coefficient; its dominant uncertainty (fit-window systematic, ≈ −68 → −112 kHz/K) is unrepresented by any printed error bar.
- **#4 `k_floor_w_m_k` (0.1 W/m/K).** Hedley 1970 prints no uncertainty on the liquid-p-terphenyl kL points that anchor the floor; the 0.1 round-down itself has no stated rule. Load-bearing as the working-band floor / anisotropy bracket.

---

## 3. CANARY

**Withheld ground truth** (`refs/singh_fig2biii_reanalysis.md`, 2026-07-04; readable by this
synthesizer, **not** by Stage 2): Singh's −101 kHz/K region-III Txz slope has a documented
fit-window inconsistency — the drawn red line in Fig. 2B(iii) is **−112 kHz/K over cold-finger
254–324 K** (OLS −111.9 ± 1.1), the printed −101 matches **no stated window** (would need an
unstated ~235 K start), the full SI region III (150–330 K) gives −68.4 ± 1.7, and **no error
bar exists in print**; the T-axis is cold-finger (≈+55 K laser offset), so the fit samples
actual sample T ≈ 310–380 K.

**Did any Stage-2 agent INDEPENDENTLY flag a slope/window/uncertainty issue on this constant?**
**YES.** Both repo-blind Stage-2 refute agents (`singh_fig2biii_primary` and
`df_spin_band_ensemble`), with no access to this repo or the reanalysis file, independently
extracted the Fig. 2B(iii) vector artwork, calibrated on the tick-mark segments (x: 260.33/302.94/345.56 pt → 100/200/300 K; y: 242.46/266.07/289.67 pt → 1454/1450/1446 MHz), and reported: drawn red line ≈ **−112 kHz/K over T≈254–323 K**; −101 matches only an **unstated** ~230–330 K window; full region III ≈ **−70 kHz/K**; **sign and error bar absent in print**. These reproduce the withheld ground truth to within a few percent.

### CANARY: CAUGHT

The adversarial layer works: the deliberately-withheld fit-window / drawn-line / missing-uncertainty defect was re-derived from primary sources by the clean-context refute stage without seeing the repo's own reanalysis.

---

## 4. Scope notes

- **Adjacent classes excluded from scope** (per Stage 0 enumeration `excluded_adjacent`): `RigSampleGeometry`.
- **Stage agents that failed or returned null:** none. No `AGENT_FAILED` verdicts. All 14
  claim-group refutes are either present (2: both REFUTED) or legitimately `{skipped:true}`
  (12: no Stage-1-VERIFIED field to refute, because the locator resolved to
  NOT_AT_CLAIMED_LOCATOR, NO_LOCATOR_CLAIMED, or SOURCE_MISSING).
- **Load-bearing hotspot:** the only literature-anchored, verdict-relevant physical numbers in
  §6T are the two df_spin −101e3 Hz/K fields — both REFUTED, both NONE-IN-PRINT. Every other
  §6T constant is a self-declared UNSOURCED/ASSUMED bracket, nuisance-sweep, or scoping value
  (correctly graded as such) rather than a verified measurement.
- **Not "clean" ≠ "wrong":** the 13 unflagged constants raise no provenance-integrity flag but
  fail the fully-clean bar (no in-print error bar and/or no verified literature locator); they
  are honest engineering assumptions, appropriate for the sensitivity/identifiability role
  SPEC §7.T5 assigns them.
