# §5a own-model checkpoint — live lossy-wall solve at Booth's TE01δ point

## Context

Every margin number in `thermal/reports/q_margin_planning_point.md` currently composes
Booth's printed Q₀ = 6980 with Breeze's k = 0.2 — a cross-build composite, neither
build's number, flagged as such in the report's own status notes ("the §5a checkpoint
run supersedes every number here"). The frozen gate record (2026-07-06) has
`phase1_complete: false` with 5 of 6 rows `deferred_requires_comsol`, all blocked on
SPEC §11 gap #1 (Booth's dielectric cross-section unpinned; the assumed a/L = 0.5 puck
lands at 3.1 GHz). This pass runs the deferred Booth-point rows live, produces the
own-model f / Q₀ / p_e / field record, retires the composite in the margin report, and
pins the nominal centre Layer A will sweep around. COMSOL licence is available this
session.

**Load-bearing finding of this planning pass (from the primary sources, verifiable
in-repo):** the geometry ambiguity is closed by documents already in hand —

1. **The supervisor `.mph` is Booth's ANAPOLE row, verbatim.** Booth's thesis
   (`MEng_thesis-01865045.pdf`) Appendix A (p. 29) has TWO SrTiO₃ rows:
   TE01δ = 12.28 / 18.42 / 2.46 mm and Anapole = 22.36 / 33.54 / 4.472 mm. The
   `refs/comsol/booth/2D Resonator Lossy.mph` read-off (README: cavity r ∈ [0, 22.36] mm,
   z ∈ ±16.77 mm, circle centre r = 11.18 mm, radius 4.472 mm) matches the anapole row
   exactly, and its Q = 9581.37 matches Table 8's anapole Q = 9.58E+03 to 3 s.f.
   The README's current "1.82×-scaled torus variant / deviations" description is a
   misidentification and gets corrected this pass.
2. **"Resonator Width" = the axisymmetric r-extent** (box radius), proven by the
   `.mph`↔App. A correspondence. SPEC §2's parenthetical "box width 12.28 mm (→ box
   radius 6.14 mm)" is refuted; so is `geometry.py`'s docstring reading of 2.46 mm as
   the torus *major* radius.
3. **Table 4 (p. 15) fixes the construction ratios**: Box Width x, Box Height (3/2)x,
   Dielectric (cross-section = torus minor) Radius x/5; "Resonator dimensions are
   always adjusted in a proportionate manner, ensuring set ratios are maintained."
   The torus centre ratio is untabulated; the `.mph` pins it at the radial midpoint
   (11.18 = 22.36/2), and p. 17 confirms ring-to-axis distance was never optimised.
4. **Torus form is Booth's own statement** ("the toroidal resonator", p. 13;
   "torus-shaped dielectric ring", p. 16). The puck reading retires for the Booth point.

**Recovered TE01δ geometry (x = 12.28 mm):** box radius 12.28 mm, box height 18.42 mm
(= 1.5x exactly), torus minor radius x/5 = **2.456 mm** (App. A's 2.46 is its 3-s.f.
print — the anapole row prints the ratio value 4.472 = 22.36/5 at 4 s.f.), torus major
radius x/2 = **6.14 mm**, centred at the box mid-plane. Expressible today via
`CavityGeometry(box_radius_m=12.28e-3, box_height_m=18.42e-3, dielectric_radius_m=6.14e-3,
dielectric_shape=TORUS, dielectric_minor_radius_m=2.456e-3)` — no geometry-engine change
needed, only the provenance home and the wiring.

**Also settled from the thesis:** (a) Booth's Q is explicitly UNLOADED — p. 8: "Where
losses from external factors like coupling are ignored, the resulting measured Q factor
is referred to as 'unloaded'. The unloaded Q factor is what is referred to throughout
this project." Booth states **no** coupling coefficient (coupling out of scope, p. 13)
⇒ k = 0.2 stays Breeze's flagged planning assumption, now composed with an own-model Q₀.
(b) Copper σ = 6.00E+07 S/m is printed in Table 3 — the committed `Copper.sigma` now has
a Booth-primary corroboration. (c) Booth's mesh: "Extremely fine", max free-space
element 1 mm. (d) Booth's Q convention: Q = ω/(2|δ|) (p. 13) — the committed §3
convention.

