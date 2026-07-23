# Archive — Oxborrow "standard resonator" email, 2026-07-23

**Grade for all email content: Oxborrow-WRITTEN (2026-07-23), archived.**
Both emails carry Oxborrow's "written without AI" sign-off.

Archived 2026-07-23 (day of receipt) by the repo author. Canonical directory
name: `oxborrow_std_resonator_2026-07-23` — the ratified plan checkpoint and
its prompt (`docs/plans/prompt-2026-07-23_oxborrow_standard_resonator.md`)
refer to this same archive as `oxborrow_standard_resonator_2026-07-23`; the
on-disk "std" spelling is the canonical name (runtime-ratified 2026-07-23).

## What this is

Mark Oxborrow's email of Thu 23 Jul 2026 03:06:46 +0000, subject "resonator
magnetic field profile", to Vanessa Ussalim ("Ussalim, Vanessa C"
`<vanessa.ussalim24@imperial.ac.uk>`), cc Niall Randall Carrera, Mingyang
Liu, Aaryan Sharif — plus his follow-up reply of 03:10:11 +0000 on the same
thread. THIRD-PARTY CONTEXT: it is addressed to Vanessa for her maser
filling-factor comparison across crystal dimensions; it is NOT a reply to any
maphon ask. In particular it is not a reply to the owed confirmation email
(which remains UNSENT as of this archive), so the reply-ingest machinery
(`cavity.sweep.reply_ingest`) is deliberately NOT invoked on it.

Thread root, quoted in full beneath the 23 Jul body: Vanessa Ussalim,
17 Jul 2026 10:35, "H(r) for Filling Factor Calculation" — asks for H(r) data
and "the denominator cavity integral value"; her inline snippet of that
integral, `∭_cavity H²(r) dV`, is `images/b69d2bf3-….png`. Oxborrow's reply
of 17 Jul 10:48 offers to model it from scratch, and points at
https://arxiv.org/abs/2412.21166 ("The geometry of the cavity they analysed
is drawn / explained in […] updated in the .pdf attached") for the cavity
Niall/Mingyang analysed. NB this 17 Jul thread is DISTINCT from the
2026-07-17 STO-geometry email archived at
`calibration/data/raw/oxborrow_sto_2026-07-17/`.

## Inventory (9 files, MANIFEST-pinned)

