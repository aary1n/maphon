# Layer A implementation plan — ZERO-LICENCE tier (L1–L5)

**Status: RATIFIED 2026-07-15 (one correction + three riders — see Ratification
record at the end). Implementation proceeds on this document.**

Authority: `docs/plans/layer_a_sweep_design.md` (DRAFT v2 + 2026-07-14 ratification
outcomes) is the plan of record; SPEC.md §7, SPEC_phase2_expanded.md §7.2–7.7,
`docs/field_export_schema.md` v1. Q1 RESOLVED — zero-licence implementation starts;
training solves stay gated on Q2/Q9/Q11 (critical-path partition). This plan adds
no design quantity; where it must invent an implementation detail, the invention is
flagged in §"Invented assumptions" below.

---

## Context

Layer A (static forward UQ: DOF sweep → surrogate → C₀/κc population) was deferred
until the two-linewidth law settled; the design doc dissolved that deferral by
making the design law-agnostic, and the 2026-07-14 ratification pass resolved Q1:
implementation may start now at zero licence cost. Zero training solves can run
until Phase 1b definition resolves (Q2 plate, Q9 bore, Q11 crystal εr) — so this
tier builds the entire pipeline against a mock solve backend, with the Q2/Q9/Q11
gate **enforced in code, not convention**: the machinery hard-refuses to emit or
execute solve-ready work while any TODO-trace sentinel is unresolved. The outcome:
when the sentinels resolve, the licensed sweep is a data change, not a code change.

---

## Scope guard (constraints, restated as commitments)

- **Zero COMSOL solves.** The mock/dry-run tier governs; nothing in this pass
  touches a licence. `--comsol` wiring exists but its backend refuses while
  sentinels are unresolved.
- **`src/cavity/` physics modules read-only.** No edit to `forward_model/`,
  `extraction/`, `export/`, `thermal/`, `validation/`, `provenance/`. In
  particular: **no Phase 1b geometry** (no bore/crystal in
  `forward_model/geometry.py` — that is SPEC §5b work, a separate licensed pass;
  the ComsolBackend additionally guards Phase 1b solve specs with a
  NotImplemented refusal naming §5b).
- **Pinned centre import-only** (gate record `823e67969516bcf2`,
  `refs/gate_runs/20260711T132705Z_rejudge/`): Q₀ = 6764.585235432756 is read from
  `checkpoint_manifest.json → branches/canonical/wall_loss/q_total`; no
  re-derivation anywhere; a pin test re-reads the record and asserts equality.
- **Conventions block (§8) imported, never re-derived:** κc = f/Q_L cyclic-Hz via
  the existing `cavity.thermal.broadening.resonance_linewidth_hz` (single source);
  Q consumed from the bundle `summary.q` (never recomputed from interface
  scalars); every volume integral through
  `cavity.extraction.quadrature.axisymmetric_volume_integral` (2πr Jacobian);
  no `.mph` results-tree evaluation anywhere in this tier (convention 3 has no
  instance to guard); all constants from `cavity.provenance.constants`, no fresh
  physics literals.
- **Places where the implementation needs a convention §8 does NOT pin** are
  flagged in their own section below — none is silently picked.

---

## Module map — files created / modified

**New files (8 source + 8 test):**

| File | L-item | Role |
|---|---|---|
| `src/cavity/sweep/dofs.py` | L1 | DOF table as code: rung vocabulary, TODO-trace sentinels, resolution machinery |
| `src/cavity/sweep/design.py` | L1 | Sobol design-matrix generation, d=8 / d=7 modes, block ledger, solve-ready refusal |
| `src/cavity/sweep/backend.py` | L2 | `SolveBackend` protocol; `MockBackend`; licence-gated `ComsolBackend` |
| `src/cavity/sweep/driver.py` | L2 | Per-draw pipeline, raw-rows store, CLI (`python -m cavity.sweep.driver`) |
| `src/cavity/sweep/compose.py` | L3 | Item-9 compositions (κc, f·η_H, anchored C₀), derived artifacts, R4 projection check |
| `src/cavity/sweep/centre_check.py` | L5 | Pinned-centre import + Phase 1b 5-solve verification block (sentinel-gated) |
| `src/cavity/surrogate/pce.py` | L4 | PCE multi-index basis, input standardisation, LSQ fit, analytic LOO, Q² |
| `src/cavity/surrogate/cv_gate.py` | L4 | Composed-space CV gate carrying the Q8 thresholds (advisory until ratified) |

