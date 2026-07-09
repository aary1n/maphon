# EM field-export schema + observable-b weight functionals

## Context

Four consumers need the forward model's eigenmode fields, and each would otherwise
invent its own ad-hoc export: (1) observable-b differential detuning (SPEC §7.T5(b)
— cavity arm E-weighted over the STO, spin arm H-weighted over the gain region),
(2) the Niall/Nina Maxwell-Bloch handoff (SPEC §9: "This repo *feeds* it"; framework
arXiv 2412.21166), (3) the Layer A surrogate's training data (SPEC §7 / §7-expanded
§7.5: O(150–300) solves, every one logged per §1), (4) the inhomogeneous thermal
line observable (SPEC §7.T2 output 3, consuming spin-arm weights through
`cavity.thermal.broadening`). Getting the schema wrong is expensive four times over;
**the standalone schema document is the primary deliverable, the exporter its
reference implementation.** This pass builds the weights and the pipe; it makes no
predictions (the weights SERVE the §7.T5(b) prediction — spin arm calibrated,
cavity arm predicted; nothing here runs either).

**SPEC basis located (authoritative, read this pass):** §7.T5(b) two-observables
split (SPEC.md:218–220); §7.T2 outputs 1 & 3 (SPEC.md:208–210); §3 extraction
(2πr Jacobian, p_e, V_mode variants, "κc and gain-region H must be exposed cleanly"
— SPEC.md:93–101); §1 reproducibility metadata (SPEC.md:74); §8 analytic-anchor
discipline (SPEC.md:252–260); §11 item 4 Q convention (Q = f′/(2f″) from bare
`freq`, never `imag(emw.freq)` — consume, never re-derive; SPEC.md:298); §6/§6T
constants rules (SPEC.md:136–156); §9 Maxwell-Bloch boundary (SPEC.md:268); §10
module shape (SPEC.md:282–288); §7-expanded §7.2/§7.3/§7.5 (DOF taxonomy, tuned
operating point, surrogate design). Provenance doc: W20 angular-"Hz" trap (header
check); ⟨matrix element⟩ row = the order-unity orientation gap.

**Existing machinery consumed (mapped this pass, do not re-derive):**
- `FieldSample` (src/cavity/extraction/fields.py:33): flattened structured (r,z)
  grid; `e_complex`/`h_complex` (N,3) complex128 in cylindrical components
  (r, φ, z); `eps_r_complex`; `weights_m2` (composite-trapezoid plane weights);
  `dielectric_mask`; optional `gain_region_mask` with `effective_gain_mask`
  fallback → dielectric (fields.py:134).
- `axisymmetric_volume_integral(g, r_m, weights_m2)` = 2π·Σ wᵢrᵢgᵢ — the single
  Jacobian primitive (src/cavity/extraction/quadrature.py:30).
- `electric_filling_factor` (modal.py:91, uses Re ε), `mode_volumes` (modal.py:60,
  global/local variants), `q_from_eigenfrequency` (qfactor.py:22),
  `assert_pec_lossy_q_consistency` (validate.py:25).
- Mode selection: `compute_mode_diagnostics` + `identify_te01delta` +
  `TE01DeltaCriteria` (forward_model/mode_id.py) — field-symmetry primary,
  proximity only a tiebreak. Consumed via `picked_index` + `diagnostics`.
- Persistence: `SolveRecord` / `save_solve_record` / `load_solve_record`
  (forward_model/persistence.py, SCHEMA_VERSION=1): `<hash>/{meta.json,fields.npz}`;
  meta already carries comsol_version, mesh settings, element count, diagnostics,
  picked_index, created_at_utc; fingerprint hash deliberately excludes runtime facts.
  Re-derivation without COMSOL is first-class (tested).
- `line_observable_from_samples(delta_t_k, weights, df_dt_hz_per_k)`
  (thermal/broadening.py:142) — consumer 4's exact entry point; weights =
  probe measure, shape-only.
- Frozen gate artifact: refs/gate_runs/20260706T211615Z_live_comsol/solves/
  888536d768e0fba1/{meta.json,fields.npz} (LFS), p_e = 0.9976566720273174 recorded
  in gate_report.json `analytic_benchmark/pec_lossy_q` inputs ("0.9977" in
  constants.py:221 prose).
