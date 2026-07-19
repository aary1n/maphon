# Layer A sweep design — DOF space, item-9 closure, and solve budget

**Status: DRAFT v2 — post-adversarial-pass, pending freeze. Nothing here is
implemented; no COMSOL runs, no SPEC edits are licensed by this doc.
Implementation start (zero-licence work) is ratified per Q1 — see
"Ratification outcomes (2026-07-14)" — while training solves stay gated by
the critical-path partition (end of OPEN QUESTIONS).**
This is the revisit the SPEC 2026-07-13 update block requires: *"Layer A
remains deferred until this law is settled — its sweep design was shaped by
the cavity-only scaling and is revisited against the turnover map"*
(`thermal/reports/q_margin_turnover.md`). The design below is deliberately
**law-agnostic** (§5 of this doc): no recorded quantity depends on which
threshold law is ratified, so the deferral reason is dissolved by
construction — whether implementation may start before Oxborrow's reply on
the findings note is a ratification question, not a design constraint
(Open Questions, Q1).

Authority chain: SPEC.md §7 (Layer A), SPEC §7-expanded (`SPEC_phase2_expanded.md`
§7.2–7.7), SPEC §11 items 9/10, the 2026-07-13 two-linewidth update block,
`docs/field_export_schema.md` v1, and the §5a re-based gate record. Where this
doc states a number not found in those sources, it is flagged inline at its
rung. Rung vocabulary: **literature-confirmed / supervisor-confirmed /
planning-assumption / TODO-trace.**

---

## 1. Nominal centre (pinned; no re-derivation)

