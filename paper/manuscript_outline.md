# Manuscript outline — STO TE01δ maser cavity: thermal operating margin (working title)

**Status: PLANNING ARTIFACT (paper spine, 2026-07-20). Not a draft manuscript.**
This outline maps each prospective section onto the claim register
(`paper/claim_evidence_matrix.md`, claim IDs `C*`) so that every sentence the
manuscript will eventually assert is traceable to a claim row with a stated
evidence grade, and every currently-blocked section is marked with what
unblocks it. SPEC.md is authoritative; where this outline and SPEC disagree,
SPEC wins. Results are the priority; the manuscript is post-placement
(SPEC §0).

**Register:** standard physics/UQ terminology (surrogate, PCE, GP, Sobol) —
SPEC's Register note applies.

**Working title candidates** (decision deferred; supervisor input expected):
- "Thermal operating margin of a room-temperature pentacene maser: a
  distributional forward model" (leads with C1 — requires Layer A/C complete)
- "How much heating can a solid-state maser absorb? Two-linewidth threshold
  margins for the STO TE01δ cavity" (leads with C2 — requires ratification)

**Attribution guards (binding, from SPEC):** the calibration data is the
**Cowley-Semple ODMR dataset** (Angus Cowley-Semple, Bayliss group, Glasgow) —
never "our measurement"; co-authorship/acknowledgement brokered via Oxborrow
EARLY (SPEC §7-expanded §7.8 data-status guard). The Singh raw series is
privately shared (Harpreet Singh, Ajoy group) — same early-brokering guard
(`SpinFreqTempCoefficient` caveats). Booth's V_mode finding (C3b) is presented
as a normalisation-convention identification pending Booth-side confirmation,
never as an error accusation.

---

## §1 Introduction

Claims consumed: C16 (novelty/green field), framing guard.

- Room-temperature pentacene:p-terphenyl masers; the Breeze/Booth/Wu lineage;
  the STO TE01δ cavity as the high-C₀ platform.