- `bessel_zero_jprime`, `f_te_mnp` (validation/analytic.py) — frequency-level only;
  **no analytic field maps exist** (they get authored here as the §8 anchor).

**Two mapped gaps that bound this pass's honesty:**
- κc / loaded-Q split is NOT in extraction (SPEC §3 requirement outstanding;
  §7-expanded §7.3 convention guard is its own pass). This pass stores f and
  unloaded Q and DOCUMENTS the split; it does not build it.
- Phase 1b (bore + crystal) is unbuilt: only STO-vs-air domains exist. The spin-arm
  weight is built against `effective_gain_mask`; on today's geometry that fallback
  is the STO puck — physically NOT the gain region. Every artifact from current
  geometry is labelled schema-example, not physics handoff.

---

## A. Consumer requirements table

| # | Consumer | Fields / derived quantities | Domain | Fidelity | Basis |
|---|---|---|---|---|---|
| 1 | Observable-b differential detuning (later pass) | w_E(r,z) cavity-arm weight + companion p_e; w_s(r,z) spin-arm weight; both as densities on the (r,z) grid co-registerable with `cavity.thermal` ΔT fields; f (cyclic Hz); §6T coefficients NOT here (they stay in provenance) | w_E: STO (`dielectric_mask`); w_s: gain region (`gain_region_mask`, Phase-1b-gated) | weights to quadrature accuracy (gate residual class ~1e-4); the p_e correction itself is −0.2%, coefficient bands ±10-20% → 1% weight fidelity is ample | SPEC §7.T5(b) ("E-energy-weighted over the STO" / "gain-region-H-weighted"); §7.T2 output 1; §3 ("doubly load-bearing") |
| 2 | Maxwell-Bloch handoff (Niall/Nina — NO repo access) | Complex H components on grid over gain region + total stored magnetic energy U_H (their g_j = γ√(μ₀hf/2V_mode^j), V_mode^j = ∫μ₀\|H\|²dV/μ₀\|H(r_j)\|² — |H| magnitude, no orientation projection in the published framework); f (cyclic Hz); Q (+ the loaded/unloaded caveat); volume measure 2πrᵢwᵢ so the coupling histogram (10 bins in the paper) is volume-weighted, not (r,z)-point-weighted — THE trap; precomputed w_s + g-histogram recipe in the doc | gain region (today: fallback = STO, labelled); full domain included for context | grid fine enough that the binned g-distribution is converged (their model is 10-bin coarse — 201×301 is far past this); normalisation immaterial to g_j (ratio) but fixed anyway | arXiv 2412.21166 (Carrera, Jiang, Shu, Wu, Oxborrow; COMSOL RF 2D-axisym, |H|-based V_mode^j, histogram-binned) — verified from full text this pass. **Open asks flagged below**: raw maps vs precomputed histogram; loaded vs unloaded Q for κc; whether E/loss maps wanted; npz OK for their stack |
| 3 | Layer A surrogate training data | Per-solve row: θ = fingerprint (geometry/materials/mesh/study/grid — already canonical in meta.json) + stable-keyed scalar outputs (f′, f″, Q, p_e, V_mode global/local, U_E, U_H, F_m, weight summary stats); export_schema_version + record_hash so rows are globbable and auditable; full field arrays OPTIONAL per solve (scalars always; fields ~6 MB × 300 solves = storage decision per sweep) | scalars global; masks per domain | scalar = extraction accuracy; **schema stability across revisions is the binding requirement** (version field from day one — consumer 3 outlives schema revisions) | SPEC §7 Layer A; §7-expanded §7.2 (θ taxonomy), §7.3 (evaluated at (θ, p_tune)), §7.5 (O(150–300) solves, §1 logging per solve) |
| 4 | Inhomogeneous thermal line broadening (Oxborrow-mandated observable) | Spin-arm probe measure πᵢ = w_s·2πrᵢwᵢ (sums to 1) at nodes where ΔT will be sampled — the `weights` argument of `line_observable_from_samples`; f and Q for the "how many linewidths" unit (Δf·Q/f) | gain region — SAME weights as consumer 1's spin arm (that identity is the design point) | weight-shape fidelity only (broadening is normalisation-free); uniform-T ⇒ zero-width anchor already in CI | SPEC §7.T2 output 3 ("probe weight = the coupling weight in the maser geometry"); §7.T4 linkage (same physics as margin); broadening.py:150 names gain-region-H weighting as the intended maser input |

