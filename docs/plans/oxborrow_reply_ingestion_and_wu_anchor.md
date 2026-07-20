# Plan — Oxborrow reply ingestion and the first W2 Wu-anchor solve

**Intended repo path:** `docs/plans/oxborrow_reply_ingestion_and_wu_anchor.md`
**Status: DRAFT FOR APPROVAL — nothing in the repository is edited by this plan. Planned against live `main` @ `0b2668f9410630ed29b61a08219e5b98c858f49c` (2026-07-19, "thermal: pin S1 inflow normalisation"), verified live via GitHub before writing. No COMSOL solve and no physics-number change is licensed by this document; it specifies what happens WHEN Mark Oxborrow's reply lands.**

**Rulings ratified 2026-07-20 (user):** D1 — an explicitly responsive written answer from Oxborrow resolves Q13 (no measurement required; question-unaware restatements do not count). D2 — the Q2 planning-assumption escape hatch is ARMED (provenance must preserve the exact proposal, the follow-up, and the recorded absence of reply). D3 — a reply-sourced non-15 mm internal height becomes the modelled W2 nominal at the written rung; 15 mm is never averaged with it or silently replaced (it stays the print record). D5 — informal bands ("give or take X") are read as UNIFORM bands, one convention everywhere.

Scope: the pending Oxborrow reply on (i) the Q13 STO-height print fork {8.5, 8.6} mm, (ii) the Q2 tuning piston — internal cavity height and usable travel, and (iii) crystal dimensions, nominal axial placement, and lateral centring tolerance (Q9 + the crystal-dims cross-build ask). Then the first W2 Wu-anchor solve and the transition into Phase 1b, Layer A, and the d = 8 / d = 7 decision.

Machinery of record (verified at HEAD): `cavity.sweep.dofs` (`SENTINEL_Q2/Q9/Q13`, `ForkTrace`, `SentinelResolution`, `_REQUIRED_PAYLOAD_KEYS`, `SOLVE_GATE_QUESTIONS`), `cavity.sweep.resolutions` (`RATIFIED_RESOLUTIONS`, currently Q11 only), `cavity.sweep.design.materialise_dims`, `cavity.sweep.backend` (`ComsolBackend`, `draw_solve_spec`), `cavity.sweep.centre_check`, `provenance.constants` (`STO_HEIGHT_FORK`, `GEOM_WU_STO_RING`, `TARGETS.wu_ring`), `docs/w2_wu_anchor_windows.md` (windows ratified 2026-07-19).

---

## 0. Step zero, unconditional: archive the reply before reading numbers out of it

Byte-preserving archive at `calibration/data/raw/oxborrow_<topic>_<date>/` exactly as the four existing Oxborrow/Cowley-Semple archives: `.eml` export + rendered `.md` + any attachments/photos, `MANIFEST.sha256` with the provenance comment block, LFS routing via the existing blanket rules, `-text` line-ending protection. Add the archive to `tests/test_calibration_integrity.py::TestRealArchive` (one new `test_oxborrow_<topic>_archive_intact`, the `wu_build_papers` pattern). While the R10a Gmail re-auth deferral stands, the same deferral discipline applies: if the `.eml` cannot be exported yet, archive the `.md` render now, record the deferral in the commit message, and do NOT let the missing `.eml` block resolution minting — the manifest is amended (dated errata block, Finding-1 precedent) when the `.eml` lands.

Every `SentinelResolution.provenance` string minted under this plan cites the archive path and quotes the discriminating sentence(s) verbatim.

---

## 1. Response-to-resolution mapping

### 1.1 Q13 — STO ring height fork

Payload contract (from `_REQUIRED_PAYLOAD_KEYS["Q13"]`, verified):

```
{
  "sto_height_m": <float, metres>,           # required
  "selection_evidence": <str>,               # required — WHICH discriminator landed
  "sto_height_band_m": (<lo>, <hi>),         # optional — caliper band; consumed by
}                                            #   materialise_dims in preference to
                                             #   the ±25 µm machining placeholder
```