Tests: `tests/test_sweep_dofs.py`, `test_sweep_design.py`, `test_sweep_backend.py`,
`test_sweep_driver.py`, `test_sweep_compose.py`, `test_sweep_centre_check.py`,
`tests/test_surrogate_pce.py`, `test_surrogate_cv_gate.py`.

**Modified files (2, docstring + re-exports only):**
`src/cavity/sweep/__init__.py`, `src/cavity/surrogate/__init__.py` — replace the
"Not yet implemented (Phase 2)" stubs with the implemented-surface docstring and
public re-exports. `src/cavity/mc_yield/__init__.py` untouched (Layer C is not
this tier).

---

## L1 — Design-matrix generation (`sweep/dofs.py`, `sweep/design.py`)

**`dofs.py`:**
- `Rung` enum = the design doc's vocabulary verbatim: `LITERATURE_CONFIRMED`,
  `SUPERVISOR_CONFIRMED`, `PLANNING_ASSUMPTION`, `TODO_TRACE`.
- `TodoTrace` frozen dataclass: `question_id` ("Q2" | "Q9" | "Q11"),
  `description`, `routes_to` ("Oxborrow" / "literature trace"). Used as the value
  slot wherever the design doc says TODO-trace.
- `DofSpec` frozen dataclass: `name`, `kind` (NOISE | CONTROL |
  NOISE_NOT_A_SWEEP_DIM for row 6), `nominal: float | TodoTrace`,
  `band: tuple[float, float] | TodoTrace`, `distribution`
  (TRUNC_GAUSSIAN_3SIGMA | UNIFORM | TRIANGULAR_VARIANT | CONTROL_ROOT_SOLVED),
  `nominal_rung`, `band_rung`, `provenance` (source-constant path string).
- `LAYER_A_DOFS`: the 9-row §2 table. Nominals/bands imported from
  `provenance.GEOM_BOOTH_TE01D` (rows 1–4), `TOL.machining_tol_m` (±25 µm bands,
  rung PLANNING_ASSUMPTION per §7.4 placeholder/ACTION 7.10.1),
  `TOL.epsilon_r_min/max` = [312, 318] (Q4 ruling: TOL governs),
  `TOL.tan_delta_min/max` = [1.0, 2.3]×10⁻⁴, `STO` nominals. Row 5 (bore radius):
  nominal and band both `TodoTrace("Q9")`, floor note = crystal radius 1.5 mm
  (`provenance.CRYSTAL`). Row 6 (bore eccentricity): NOISE_NOT_A_SWEEP_DIM, band
  `TodoTrace("Q9")` (centring tolerance distinct from `machining_tol_m` per the
  `TolRanges` docstring — never folded in). Row 9 (plate p_tune): CONTROL, nominal
  and [p_min, p_max] both `TodoTrace("Q2")`.
- `DofResolution` machinery: `resolve(dof_name, nominal, band, rung, provenance)`
  produces a resolved table; **refuses** `rung == TODO_TRACE` and refuses to
  resolve a DOF that is not a sentinel (no silent re-picks of committed rows).
  This is the only path by which ratified Q2/Q9/Q11 numbers enter later.
- `unresolved_sentinels(mode)` → the open question IDs blocking that mode
  (d=8 baseline: Q2+Q9+Q11; d=7 degraded: Q9+Q11 — the fallback relieves only Q2,
  because bore radius, row 5, is one of the seven noise dims and rider R1 makes
  Phase 1b geometry a precondition for admissible rows regardless).

**`design.py`:**
- `DesignMode` enum: `BASELINE_D8` (7 noise + p_tune) / `DEGRADED_D7`
  (noise-only, recorded FALLBACK not baseline — §2/§6).
- `BudgetLedger`: the §6 block table as committed constants —
  d=8: centre-verification 5, training 120, held-out 30, AL reserve 40, mesh
  spot-checks 4, confinement 10, total 209 (+6 eccentricity contingency);
  d=7: training 97, total 186. Ceiling ≤ 300 / floor ≥ 150 asserted; a design
  request exceeding the ceiling refuses (the §6 overrun cut order is quoted in
  the refusal message, not automated). Block counts are imported verbatim from
  the committed table (120, 97) — not re-derived from 2.7× arithmetic (the doc's
  own rounding: 2.7×45 = 121.5 → committed 120; 2.7×36 = 97.2 → committed 97).
