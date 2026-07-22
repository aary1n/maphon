# W2 — Wu-anchor acceptance windows (drafted 2026-07-19; RATIFIED as planning choices, revisable at first solve)

Scope: the acceptance windows for validating the re-based model against
`TARGETS.wu_ring` (Wu 2020 + PRL 127 SM; k = 1 stated). W1 (the Phase 1b
window precedent) governs style. No gate row binds `wu_ring` until the
first W2-passing solve creates the Wu anchor record.

## Convention finding (the precondition — the 225/360 lesson)

The SM's "magnetic mode volume ≈ 0.32 cm³" is printed without a formula.
Its convention is INFERRED from its role: SM Eq. S5 (Einstein B
coefficient, B = μ₀γ²hf·T₂⟨σ²⟩/2V_mode) and Wu 2020's g_s =
γ√(μ₀hf/2V_mode) are the Breeze-family per-spin forms — V_mode
normalised at the field the spins see. That is `v_mode_local_m3`
(`extraction/modal.py`: ∫|H|²dV / max_gain(|H|²)), not
`v_mode_global_m3`. Grade of the identification: INFERENCE from printed
equations, not a stated convention — hence V_mode is a DIAGNOSTIC row
below, not a gate.

Build-specific consistency check, free at solve time: the SM places the
illuminated prism on the equatorial circle "where the magnitude of the
TE01δ mode's a.c. magnetic flux density, B, is maximum" (B ≥ 90 % of max
throughout). The gain region therefore contains the global |H|² maximum,
forcing v_mode_local ≈ v_mode_global for THIS build. Failure of that
near-equality indicts the gain mask or the field solution before any
comparison to 0.32 cm³ is meaningful.

Consistency note (recorded, not load-bearing): Q₀ = 7200 with all loss
dielectric implies effective tanδ = 1/7200 = 1.39e-4 = the re-derived
`TOL.tan_delta_max`; the canonical tanδ = 1.1e-4 gives Q_diel ≈
1/(p_e·tanδ) ≈ 9.1e3, leaving a plausible wall share. Anchor, band, and
loss split are mutually consistent pre-solve.

## Windows (planning choices, user-ratified 2026-07-19)

| Row | Quantity | Target | Window | Kind |
|---|---|---|---|---|
| W2.1 | f (Phase 1b Wu model, canonical nominals) | 1.4495 GHz | ±1.5 % | GATE. Residual sign recorded; a residual reachable inside the εr band [312, 318] (~±1 % on f) is non-alarming and must be stated with the εr sensitivity. |
| W2.2 | Q₀ | 7200 | ±25 % | GATE. The tanδ band [1.0, 1.4]e-4 alone spans ~±17 % of Q_diel; tighter would gate on an unvalidated loss split. |
| W2.3 | v_mode_local_m3 | 0.32 cm³ | report, no gate | DIAGNOSTIC (convention inferred, above). |
| W2.4 | v_mode_local / v_mode_global | ≈ 1 | within 10 % | GATE (build-specific, from the convention finding). |

Preconditions: solve on the Phase 1b Wu model — crystal present (εr =
3.0, Q11 planning grade) and spacer flag ON — matching what Wu's own
COMSOL simulated (Wu 2020 Fig. 6: STO + crystal + support highlighted).
Q13 must be resolved (no silent height selection) before the W2 solve.

First W2-passing solve creates the Wu anchor record and the Wu-build
sweep centre (design-doc 2026-07-19 addendum).

## Addendum — 2026-07-22: dual-geometry solve protocol (PRE-REGISTERED, written before any W2 solve exists)

Dated record; nothing above is edited. No window above is revised by
this addendum, and none will be revised at solve time under any
outcome.