Requirement flagged as open ask (consumer 2): the published framework is
underdetermined on (i) preferred consumption form (field maps vs precomputed
g-histogram — we ship both ingredients + recipe), (ii) whether their κc uses loaded
or unloaded Q and which coupling k (Breeze k=0.2 vs W20 unstated, SPEC §11 item 3),
(iii) whether E-field/loss maps are wanted for extensions. These go to Niall/Nina;
the schema stores enough for all readings.

---

## B. Physics of the two weight functionals (fixed BEFORE any format decision)

### (a) Cavity arm — E-energy-density weight over the STO

Bethe–Schwinger cavity perturbation for a small isotropic Δε(r) confined to the
dielectric: δf/f = −∫Δε(r)|E|²dV / (2∫ε′(r)|E|²dV) (denominator over ALL domains =
2× electric stored energy; time-averaged phasor densities). With a uniform
coefficient over the STO, Δε(r) = (dεr/dT)·ΔT(r):

  δf = [−(f/2)·(dεr/dT)/εr′]_§6T · p_e · ⟨ΔT⟩_wE,
  ⟨ΔT⟩_wE = ∫_STO w_E(r) ΔT(r) dV,
  **w_E(r) = ε′(r)|E(r)|² / ∫_STO ε′|E|² dV**  (normalised: ∫_STO w_E dV = 1),

with the bracket exactly `cavity_df_dt_hz_per_k` (provenance §6T) and p_e the
existing electric filling factor. ε′ = Re(eps_r_complex), matching modal.py:97
(imaginary part is loss, not stored energy). Uniform-ΔT limit collapses to
δf = df/dT·p_e·ΔT — precisely §6T's "E-weighting p_e ≈ 1 assumed (gate-run
p_e = 0.9977, a −0.2% correction inside the band)".

Normalisation: unit integral over the STO; the companion scalar p_e (ratio of STO
to total E-energy) carries the −0.2% bookkeeping explicitly, so no weight ever
silently absorbs it.

**Sanity checks:** ∫_STO w_E dV = 1 to machine precision; **closed loop:** p_e
recomputed through the weights path == `electric_filling_factor(field)` to ~1e-12
(same arrays, same quadrature primitive) and == 0.9976566720273174 from the frozen
gate record (tolerance only for JSON rounding); uniform-ΔT reproduces the §6T
arithmetic exactly; TE011 analytic anchor (§F).

### (b) Spin arm — coupling-strength weight over the gain region