## §5a as written (verbatim) and the pass criteria

SPEC §5a (SPEC.md:126–128):

> **5a. Pre-Phase-2 checkpoint — run *your* model for Booth's real C₀ and κc (NEW,
> required before §7T is trusted)**
> Everything about "C ~ 190, ~0.5 K kills it" is currently Breeze's numbers + Wu's
> coefficients — **not** your forward model on Booth's actual geometry, which carries a
> real (if modest) Q gap. Once §5 passes, the first real thermal checkpoint is: run the
> validated model to extract Booth's **own** C₀ and loaded κc at the tuned operating
> point, and confirm the "decisively above threshold, thin thermal margin" story holds
> with your numbers before building the thermal layer on it. If C₀ or κc land materially
> off the assumed values, the margin arithmetic — and possibly the framing — changes.
> Cost: hours, once §5 is green.

**The SPEC is NOT silent on numeric tolerances vs Booth** — the committed §5 gate
windows (`gate_targets.py`, used verbatim in the frozen gate report) are the gate. No
new tolerances are proposed, so the SPEC-silent second STOP is not triggered. The gates:

| Check | Window | Source (committed) |
|---|---|---|
| f at Booth geometry | 1.4495–1.4505 GHz (±0.5 MHz = 4 s.f.) | `F_ROW_HALF_WIDTH_HZ` |
| Q, Impedance walls | 6910.2–7049.8 (±1% of 6980) | `BOOTH_TWO_POINT_REL_TOL` |
| V_mode (global-max) | 0.40491–0.41309 cm³ (±1% of 0.409) | `BOOTH_TWO_POINT_REL_TOL` |
| Q_diel (PEC arm) | 9000–10000 | `TARGETS.q_diel_lo/hi` |
| Wall-loss fraction | 0.23–0.27; `below_resolution` ⇒ FAIL | `TARGETS.wall_loss_fraction_lo/hi` |
| F_m | [1e7, 1e8) | `F_M_ORDER_LO/HI` |
| Material identity | solve εr = 316.3 (BoothPayload check) | `TARGETS.booth` |

The §5a checkpoint quantities themselves (κc, Δf_max, ΔT_max) are **reported, not
gated**: if the Q row passes, own-model Q₀ is within 1% of 6980, so κc and the margin
numbers are pinned to ≤~1% of the composite by construction — the checkpoint's numeric
discipline is inherited from the §5 windows, no invented "materially off" threshold.
"Story holds" = ΔT_max stays order ~0.5 K (reported comparison vs the 0.567–0.725 K band).

