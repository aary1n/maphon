# Figures pass — six publication-grade figures + supervisor one-pager (rendering only)

## Context

First presentation artifact of the project: render six figures from the EXISTING archived records
(§5a run archive, byte-pinned margin report, Singh raw archive, committed thermal/detuning/provenance
machinery) plus a one-page supervisor summary. Dual purpose, both explicit: (1) supervisor-facing
one-pager for the next Oxborrow meeting; (2) seed of the manuscript figure set — figure quality,
captions, and provenance stamps ARE the deliverable. No new physics, no solves, no COMSOL, no
thermal/extraction changes. Caption honesty = provenance discipline (same rules as `constants.py`):
every applicable SPEC status flag appears in its figure's caption. Captions below are the ratification
objects — they ship as committed constants and are pinned in the one-pager.

**User rulings taken during planning (AskUserQuestion):**
1. **F2 V_mode annotation = archive wording.** The prompt's "identified convention collision — own
   E-based 0.656 vs Booth magnetic Eq. 15" is refuted by the record and by direct recomputation from
   the archived fields: 0.6558 cm³ **is** the H-based magnetic global-max value (E-based = 0.8591,
   εE-based = 0.4804), and Booth's Eq. 15 (thesis PDF p. 8) is V_m = ∭_cavity H²(r)dV / H²_max —
   the *same* magnetic-global family. F2 annotates the ×1.60 as UNRESOLVED, two-sided, per the
   committed failure record, **plus** the new page-cite as evidence that convention choice among the
   computed variants does not explain it. No "identified collision" claim; resolution stays a separate
   pending pass.
2. **First-paper-boundary ask: descriptive reference only** (Gmail token expired; no verbatim quote).
3. **Asks-list = six items**: the five enumerated + the Booth V_mode-definition ask (SPEC §11 items 1/8).

## Placement + module decisions (plan's calls)

- **Figures land in `docs/figures/`** (new dir): next to the one-pager that embeds them; `refs/` is
  read-only inputs, `thermal/reports/` is module-owned computed reports, and a new top-level `figures/`
  would add a namespace for what is document content. One PDF + one PNG per figure (12 files).
  Existing `.gitattributes` routes `*.pdf` → LFS (leave as-is; PNGs stay regular blobs like
  `thermal/reports/*.png`).
- **Generator = new package `src/cavity/figures/`** (the one permitted `src/cavity` addition):
  - `_style.py` — the single shared rcParams module: serif fonts + mathtext (`stix`/DejaVu Serif —
    LaTeX-adjacent, **no usetex** so regeneration is machine-independent), no seaborn, colourblind-safe
    perceptually-uniform sequential maps (`viridis` for F1 fields, `magma`/`inferno` for F3 ΔT),
    figure-footer provenance-stamp helper (stamps the ARCHIVE's identity — record hash / run dir /
    archive commit from the manifest — never the render-time clock or commit, so output is
    deterministic).
  - One module per figure: `f1_mode_maps.py`, `f2_reproduction_table.py`, `f3_delta_t_map.py`,
    `f4_cavity_arm_envelope.py`, `f5_margin_waterfall.py`, `f6_singh_axis_map.py`. Uniform contract
    per module: `CAPTION: str` (the ratified caption, committed), `build_data() -> dict` (pure, no
    matplotlib import — everything the figure plots), `render(data) -> Figure`, `main()` (writes
    `docs/figures/<name>.pdf` + `.png`). matplotlib imported lazily inside `render` with `Agg`
    (the `report_3a.py` precedent; matplotlib stays in the `reports` extra — env already has 3.11.0).
  - `__main__.py` — `python -m cavity.figures` regenerates all six; each module also runs standalone
    (`python -m cavity.figures.f3_delta_t_map`). Reproducible-by-command, not notebook-interactive.
- Before writing any chart code at implementation time: load the `dataviz` skill (required trigger).

## The six figures

### F1 — TE01δ mode maps (|E|, |H|)