- The unmodelled question: pump-induced differential heating detunes cavity
  from spin line (STO's quantum-paraelectric εr(T)); operating margin, not
  static yield, is the open quantity. Wu's own single lumped ΔT ≈ 0.3 K
  estimate is the entire literature on the point.
- **Framing guard (verbatim discipline, SPEC §7-expanded §7.8):** no prior
  work modelled the maser's thermal operating margin across the build
  population, nor its scaling with Q. Do NOT assert any prior work specified
  thermal yield or margin analysis. Booth named MC/gradient-descent as future
  work for *shape optimisation* and did not execute it.
- Novelty positioning is **Oxborrow-endorsed at the green-field level only**
  (C16: "Neither Angus Cowley-Semple nor Ziqiu Huang is modelling thermal
  response", written 2026-07-04). The budget-*distribution* framing itself is
  OURS-UNRATIFIED — the introduction must not present it as agreed
  collaboration framing until SPEC §11 item 10 closes.
- BLOCKED decision: **first-paper boundary** (what belongs in paper 1 vs 2) is
  a genuinely pending Oxborrow question (SPEC §11 item 10). This outline
  carries the maximal single-paper scope; cutting is a ratification outcome.

## §2 Forward model and validation

Claims consumed: C3 (Booth §5a anchor GREEN), C3b (225/360 V_mode finding),
C17 (Booth geometry recovery), C14 (Wu build re-base), C5 (W2 anchor — BLOCKED).

- §2.1 Model: 2-D axisymmetric emw eigensolve; extraction conventions
  (Q = f′/2f″; 2πr Jacobian; loaded/unloaded split; the §8 analytic benchmark
  and PEC+lossy convention anchor).
- §2.2 Solver-correctness anchor (Booth): recovered torus geometry (C17),
  gate record GREEN 5/0/1 — f to 4 s.f., Q₀ +0.02%, V_mode +0.21% after the
  partial-revolution correction, wall split inside window.
- §2.3 The V_mode normalisation finding (C3b): Booth's printed 0.409 cm³
  carries the COMSOL default 225°/360° revolution factor (mechanism read from
  the reference `.mph`; quantitative closure +0.21%; her comparative
  conclusions survive — the factor is uniform across her Table 8).
  **Strongest permitted wording:** "identified a normalisation-convention
  difference … pending confirmation" — Booth-side written confirmation is
  PENDING; the findings note is drafted, not sent.
- §2.4 The modelled build (C14): Wu STO ring (k = 1 stated in print ⇒
  Q₀ = 7200; tanδ ceiling re-derived 1.4×10⁻⁴); Q13 height fork {8.5, 8.6} mm
  DISCLOSED as a print fork (verified two-sided against the archived PDFs).
- §2.5 **BLOCKED — Wu anchor validation (C5):** no W2 solve exists. Windows
  are ratified planning choices (`docs/w2_wu_anchor_windows.md`). Unblocks on
  Q13 resolution (Oxborrow reply/caliper) + a licence session. Until then the
  paper CANNOT claim the forward model reproduces the modelled build; it can
  claim solver correctness via Booth (§2.2) only.
- Honesty line carried from SPEC §5a: benchmark PASS ≠ phase complete —
  `phase1_complete` is FALSE on the deferred confinement row (Layer A
  trajectory block).

## §3 Analytical thermal submodel

Claims consumed: C6 (S-ladder), C7 (line broadening), C11 (df_cavity/dT),
C12 (df_spin/dT), C8/C18 (identifiability), plus the §7.T7 radiation check.

- §3.1 Transport core: cylinder Bessel/Robin closed forms; layered/Hankel rig
  solver; anchors (§8 discipline) incl. cross-solver agreement ≤1e-4.
- §3.2 Coefficients (graded): df_cavity/dT +2.73 MHz/K [2.3, 2.9] (C11 —
  derived from microwave parameterisations; MODEL-ONLY arm; integrate-don't-
  multiply for ΔT ≳ 20 K); df_spin/dT −109 kHz/K [−120, −64] (C12 —
  raw-data-graded; the temperature-axis branch IS the band; no printed
  uncertainty exists anywhere — the ± is ours). Signs opposite; detuning ADDS.
- §3.3 Scenario ladder at ballpark tier (C6): S0 exact 1-D anchor; S1
  imposed-cold idealisation (log-divergent-inflow caveat stated); S4
  side-fire bracket pair (m = 0 smear = structural lower bracket; spot
  estimate = upper member). Power axis is a SCOPING GRID — no shot repetition
  rate is in print, so no Wu-derived CW operating point exists.
- §3.4 Inhomogeneous thermal line observable (C7): shift + RMS width in
  linewidth units — the observable Oxborrow asked for; uniform-T zero-width
  limit exact in CI. No device prediction yet (w_s headline mode UNRATIFIED;
  gain mask = STO fallback until Phase 1b).
- §3.5 Radiation/convection: h_rad linearisation validity (5.1% at ΔT = 10 K,
  16% at 30 K); enclosure regime reframe (h → 0 floor); Rayleigh-onset
  nonlinearity caveat (2026-07-16). Open: the across-range competition report
  (maser-cylinder geometry) — SPEC §7.T7 follow-up.

## §4 Calibration against the Cowley-Semple ODMR dataset

Claims consumed: C4 (T3/T4/T5 at digitized grade), C8/C18 (identifiability),
C13 (κs grading), WS3 output (deuteration experiment design).

- §4.1 Dataset + rig (graded metadata; enclosure confirmed; spot
  collaborator-SUGGESTED 400 µm swept; thickness UNKNOWN swept 0.2–1.0 mm;
  power plane UNKNOWN — every statement plane-independent or branch-labelled).
- §4.2 T3 slopes: d14 −0.100 ± 0.006, h14 −0.0745 ± 0.006 MHz/mW (digitized
  grade; `superseded_by_raw_data=True` stamped — re-fit when raw lands).
- §4.3 T4 ratio verdict — **verbatim claim discipline:** "the d14/h14
  sensitivity difference does not REQUIRE a deuteration effect — an intrinsic
  effect is NOT REQUIRED and NOT EXCLUDED" (geometry-sufficient; low
  discriminating power; glue-contact confound documented; CPW via-contact
  caveat rides).
- §4.4 T5: η_abs·R_int fits; probe-inferred heating 13.2/9.8 K at 14.39 mW
  (η_abs-free) — reproduces Oxborrow's "several tens of Celsius" class at
  order of magnitude, not tuned to it.
- §4.5 Identifiability (C8/C18): plate observable = k·w product (CONDITIONAL
  on independent w to ×3); film has no k-lever (UNIDENTIFIABLE — insensitive,
  not underdetermined); volumetric burial only loosens the w-prior.
- §4.6 Deuteration identifiability / experiment design (WS3 artifact):
  what WOULD discriminate geometry-only from geometry+isotope; dominant
  nuisance; matched-sample and power-grid requirements. **This section makes
  no detection claim by construction.**
- BLOCKED upgrades: raw traces → all §4 numbers re-fit at raw grade
  (pre-registered pipeline, D4–D7 rulings); thickness/plane/spot metadata →
  sweep axes collapse.

## §5 Two-linewidth threshold and the Q-margin turnover

Claims consumed: C2 (law + sign inversion + turnover map), C13 (κs), C15
(crystal εr planning grade), C1 planning point.

- §5.1 The linearised two-mode threshold: C₀ = 1 + 4Δ²/(κc+κs)²;
  Δf_max = ((κc+κs)/2)√(C₀−1); frequency pulling as an outcome; the committed
  κs → 0 limit recovered. Unit discipline (cyclic-Hz FWHM; the W20
  angular-"Hz" trap).
- §5.2 The turnover map: exponent E(Q_L); crossings Q_− ≈ 63, Q_+ ≈ 973
  (κs = 1.4 MHz); operating point κc/κs ≈ 0.18 ⇒ E ≈ +0.35 — **sign-inverted
  vs the napkin 1/√Q**.
- **Rung discipline (hard):** the QUESTION is supervisor-endorsed
  (2026-07-06, verbal); the RESULT is UNRATIFIED (findings note drafted, NOT
  sent). The paper cannot headline E ≈ +0.35 until (i) Oxborrow ratifies the
  derivation + framing, (ii) the Layer A joint-DOF derivation replaces the
  fixed-G calibration, (iii) the κs branch is discriminated (Angus low-power
  extrapolation). Until then §5.2 is presented as a derived planning-tier
  turnover structure with the branch-dependence stated.
- §5.3 Planning point: Δf_max ≈ 11.4 MHz, ΔT_max ≈ 3.9 K (bands stated;
  C₀ = 190 IMPORTED, never recomputed from κs; κs branch labelled).

## §6 Thermal-margin distributions (THE owned deliverable) — BLOCKED

Claims consumed: C1, C9, C10. Entirely dependent on: Q13 + Q2 + Q9
resolutions (Oxborrow), Phase 1b engine + W2 pass (licence), Layer A training
campaign (209-solve budget), Layer C composition.

- §6.1 p(Δf_max), p(ΔT_max), p(P_max) at the tuned operating point with the
  three-channel error budget (sampling / emulator / thermal-coefficient).
- §6.2 Q-spread explanation (C9) and tolerance/design budget (C10); Sobol.
- This section exists in the outline so the claim matrix exposes it as the
  headline with **no current end-to-end evidence chain** — that absence is
  the honest state, not a gap to paper over.

## §7 Discussion and future work

- Margin implications; κs(ΔT) feedback (identified, deliberately not
  implemented); forced-air variant (flagged, not adopted); SPEC §9 exclusions
  stated as exclusions (shape optimisation, cooling channels, materials
  survey, loop-gap — Zangwill's project by name).
- Honest-limits paragraph: provenance table's three threats (η_opt hidden
  factors; κs sample-specificity; pump-conditional kinetic rates) as scope
  boundaries of any "parameter-free" language.

## Methods / appendices

- Extraction conventions + benchmark tables (§8 anchors, PEC+lossy residual).
- Provenance methodology: the graded-constant single-source discipline;
  forks/sentinels (Q13 shown as the worked example); archives + manifests.
- Reproducibility: `python -m publication.build` (WS4) — artifact
  regeneration, index, and the four separated statuses.

---

## Standing blockers table (mirrors claim matrix; regenerate mentally, not here)

| Blocker | Blocks sections | Unblocked by |
|---|---|---|
| Q13 height fork | §2.4–2.5, §6 | Oxborrow written reply (D1-responsive) or caliper |
| Q2 travel band | §6 (d8 design) | Oxborrow reply; D2 escape hatch after concrete-proposal follow-up |
| Q9 placement | §6, Phase 1b | Oxborrow reply (all three payload numbers) |
| W2 anchor solve | §2.5, sweep centre | Q13 + licence session |
| Raw ODMR traces | §4 raw grade | Cowley-Semple reply (D4–D7 pipeline ready) |
| κs branch | §5 headline | Angus low-power linewidths + Oxborrow class ruling (D4 conjunction) |
| Ratifications | §1 framing, §5.2, §6 | Oxborrow: findings note, budget-distribution framing, first-paper boundary |
| Confinement row | "Phase 1 complete" language | Layer A trajectory block (licence) |