**Pre-registered branch choices (RATIFIED via AskUserQuestion this session):**
1. **Q/wall gates judged on the Booth-faithful material branch**: tanδ = 0.0333378/316.3
   ≈ 1.0540e-4 — the `.mph`'s exact entry, = the unrounded Debye scaling of Table 1's
   1.6e-3 @ 22 GHz (Table 2's printed 1.1e-4 is the 2-s.f. round). The ~4.4% tanδ delta
   is a ~3% Q lever against a ±1% window; a like-for-like reproduction cannot stack it.
   The **canonical branch (tanδ = 1.1e-4, SPEC §2)** is solved as a companion: reported
   in the checkpoint record and it **feeds the margin report** (Phase 2 runs the SPEC §2
   model). SPEC §6's "Booth 6,980 = same tanδ" account gets a dated correction.
2. **Geometry + mph-exact tanδ live in `provenance/constants.py`** (new frozen
   dataclass + constant, full grade notes) — graded provenance facts, not solve outputs;
   the read-only rule's argue-at-STOP carve-out exercised and ratified.
3. **Minor radius = ratio-exact 2.456 mm gates**; one finest-mesh walls-on solve at the
   printed 2.46 mm is recorded as a sensitivity diagnostic.

## Solve specification

- **Geometry (gated):** recovered Booth TE01δ torus above. Provenance: Booth App. A
  (p. 29) + Table 4 ratios (p. 15) + free-DOF (major radius) pinned at x/2 by the
  supervisor `.mph` (= App. A anapole row; README record) + p. 17 non-optimisation
  statement. Recorded as `BoothTE01DeltaGeometry` in constants.py and in a new
  `refs/booth_geometry_recovery.md` with page-level citations.
- **Materials:** εr′ = 316.3 both branches; faithful branch ε″ = 0.0333378
  (tanδ = 1.05400e-4, source: `.mph` material node, in-repo; grade: supervisor-supplied
  Booth-tradition reference file, corroborated as unrounded Debye scaling of Table 1);
  canonical branch tanδ = 1.1e-4 (`STOSingleCrystal` default). μr = 1, σ_STO = 0.
- **Wall model:** Impedance BC, copper σ = 6.0e7 S/m via `COPPER` (SPEC §2/§6;
  primary now corroborated by Booth Table 3's printed 6.00E+07 — docstring note added,
  value untouched). PEC arm for the §4 split. R_s = √(ωμ₀/2σ) per SPEC §2.
- **Mesh:** `refinement_ladder(MeshConfig(dielectric_max_h_m=5e-4, air_max_h_m=2e-3),
  n_levels=5, factor=√2)` — finest level 1.25e-4 / 5e-4, the proven §2 e2e / frozen-
  anchor level; fully curved dielectric boundary (built-in for the torus circle).
  Convergence assessed over the full ladder per arm (`assess_convergence`; non-asymptotic
  ⇒ `ConvergenceError` ⇒ STOP, no sigma fabricated).
- **Study:** Eigenfrequency, search at `TARGET.f_design_hz` = 1.45 GHz, n_modes = 12.
- **Mode selection:** `TE01DeltaCriteria` — field-symmetry primary, proximity tiebreak,
  re-identified at every ladder level; never a hardcoded index. (Repo convention is
  stronger than proximity-only; consumed as committed.)
- **Q:** consumed from `q_from_eigenfrequency` = f′/(2f″) from bare `freq` — never
  re-derived, never `imag(emw.freq)` (§11 item 4, resolved).
- **Solve inventory:** 2 material branches × 2 wall arms × 5 ladder levels = 20
  eigensolves via `run_wall_loss_study`/`run_convergence_study` (cache-deduped), + 1
  printed-2.46 sensitivity solve (faithful, walls-on, finest). ~1–1.5 h wall-clock.
- **Archive:** `refs/gate_runs/<UTC>_live_comsol/` — `gate_report.json`, all §1
  `SolveRecord`s under `solves/`, finest-level raw `.mph` per gated arm under `mph/`
  (new optional `save_mph_dir` threaded through the solve path; `.gitattributes` already
  routes `*.mph` and `refs/gate_runs/**/*.npz` through LFS), plus the checkpoint record
  `booth_5a_checkpoint.md`.

## Honesty table (as it will stand after a green pass)

| Quantity | Status after pass | Basis / caveat |
|---|---|---|
| f at Booth point | **OWN-MODEL** | solve record, both branches |
| Q₀ (= Q_total, unloaded) | **OWN-MODEL** | gated on faithful branch; canonical companion reported |
| Q_diel, Q_wall, wall fraction | **OWN-MODEL** | §4 two-solve split, ladder sigmas |
| p_e at Booth point | **OWN-MODEL** | walls-on; retires the 3.14 GHz PEC-puck placeholder |
| V_mode (global/local), F_m | **OWN-MODEL** | §3 extraction |
| Field record, w_E/w_s | **OWN-MODEL** | w_s still gain-mask = STO fallback (Phase 1b pending), \|H\|² default UNRATIFIED |
| κc = f/Q_L | **COMPOSED**: own-model Q₀ × k = 0.2 | k is Breeze's; Booth thesis p. 8 is explicit that only unloaded Q is used and coupling is out of scope ⇒ k stays a flagged planning assumption — the checkpoint does NOT make κc fully own-model |
| C₀ = 190 | **PLANNING** (unchanged) | revision-note value; N assumed, g_s derived, κ_s fitted (provenance table) — a COMSOL solve cannot touch the spin side; §5a's "Booth's own C₀" is delivered only in its κc/Q arm |
| εr = 316.3, tanδ, σ_Cu | **LITERATURE INPUTS** | own-model outputs are conditional on them |
| df_cavity/dT, df_spin/dT | **LITERATURE/DERIVED §6T** | untouched (read-only this pass) |
| Booth 6980 / 0.409 cm³ | **LITERATURE anchors** | comparison targets only |

## What "validated" licenses downstream (precisely)

- **Margin report** (`report_margin.py` → `thermal/reports/q_margin_planning_point.md`):
  own-model row becomes the **headline** (canonical-branch Q₀ → Q_L = Q₀/1.2 → κc =
  f/Q_L cyclic-Hz; Booth-point walls-on p_e replaces the PEC placeholder; Δf_max/ΔT_max
  recomputed), and the cross-build composite is **kept as a labelled superseded-
  comparison row** — recommendation: replacement-as-headline with audit trail, because
  keeping the composite as headline would misstate provenance once a better rung exists,
  while deleting it would hide the supersession the report's own status notes promised.
  R5 status note retired/rewritten; byte-pins in `test_thermal_detuning.py` updated.
- **Superseded stamped artifacts:** only the margin report regenerates. The 2026-07-06
  gate run stays frozen (historical record, correct at its time); the new run dir sits
  alongside it.
- **Export bundle:** **YES, re-mint argued** — from the canonical-branch walls-on finest
  record: the first non-PEC, physics-real reference bundle (actual TE01δ at 1.45 GHz,
  impedance walls), directly serving the Maxwell-Bloch handoff and §7.T5(b). Gain-mask =
  STO-fallback flag stays. Minted AFTER the main commit (clean-parent discipline,
  e683fd6 pattern), committed separately; the old PEC bundle remains as schema example.
- **Layer A:** nominal centre = recovered geometry + canonical materials + the validated
  finest mesh level, named by record hash in the checkpoint record. Mesh-convergence
  evidence (below) is the inheritance Layer A needs.
- **`phase1_complete`: CANNOT flip true this pass even if every Booth row passes.**
  `phase1_complete = all six rows PASS` (gate.py:620) and the confinement-trend row
  requires the Breeze parametric sweep — explicitly out of scope here. Best case:
  n_pass 1→5, n_deferred 5→1, `phase1_complete` stays false with exactly one row
  outstanding, and the SPEC hunk says precisely that (the outstanding row is a
  Breeze-side sweep, not a Booth-side unknown).

## Failure branches (pre-planned; a failure is a result)

Discipline: **no geometry retuning, no tolerance widening, no branch re-picking
mid-pass.** Any gated check failing ⇒ the pass STOPS after archiving; a failure report
is committed instead of the downstream updates. In every failure case: margin report
untouched (composite stays headline), export not re-minted, xfail stays (reason updated
to point at the failure report), SPEC gets a dated finding hunk (not a status-cleared
hunk).

Diagnostics every failure report carries: full eigenspectrum + per-mode `TE01DeltaCriteria`
diagnostics at the finest level; the complete per-level convergence tables (f′, f″, Q,
deltas) both arms both branches; wall-loss split with sigmas and `below_resolution`
flag; p_e; V_mode both variants; the printed-2.46 sensitivity solve; the canonical-vs-
faithful branch deltas. Interpretive keys pre-stated: f ≫ 1.45 GHz (e.g. ~2.5–3 GHz) ⇒
geometry recovery refuted (gap #1 reopens, ask Oxborrow for Booth's TE01δ `.mph`);
f within ~1% but outside ±0.5 MHz ⇒ convergence/dimension-precision issue (sensitivity
solve discriminates); Q outside with f/V inside ⇒ loss-model issue (split + branch
deltas isolate tanδ vs wall arm); wall fraction outside [0.23, 0.27] with Q inside ⇒
the §4 window's derivation (SPEC §6's tanδ account) is indicted — report, don't widen;
`ConvergenceError` ⇒ mesh ladder not asymptotic — report ladder, no sigma, STOP.

## Wall-loss xfail (`test_booth_table_8_wall_loss_split`) — resolves THIS pass, conditionally

This pass is exactly the run the xfail was parked for (its reason: "when paper-geom
arrives… wire decompose_wall_loss… asserting TARGETS windows"; the geometry recovery is
the paper-geom substitute, and the live §4 study runs here). **If the split lands inside
both intervals:** the marker is removed DELIBERATELY and the test is rewritten to load
the archived frozen §5a records (`load_solve_record` on the committed run dir,
skip-if-LFS-pointer pattern) and assert `TARGETS.q_diel_lo <= Q_diel <= TARGETS.q_diel_hi`
and `TARGETS.wall_loss_fraction_lo <= wall_fraction <= TARGETS.wall_loss_fraction_hi` —
Booth Table 8's windows verbatim, never retuned to our solve. CI-tier (no COMSOL needed;
extraction re-runs from stored fields — the §1 re-derivation path). **If it fails:** the
xfail stays, reason updated. Like-for-like accounting documents the 1-xfail → 1-passed
(or 1-skipped-without-LFS) change in the summary.