- `generate_design(mode, block, *, seed, geometry_distribution, eps_r_variant)`:
  scrambled `scipy.stats.qmc.Sobol` (scipy ≥ 1.10, already a dependency) in
  [0,1]^d with pinned seed (SPEC §1), transformed per-DOF via inverse CDF —
  `scipy.stats.truncnorm` for rows 1–4 (±3σ = band, truncation at band edges)
  with the uniform variant switchable and reported ("the gap is informative",
  §7.4); uniform for εr/tanδ; triangular-toward-nominal (peak 316.3, endpoints
  [312, 318]) as the εr sensitivity variant. Returns a `DesignMatrix` carrying
  draws, mode, block, seed, per-DOF resolution provenance, and a design-row hash
  per draw (audit; distinct from the solve `record_hash`).
- **The Q2/Q9/Q11 gate in code:** `DesignMatrix.solve_rows()` — the only exit to
  anything executable — raises `UnresolvedTodoTraceError` naming the unresolved
  question IDs if any DOF the mode requires still carries a sentinel. Shape-only
  draft matrices for the mock tier come from `mock_resolutions()`, whose values
  are marked `mock=True` end-to-end and are **refused by `solve_rows()`
  unconditionally** — a test double can exercise the pipeline's shape but can
  never be serialised as solve-ready.

Reuse: `scipy.stats.qmc`, `provenance.constants` (all values), no new deps.

---

## L2 — Solve-driver scaffolding (`sweep/backend.py`, `sweep/driver.py`)

**`backend.py`:**
- `SolveBackend` protocol: `solve(spec: DrawSolveSpec) -> ForwardModelResult`-shaped
  result (record + extraction), where `DrawSolveSpec` = geometry + materials +
  study + mesh derived from one design row (θ → `CavityGeometry` torus branch off
  `GEOM_BOOTH_TE01D`, canonical materials branch εr′ 316.3 / tanδ 1.1×10⁻⁴ nominal
  with sampled overrides, walls-on, search 1.45 GHz, n_modes = 12, validated
  finest mesh — all per §1/§6).
- `MockBackend`: mints a synthetic `SolveRecord` whose `FieldSample` is built from
  the existing closed-form machinery (`cavity.validation.analytic_fields.te011_fields`
  on a structured grid), with smooth θ-dependent parameter maps for f″/amplitudes
  so downstream surrogate smoke tests see draw-to-draw variation. Every mock
  record/bundle is labelled mock in `status_notes` semantics (and mock bundles
  already carry `gain_mask_is_fallback: true` → inadmissible for the
  G-regression by the existing schema §9 guard — the admissibility plumbing gets
  exercised for free).
- `ComsolBackend`: thin wrapper over the existing
  `forward_model.runner.run_forward_model` (persistence/cache/`save_mph_dir`
  included). Its **constructor** refuses (`UnresolvedTodoTraceError`) while
  `unresolved_sentinels()` is non-empty — the licence gate is in code, upstream
  of any client connection. Phase 1b solve specs additionally refuse with a
  NotImplemented error naming SPEC §5b (geometry engine has no bore/crystal;
  building it is not licensed by the design doc).

**`driver.py`:**
- `run_sweep(design, backend, out_root)`: per draw — geometry build → eigensolve
  (backend) → `cavity.export.writer.export_bundle` → schema-v1 RAW summary-row
  extraction (`REQUIRED_SUMMARY_KEYS` from `cavity.export.schema`, exactly) →
  append to the raw-rows store. Row = REQUIRED_SUMMARY_KEYS + design metadata
  (θ values, mode, block, draw index, seed, design-row hash). **Raw schema-v1
  quantities ONLY**: the row writer holds an explicit deny-list (no `kappa_c`,
  `c0`, `delta_f_max`, or any derived key) and refuses otherwise — enforced by
  construction and by test.
- Admissibility guard: `gain_mask_is_fallback` rides every row (rider R1);
  `record_hash` rides every row (SPEC §1 audit).
- CLI: `python -m cavity.sweep.driver` with `--mock` (dry-run tier, exercises the
  full pipeline shape end-to-end on a small design) and `--comsol` (mirrors the
  conftest flag convention; constructs `ComsolBackend`, which refuses today).

Reuse: `run_forward_model`, `solve_fingerprint`/`solve_hash`/`SolveRecord`
(persistence), `export_bundle`, `load_bundle`/`validate_bundle`,
`REQUIRED_SUMMARY_KEYS`, `analytic_fields`, conftest `--comsol` pattern.

---

## L3 — Item-9 composition plumbing (`sweep/compose.py`)