Exactly as pinned by `docs/plans/humble-stirring-stardust.md` ("Layer A:
nominal centre = recovered geometry + canonical materials + the validated
finest mesh level") and the re-based §5a gate record:

- **Geometry:** recovered Booth TE01δ torus, `provenance.GEOM_BOOTH_TE01D` —
  box radius 12.28 mm, box height 18.42 mm, torus minor radius 2.456 mm
  (ratio-exact x/5), torus major radius 6.14 mm (x/2). Derivation:
  `refs/booth_geometry_recovery.md`.
- **Materials: CANONICAL branch** — εr′ = 316.3, tanδ = 1.1×10⁻⁴
  (`provenance.STO`; the SPEC §2 model Phase 2 runs), Cu σ = 6.0×10⁷ S/m
  (`provenance.COPPER`), impedance-BC walls. **Not** the Booth-faithful
  branch (`BOOTH_MPH_TAN_DELTA` = 1.054×10⁻⁴) — that branch exists for
  like-for-like Booth reproduction only; the branch delta (−3.10 % on Q) is
  a documented convention split, not a free parameter.
- **Gate record:** `refs/gate_runs/20260711T132705Z_rejudge/` (record hash
  `823e67969516bcf2`, as cited by the turnover map) — §5a re-based GREEN,
  5 pass / 0 fail / 1 deferred. Canonical-branch anchor values: Q₀ =
  6764.5852, Q_L = Q₀/(1+k) = 5637.1544 with k = `DELOAD_K` = 0.2,
  p_e = 0.99750.
- **Mesh:** the validated finest ladder level (dielectric 1.25×10⁻⁴ m / air
  5×10⁻⁴ m), inherited with the archived per-level convergence tables as its
  justification (humble-stirring-stardust, "Mesh-convergence evidence").

**Phase 1b rider (load-bearing).** The pinned centre is the no-crystal Booth
validation point. The sweep itself must run on **Phase 1b geometry**
(pentacene crystal sub-domain in the torus central opening, SPEC §5b) —
otherwise the gain-region columns that close item 9 are the STO fallback and
carry no G-physics (§3 below). The design therefore includes a budgeted
verification that the Phase 1b additions perturb the pinned centre only
weakly (SPEC §5b: "Booth argues it barely perturbs the mode; **verify, don't
assume**"), and the sweep centre is defined as: *the Phase 1b model whose
no-crystal limit reproduces the pinned gate-record values.* No re-derivation
of the centre is performed or permitted. *(Wording updated 2026-07-16 with
the Q9 reframe — formerly the ratified "no-bore/no-crystal limit": the
recovered Booth geometry contains a torus central opening, often termed the
bore, but no separately constructed or independently parameterised bore, its
clearance being implied by the torus major and minor radii — so the
no-crystal limit is the same statement.)*

---

## 2. DOF table

Seven sampled noise DOFs + one control. Crystal centring **eccentricity** is
listed but excluded from the axisymmetric sweep dimensions (it breaks m = 0; handled by
the §7-expanded §7.4 side-branch — see notes). d = 8 surrogate dimensions
(7 noise + 1 control), contingent on Q2 (plate definition); if the plate
stays undefined, the noise-only d = 7 degraded mode (note below the table;
budget line in §6) is the FALLBACK, not the baseline.

| # | DOF | Class | Nominal (source) | Range | Sampling distribution | Provenance rung for the range |
|---|---|---|---|---|---|---|
| 1 | Box radius | noise | 12.28 mm (`GEOM_BOOTH_TE01D.box_radius_m`) | ±25 µm (`TOL.machining_tol_m`) | trunc. Gaussian, ±3σ = band; uniform variant reported | **planning-assumption**, committed placeholder — SPEC §7-expanded §7.4 labels ±25 µm a placeholder; workshop confirmation is open ACTION 7.10.1. Do not treat as physically grounded. |
| 2 | Box height | noise | 18.42 mm (`GEOM_BOOTH_TE01D.box_height_m`) | ±25 µm | as row 1 | as row 1 |
| 3 | Torus minor radius | noise | 2.456 mm (`GEOM_BOOTH_TE01D.torus_minor_radius_m`) | ±25 µm | as row 1 | as row 1. Note the measured stiff f-lever ≈ −0.35 MHz/µm (§2 finding, printed-2.46 sensitivity solve): this DOF alone moves f by ∓ ~8.8 MHz across the band — it dominates the tuning-feasibility metric. |
| 4 | Torus major radius | noise | 6.14 mm (`GEOM_BOOTH_TE01D.torus_major_radius_m`) | ±25 µm | as row 1 | as row 1 |
| 5 | Crystal axial offset (`crystal_axial_offset_m`) | noise | **TODO-trace** — signed axial displacement of the crystal centre from the torus equatorial plane; coordinate fixed with the 2026-07-16 Q9 reframe, superseding the retired "bore radius" row (the torus central opening — often termed the bore — is not an independently parameterised geometry primitive; its clearance is implied by rows 3–4). Crystal dimensions themselves are resolved: 3 mm × 8 mm (Breeze 2017, `provenance.CRYSTAL`). | **TODO-trace** | trunc. Gaussian once band exists | **TODO-trace** (both nominal and band) |
| 6 | Crystal centring eccentricity (`crystal_eccentricity_m`) | noise, **not a sweep dim** | 0 = CENTRED — **supervisor-confirmed** (Oxborrow-verbal, in-person 2026-07-16; was planning-assumption "0 by construction", numeric nominal unchanged) | **TODO-trace** (achievable centring tolerance unknown; distinct from `machining_tol_m` per the `TolRanges` docstring — do not fold in) | n/a in the axisymmetric sweep | nominal: supervisor-confirmed (verbal, 2026-07-16); band **TODO-trace**; method itself open (§7-expanded §7.4: (a) first-order perturbation from stored axisymmetric fields → (b) bounded 3-D side-study → (c) drop with justification; decision gate = the first-order estimate, BEFORE the main sweep) |
| 7 | εr (STO) | noise | 316.3 (`provenance.STO`) | [312, 318] (`TOL.epsilon_r_min/max`) | uniform (conservative baseline); triangular-toward-nominal as sensitivity variant | **literature-anchored span**: endpoints = the committed published-anchor εr values (Wu 312 / Booth 316.3 / Breeze 318, `TARGETS.*.epsilon_r_real`); distribution shape = planning-assumption. Flag: SPEC §6 prose says "standardise on 316.3–318" while §7-expanded §7.4 and `TOL` commit [312, 318] — an internal tension to resolve at ratification (Q4), not silently re-pick. |
| 8 | tanδ (STO) | noise | 1.1×10⁻⁴ (`provenance.STO`) | [1.0, 2.3]×10⁻⁴ (`TOL.tan_delta_min/max`) | uniform (conservative baseline) | **literature-confirmed span**: measured-device effective loss, Breeze Q₀ ≈ 10,700 ↔ Wu Q₀ ≈ 4,320 (SPEC §6) — an *effective*-loss inference through the model, which is why §7.4's Bayesian re-inference is the flagged upgrade (recommended-if-time; out of this doc's scope). |
| 9 | Tuning-plate position p_tune | **control** (solved per draw, never sampled) | **TODO-trace** | [p_min, p_max] **TODO-trace** | n/a — root-solved per draw to put f̂ on f_spin = 1.4493 GHz (`TARGET.f_xz_measured_hz`) | **TODO-trace, blocking-adjacent**: no plate exists in the geometry engine, the SPEC geometry, or any repo artifact. §7.3's per-draw algorithm is unimplementable until the plate mechanism and travel are defined (Q2). |

Additional §7.4 commitments carried as-is: εr–tanδ default **independent**
(positive correlation tightens the joint tail — flagged, stretch); geometry
distributions reported under **both** truncated-Gaussian and uniform readings
("the gap is informative"); surface finish → R_s is **not** sampled (named
secondary in §7.4; listed in Open Questions Q6 rather than silently added or
silently dropped). Thermal coefficients (`DF_CAVITY_DT`, `DF_SPIN_DT`,
k/ρ/c_p, pump) are **model coefficients, not sampled noise** (§7.2) — they
enter Layer B/C and their uncertainty is error-budget channel 3, not a sweep
dimension. **No tolerance in this table is invented; every non-traceable
bound is left as TODO-trace for the ratification pass.**

**Q2 degraded mode — d = 7, FALLBACK not baseline.** If the plate stays
undefined, Layer A runs the noise-only d = 7 sweep: order-2 full basis
C(9, 2) = 36 terms, training block rescaled at the same 2.7× ≈ 97 solves
(revised budget line in §6); the surrogate is f(θ) alone with **no per-draw
root-solve** (row 9's control dimension drops out of the design), and the
sweep reports **REQUIRED PLATE AUTHORITY** — the tuning travel the plate must
supply to cover the population f-scatter (± ~15–20 MHz — planning estimate,
minor-radius lever + εr band, superseded by the sweep itself) — as an
explicit deliverable. This converts Q2 from schedule-blocking (for the sweep)
into an output that *specifies what the plate must do*; the joint (θ, p)
surrogate becomes a follow-on pass once the plate exists.

---

## 3. Item-9 closure design — the joint C₀ / κc / G regression from schema-v1 columns

**Requirement (SPEC §11 item 9, post-2026-07-13 residue):** derive the
*joint* dependence of C₀ and κc on the geometry DOFs — hazard 1 of §7.T4 now
explicitly including the carriers of G (N, g_s, V_mode, gain-region overlap)
and κs — and re-run the turnover-map check in ΔT space. **C₀ ∝ Q is not
assumed anywhere in this design;** it is a hypothesis the sweep output tests.

**Decomposition.** C₀ ∝ G²/(κc·κs). With the schema-v1 per-spin coupling
g_j = γ√(μ₀hf/2V_mode^j), V_mode^j = ∫|H|²dV/|H(r_j)|² (schema §6, the
published-framework definition), a uniform spin density n over a fixed
crystal gives

    G² = Σ_j g_j² = n · (γ²μ₀hf/2) · η_H,
    η_H ≡ ∫_gain |H|² dV / ∫_all |H|² dV,

i.e. the entire geometry dependence of G² is carried by **f × η_H**. η_H is
exactly the schema-v1 scalar `summary.magnetic_filling_factor` (verified:
`cavity/extraction/weights.py` computes `h2_gain / h2_all`, raw |H|²,
projection-independent — matching the Breeze-2017 / arXiv:2412.21166 |H|
convention).

**Schema-v1 columns that close the regression** (all in
`REQUIRED_SUMMARY_KEYS`, `cavity/export/schema.py`, globbable across bundles
per consumer 3 of `docs/plans/zesty-dazzling-kazoo.md`):

| Quantity | Column(s) | Role |
|---|---|---|
| f | `f_real_hz` | κc numerator; G² prefactor; tuning root-solve target |
| Q₀ (unloaded) | `q` (+ `f_imag_hz`) | κc via composition (below) |
| η_H | `magnetic_filling_factor` | G² geometry factor — the gain-region-overlap column item 9 names |
| V_mode | `v_mode_global_m3`, `v_mode_local_m3` | g_s bookkeeping + supporting marginal; not independently needed for C₀ once η_H is used (the per-spin sum absorbs it); cross-check identity 1/max(w_s) ↔ `v_mode_local_m3` |
| p_e | `p_e` | Q interpretation (Q_diel = 1/(p_e·tanδ) diagnostic) |
| guard | `gain_mask_is_fallback` | row admissibility (below) |
| audit | `record_hash` | row → solve traceability (SPEC §1) |
| refinement reserve / R4 check | arrays `h_complex`, `gain_region_mask`, `weights_m2`, `r_m` | recompute η under projection variants (the rider-R4 projection check is COMMITTED, not reserve — verdict below) / non-uniform spin density (reserve) without re-solving |

**Compositions (flagged, not columns):**
- **κc(θ, p) = (1+k)·f/Q₀, k = `DELOAD_K` = 0.2, cyclic-Hz FWHM.** Schema v1
  deliberately stores unloaded Q only (schema doc §7); the loaded/unloaded
  split is not a schema column. k is Breeze's planning assumption (Booth
  states no coupling). Consequence, stated not worked around: any *geometry
  dependence of the coupling itself* is invisible to Layer A — κc's sampled
  shape is exactly f/Q₀. Rung: planning-assumption, carried per draw.
- **C₀(θ, p) = C₀_planning · [f·η_H/κc] / [f·η_H/κc]_nominal**, with
  C₀_planning = 190 (`report_margin.PLANNING_C0`). This extends the committed
  import convention ("C₀ = 190 stays the IMPORTED planning cooperativity,
  never recomputed from κs" — SPEC §7.T4) to a **relative anchored law**: the
  sweep derives geometry *ratios*, never an absolute G². N (which carries
  the zone-refining doping caveat, Oxborrow-verbal 2026-07-06) cancels
  exactly: N genuinely is a sample property with no geometry dependence. The
  order-unity unmeasured orientational matrix element does **not** cancel by
  identity — it couples to the *direction* of H over the gain region, and
  its cancellation in the ratio is rider R4 (verdict below), not a
  construction. Rung of the anchoring convention: planning-assumption,
  new in this doc — ratification item (Q3).
- **κs per draw = `KAPPA_S` static planning branch** (point 1.4 MHz, band
  0.55–1.75 MHz), geometry-independent **by construction**. Item 9's
  re-scoped κs clause is therefore only *partially* closeable by this sweep:
  the EM solver cannot derive a spin-linewidth geometry dependence, and the
  one plausible coupling channel — thermal broadening κs(ΔT) — is explicitly
  out of scope (§10). Sensitivity is carried by re-running Layer C at the κs
  band edges, not by sampling κs.

**The regression itself.** Surrogates are fit to the RAW columns (ln f,
ln Q₀, ln η_H, ln V_mode, p_e — §9), and C₀/κc are composed per draw
downstream. The item-9 deliverables are then: (i) the joint sampled
distribution (C₀, κc) with its correlation structure; (ii) the regression of
ln C₀ against ln Q_L across the population — the *test* of C ∝ Q (the
fixed-G turnover calibration c = C₀/Q_L is precisely the assumption this
replaces); (iii) the turnover-map check re-run with the sweep-derived joint
law, in Δf space **and** in ΔT space (folding in the §6T coefficients — the
"turnover map in ΔT space" wording of item 9).

**Verdict: NO BLOCKING FINDING at schema level.** Schema v1 answers item 9
as written, under FOUR stated riders (R1–R4): (R1) **rows must come from
Phase 1b geometry** — bundles with `gain_mask_is_fallback: true` describe the
STO puck, not the pentacene gain region (schema §9), and are inadmissible for
the G-regression; this is a sequencing precondition (Phase 1b before the
sweep), not a schema gap; (R2) κc is available only under the flagged k = 0.2
composition — a modelled coupling port would be a schema/model *extension*,
not within item 9 as written; (R3) κs enters as a constant — see above;
(R4) **projection invariance of the anchored ratio** — rung:
planning-assumption (plausible to first order for the TE01δ axial H in the
torus central opening; **not an identity**). The orientational matrix element couples to the
DIRECTION of H over the gain region, while raw-|H|² η_H is
projection-independent by construction — so the ratio law
C₀(θ,p) = 190 × [f·η_H/κc]-ratio ASSUMES the field-direction distribution
over the crystal is draw-invariant across the DOF box. Committed zero-solve
check (not a refinement reserve): recompute η under a direction-sensitive
`SpinProjection` (the machinery behind `w_spin_per_m3`, e.g.
`axis_projected`, evaluable from the stored `h_complex` arrays; the schema
*default* is itself raw |H|²) vs raw |H|², across a handful of sweep-corner
bundles, and report the spread of the ratio law under the two projections.
If the spread is non-negligible vs the CV-gate scale (§9), the projection
choice is ESCALATED, not averaged.

---

## 4. Q-span check against the turnover map

The superseded −1/2 law plays no role in any range choice below; every
comparison is against `thermal/reports/q_margin_turnover.md`.

**Population Q_L span (first-order arithmetic from committed record values —
planning estimate, superseded by the sweep itself).** Holding geometry at
nominal and using the gate-record wall split: 1/Q₀ = p_e·tanδ + 1/Q_wall with
p_e = 0.99750 and Q_wall = 1/(1/6764.5852 − 0.99750·1.1×10⁻⁴) ≈ 26,240
(canonical record). Across the tanδ band [1.0, 2.3]×10⁻⁴:

| tanδ | Q₀ | Q_L = Q₀/1.2 |
|---|---|---|
| 1.0×10⁻⁴ | ≈ 7254 | ≈ 6045 |
| 1.1×10⁻⁴ (nominal) | 6764.59 | 5637.15 |
| 2.3×10⁻⁴ | ≈ 3738 | ≈ 3115 |

Geometry scatter at the ±25 µm placeholder moves the wall fraction at the
few-percent level (second order vs the 2.3× tanδ lever); εr moves f far more
than Q. So the sampled build population spans **Q_L ≈ 3.1k–6.0k**,
tanδ-dominated.

**Against the map:** the fixed-G crossings are Q_− = 63.19, Q_+ = 972.5 at
κs = 1.4 MHz, with the κs band moving Q_+ across [746.2, 2613]
(κs = 1.75 → 0.55 MHz). Findings:

1. **The population cannot approach the turnover.** Its floor (≈ 3115) sits
   above Q_+ at every κs band edge; even at the most adverse edge
   (κs = 0.55 MHz, Q_+ = 2613) the clearance is only ≈ 19 % in Q_L — worth
   stating, but the whole population is on the far side (κc < κs, E > 0)
   under the fixed-G calibration. No sweep range is extended to chase the
   crossing: fabrication scatter physically cannot reach it, and widening
   ranges beyond fabrication reality to visit the turnover would corrupt the
   build-population semantics of Layer A. (The turnover region is already
   covered deterministically by the map itself.)
2. **The exponent is not constant across the population** — E ≈ +0.26 at
   Q_L ≈ 3.2k rising to ≈ +0.35 at the operating point (map rows). A single
   power-law fit of margin vs Q would be wrong by construction; the empirical
   regression (§3, deliverable ii–iii) tests the map's functional form /
   reports local E, never one exponent.
3. **The crossings themselves are fixed-G objects** (c = `PLANNING_C0`/Q_L —
   the same C ∝ Q napkin assumption item 9 exists to replace). Once the
   sweep-derived joint law exists, the crossing locations are re-derived
   downstream in Layer C; the check in this section is then re-run as an
   output, not an input.
4. **Threshold distance:** under fixed-G scaling the population's C₀ floor is
   ≈ 190·(3115/5637) ≈ 105 — decisively above threshold everywhere, so
   √(C₀−1) stays smooth over the sampled space and §7.5's "Ĉ₀ near 1"
   active-learning boundary is expected to be empty (the low-margin boundary
   remains live via κc).

---

## 5. Law-agnosticism statement

Every recorded training row is **raw physics per schema v1**: f′
(`f_real_hz`), f″ (`f_imag_hz`), Q (`q`), p_e, V_mode (both variants), F_m
(both), raw energies U_E/U_H (`u_e_raw_j`, `u_h_raw_j`, `u_e_fraction`),
weight statistics (`magnetic_filling_factor`, `h_phi_energy_share`,
`spin_projection_mode`), and the audit keys — plus the full field arrays in
`fields.npz`. **No margin-law quantity is stored in any row**: no Δf_max, no
ΔT_max, no exponent, and not even C₀/κc themselves (both are downstream
compositions, §3). The threshold law enters exactly once, in Layer C
per-draw post-processing (`cavity.thermal.detuning` / `report_margin`).

**If Oxborrow amends the law** — different κs convention, a low-power κs
from Angus, a hom×inhom composition, or the injection-locked/fixed-ω rider of
§7.T4 — the consequence is a **Layer C re-run only**: solves, bundles,
training rows, and fitted surrogates are untouched. The one carve-out, stated
honestly: an amendment that changed *which raw quantities matter* (e.g.
requiring a per-draw modelled loaded-Q split rather than the k = 0.2
composition) is a schema/model extension and would require re-export or new
solves — that is a change of inputs, not of law, and nothing currently on the
table asks for it.

---

## 6. Solve-budget accounting

Budget ceiling: **O(150–300) COMSOL solves total, hard** (SPEC §7-expanded
§7.5). One "solve" = one eigenfrequency study (search 1.45 GHz, n_modes = 12,
mode ID by field symmetry) at the validated finest mesh level, walls-on,
canonical branch, one geometry point; each solve persists its SPEC-§1 record
and mints one schema-v1 bundle (= one training row).

Dimensions d = 8 (7 noise + p_tune; eccentricity excluded from the sweep
dims, §2). PCE order 2 full basis: C(8+2, 2) = **45 coefficients**; training
at ≈ 2.7× oversampling. Sparse order-3 enrichment (LARS-selected terms) fits
on the same rows — no additional solves. (Q2 degraded d = 7 fallback:
36-term basis — revised budget line below the table.)

| Block | Solves | Notes |
|---|---:|---|
| Phase 1b perturbation verification | 5 | itemized: (crystal ON / OFF at nominal) × 2 mesh levels = 4, + 1 PEC arm (crystal ON, wall-split diagnostic) = **5** — the draft's "6" over-counted by one, corrected here — the §5b "verify, don't assume" gate on the sweep centre (§1 rider) |
| Main training design (Sobol, d = 8) | 120 | 2.7× the 45 order-2 coefficients |
| Held-out validation set | 30 | independent batch, never used in fitting (CV gate, §9) |
| Active-learning reserve | 40 | GP-variance-placed near f̂ ≈ f_spin and the low-margin (large-κ̂c) boundary, per §7.5 |
| Mesh-inheritance spot-checks | 4 | 2 sweep-corner points × 2 extra refinement levels — checks the nominal-point ladder evidence transfers across the DOF box |
| Confinement trajectory (§7) | 10 | 8 walls-on trajectory points + 2 PEC-arm solves at the tight endpoint (wall-split diagnostic) |
| **Total** | **209** | **≤ 300 ceiling, ≥ 150 floor — fits with 91 in reserve** |
| Contingency: eccentricity bounded 3-D side-study | +6 | only if the zero-solve first-order perturbation estimate (from stored axisymmetric fields) demands it → 215 |

**Degraded d = 7 budget line (Q2 fallback, §2 — fallback only; the d = 8
baseline stands if the plate is defined in time):** order-2 full basis
C(9, 2) = 36 terms; training block at the same 2.7× oversampling ⇒
**97 solves** (2.7 × 36 = 97.2). All other blocks unchanged:
5 + 97 + 30 + 40 + 4 + 10 = **186** total (192 with the eccentricity
contingency). Surrogate is f(θ) alone, no per-draw root-solve; the
REQUIRED-PLATE-AUTHORITY deliverable (vs the ± ~15–20 MHz population
f-scatter — planning estimate, §2) replaces the tuning-yield metric until
the plate exists.

**Overrun discipline (pre-committed cut order, no adaptive-sampling
hand-waving):** if the CV gate fails within budget, cut in this order —
(1) drop sparse order-3 ambitions, (2) shrink the active-learning reserve,
(3) reduce held-out 30 → 20. **Never cut** the Phase 1b verification block or
the confinement trajectory (a §5 gate row). If the gate still fails at 300
solves, that is a STOP-and-report finding (surrogate inadequacy is a result),
not a licence to exceed the ceiling.

---

## 7. Confinement row (deferred §5 gate row) — folded in as a byproduct

The one deferred §5 row: "tightening toward V_mode ≈ 0.2 raises Q toward
~10,000; order-10⁷ F_m judged at this endpoint" (Breeze Table 1 anchor;
re-scoped 2026-07-11 — the order-10⁷ window lives HERE, not at the Booth
point). Committed judgment criteria (`provenance/gate_targets.py`, used
verbatim — no new windows invented here):

- monotone Q rise over ≥ `CONFINEMENT_MIN_POINTS` = 3 points ("a continuous
  confinement trend, not two unrelated points" — SPEC §5);
- endpoint Q ∈ [`CONFINEMENT_ENDPOINT_Q_LO`, `CONFINEMENT_ENDPOINT_Q_HI`] =
  [9000, 10500] at V_mode ≤ `CONFINEMENT_ENDPOINT_V_MODE_MAX_M3` = 0.22 cm³;
- F_m ∈ [`F_M_ORDER_LO`, `F_M_ORDER_HI`) = [10⁷, 10⁸) at the tightest sampled
  confinement point (anchor `TARGETS.breeze`: Q = 10⁴, V = 0.2 cm³,
  F_m = 3.6×10⁷ at εr = 318).

**Design:** a deliberate 8-point 1-D design-space trajectory from the Booth
point (V_mode ≈ 0.65 cm³) toward the Breeze confinement point — **not**
fabrication noise (±25 µm scatter cannot move V_mode ×3; the trajectory is a
separate solve block, §6). The trajectory *parameter* is an open design
choice (Q5): candidates are geometric interpolation Booth → Breeze (requires
pinning Breeze's build geometry — **TODO-trace**, no Breeze dimensions exist
in any repo artifact) or a single-lever path (box/torus proportions at fixed
f). Also open: whether the endpoint is judged at canonical εr = 316.3 or at
the anchor's own εr = 318 (`TARGETS.breeze.epsilon_r_real` exists precisely
because pairing across εr chases a phantom ~14 MHz shift — the committed
`gate_targets` rationale is consulted at implementation, not overridden
here).

**Closure condition for `phase1_complete`:** the row PASSES when all three
committed criteria above hold on the trajectory; with it green, all six §5
rows pass and `phase1_complete` flips true (gate logic: all-rows-PASS —
currently 5/0/1 per the re-judge record). Per the Booth-rebase discipline
(`project_vmode_rebase`): §5a benchmark PASS ≠ phase complete — **this
trajectory is the one outstanding item**, and it rides the Layer A budget as
a byproduct rather than a separate campaign.

---

## 8. Conventions block (pinned by construction — every consumer imports, none re-derives)

1. **Q = f′/(2f″) from the bare complex solver eigenfrequency `freq`** —
   never `imag(emw.freq)` (COMSOL realifies interface-scoped variables in
   results evaluation; SPEC §11 item 4, guarded in
   `tests/test_comsol_mph_server.py`). The imag = 0 probe reading was a
   script bug, retracted — never re-introduce.
2. **2πr axisymmetric Jacobian** on every volume integral:
   ∭ g dV = 2π ∬ g·r dr dz (SPEC §3). Export-grid node volumes are
   dV_i = 2π·r_m·weights_m2 (schema §6 trap — never node counts).
3. **Full 360° revolution for any Revolution-2D dataset** — the Booth 225°
   trap (§5a finding: COMSOL's default partial revolution, start −90°, angle
   225°, silently scaled her printed V_mode by 0.625). The repo's own
   integrals are grid-based and structurally immune; the guard applies to any
   .mph-side results-tree evaluation ever used for cross-checks.
4. **κc = f/Q_L in CYCLIC-Hz FWHM — never 2πf/Q_L** (the W20 angular-"Hz"
   trap, schema §7). **Scope:** this rule governs all Layer A rows,
   margin-law inputs, and every composition in this doc. Schema §7 itself
   defines the Maxwell-Bloch handoff κc as 2πf/Q_L in rad/s DELIBERATELY —
   that consumer-side angular convention is a documented deliberate
   conversion (schema §7), not an instance of the W20 trap (the trap is
   unlabelled angular rates printed as "Hz"). κs same convention (`KAPPA_S`;
   anchor A6 carries the 2π sibling trap). Loaded/unloaded split: **C and κc
   use loaded Q_L; F_m uses unloaded Q₀** (§7-expanded §7.3 convention
   guard); Q_L = Q₀/(1+k), k = `DELOAD_K` = 0.2, flagged planning assumption
   per draw.
5. Supporting (inherited, stated for completeness): e^{+iωt} phasors with
   Im(f) > 0 ⇔ decay; unit-total-EM-energy normalisation for exported fields;
   mode identification by field symmetry, never eigenvalue order; all
   constants imported from `provenance/constants.py`, no fresh literals.

---

## 9. Surrogate plan (per SPEC §7-expanded §7.5)

- **Primary: PCE**, order 2 full basis (45 terms at d = 8) with
  LARS-selected sparse order-3 enrichment on the same training rows. Sobol
  indices fall out of the coefficients analytically (§7.7).
- **Outputs surrogated — RAW basis:** f, ln Q₀, ln η_H, ln V_mode, p_e; one
  surrogate per output; C₀ and κc **composed** downstream per §3.
  *Deliberate deviation-in-form from §7.5's letter* (which names C₀/κc as
  surrogate outputs, predating the two-linewidth re-scope): the raw basis is
  what law-agnosticism (§5) requires; §7.5's intent — CV-gating the
  decision-relevant quantities — is honoured by evaluating the gate in
  composed C₀/κc space as well. Flagged for ratification (Q7).
