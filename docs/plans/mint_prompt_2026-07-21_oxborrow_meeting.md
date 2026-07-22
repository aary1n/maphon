# PROMPT — PLAN CHECKPOINT ONLY

Do not edit any file. Produce the plan below, then STOP and wait for ratification.

**Scope:** provenance/sentinel pass minting the 2026-07-21 Oxborrow meeting outcomes. Third resolution pass (RESOLUTION_Q11 precedent, then the 2026-07-16 docstring pass). It mints TWO sentinel resolutions (Q13, Q2), ONE graded-constant graduation with its two mechanical report regenerations (PLANNING_C0 → 200), and docstring/doc-level records for everything else. Evidence source for every item is the archived meeting notes (A0) — every resolution payload and grade tag cites that archive path, never memory.

**Hard scope guards:**
- No physics or logic changes. No numeric changes other than those explicitly listed (A1, A3). No new constants except those listed.
- Q9 stays UNRESOLVED — no `SentinelResolution` for it (A4 is docstring/description-level only).
- The ONLY artifact regenerations sanctioned in this pass are the two deterministic generator outputs that consume `PLANNING_C0`: `thermal/reports/q_margin_planning_point.md` (via `cavity.thermal.report_margin`) and `thermal/reports/q_margin_turnover.md` (via `cavity.thermal.report_turnover`), plus their byte-pins. Everything else that goes stale (F5, the one-pager, SPEC prose) is enumerated and left stale with the follow-on pass named (plan requirement 5).
- Archived gate runs, `refs/gate_runs/`, the frozen `wu_measured` anchor, and all archived reports outside the two named above are byte-immutable.
- `KAPPA_S`, the two-linewidth law, and its UNRATIFIED status are untouched (see the A3 guard).
- No Layer A / sweep-engine work. Resolving Q13+Q2 narrows the D8/D7 solve gates to Q9 alone; gate-refusal *messages and their pinned tests* update mechanically (they interpolate `_SENTINELS_BY_QUESTION` descriptions — enumerate the flips), but no engine, design, or backend logic changes and every solve-ready exit still refuses (on Q9).
- `mock_resolutions()` in `dofs.py` is untouched — mocks stay mocks; the Q13 mock's "evidence-favoured branch" note may gain a dated one-line annotation that the real resolution has since landed, nothing more.
- No opportunistic refactors, no test deletions, no tolerance changes.

**Known machinery facts (verified against `main` — use these, do not rediscover them wrong):**
- `SentinelResolution` / `Rung` / `ResolutionContext` live in `src/cavity/sweep/dofs.py`; ratified resolutions register in `src/cavity/sweep/resolutions.py` (`RATIFIED_RESOLUTIONS`, currently `(RESOLUTION_Q11,)`).
- Required payload keys: Q13 → `("sto_height_m", "selection_evidence")`, optional `sto_height_band_m` (the RESOLUTION_Q11 extra-key precedent); Q2 → `("p_tune_nominal", "p_tune_min", "p_tune_max", "mechanism")`. All lengths in METRES.
- The `Rung` enum has NO verbal/written member — use `Rung.SUPERVISOR_CONFIRMED` and carry "(VERBAL, in-person meeting 2026-07-21; contemporaneous notes archived at <A0 path>; written confirmation pending — rides the confirmation email)" in the provenance string, exactly the Q9-partial precedent in `SENTINEL_Q9.description`.
- `PLANNING_C0 = 190.0` and `PLANNING_C0_ROWS = (50.0, 190.0, 500.0)` live in `src/cavity/thermal/report_margin.py`; `report_turnover.py` imports `PLANNING_C0` from there. Both reports are byte-pinned in `tests/test_thermal_detuning.py`.
- `STO_HEIGHT_FORK` (a `ForkedConstant`) lives in `src/cavity/provenance/constants.py`; `SENTINEL_Q13` (a `ForkTrace`) mirrors it in `dofs.py`; `WuSTORingGeometry.sto_height_m` holds the fork object.
- `GEOM_WU_STO_RING.sto_outer_radius_m = 6.0e-3` (Wu 2020 print "O.D. = 12.0 mm") is DOF row 2 (`sto_outer_radius_m`) at `LITERATURE_CONFIRMED` rung with the ±25 µm machining band.

---