- **Layout:** ONE figure, two panels side-by-side (|E| left, |H| right), shared (r, z) axes in mm,
  separate colorbars, each field normalised to its own max (eigenmode amplitude arbitrary); geometry
  outline overlaid (box rectangle from `fingerprint.geometry`, torus circle major 6.14 mm / minor
  2.456 mm at mid-plane); f and Q₀ stamped in-panel.
- **Data source (disk):** archived §5a finest-level **canonical-branch walls-on** SolveRecord
  `refs/gate_runs/20260710T083340Z_live_comsol/solves/823e67969516bcf2/` via
  `cavity.forward_model.persistence.load_solve_record` (LFS npz; grid 201×301 flattened r-slowest,
  keys `r_m, z_m, e_complex, h_complex, weights_m2, ...`).
- **Render-time compute:** |E| = √(Σ|E_i|²), |H| likewise; reshape via `fingerprint["grid"]`;
  f′ = spectrum[picked_index]; Q₀ = `q_emw_cross_check` (6764.585); nothing else derived.
- **Caption (draft):** "TE01δ mode maps at the recovered Booth torus: |E| (left) and |H| (right) over
  the (r, z) half-plane, each normalised to its own maximum (eigenmode amplitude is arbitrary); copper
  box and dielectric torus cross-section outlined. Rendered from the archived §5a finest-mesh walls-on
  SolveRecord, CANONICAL branch (SPEC §2 materials: εr′ = 316.3, tanδ = 1.1×10⁻⁴; record
  `823e67969516bcf2`, 7492 elements, `refs/gate_runs/20260710T083340Z_live_comsol`): f = 1450.382 MHz,
  Q₀ = 6764.6. Mode identified by field symmetry (azimuthal-E energy fraction 1.00, zero on-axis H_z
  sign changes), not eigenvalue order. The gated FAITHFUL companion (tanδ = 1.054×10⁻⁴, the .mph-exact
  unrounded Debye value) gives Q₀ = 6981.3 vs Booth's 6,980 (+0.02%); branch delta −3.10% as measured.
  The §5a gate as a whole is a GATED FAIL on the V_mode row (see F2); these maps carry no
  §5a-validated status."

### F2 — Reproduction table-as-figure (the honesty table)

- **Layout:** single-panel rendered table. Main block, columns *Quantity | Booth print / committed §5
  window | Own model (faithful) | Δ or ratio | Verdict* with red shading on FAIL rows:
  f (PASS) · Q₀ 6,980→6981.32, +0.02% (PASS) · Q_diel 9511.5 vs [9000, 10000] (PASS) · wall fraction
  0.26601 vs [0.23, 0.27] (PASS) · **V_mode (magnetic global-max) 0.6558 vs 0.409 ±1%, ×1.60 (FAIL)** ·
  **F_m 7.14×10⁶ vs [10⁷, 10⁸) (FAIL, arithmetic consequence)**. Sub-block "V_mode variants (diagnostics,
  not §3 outputs)": H-global 0.6558 · H-local 0.6558 (identical) · E-based 0.8591 (×2.10) · ε-weighted-E
  0.4804 (×1.17) — none reproduces 0.409. Footer block: faithful vs canonical Q₀ 6981.32 / 6764.59
  (−3.10%); gate tallies 3/2/1, `phase1_complete = false`.
- **Data source (disk):** `refs/gate_runs/20260710T083340Z_live_comsol/checkpoint_manifest.json`
  (branches, gate checks + windows, `diagnostic_mode_volumes`, tallies) — no LFS needed. Booth prints
  from `TARGETS.booth` / Table 8 cites.