## Mesh-convergence evidence

`run_wall_loss_study` runs each arm through the 5-level ladder; `assess_convergence`
demands monotonically shrinking deltas on f′ AND f″ and emits the finest-pair residuals
as the 1σ that `decompose_wall_loss` requires (never fabricated). The checkpoint record
tabulates, per arm per branch: mesh configs, element counts, per-level f′/f″/Q, the
delta sequence, σ_f′, σ_f″, σ_Q — beyond the prompt's two-refinement minimum. Layer A
inherits the finest level with this table as its justification.

## Baseline invariant

Fresh, before any edit: `uv run pytest` → expect **504 passed / 21 skipped / 1 xfailed**;
`uv run pytest --comsol` → expect **524 / 1 / 1**. Reconcile any drift or STOP. (The
--comsol baseline re-runs the live anchors; licence available.) Like-for-like both tiers
at the end; permitted deltas = the xfail resolution + enumerated new/updated tests below,
each named in the summary with before/after counts.

## Implementation steps

0. Baseline both tiers (above).
1. **`src/cavity/provenance/constants.py`** (ratified additions only):
   `BoothTE01DeltaGeometry` frozen dataclass (box_radius 12.28e-3, box_height 18.42e-3,
   torus_minor 2.456e-3 = x/5, torus_major 6.14e-3 = x/2, + printed_minor 2.46e-3 as the
   sensitivity literal) + `GEOM_BOOTH_TE01D`; `BOOTH_MPH_TAN_DELTA = 0.0333378 / 316.3`
   (grade notes: .mph material node; unrounded Debye of Table 1); docstring corrections:
   `NominalGeometry` (width-reading superseded for the Booth point — fields untouched),
   `Copper` (Booth Table 3 corroboration). Tests: `tests/test_provenance_booth_geometry.py`
   (ratios exact, fits-in-box, tanδ arithmetic).
