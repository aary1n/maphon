# PROMPT — PLAN CHECKPOINT ONLY

Do not edit any file. Produce the plan below, then STOP and wait for ratification.

**Scope:** provenance pass archiving and minting the **2026-07-23 Oxborrow "standard resonator" email** (to Vanessa Ussalim, thread cc Randall Carrera / Liu / Sharif; attachments: COMSOL `.mph`, two H-field CSV grids, one field-plot image/pdf; thread root = the 2026-07-17 H(r) filling-factor request emails). Fourth provenance pass in this lineage (RESOLUTION_Q11 → 2026-07-16 docstring pass → the 2026-07-21 meeting mint + its 2026-07-22 errata). This pass mints **ZERO sentinel resolutions** — nothing resolves; it is an archive-plus-annotation pass: written-corroboration annotations at correctly restricted scope, one new-anchor-candidate record, and a re-scoped confirmation-email ask list. Evidence source for every item is the archived email + attachments (A0) — every annotation cites that archive path, never memory and never this prompt.

**Email facts of record (verified from the email — state them in annotations from the A0 archive, not from here):** Oxborrow, WRITTEN, 2026-07-23, "written without AI": the "standard" resonator "whose dimensions we defined yesterday with Aaryan" [DATING DISCREPANCY, recorded not harmonised: the email's "yesterday" would imply 2026-07-22, but the repo author's first-hand account (2026-07-23) is that NO meeting has occurred since 2026-07-21 — the referenced definition session is therefore identified as the 2026-07-21 meeting on the first-hand account, and the email's "yesterday" is carried verbatim as an inaccuracy in the source, the two statements recorded side by side]; STO ring **12.2 mm O.D. / 4 mm I.D. / 8.6 mm high**; copper cavity **28 mm inner diameter, 15 mm high**; ring resting on a **plastic support 3 mm** above the cavity floor; **f = 1.41 GHz for this geometry** (plot header: `lambda(1)=1.4128E9`); "Would have to lower the ceiling to squeeze the frequency upwards"; "Can easily change the dimensions"; dielectric ring, air, and support all non-magnetic (B = μ₀H); H supplied as Hrad/Haxi on 20×20 and 100×100 (r, z) grids; purpose = Vanessa's filling-factor comparison across crystal dimensions.

**Hard scope guards:**
- No physics or logic changes. NO numeric changes anywhere. No new `SentinelResolution` objects; `RATIFIED_RESOLUTIONS` stays `(RESOLUTION_Q2, RESOLUTION_Q11, RESOLUTION_Q13)`.
- **Q9 stays UNRESOLVED and untouched** — the email contains no crystal at all; every solve-ready exit still refuses naming Q9. State this as a verified non-event, do not edit Q9 machinery.
- **No carried value moves.** `GEOM_WU_STO_RING.sto_outer_radius_m` stays the 12.0 mm print at its rung; the O.D. treatment-(i) record stands; `STO_HEIGHT_FORK` stays the fork-object record; `sto_inner_radius_m` stays 2.025e-3; no branch of the 12.0-vs-12.2 discrepancy is selected by this pass.
- **The Wu-anchor machinery is byte-untouched:** `docs/w2_wu_anchor_windows.md` including the 2026-07-22 dual-geometry addendum, all W2 windows, `TARGETS.wu_ring`, and the pre-registered triage. Any use of the email's 1.41 GHz in W2 triage is informational annotation elsewhere (A3), never an edit to the protocol. If the standard-build arm is ever to join the licence session, that is a FUTURE dated addendum requiring its own ratification — this pass only names it, it does not write it.
- **No solves, no window drafting, no gate rows** for the new anchor candidate (A3): windows-before-solve is the W2 precedent; this pass records the candidate and names the ratification item, nothing more.
- No CSV ingestion, no `.mph` parsing, no field-export-schema work this pass — enumerated as named follow-ons only (A4/A5).
- `KAPPA_S`, the two-linewidth law, and its UNRATIFIED status untouched. `C0_PLANNING` untouched — the email says nothing about C₀; its written-confirmation ask stays open unchanged.
- The `Rung` enum is untouched (no written member exists; the finer truth rides provenance strings, the Q9-partial / 2026-07-22-errata precedent).
- Archived directories are byte-immutable, including `calibration/data/raw/oxborrow_meeting_notes_2026-07-21/` and its MANIFEST.
- No opportunistic refactors, no test deletions, no tolerance changes.

**Known machinery facts (verified against `main` — use these, do not rediscover them wrong):**
- The "written confirmation from Oxborrow pending — rides the confirmation email" caveat currently lives in (at least): `src/cavity/sweep/resolutions.py` (module docstring, `RESOLUTION_Q2`, `RESOLUTION_Q13`, `ratified_resolutions()`), `src/cavity/provenance/constants.py` (`STO_HEIGHT_FORK` docstring, `WuSTORingGeometry` docstring O.D./height/height-fork/internal-height lines, `PlanningCooperativity`), `src/cavity/sweep/dofs.py` (sentinel descriptions, DOF row-2 provenance), and `docs/commit_errata_2026-07-22.md`. Enumerate the exact set at plan time.
- The ring-identity claim (measured/defined ring == the Wu 2020 build's ring) is graded SEPARATELY from measurement provenance and is Oxborrow-VERBAL — `STO_HEIGHT_FORK` docstring and the 2026-07-22 errata are the wording precedents.
- Archive precedent: `calibration/data/raw/<source>_<date>/` + `MANIFEST.sha256` (2026-07-16 notes, 2026-07-17 geometry email, 2026-07-21 meeting notes). The 2026-07-17 geometry-email archive (`oxborrow_geometry_2026-07-17/`) had a DEFERRED-pending-.eml-export note (R10a) — reuse that convention if the .eml export is not immediately available.
- The confirmation-email line-item list of record is the 2026-07-21 mint's plan-requirement-8 set: (i) ring height 8.6 mm, (ii) O.D. 12.2-vs-12.0 + band ask, (iii) travel band [15, 25] mm, (iv) C₀ = 200; plus the standing riders (piston gap depth; caliper band; spacer dims).
- `BOOTH_TABLE8_REVOLUTION_FACTOR`'s docstring records the .mph-as-readable-zip inspection precedent (`dmodel.xml`).

---

## A0 — Archive the email + attachments (step zero; everything cites it)

Create `calibration/data/raw/oxborrow_standard_resonator_2026-07-23/` containing: the .eml export of the 2026-07-23 email (with the full 2026-07-17 thread beneath it), the `.mph` file, both H-field CSVs (20×20 and 100×100), and the field-plot image/pdf, under a `MANIFEST.sha256`. If the .eml export is not yet in hand, the R10a deferred-archive convention applies (manifest README records the outstanding attach; the CSV/.mph files archive now if available).

Grade for all email content: **Oxborrow-WRITTEN (2026-07-23), archived.** The manifest README additionally records: (a) the email's addressee and purpose (Vanessa's filling-factor calculation — third-party context, not a reply to any maphon ask); (b) the **dating discrepancy**: the email's "defined yesterday" implies 2026-07-22, but per the repo author's first-hand account (2026-07-23) no meeting has occurred since 2026-07-21 — the referenced definition session is identified as the **2026-07-21 meeting** (the same session as the archived caliper measurements, `calibration/data/raw/oxborrow_meeting_notes_2026-07-21/`), the email's wording is preserved verbatim, and the identification's basis (first-hand account, not the email) is stated. NO separate meeting record exists or is invented.

## A1 — Written-corroboration annotations, scope-restricted (the main event)

The email is Oxborrow's written statement of **12.2 O.D. / 8.6 height / 15 mm internal height / 3 mm clearance / 28 mm enclosure I.D.** — the numbers whose written confirmation every 2026-07-21 record is waiting on. But the statement's SCOPE is the standard resonator defined at the 2026-07-21 meeting (per the first-hand identification in A0; the email's "yesterday" discrepancy rides that record), and it asserts nothing about the Wu 2020 build. Plan BOTH candidate treatments and recommend one with reasoning:

  (i) **Written-corroboration annotation, dated, at each caveat site** (recommended starting position): each "written confirmation pending" location gains a dated line — *2026-07-23, Oxborrow-WRITTEN (archive path): the standard-resonator email states <value> for the ring/cavity in question; corroborates the 2026-07-21 measured value IN THE STANDARD-RESONATOR CONTEXT; the ring-identity claim (that this ring is the Wu 2020 build's ring) remains Oxborrow-VERBAL and is NOT addressed by the email; the confirmation-email ask NARROWS (identity + caliper band) but does not close.* No rung changes, no caveat deletions.
  (ii) Full discharge of the written-pending caveat on the measurement values (identity claim still excluded), treating the coincidence of all five numbers as sufficient.

The recommendation must weigh: (ii) silently imports the identity assumption the repo has spent two passes keeping separate; (i) costs one extra ask line and loses nothing; AND the same-session identification (A0 — the definition session IS the caliper session, per first-hand account) strengthens (ii)'s case for the measurement VALUES specifically, since the written dims most naturally restate that session's measurements — but even so, the email still never asserts the ring is the Wu 2020 build's ring, so the identity claim survives either treatment at its verbal grade. Whichever treatment: the 2026-07-21 archive's MANIFEST and the 2026-07-22 errata are byte-immutable — annotations land only at the living docstring/description sites (enumerate them per the known-facts list, completed at plan time).

Two item-specific notes:
- **Q2:** the email corroborates the 15 mm internal height and — in writing — the tuning MECHANISM AND DIRECTION ("lower the ceiling to squeeze the frequency upwards"). It does NOT restate the [15, 25] band endpoints; the annotation must say exactly that (nominal + mechanism written-corroborated; band endpoints still caliper-only). The gap-depth rider stays open.
- **Deck clearance / support:** 3 mm and "plastic" corroborate `deck_clearance_m` and the CLPS support class at the generic-"plastic" level only — no material upgrade (Polypenco/Rexolite identity untouched).

## A1b — I.D. print variance: 4 mm written vs 4.05 mm carried — record, do not harmonise

The email prints "4 mm inner diameter" against the carried Wu 2020 print 4.05 mm (`sto_inner_radius_m = 2.025e-3`) — and against the dual-geometry protocol's fixed 4.05. The repo already treats the PRL SM's "4-mm bore" as a ROUND of 4.05, and this is most plausibly the same round — but it is now a fresh written print at variance with the carried value, and for the STANDARD resonator it may simply be the design value. Record it as a dated annotation on the `sto_inner_radius_m` provenance (round-of-4.05 stated as the likely reading, SPECULATION-tagged; a genuinely 4.00 mm standard-build I.D. listed as the alternative), and add the one-line disambiguation ask to the confirmation email (A6). No fork, no sentinel, no value change — the Layer-A-deferred low-cost logic of the 2026-07-21 A1b treatment-(i) applies a fortiori.

## A2 — Standard-build geometry record: propose the home, do not scatter

The email fully specifies a NEW build (the lab's going-forward "standard" resonator) that is not the Wu build and not the Booth torus. Propose exactly ONE home for it and recommend: (i) a new frozen dataclass in `provenance/constants.py` (e.g. `StandardResonatorGeometry` / `GEOM_STD_RING`), fields verbatim from the email at WRITTEN grade, with an explicit NOT-A-MODELLED-GEOMETRY guard (no DOF rows, no solve consumes it, the modelled build stays `GEOM_WU_STO_RING`); or (ii) a docs-level record only (e.g. a section in the A0 manifest README), deferring any constant until something consumes it. The recommendation must weigh the repo's "single source of truth" rule against its "no constant without a consumer" hygiene. Whichever home: the crystal is ABSENT from this build's record (none is stated), and the 12.2/4/8.6 values cite the email, never the 2026-07-21 notes.

## A3 — New anchor CANDIDATE: Oxborrow's own COMSOL f = 1.4128 GHz — recorded, no windows, no gate

Record (home: the A2 geometry record's docstring plus a line in `docs/w2_wu_anchor_windows.md`'s vicinity ONLY if a dated-addendum note is ratified — otherwise the A2 home alone): Oxborrow's own COMSOL solve of the standard-resonator geometry yields **f = 1.4128 GHz** (email prose "actually 1.41 GHz"; plot header 1.4128E9), model file in hand (A0 archive). Grade: SUPERVISOR-WRITTEN MODEL OUTPUT — not a published print, not a measurement.

- Name the future ratification item (**W4**, or the next free W-number — check for collisions): acceptance windows for a maphon reproduction of the standard-build solve, to be drafted BEFORE any solve, W2-style. NOT drafted this pass.
- Informational annotation, speculation-tagged, wherever the plan judges it belongs (candidate: the A2 docstring): at the SAME 15 mm ceiling, Oxborrow's 12.2-O.D. standard-build model sits ~2.5% below Wu's printed 1.4495 GHz — outside the W2.1 ±1.5% window class — and his ceiling sentence states the tuning direction in writing. Consistent with the dual-geometry protocol's Run-A/Run-B question; SELECTS NOTHING; the protocol is untouched (differences from Run B — no crystal, support form, I.D. — listed beside it).
- Explicitly note what the email does NOT contain: any Q value (κc branches, `TARGETS.wu_ring`, MQ2 unaffected).

## A4 — .mph inspection: named follow-on, not this pass

Enumerate as a follow-on task (no execution here): licence-free readable-zip inspection of the archived `.mph` (`dmodel.xml`; the `BOOTH_TABLE8_REVOLUTION_FACTOR` precedent) to read out and mint at written-artifact grade: his STO εr and tanδ, wall treatment, crystal presence/absence, and the Revolution 2D angle settings (the 225/360 workflow-tradition question — C3b-adjacent). State the follow-on's name and its evidence value; touch nothing.

## A5 — H-field CSVs: named follow-ons, not this pass

Enumerate (no execution): (a) ingestion of the 100×100 grid through `docs/field_export_schema.md` as its first genuine-external-data exercise; (b) a v_mode_local/v_mode_global computation on the ingested grid via `extraction/modal.py` — an independent-data rehearsal of the W2.4 convention check (caveats stated in the enumeration: H-only, half-plane grid, 2πr weighting, coarse-grid resolution); (c) the cross-person consistency hook — Vanessa's filling-factor numbers vs maphon's extraction on the same CSV. Record in the A0 manifest README that these follow-ons exist; nothing else moves.

## A6 — Confirmation-email ask list, re-scoped

Update the ask list at its living homes (enumerate them; the 2026-07-21 plan-requirement-8 set is the baseline). After this pass the asks are: (i) **ring identity** — is the 12.2/8.6 standard ring the Wu 2020 build's ring (the one remaining load-bearing gap); (ii) caliper band (repeats/placement) for the 2026-07-21 readings; (iii) piston-step gap depth (standing rider); (iv) C₀ = 200 written confirmation (standing, untouched by this email); (v) I.D. 4.00-vs-4.05 disambiguation (A1b); (vi) NEW rider: an E-field export (or blessing to export from the archived .mph) for the E-energy-weighting assumption on `DF_CAVITY_DT` (currently "assumed ≈ 1", p_e = 0.9977). Items (i)/(ii)/(iii)/(iv) narrow or persist; nothing closes silently.

---

## Plan output requirements

1. The A1 treatment recommendation (i)-vs-(ii) with reasoning, and the COMPLETE enumeration of every "written confirmation pending" site with its proposed dated annotation string verbatim, per file.
2. The A2 home recommendation with reasoning; if (i), the exact class/instance names and field list verbatim.
3. The A3 record's exact wording verbatim, the chosen W-number with collision check, and confirmation that no window, gate row, or protocol edit rides this pass.
4. Per-file edit list across A0–A6, distinguishing new files (archive dir, manifest) from annotation-only edits.
5. Expected test impact: before/after counts verbatim. Expectation to confirm or refute at plan time: ZERO behavioural changes — docstring/description edits only; enumerate any pinned test that asserts docstring/description TEXT (the refusal messages interpolate sentinel descriptions — if any A1 annotation lands in a sentinel description, list the exact expected message shifts, else state that annotations deliberately avoid interpolated fields).
6. Confirmation, file by file, that the byte-immutable set is untouched: both prior archives + manifests, `docs/commit_errata_2026-07-2{0,2}.md`, `docs/w2_wu_anchor_windows.md` + addendum, all `refs/gate_runs/`, all pinned reports.
7. The A6 ask list verbatim as it will read after the pass, with its homes.
8. The named follow-on passes this plan creates but does not execute: the .mph inspection (A4), the CSV ingestion + convention rehearsal (A5), the W4 window-drafting ratification item (A3), and the possible standard-build licence-session arm (dated-addendum route, its own ratification).

Then STOP.