- **Cross-check: GP** on the same training set; predictive variance drives
  active learning (§6 reserve) and the §7.6 channel-2 emulator interval.
- **CV gate (committed structure; numeric thresholds are planning choices,
  flagged):** LOO/k-fold Q² per output plus the 30-row held-out set. Gate
  thresholds per §7.5: f-surrogate error ≪ the tuning linewidth; C₀/κc
  errors ≪ the margin scale — operationalised as: LOO-driven per-draw
  |δΔf_max| ≤ 5 % of the 5th-percentile Δf_max, and f LOO RMSE ≤ 10 % of κc
  (≈ 26 kHz at the planning point). Both "≪" quantifications are
  **planning-assumption** rung, listed for ratification (Q8); failure path =
  active learning within budget, then the §6 overrun discipline.
- **MC layer:** 10⁴–10⁵ Sobol draws on the fitted surrogate (zero solves);
  §7.6 three-channel error budget (sampling / emulator / thermal-coefficient)
  downstream in Layer C, unchanged by this doc.

---

## 10. Explicitly out of scope

- **κs(ΔT) feedback** (thermal broadening → κs → threshold): identified
  2026-07-13, deliberately NOT implemented; needs a hom×inhom composition
  model `broadening.py` does not claim.
- **§7.T6 mitigation/materials variants** (sapphire multiblade heat sink,
  crystal capillaries) — unratified brainstorm, off critical path; likewise
  the §9 materials survey exclusion stands.