| File | Bytes | Identity |
|---|---|---|
| `resonator magnetic field profile.eml` | 4,094,931 | The 2026-07-23 email (headers + full quoted 17 Jul thread + all five attachments embedded). |
| `Re_ resonator magnetic field profile.eml` | 4,852 | Oxborrow's follow-up reply, 03:10:11 +0000; body is the one-line H² decomposition quoted below. |
| `1p41GHz_4mm_bore_mo1.mph` | 1,310,940 | The COMSOL model file attached to the email. |
| `20 by 20 Magnetic Field grid mo1.txt` | 39,083 | 20×20 (r, z) H-grid CSV export, columns `r z Hrad Haxi` (COMSOL 6.0.0.405; header verbatim below). |
| `100 by 100 Magnetic Field grid mo1.txt` | 969,222 | 100×100 version of the same export (10,000 nodes). |
| `1p45report.docx` | 422,045 | FIFTH attachment (not anticipated by the plan prompt's attachment list): a COMSOL auto-generated model REPORT (report date "Jul 23, 2026, 3:48:03 AM"), template lineage "This simulates the optical mode in a disk or ring resonator. […] Mark Oxborrow. Ported to COMSOL 4.2 by David Hutchison"; prints Parameters / Geometry / Eigenvalue sections. Content grading DEFERRED to the A4 follow-on below. |
| `images/8b5372d5-3116-4894-97cf-76b77fe34765.png` | 222,831 | The field plot inlined in the 23 Jul body. Header text verbatim: `lambda(1)=1.4128E9  Surface: 0*Eazi+abs(MagEnDens)+1e-14  Arrow Surface:`. |
| `images/b69d2bf3-b7bf-4c79-b9a4-8d771656ec3d.png` | 9,389 | Vanessa's denominator-integral snippet, inlined in her quoted 17 Jul email. |
| `README.md` | — | This file. |

**Attachment integrity — VERIFIED at archive time:** all six embedded MIME
parts of the main `.eml` were base64-decoded and byte-compared (SHA-256)
against the standalone files above — **all six are byte-identical**. (The
`size=` values in the Content-Disposition headers are encoder-side figures
and do not equal decoded sizes — recorded so nobody re-litigates the
mismatch.) The two `images/` files are the inline `image.png` parts saved
under export UUIDs; mapping via Content-ID: cid `e5e5f87c-80a1-4403-a71d-…`
(23 Jul body, field plot) = `images/8b5372d5-…png`; cid
`6a70f936-4e06-407b-a2b2-…` (17 Jul quoted body, the integral snippet) =
`images/b69d2bf3-…png`.

**Outstanding attaches: NONE.** Every item on the plan prompt's attachment
list (.eml, .mph, both CSV grids, field-plot image) is in hand — the R10a
deferred-archive branch was not needed. The inventory EXCEEDS the prompt's
list by three items (the reply .eml, `1p45report.docx`, the snippet png),
archived with the rest.

## Facts of record (verbatim prints — cite THIS archive, never memory)

From the 2026-07-23 body:

> Here is the magnetic field plot for the "standard" resonator whose
> dimensions we defined yesterday with Aaryan.

> STO ring: 12.2 mm outer diameter, 4 mm inner diameter, 8.6 mm high
>
> Copper cavity: 28 mm inner diameter, 15 mm high.
>
> STO ring resting on a (plastic) support 3 mm above the copper cavity's
> floor.

> The frequency is actually 1.41 GHz for this geometry. Would have to lower
> the ceiling to squeeze the frequency upwards.

> Can easily change the dimensions to generate a slightly different grid map.

> Note that the dielectric ring, surrounding air and plastic support are all
> "non-magnetic", meaning that flux density B = mu H, where "mu" is the
> permeability of a vacuum.

> At each grid point with a radial = horizontal (r) and axial = vertical (z)
> co-ordinate, the radial (horizontal) component Hrad, and axial (vertical)
> component (Haxi) of the magnetic field strength H is given.

From the 03:10 follow-up reply (the whole body):

> H^2 = Hrad^2 + Haxi^2  (since H has no azimuthal component)

Field-plot header: `lambda(1)=1.4128E9` — the archived model report's own
NOTES state the solver's "lambda" output "is frequency not wavelength even
though it is called lambda by the solver, and is in Hz"; i.e. the plot header
prints f = 1.4128 GHz, matching the prose "actually 1.41 GHz".

## Dating discrepancy (recorded, NOT harmonised)

The email's "whose dimensions we defined **yesterday** with Aaryan" would,
read literally against the 2026-07-23 send date, imply a 2026-07-22 session.
Per the repo author's first-hand account (2026-07-23): **no meeting has
occurred since 2026-07-21.** The referenced definition session is therefore
identified as the **2026-07-21 meeting** — the same session as the archived
in-person caliper measurements
(`calibration/data/raw/oxborrow_meeting_notes_2026-07-21/`). The
identification's basis is the FIRST-HAND ACCOUNT, not the email; the email's
"yesterday" is preserved verbatim above and carried as an inaccuracy in the
source. The two statements stand side by side; NO separate meeting record
exists or is invented.

## Model-name mismatch (recorded, NOT harmonised)

Both CSV exports carry the header (verbatim, 20×20 shown; the 100×100 header
is identical except `% Date: Jul 23 2026, 03:16` and 10000 nodes):

```
% Model:              1p44GHz_6mm_bore_mo4.mph
% Version:            COMSOL 6.0.0.405
% Date:               Jul 23 2026, 03:02
```

and `1p45report.docx` likewise reports model `1p44GHz 6mm bore mo4.mph` at
path `G:\Working Zone\Imperial 2025-26\Teaching\UROP\Vanessa\1p44GHz_6mm_bore_mo4.mph`
— while the attached model file is named `1p41GHz_4mm_bore_mo1.mph`. The
exported CONTENT is consistent with the standard geometry stated in the email
body: the field plot draws the ring at r ≈ 2–6.1 mm, z ≈ 0–8.6 mm inside a
domain r ≤ 14 mm, z ∈ [−3, +12] mm, and the grids tile exactly that cavity
box, cell-centred (20×20: r = 0.35 + k·0.70 mm, z = −2.625 + k·0.75 mm;
100×100: r = 0.07 + k·0.14 mm, z = −2.925 + k·0.15 mm). Candidate
explanation — SPECULATION, asserted nowhere: a 6-mm-bore predecessor model
was modified in-session to the standard dims and the exports/report were made
before a save-as minted the `1p41GHz_4mm_bore_mo1.mph` name. Disposition:
resolution rides the A4 follow-on (the attached model's `dmodel.xml` settles
what the attached file actually contains); until then the grid ↔ attached-
model provenance is NOT established by the headers, and that caveat rides any
use of the grids (A5).

## Follow-ons registered here (names only; nothing executed at archive time)

- **A4 — standard-resonator .mph/report readout** (licence-free): read the
  archived `.mph` as a zip (`dmodel.xml`; the `BOOTH_TABLE8_REVOLUTION_FACTOR`
  precedent) plus the archived `1p45report.docx`, to mint at written-artifact
  grade: STO εr and tanδ, wall treatment, crystal presence/absence,
  Revolution-2D angle settings (the 225/360 workflow-tradition question),
  and the model-name-mismatch resolution above.
- **A5a — grid ingestion**: the 100×100 grid through
  `docs/field_export_schema.md` (adapter; caveats: H-only, no E/masks,
  half-plane grid, 2πr weighting via the quadrature primitive, coarse grid,
  real-signed values, unknown normalisation, the provenance caveat above).
- **A5b — v_mode convention rehearsal**: v_mode_local / v_mode_global on the
  ingested grid via `cavity.extraction.modal` (H-only suffices); the
  crystal-less build's gain-mask definition must be declared before
  computing.
- **A5c — cross-person consistency hook**: Vanessa's filling-factor
  numerator/denominator vs maphon's extraction on the same CSV, when her
  numbers exist.
- **W3 — standard-build reproduction windows** (named ratification item,
  NOT drafted): acceptance windows for any maphon reproduction of the
  standard-build solve, drafted BEFORE any solve, W2-style.