**Hold-lift, on the record.** The 2026-07-21 mint (commit `2e19187`)
held the W2 solve pending the STO-ring O.D. question: Wu 2020 prints
O.D. 12.0 mm (the carried value, `GEOM_WU_STO_RING.sto_outer_radius_m`);
an in-person caliper measurement of the reportedly same ring during the
2026-07-21 meeting reads 12.2 mm — 0.2 mm on the dominant dimension,
~8x the ±25 µm machining band (provenance corrected 2026-07-22,
`docs/commit_errata_2026-07-22.md`: a first-hand in-person caliper
measurement, written confirmation from Oxborrow pending; the claim that
the measured ring IS the Wu 2020 build's ring stays Oxborrow-VERBAL).
**That hold is lifted by user decision of 2026-07-22**, resolved via
the dual-geometry protocol below — by solving BOTH geometries in one
session, NOT by selecting a branch and NOT by absorbing or dismissing
the discrepancy. The O.D. treatment-(i) record is untouched: the print
stays the carried value at its rung, the measurement stays recorded
beside it, neither is called wrong, and no carried value changes.

**Two solves, identical in every input except the ring O.D.:**

- **Run A — print O.D. 12.0 mm** (the carried value,
  `GEOM_WU_STO_RING.sto_outer_radius_m` = 6.0e-3).
- **Run B — measured O.D. 12.2 mm** (outer radius 6.1e-3; the
  2026-07-21 in-person caliper value, written confirmation pending,
  ring-identity claim verbal — entering this session as a LABELLED
  DIAGNOSTIC INPUT only, never as a carried geometry value).

Everything else, fixed identically for both runs and stated here
before results exist: ring I.D. 4.05 mm; ring height 8.6 mm via
`RESOLUTION_Q13` (in-person caliper, written confirmation pending; the
±25 µm placeholder band applies, unconsumed here); enclosure radius
14.0 mm (28-mm-fitting caveat riding); box internal height = the
recorded as-operated 15 mm (= `RESOLUTION_Q2`'s nominal, at the
band's lower edge); deck clearance 3.0 mm; flat ceiling — no piston
step (matches Wu's own Fig. 6 simulation region; the gap-depth rider
is open); spacer ON (CLPS εr 2.53, figure-derived seat dims, tanδ
deliberately ungraded = 0); **crystal PRESENT** (the §5b sub-domain,
built this session as the ratified precondition requires): planning
dims 3.0 × 8.0 mm (`GEOM_WU_STO_RING.crystal_*`, cross-build-transfer
flag riding), εr = 3.0 via `RESOLUTION_Q11` (planning grade, band
[2.4, 4.1] unconsumed), crystal tanδ deliberately ungraded = 0 (the
spacer precedent), placed on-axis (eccentricity nominal CENTRED —
supervisor-confirmed design nominal; the m = 0 axisymmetric solve can
represent nothing else) and axially centred on the ring mid-height
plane — a LABELLED PLANNING PLACEMENT recorded in the run meta (Q9
open; placement is not a W2 gate row). Materials: canonical branch
(STO εr' 316.3, tanδ 1.1e-4, Cu σ 6.0e7, impedance walls; PEC
companion arm per run for the wall split). Study: eigenfrequency
search at 1.45 GHz, n_modes 12. Mesh: the §5a-precedent convergence
ladder — base (dielectric 5e-4 m, air 2e-3 m), 5 levels, factor
sqrt(2), ending at the validated finest level (1.25e-4 / 5e-4) —
per arm, sigmas from the ladders, never fabricated.

**Gate binding.** Run A binds the W2 gates (W2.1 / W2.2 / W2.4 above).
The windows were ratified against the print build and are not revised
at solve time — no window edits under any outcome. Judgment ORDER
inside Run A restates the precondition above: W2.4 (the
local/global-ratio convention check) is computed and judged FIRST;
a W2.4 failure indicts the gain mask or field solution — stop and
triage before any window comparison, and the W2.3 number is declared
meaningless for that record. W2.3 stays report-only (convention grade
INFERENCE).

**Run B is DIAGNOSTIC.** It quantifies the model's f and Q0
sensitivity to the O.D. discrepancy (the implied local d f / d O.D.
and d Q0 / d O.D. are deliverables of the session regardless of
pass/fail) and indicates which geometry the printed anchors
(f = 1.4495 GHz, Q0 = 7200) are consistent with. Run B binds no gate,
creates no anchor record, and selects no branch regardless of result.
Any statement that Run B "lands inside" a window is informational
only.

**Pre-registered triage (restating 2e19187 and the ingestion plan
§4.4).** If Run A fails the f window, triage FIRST against the O.D.
discrepancy — does Run B land inside? — before questioning the
solver. If BOTH runs fail f beyond the εr-band explanation
([312, 318], ~±1% on f), that indicts the model/solver path and the
failure-triage ladder in
`docs/plans/oxborrow_reply_ingestion_and_wu_anchor.md` §4.4 governs
(no geometry retuning, no tolerance widening, no branch re-picking in
the failing session; the red result is the committed finding).

**Anchor-record conditions.** The Wu anchor record and the Wu-build
sweep centre are created ONLY by a passing Run A. If Run A fails and
Run B passes, NO anchor record is created; the result is written up
as a finding for the confirmation email to Oxborrow (already owed,
already carrying the O.D. line item) and the anchor question waits on
his written answer.