- **Observable-b prediction runs** (§7.T5(b) maser-geometry detuning
  predictions) — separate pass; this sweep only produces the field/weight
  inputs.
- **Headline use of the two-linewidth margin numbers** (11.39 MHz / 3.90 K
  planning point): UNRATIFIED pending the findings-note asks
  (`docs/q_margin_two_linewidth_findings_note.md`, drafted not sent; one-pager
  ask 7 / SPEC §11 item 10). Layer A's design does not depend on them (§5).
- **Bayesian tanδ re-inference** (§7.4 elevated) — recommended-if-time,
  separate pass; baseline uses the uniform band.
- **Forced-air convection sweep** (flagged future variant, NOT adopted —
  §7.T4 reframe), and everything in SPEC §9 (shape optimisation, cooling
  channels, loop-gap = Zangwill).
- **SPEC edits, sweep-driver implementation, any COMSOL run** — this pass is
  the design doc only.

---

## OPEN QUESTIONS (for the ratification pass)

1. **Implementation-start gating:** the law-agnostic design dissolves the
   stated reason for Layer A's deferral (§5). May implementation start before
   Oxborrow replies to the two-linewidth findings note, or does the deferral
   stand until then as a matter of process?
2. **Tuning plate (blocking-adjacent):** what is the physical mechanism
   (movable end wall? dielectric plunger?), its geometric parameterisation,
   and [p_min, p_max]? No repo artifact defines it, yet §7.3's per-draw
   algorithm — and one of the eight surrogate dimensions — depends on it.
   Population f scatter is ± ~15–20 MHz (planning estimate — minor-radius
   lever + εr band first-order arithmetic, superseded by the sweep itself),
   so plate authority directly sets the tuning-yield metric. Degraded d = 7
   fallback recorded in §2/§6.
