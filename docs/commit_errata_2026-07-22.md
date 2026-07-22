# Provenance errata — 2026-07-21 meeting mint (`2e19187`), 2026-07-22

**Status: dated errata record (the audit-ruling-4 discipline, per
`docs/commit_errata_2026-07-20.md`: corrections are recorded beside the
history, never by rewriting it). The `2e19187` commit is NOT rebased.**

## Erratum — three in-situ measurements under-graded as verbal reports

The `2e19187` commit message and the provenance strings it minted grade
the meeting's numeric measurement outcomes as "verbally-reported caliper
measurement" / Oxborrow-VERBAL: the STO ring height (8.6 mm,
`RESOLUTION_Q13`), the ring outer diameter (12.2 mm, the O.D. discrepancy
record), and the piston travel band ([15, 25] mm, `RESOLUTION_Q2`).

**That under-states what happened.** All three were caliper-measured IN
PERSON, live and in situ during the 2026-07-21 meeting, performed/witnessed
first-hand by the repo author, who was present — the same session as the
archived contemporaneous notes and the four crystal-placement photographs.
They are first-hand in-person caliper measurements, not verbal reports of
measurements made elsewhere. Source of the correction: the repo author's
first-hand account (2026-07-22), consistent with the archived notes'
own wording ("Sto height 8.6 mm. CONFIRMED. STO ring outer diameter,
12.2 mm confirmed. Measured physically.") and the in-meeting photo EXIF
record (`calibration/data/raw/oxborrow_meeting_notes_2026-07-21/`).

The under-grade originated in the mint prompt's own grading rule
(`docs/plans/mint_prompt_2026-07-21_oxborrow_meeting.md`, A0: "Where an
item is a verbal report of a physical measurement, say exactly that"),
which presumed every physical measurement had been made elsewhere and
reported into the meeting. The mint executed that rule faithfully; the
rule mis-described these three items.

## What was correct at mint time and is unchanged

- **C₀ = 200 genuinely IS a verbal elicitation** — its ELICITED /
  supervisor-verbal grading (`C0_PLANNING`) is correct and untouched.
- **Written confirmation from Oxborrow is still pending** on all four
  line items; the "written confirmation pending — rides the confirmation
  email" caveat stays everywhere.
- **No measurement band exists for any caliper value** (single readings,
  no repeats, no stated caliper placement); the caliper-band ask stays
  open, and the ±25 µm placeholder route applies where applicable (Q13).
- **The ring-identity claim keeps its verbal grade**: that the measured
  ring IS the same ring as the Wu 2020 build is Oxborrow's verbal
  assertion, not independently verified — graded separately from the
  measurement provenance.
- **The O.D. treatment (i) is unchanged**: the Wu print 12.0 mm stays the
  carried value at its rung, 12.2 mm stays the recorded measurement,
  neither is called wrong, no branch is selected, `STO_HEIGHT_FORK` is
  untouched, and no new fork or sentinel is minted.
- **The `Rung` enum is unchanged** — `SUPERVISOR_CONFIRMED` remains the
  minted rung (no verbal or measured member exists); the finer truth is
  carried in the provenance strings, per the Q9-partial precedent.
- **No numeric, physics, logic, or window changes** ride this correction.

## Where the correction lives

Corrected in place, each site tagged "provenance corrected 2026-07-22":
the `STO_HEIGHT_FORK` / `WuSTORingGeometry` docstrings
(`src/cavity/provenance/constants.py`), `RESOLUTION_Q13` /
`RESOLUTION_Q2` and the module docstrings (`src/cavity/sweep/resolutions.py`),
the `SENTINEL_Q13` / `SENTINEL_Q2` descriptions, DOF row-2 provenance and
module docstring (`src/cavity/sweep/dofs.py`), the `reply_ingest.py`
dedupe rationale comment, affected test docstrings, and a 2026-07-22
entry appended to the SPEC revision record (the 2026-07-21 block is
preserved verbatim) plus dated addenda on SPEC §11 items 12/13.

NOT corrected, by the archive discipline (byte-immutable): the A0
archive's `MANIFEST.sha256` provenance comment prints "verbal report of a
caliper measurement" on its `RESOLUTION_Q13` line — it stays verbatim and
reads through this erratum. The mint prompt
(`docs/plans/mint_prompt_2026-07-21_oxborrow_meeting.md`) is the
historical prompt of record and is likewise not edited.

The commit history is not rewritten.
