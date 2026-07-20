# Plan — Cowley-Semple reply ingestion and the calibration re-base

**Intended repo path:** `docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md`
**Status: DRAFT FOR APPROVAL — nothing in the repository is edited by this plan. Planned against live `main` @ `0b2668f9410630ed29b61a08219e5b98c858f49c` (2026-07-19). This plan specifies what happens WHEN Angus Cowley-Semple's reply lands on: raw ODMR spectra or fitted centres/linewidths; the optical-power measurement plane and calibration; crystal/glass/rubber-cement thicknesses; acquisition/settling protocol; sample placement and CPW geometry.**

**Rulings ratified 2026-07-20 (user):** D4 — the κs re-grade gate is a strict conjunction (raw-fit candidates recorded + Oxborrow's explicit linewidth-class ruling + fit-quality/extrapolation gates passed). D5 — informal ranges are read as UNIFORM bands. D6 — nonlinear power models are claimable only under a strict AND gate: ≥ 8 independent power points per sample AND ΔAICc ≥ 4 over linear WLS. D7 — feed supersession is archive-copy-then-regenerate-in-place on the stable canonical path, with `dataset_version` + provenance fields in both files and an explicit supersedes pointer in the new canonical feed.

Machinery of record (verified at HEAD): `calibration/` (integrity, constants, samples, rig_model, slope_fit, ratio_test, absolute_fit; reports incl. `observable_a_feed.json`); the immutable archive `calibration/data/raw/cowley_semple_2026-07-14/` (MANIFEST-pinned, CI-verified); the graded digitized CSV `calibration/data/derived/odmr_shift_vs_power_digitized.csv` whose loader refuses to fit without the `graph-digitized-provisional; superseded_by_raw_data=True` header; the Layer B plan's standing hooks ("raw traces land → re-fit T3–T5; the CSV, `DIGITIZED_SIGMA_MHZ`, and reports retire together"); and — on the cavity side, via provenance only — `KAPPA_S` (the Cowley-Semple linewidth table as the graded two-linewidth κs) and `DF_SPIN_DT`.

---

## 1. Durable ingestion path

### 1.1 Raw archive (byte-preserving, immutable from commit)
New directory `calibration/data/raw/cowley_semple_<date>/`, the 2026-07-14 shape exactly:
- the `.eml` export + rendered `.md` + every attachment **byte-identical as sent** (spectra files, tables, XLSX, Origin exports, photos, sketches — whatever arrives, unconverted);
- `MANIFEST.sha256` (CRLF/GNU-two-space dialect, `#` provenance comment block: sender, date, message-id, attachment inventory, any known caveats);
- LFS routing via the existing blanket rules; `-text` protection;
- +1 `TestRealArchive` test in `tests/test_calibration_integrity.py`;
- read-only forever; any later correction is a dated in-manifest errata line (Finding-1 ruling (a) precedent), never a byte edit.

### 1.2 Formats — preferred and realistic alternatives
Preferred (stated in the ask, not demanded): per-trace CSV/TSV `frequency, signal` (or `frequency, contrast`) with one file per (sample, optical power, MW power) and a small metadata table (CSV) keyed by trace filename. Accepted without complaint, with the conversion rule per format:

| Arrives as | Raw archive | Derived form |
|---|---|---|
| CSV/TSV/TXT numeric | as-is | consumed directly (a copied, header-graded derived version if column semantics need normalising) |
| XLSX | as-is | `calibration/tools/xlsx_to_csv.py` (new, committed, deterministic — pinned sheet/column mapping recorded in the derived header); derived CSVs land under `data/derived/` with SHA-256s recorded in the derived files' headers |
| Origin `.opj` / exports | as-is | if numeric export accompanies it, that is the derived source; if only the `.opj`, ask Angus for a CSV export FIRST (one line); committed digitisation of rendered figures is the last resort, stamped `graph-digitized-provisional` exactly as today |
| Image exports (PNG/PDF plots) | as-is | committed digitisation script + graded CSV, `graph-digitized-provisional; superseded_by_raw_data=True` — i.e. the same grade as today; images DO NOT retire the digitized grade |
| Emailed inline table | the `.eml`/`.md` IS the raw | transcription to derived CSV with a transcription-check note (every value re-read against the archive by a second pass; check recorded in the header) |
| Photos / geometry sketches | as-is (images/) | measurements read off them are FIGURE-STATED grade constants, each citing the file |

### 1.3 Dataset versioning and supersession rules
- **The existing digitized dataset is immutable and is SUPERSEDED, not overwritten.** `odmr_shift_vs_power_digitized.csv` and the three T3–T5 reports keep their bytes as the dated record of the digitized grade. **Feed supersession — RATIFIED as D7 (2026-07-20), archive-copy-then-regenerate-in-place:** before replacing the canonical feed, copy the existing digitized-grade artifact to `observable_a_feed_digitized_2026-07-14.json` (same directory), then regenerate `observable_a_feed.json` from the selected raw dataset **in the same changeset**. Downstream consumers continue to use the stable canonical path. BOTH files carry explicit `dataset_version` and `provenance` fields, and the new canonical feed carries a `supersedes` field naming the artifact/dataset it supersedes. Existing digitized data and archived reports remain immutable throughout.
- **Supersession vs. new-dataset rule (fixed in advance):** raw traces of the SAME acquisitions that produced the digitized points SUPERSEDE the digitized CSV (its `superseded_by_raw_data=True` stamp fires; the CSV stays in-tree as record, `DIGITIZED_SIGMA_MHZ` retires from headline duty with a dated docstring note). A NEW acquisition (re-measured series, new samples, new powers) is a NEW dataset version — both live, neither supersedes, and cross-dataset comparison is an analysis output, not a merge.
- Every derived artifact carries `dataset_version` (e.g. `cowley_semple_2026-07-14-digitized`, `cowley_semple_<date>-raw`) in its header/JSON; loaders take the version EXPLICITLY (no "latest" magic); the refit modules select the raw version by name in code, with the digitized loader kept callable for the record.

---

## 2. Metadata schema

New graded dataclasses appended to `calibration/constants.py` (single-source discipline; existing entries get dated annotations where superseded in meaning, never edited-in-place; grades: COLLABORATOR-CONFIRMED / COLLABORATOR-SUGGESTED / FIGURE-STATED / PLANNING-ASSUMPTION, plus MEASURED-BY-COLLABORATOR where he states an actual measurement). Every entry NON-TRANSFERABLE, as now. Informal ranges in his answers ("roughly X", "somewhere between A and B") are read as **UNIFORM bands** (D5, user-ratified 2026-07-20 — the single convention at every site, with his wording quoted). Fields — one slot per ask, each nullable-with-grade so partial replies ingest cleanly:

- **Sample identity:** sample id/label per trace; growth batch if stated.
- **Isotope:** d14 / h14 per sample (d14 currently collaborator-confirmed, h14 figure-stated — upgrade h14 only if the email TEXT states it).
- **Nominal concentration** per sample + grade (zone-refining caveat rides regardless).
- **Crystal lateral dimensions:** existing `SampleLateralSize` (1.12 / 1.79 mm) stands; new values only as dated supersessions with his method stated.
- **Crystal thickness (per-sample)** — the top residual gap: value + method + uncertainty; collapses the 0.2–1.0 mm sweep axis to measured ± stated uncertainty (or ± a stated reading of "roughly", quoted).
- **Glass (substrate) thickness**; **rubber-cement bond-line thickness** (value or his "thin smear"-class description, graded accordingly);
- **Optical wavelength** (520 nm confirmed — slot exists for completeness);
- **Power values per trace** and **power measurement plane** — enum {AT_SAMPLE, DIODE_OUTPUT, AFTER_FIBRE, OTHER(str)} + any calibration he describes (power-meter model, where placed, when calibrated);
- **Settling time / acquisition order:** wait time between setting laser power and sweeping; sweep direction and dwell per point; trace order (ascending/descending power, interleaved?); repeats; MW power per trace and whether it was held fixed;
- **CPW geometry:** trace width, gap, ground layout, via positions/pitch, board stack (already partially known: lead-free-HASL/Cu/FR-4), short/50 Ω termination;
- **Sample position and orientation:** where on the CPW the crystal sits (over trace/gap), distance to the nearest vias, long-axis orientation, which face is glued down; photos referenced by archive path.

---

## 3. Parser / refit pipeline

New modules (all under `calibration/`, one-way import boundary respected; whitelist in `tests/test_calibration_import_boundary.py` extended FIRST if any new `cavity.*` import is needed):

**`calibration/raw_ingest.py`** — loads the versioned raw/derived traces; refuses ungraded headers (the `load_digitized` pattern); returns typed trace objects (sample, optical power + plane, MW power, freq array, signal array, acquisition metadata).

**`calibration/lineshape.py`** — per-spectrum fits:
- Models: Lorentzian (primary), Gaussian and Voigt (variants), linear baseline; fit windows recorded.
- Outputs per trace: centre f0, FWHM, amplitude, baseline params, **full covariance**, residual diagnostics (χ²/dof, residual autocorrelation, worst-point), convergence flags. Point uncertainties for downstream fits derive from the fit covariance — with the honesty note that residual-derived σ replaces the retired ±0.05 MHz digitisation floor and the derivation method is stated in the output header.
- **Comparison against Angus's fitted values where both exist:** per-trace Δcentre and ΔFWHM tables; headline = OUR fits from raw (reproducible in-repo), his values carried as the cross-check column with attribution; discrepancy > combined uncertainty → flagged, investigated (model choice first), never averaged away.

**Power-dependence modelling (extends `slope_fit.py` as `fit_power_models`):**
- Candidates: linear WLS (primary, the T3 continuation); piecewise-linear with one changepoint; quadratic (the only "low-order nonlinear" admitted).
- **Overfitting guard — RATIFIED as D6 (2026-07-20), a strict AND gate:** piecewise and quadratic are claimable ONLY if BOTH (i) the dataset supplies **≥ 8 independent power points per sample** AND (ii) **ΔAICc ≥ 4** in favour of the nonlinear model relative to linear WLS. Per-point σ quality does not substitute for the point count; with the current 4–6 points per sample the nonlinear models are reported-only diagnostics regardless of ΔAICc. When the gate is not met, linear stands and the alternatives are listed with their ΔAICc, unclaimed. The h14 10.16→12.33 mW step question is re-tested on raw errors (the digitisation-floor z = −1.93 verdict retires with the floor).
- **Linewidth vs power:** FWHM(P_opt) and — if MW powers vary or he supplies an MW-power series — FWHM(P_MW). **Extrapolation toward zero optical and zero MW power only where the model comparison supports the functional form over the measured range:** a linear form that stands may be extrapolated to its intercept; any NONLINEAR extrapolation basis must first pass the D6 strict AND gate (≥ 8 points AND ΔAICc ≥ 4). The extrapolated intercept is reported with its CI and grade "fit-extrapolated", NEVER as a measured linewidth. If the data cannot discriminate the form, the extrapolation is refused in print ("insufficient support for extrapolation"), and the lowest-power measured FWHM is reported as the operational bound instead.

---

## 4. Exact recalculations, in dependency order

1. **T3 re-fit — d14/h14 slopes** on raw-fit centres with covariance-derived errors → new slopes ± σ, χ²/dof as lack-of-fit; digitized-vs-raw slope deltas tabulated.
2. **d14/h14 sensitivity ratio** with correlated-error propagation from the per-trace covariances.
3. **T4 — geometry-sufficient verdict re-run:** identical pre-fixed three-way rule (inside-2σ → geometry-sufficient; all-one-side → intrinsic-required; straddle-without-inside → indeterminate) on the re-measured ratio; sweep axes COLLAPSED where metadata landed (thickness → measured ± unc; h_sub decade sweep narrowed per §4.6; spot unchanged unless he measures it); `discriminating_power` and the glue-confound φ recomputed on the narrowed sweep; COMSOL contingency trigger unchanged.
4. **η_abs·R_int (T5):** re-fit on raw slopes; if the power plane resolves to AT_SAMPLE, η_abs is bounded by absorption+optics only and the T4 η-cancellation condition text is rewritten accordingly; if DIODE_OUTPUT (or upstream), delivery loss folds into η_abs by construction — recorded as such, and the ~0.16 fitted values are re-interpreted, not re-graded upward. Either way ΔT/P fits are plane-independent (the standing statement, kept).
5. **Inferred ΔT:** probe-inferred heating at max power (η_abs-free triplet-thermometer reading) re-computed with raw slopes over the full `DF_SPIN_DT` band; point + band as in the current feed.
6. **Bond-line and placement sensitivity:** with cement bond-line thickness (+ a cement-k literature value pulled and graded on OUR side, flagged as literature-for-a-named-product), the underside lump gets a computed series-resistance BAND (glass + bond line) — the decade sweep 1e2–1e5 narrows to that band ± a stated contact-resistance allowance, as a dated supersession of `UndersideCoupling` with the derivation in the docstring; per-sample h_sub stays free within it (the confound is narrowed, not deleted). CPW placement/via metadata → a lateral-asymmetry / effective-sink note quantified at the level the rig model supports (an h_sub asymmetry prior between samples if the photos/his answer show different via proximity), feeding the T4 confound bound — no new solver physics unless the ratio test's contingency fires.
7. **The two-linewidth κs input** — the one output that crosses to the cavity side, and it crosses through `provenance/constants.py` ONLY: new linewidth values (especially low-power extrapolations, if supported per §3) are candidate re-grades of `KAPPA_S` (point/band). This is a SEPARATE changeset whose trigger is now fully defined — **RATIFIED as D4 (2026-07-20), a strict conjunction; `KAPPA_S` moves ONLY after ALL THREE hold:** (i) the raw spectra have been fitted and the candidate linewidths WITH uncertainties are recorded in-repo (graded constants-in-waiting in the calibration namespace + a dated SPEC §6T note); (ii) **Oxborrow explicitly answers which linewidth class is physically appropriate for the two-linewidth threshold model** (operating-power ODMR FWHM vs low-power-extrapolated vs other — the drafted findings note asks exactly this); and (iii) the selected estimate satisfies the applicable §3 fit-quality gates and, where extrapolated, the §3 extrapolation gates (incl. D6 where the basis is nonlinear). Until all three: recorded-in-waiting, `KAPPA_S` untouched. When it does move, the enumerated ripple executes in one dated changeset: `KAPPA_S` fields + docstring; `compose.KAPPA_S_BRANCHES` consumers unchanged in code but re-pinned in `test_sweep_compose.py`; `thermal/reports/q_margin_turnover.md` + `q_margin_planning_point.md` regenerated via their generators (crossings Q± move); F5 waterfall regenerated + `test_figures.py` token pins; SPEC §6T/§7.T4 dated lines; all deltas declared.

## 5. Files, reports, tests, figures likely to change

**New:** raw archive + manifest; `calibration/raw_ingest.py`, `calibration/lineshape.py`, `calibration/tools/xlsx_to_csv.py` (as needed); derived raw-version CSVs; reports `slope_fit_raw.md`, `ratio_test_raw.md`, `absolute_fit_raw.md`, `lineshape_fits_raw.md`; regenerated `observable_a_feed.json` (dataset-versioned, digitized copy archived per §1.3); tests `test_calibration_raw_ingest.py`, `test_calibration_lineshape.py`, + refit pins.
**Modified (dated, additive):** `calibration/constants.py` (metadata dataclasses; `DIGITIZED_SIGMA_MHZ` retirement note; `UndersideCoupling`/`CrystalThickness`/`ExcitationSource.power_plane` supersession annotations); `tests/test_calibration_{slope_fit,ratio_test,absolute_fit}.py` (raw-version pins added; digitized pins KEPT against the archived digitized artifacts so the record stays enforced); `docs/plans/layer_b_calibration_plan.md` (dated as-executed addendum); `SPEC.md` §11 item 5 dated status block.
**Conditionally (κs ratified):** `provenance/constants.py`, `test_provenance_*` pins, `test_sweep_compose.py`, turnover/planning-point reports + their content pins, `f5_margin_waterfall` + figure token tests, SPEC §6T/§7.T4.
**Never:** bytes of any existing raw archive; the digitized CSV; archived reports' bytes; anything in `src/cavity/` outside the ratified κs changeset; the import-boundary direction.

## 6. Decision tree for claim strength (pre-registered)

Model set for the d14/h14 comparison: M0 = shared transport, per-sample geometry only (the current T4 branch); M1 = M0 + one intrinsic per-sample multiplier (an isotope term on Θ or df/dT — NOT decomposed further; k-isotope vs df/dT-deuteration stay indistinguishable here by design).

- **Geometry sufficient, deuteration unresolved** (M0 inside the pre-fixed criterion): the current claim class, restated at the raw grade — "not required and not excluded" carries verbatim; discriminating-power number updated.
- **Evidence favouring an additional isotope term** — claimed ONLY if ALL of: M1 preferred decisively (stated ΔAICc/Bayes threshold, fixed before fitting); the glue-contact confound φ, on the metadata-narrowed h_sub band, cannot reproduce the ratio; the power-plane question is resolved (else the η-cancellation condition is untested); and the settling protocol passes §6's steady-state check. Anything less → the verdict stays at "not required, not excluded". **No claim that deuteration is detected unless the model comparison genuinely discriminates it — this sentence appears verbatim in every report this plan generates.**
- **Insufficient discriminating power** (band still brackets from both sides, or metadata didn't land): say exactly that; the feed's `discriminating_power` field carries it.
- **Acquisition protocol inconsistent with steady state** (settling time short vs the thermal time constant the rig model computes from the ingested geometry; or raw traces show order/hysteresis effects between adjacent powers): ALL steady-state fits re-grade to "protocol-caveated"; slopes reported with the transient caveat; assumption 7 of the Layer B register flips from "unverified" to "violated"; the honest product is then the settling-time-aware bound, and the follow-up ask is a hold-time series — no steady-state claims survive the check unqualified.

**Explicit parameter separation, carried in every fit output:** experimental observables (per-trace centre frequencies, FWHMs, labelled powers + plane, geometry measurements) — fitted nuisance parameters (η_abs, h_sub per sample, spot diameter, unmeasured thicknesses, baseline/lineshape params) — transport parameters (k_PTP band, geometry factor Θ from the rig solver) — isotope/deuteration terms (M1's multiplier only, entering solely through model comparison). No quantity migrates categories silently; the feed JSON gains a `parameter_roles` block naming each.

## 7. Concrete acceptance criteria

- Archive verifies both directions in CI; zero byte changes to prior archives (existing `TestRealArchive` stays green).
- Loaders refuse ungraded/unversioned data (tested); digitized loader still loads the digitized record (tested).
- Every fit output carries dataset_version, grade, covariance, and residual diagnostics; lineshape fits reproduce a committed synthetic-spectrum truth set within stated tolerance (new anchor tests, §8-discipline).
- T3–T5 raw results regression-pinned; digitized-era pins retained against archived artifacts; all deltas (digitized→raw) tabulated in one report section, with sign and σ.
- The three-way T4 rule and the §6 claim thresholds appear in the code/tests BEFORE the raw numbers are looked at (pre-registration enforced by commit order within the changeset).
- κs: no `provenance.KAPPA_S` movement without the ratification changeset; grep-level check in review notes.
- Suite green at a declared collection count; import boundary test green.

## 8. Out of scope
No maser-geometry transfer of any rig number (NON-TRANSFERABLE stands); no Layer A coupling except the ratified κs path; no COMSOL (the analytic engine remains sufficient unless the pre-fixed T4 contingency fires — indeterminate AND verdict flips across the radius-mapping band); no editing of `src/cavity/` physics.