Consumes raw schema-v1 columns; composes downstream; **derived quantities are
never persisted as raw rows** (separate `derived_rows` artifact namespace, and
the raw-row deny-list above is the second lock).

- `kappa_c_hz(f_hz, q0)` = delegated to
  `broadening.resonance_linewidth_hz(f_hz, q0 / (1 + DELOAD_K))` — i.e.
  (1+k)·f/Q₀ in cyclic-Hz FWHM, single-sourced through the committed helper
  (§8 convention 4; k = `DELOAD_K` = 0.2 per Q12, uniform per draw, no scatter).
- `g2_relative(f_hz, eta_h)` = f·η_H, with η_H = the raw
  `magnetic_filling_factor` column (verified `h2_gain/h2_all`,
  projection-independent).
- `c0_anchored(f, eta_h, kappa_c, anchor)` =
  `PLANNING_C0` × [f·η_H/κc] / [f·η_H/κc]_anchor (Q3 APPROVED convention,
  contingent on rider R4). `AnchorPoint` is constructed from a bundle and
  **refuses `gain_mask_is_fallback: true` anchors** unless an explicit
  `diagnostic_only=True` override is passed (provenance-refusal pair); the
  anchor's `record_hash` and κs branch ride every derived row.
- `g2_absolute(...)`: the schema §6 recipe (g_j = γ√(μ₀hf/2V_mode^j),
  volume-weighted, dV = 2πr·weights), labelled DIAGNOSTIC ONLY per Q3.
- Derived artifact: `DerivedRow` carries values **plus** its composition
  convention explicitly — k, anchor record_hash, κs branch value, projection
  mode — serialised alongside, never bare numbers.
- **Rider R4 projection-invariance check (COMMITTED, not reserve):**
  `projection_invariance_report(bundle_dirs)` recomputes η_H from the stored
  `h_complex`/`gain_region_mask`/`weights_m2`/`r_m` arrays under
  `SpinProjection.isotropic_h2()` vs `axis_projected` (existing
  `extraction.weights.projected_h2_density` machinery;
  `axisymmetric_volume_integral` for every integral), across a set of
  sweep-corner bundles, and reports the spread of the anchored-ratio law under
  the two projections. If the spread is non-negligible vs the CV-gate scale
  (§9/Q8), the report flags ESCALATE — it never averages. Committed test: an
  axially-dominated synthetic mode → spread ≈ 0; a synthetic mixed-component
  field → non-zero spread detected and escalation flagged.
