# Layer B calibration plan — Cowley-Semple 2026-07-14 CW-ODMR dataset (observable-a)

**Status: RATIFIED WITH CONDITIONS 2026-07-14; EXECUTED same day.**
Ratification conditions (all applied):

1. **Finding 1 → ruling (a):** diff `thermal.md` vs `thermal.eml`; re-mint the one
   manifest line iff divergence is render/re-save-level; stop on content-level
   divergence. *Outcome: zero body-token divergence (render-level only) → re-minted
   with in-manifest errata; record `calibration/reports/integrity_finding1_2026-07-14.md`.*
2. **Finding 2 → go**, with an LFS pre-check: verify `.gitattributes` already has LFS
   before routing; commit as plain objects otherwise. *Outcome: LFS confirmed in use
   (mph/pdf/npz); PNGs + eml routed through it — LFS oids = the manifest's own pins.*
3. **df_spin/dT: prompt band OVERRULED.** Use graded `provenance.DF_SPIN_DT`
   (point −108.5, band [−120, −64] kHz/K); flag "−50 to −108" as a stale quote.
4. **Scoping-value correction:** the drafted hand-pass h14 slope/ratio were wrong.
   Independent WLS (ratifier's): d14 −0.100 ± 0.006, h14 −0.0745 ± 0.006 MHz/mW,
   ratio **1.34 ± 0.13** — T3 regression pins must match an independent calculation;
   T4 framed around 1.34 ± 0.13. *(Both conditions are met in
   `tests/test_calibration_slope_fit.py`: the module's closed form is cross-checked
   in-test against `numpy.polyfit(cov="unscaled")`.)*

Minor conditions: plan assumption 3 upgraded to **figure-stated** (h14 spectra title
"0.1% Pc:PTP"); assumption 4 cross-references the pending power-measurement-plane
question to Angus (recorded in `ExcitationSource.power_plane` and the feed JSON);
radiation branch ratified **as flagged branch** (not headline).

**Context.** Calibrate the Layer B thermal submodel (SPEC §7.T5 observable-(a))
against the Cowley-Semple d14/h14 CW-ODMR dataset received 2026-07-14 (email from
Angus Cowley-Semple, archived with 10 attachments at
`calibration/data/raw/cowley_semple_2026-07-14/` with `MANIFEST.sha256`).
The calibration rig (PCB stripline; crystal–rubber-cement–glass–HASL/Cu–FR-4 stack;
enclosed ambient) is NOT the maser cavity: its thermal parameters do not transfer.
Everything lives in the `calibration/` namespace; dependency direction is strictly
one-way (`calibration` may import `cavity`; nothing in `src/cavity/` may import
`calibration` — enforced in CI). Calibration constants live in
`calibration/constants.py`, graded like `provenance/constants.py`, every entry
NON-TRANSFERABLE. Physics modules under `src/cavity/` are read-only.
`calibration/data/raw/` is read-only forever. No Layer A work; no
broadening/linewidth analysis.

---

## 0. Pre-existing integrity findings (recon 2026-07-14; resolved under conditions 1–2)

**Finding 1 — `thermal.md` failed its manifest hash (content-level).** All 10 images
and `thermal.eml` PASSED; `thermal.md` failed under every line-ending variant
(pinned `98cd3c36…`, as-archived `ff856929…`). The manifest itself is CRLF, so naive
`sha256sum -c` fails on all 12 names — the verifier parses universal-newline.
Token-level md-vs-eml comparison: **zero email-body tokens missing from the md**;
only-in-md tokens are the header block + a residual CSS fragment → render-level
drift → re-mint per ruling (a).

**Finding 2 — the raw archive was not in version control.** The generic `data/`
gitignore rule silently excluded `calibration/data/**`; commit `7f44606`'s "archive"
message predates actual tracking (it contained only the CSV at the old
`calibration/derived/` path). Fixed: `!calibration/data/` + `!calibration/data/**`
negations (git does not descend into excluded directories — the directory itself
must be re-included), LFS routes + blanket `-text` in `.gitattributes`, CSV move
staged as a rename, corrective note in the commit message.

## T0 — Integrity gate (`calibration/integrity.py`)

`verify_manifest` both directions (entries exist + hash-match; no unpinned extras);
`require_intact` writes a dated failure report to `calibration/reports/` and raises
`CalibrationIntegrityError` — every data-consuming module calls it first. CLI
`python -m calibration.integrity` (exit 0/1). Read-only-forever enforcement = CI:
`tests/test_calibration_integrity.py::TestRealArchive` re-verifies the working tree
every run. Manifest dialect: CRLF, `#` comments (the errata block), GNU two-space
format; malformed lines are errors, never skips.

## T2 — Sample configs + rig model

`calibration/constants.py`: every email value graded (collaborator-confirmed /
collaborator-suggested / figure-stated / planning-assumption), all NON-TRANSFERABLE.
Notable grades: spot 400 µm = **suggested, not measured** (swept 300–500 µm);
h14 concentration = figure-stated; power plane = open Angus ask; enclosure confirmed
→ h = 5 W/m²/K (bottom of `H_CONV_AIR`); radiation = flagged branch via
`h_rad_linearized` (≈ +5 W/m²/K, comparable to h_conv — §7.T7 forbids assuming small).

`calibration/samples/`: `D14`/`H14` `SampleConfig` + the ratified `SweepGrid`
(thickness 0.2–1.0 mm per-sample independent, spot 300–500 µm, h_sub 1e2–1e5
decades lumping the rubber-cement/glass/PCB stack, k = `K_PTP` band 0.1–1.0,
radius mapping inscribed 0.50 / equal-area 0.564 / circumscribed 0.707 × lateral).

**Engine: analytic — `cavity.thermal.cylinder.solve`. No COMSOL.** The solver
natively provides finite cylinder, per-surface Robin, top-hat `'disc'` +
`'surface'` deposition, Beer-Lambert variant, energy diagnostics. Measured cost:
6.4 ms/solve; the full two-sample T2 sweep ≈ 2 s. Observable: **spot-averaged
top-surface ΔT per absorbed watt** (Θ_probe, K/W; probe = excitation disc,
co-located per §7.T5(a)). COMSOL contingency trigger (fixed in advance): T4
indeterminate AND verdict flips across the radius-mapping band edges. *Outcome:
not fired.*

Anchors (§8 discipline, `tests/test_calibration_rig_model.py`): h_sub→∞ recovers
the Dirichlet base; wide-crystal limit matches the independent layered/Hankel
solver (centre 5e-4, probe average 1e-4 — convergence measured against mode count
first); energy balance; quadrature convergence; monotonicity in h_sub/k/t;
d14-hotter-than-h14 mechanism; radiation-branch direction.

## T3 — Slope fits (`calibration/slope_fit.py`)

Input EXCLUSIVELY `calibration/data/derived/odmr_shift_vs_power_digitized.csv`;
loader refuses to run without the grade + error-model header; every output stamped
`graph-digitized-provisional; superseded_by_raw_data=True`. WLS with the uniform
±0.05 MHz floor; parameter errors floor-propagated (χ²/dof reported as lack-of-fit,
not absorbed). **Results** (`calibration/reports/slope_fit_digitized.md`):
d14 −0.1000 ± 0.0062, h14 −0.0745 ± 0.0057 MHz/mW, ratio **1.343 ± 0.132** —
matching condition 4's independent WLS. h14 step 10.16→12.33 mW: observed −0.30 vs
predicted −0.162 MHz, z = −1.93 → **does NOT exceed the floor at 2σ** (h14 global
χ²/dof = 3.67 elevated; quantization caveat carried; step/fit correlation neglected
— stated as approximate, χ² is the primary statistic).

## T4 — Ratio discrimination (`calibration/ratio_test.py`)

Θ_d14/Θ_h14 over the shared-parameter sweep (η_abs and df/dT cancel by
construction — condition stated: near-total absorption, l_abs ≪ t; interface
parameters shared, thicknesses per-sample free) vs measured 1.343 ± 0.132.
Three-way rule fixed at ratification: inside-2σ → geometry-sufficient; all one
side → intrinsic-effect-required; straddle-without-inside → indeterminate.
**VERDICT: GEOMETRY-SUFFICIENT** — model band [0.584, 2.329], 53.9% of 8775 points
inside ±2σ, stable across the radius-mapping band; COMSOL trigger not fired.
Glue confound quantified (matched geometry): φ = h_sub(d14)/h_sub(h14) reproducing
the measured ratio spans 1.49 → 0.008 across h_ref 1e2→1e5 — an alternative the
test cannot exclude. Intrinsic branch deliberately not decomposed (k-isotope vs
df/dT-deuteration indistinguishable here). Report:
`calibration/reports/ratio_test_digitized.md`.

## T5 — Absolute fits (`calibration/absolute_fit.py`)

Chain |slope| = |df_spin/dT|·η_abs·Θ with df_spin/dT per condition 3 (graded
`DF_SPIN_DT`; stale prompt band flagged inside the feed itself). **Results**
(`calibration/reports/absolute_fit_digitized.md` + `observable_a_feed.json`):
η_abs·R_int = 917 [781, 1659] K/W (d14), 683 [573, 1252] K/W (h14) — coefficient
band dominates (×1.875). Probe-inferred heating at 14.39 mW = 13.2 K (d14) /
9.8 K (h14), **η_abs-free** (the triplet-thermometer reading) — Oxborrow's
"several tens of Celsius" class reproduced at order of magnitude, not tuned to.
98–99% of the sweep admits η_abs ≤ 1. Deuteration asymmetry carried per sample:
**h14 is the clean fit** (protonated = Singh's crystal); d14 caveated.

---

## Files created / modified (as executed)

**Created:** `calibration/{__init__,integrity,constants,rig_model,slope_fit,ratio_test,absolute_fit}.py`,
`calibration/samples/__init__.py`, `calibration/reports/` (integrity record, three
T3–T5 reports, `observable_a_feed.json`), this document, and 7 test files
`tests/test_calibration_{integrity,import_boundary,samples,rig_model,slope_fit,ratio_test,absolute_fit}.py`.

**Modified:** `pyproject.toml` (pytest `pythonpath = ["src", "."]`), `.gitignore`
(calibration/data negations), `.gitattributes` (LFS + `-text`), `SPEC.md`
(§11 item 5 dated status block), `MANIFEST.sha256` (single re-mint line + errata,
under condition 1). Physics modules under `src/cavity/`: untouched.

## Interfaces to existing thermal machinery (import-only, one-way; CI-enforced whitelist)

`cavity.thermal.cylinder` (`CylinderSpec`, `SurfaceBC`, `PumpSource`, `solve`) —
engine · `cavity.thermal.layered` (`Layer`, cross-check anchors) ·
`cavity.thermal.radiation` (`h_rad_linearized`) · `cavity.provenance.constants`
(`K_PTP`, `DF_SPIN_DT`, `EMISSIVITY_PTP`, …). The whitelist lives in
`tests/test_calibration_import_boundary.py`; extend it here first.

## Test counts

Before: `558 tests collected` (verbatim: "558 tests collected in 6.84s").
After: **646 collected** — 88 new: integrity 14 (incl. boundary guard 2), samples 14,
rig_model 13, slope_fit 16, ratio_test 17, absolute_fit 14.

## Assumptions (final register)

1. Crystal→cylinder equal-area radius mapping, band [0.50, 0.71]×lateral (swept).
2. Caliper lateral = face width, not diagonal (photos consistent).
3. h14 nominal 0.1% — **figure-stated** (upgraded per minor condition).
4. Legend powers = at-sample — measurement plane = open Angus ask (cross-referenced
   in constants + feed; only η_abs's interpretation moves).
5. Surface deposition headline; Beer-Lambert available as sensitivity.
6. Radiation as ratified flagged branch.
7. Traces read as settled steady state (CW implied, unverified).
8. Underside stack lumped to one effective Robin (Cu-spreader argument), decades swept.
9. Shared k between samples in T4's geometry branch (isotope effect → intrinsic verdict).

## Standing hooks

- **Raw ν(P) traces land → re-fit T3–T5** (every derived number is stamped
  superseded_by_raw_data=True; the CSV, constants literal `DIGITIZED_SIGMA_MHZ`,
  and reports retire together).
- Per-sample thickness from Angus → collapse the thickness axis of the sweep.
- Power-measurement plane from Angus → fix η_abs's interpretation.
- T4's geometry-sufficient verdict is provisional at the digitized grade; the
  glue-contact confound is the argument to carry into any collaboration summary.