## A0 — Archive the meeting record (step zero; everything cites it)

Copy the contemporaneous notes file (`21 07 2026 cont notes.docx` — path supplied at run time) to `calibration/data/raw/oxborrow_meeting_notes_2026-07-21/` with a `MANIFEST.sha256`, per the 2026-07-16 notes precedent. If the crystal-placement photos (A4) are available as files, archive them in the same directory under the manifest; if not, the manifest README records their existence and holder as an outstanding attach.

Grade for all meeting content: **Oxborrow-VERBAL (2026-07-21), contemporaneous notes archived.** Where an item is a verbal report of a physical measurement, say exactly that — do not shorthand it to "measured."

## A1 — Q13 RESOLVED: STO ring height fork collapses to 8.6 mm

- Route: the fork's named caliper route. Rung: `Rung.SUPERVISOR_CONFIRMED`; provenance string states verbatim that this is a *verbal report of a physical caliper measurement* (8.6 mm), in-person meeting 2026-07-21, notes archived (A0), written confirmation pending. 8.6 was already the evidence-favoured branch (two prints vs one); the measurement decides it.
- Mint `RESOLUTION_Q13` in `resolutions.py` with payload `{"sto_height_m": 8.6e-3, "selection_evidence": "<caliper, verbal report, meeting 2026-07-21, archive path>"}`. No `sto_height_band_m`: no measured band was obtained, so the ±25 µm machining placeholder materialises per `design.materialise_dims` — state this in the payload/provenance rather than leaving it implicit.
- `STO_HEIGHT_FORK` in provenance is NOT deleted and NOT collapsed to a float — the fork object remains the record; the number enters ONLY via the resolution (the machinery's designed path). Its docstring ("No plain-float ring height exists in the repo until Q13 resolves") gains a dated resolution annotation; the SM 8.5 print is annotated superseded-by-measurement, preserved as printed.
- Update the stale-by-construction docstrings: `resolutions.py` module + `ratified_resolutions()` ("Q11 only as of 2026-07-17"), `RATIFIED_RESOLUTIONS` (now three entries, question order), `SENTINEL_Q13.description` (resolution recorded, fork decided), `dofs.py` module docstring rows list, and the `WuSTORingGeometry` docstring's Q13 lines.
- Enumerate: every consumer of `STO_HEIGHT_FORK` / `SENTINEL_Q13`, every test pinning the fork-refusal behaviour or a solve-gate refusal message naming Q13, with expected before/after behaviour per test.

## A1b — NEW DISCREPANCY: measured O.D. 12.2 mm vs printed 12.0 mm — flag, do not absorb

The meeting notes record STO ring outer diameter **12.2 mm, physically measured** (same verbal-report-of-measurement rung as A1). `GEOM_WU_STO_RING.sto_outer_radius_m` carries **12.0 mm as an exact print** (Wu 2020 §III.C), feeding DOF row 2 at `LITERATURE_CONFIRMED` with a ±25 µm band. The 0.2 mm gap is **8× the entire machining band** — this is a print-vs-caliper conflict of exactly the class that created Q13, NOT a confirmation, and it must not be recorded as one.

- Do not overwrite the print. Plan BOTH candidate treatments and recommend one with reasoning:
  (i) a dated measured-value annotation at the verbal rung on `GEOM_WU_STO_RING` (docstring + the DOF row-2 provenance string), discrepancy stated numerically, question queued for the confirmation email — fork deferred until the written reply either upholds or dissolves the conflict;
  (ii) a new `ForkedConstant` + sentinel (next free Q-number) that refuses arithmetic on the O.D. now, registered in `_REQUIRED_PAYLOAD_KEYS` / `_SENTINELS_BY_QUESTION` / the solve gates.
- The recommendation must weigh: Layer A is deferred (no solves consume row 2 today — the cost of (i) is low); the Q13 precedent treats measurement as decisive but that measurement *agreed* with the favoured print while this one *contradicts* the only print; and candidate explanations (fitting/wrap, print rounding, caliper placement, a different ring) may be LISTED as speculation only, never asserted.
- Whatever the treatment: the confirmation email gains the line "we measured O.D. ≈ 12.2 mm against the printed 12.0 mm — which should the model carry, and is a caliper band available?"

## A2 — Q2 RESOLVED: piston travel band [15, 25] mm

- Mint `RESOLUTION_Q2` with payload `{"p_tune_nominal": 15e-3, "p_tune_min": 15e-3, "p_tune_max": 25e-3, "mechanism": "<box internal height / piston position on the brass screw; travel band Oxborrow-verbal 2026-07-21, archive path; nominal = the recorded as-operated 15 mm = GEOM_WU_STO_RING.box_internal_height_asoperated_m>"}`. Rung `SUPERVISOR_CONFIRMED`, verbal caveat + written-pending in the provenance string. Note the nominal sits AT the band edge — confirm the machinery accepts nominal == min (enumerate any validator that assumes strict interiority) or state the fallback (e.g. nominal at the emailed-18 mm interior point, with the as-operated 15 mm recorded alongside) as a plan decision point.
- Consistency block in the provenance (informational): as-operated 15 mm = lower edge; the 2026-07-17 emailed 18 mm sits interior; with ring 8.6 mm + 3 mm deck = 11.6 mm occupied, the band implies ceiling-to-STO clearance 3.4–13.4 mm, bracketing the stated 5–10 mm typical operating separation.
- The rider stays OPEN and the payload says so: the piston-step annular-gap DEPTH (the optional Q2 payload key named in `dofs.py`) was not obtained — still an ask, does not block the resolution.
- Update: `SENTINEL_Q2.description` + `routes_to` (email answered in person 2026-07-21), the `resolutions.py` docstrings (shared with A1), the `dofs.py` module docstring row-9 lines, and the `GEOM_WU_STO_RING.box_internal_height_asoperated_m` / `p_tune` provenance strings ("travel band OPEN" → resolved, dated).
- Enumerate: every solve-ready exit whose refusal names Q2; after A1+A2 both design modes refuse on **Q9 only** — list each affected refusal message and pinned test with expected before/after text (the messages interpolate sentinel descriptions, so A1/A2's description edits propagate into them too — account for that in the expected strings).

## A3 — PLANNING_C0 graduated to provenance at 200, both pinned reports regenerated

The 2026-07-13 rationale for keeping C₀ out of `provenance/constants.py` ("no measured C0 exists") is superseded in part: still not measured, but now ELICITED — Oxborrow, verbal, 2026-07-21, quoted with his stated condition: *"If everything's going well, and nothing's misbehaving, and everything's coupled properly, C = 200 seems good. Use C₀ = 200."* The conditional phrasing is part of the record: a best-case planning value, and the docstring carries that framing.

- New provenance constant (propose the exact class/instance names, e.g. `PlanningCooperativity` / `C0_PLANNING`): value **200.0**, grade ELICITED / SUPERVISOR-VERBAL (2026-07-21, archive cite, written confirmation pending), with the 190 era preserved as a dated prior-value record (the `TOL.tan_delta_max` two-era pattern) and the "never recomputed from κs — no G² exists until Phase 1b" convention restated verbatim.
- Rewire `report_margin.py`: `PLANNING_C0` imports from provenance (or is replaced by the provenance name — propose which, respecting the `report_turnover` import); `PLANNING_C0_ROWS` becomes `(50.0, 200.0, 500.0)`; the module docstring's "deliberately NOT graduated" paragraph gains the dated reversal.
- Sweep both generators for hardcoded "190" PROSE that f-strings don't catch (known: the turnover report's "the planning-point report imports C0 = 190 directly" status note; check `detuning.py`'s rung strings too) and update.
- Regenerate both reports through their committed generators; update the byte-pins in `tests/test_thermal_detuning.py`. State the expected numeric movements in the plan (√(199)/√(189) ⇒ Δf_max +2.6%-class; turnover calibration c = C0/Q_L rescales likewise; crossings move slightly).
- Guard, verbatim in the constant's docstring AND the changeset message: *Oxborrow's C₀ = 200 grades the planning cooperativity only; it is NOT ratification of the two-linewidth threshold law, the turnover result, or the margin framing, which remain UNRATIFIED pending the findings note.*
- Enumerate every OTHER artifact that prints 190 (F5 figure, supervisor one-pager, SPEC prose, decision memo, any docs/plans references): STALE this pass, regeneration rides the margin re-presentation follow-on (C₀-axis figure + Wu-print κc branch). Nothing in that list is touched here.

## A4 — Q9 docstring-level annotation only (sentinel stays unresolved)

Record in `SENTINEL_Q9.description`, the `crystal_eccentricity_m` row provenance, and the design doc's Q9 entry, at the verbal rung with the A0 citation:

- Test-rig placement facts: crystal simply placed inside the ring; length visually comparable to the ring height; **not deliberately centred in this test rig**; no tolerances obtained; **photos exist** (archived per A0, or recorded as pending attach).
- Reconciliation, stated explicitly so the rungs never read as contradictory: 2026-07-16's *eccentricity nominal = CENTRED (supervisor-confirmed)* is the design nominal; 2026-07-21's *not really centred* describes the test-rig realisation. Compatible; the realisation looseness is information about the centring-tolerance band (the open half of Q9), and the photos are the candidate evidence for bounding it.
- Transfer caveat: in the actual device the crystal would be grown on a waveguide — test-rig placement bounds do not transfer; flagged, not resolved.
- No `SentinelResolution`, no numeric changes, no new mocks. The `crystal_eccentricity_m` nominal (0.0, `SUPERVISOR_CONFIRMED`) is untouched.

## A5 — S-ladder label ask CLOSED AS UNRECOVERABLE

Email B's S2/S3 question is answered: **joint recall failure** (neither Oxborrow nor the notetaker remembers; 2026-07-21). Record at the verbal rung:

- Retire the ask from every pending-ask list/checklist it appears in (enumerate the homes: SPEC's 2026-07-16 outcome-5 block annotation convention, `report_s_ladder.py` docstring, `thermal/reports/s_ladder_ballpark.md`).
- The numbering caveat becomes permanent: S3's reserved label is marked content-lost (bare heading, content never captured, unrecoverable by recall); S0/S1/S4 entries and artifacts untouched; no renumbering.
- `s_ladder_ballpark.md` is content-pinned: state whether the wording lands in the generator (⇒ regeneration + re-pin, and if so add it to the sanctioned-regeneration list explicitly in the plan for ratification) or in a dated errata note alongside (the Finding-1 manifest-errata precedent). Recommend one.

## A6 — Booth 225/360 verbal reaction: recorded, explicitly NOT confirmation

Append to the C3b record's doc home (candidates: `docs/booth_vmode_findings_note.md` status header; the `BOOTH_TABLE8_REVOLUTION_FACTOR` docstring's rung list): Oxborrow-verbal 2026-07-21 — plausible-mistake reaction to the 225/360 finding ("could be a mistake" on Booth's side). Tag as speculation at the verbal rung; the confirmation rung is unchanged (Booth-side WRITTEN CONFIRMATION PENDING); "identified, pending confirmation" wording stays everywhere; no tone upgrade. Note only that the reaction supports sending the note to Booth.

## A7 (optional, docs-only — include only if a natural home exists)

Process note at the communications-checklist home: Oxborrow's stated review condition — write-ups must be self-contained, variables introduced properly, no mind-reading — recorded as the standing format bar for the two-linewidth findings note and future notes. No new file for this.

---

## Plan output requirements

1. Full consumer enumeration for the Q13 fork collapse and the Q2/Q13 solve-gate changes: per file, per test, expected before/after behaviour — including refusal-message text shifts caused by the A1/A2 sentinel-description edits themselves.
2. A1b treatment recommendation with reasoning, plus the O.D. consumer enumeration (geometry engine RING path, DOF row 2, any export/report that prints it).
3. Exact proposed constant/class/field names, the three `SentinelResolution` payload dicts verbatim, and the grade/provenance strings verbatim.
4. Per-file edit list across A0–A7.
5. The stale-artifact list (A3's non-regenerated consumers of 190) with the named follow-on pass, and confirmation nothing in it is touched.
6. Expected test impact: before/after counts verbatim; every pin that re-mints (the two A3 reports; A5 if the generator route is recommended); no deletions, no tolerance changes.
7. The A2 nominal-at-band-edge validator check result and the chosen convention.
8. The confirmation-email line items this pass depends on for written-rung upgrades: (i) ring height 8.6 mm, (ii) the O.D. 12.2-vs-12.0 question + band ask, (iii) travel band [15, 25] mm, (iv) C₀ = 200.

Then STOP.