- Supporting committed test (from the §3 table's cross-check column): the exact
  identity 1/max(`w_spin_per_m3`) = η_H × `v_mode_local_m3` under the isotropic
  projection, asserted on mock bundles.

κs is **not** composed here (rider R3: static planning branch, enters in
Layer C); the only κs appearance in this tier is in the CV-gate's composed
Δf_max evaluation, imported from `provenance.KAPPA_S`.

---

## L4 — Surrogate scaffolding (`surrogate/pce.py`, `surrogate/cv_gate.py`)

**`pce.py`:**
- Total-degree multi-index generation for arbitrary (d, order); order-2 full
  basis = C(d+2, 2) terms — **45 at d = 8, 36 at d = 7**, pinned in tests.
  (LARS order-3 sparse enrichment: index generation is included by generality;
  the LARS selection loop is deferred to the licensed pass — it has no
  meaningful mock exercise. Stated, not silent.)
- Input standardisation: per-DOF isoprobabilistic map to U(0,1) via each DOF's
  own CDF (truncnorm / uniform / triangular), then orthonormal shifted-Legendre
  tensor basis on the cube. (Invented implementation assumption — flagged below.)
- Fit: least squares (`numpy.linalg.lstsq`); analytic LOO residuals via the hat
  matrix (verified against brute-force refit in test — second code path); Q²
  per output; deterministic under pinned inputs.
- Outputs surrogated — RAW basis per Q7 (resolved): f, ln Q₀, ln η_H,
  ln V_mode (both variants, supporting), p_e. One surrogate per output. C₀/κc
  are never surrogate outputs.
- Sobol-from-coefficients and the GP cross-check/active-learning layer are
  **out of this tier** (nothing to actively learn on mock rows); §9 unchanged.

**`cv_gate.py`:**
- `GateThresholds` dataclass carrying the two Q8 numbers as explicit fields with
  `rung = PLANNING_ASSUMPTION` and `ratified: bool = True` (default cites the
  2026-07-15 R1 ruling). An unratified instance is constructible and reports
  **ADVISORY**, never a bare PASS/FAIL (the mechanism survives for future
  re-opens; exercised in test). Every gate report prints the κs branch it was
  evaluated under.
- Composed-space evaluation (honouring §7.5's intent per the Q7 ruling): from
  the raw surrogates' LOO/held-out predictions, compose per draw
  κ̂c = `compose.kappa_c_hz`, Ĉ₀ = `compose.c0_anchored`, then
  Δf̂_max = `cavity.thermal.detuning.delta_f_max_hz(Ĉ₀, κ̂c, KAPPA_S.kappa_s_hz)`
  (existing committed law implementation — reused, not re-derived), and evaluate:
  per-draw |δΔf_max| vs threshold 1 and f LOO RMSE vs threshold 2.

---

## ⚖ Q8: CV-gate numerics — RATIFIED 2026-07-15 (rider R1; rung planning-assumption)

§7.5's gate says surrogate error "≪ the tuning linewidth" (f) and "≪ the margin
scale" (C₀/κc). Proposed quantifications, with the computation behind each
number (all inputs are committed record/constants values; scoping MC: 2×10⁶
draws, tanδ ~ U[1.0, 2.3]×10⁻⁴ through the gate-record wall split
1/Q₀ = p_e·tanδ + 1/Q_wall with p_e = 0.99750, Q_wall = 26 244 from
Q₀ = 6764.5852; f = f_spin = 1.4493 GHz per draw; fixed-G planning scaling
C₀ = 190·Q_L/5637.1544; Δf_max = ((κc+κs)/2)√(C₀−1), κs = 1.4 MHz. This
computation reproduces the design doc's own §4 table — Q₀ endpoints 7254/3738,
C₀ floor 105, planning-point Δf_max 11.391 MHz — before extending it):

**Gate 1 (margin arm): per-draw LOO/held-out |δΔf_max| ≤ 5% of the population
5th-percentile Δf_max**, both recomputed from the sweep's own composed population
at the committed κs point branch (1.4 MHz), with the κs band edges reported
alongside. Pre-sweep planning quantification: P5(Δf_max) = **9.571 MHz** →
threshold **479 kHz**; at the conservative κs-lo edge (0.55 MHz)
P5 = 5.183 MHz → 259 kHz, reported not binding (binding the gate at the most
extreme unratified κs branch would let that branch drive solve spend).

*Why 5%, argued:* (i) the decision-relevant scale is the P5 quantile, not the
mean (§7.6: the tail is what a tolerance budget acts on) — so the gate scale is
P5, and 5%-of-P5 caps surrogate-induced bias on the reported worst-off margin at
one part in twenty; (ii) that keeps the surrogate channel an order below the
physics bands carried on the same number — the κs band moves P5 by −46%/+19%
(5.18–11.38 MHz) and the §7.6 thermal-coefficient envelope spans ≈1.8–5.8 K
around 3.90 K (≈ −54%/+49%) — so a gate-passing surrogate cannot flip any
decision the pipeline reports, while a materially tighter gate (1%) would spend
active-learning solves suppressing a channel already invisible under channel 3;
(iii) error-transfer arithmetic (computed): ∂lnΔf_max/∂lnκc = κc/(κc+κs) =
0.155 (planning point) to 0.245 (worst-off draw); ∂lnΔf_max/∂lnC₀ =
C₀/(2(C₀−1)) = 0.503–0.505 — so 5% composed admits ~10% error in Ĉ₀ or
~20–32% in κ̂c per draw, comfortably achievable for an order-2 PCE over a box
where the entire Q_L response spans ×1.94 quasi-linearly in ln-space; the gate
still binds meaningfully because it is evaluated in composed space and catches
correlated per-output errors the raw view misses (the Q7 ruling's intent).

**Gate 2 (tuning arm): f-surrogate LOO RMSE ≤ 10% of the population-minimum
κ̂c**, recomputed from the sweep's own rows. Planning quantification:
min κc = 239.7 kHz (tanδ-lo edge) → threshold **24.0 kHz**; the planning-point
sibling is 25.7 kHz (the design doc's "≈ 26 kHz").

*Why 10%-of-min-κc, argued:* the f surrogate's job is the per-draw root-solve
onto f_spin (d=8) / the population f-scatter (d=7). A residual mistuning
δ = 24–26 kHz after the root-solve:
(i) inflates the threshold by 4δ²/(κc+κs)² ≈ **0.4%** of the C₀ = 1 unity —
computed at the conservative **κs = 0.55 MHz lo-edge** (δ = 25.7 kHz,
κc = 257.1 kHz → 0.41%; the draft's 0.39% was this lo-edge-class figure). At
the committed 1.4 MHz point branch the same check reads ≈ 0.09–0.10%
(δ = 24.0 kHz, κc = 239.7 kHz → 0.09%; δ = 25.7 kHz, κc = 257.1 kHz → 0.10%).
Branch labelled per the 2026-07-15 ratification correction; negligible on
either branch; (ii) consumes **0.27%** of P5(Δf_max) (point branch); (iii) is
**3.1%** of the mean linewidth (κc+κs)/2 (point branch) — i.e. an order below
"a linewidth of mistuning" on every reading, while ~10³× smaller than the
±15–20 MHz population f-scatter the plate must cover, so the tuning-yield
metric is untouched. Binding at the population
**minimum** κc (not the planning point) is the conservative choice and costs
nothing: f is the easiest output to surrogate (the −0.35 MHz/µm minor-radius
lever is near-linear over ±25 µm).

**Mechanics (as RATIFIED, rider R1):** both thresholds recompute from the
sweep's own population once it exists; the planning values above
(479 kHz / 24.0 kHz) enter the code only as regression pins whose test
**re-derives them from the committed constants in-test** (no magic numbers; the
pin must match an independent calculation). Failure path unchanged: active
learning within budget → §6 overrun cut order. Rung: PLANNING_ASSUMPTION.
`GateThresholds.ratified` defaults **True**, citing the 2026-07-15 ruling; the
unratified/advisory path remains constructible (future re-opens) and is
exercised in test. **Every gate report prints the κs branch it was evaluated
under** (point 1.4 MHz / lo 0.55 MHz / hi 1.75 MHz).

---

## L5 — Sweep-centre verification block (`sweep/centre_check.py`)

- `PinnedCentre`: import-only values from the re-based gate record — record hash
  `823e67969516bcf2`, canonical Q₀ = 6764.585235432756 (manifest path
  `branches/canonical/wall_loss/q_total`), Q_L = Q₀/(1+`DELOAD_K`),
  p_e = 0.99750. Pin test re-reads
  `refs/gate_runs/20260711T132705Z_rejudge/checkpoint_manifest.json` and asserts
  equality (drift detection, zero re-derivation).
- The §6 block, itemised verbatim as data: (bore+crystal ON/OFF at nominal) ×
  2 mesh levels = 4, + 1 PEC arm (bore+crystal ON, wall-split diagnostic) = **5
  solves** (the corrected count; the draft's 6 was the over-count).
- `run_centre_verification(backend)`: **hard-refuses** while row-5/Q9 (bore
  nominal) or Q11 (crystal εr — repo carries only "εr < 5", a bound not a value)
  sentinels are unresolved; the refusal names the question IDs. The sweep centre
  definition is carried verbatim: *the Phase 1b model whose no-bore/no-crystal
  limit reproduces the pinned gate-record values.*
- Mock-shape exercise via the same `mock_resolutions()` test-double path as L1
  (never solve-ready). Real execution additionally requires the Phase 1b
  geometry engine (SPEC §5b, not this tier — refusal names it).
- **The block reports deltas but cannot judge PASS/FAIL:** the acceptance window
  for "perturbs the pinned centre only weakly" is unpinned (see next section).

---

## Conventions the implementation needs that §8 does NOT pin (flagged, not picked)

1. **L5 acceptance window** — no artifact commits a numeric window for "Phase 1b
   additions perturb the pinned centre only weakly" (SPEC §5b says verify, don't
   assume; the design doc budgets the solves but states no tolerance). The code
   carries a `perturbation_window: TodoTrace` slot and reports deltas only.
   **Rider R2 (2026-07-15): deferral APPROVED — this is now a NAMED ratification
   item (W1, "Phase 1b weak-perturbation window") queued WITH Q9 + Q11: it comes
   due the moment both resolve, not after them.**
2. **Q8 thresholds** — RATIFIED 2026-07-15 (rider R1), rung
   planning-assumption, as mechanised above.
3. **PCE polynomial family for truncated-Gaussian inputs** — §9 pins "PCE order 2
   full basis" but not the family/measure handling; see invented assumption B.

---

## Invented assumptions (explicit, per constraints)

- **A. Rows persistence format:** JSONL (one row per line, stable keys) under
  `runs/layer_a/<design_id>/raw_rows.jsonl` and `derived_rows.jsonl`
  (+ a `design_manifest.json` with mode/seed/blocks/resolutions). Chosen for
  append-safety and glob-ability with zero new dependencies.
- **B. PCE standardisation:** isoprobabilistic per-DOF CDF map to the uniform
  cube + shifted-Legendre orthonormal basis for all rows (exactly orthonormal
  w.r.t. the transformed measure; marginal transforms preserve independence).
  Rung: planning-assumption, numerics-only.
- **C. Mock field content:** analytic TE011 closed-form fields with smooth
  θ-dependent parameter maps — labelled mock everywhere; mock bundles are
  schema-valid but `gain_mask_is_fallback: true` (inadmissible for physics by
  the existing schema guard).
- **D. Design-row identity:** SHA-based row hash over (design id, seed, index,
  θ) for row→design audit, alongside (not replacing) the solve `record_hash`.
- **E. Advisory-until-ratified gate mechanism** (`GateThresholds.ratified`).

---

## Test plan

**Baseline, verbatim (verified this pass): `652 tests collected in 1.27s`.**

Proposed tests per file (counts are ESTIMATES, calibrated with the Layer B ×1.9
lesson — the discipline tests are enumerated, not implied):

| Test file | Focus (incl. discipline tests) | Est. |
|---|---|---|
| `test_sweep_dofs.py` | 9-row table integrity; every nominal/band pinned against its provenance constant; sentinel rows carry the right question IDs; rung vocabulary; row 6 not-a-sweep-dim; d8/d7 dimension lists; resolution-refusal pairs (TODO rung refused; non-sentinel resolution refused) | ~22 |
| `test_sweep_design.py` | Sobol determinism under pinned seed (regression pin, independently computed); block sizes 120/30 and 97/30 verbatim; ledger totals 209/186 + ceiling refusal; truncnorm ±3σ endpoints; uniform + triangular variants; bounds respected; **hard-refusal pairs**: `solve_rows()` under unresolved sentinels in both modes, refusal names Q-IDs, mock-resolution rows always refused | ~26 |
| `test_sweep_backend.py` | Mock bundles pass `validate_bundle`; θ-variation shows in rows; ComsolBackend constructor refusal (sentinels) with no client; Phase 1b spec refusal naming §5b | ~16 |
| `test_sweep_driver.py` | End-to-end dry run on a small mock design; rows carry exactly REQUIRED_SUMMARY_KEYS + design keys; **raw-only deny-list refusal pair**; `gain_mask_is_fallback` and `record_hash` on every row; CLI `--mock` path; `--comsol` path refuses today | ~18 |
| `test_sweep_compose.py` | κc pin vs independent (1+k)f/Q₀ arithmetic AND vs `resonance_linewidth_hz` (second code path); cyclic-vs-angular 2π trap guard; anchored C₀ ≡ 190 at the anchor point exactly; anchor invariance (N-cancellation semantics); fallback-mask anchor refusal + diagnostic-override pair; derived rows carry (k, anchor hash, κs branch, projection); absolute-G² diagnostic vs the schema §6 recipe; R4 report: axial toy ≈ 0 spread / mixed field escalates; 1/max(w_s) = η_H·v_mode_local identity | ~26 |
| `test_sweep_centre_check.py` | Import-only pins re-read from the rejudge manifest (hash + Q₀ + p_e); 5-solve itemisation verbatim (4+1); Q9/Q11 refusal pair; unpinned-window slot refuses PASS/FAIL, reports deltas; mock-shape exercise | ~14 |
| `test_surrogate_pce.py` | Basis counts 45 (d=8) / 36 (d=7) pinned; orthonormality (numeric); exact recovery of an order-2 polynomial; analytic LOO vs brute-force refit (second code path); Q² on an analytic function; standardisation round-trips; determinism | ~22 |
| `test_surrogate_cv_gate.py` | Threshold planning pins **re-derived in-test from committed constants** (479 kHz / 24.0 kHz); ratified-by-default citing the 2026-07-15 R1 ruling + unratified-instance ADVISORY pair; gate report prints its κs branch; composed Δf̂_max path agrees with direct `detuning.delta_f_max_hz` (second code path); gate detects a corrupted surrogate; κs band edges reported | ~14 |

**Estimated after-count: 652 + ~158 ≈ 810 collected** (range 790–830; the naive
behaviour-only count would be ~85, ×1.9 discipline calibration ≈ 160). The exact
after-count will be recorded verbatim at implementation; deviations declared.

---

## Verification (end of implementation pass)

1. `python -m pytest -q` — full suite green; record the collected count verbatim
   against the 652 baseline; zero `requires_comsol` tests executed.
2. Dry-run tier end-to-end (the L2 requirement, exercised for real):
   `python -m cavity.sweep.driver --mock` on a small (e.g. 16-draw) mock design →
   every minted bundle passes `validate_bundle`; `raw_rows.jsonl` rows carry
   exactly the schema keys; `compose` produces derived rows with the convention
   block; PCE fits the mock rows; the CV gate emits an ADVISORY report with both
   thresholds and the κs-edge sidebar; the R4 projection report runs on mock
   corner bundles.
3. Refusal walk (the gate is code, not convention): demonstrate — in one
   transcript — `solve_rows()` refusing (names Q2/Q9/Q11), `ComsolBackend()`
   refusing, `run_centre_verification()` refusing, and the raw-row writer
   refusing a derived key.
4. Confirm zero writes outside `runs/`, scratch, and the new source/test files;
   `git status` shows only the listed files.

## Explicitly out of this tier

Training/AL/confinement solve execution (licence-gated); Phase 1b geometry
engine (SPEC §5b pass); LARS order-3 selection loop; GP cross-check + active
learning; Sobol indices; Layer C consumption of sweep output (`mc_yield`);
confinement-trajectory design (Q5 open); any SPEC edit; any COMSOL run.

---

## Ratification record (2026-07-15)

RATIFIED with one correction and three riders; question texts and design
quantities above stand as drafted, amended only as recorded here.

- **CORRECTION — Q8 Gate 2 check (i):** the 0.39% mistuning-inflation figure is
  labelled as computed at the κs = 0.55 MHz lo-edge (it does not reproduce at
  the 1.4 MHz point branch, where it is ~0.09%). Conservative edge accepted;
  the label is mandatory. Applied in the Gate 2 rationale above, with inputs
  stated.
- **R1 — Q8 numerics RATIFIED** at rung planning-assumption exactly as
  mechanised: thresholds recompute from the sweep's own population; planning
  values 479 kHz / 24.0 kHz enter only as in-test re-derived regression pins;
  `GateThresholds.ratified` flips true on this ruling; every gate report prints
  the κs branch it was evaluated under.
- **R2 — L5 acceptance window:** deferral APPROVED; it becomes a named
  ratification item (W1) that comes due the moment Q9 + Q11 resolve — queued
  with them, not after them.
- **R3 — LARS deferral and the two `__init__` stub modifications APPROVED** as
  declared.

---

## Implementation record (2026-07-15, same day as ratification)

- **Baseline verbatim:** `652 tests collected` (verified pre-implementation).
- **After-count verbatim:** `792 tests collected` — 140 new tests across the
  eight planned test files; full suite `771 passed, 21 skipped` (all skips are
  the pre-existing `requires_comsol` / MPh-contract categories; zero COMSOL
  executed).
- **Deviation declared:** 140 new vs the ~158 estimate (−18, inside the stated
  790–830 range at 792): the dofs/design/compose files landed slightly under
  their per-file ranges; no planned discipline test was dropped.
- **Deviation declared (module surface):** driver orchestration functions
  (`run_sweep`, `run_mock_dry_run`, `load_raw_rows`, `validate_raw_row`) are
  imported by module path (`cavity.sweep.driver`) rather than re-exported from
  the package `__init__`, so `python -m cavity.sweep.driver` runs without
  runpy's already-imported RuntimeWarning. Everything else re-exports as
  planned.
- **Verification executed:** CLI `--mock` full dry run (bundles →
  `validate_bundle`-clean → raw rows → derived rows with convention blocks →
  PCE fit → CV-gate report printing its κs branch → R4 projection report);
  CLI `--comsol` refuses with exit 2 naming Q2/Q9/Q11 (d8) and Q9/Q11 (d7);
  four-refusal walk (solve_rows / ComsolBackend / centre verification /
  raw-row deny-list) all fire; `runs/` untouched (dry-runs to scratch);
  working tree contains exactly the planned files.
- **Planning-pin closure:** `planning_threshold_pins()` from committed
  constants → gate 1 threshold 478.54 kHz (P5 = 9.5708 MHz, κs point branch;
  lo 5.1829 / hi 11.3776 MHz sidebar), gate 2 threshold 23.975 kHz
  (min κc = 239.750 kHz) — matching the ratified plan's ≈479 / ≈24.0 kHz and
  re-derived independently in-test by Monte Carlo (5×10⁵ draws) plus a
  monotonicity check backing the closed-form quantile image.