3. **C₀ anchored-ratio convention (§3):** ratify
   C₀(θ,p) = 190 × [f·η_H/κc]-ratio as the per-draw extension of the
   committed import convention (absolute G² reported as diagnostic only).
4. **εr band tension:** [312, 318] (`TOL`, §7.4, anchor-εr span) vs SPEC §6
   prose "standardise on 316.3–318" — which governs the sampled band?
5. **Confinement trajectory lever (§7):** geometric interpolation Booth →
   Breeze (requires pinning Breeze's build geometry — currently TODO-trace)
   vs a single-lever proportional path; and endpoint-judgment εr branch
   (316.3 canonical vs the anchor's 318).
6. **Surface finish → R_s:** stays unsampled per §7.4 ("secondary") — confirm,
   or add an effective-σ_Cu DOF (would raise d to 9 and the order-2 basis to
   55 terms; budget still fits).
7. **Surrogate output basis:** raw (f, ln Q₀, ln η_H, …) with downstream
   composition, vs §7.5's literal C₀/κc list (§9 deviation flag).
8. **CV-gate numerics:** the 5 %-of-5th-percentile-Δf_max and 10 %-of-κc
   quantifications of §7.5's "≪" (planning-assumption rung).
9. **Crystal placement + centring tolerance (§2 rows 5–6)** *(renamed
   2026-07-16 from "bore nominal + centring tolerance" — the recovered Booth
   geometry contains a torus central opening, often termed the bore, but no
   separately constructed or independently parameterised bore; crystal
   dimensions are resolved, `provenance.CRYSTAL`, Breeze 2017 3 × 8 mm)*:
   the crystal axial-offset nominal + band (signed axial displacement of the
   crystal centre from the torus equatorial plane), the achievable lateral
   centring tolerance, and sign-off on the eccentricity decision ladder
   (first-order estimate → bounded 3-D → drop). **Partial resolution
   (Oxborrow-verbal, in-person 2026-07-16): eccentricity nominal = CENTRED —
   supervisor-confirmed, numeric nominal unchanged; tolerance band still
   open; Q9 remains unresolved.**
10. **Machining tolerances:** the ±25 µm placeholder (`TOL.machining_tol_m`)
    still awaits the workshop/Oxborrow numbers (§7-expanded ACTION 7.10.1) —
    the DOF table re-issues on receipt; no other row changes.
11. **Crystal permittivity for Phase 1b:** the repo carries only "εr < 5"
    (Breeze 2017) — a bound, not a value. The Phase 1b sub-domain needs a
    graded constant (TODO-trace) before the sweep-centre verification block
    can run. **Resolution (literature trace, 2026-07-17): point εr = 3.0 =
    round central planning value (band mid 3.25; anthracene isotropic mean
    3.13), band [2.4, 4.1] — principal OPTICAL permittivities of
    crystalline anthracene, εxx 2.42 / εyy 2.90 / εzz 4.07 (±0.05),
    Cummins & Dunmur 1974, J. Phys. D: Appl. Phys. 7, 451 (immersion
    method — refractive-index-derived; Zotero WNLM2C8X), carried across a
    three-layer planning-tier inference chain: chemical-class analogy
    anthracene → p-terphenyl; optical → static/microwave extrapolation,
    justified only by both crystals being nonpolar rigid aromatics (no
    orientational/Debye contribution expected between optical and
    microwave); consequence of either layer failing bounded by Breeze 2017
    <1% electric filling. Below the Breeze "εr < 5" bound by construction.
    Negative space: direct p-terphenyl static/microwave permittivity NOT
    FOUND (trace 2026-07-17); Selvakumar et al. 2014 (J. Mol. Struct.
    1056–1057, 152; Zotero KCDCRN4C) examined and REJECTED — εr 5760 @
    1 kHz is electrode/Maxwell–Wagner polarization per the paper's own
    attribution, unusable at any grade. First non-mock SentinelResolution:
    `cavity.sweep.resolutions.RESOLUTION_Q11`; the band rides the payload
    unconsumed (machine-readable metadata for a future Phase 1b εr
    sensitivity check, mirroring Q9's band-carrying pattern). Q2/Q9
    unchanged and still blocking. RESOLVED (planning grade).**
12. **k = 0.2 across the population:** the de-loading constant is applied
    uniformly per draw (rider R2, §3) — confirm this stands until a coupling
    model exists, and that no per-draw k scatter is wanted in baseline.

### Critical-path partition (what actually gates solves)

§5 dissolves the law-deferral, but the sweep is now gated on **Phase 1b
DEFINITION**: rider R1 (admissible rows must come from Phase 1b geometry,
§3) + Q2 (plate) + Q9 (crystal placement nominal/band) + Q11 (crystal εr) together mean
**zero training solves can run until those resolve.** Partition of the
twelve questions:

- **SCHEDULE-BLOCKING** (external input or a design decision required
  before any training solve): **Q2** (for the baseline d = 8 (θ,p) sweep;
  the d = 7 degraded mode, §2/§6, is the pressure-relief fallback), **Q9**,
  **Q11**. **Q5**'s Breeze-geometry branch joins this class only if the
  interpolation lever is chosen. **Q10** blocks nothing (the DOF table
  re-issues on receipt; no other row changes) but rides the same Oxborrow
  channel.
- **RATIFICATION-ONLY** (resolvable by the ratifier, no external
  dependency): Q1, Q3, Q4, Q6, Q7, Q8, Q12.
- **Routing:** Q2 and Q9 route to Oxborrow — add them to the findings-note
  asks or the next touchpoint. Q11 is first a literature trace (the
  p-terphenyl host εr is published); escalate only if the trace fails.
- **Consequence, stated plainly:** implementation — driver code, schema
  plumbing, design-matrix generation — can start now at zero licence cost;
  solves cannot.

---

## Ratification outcomes (2026-07-14)

Rulings from the adversarial/ratification pass. Question texts above stand
as drafted; status is recorded here.

- **Q1 — RESOLVED.** Implementation starts now (zero-licence work); solves
  are gated on Phase 1b definition regardless (critical-path partition),
  which forces the Oxborrow exchange before any licence burn. The process
  concern is satisfied by construction.
- **Q2 — OPEN** (schedule-blocking for the baseline (θ,p) sweep; d = 7
  degraded fallback recorded in §2/§6; routes to Oxborrow).
- **Q3 — RESOLVED.** Anchored-ratio convention APPROVED, contingent on
  rider R4 (§3 projection-invariance check). Absolute G² reported as
  diagnostic only.
- **Q4 — RESOLVED.** TOL [312, 318] governs (committed constant,
  anchor-derived endpoints); SPEC §6 prose "standardise on 316.3–318" is the
  stale artifact — a SPEC prose fix is queued for a later SPEC pass; SPEC is
  not edited here.
- **Q5 — OPEN** (the Breeze-geometry branch is schedule-blocking only if
  the interpolation lever is chosen).
- **Q6 — RESOLVED.** R_s stays unsampled per §7.4 "secondary"; revisit only
  if the sweep's wall-fraction diagnostics argue otherwise.
- **Q7 — RESOLVED.** Raw surrogate basis APPROVED; §7.5's intent honoured
  via the composed-space CV gate (§9).
- **Q8 — OPEN** (a numeric planning choice, deferred to the implementation
  plan). *2026-07-19: RESOLVED — see the 2026-07-19 addendum.*
- **Q9 — OPEN** (schedule-blocking; routes to Oxborrow).
- **Q10 — OPEN** (blocks nothing; rides the Oxborrow channel).
- **Q11 — OPEN** (schedule-blocking; literature trace first, escalate only
  on failure). *2026-07-17: RESOLVED (planning grade) — trace executed,
  direct value NOT FOUND, anthracene-analogy planning value ratified; see
  the resolution record in the question text above.*
- **Q12 — RESOLVED.** Uniform k = 0.2 per draw, no scatter, per the
  committed convention.

---

## Addendum — 2026-07-18 geometry re-base (Wu ring): DOF-table re-parameterisation + Q13

Dated record; nothing above is edited — the §2 table and the 2026-07-14
ratification outcomes stand as the record of their date. Changeset of record:
SPEC.md dated revision block 2026-07-17/18 (Oxborrow-WRITTEN re-base,
2026-07-17); implementation plan `docs/plans/plan-checkpoint-spec-zany-pizza.md`.

- **Rows 1–4 re-parameterised** — the modelled build is now the Wu STO ring
  (`provenance.GEOM_WU_STO_RING`): rows 1–3 = `box_radius_m` (14.0 mm, Fig. 6
  caption — the 28-mm-nominal pipe-fitting caveat rides the provenance string),
  `sto_outer_radius_m` (6.0 mm), `sto_inner_radius_m` (2.025 mm), each keeping
  the ±25 µm `TOL.machining_tol_m` band at its unchanged planning-assumption
  rung; row 4 = `sto_height_m`, the **Q13 print fork {8.5, 8.6} mm**
  (`SENTINEL_Q13`, a `ForkTrace` machine-reading `provenance.STO_HEIGHT_FORK`;
  8.6 evidence-favoured, never silently selected; NO band exists
  pre-resolution — post-resolution band = payload override or nominal ±
  machining tol, the Q9-branch mirror in `materialise_dims`).
- **The former `box_height_m` noise row is DELETED, not renamed**
  (invalidate-don't-rename discipline; the bore-radius row is the precedent):
  the quantity became the control — p_tune IS the box internal height (piston
  position, metres; Q2 re-scope: mechanism supervisor-written 2026-07-17 and
  in print, travel band STILL OPEN, asked by email 2026-07-18). As-operated
  nominal 15 mm recorded at `GEOM_WU_STO_RING.box_internal_height_asoperated_m`;
  row 9's "no plate exists in the geometry engine" is superseded — the engine
  now represents the piston, while the Q2 licence gate still refuses every
  real solve.
- **Row 5 context (Q9, still OPEN):** for the Wu build the crystal-in-bore is
  real and its 3 × 8 mm dims re-grade to PLANNING-ASSUMPTION with the
  cross-build-transfer flag (five Wu-side ~4 mm indicators; SPEC §5b) — the
  table's "dimensions themselves are resolved" sentence reads Booth-context
  only from this date.
- **Row 8 band narrows mechanically:** `TOL.tan_delta_max` 2.3e-4 → 1.4e-4
  (gap #3 CLOSED — Wu's k = 1 STATED in print ⇒ Q₀ = 7,200; SPEC §6 + §11
  item 3; the row's "Wu Q₀ ≈ 4,320" quote is the assumed-k-era reading).
- **Q13 — OPEN** (schedule-blocking in BOTH design modes — D8:
  Q2+Q9+Q11+Q13, D7: Q9+Q11+Q13; the unresolved fork exits as a named
  refusal via the design blocker filter, not a sampling TypeError; routes to
  Oxborrow written reply or a caliper, spacer dims on the same caliper list).

---

## Addendum — 2026-07-19: sweep-centre re-definition (Wu build) + Q8 numbers

Dated record; nothing above is edited.

- **Sweep centre re-defined for the Wu build.** §1's pinned centre
  (Booth gate record `823e67969516bcf2`) remains the record of its date
  and the §5a solver-correctness anchor. From this date the sweep centre
  is: *the Wu Phase 1b model (crystal + spacer sub-domains,
  `GEOM_WU_STO_RING` nominals, canonical materials) whose no-crystal
  limit reproduces the W2-validated Wu anchor* — where the W2 anchor
  record does not yet exist (licence-session follow-on; W2 windows
  drafted, see `docs/w2_wu_anchor_windows.md`). No training solve may
  cite the Booth centre as the Wu sweep centre. The centre_check pinned
  record remains Booth-build (its 2026-07-18 docstring note); the
  Wu-build centre record is created by the first W2-passing solve.
- **Q8 re-expressed at the Wu operating point (definitions unchanged,
  ratified 2026-07-19):** f LOO RMSE ≤ 10 % of κc = 10 % × 402.6 kHz ≈
  40 kHz (κc = f/Q_L, literature at the stated k = 1; supersedes the
  Booth-era "≈ 26 kHz at the planning point" figure, which was 10 % of
  the composed 257 kHz). The |δΔf_max| ≤ 5 % of the 5th-percentile
  Δf_max rule is law-agnostic and stands as written. Q8 status:
  RESOLVED at these numbers (user-ratified 2026-07-19), subject only to
  the standing failure path (active learning within budget, then §6
  overrun discipline).