A spin at r couples to the mode by magnetic dipole with strength
g(r) ∝ |H_proj(r)|/√U_H (Breeze 2017, npj QI 3, 40: g_s = γ√(μ₀ħω_c/2V_m);
position-resolved form = arXiv 2412.21166's g_j). In the weak-excitation /
linear-response regime each spin enters the collective cavity response with weight
g(r)² — so the ensemble observable (frequency pull, thermal shift, inhomogeneous
width) is g²-weighted:

  **w_s(r) = |H_proj(r)|² / ∫_gain |H_proj|² dV**  (∫_gain w_s dV = 1).

**Which component is H_proj — stated exactly, with basis.** At zero field the
triplet eigenstates |X⟩,|Y⟩,|Z⟩ are quantised along the molecular ZFS axes and the
X–Z transition's magnetic-dipole matrix element is carried by S_y alone — B₁ along
the molecular y-axis drives it. Primary, in-file: Breeze 2017 p. 2: the TE01δ
axial magnetic field "via the S_y spin-operator, induces transitions … in suitably
aligned pentacene molecules." So the exact projection is
H_proj = H(r)·ŷ_mol,site — **crystal-orientation-dependent** (and site-dependent:
pentacene occupies inequivalent p-terphenyl host sites), and the orientation of the
actual crystal is not in hand (provenance table's ⟨matrix element⟩ row: W20's
"sizeable fraction of unity", never measured). Therefore: **parameterise, don't
silently pick |H|².**

Implementation (axisymmetry-honest): the solve is m=0, a mounted crystal is not
axisymmetric; the azimuthal average is exact and closed-form. For a molecular-y
unit vector at polar angle to the cavity axis with cos = u_z:

  ⟨|H·û|²⟩_φ = u_z²|H_z|² + ((1−u_z²)/2)(|H_r|² + |H_φ|²).

`SpinProjection` parameter with two modes (+ optional site mixture as a list of
(u_z, fraction)):
- `isotropic_h2` (DEFAULT): w_s ∝ |H|² = |H_r|²+|H_φ|²+|H_z|². This is exactly the
  published-framework convention (Breeze 2017's g_s; arXiv 2412.21166 uses |H|
  magnitude) — the default matches what consumer 2's model actually consumes.
  It also equals the uniform-orientation average of the projected weight after
  normalisation (⟨|H·û|²⟩_iso = |H|²/3 pointwise; the 1/3 cancels) — asserted as a test.
- `axis_projected(u_z)`: the closed-form azimuthal average above; u_z = 1 recovers
  the pure |H_z|² weight (Breeze's "magnetic field dipole directed along the
  cylindrical axis" picture).
B vs H: μr = 1 everywhere → proportional, cancels in the normalised weight.
H_φ ≈ 0 for a clean TE01δ mode; its share is kept as a stored mode-purity
diagnostic, not dropped.

**Rung (flag for the summary):** the |H|² default is literature-backed (Breeze
2017-class Tavis-Cummings coupling; the Maxwell-Bloch paper's own practice). The
projected refinement is OUR implementation of Breeze's S_y statement — derived,
unratified; which mode observable-b should headline is an Oxborrow/literature
ratification item. The order-unity orientational matrix element remains the
provenance table's honest gap either way (weights are normalised, so it cancels in
every SHAPE observable — it re-enters only in absolute-g claims, which this pass
does not make).

**Sanity checks:** ∫_gain w_s dV = 1 to machine precision; uniform-field limit
w_s = 1/V_gain exactly; isotropic-average ≡ h2 identity; u_z = 1 ≡ |H_z|²-only;
cross-link to §3: 1/max(w_s) equals the gain-confined mode volume, reconciled
against `mode_volumes().local_m3` through the gain-region magnetic filling factor
(∫_gain|H|²/∫_all|H|²) on the gate record; probe measure πᵢ = w_sᵢ·2πrᵢwᵢ sums
to 1 and feeds `line_observable_from_samples` unchanged (uniform-ΔT ⇒ zero width,
already anchored in broadening's CI).

---

## C. Schema design decisions (each argued)

1. **Structured grid, not mesh-native (v1).** The entire validated §3 extraction
   stack operates on the FieldSample structured grid with pre-built trapezoid
   weights routed through the single Jacobian primitive; exporting that same
   representation makes exported quantities bit-identical to what the §5/§8 gate
   validated (the p_e closed loop is only meaningful on the same representation).
   All four consumers want samples/grids; none needs elements. Mesh-native nodal
   sets exist transiently at solve time (`export_nodal_fields`) but are deliberately
   resampled and not persisted today — persisting them would add a second,
   unvalidated representation. Boundary fidelity is handled honestly instead:
   `dielectric_mask` is nodal, boundary-straddle error is quadrature-resolution-
   bounded and empirically visible in the gate's closed-form residual (5.6e-5);
   the schema doc states this caveat and points at the §2 convergence discipline.
   Grid shape + 'ij' ordering stored so consumers can reshape to (n_r, n_z).
   Mesh-native export = a future schema-version bump if a consumer materialises.

2. **Store 2D-axisymmetric native; consumers reconstruct 3D.** Stored: flattened
   (r,z) nodes, all six complex components in cylindrical basis (r, φ, z),
   azimuthal index m=0 declared. NOT stored: any pre-rotated 3D grid (pure bloat;
   reconstruction is one documented formula). The schema doc gives: field(r,φ,z) =
   field(r,z) (m=0), right-handed (r̂, φ̂, ẑ), volume element dV = 2πr dr dz, and —
   called out as a trap for consumer 2 — that uniform (r,z) samples are NOT
   volume-uniform: any histogram/statistic over the gain region must weight nodes
   by 2πrᵢwᵢ (the recipe is spelled out with the stored arrays).

3. **Normalisation fixed: unit total stored EM energy.** COMSOL eigenmode
   amplitudes are arbitrarily scaled, and consumer 3 compares across solves, so a
   convention is mandatory. Stored fields satisfy U = U_E + U_H = 1 J with
   time-averaged peak-phasor densities u_E = ε₀ε′|E|²/4, u_H = μ₀|H|²/4 integrated
   with the 2πr Jacobian. The raw scale is not discarded: `raw_total_energy_j`
   (and raw U_E, U_H) stored so raw COMSOL amplitudes are recoverable; U_E vs U_H
   split stored as a mode-health diagnostic. All weights are scale-invariant, so
   this choice costs consumers nothing and buys cross-solve comparability and a
   well-defined g_j.

4. **Units and frequency convention: SI, cyclic Hz, explicit sign chain.**
   Complex eigenfrequency stored as `f_real_hz`/`f_imag_hz` (cyclic Hz, matching
   persistence); Q consumed from `q_from_eigenfrequency` (= f′/(2f″), §11 item 4 —
   never re-derived); phasor convention e^{+iωt} with ε = ε′(1 − i·tanδ) (SPEC §2)
   and Im f > 0 ⇔ decay (the sign chain qfactor.py guards, stated as a block in the
   doc). κc: the schema stores unloaded Q only and DOCUMENTS κc = 2πf/Q_L with the
   de-loading convention Q₀ = Q_L(1+k), k = 0.2 (`DELOAD_K`, Breeze 2017; Wu
   unstated — SPEC §11 item 3); the loaded/unloaded single-sourcing is §7-expanded
   §7.3's own pass and is flagged, not smuggled in. **The W20 angular-"Hz" trap is
   called out verbatim-class in the schema doc** (κc = 2πf/Q_L in rad/s vs
   κc/2π in Hz; the provenance-doc check that W20's "2.5 MHz" ≡ 400 kHz linewidth),
   so downstream consumers don't re-import it.

5. **Format: npz + JSON sidecar, not HDF5.** Matches the existing persistence
   artifact class exactly (SCHEMA_VERSION=1 SolveRecords are npz+meta.json);
   `.gitattributes` already routes refs npz through LFS; runtime deps stay
   numpy/scipy only (no h5py anywhere today); consumer 2 reads npz from Python
   (numpy) or Julia (NPZ.jl) with zero repo access; ~6–8 MB/solve is far below any
   npz pain point. HDF5's advantages (hierarchy, self-description) are covered by
   the embedded metadata JSON + the schema doc shipped inside every bundle; its
   costs (new dependency, new LFS/convention surface, divergence from the validated
   persistence layer) buy nothing a consumer asked for.

6. **Reproducibility metadata block (§1), complete per bundle.** Carried over from
   SolveRecord meta: COMSOL version, mesh settings (full MeshConfig), element
   count, full mode spectrum + per-mode diagnostics, `picked_index`,
   `created_at_utc`, canonical fingerprint (geometry/materials/mesh/study/grid) and
   `record_hash` — the full §1 chain back to the solve. Added by the export layer:
   `export_schema_version`; **mode-selection criterion** (the `TE01DeltaCriteria`
   thresholds — currently NOT in solve meta; selection is field-symmetry primary
   with proximity only as tiebreak, and the bundle says so — never a hardcoded
   index); raw complex eigenfrequency of the picked mode at top level; exporter git
   commit + package version; normalisation declaration (convention name + raw
   energies); convention block (units, phasor, component order, m=0); weight
   definitions with their parameters (projection mode, u_z/site mixture, masks
   used, gain-mask-fallback flag).

7. **Versioning from day one.** Top-level `export_schema_version: 1` (independent
   of persistence's internal SCHEMA_VERSION); readers refuse on unknown major,
   mirroring `load_solve_record`'s mismatch-is-a-miss discipline; the schema doc
   carries the same version + a changelog section. Consumer 3 will outlive
   revisions — stable keys are contract, renames are version bumps.

**Bundle contents (one directory per export):**
- `fields.npz`: r_m, z_m, weights_m2, shape_rz; e_complex, h_complex (unit-energy
  normalised, (N,3), cylindrical); eps_r_complex; dielectric_mask;
  gain_region_mask (ALWAYS materialised, fallback flagged in meta);
  w_e, w_spin (N,) weight densities; spectrum_f_real_hz/f_imag_hz/q_emw.
- `export_meta.json`: block per decision 6 + summary scalars (f′, f″, Q, p_e,
  V_mode global/local, U_E_raw, U_H_raw, F_m, weight diagnostics incl. H_φ share)
  — the flat stable-keyed row consumer 3 globs.
- `FIELD_EXPORT_SCHEMA.md`: the standalone doc, copied in (self-containment for
  consumer 2).

---

## D. The standalone schema document

**Location:** `docs/field_export_schema.md` (new `docs/` dir), version-locked to
`export_schema_version`; a copy ships inside every bundle so the handoff needs no
repo access. Contents: purpose + consumer list; physics definitions of both weight
functionals exactly as §B (with the Breeze 2017 / arXiv 2412.21166 citations and
the orientation caveat); array-key table (name, shape, dtype, units, definition);
conventions block (SI, cyclic Hz, e^{+iωt}, ε′(1−i·tanδ), Im f>0 ⇔ decay,
Q = f′/(2f″), cylindrical (r,φ,z), m=0 reconstruction, dV = 2πr dr dz);
normalisation declaration + raw-scale recovery; the volume-weighting trap and a
worked, dependency-free numpy recipe building the g_j histogram (γ√(μ₀hf/2V_mode^j)
from the stored arrays — consumer 2's exact consumption path); the W20
angular-Hz trap warning; κc/de-loading note (k = 0.2, loaded-split pending);
metadata glossary; gain-mask-fallback semantics; versioning policy + changelog.

---

## E. Computable without COMSOL vs COMSOL-gated

**No COMSOL (all CI tests):** both weight functionals on synthetic fields
(`tests/_extraction_fixtures.py` pattern), on new analytic TE011 field maps, and on
the frozen gate `SolveRecord` (refs/gate_runs LFS npz — tests skip with a clear
reason if the file is an unsmudged LFS pointer); the p_e closed loop; schema
validation; bundle write→read round-trip; **export built end-to-end from a cached
SolveRecord** — the exporter is a pure function of SolveRecord, which is the §1
re-derivation path and means a licence is needed only to mint new records.

**COMSOL-gated (exactly one test, `requires_comsol`):** live solve →
`run_forward_model` → export → validate: unit-energy normalisation holds, bundle
p_e == extraction p_e, picked mode consumed from `picked_index` (not re-selected),
round-trip identical.

## F. Analytic anchors (§8 discipline)

1. **New closed-form TE011 field maps** (`src/cavity/validation/analytic_fields.py`,
   building on `bessel_zero_jprime`): E_φ ∝ J₁(k_c r)sin(πz/L),
   H_r ∝ J₁(k_c r)cos(πz/L), H_z ∝ J₀(k_c r)sin(πz/L), k_c = x′₀₁/a, evaluated on
   `make_structured_grid`-class grids. Anchors, all hand-derivable via the Lommel
   integral ∫₀^b J_n²(kr) r dr = (b²/2)[J_n′²(kb) + (1−n²/(kb)²)J_n²(kb)]:
   - electric-energy fraction inside a coaxial sub-cylinder r<b vs the weights-path
     computation (cavity-arm anchor — the closed form IS a p_e for a synthetic
     "dielectric" mask with ε=1);
   - spin-arm weight moments over a crystal-like sub-region (r<b, |z−L/2|<h/2):
     closed-form radial (J₀², J₁²) × elementary axial (sin², cos²) integrals;
   - U_E = U_H equality (resonance identity, exact analytically; asserted to
     quadrature tolerance) — doubles as the normalisation-convention check.
   Tolerances grid-resolution-bounded and stated, §8 style.
2. **The p_e closed loop** on the frozen gate record: weights path ==
   `electric_filling_factor` == 0.9976566720273174 (gate JSON) — the STO-domain
   check the task names.
3. **Uniform limits:** uniform ΔT ⇒ pure shift/zero width through
   `line_observable_from_samples` (exact, already CI-anchored in broadening);
   uniform field ⇒ w_s = 1/V_gain exact.
4. **Identity checks:** isotropic-orientation average ≡ h2 weight; u_z=1 ≡ |H_z|²
   weight; ∫w dV = 1 machine-precision both arms.

---

## G. Implementation steps

0. **Baseline invariant, fresh, before any edit:** `uv run pytest` → expect
   392 passed / 20 skipped / 1 xfailed; `uv run pytest --comsol` → expect
   411 / 1 / 1. Reconcile any drift or STOP. (Totals are consistent: 413 both
   tiers; counts are emergent, not pinned in-repo — verified this pass.)
1. `src/cavity/validation/analytic_fields.py` — TE011 closed-form field maps +
   closed-form sub-region integral helpers. Tests: `tests/test_analytic_fields.py`.
2. `src/cavity/extraction/weights.py` — `WeightField` (frozen dataclass: values
   (N,) density in m⁻³, mask, params, `probe_measure()` → πᵢ = wᵢ·2πrᵢ·w_m2ᵢ),
   `cavity_arm_weight(field) -> WeightField` (+ p_e companion via existing
   `electric_filling_factor`), `spin_arm_weight(field, projection=SpinProjection.isotropic_h2())`,
   `SpinProjection` (isotropic_h2 | axis_projected(u_z) | site mixture). All
   integrals through `axisymmetric_volume_integral`. Re-export via extraction
   `__init__`. Tests: `tests/test_extraction_weights.py` (checks §B + anchors §F;
   gate-record tests skip-if-LFS-pointer).
3. `src/cavity/export/` — `schema.py` (EXPORT_SCHEMA_VERSION=1, required-key
   contract, `validate_bundle`, `load_bundle` refusing version mismatch),
   `writer.py` (`export_bundle(record: SolveRecord, out_dir, *, projection=...) ->
   Path` — pure function of a SolveRecord; normalisation; meta assembly incl. git
   commit via `git rev-parse HEAD`, recorded-not-hashed, mirroring persistence's
   runtime-fact discipline). Tests: `tests/test_export_schema.py` (round-trip
   bit-identical arrays, validation refusals, metadata completeness,
   from-cached-gate-record end-to-end, unit-energy assert).
4. `docs/field_export_schema.md` per §D; copied into bundles by the writer.
5. `tests/test_export_comsol.py` — the one `requires_comsol` live test (§E).
6. Reference bundle: generate from the frozen gate record →
   `refs/exports/20260706T211615Z_gate_888536d768e0fba1/` labelled SCHEMA EXAMPLE
   (PEC walls, no bore/crystal, gain mask = STO fallback — stated in its meta);
   `.gitattributes` += `refs/exports/**/*.npz filter=lfs ...`;
   `.gitignore` += `!refs/exports/**`. This is the concrete file a schema handoff
   needs; the physics handoff bundle waits for Phase 1b + impedance walls.
7. SPEC.md — minimal dated hunks (≤3), only where export/handoff status lives:
   §9 Maxwell-Bloch bullet gains a dated feed-schema-BUILT parenthetical
   (docs/field_export_schema.md v1 + cavity.export); §10 module list gains
   `export` + the weights note under extraction; §7.T5(b) gains a dated
   status parenthetical: weight machinery BUILT, no prediction runs, |H|² default
   with parameterised projection pending ratification. No thermal-solver, no
   constants-grade, no gate-row, no Q-convention edits.
8. Like-for-like both tiers; strict xfail stays xfail; verbatim `git status` +
   `git log -1 --oneline` captured for the summary.

## H. Out-of-scope guards (hard)

No detuning integration, no broadening computation runs, no Maxwell-Bloch runs, no
surrogate training, no predictions. No κc/loaded-Q extraction API (documented +
flagged only). No Phase 1b geometry work (gain mask stays a hook). No touching
thermal solvers, constants' grades, gate rows, or the Q convention. No
opportunistic refactors.

## I. Verification

- `uv run pytest` (both before and after; after-counts = before + new tests, no
  regressions, xfail intact).
- `uv run pytest --comsol` like-for-like (needs the local licence; if unavailable
  at implementation time: stop and report, per the baseline rule).
- `uv run pytest tests/test_extraction_weights.py tests/test_export_schema.py
  tests/test_analytic_fields.py -v` — the new surface.
- Manual: build the reference bundle, `np.load` it back, check meta keys and the
  schema doc copy; confirm `git check-attr` shows LFS routing for the new refs path.

## J. Post-implementation summary contract (deliver all eight)

1. files changed; 2. consumer-requirements table as built + open asks (esp. the
Maxwell-Bloch field-input questions); 3. schema decisions with arguments;
4. spin-arm weight choice, its basis (Breeze 2017 S_y / |H|² default /
parameterised projection) and its rung — flagged as the item most likely needing
Oxborrow/literature ratification; 5. weight sanity-check results incl. p_e closed
loop vs 0.9977 (0.9976566720273174 exact); 6. validation commands; 7. open asks
(Niall/Nina list + κc loaded-split + Phase 1b dependency + orientation
ratification); 8. verbatim `git status` and `git log -1 --oneline`.
