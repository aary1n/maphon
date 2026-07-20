# Claim–evidence matrix

**Status: PLANNING ARTIFACT (paper spine, 2026-07-20).** One row per
prospective paper claim. The YAML block at the end is the machine-readable
register consumed by `python -m publication.build` (WS4); the prose table and
the YAML must stay in sync (guarded by `tests/test_paper_spine.py`).

Vocabulary:
- **category** — measured / derived / fitted / inferred / planning-grade /
  supervisor-unratified (multiple allowed; "measured" is reserved for
  quantities someone actually measured, none of which are ours in this repo).
- **evidence_chain** — `complete` means: producing code → committed artifact →
  guarding test all exist at the claim's stated grade. `missing:` names the
  absent link. A chain can be complete at planning grade — completeness is
  about traceability, not about scientific maturity.
- **headline** — a claim the paper would lead with. The publication build
  command refuses "headline-ready" status while any headline claim has an
  incomplete chain or an unresolved blocker.

Cross-references: outline sections in `paper/manuscript_outline.md`; referee
exposure in `paper/reviewer_attack_surface.md`; artifact contract in
`paper/figure_contract.yaml`.

---

## Headline claims

### C1 — Thermal-margin distribution (THE owned deliverable)
- **Strongest wording currently permitted:** "At planning grade, a
  two-linewidth composition over imported planning values gives a
  point thermal margin Δf_max ≈ 11.4 MHz / ΔT_max ≈ 3.9 K for the
  composite planning cavity, with stated κs-band and coefficient-band
  envelopes (≈1.8–5.8 K); the population distribution is designed but not
  yet computed."
- **Prohibited stronger wording:** any distributional statement
  ("the population margin is…", "X% of builds survive…"); any
  device-validated margin; presenting 3.9 K as a measured or ratified
  number.
