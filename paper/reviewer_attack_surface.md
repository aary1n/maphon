# Reviewer attack surface — anticipated referee lines and the current defence state

**Status: PLANNING ARTIFACT (paper spine, 2026-07-20).** One entry per
anticipated attack: the attack as a referee would phrase it, the current
defence (with artifacts), the residual exposure, and what closes it. Claim
IDs refer to `paper/claim_evidence_matrix.md`. An attack marked **OPEN
EXPOSURE** cannot currently be answered end-to-end — those are the ones the
publication build command (`python -m publication.build`) reports against
headline readiness.

---

## A1 — "Your margin numbers rest on an unratified threshold law and an imported C₀ = 190."

Claims: C1, C2.
**Defence now:** the two-linewidth law is derived on the record (SPEC §7.T4
re-derivation block, 2026-07-13) and was itself prompted by an external
review argument, then verified by independent derivation; the committed
(κc/2)√(C₀−1) form is recovered exactly as the κs → 0 limit; the C₀-import
convention is stated everywhere it is used ("C₀ = 190 stays the IMPORTED
planning cooperativity, never recomputed from κs") and the fixed-G
calibration of the turnover map is flagged as the same napkin assumption
Layer A item 9 exists to replace.
**Residual exposure:** the result is supervisor-UNRATIFIED (findings note
drafted, not sent); no G² exists until Phase 1b; the fixed-G turnover
crossings are convention objects.
**Closes it:** Oxborrow ratification + Layer A joint C₀/κc/κs DOF derivation
(SPEC §11 item 9) + κs branch discrimination (A2). Until then: planning-tier
language only. **OPEN EXPOSURE for headline use.**

## A2 — "κs = 1.4 MHz is another sample's ODMR FWHM at unspecified power — not your crystal's linewidth."

Claims: C13, C2, C1.
**Defence now:** fully disclosed as a BRANCH CHOICE (`KAPPA_S` docstring):
best-per-host-at-differing-powers caveat rides every margin number; the band
0.55–1.75 MHz spans the Pc:PTP rows; the maser crystal (0.053% protonated)
matches no table row and this is stated; the single-homogeneous-packet
mapping is labelled a threshold-model assumption; W20's same-build angular
κs = 1.1 MHz is recorded (with the 2π trap guard) and deliberately not
resolved into the constant.
**Residual exposure:** the branch question is real — margin moves −46%/+19%
across the band.
**Closes it:** Angus's raw linewidth table + low-power extrapolations
(load-bearing ask), Oxborrow's linewidth-class ruling (D4 conjunction), or an
FID/echo measurement on the actual maser crystal (provenance table threat 2).

## A3 — "You claim Booth's printed mode volume is wrong by ×1.6 based on your own reading of her files."

Claims: C3, C3b.
**Defence now:** mechanism read directly from the supervisor-supplied
`.mph`'s results tree (partial-revolution dataset, 225°/360°); quantitative
closure to +0.21%; Table 8 shown internally consistent so her comparative
conclusions survive; the finding is framed as a normalisation-convention
identification, NOT an error accusation; the archived failing record was
never edited — a new re-judged record was minted alongside.
**Residual exposure:** the TE01δ row inherits the mechanism by
uniform-workflow inference; Booth-side written confirmation PENDING (findings
note drafted with the truncation-alias discrimination question).
**Closes it:** Booth/Oxborrow written confirmation. Until then the paper says
"identified…, pending confirmation".

## A4 — "Your calibration numbers are digitized from plot images."

Claim: C4.
**Defence now:** every derived number is stamped
`graph-digitized-provisional; superseded_by_raw_data=True`; the ±0.05 MHz
quantisation floor is the stated error model; the loader refuses ungraded
input; the raw-data re-fit pipeline is pre-registered (D4–D7 rulings,
2026-07-20) including the supersession discipline (digitized CSV immutable,
superseded not overwritten).
**Residual exposure:** none at the claim level as long as wording stays at
digitized grade; the h14 χ²/dof = 3.7 and the step non-detection carry the
quantisation caveat.
**Closes it:** Angus's raw ν(P) traces (top data ask).

## A5 — "Was the laser power measured at the sample? If not, your η_abs is meaningless."

Claim: C4 (T5).
**Defence now:** the power-measurement plane is an OPEN Angus ask, recorded
in `ExcitationSource.power_plane` and inside the feed JSON; the analysis
splits plane-independent statements (ΔT per labelled watt, slope ratios,
probe-inferred heating) from plane-dependent ones (η_abs interpretation
only); fitted η_abs ≈ 0.16–0.17 is explicitly flagged as compatible with
near-total absorption ONLY IF the missing ~83% is upstream delivery loss.
**Residual exposure:** η_abs·R_int decomposition ambiguous until the plane
resolves; T4's shared-η_abs cancellation condition is untested.
**Closes it:** one metadata line from Angus.

## A6 — "You are implying deuteration matters / doesn't matter without evidence."

Claims: C4 (T4), WS3 study.
**Defence now:** the pre-registered three-way rule returned
GEOMETRY-SUFFICIENT with LOW discriminating power; the verdict sentence is
carried verbatim: an intrinsic effect is "NOT REQUIRED and NOT EXCLUDED";
the glue-contact confound φ is quantified as an alternative the test cannot
exclude; the CPW via-contact caveat (2026-07-16) is recorded as further
weakening any deuteration-only attribution; the deuteration-identifiability
study (WS3) is experiment DESIGN, refuses detection claims by construction,
and keeps Angus-pending unknowns sampled, never fixed.
**Residual exposure:** minimal if wording discipline holds; the
deuteration-transfer caveat on df_spin/dT (protonated Singh crystal → d14
samples) must ride every cross-sample statement.
**Closes it (for a real claim either way):** matched-sample data per the WS3
design outputs — not more analysis of the current pair.

## A7 — "Unit conventions: maser papers mix angular and cyclic rates; how do I know you didn't?"

Claims: C2, C13, C14.
**Defence now:** the W20 angular-"Hz" trap is documented in the provenance
table (verified numerically: κc = 2πf/Q_L reading reproduces the printed
400 kHz linewidth); the repo convention (cyclic-Hz FWHM, κc = f/Q_L,
κs = 1/(πT₂)) is single-sourced and CI-anchored (anchor A6 carries the 2π
sibling trap); the export schema's deliberate angular handoff for
Maxwell-Bloch consumers is labelled as a conversion, not a trap instance.
**Residual exposure:** low; the anchors are regression-pinned.
**Closes it:** nothing pending — cite the anchors and the trap note.

## A8 — "Singh et al. print no uncertainty; your −109 ± band is your own invention."

Claim: C12.
**Defence now:** the raw point series behind the figure is archived
byte-for-byte with SHA-256 pins (shared by the first author); the printed
−101 is shown consistent with its own raw data to ~1%; the dominant
systematic (temperature-axis definition, ×1.7 between branches) IS the band;
statistical + quantisation contributions are stated (1–3 kHz/K); the ± is
explicitly labelled ours, residual-based; the paper's headline 247 kHz/K is
excluded with its phase-transition-region provenance.
**Residual exposure:** axis-definition unresolved (Harpreet ask); Zenodo
identity unverified; attribution brokering pending.
**Closes it:** Harpreet's axis metadata; Zenodo access if the ± becomes
load-bearing; early acknowledgement brokering via Oxborrow.

## A9 — "Your calibration rig numbers cannot transfer to the maser geometry."

Claims: C4, C1.
**Defence now:** that is the repo's own rule — every calibration constant is
NON-TRANSFERABLE by declaration and import boundary (CI-enforced one-way
`calibration` → `cavity`); what transfers is the transport model and dν/dT,
stated in SPEC §7.T5; ΔT numbers never cross geometries.
**Residual exposure:** none if the discipline holds; the paper must state
the asymmetry (spin arm calibrated, cavity arm model-only).
**Closes it:** nothing pending — this is a design feature to present, not a
gap.

## A10 — "Your forward model has never reproduced the build you actually model (Wu ring)."

Claims: C5, C14.
**Defence now:** solver correctness is anchored on Booth (§5a GREEN, five
windows); the Wu re-base is literature-verified line-by-line against the
archived primary PDFs (k = 1 stated in print; Q₀ = 7200 corroborated twice);
W2 acceptance windows are ratified in advance of any solve (pre-registration
discipline), with V_mode held out of gates pending the integration-convention
check (the 225/360 lesson applied prospectively).
**Residual exposure:** REAL — no W2 solve exists; the Q13 height fork blocks
it; `phase1_complete` is FALSE regardless (confinement row).
**Closes it:** Q13 resolution + licence session → first W2-passing solve.
**OPEN EXPOSURE.**

## A11 — "What did your supervisor actually approve, versus what did you decide?"

All claims.
**Defence now:** the endorsement ladder is explicit and dated at every rung
(verbal vs written distinguished; verbal→written supersessions annotated,
e.g. the thermal-paste withdrawal); ours-unratified items are named (budget-
distribution framing, Q-margin result, calibration-target plan, D8, w_s
headline mode); "293+30=323" is labelled our reading of a verbal ruling.
**Residual exposure:** the framing items themselves — a referee cannot
attack what the paper doesn't overclaim, but the paper cannot lead with
unratified framing.
**Closes it:** the pending Oxborrow ratifications (SPEC §11 item 10),
including the first-paper boundary.

## A12 — "Your own-build κc uses Breeze's k = 0.2 — that's not your cavity's coupling."

Claims: C1, C2 (planning points).
**Defence now:** documented import (Booth states no coupling; Q12 ruling:
uniform k = 0.2, no scatter); every composed κc carries the
planning-assumption flag per draw; the Wu anchor itself now carries its own
stated k = 1 and is never mixed with the k = 0.2 composition.
**Residual exposure:** a modelled coupling port is out of scope (rider R2);
geometry dependence of coupling is invisible to Layer A — stated, not hidden.
**Closes it:** nothing pending at current scope; a coupling model would be a
schema/model extension (flagged as such).

## A13 — "The thermal scenario numbers look enormous (hundreds of K/W) — is the device viable at all?"

Claims: C6, C1.
**Defence now:** the S-ladder is BALLPARK tier by declaration, not device
prediction; the power axis is a scoping grid (no shot repetition rate exists
in print, so no CW operating point is derivable — stated); idealised BCs are
labelled (imposed-cold = blown-air limit; the as-built seat is insulating
CLPS, recorded); the S4 bracket pair brackets structurally, not statistically.
**Residual exposure:** a referee may still ask for the composite-body
(crystal+STO+spacer) calculation — recorded as above ballpark tier, deferred.
**Closes it:** the deferred composite-body pass + the §7.T7 across-range
competition report; neither is promised in the current claims.

## A14 — "Software tests are not physics validation."

All claims; WS4.
**Defence now:** the repo's own doctrine — anchors/pins guard conventions and
reproducibility, the validation gates (§5/§5a/W2) guard physics against
published anchors, and the two are never conflated; the publication build
command separates artifact reproducibility / scientific validation /
supervisor ratification / publication readiness as four independent statuses
and refuses "headline-ready" on test-green alone.
**Residual exposure:** none if the separation is maintained in prose.
**Closes it:** nothing pending — present the separation.

---

## Summary of OPEN EXPOSURES (headline blockers)

1. A1/A2 — margin law unratified + κs branch undiscriminated (Oxborrow +
   Angus).
2. A10 — no W2 Wu-anchor solve (Q13 + licence).
3. C1 itself — no Layer A/C population run (Q2/Q9/Q13 + licence + campaign).
4. A3 — Booth confirmation pending (findings note unsent).
5. A11 — framing ratifications pending (incl. first-paper boundary).