Rung: `Rung.SUPERVISOR_CONFIRMED` for a written answer or a caliper value; `mock=False`. Registered in `cavity.sweep.resolutions.RATIFIED_RESOLUTIONS` — the only path; `provenance.STO_HEIGHT_FORK` itself is never edited (it is the print record and stays forked forever as history).

Case handling:

| Reply form | Resolution | Notes |
|---|---|---|
| **"Use 8.6" (or "use 8.5") in writing, no measurement** | FULL resolution. `sto_height_m` = the stated value; `selection_evidence` = "Oxborrow written reply <date> to the explicit 8.5-vs-8.6 question" + verbatim quote; no band key → the ±25 µm `TOL.machining_tol_m` placeholder band applies via `materialise_dims`. | Pre-registered symmetry: a written "8.5" resolves to 8.5 at exactly the same rung with exactly the same friction as "8.6". The fork's evidence-favoured flag creates zero pull on the resolution. |
| **Caliper measurement with finite precision** (e.g. "8.58 ± 0.02 mm") | FULL resolution. `sto_height_m` = the measured value — legal even if it is NEITHER print candidate (the validator does not enforce fork membership; verified in `dofs.py`); `sto_height_band_m` = measured ± the precision HE states. If he states a value but no precision, the band key is omitted and the machining placeholder applies, with the missing-precision noted in `selection_evidence` and a one-line follow-up queued (not blocking). | Never substitute a caliper-class precision of our own invention for his unstated one. An off-candidate measurement supersedes both prints; both prints stay recorded on `STO_HEIGHT_FORK.candidate_sources` unchanged. |
| **He restates published geometry without engaging the fork** (the 2026-07-17 archived email already contains a written "8.6 mm height" — but as a summary of the SM/papers, sent BEFORE the explicit fork question of 2026-07-18) | **RULED — D1, user-ratified 2026-07-20:** an EXPLICITLY RESPONSIVE written answer from Oxborrow suffices — any reply that engages the 8.5-vs-8.6 question and states a height resolves Q13 at SUPERVISOR_CONFIRMED (written), with or without a measurement claim; `selection_evidence` quotes the responsive sentence and notes it is a written selection, not a measurement. A question-UNAWARE restatement (the 2026-07-17 email is the standing example) remains NON-resolving: it lands as a dated rung annotation on the fork record only. The responsiveness judgment is recorded in the provenance string (which sentence, responding to which question). | |
| **No height content** | Q13 stays open; the incomplete-reply branch (§5) applies. | |

### 1.2 Q2 — tuning piston: internal cavity height and usable travel

Payload contract (verified): `{"p_tune_nominal", "p_tune_min", "p_tune_max", "mechanism"}`, all metres for the three numerics; `p_tune` semantics = **box internal height (piston position)**, fixed 2026-07-18. Optional rider key: `"piston_gap_depth_m"` (the extra-key pattern the validator permits, RESOLUTION_Q11 precedent).

**Unit/parameterisation conversions.** Mark may answer in any of three coordinate systems. Conversion rules, fixed here in advance so no arithmetic is improvised on the day:

1. **Internal height directly** ("the cavity inside is H mm; ceiling screws from H_lo to H_hi"): identity map, `p_tune_* = H_* × 1e-3`.
2. **Plate-to-STO gap g** (his historical habit — the 2026-07-16 email's "5–10 mm" and the 2026-07-17 email's "6.4 mm" are both gap-form): `p_tune = deck_clearance_m + sto_height + g` = `3.0e-3 + h_Q13 + g`. **This conversion is Q13-coupled: it is FORBIDDEN while Q13 is unresolved** (the fork refuses arithmetic by design — `ForkedConstant.__float__` raises). If the reply gives gap-form travel but not the height, the Q2 resolution is minted only AFTER Q13 resolves, with the derivation `p = 3.0 mm + h(Q13) + g` recorded verbatim in the provenance string. No per-branch pre-computation.
3. **Screw turns / thread pitch**: convert only if he states the pitch; otherwise treat as partial (mechanism colour, no travel).