- **Evidence rung:** planning-grade composition; supervisor-UNRATIFIED
  (both the law's result and the budget-distribution framing).
- **Source:** two-linewidth law (SPEC §7.T4 re-derivation 2026-07-13);
  §5a rejudged record Q₀; `KAPPA_S`/`DF_SPIN_DT`/`DF_CAVITY_DT` grades.
- **Code:** `cavity.thermal.detuning` (`delta_f_max_hz`, `delta_t_max_k`,
  `q_loaded`), `cavity.thermal.report_margin.build_report`.
- **Tests:** `tests/test_thermal_detuning.py::test_a6_kappa_c_cyclic_hz_and_planning_point`,
  `::test_a11_report_status_notes_and_byte_pin`; `tests/test_figures.py::test_f5_data_pins`.
- **Artifacts:** `thermal/reports/q_margin_planning_point.md`,
  `docs/figures/f5_margin_waterfall.{png,pdf}`.
- **Chain:** **missing** — (i) no Layer A/C population run exists (blocked:
  Q2/Q9/Q13, Phase 1b engine, W2 anchor, licence, 209-solve campaign);
  (ii) `PLANNING_C0 = 190` is a report-local literal in
  `cavity/thermal/report_margin.py`, not a graded constant in
  `provenance/constants.py` (claim-trace finding, 2026-07-20; confirmed
  by the final adversarial review as its BLOCKER 4). **Deliberate
  deferral (2026-07-20):** promoting it into the provenance module
  creates a new graded planning-import constant — a §6-discipline
  changeset that wants user ratification, not a side effect of a
  publication-layer pass. Until then the literal stays disclosed here,
  pinned by `test_paper_spine.py::TestResultRegisterStaleness::
  test_planning_c0_flagged_as_ungraded`, and blocks headline readiness
  through this chain entry.
- **Unlocked by:** Oxborrow replies (Q13/Q2/Q9) → W2 pass → Layer A campaign
  → Layer C; plus ratification (below).

### C2 — Two-linewidth threshold law and the Q-margin turnover (E ≈ +0.35)
- **Strongest wording:** "For the linearised two-mode threshold with
  frequency pulling, Δf_max = ((κc+κs)/2)√(C₀−1); under the fixed-G planning
  calibration the Q-margin exponent at the operating point is ≈ +0.35 —
  sign-inverted relative to the κs → 0 napkin law — with the turnover set by
  the linewidth hierarchy. Derived, planning-tier, unratified."
- **Prohibited:** "higher-Q cavities have more thermal margin" as an
  established device result; any headline use of E ≈ +0.35 before
  ratification; presenting the fixed-G crossings as physical.
- **Rung:** derived (independently verified on the record);
  supervisor-UNRATIFIED — the QUESTION is endorsed (Oxborrow-verbal
  2026-07-06), the RESULT is not; findings note drafted, NOT sent
  (`docs/q_margin_two_linewidth_findings_note.md`).
- **Code:** `cavity.thermal.detuning.q_margin_exponent`,
  `cavity.thermal.report_turnover.build_report`.
- **Tests:** `tests/test_thermal_detuning.py::test_a5_two_linewidth_exponent_limits`,
  `::test_a14_closed_form_turnovers_and_no_crossing_branch`,
  `::test_a14_turnover_report_byte_pin`.
- **Artifacts:** `thermal/reports/q_margin_turnover.md`.
- **Chain:** **missing** — same `PLANNING_C0` ungraded literal; the joint
  C₀/κc/κs dependence on geometry DOFs (SPEC §11 item 9 residue) is underived
  (Layer A); the κs branch is undiscriminated (D4 conjunction pending).
- **Unlocked by:** Oxborrow ratification of the findings note; Angus
  low-power linewidths + Oxborrow linewidth-class ruling (D4); Layer A.

### C9 — Literature Q-spread explanation · C10 — Tolerance/design budget
- **Strongest wording:** none — not produced. The outline carries them as
  the Layer A/C dependents they are.
- **Chain:** **missing** — everything downstream of the unrun campaign.
- **Unlocked by:** same chain as C1.

## Validation and provenance claims (supporting)

### C3 — §5a Booth anchor GREEN (5 pass / 0 fail / 1 deferred)
- **Strongest wording:** "The forward model reproduces Booth's TE01δ anchor:
  f to 4 s.f., Q₀ to +0.02% (faithful branch), and V_mode to +0.21% against
  the Booth-implied value under an INFERRED partial-revolution
  normalisation of her print (mechanism read from the reference model;
  Booth-side confirmation PENDING — see C3b), wall split inside the
  committed window. Phase 1 is NOT complete — the confinement row is
  deferred to the Layer A trajectory." *(Wording carries C3b's caveat
  inline — adversarial-review fix 2026-07-20: the V_mode clause is not
  independently reusable without the pending-confirmation rider.)*
- **Prohibited:** "Phase 1 complete"; "model fully validated"; quoting the
  canonical-branch Q₀ as having passed the ±1% Booth window (it never did —
  branch delta −3.10% is documented).
- **Rung:** derived, archived; gate re-based on the corrected anchor at
  unchanged tolerance.
- **Code:** `cavity.validation.run_5a` (rejudge path),
  `cavity.validation.report_5a.render_checkpoint_markdown`.
- **Tests:** `tests/test_report_5a.py::test_rejudged_checkpoint_record_regenerates_byte_identical`,
  `::test_rejudged_manifest_records_archive_judgment`;
  `tests/test_figures.py::test_f1_data_pins`, `::test_f2_data_pins`.
- **Artifacts:** `refs/gate_runs/20260711T132705Z_rejudge/` (immutable),
  F1/F2 figures.
- **Chain:** complete (at its grade).
- **Unlocked by (stronger claim):** confinement trajectory (licence) →
  `phase1_complete`.

### C3b — Booth V_mode 225/360 partial-revolution finding
- **Strongest wording:** "Booth's printed V_mode carries a 225°/360°
  partial-revolution normalisation (mechanism read from the reference model's
  results tree; quantitative closure +0.21%; her Table 8 is internally
  consistent so comparative conclusions survive). Pending Booth-side
  confirmation."
- **Prohibited:** "Booth's thesis is in error" (confirmed-tone); using the
  corrected V without the pending-confirmation caveat; presenting the TE01δ
  row's inheritance as directly observed (it is uniform-workflow inference).
- **Rung:** inferred (mechanism confirmed in the one `.mph` in hand; row
  inheritance by inference + closure); externally UNCONFIRMED (findings note
  drafted, not sent — `docs/booth_vmode_findings_note.md`).