- **Render-time compute:** ratios/deltas only.
- **Caption (draft):** "Booth reproduction at the recovered TE01δ torus (`refs/booth_geometry_recovery.md`),
  §5a live run 2026-07-10 (archive `refs/gate_runs/20260710T083340Z_live_comsol`, gated record
  `2b276c4424e49bb9`): own-model values on the FAITHFUL material branch (tanδ = 1.054×10⁻⁴, the
  .mph-exact unrounded Debye value, `BOOTH_MPH_TAN_DELTA`; ratified pre-registration) judged against
  the committed §5 windows — no new tolerances. f, Q₀ (+0.02% vs Booth Table 8's 6.98×10³), Q_diel and
  the wall-loss fraction PASS; V_mode (magnetic global-max, the §3 convention — the same |H|²-global
  family as Booth's printed Eq. 15 definition, thesis p. 8: V_m = ∭H²dV/H²_max) reads 0.656 cm³ vs
  Booth's printed 0.409 cm³ — ×1.60, FAIL — and F_m FAILS as its direct arithmetic consequence. The
  excess is UNRESOLVED and two-sided: either Booth's printed V_mode uses a definition/normalisation
  not spanned by the computed variants, or the model's field genuinely spreads more than her solve's —
  the local-max variant is identical and the E-based diagnostics (0.859, 0.480 cm³) do not reproduce
  0.409 either, so no computed convention variant explains it, and the passing energy-ratio rows
  cannot arbitrate. Booth's V_mode definition is a standing supervisor/Booth ask; its resolution is a
  separate pending pass — neither side is adopted here. Branch discipline: gate-passage is a
  faithful-branch statement only; the canonical companion (tanδ = 1.1×10⁻⁴, Q₀ = 6764.6, the SPEC §2
  model Phase 2 runs) was never judged against the ±1% window; branch delta AS MEASURED −3.10%.
  Tallies 3 pass / 2 fail / 1 deferred (confinement trend — Breeze-side sweep); `phase1_complete`
  remains false."

### F3 — ΔT(r, z) heatmap, maser crystal

- **Layout:** single (r, z) heatmap, colourbar in K, crystal outline; peak and volume-average ΔT
  annotated; small annotation of the illuminated face.
- **Data source (module call, computed at render time — closed-form, no solves in the COMSOL sense):**
  `cavity.thermal.cylinder.solve` at the **committed worked-example graded-inputs stack**
  (`tests/test_thermal_cylinder.py::test_maser_worked_example_graded_inputs`): crystal r = 1.5 mm,
  h = 8 mm (`CRYSTAL`), k = `K_PTP.k_mid` = 0.3162 W m⁻¹K⁻¹, end-fire Beer-Lambert (l_abs = 200 µm =
  `L_ABS_PUMP` scoping grid[5]), flood radial, Dirichlet base + Robin side/top at
  h = `h_top_with_radiation(H_CONV_AIR.h_band_hi, EMISSIVITY_PTP.eps_nominal, 300)` = 25.5 W m⁻²K⁻¹;
  n_modes = 64; grid ~121×161. ΔT sampled via `CylinderSolution.delta_t`.
- **Pump power (plan's pick + basis):** **P_abs = 50 mW** — chosen so the volume-averaged
  ΔT ≈ 18.5 K sits inside Oxborrow's in-thread "several tens of Celsius" inference (~13–30 K
  steady-state at 100 mA, SPEC §11 item 5); explicitly illustrative; ΔT strictly linear in P.
  Verified at plan time: peak ≈ 52.9 K, vol-avg ≈ 18.5 K, boundary-flux energy diagnostic closes to P.
- **Caption (draft):** "Steady-state ΔT(r, z) in the maser crystal (Pc:PTP cylinder, radius 1.5 mm ×
  height 8 mm; provenance `Crystal`), computed by the licence-free closed-form Bessel/Robin conduction
  anchor `cavity.thermal.cylinder` at the committed worked-example stack: END-FIRE axial Beer-Lambert
  deposition (D2 — supervisor-preferred, Oxborrow-verbal 2026-07-08; side-fire structurally outside
  the axisymmetric eigenbasis), l_abs = 200 µm (UNSOURCED-SCOPING value; nominal-doping arithmetic
  would overstate absorption — Oxborrow-verbal 2026-07-06), flood radial profile (D3), k = 0.316
  W m⁻¹K⁻¹ (geometric mid of the 0.1–1 band; the 0.1 floor's provenance is a liquid-phase value),
  Dirichlet base ('substrate at room temperature') and Robin side/top at h = h_conv,hi + h_rad ≈ 25.5
  W m⁻²K⁻¹ (free-convection ceiling — both real geometries likely sit below the 5–20 band — plus
  linearised radiation at ε = 0.90 of the ratified 0.80–0.95 band). P_abs = 50 mW is ILLUSTRATIVE:
  chosen so the volume-averaged ΔT ≈ 19 K sits inside Oxborrow's in-thread 'several tens of Celsius'
  inference (~13–30 K at 100 mA drive); ΔT is strictly linear in P — rescale freely. Peak ΔT ≈ 53 K at
  the illuminated face; at this ΔT the linearised h_rad under-reads the exact quartic by ~5–16%
  (§7.T7). Energy diagnostic: boundary flux = P_abs to solver truncation. All D1–D7 BC/heating details
  are parameterised planning assumptions pending Oxborrow (§11 item-10 bundle)."

### F4 — Δf_cavity over the 30 K envelope + spin arm

- **Layout:** single axes, T = 293→323 K vs Δf (MHz). Three cavity-arm curves: adopted integrated CW
  closed form (`detuning.cavity_arm_shift_uniform_hz`), 293 K point-slope × ΔT
  (`cavity_df_dt_hz_per_k(293)`·ΔT), first-order integral of the committed slope
  ((f/2εr)·C·[1/(293−T₀) − 1/(T−T₀)]) — exactly the A10 anchor's three comparators. Spin arm drawn on
  the same axes **with its true (negative) sign** as a thin band hugging zero
  (band |df_spin/dT| ∈ [64, 120] kHz/K × ΔT; point −109 kHz/K dashed) — the ~4% asymmetry and the
  opposite sign are the point; annotated. A10 ratio annotation box at the 323 K endpoint.
- **Data source:** all render-time evaluation of committed functions/constants (`DF_CAVITY_DT`,
  `DF_SPIN_DT`, `STO`, `TARGET`); no disk reads.
- **Caption (draft):** "Cavity-arm detuning over the ruled 30 K operating envelope, 293→323 K
  ('293 + 30 = 323' is our reading of the verbal 30 K ruling — Oxborrow-verbal 2026-07-08 — not his
  verbatim range). Three branches of the same §6T constant (Rupprecht & Bell Curie–Weiss parameters
  C = 8.25×10⁴ K, T₀ = 37 K; local-slope caveats and the 112 K validity floor as graded): the ADOPTED
  integrated closed form (`cavity.thermal.detuning`; +82.6 MHz at the envelope top), the 293 K point
  slope × ΔT (+2.885 MHz/K), and the first-order integral of the committed slope. Documented spreads
  (CI anchor A10): integrated = +0.7% vs the 300 K point slope × 30 K, +6.6% vs the first-order
  integral, −4.6% vs the 293 K slope × 30 K. The spin arm is drawn to the same scale at its §6T band
  (−64…−120 kHz/K; graded point −109 kHz/K, the conservative face-value branch): at the envelope top
  it reaches only ~2–4% of the cavity arm — that asymmetry is the point — and its sign is OPPOSITE
  (cavity blue-shifts, spins red-shift on heating), so the differential detuning ADDS. Spin-arm
  caveats ride along: the raw data's temperature-axis definition is UNRESOLVED (it IS the band),
  deuteration transfer unverified, local slopes only. p_e ≈ 1 assumed (gate-run p_e = 0.9977, a −0.2%
  correction inside the band)."

### F5 — Margin waterfall

- **Layout:** five-stage chart (five mini-panels in a row, one quantity each — the stages carry
  different units, so no single shared bar axis): Q₀ = 6,980 → [÷(1+k), k = 0.2] → Q_L = 5,817 →
  [f/Q_L] → κc = 249.3 kHz → [(κc/2)√(C₀−1), C₀ = 190] → Δf_max = 1.71 MHz → [common-ΔT inversion] →
  ΔT_max = 0.584 K with whiskers [0.567, 0.725] K. Transform arrows labelled between panels.
- **Data source:** recompute at render time through the committed functions (`detuning.q_loaded`,
  `broadening.resonance_linewidth_hz`, `detuning.delta_f_max_hz`, `detuning.delta_t_max_k`) with
  inputs exactly as `cavity.thermal.report_margin` (p_e from the frozen export bundle meta) —
  cross-checked in the regeneration test against the byte-pinned
  `thermal/reports/q_margin_planning_point.md` values (0.5843 K; band [0.567, 0.725]).
- **Caption (draft):** "Thermal-margin budget at the planning point, regenerated through the same
  committed functions as the byte-pinned report (`thermal/reports/q_margin_planning_point.md`):
  Q₀ = 6,980 (Booth Table 8) → Q_L = 5,817 under de-loading k = 0.2 (Breeze 2017; Wu's coupling
  unstated — flagged) → κc = f/Q_L = 249.3 kHz (CYCLIC-Hz FWHM, never the angular 2πf/Q_L — the
  provenance table's verified W20 angular-'Hz' trap) → Δf_max = (κc/2)√(C₀−1) = 1.71 MHz at C₀ = 190
  (the SPEC revision-note planning value, never a measured constant) → ΔT_max = 0.584 K, whiskers =
  the §6T coefficient band [0.567, 0.725] K. CROSS-BUILD COMPOSITE: this point composes Booth's
  Q₀ = 6980 (Booth Table 8) with Breeze's de-loading k = 0.2 (Breeze 2017; Wu's coupling unstated,
  SPEC §11 item 3) — the resulting Δf_max is NEITHER build's number and must not be quoted as Booth's
  or Breeze's margin. §5a supersession status: own-model f/Q/split numbers now exist ARCHIVED
  (2026-07-10) but are NOT §5a-validated — the run is a GATED FAIL on the V_mode row — so the
  composite REMAINS the planning-point headline and the own-model rebase is pending the V_mode pass.
  Riders: p_e = 0.9977 is the frozen PEC-anchor placeholder (moves these numbers ~0.2%); the two arms
  compose under the common-ΔT planning convention D8 (direction conservative — overstates detuning,
  understates ΔT_max); the probe weight is a uniform-over-crystal placeholder, so spin-arm content
  inherits UNRATIFIED-w_s status doubly (gain mask = STO fallback until Phase 1b). The Q-margin
  QUESTION is supervisor-endorsed (verbal, 2026-07-06); the RESULT remains unratified — this is a
  planning point, not a claim."

### F6 — Singh axis-map provenance figure

- **Layout:** two panels. Left: the committed raw X–Z point series (file axis) with window fits
  (drawn-line span −102.3 ± 1.1 over 254–324; operating point −108.5 ± 2.2 over 293–310; band-edge
  windows), and the 197 re-digitised figure points mapped through the *inverse* affine map onto the
  raw axis — visibly coincident (rms 0.09 K / freq residuals at the 0.1 MHz quantisation floor).
  Right: slope-vs-window summary (forest-plot style): printed −101, digitised figure-axis −112,
  raw-axis fits, ×1.073 inflation arrow across the figure/file boundary, and the carried band
  [−120, −64] kHz/K shaded with the graded point −109.
- **Data source (disk — raw data IS in the repo):** `refs/singh_2025_raw/Fig2B_(iii)XZ_xztemp.txt`
  (SHA-256-pinned) + `refs/singh_fig2biii_vector_extraction.csv`, both loaded through
  `cavity.provenance.singh_raw_fits` (`load_xz`, `ols_slope`, `point/band_lo/band_hi_window_fit`,
  `affine_map_vs_extraction` — the 0.9316/16.56 are COMPUTED at render time, never hard-coded).
- **Caption (draft):** "Provenance of the spin-arm coefficient: the Singh et al., Nat. Commun. 16,
  10530 (2025) Fig. 2B(iii) X–Z series exists in two temperature axes related by an exact affine map,
  T_fig = 0.9316·T_raw + 16.56 K (rms 0.09 K; recomputed at render time by
  `cavity.provenance.singh_raw_fits` from the two committed point sets). Left: the raw point series
  (`refs/singh_2025_raw/`, byte-for-byte as received from the first author, SHA-256-pinned;
  plotted-point exports, not raw acquisition; 0.1 MHz quantisation) with window fits; overlaid, the
  197 re-digitised figure points (`refs/singh_fig2biii_vector_extraction.csv`) mapped through the
  affine map — coincident at the quantisation floor. Right: slope vs fit window — the paper's printed
  −101 kHz/K agrees with its own raw data to ~1% (raw OLS −102.3 ± 1.1 over file-axis 254–324 K, the
  drawn red line's span; the paper prints no uncertainty anywhere), while the earlier digitised
  −112 kHz/K was a faithful reading of the FIGURE, whose axis inflates slopes ×1.073 — the
  printed-vs-digitised discrepancy is localised entirely to the figure/file axis boundary. Which axis
  carries the calibrated sensor reading is UNRESOLVED (top ask to the authors); that systematic IS
  the carried band [−1.2×10⁵, −6.4×10⁴] Hz/K (shaded), with the graded point −1.09×10⁵ Hz/K = the
  conservative face-value branch over 293–310 K — a documented branch choice, not a best estimate.
  Deuteration-transfer caveat retained (protonated Singh crystal vs the dataset's Pc-d₁₄:PTP-d₁₄)."

## One-pager — `docs/supervisor_onepager_2026-07.md`

Half a page of prose + the six figures (relative links `figures/*.png`) with their captions verbatim
(copied from the modules; pinned by test) + closing asks-list. Prose covers: what was built (validated
§8 benchmark → forward model → extraction → gate machinery; closed-form thermal submodel + detuning
budget maps; provenance/grading discipline), what the §5a run showed (geometry recovery empirically
supported — f 4 s.f., Q₀ +0.02%; V_mode red ×1.60 unresolved two-sided; phase1_complete false at
3/2/1), what is blocked on what (own-model margin rebase ← V_mode resolution; observable-b ← Phase 1b
+ Angus metadata; claim levels ← ratification bundle).

**Asks-list (as committed):**
1. The first-paper-boundary question from the 2026-07-06 framing note — still pending (descriptive
   reference; no verbatim quote — user ruling).
2. The Angus introduction (committed Monday 2026-07-06; reminder sent; §11 item-5 asks route through it).
3. D8 ratification — the common-ΔT two-arms convention of the detuning integration.
4. w_s projection ratification — which spin-projection mode headlines observable-b (|H|² default,
   Breeze-framework convention; UNRATIFIED).
5. Lang temperature-window follow-up — Lang 2007 Fig. 4 read locally at the ruled 293–323 K window
   (corroborates the cold-finger branch; local-fit discipline per §6T).
6. Booth's V_mode definition — what does Table 8's V_mode compute? (new ask minted by the §5a run;
   SPEC §11 items 1/8; F2's red row).

## Regeneration test — `tests/test_figures.py` (the only new tests)

Per the byte-pin/regeneration-pin precedent, but pinning the **data arrays feeding each figure**, not
binary images (no RNG anywhere; determinism from fixed inputs + shared rcParams):

1. `test_f1_data_pins` — loads the archived record (gate-record-style **skip** if LFS pointer/absent);
   pins f′ = 1450382241.977 Hz, Q₀ = 6764.5852, grid shape (201, 301), and recomputes V_mode from the
   plotted |H|² grid = 6.557764e-07 m³ (ties the picture to the failing gate number).
2. `test_f2_data_pins` — build_data vs `checkpoint_manifest.json` verbatim values (0.6558/0.8591/0.4804
   cm³, +0.02%, −3.10%, tallies 3/2/1, phase1_complete false) and the FAIL rows marked red.
3. `test_f3_data_pins` — worked-example stack regenerates: peak ≈ 52.86 K, vol-avg ≈ 18.52 K at
   P = 50 mW (tight rel tol), boundary-power energy diagnostic closes to P; ΔT-linearity spot check.
4. `test_f4_data_pins` — endpoint 82.61 MHz and the three A10 ratio windows (same bounds as anchor
   A10); spin-band endpoints from `DF_SPIN_DT`.
5. `test_f5_data_pins` — stage values equal the byte-pinned margin report's numbers (Q_L 5816.67,
   κc 249.284 kHz, Δf_max 1.7135 MHz, ΔT_max 0.5843 K, band [0.567, 0.725]).
6. `test_f6_data_pins` — affine map scale/offset/rms via `affine_map_vs_extraction()` (same tolerances
   as the existing provenance test), the −102.3/−108.5/−119.7/−64.4 window fits, band endpoints.
7. `test_captions_pinned_in_onepager` — each module's `CAPTION` appears verbatim in
   `docs/supervisor_onepager_2026-07.md`; per-figure flag words asserted present (e.g. "UNRESOLVED",
   "CROSS-BUILD COMPOSITE", "UNRATIFIED-w_s", "ILLUSTRATIVE", "planning assumption").
8. `test_render_smoke_shared_style` — `pytest.importorskip("matplotlib")`; every figure renders under
   Agg with the shared rcParams and writes both PDF+PNG to tmp_path.

Data-pin tests import no matplotlib (build_data is matplotlib-free), so tiers stay clean.

## SPEC edit (one dated hunk; user may strike)

Append an inline italic dated parenthetical to §11 item 10 (the written-comms/framing bullet — the
natural home): *(2026-07-10: presentation artifact committed — six-figure set `docs/figures/` +
supervisor one-pager `docs/supervisor_onepager_2026-07.md`, rendered from the archived §5a records,
the byte-pinned margin report, and the committed §6T machinery only — no new physics; captions carry
the standing flags verbatim; asks-list mirrors this item plus §11 items 1/5/8 and the D8/w_s
ratifications.)*

## Files changed (complete list)

- NEW `src/cavity/figures/` — `__init__.py`, `__main__.py`, `_style.py`, `f1_mode_maps.py`,
  `f2_reproduction_table.py`, `f3_delta_t_map.py`, `f4_cavity_arm_envelope.py`,
  `f5_margin_waterfall.py`, `f6_singh_axis_map.py`
- NEW `docs/figures/` — 6 × (`.pdf` + `.png`)
- NEW `docs/supervisor_onepager_2026-07.md`
- NEW `tests/test_figures.py`
- EDIT `SPEC.md` — the one dated hunk above
- Nothing else. `refs/` strictly read-only; no changes to any existing `src/cavity` module, no
  pyproject change (matplotlib already in the `reports` extra; env has 3.11.0).

## Verification

1. **Baseline BEFORE any edit:** `uv run pytest` → expect **515 passed / 21 skipped / 1 xfailed**;
   `uv run pytest --comsol` → expect **535 / 1 / 1**. Reconcile or STOP (537 collected confirmed at
   plan time).
2. Implement; regenerate figures via `uv run python -m cavity.figures`; verify 12 files land.
3. **End, like-for-like both tiers:** `uv run pytest` → **523 / 21 / 1** (515 + 8 new);
   `uv run pytest --comsol` → **543 / 1 / 1**. (On checkouts without LFS content, test 1 skips — same
   behaviour as the existing gate-record fixture.)
4. Deleted-and-regenerated determinism check: delete `docs/figures/*`, re-run the module, `git status`
   shows only untracked-identical/-bit-identical PNG re-adds (PDFs via LFS may re-hash — the pin is on
   data, not binaries; report as such).
5. Final summary per the user's 7-point request (files, per-figure source/compute/caption-as-committed,
   asks-list, deviations, test design+results, both-tier counts, verbatim `git status` +
   `git log -1 --oneline`).

## Deviations from the brief (explicit)

1. **F2 annotation** uses the archived record's two-sided UNRESOLVED wording, not the prompt's
   "identified convention collision / own E-based" framing — user-ratified during planning after the
   labelling was refuted from the archive (0.6558 is H-based) and the thesis (Eq. 15, p. 8, is
   magnetic-global — same family as ours).
2. **Ask #1** is a descriptive reference, not a verbatim quote (Gmail connector token expired;
   user-ruled fallback).
3. **Asks-list has six items** (Booth V_mode definition appended) — user-ratified.