**Known-conflict handling (pre-registered; RATIFIED as D3, 2026-07-20).** The archived 2026-07-17 written email states internal height ≈ **18 mm** ("18 mm heigh, 28 mm in ID", implying gap 18 − 8.6 − 3 = 6.4 mm), while the print record is **~15 mm as-operated** (Wu 2020 Fig. 6 caption; PRL SM "~15 mm") — the value pinned as `GEOM_WU_STO_RING.box_internal_height_asoperated_m`. If the reply confirms 18 mm (or any non-15 value): do NOT silently average, replace, or discard. The print stays the as-published record with its dated docstring; the reply's value enters the Q2 payload as `p_tune_nominal` at the supervisor-written rung with the discrepancy stated in the provenance string; a dated annotation lands on `box_internal_height_asoperated_m` noting that the current bench nominal differs from the as-published sim height (same-build-different-epoch is physically plausible — the ceiling is a screw). W2 consequence in §4.1. Users of the 15 mm fallback constant (`draw_solve_spec` callers, d7 tests) are enumerated in §6 and re-pointed in the same changeset, dated.

Case handling:

| Reply form | Resolution status |
|---|---|
| Nominal + both travel ends (any parameterisation above, Q13 available where needed) | **FULL** — mint `RESOLUTION_Q2`; `mechanism` string cites the already-known written + print mechanism (screw-suspended ceiling / 26-mm piston on brass screw) rather than restating it as new information. |
| Gap-form travel while Q13 open | **DEFERRED-FULL** — payload assembly blocked on Q13; recorded as "answered, awaiting Q13 arithmetic"; no number minted. |
| "Typical 5–10 mm" style without commitment to THIS build, or one end only ("can screw the ceiling higher" with no upper stop) | **PARTIAL** — sentinel stays. Upgrade what upgraded: dated annotation on `SENTINEL_Q2.description`/`routes_to`; the defined end may be recorded as a rung-annotated bound. A follow-up email goes out with a CONCRETE proposal for him to confirm or correct (e.g. "shall I take usable travel as gap 5–10 mm on the current build?") — we propose, he ratifies; we never adopt a travel band he did not confirm. **Escape hatch ARMED — D2, user-ratified 2026-07-20:** if the concrete-proposal follow-up goes unanswered, mint `RESOLUTION_Q2` at `Rung.PLANNING_ASSUMPTION` (`mock=False`) whose provenance string preserves VERBATIM (i) the exact proposal sent (the proposed band and its reading), (ii) the follow-up date(s) and archive path(s), and (iii) the recorded absence of a reply as of the mint date, with elapsed time stated. The payload band = the proposed band under the D5 uniform reading. The moment he later answers, the resolution is superseded in place by a SUPERVISOR_CONFIRMED replacement with a dated supersession note — never edited silently. |
| Piston-gap depth stated | Rider key `piston_gap_depth_m` on the Q2 payload + the §6 wiring change (the depth currently has NO consumer in `draw_solve_spec` — hidden coupling H1). |
| Piston-gap depth NOT stated | The recess stays unmodelled in the training geometry (flat ceiling — which is also what Wu's own Fig. 6 sim draws, so the W2 nominal is unaffected); the queued piston-gap sensitivity solve (SPEC re-base outcome 9) stays queued behind a depth number or a user-ratified planning depth. Never a silent default depth. |

### 1.3 Q9 — crystal placement (+ the crystal-dims ask, which is NOT Q9)

Payload contract (verified): `{"crystal_axial_offset_nominal_m", "crystal_axial_offset_band_m", "centring_tolerance_m"}` — all three required; the validator refuses a partial payload, so **Q9 mints only when all three exist**.

Two deliberate scope notes first:

- **Crystal DIMENSIONS are not in the Q9 payload.** A dims answer routes to provenance (§1.4), not to this sentinel. Verified: `SENTINEL_Q9.description` says so explicitly.
- **Coordinate-wording debt:** the Q9 docstrings still say "torus equatorial plane" (Booth-era). For the Wu build the same coordinate is the RING mid-height plane. The resolution changeset updates the wording (docstring/comment only, dated; no physics change).

Case handling:

| Reply form | Resolution status |
|---|---|
| Axial nominal + axial band + achievable centring tolerance (numbers for all three) | **FULL** — mint `RESOLUTION_Q9` at SUPERVISOR_CONFIRMED (written). |
| "Nominally centred / roughly mid-height, hand-placed" with NO tolerance | **PARTIAL** — mirror of the 2026-07-16 eccentricity partial: rung upgrades and nominal pins where stated (axial nominal 0 at written rung, via dated annotation on the DofSpec provenance, exactly as `crystal_eccentricity_m.nominal_rung` was upgraded), **no resolution minted**, all refusals stand. Follow-up with a concrete proposal ("hand placement — is ±0.5 mm axial a fair band? what centring slack does the bore give over the crystal diameter?"). The geometric containment bound |offset| ≤ (box_height − crystal_height)/2 and the annular clearance (bore radius − crystal radius) are legal to STATE as bounds in the follow-up — they are derived constraints, not sampling bands, and must not be minted as bands themselves. |
| "Approximate" placement with a stated slack ("give or take a millimetre") | **FULL** if the slack covers both the axial band and the centring tolerance readings, with the informal wording quoted and the reading fixed by the ratified convention (D5, 2026-07-20): **informal slack is read as the UNIFORM band** — recorded as a planning-tier reading layered on a written number, the same convention at every site. If the slack plausibly covers only one of the two coordinates, mint nothing; ask which. |
| Nothing on placement | Q9 open; §5. |

**Post-resolution obligation (hidden coupling H2):** `centring_tolerance_m` is validated but consumed by no computation at HEAD (verified by repo-wide grep — the eccentricity row is excluded from sweep dims). Minting Q9 makes the §7.4 decision-ladder FIRST-ORDER ECCENTRICITY ESTIMATE due BEFORE the main sweep (design-doc commitment). The Q9 changeset must schedule it explicitly so the tolerance number does not sit payload-complete but work-orphaned.

### 1.4 Crystal dimensions (cross-build-transfer flag) — provenance change, not a sentinel

If Mark answers on the Wu-build crystal (expected forms: "~4 mm diameter, didn't entirely fill the bore", "grown in the 4 mm PTFE mold", a caliper, or "we still have it, it's X × Y"):

- Lands as a re-grade of `GEOM_WU_STO_RING.crystal_diameter_m` / `crystal_height_m` from PLANNING-ASSUMPTION (Breeze import) to supervisor-written / measured, with the cross-build-transfer flag CLOSED (dated), or as a new graded constant if he distinguishes the current crystal from the Wu-2021 one.
- "Slotted snugly … did not entirely fill it" reads as diameter < 4.05 mm: record nominal + bound ("< bore I.D.") + any stated number; never pin exactly 4.0 from the SM round.
- **Zotero finding to carry into the ask/ingestion (new, this pass):** "the Wu crystal" is not one object across the two papers — Wu 2020's crystal is a lollipop grown AROUND the embedded Ce:YAG wedge (PTFE mold 4 mm × 8 mm), while the PRL-127 crystal is dye-laser-pumped through a wall hole with no LC mentioned. If the current build's crystal contains an embedded YAG wedge, the homogeneous-crystal assumption in Phase 1b EM (Q11 εr = 3.0 uniform) and in the thermal S-ladder gains a stated composite-body flag. One clarifying line in the follow-up email; if unanswered, the flag is recorded at planning tier, homogeneous stays the modelled branch.
- Ripples (enumerated in §6): Phase 1b geometry build, W2 preconditions (crystal present), `thermal/report_s_ladder` modelled-body note, broadening/detuning probe geometry docstrings. NOT Layer A DOF rows (crystal dims are not DOFs) and NOT calibration (rig side is disjoint).

### 1.5 What fully vs partially resolves — one-line summary

FULL: Q13 = one height (question-aware or measured); Q2 = nominal + both travel ends in any convertible parameterisation; Q9 = all three payload numbers. Everything else is PARTIAL: rung annotations and follow-ups only, refusals intact, no invented completions.

---

## 2. Prohibition — the evidence-favoured branch is never silently selected

Standing rule, restated as a gate on this plan's changesets: **no changeset under this plan may read `STO_HEIGHT_FORK.evidence_favoured` (or `SENTINEL_Q13.evidence_favoured`) into any non-mock value, default, fallback, doc nominal, or test expectation.** The one sanctioned machine read remains `mock_resolutions()` (labelled, refused by every solve-ready exit). Concretely: if Mark's reply resolves Q2 and Q9 but NOT Q13, the temptation to run W2 "on 8.6 since it's favoured anyway" is refused — W2's own ratified precondition ("Q13 must be resolved (no silent height selection) before the W2 solve") is binding. CI enforcement already exists (`test_forked_constant_refuses_float_coercion`, `test_sto_height_row_is_q13_fork_trace`); the changeset adds a grep-style negative check in review notes, not new machinery.

---

## 3. Exact artifacts that change per resolution

**No file below changes in this planning task.** These are the changesets that execute when the reply lands, each additive-or-dated per repo discipline.

**Every resolution (shared):**
- `calibration/data/raw/oxborrow_<topic>_<date>/` + `MANIFEST.sha256` (new, §0)
- `tests/test_calibration_integrity.py` (+1 archive-intact test)
- `src/cavity/sweep/resolutions.py` — `RESOLUTION_Q13` / `RESOLUTION_Q2` / `RESOLUTION_Q9` appended to `RATIFIED_RESOLUTIONS` (question order preserved)
- `src/cavity/sweep/dofs.py` — dated pointer appended to the resolved sentinel's `routes_to` (the Q11 precedent); NO structural edits to `_REQUIRED_PAYLOAD_KEYS` or `SOLVE_GATE_QUESTIONS`
- `SPEC.md` — §11 items 12 (Q13) / 13 (Q2) / Q9's standing entries get dated status blocks; newest-last revision block
- `docs/plans/layer_a_sweep_design.md` — dated addendum (row 4 / row 9 / row 5 status)
- `tests/test_sweep_resolutions.py` — new pin tests per resolution (payload values, rung, non-mock, provenance-cites-archive) **and deliberate re-scope of the refusal-shape tests**: `test_ratified_context_resolves_q11_while_q2_q9_q13_remain` and `test_solve_ready_exits_still_refuse_naming_q2_q9_q13` assert the exact current refusal set and will fail on any resolution — each changeset re-scopes them to the then-current unresolved set, with the collection-count delta declared in the commit message (the repo's standing discipline). Zero silent test edits.

**Q13 additionally:** nothing else at rest — `materialise_dims` and the D7/D8 gates consume the payload with no code change (verified). If a caliper band arrives, no code change either (`sto_height_band_m` branch already implemented).

**Q2 additionally:**
- `src/cavity/sweep/backend.py` — IF a gap depth arrives: wire `piston_radius_m` (= `GEOM_WU_STO_RING.piston_radius_m`) + `piston_gap_depth_m` into the `CavityGeometry` built by `draw_solve_spec` (hidden coupling H1: the geometry engine supports the jointly-present piston fields — verified in `forward_model/geometry.py` — but `draw_solve_spec` does not populate them today), behind an explicit `include_piston_step` flag defaulting to the ratified stance, + tests in `test_sweep_backend.py`.
- If internal-height nominal ≠ 15 mm: dated annotation on `GEOM_WU_STO_RING.box_internal_height_asoperated_m`; audit + re-point of `box_height_fallback_m` call sites and the tests that pass the 15 mm fallback (`test_box_height_fallback_required_without_p_tune` and the d7/dry-run fixtures), each edit dated.
- `tests/test_sweep_design.py` / `test_sweep_backend.py` — d8 materialisation on the REAL Q2 payload (new tests), mock-refusal tests untouched.

**Q9 additionally:**
- Docstring wording updates torus→ring plane (`dofs.py` SENTINEL_Q9 + `crystal_axial_offset_m` row provenance), dated.
- Schedule entry for the eccentricity first-order estimate (H2) in the changeset's plan-of-record.

**Crystal dims (if answered):** `provenance/constants.py` (`GEOM_WU_STO_RING.crystal_*` re-grade or new constant, dated; cross-build flag closure), `tests/test_provenance_wu_geometry.py` (+pins), SPEC §5b dated note, `thermal` report/module docstring notes where the 3 × 8 planning dims are named (`report_s_ladder`, `cylinder` docstrings — dated annotations, numbers regenerated only via generators).

**Generated artifacts likely to change (always via their generators, never hand-edited):** none at Q13/Q2/Q9 resolution itself; `thermal/reports/s_ladder_ballpark.md` only if crystal dims change AND the ladder is deliberately regenerated (its content pin `tests/test_thermal_s_ladder.py` is updated in the same commit, delta declared); margin/turnover reports unchanged (no κ or Q inputs move here).

---

## 4. The first W2 Wu-anchor solve (after the blockers close)

Preconditions (from the ratified `docs/w2_wu_anchor_windows.md`, restated): **Q13 resolved** (hard); crystal sub-domain present at the Q11 planning εr = 3.0; spacer flag ON; **a COMSOL licence session** (nothing here runs in CI); Phase 1b geometry engine able to represent the crystal-in-bore (the SPEC §5b build — see §4.5 sequencing: the crystal engine work is itself a prerequisite pass). Q2 is NOT a precondition (the W2 doc does not require it), but §4.1 fixes what height the solve uses.

### 4.1 Geometry / material branch
- `DielectricShape.RING` at `GEOM_WU_STO_RING` nominals; `sto_height_m` = the Q13-resolved value.
- Box internal height: the recorded as-operated nominal — **15 mm if the reply does not revise it; the reply-sourced value at the written rung if it does** (D3, user-ratified 2026-07-20: the reply value BECOMES the modelled W2 nominal; 15 mm is never averaged with it or silently replaced — it stays the print record, and the choice is recorded in the run's meta either way). Flat ceiling (no piston step): this matches Wu's own Fig. 6 simulation region (14 mm × 15 mm, flat), so the anchor comparison is like-for-like; the piston-step recess is the queued post-Q2 sensitivity solve, not part of the anchor nominal.
- Materials: CANONICAL branch (εr 316.3, tanδ 1.1e-4, Cu 6.0e7), impedance walls; PEC companion arm for the wall split.
- Spacer: ON, `CLPS` εr 2.53, figure-derived seat dims; the with/without-spacer delta solve is the queued companion (same session if budget allows).
- Crystal: present, planning dims (or Mark-revised dims if landed), εr 3.0 (Q11), placed per Q9 nominal if resolved, else axially centred AT A LABELLED PLANNING PLACEMENT recorded in meta (placement is not a W2 gate row; the sensitivity rides Q9).

### 4.2 Required output fields
`f_real_hz`, `Q0` (impedance arm), `Q_diel` + wall fraction (PEC pairing), `p_e`, `v_mode_global_m3`, `v_mode_local_m3` (gain-region max), the local/global ratio, spacer on/off delta (companion), solve fingerprint + SCHEMA_VERSION 2 fields, mesh level + element count, git commit + dirty flag — i.e. a `run_5a`-class record, not a bare number.

### 4.3 Acceptance windows (as ratified 2026-07-19 — restated, not re-derived)
- W2.1 f = 1.4495 GHz ± 1.5 % — GATE; residual sign recorded; a residual reachable inside εr [312, 318] is non-alarming and must be stated with the εr sensitivity.
- W2.2 Q0 = 7200 ± 25 % — GATE (deliberately loose: the tanδ band alone spans ~±17 %). **A W2.2 pass re-grades nothing about tanδ** — the window is an anchor check, not a loss measurement.
- W2.3 v_mode_local vs 0.32 cm³ — REPORT ONLY (convention inferred, the 225/360 lesson).
- W2.4 v_mode_local / v_mode_global ≈ 1 within 10 % — GATE (build-specific consistency; fails indict the gain mask or field solution BEFORE any 0.32 cm³ comparison is meaningful).

### 4.4 Record / archive structure and failure triage
- Archive: `refs/gate_runs/<UTC>_wu_anchor_w2/` in the established shape — `gate_report.json`, per-solve `solves/<hash>/{fields.npz, meta.json}`, `checkpoint_manifest.json`, a human `wu_anchor_w2.md` judged strictly by the committed windows. First PASSING record becomes "the Wu anchor record" and creates the Wu-build sweep-centre record (design-doc 2026-07-19 addendum). Byte-immutable thereafter.
- **Runner path:** a `run_5a`-style validation runner (new `cavity.validation.run_w2` or an extension), driving `forward_model` directly. It must NOT be threaded through `sweep.ComsolBackend` and must NOT weaken or special-case `assert_solveable` — the sweep gate's refusal set is untouched by W2 (hidden coupling H3: the sweep gate covers training solves; W2 is a validation solve with its own precondition list, and the two gates must never be merged or cross-wired).
- Failure triage, pre-registered (§5a discipline: the red result is the committed finding; no geometry retuning, no tolerance widening, no branch re-picking in the failing session):
  - W2.1 fail beyond εr-band reach → suspects in order: Q13 height as-resolved (re-check the resolution payload against the archive, not the physics), enclosure radius (the 28-mm-nominal fitting caveat), internal height branch (15 vs reply value — solve the OTHER branch as a diagnostic companion, labelled), mesh convergence.
  - W2.2 fail → loss split diagnostics (Q_diel, wall fraction) before any tanδ discussion; spacer-off companion delta.
  - W2.4 fail → gain-mask/field-solution audit; W2.3 comparison is declared meaningless for that record.
  - Any fail → archived failure record, `phase1_complete` untouched, no gate row binds `wu_ring`, findings note to Oxborrow if the discrepancy implicates the build description.

### 4.5 Transition out of the W2 anchor
1. **Phase 1b verification block** (the budgeted 5-solve block, `centre_verification_specs`: on/off × finest/coarser + PEC arm) — now against the WU centre definition ("the Wu Phase 1b model whose no-crystal limit reproduces the W2-validated Wu anchor"). Sequencing note: building the crystal sub-domain in the geometry engine is SPEC §5b work and is a prerequisite of both W2 (crystal present) and this block — one licensed engine-building pass, then W2, then the block, in that order. The Booth `PINNED_CENTRE` in `centre_check` remains Booth's record; the module's "off-arm vs pinned" wiring is re-pointed to the Wu anchor record in a dated changeset (hidden coupling H4: the current `meaning` strings and `read_gate_record_values` are Booth-record-shaped).
2. **W1 ratification is now due** (queued "with Q9 + Q11" — both then resolved): commit the numeric weak-perturbation window, implement `judge_centre_verification`'s ratified-window branch, re-scope `test_report_judgment_is_unjudged_with_the_w1_sentinel` deliberately.
3. **Layer A training campaign:** design freeze per the design doc; budget 209/300 (d8) with the pre-committed cut order; Q8 CV thresholds at the Wu operating point (f LOO RMSE ≤ ~40 kHz; |δΔf_max| ≤ 5 % of the 5th-percentile Δf_max); raw/derived boundary and law-agnostic rows as built.
4. **d = 8 baseline vs d = 7 fallback — decision rule, fixed now:** d8 iff `RESOLUTION_Q2` is minted (full travel) at campaign start; else d7 with `box_height_fallback_m` = the then-current recorded nominal (15 mm or Mark-revised) passed EXPLICITLY, and the campaign's report carries the REQUIRED-PLATE-AUTHORITY deliverable (population f-scatter → travel the plate must supply) so the d7 run itself sharpens the Q2 follow-up. A Q2 resolution arriving mid-campaign does not retrofit solved rows: the (θ, p) joint design is a follow-on block, per the design doc.

---

## 5. Incomplete-reply branch — what stays legal without fabricating numbers

If the reply answers some/none of Q13/Q2/Q9:

Legal immediately: archive + manifest + integrity test (§0); dated rung annotations on sentinels/DofSpecs for anything he DID state; SPEC §11 dated status lines; the follow-up email (concrete proposals, us-propose-he-ratifies); test-re-scope PREP (branch/patch drafted, not merged); the Q2 gap-form arithmetic recorded symbolically pending Q13; W2 runner scaffolding as zero-licence code (the runner can be written and mock-tested — its licence gate and preconditions keep it inert); Phase 1b engine work per its own plan (Q1 ruling: implementation may proceed, solves stay gated).

Illegal without the answer: minting any of the three resolutions with partial payloads (the validator refuses anyway); adopting the evidence-favoured 8.6; adopting a travel band, axial band, centring tolerance, caliper precision, or piston-gap depth we chose; running W2; emitting any solve-ready row; and re-scoping the refusal tests ahead of an actual resolution.

---

## 6. Hidden couplings the executor must account for (from the sentinel-path trace)

H1 `draw_solve_spec` builds RING geometry WITHOUT piston fields today — Q2's gap-depth rider needs a wiring change, not just a payload.
H2 `centring_tolerance_m` has no consumer — Q9 resolution triggers the due-before-sweep eccentricity first-order estimate.
H3 W2 runs outside the sweep gate — never through `ComsolBackend`, never weakening `assert_solveable`.
H4 `centre_check` pinned record + meaning strings are Booth-shaped — Wu-centre re-pointing is its own dated change.
H5 The refusal-asserting tests (`test_solve_ready_exits_still_refuse_naming_q2_q9_q13`, `test_ratified_context_resolves_q11_while_q2_q9_q13_remain`, backend/centre-check refusal tests) fail BY DESIGN on each resolution — each changeset re-scopes them with declared collection deltas.
H6 Gap-form Q2 arithmetic is Q13-coupled (fork refuses floats) — ordering constraint on minting.
H7 The 15 mm as-operated constant has call sites (d7 fallback, tests, docs) that must be audited if the reply revises the height.
H8 Q9 docstrings carry Booth "torus" wording — update with the resolution, dated.

## 7. Acceptance criteria and tests, per stage

- **Ingestion changeset(s):** archive verifies via `calibration.integrity` (CI); new resolution pin tests green; refusal tests re-scoped with declared collection delta; repo-wide grep shows no non-mock read of `evidence_favoured`; suite green at the declared count; no numeric constant changed except reply-sourced payload values at their stated rungs.
- **W2 session:** record archived in the §4.4 shape; verdict = the committed windows verbatim; on pass, the Wu anchor + sweep-centre records exist and `wu_ring` gains its first bound gate row in a follow-up zero-licence changeset; on fail, failure record archived and nothing else moves.
- **Phase 1b verification:** 5-solve block archived; deltas reported; judgment only after W1 ratifies; `phase1_complete` moves only per the SPEC §5 gate, never here.
- **Layer A start:** design freeze doc dated; first training block emitted only through `solve_rows` on the ratified (non-mock) context; d7-vs-d8 decision recorded with its rule (§4.5.4).

## 8. Explicitly out of this plan
No COMSOL solve in the planning task; no physics-number changes; no edits to archived records; no κs/tanδ/εr re-grades (Plan B territory or ratification items); no gate-row binding of `wu_ring` before a W2 pass.