- **Code/constants:** `BOOTH_TABLE8_REVOLUTION_FACTOR`,
  `BOOTH_IMPLIED_V_MODE_M3`, `BOOTH_IMPLIED_F_M` (provenance).
- **Tests:** `tests/test_provenance_targets.py` (derived-anchor pins),
  `tests/test_validation_gate.py` (fork guard on the F_m identity).
- **Chain:** complete at its rung.
- **Unlocked by:** Booth/Oxborrow written confirmation (note must be SENT).

### C14 — Wu build re-base (k = 1 ⇒ Q₀ = 7200; geometry; tanδ ceiling 1.4e-4)
- **Strongest wording:** "The modelled build is the Wu STO ring, with every
  dimension re-verified against the archived primary PDFs; Wu's output
  coupling k = 1 is stated in print, giving Q₀ = 2Q_L = 7200 (independently
  corroborated) and a measured-device effective-loss ceiling
  tanδ ≤ 1.4×10⁻⁴; the ring-height print fork {8.5, 8.6} mm is disclosed and
  unresolved (Q13)."
- **Prohibited:** any plain-float ring height; silently selecting 8.6;
  claiming the model reproduces this build (that is C5/W2, unsolved).
- **Rung:** literature (re-verified 2026-07-20 against
  `calibration/data/raw/wu_build_papers_2026-07-18/` including the k = 1
  sentence, both Q₀ = 7200 prints, and both fork branches).
- **Code/constants:** `provenance.GEOM_WU_STO_RING`, `STO_HEIGHT_FORK`,
  `TARGETS.wu_ring`, `TOL.tan_delta_max`, `WU_PUMP_BEAM`.
- **Tests:** `tests/test_provenance_wu_geometry.py` (all pins incl.
  `::test_forked_constant_refuses_float_coercion`,
  `::test_tan_delta_max_rederivation_arithmetic`);
  `tests/test_provenance_targets.py::test_wu_ring_deload_yields_q0_7200`,
  `::test_no_gate_row_binds_wu_ring_until_w2`;
  `tests/test_calibration_integrity.py::TestRealArchive::test_wu_build_papers_archive_intact`.
- **Chain:** complete.
- **Unlocked by (stronger):** Q13 resolution collapses the fork.

### C5 — Wu-anchor validation (W2)
- **Strongest wording:** none about model-vs-build agreement — no W2 solve
  exists. Permitted: "acceptance windows were ratified in advance of any
  solve, with V_mode held out of gates pending an integration-convention
  check."
- **Prohibited:** any statement that the model reproduces the Wu build.
- **Rung:** planning (windows ratified 2026-07-19 as planning choices).
- **Artifacts:** `docs/w2_wu_anchor_windows.md`.
- **Chain:** **missing** — the solve itself (Q13 + licence session).

### C17 — Booth geometry recovery (torus, ratio-exact minor radius)
- **Strongest wording:** "Booth's under-specified cross-section is recovered
  from her own construction ratios and the supervisor-supplied reference
  model (torus, minor radius x/5 = 2.456 mm, major x/2), empirically
  confirmed by f (4 s.f.) and Q (+0.02%)."
- **Rung:** derived (document recovery + empirical closure).
- **Code/artifacts:** `provenance.GEOM_BOOTH_TE01D`,
  `refs/booth_geometry_recovery.md`.
- **Tests:** `tests/test_provenance_booth_geometry.py`.
- **Chain:** complete.

## Thermal-model claims (supporting)

### C6 — S-ladder ballpark scenario table
- **Strongest wording:** "Ballpark-tier idealised scenarios for the
  homogeneous planning crystal: S0 exact 1-D anchor (machine-precision);
  S1 imposed-cold ratios (log-divergent-inflow caveat stated); S4 side-fire
  bracket pair (m = 0 smear = structural lower bracket, spot estimate =
  upper). Power axis is a scoping grid — no CW operating point is derivable
  from print."
- **Prohibited:** "device predictions"; deriving a Wu CW power; composite
  crystal+STO+spacer numbers (above ballpark tier, out of scope).