2. **`src/cavity/forward_model/geometry.py`**: docstring-only correction (2.46 is the
   minor radius per Table 4; major = the free DOF pinned at x/2) — no behaviour change.
3. **`refs/booth_geometry_recovery.md`** — the recovery derivation with page-level
   thesis citations + the `.mph`-anapole identification; **`refs/comsol/README.md`**
   corrected (anapole-row identification replaces "1.82×-scaled variant"; Q = 9581.37 ↔
   Table 8 anapole 9.58E+03 cross-check recorded).
4. **`src/cavity/forward_model/runner.py`**: optional `save_mph_dir` threaded into
   `run_forward_model` (model.save before client.remove); verify custom `materials`
   propagates through `run_wall_loss_study`'s arms (fix + test if the `materials=None`
   in its common dict drops it).
5. **`src/cavity/validation/providers.py`**: wire `booth_walls_on()` +
   `wall_loss_split()` live in `LiveComsolProvider` (recovered geometry, faithful-branch
   materials for the gated payloads, ladder + cache_root + mph saving);
   **`gate_targets.py`**: update `_GAP_1`/blocked_on texts (recovery recorded; only
   confinement stays blocked). Synthetic-tier tests updated for new blocked_on wording.
6. **`src/cavity/validation/report_5a.py`** (new): deterministic checkpoint-record
   builder (recovered geometry + provenance, both branches' numbers, convergence tables,
   criteria verdicts, honesty table, §1 metadata incl. git commit). Regeneration pin test.