- **Rung:** derived, ballpark tier (Oxborrow-verbal 2026-07-16 mandate).
- **Code:** `cavity.thermal.report_s_ladder`, `cylinder`, `side_deposition`,
  `layered`.
- **Tests:** `tests/test_thermal_s_ladder.py::test_report_regenerates_byte_identical`,
  `::test_report_numbers_match_independent_recomputation`,
  `::test_s4_upper_bracket_exceeds_m0_lower_across_grid`.
- **Artifacts:** `thermal/reports/s_ladder_ballpark.md`.
- **Chain:** complete.

### C7 — Inhomogeneous thermal line observable (shift + width in linewidths)
- **Strongest wording:** "Machinery exists and is anchored (uniform-T ⇒
  exactly zero width; closed-form moment checks); no device prediction has
  been produced."
- **Prohibited:** any predicted linewidth number for either geometry.
- **Rung:** derived machinery; w_s headline mode UNRATIFIED; gain mask =
  STO fallback until Phase 1b.
- **Code:** `cavity.thermal.broadening`.
- **Tests:** `tests/test_thermal_broadening.py::test_uniform_field_gives_pure_shift_and_exactly_zero_width`
  et al.
- **Chain:** **missing** — no committed report/figure presents the
  observable (claim-trace finding 2026-07-20), and the maser instance needs
  Phase 1b w_s co-registration.
- **Unlocked by:** Phase 1b + W1; a committed observable artifact.

### C8 / C18 — Identifiability: plate conditional (k·w), film unidentifiable; volumetric generalisation
- **Strongest wording:** "In the spreading regime the plate observable is the
  product k·w — an independent spot measurement factorises it (w-prior
  ×2.3–3.2, loosening with burial); a film measurement has no k-lever
  (insensitive, not underdetermined). Conditional on the rig metadata still
  pending (form/thickness/spot)."
- **Rung:** derived at planning grade; l_abs axis UNSOURCED-SCOPING.
- **Code:** `cavity.thermal.identifiability`, `volumetric_3a`.
- **Tests:** `tests/test_thermal_identifiability.py::test_r_map_regression_pins`,
  `::test_regime_inversion_plate_vs_film`;
  `tests/test_thermal_volumetric.py::test_volumetric_regression_pins`.
- **Artifacts:** `thermal/reports/identifiability_3a_computed.md`,
  `identifiability_3a_volumetric_computed.md` (+ maps). NOTE (claim-trace
  2026-07-20): the NARRATIVE files `identifiability_3a.md` /
  `identifiability_3a_volumetric.md` are dated hand-authored records whose
  headers advertise the generator of their `_computed` counterparts — cite
  the `_computed` files for numbers.
- **Chain:** complete at planning grade (with the narrative/generated
  distinction recorded).

### C11 — df_cavity/dT = +2.73 MHz/K, band [+2.3, +2.9] (293–323 K)
- **Rung:** derived (M→D) from in-hand microwave parameterisations;
  MODEL-ONLY arm; R&B parameter values bottom out in an unpublished report
  (stated); envelope reading "293+30=323" is ours.
- **Code:** `provenance.cavity_df_dt_hz_per_k`, `DF_CAVITY_DT`.
- **Tests:** `tests/test_provenance_df_cavity_dt.py`.
- **Chain:** complete.

### C12 — df_spin/dT = −109 kHz/K, band [−120, −64] (raw-data grade)
- **Rung:** fitted (OLS on the archived raw point series); the
  temperature-axis branch is the dominant systematic and IS the band; the ±
  is ours (no printed uncertainty exists); deuteration-transfer caveat rides.
- **Code/artifacts:** `cavity.provenance.singh_raw_fits`,
  `refs/singh_2025_raw/` (SHA-pinned), `refs/singh_2025_raw/fit_report.md`.
- **Tests:** `tests/test_provenance_df_spin_dt.py`.
- **Chain:** complete. Attribution brokering (via Oxborrow) still pending —
  a publication-readiness item, not an evidence item.

### C13 — κs = 1.4 MHz (band 0.55–1.75), cyclic-Hz FWHM
- **Rung:** inferred from the scraped Cowley-Semple linewidth table
  (best-per-host-at-differing-powers caveat rides every consumer); BRANCH
  CHOICE, not best estimate; raw table + low-power extrapolation is a
  load-bearing pending ask.
- **Code:** `provenance.KAPPA_S`.
- **Tests:** `tests/test_thermal_detuning.py::test_a6_kappa_c_cyclic_hz_and_planning_point`
  (2π-trap guard), `tests/test_sweep_compose.py` (branch carriage),
  `tests/test_surrogate_cv_gate.py` (branch printed in gate reports).
- **Chain:** complete at its grade. **Unlocked by:** D4 strict conjunction
  (raw fits + Oxborrow class ruling + fit gates) → `KAPPA_S` re-grade.

### C15 — Crystal εr = 3.0 [2.4, 4.1] (Q11, planning grade)
- **Rung:** planning-grade resolution (anthracene-analogy three-layer chain;
  negative space recorded); first non-mock `SentinelResolution`.
- **Code:** `cavity.sweep.resolutions.RESOLUTION_Q11`.
- **Tests:** `tests/test_sweep_resolutions.py` (all five).
- **Chain:** complete at planning grade.

## Calibration claims (supporting; all digitized grade)

### C4 — Layer B T3/T4/T5 (slopes; geometry-sufficient verdict; η_abs·R_int; probe-inferred heating)
- **Strongest wording:** "At graph-digitized grade: d14 −0.100 ± 0.006 /
  h14 −0.0745 ± 0.006 MHz/mW (ratio 1.343 ± 0.132); the pre-registered
  three-way rule returns GEOMETRY-SUFFICIENT with low discriminating power —
  **an intrinsic deuteration effect is not required and not excluded**;
  η_abs·R_int = 917 [781, 1659] / 683 [573, 1252] K/W; probe-inferred heating
  at 14.39 mW = 13.2 / 9.8 K (η_abs-free), reproducing the 'several tens of
  Celsius' class at order of magnitude."
- **Prohibited:** deuteration detected/excluded; raw-grade language; a fixed
  power-measurement plane; transferring ANY rig number to the maser geometry
  (NON-TRANSFERABLE discipline).
- **Rung:** fitted, graph-digitized-provisional,
  `superseded_by_raw_data=True`.
- **Code:** `calibration.slope_fit.fit_all`, `ratio_test.run_ratio_test`,
  `absolute_fit.run_absolute_fits`.
- **Tests:** `tests/test_calibration_slope_fit.py::TestSlopePins`,
  `tests/test_calibration_ratio_test.py::TestRealSweepVerdict`,
  `tests/test_calibration_absolute_fit.py::TestFeedPins`.
- **Artifacts:** three T3–T5 reports + `calibration/reports/observable_a_feed.json`;
  addendum `ratio_test_digitized_addendum_2026-07-16.md` (dated record, no
  generator by design).
- **Chain:** complete at digitized grade.
- **Unlocked by:** Cowley-Semple raw traces (D4–D7 pipeline; supersession per
  D7), thickness, plane, spot.

### C19 — Deuteration identifiability / experiment design (WS3 study)
- **Strongest wording:** "A design study over the ratified nuisance grid
  shows the current d14/h14 dataset is insufficiently identifiable for
  isotope discrimination; the binding limiter is per-sample mounting
  (glue) asymmetry — the honest M0 envelope with unconstrained mounting
  spans two orders of magnitude — so mounting control (remount empirics /
  bond-line metrology) is the gateway measurement, ahead of thickness,
  spot, and power-plane metadata; guaranteed-detectable intrinsic factors
  X_det are quantified per metadata scenario."
- **Prohibited:** any statement that deuteration is detected, suggested,
  or excluded; using X_det as evidence about the actual samples; fixing
  any Angus-pending metadata value.
- **Rung:** derived, planning grade (design analysis on graded bands;
  digitized-grade measured σ).
- **Code:** `calibration.deuteration_design`.
- **Tests:** `tests/test_calibration_deuteration_design.py` (incl. the
  baseline-band cross-pin against the committed T4 feed and by-hand
  X_det/power-grid recomputations).
- **Artifacts:** `calibration/reports/deuteration_design.md`, `.json`.
- **Chain:** complete at its grade.
- **Unlocked by (sharper design outputs):** Angus metadata (collapses the
  scenario ladder to its realised branch); raw traces (σ_rel shrinks).