7. **Live run**: new `requires_comsol` test/driver runs the gate + companion branch +
   sensitivity solve, archives everything under `refs/gate_runs/<UTC>_live_comsol/`.
   `tests/test_gate_comsol.py` expectations updated (n_pass 5 / n_deferred 1 /
   phase1_complete False on a green run). **JUDGE. On any gated FAIL → failure-report
   path and STOP (report committed, downstream steps 8–10 skipped).**
8. **`test_wall_loss_gate.py`** rewritten per the xfail section (green path only).
9. **`src/cavity/thermal/report_margin.py`**: Q₀/p_e sourced from the archived §5a
   canonical-branch record (loader + fallback removed for the PEC placeholder); headline
   own-model row + composite demoted to labelled comparison; regenerate report; update
   byte-pins in `tests/test_thermal_detuning.py`.
10. **SPEC.md** minimal dated hunks (2026-07-09): §2 geometry bullet (recovery; puck
    retired at the Booth point; width = r-extent), §5a status (criteria used, verdicts,
    honesty summary, phase1_complete disposition), §6 tanδ bullet (Booth's actual model
    input was the unrounded 1.054e-4; canonical 1.1e-4 unchanged as the §2 nominal),
    §7.T4 status line (planning point superseded), §11 item 1 (gap #1 closed by document
    recovery + empirical confirmation) and item 8 (checkpoint run). Commit.
11. **Export re-mint** (green path): `export_bundle` from the canonical walls-on finest
    record → `refs/exports/<UTC>_booth5a_<hash>/`, after the main commit; separate commit.
12. Like-for-like both tiers; verbatim `git status` + `git log -1 --oneline`; summary
    per the 8-point contract.

## Out of scope (hard guards)

No Layer A DOF-space design; no sweep beyond the nominal point + ladder + the one
sensitivity solve; no surrogate work; no thermal-side changes;
`detuning.py`/`broadening.py`/`cylinder.py`/`weights.py` read-only; constants.py touched
ONLY by the ratified additions above; no opportunistic refactors; no geometry redesign —
the recovered geometry as pinned, or a stopped failure report.

## Verification

- Both pytest tiers before/after with exact counts reconciled and accounted.
- The live gate report's own verdicts are the primary verification; checkpoint record
  regeneration pinned byte-for-byte in CI.
- `report_margin` regeneration pinned; export bundle round-trip validated by the
  existing schema tests; `git check-attr` confirms LFS routing for new npz/mph paths.

## Post-implementation summary contract (deliver all eight)

1. files changed; 2. criteria used (SPEC's verbatim windows + the three ratified
branches) and per-criterion verdicts; 3. own-model vs Booth: f, Q₀ (vs 6980), p_e,
wall split — with the honesty table as built (k = 0.2 status explicit: Breeze's, Booth
thesis states no coupling); 4. mesh-convergence deltas on f and Q; 5. phase1_complete
disposition + superseded/re-minted artifacts; 6. margin-report row as committed
(own-model headline, composite demoted; Δf_max/ΔT_max recomputed); 7. xfail disposition
+ like-for-like accounting, both tiers, with commands and counts; 8. verbatim
`git status` and `git log -1 --oneline`.