## Process / novelty claims

### C16 — Green-field novelty ("nobody else modelling thermal response")
- **Strongest wording:** "Within the collaboration, thermal-response
  modelling is an uncontested green field (Oxborrow, written, 2026-07-04),
  corroborated by Mann 2025's author-contribution statement."
- **Prohibited:** presenting the budget-distribution FRAMING as
  collaboration-agreed (unratified); "first ever" claims beyond the framing
  guard's wording.
- **Rung:** supervisor-written (quoted in SPEC revision block).
- **Chain:** **missing** — the 2026-07-04 email itself is NOT in the
  in-repo archives (only 2026-07-16/17 correspondence is archived); the
  quote's only in-repo record is SPEC's dated block. Archive the email
  (R10a-style) to complete the chain.
- **Unlocked by:** archiving the email; the framing itself by ratification.

---

## Machine-readable register (consumed by `publication.build`)

```yaml
schema: paper-claims/v1
generated: 2026-07-20
claims:
  - id: C1
    title: Thermal-margin distribution (owned deliverable)
    headline: true
    category: [derived, planning-grade, supervisor-unratified]
    rung: planning-composition; result+framing unratified
    artifacts: [thermal/reports/q_margin_planning_point.md, docs/figures/f5_margin_waterfall.png]
    producing_code: [cavity.thermal.detuning, cavity.thermal.report_margin]
    guarding_tests: [tests/test_thermal_detuning.py, tests/test_figures.py]
    evidence_chain: "missing: Layer A/C population run (Q2/Q9/Q13+W2+licence); PLANNING_C0 ungraded literal in report_margin.py"
    blocker: "Q2/Q9/Q13 open; Phase 1b engine; W2 unsolved; Oxborrow ratification"
    unlocked_by: "Oxborrow replies -> W2 pass -> Layer A campaign -> Layer C; ratification of law+framing"
  - id: C2
    title: Two-linewidth law + Q-margin turnover (E ~ +0.35)
    headline: true
    category: [derived, supervisor-unratified]
    rung: derived planning-tier; question endorsed, result unratified
    artifacts: [thermal/reports/q_margin_turnover.md]
    producing_code: [cavity.thermal.detuning, cavity.thermal.report_turnover]
    guarding_tests: [tests/test_thermal_detuning.py]
    evidence_chain: "missing: PLANNING_C0 ungraded; joint C0/kc/ks DOF derivation (Layer A item 9); ks branch undiscriminated"
    blocker: "findings note unsent; D4 conjunction open; Layer A"
    unlocked_by: "Oxborrow ratification; Angus low-power linewidths; Layer A joint-DOF regression"
  - id: C3
    title: Booth 5a anchor GREEN 5/0/1
    headline: false
    category: [derived]
    rung: archived gate record; phase1_complete false (confinement deferred)
    artifacts: [refs/gate_runs/20260711T132705Z_rejudge/booth_5a_checkpoint.md]
    producing_code: [cavity.validation.run_5a, cavity.validation.report_5a]
    guarding_tests: [tests/test_report_5a.py, tests/test_figures.py]
    evidence_chain: complete
    blocker: "confinement row deferred (Layer A trajectory, licence)"
    unlocked_by: "confinement trajectory -> phase1_complete"
  - id: C3b
    title: Booth V_mode 225/360 partial-revolution finding
    headline: false
    category: [inferred, supervisor-unratified]
    rung: mechanism confirmed in-hand; row inheritance inferred; Booth confirmation pending
    artifacts: [docs/booth_vmode_findings_note.md]
    producing_code: [cavity.provenance.constants]
    guarding_tests: [tests/test_provenance_targets.py, tests/test_validation_gate.py]
    evidence_chain: complete
    blocker: "findings note drafted, not sent"
    unlocked_by: "Booth/Oxborrow written confirmation"
  - id: C4
    title: Layer B calibration T3/T4/T5 (digitized grade)
    headline: false
    category: [fitted, planning-grade]
    rung: graph-digitized-provisional; superseded_by_raw_data=True
    artifacts: [calibration/reports/slope_fit_digitized.md, calibration/reports/ratio_test_digitized.md, calibration/reports/absolute_fit_digitized.md, calibration/reports/observable_a_feed.json]
    producing_code: [calibration.slope_fit, calibration.ratio_test, calibration.absolute_fit]
    guarding_tests: [tests/test_calibration_slope_fit.py, tests/test_calibration_ratio_test.py, tests/test_calibration_absolute_fit.py]
    evidence_chain: complete
    blocker: "raw traces / thickness / power plane / spot pending (Angus)"
    unlocked_by: "Cowley-Semple raw reply (D4-D7 pipeline)"
  - id: C5
    title: Wu-anchor W2 validation
    headline: false
    category: [planning-grade]
    rung: windows ratified as planning choices; NO solve exists
    artifacts: [docs/w2_wu_anchor_windows.md]
    producing_code: []
    guarding_tests: [tests/test_provenance_targets.py]
    evidence_chain: "missing: the W2 solve itself"
    blocker: "Q13 fork; COMSOL licence session"
    unlocked_by: "Q13 resolution + licence -> first W2-passing solve"
  - id: C6
    title: S-ladder ballpark scenarios
    headline: false
    category: [derived, planning-grade]
    rung: ballpark tier (Oxborrow-verbal mandate); scoping power grid
    artifacts: [thermal/reports/s_ladder_ballpark.md]
    producing_code: [cavity.thermal.report_s_ladder]
    guarding_tests: [tests/test_thermal_s_ladder.py]
    evidence_chain: complete
    blocker: "composite bodies above ballpark tier (deferred); S3 label reserved (Email B)"
    unlocked_by: "n/a at this tier"
  - id: C7
    title: Inhomogeneous thermal line observable
    headline: false
    category: [derived, supervisor-unratified]
    rung: machinery anchored; w_s headline mode unratified; no prediction
    artifacts: []
    producing_code: [cavity.thermal.broadening]
    guarding_tests: [tests/test_thermal_broadening.py]
    evidence_chain: "missing: no committed observable artifact; Phase 1b w_s co-registration"
    blocker: "Phase 1b; W1; w_s ratification"
    unlocked_by: "Phase 1b + W1 -> committed observable artifact"
  - id: C8
    title: Identifiability 3a (plate k*w conditional; film no lever)
    headline: false
    category: [derived, planning-grade]
    rung: computed, regression-pinned; rig metadata pending
    artifacts: [thermal/reports/identifiability_3a_computed.md, thermal/reports/identifiability_3a_volumetric_computed.md]
    producing_code: [cavity.thermal.identifiability, cavity.thermal.volumetric_3a]
    guarding_tests: [tests/test_thermal_identifiability.py, tests/test_thermal_volumetric.py]
    evidence_chain: complete
    blocker: "form/thickness/spot pending (Angus); l_abs unsourced-scoping"
    unlocked_by: "Angus metadata; measured penetration data"
  - id: C9
    title: Literature Q-spread explanation
    headline: true
    category: [planning-grade]
    rung: not produced
    artifacts: []
    producing_code: []
    guarding_tests: []
    evidence_chain: "missing: Layer A population + (optional) Bayesian re-inference"
    blocker: "Layer A campaign"
    unlocked_by: "Layer A -> Layer C"
  - id: C10
    title: Tolerance / design budget
    headline: true
    category: [planning-grade]
    rung: not produced
    artifacts: []
    producing_code: []
    guarding_tests: []
    evidence_chain: "missing: Layer A/C outputs"
    blocker: "Layer A campaign"
    unlocked_by: "Layer A -> Layer C -> Sobol/OaT curves"
  - id: C11
    title: df_cavity/dT +2.73 MHz/K band [2.3, 2.9]
    headline: false
    category: [derived]
    rung: M->D from in-hand microwave sources; model-only arm
    artifacts: []
    producing_code: [cavity.provenance.constants]
    guarding_tests: [tests/test_provenance_df_cavity_dt.py]
    evidence_chain: complete
    blocker: "none (R&B numeric values report-depth, stated)"
    unlocked_by: "n/a"
  - id: C12
    title: df_spin/dT -109 kHz/K band [-120, -64] (raw grade)
    headline: false
    category: [fitted]
    rung: raw-data-graded; axis branch = dominant systematic; +- is ours
    artifacts: [refs/singh_2025_raw/fit_report.md]
    producing_code: [cavity.provenance.singh_raw_fits]
    guarding_tests: [tests/test_provenance_df_spin_dt.py]
    evidence_chain: complete
    blocker: "axis-definition ask (Harpreet); attribution brokering (Oxborrow)"
    unlocked_by: "axis metadata; Zenodo access if +- becomes load-bearing"
  - id: C13
    title: kappa_s 1.4 MHz band [0.55, 1.75] cyclic-Hz FWHM
    headline: false
    category: [inferred, planning-grade]
    rung: scraped-thread table; branch choice; best-per-host caveat
    artifacts: []
    producing_code: [cavity.provenance.constants]
    guarding_tests: [tests/test_thermal_detuning.py, tests/test_sweep_compose.py]
    evidence_chain: complete
    blocker: "raw table + low-power extrapolation (Angus); class ruling (Oxborrow) - D4 conjunction"
    unlocked_by: "D4 conjunction -> KAPPA_S re-grade changeset"
  - id: C14
    title: Wu build re-base (k=1, Q0=7200, geometry, tan-delta ceiling)
    headline: false
    category: [derived]
    rung: literature, re-verified vs archived PDFs (incl. 2026-07-20 pass)
    artifacts: [calibration/data/raw/wu_build_papers_2026-07-18/MANIFEST.sha256]
    producing_code: [cavity.provenance.constants]
    guarding_tests: [tests/test_provenance_wu_geometry.py, tests/test_provenance_targets.py, tests/test_calibration_integrity.py]
    evidence_chain: complete
    blocker: "Q13 fork open (disclosed)"
    unlocked_by: "Q13 resolution"
  - id: C15
    title: Crystal eps_r 3.0 [2.4, 4.1] (Q11 planning resolution)
    headline: false
    category: [planning-grade]
    rung: planning-assumption; first non-mock SentinelResolution
    artifacts: []
    producing_code: [cavity.sweep.resolutions]
    guarding_tests: [tests/test_sweep_resolutions.py]
    evidence_chain: complete
    blocker: "none at planning grade; future eps_r sensitivity check"
    unlocked_by: "n/a"
  - id: C16
    title: Green-field novelty (collaboration)
    headline: false
    category: [inferred, supervisor-unratified]
    rung: supervisor-written quote (in SPEC); framing unratified
    artifacts: []
    producing_code: []
    guarding_tests: []
    evidence_chain: "missing: the 2026-07-04 email is not archived in-repo"
    blocker: "email archive; framing + first-paper-boundary ratification"
    unlocked_by: "archive the email; Oxborrow ratification"
  - id: C19
    title: Deuteration identifiability / experiment design study
    headline: false
    category: [derived, planning-grade]
    rung: design analysis on graded bands; refuses detection claims
    artifacts: [calibration/reports/deuteration_design.md, calibration/reports/deuteration_design.json]
    producing_code: [calibration.deuteration_design]
    guarding_tests: [tests/test_calibration_deuteration_design.py]
    evidence_chain: complete
    blocker: "none at design grade; sharper outputs await Angus metadata + raw traces"
    unlocked_by: "Angus metadata collapses the scenario ladder; raw traces shrink sigma_rel"
  - id: C17
    title: Booth geometry recovery
    headline: false
    category: [derived]
    rung: document recovery + empirical closure
    artifacts: [refs/booth_geometry_recovery.md]
    producing_code: [cavity.provenance.constants]
    guarding_tests: [tests/test_provenance_booth_geometry.py]
    evidence_chain: complete
    blocker: "none"
    unlocked_by: "n/a"
  - id: C18
    title: Volumetric identifiability generalisation (k x g(w, l_abs))
    headline: false
    category: [derived, planning-grade]
    rung: computed, pinned; l_abs unsourced-scoping
    artifacts: [thermal/reports/identifiability_3a_volumetric_computed.md]
    producing_code: [cavity.thermal.volumetric_3a]
    guarding_tests: [tests/test_thermal_volumetric.py]
    evidence_chain: complete
    blocker: "measured penetration data preferred over nominal-doping arithmetic"
    unlocked_by: "Takeda 2002 / Breeze-era penetration pull"
```
