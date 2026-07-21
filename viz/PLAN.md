# viz/PLAN.md — thermal visualisation front-end, ratified plan of record (Phase 0 output)

**Status: RATIFIED 2026-07-21 — plan of record; no code exists yet.** Produced by the
Phase 0 session prescribed in `VIZ_SCOPE.md` §4; the eight Phase-0 open questions were
ruled the same day (rulings R1–R8, recorded in §7) and the operative text is folded into
the body sections below. Grounded in this pass's reads of:
CLAUDE.md, SPEC §7T + §11 item-10 bundle, `src/cavity/thermal/__init__.py`,
`src/cavity/figures/` (`__init__`, `_style`, `f3_delta_t_map`, `f5_margin_waterfall`),
`src/cavity/thermal/report_margin.py` / `report_turnover.py` / `report_s_ladder.py`,
`tests/test_figures.py`, `src/cavity/thermal/cylinder.py` (full `solve()` /
`CylinderSolution` source), `src/cavity/provenance/constants.py` (the graded axis
constants), and `docs/field_export_schema.md` (the bundle-schema precedent).

**Positioning (unchanged from VIZ_SCOPE §0, restated as binding):** presentation layer,
not evidence. Rendering only — no new physics, no solves in the COMSOL sense, no thermal
or extraction changes. Never in the claims register, never referenced by
`publication.build`, can never alter a claim grade. No viz work displaces WP1/WP2 hours.

---

## 1. Phase 0 findings (what the repo actually provides)

### 1.1 The figure contract holds and is the right seam

`cavity.figures` modules each provide `CAPTION: str` (committed, pinned verbatim into the
one-pager by `tests/test_figures.py::test_captions_pinned_in_onepager`), a pure
matplotlib-free `build_data() -> dict`, and a lazy-Agg `render()`. `f3_delta_t_map`
computes its field at figure-build time from `cylinder.solve` at the committed
worked-example stack (P = 50 mW ILLUSTRATIVE, n_modes = 64, grid 121 r × 161 z);
`f5_margin_waterfall.build_data()` recomputes the six margin stages through
`detuning`/`broadening` and is data-pinned against the byte-pinned margin report. The viz
exporters mirror this contract exactly.

### 1.2 `cylinder.solve` return type — modal internals are NOT public

`solve(spec, source, n_modes) -> CylinderSolution`. Public surface: attributes `spec`,
`source`, `n_modes`; methods `delta_t(r_m, z_m)`, `peak_k`,
`volume_average_k(r_max_m, z_lo_m, z_hi_m)`, `boundary_power_w() -> {top, base, side,
total}`, `tail_estimate_rel(scalar)`.

The modal factorisation the V1 bundle needs lives entirely in private state:

| internal | content |
|---|---|
| `sol._x` | positive eigenvalues xₙ (λₙ = xₙ/R) |
| `sol._modes` | `_AxialModes`: θ̂ₙ(ζ) closed-form evaluator, plus `f_hat` (radial projections f̂ₙ) |
| `sol._const` | `_ConstantMode` or None (present iff Robin side with h = 0) |
| `sol._theta_unit` | Θ = P·L/(πR²k_z), or 1.0 for driven solves |

`delta_t` reconstructs ΔT(r,z) = Θ·[Σₙ θ̂ₙ(ζ)·J₀(xₙρ) + θ̂const(ζ)]. Per-mode axial
problems are independent (no coupling across n), so **the first-N partial sum of a
64-mode solution is exactly the N-mode solution** — the licence for the mode-count
slider, and a pinnable identity. Root finding for the V2 loci is already public:
`robin_radial_eigenvalues(bi_side, n_modes)` (module-level, tested).

**Accessor decision: build the minimal tested accessor (VIZ_SCOPE's stated fallback).**
No reaching into privates from `cavity.viz`. Spec in §2.

### 1.3 Report generators — data paths for V3/V5

- `report_margin` / `report_turnover` return **markdown strings**, not data dicts; but
  every number flows through importable committed functions (`own_model_point()`,
  `q_loaded`, `resonance_linewidth_hz`, `delta_f_max_hz`, `delta_t_max_k`,
  `q_margin_exponent`) plus module constants (`PLANNING_C0`, `PLANNING_C0_ROWS`,
  `REJUDGE_RUN_DIR`, `_Q_L_GRID` — note `_Q_L_GRID` is private). `f5.build_data()`
  already packages the planning-point numbers. V3's curves need a data-shaped generator:
  either WP3's regeneration delivers one, or Phase 4 adds a pure
  `build_data()` sibling beside `report_turnover` (same committed calls, no new physics).
- `report_s_ladder` exposes its numbers as module-level pure functions
  (`s0_solver_deviation_k`, `s1_field_ratios`, `s1b_per_watt`, `s4_lower_cell`,
  `upper_disc_center_k_per_w`, `upper_volumetric_k_per_w`) plus the committed
  `S4_SYSTEMATIC` string — directly consumable by the V5 bundle. The ballpark-tier
  status sentence itself is inline in `build_report()` (not a named constant) — lifted
  at Phase 6 as its own output-identical micro-commit (R8).

### 1.4 Bundle-schema and determinism precedents

- `docs/field_export_schema.md` (`cavity.export`): version-locked schema
  (`export_schema_version`), **stable keys are contract**, readers refuse unknown
  versions, adding keys within a version allowed. The viz bundles adopt this policy
  verbatim (`viz_bundle_schema_version: 1`).
- `_style.py` determinism discipline: provenance stamps **input identity — never the
  render-time clock or render-time git commit**; regenerating from an unchanged repo must
  reproduce bytes. This **contradicts** VIZ_SCOPE §1.1's proposed header fields
  `commit_sha` + `generated_utc` (HEAD-sha pinning is also circular: committing the
  bundle changes HEAD). **Ruled (R3): both dropped** — for committed artifacts, git
  history is the SHA/timestamp record and the hash-pin test is the integrity mechanism;
  the header carries the deterministic input-identity fields only (generator, constants
  refs, caption, flags).

### 1.5 Graded constants that define the lattice (values read/computed this pass)

| axis | committed source | values | grade riding it |
|---|---|---|---|
| k (W m⁻¹K⁻¹) | `K_PTP` | 0.1 / 0.31622776601683794 / 1.0 | band; 0.1 floor's provenance is a liquid-phase value (caveat carried) |
| l_abs | `L_ABS_PUMP.l_abs_scoping_grid_m` | {5, 10, 20, 50, 100, 200} µm | UNSOURCED-SCOPING, each |
| h_conv (W m⁻²K⁻¹) | `H_CONV_AIR` | 5 / 20 band ends; 0 = the §7.T4 floor | planning assumption; 2026-07-08 regime reframe (open-air ceiling) |
| h_rad (W m⁻²K⁻¹) | `h_rad_linearized(EMISSIVITY_PTP.eps_nominal, 300.0)` | 5.511603935447267 (computed this pass via the committed function) | ε band 0.80–0.95 ratified as-is; additive h_conv + h_rad composition still in the §11 item-10 bundle |
| geometry | `CRYSTAL` | R = 1.5 mm, L = 8 mm | planning dims; Wu cross-build-transfer flag rides |
| base BC | D1 | Dirichlet ("substrate at RT") vs Robin | D1 planning assumption, §11 item-10 |

---

## 2. The accessor (Phase 1, in `cavity.thermal.cylinder`)

One method on `CylinderSolution`; no change to `solve()` or any existing behaviour.

```python
def modal_decomposition(self, r_m, z_m) -> dict:
    """Per-mode factor matrices of the solution on a product grid (viz seam;
    rendering-layer consumer — SPEC-neutral, no new physics).

    Returns {
      "x_n":          (n,) float64 — eigenvalues xₙ, ascending; x_n[0] == 0.0
                       iff the Bi_s = 0 constant mode is present (it counts as
                       one mode, matching solve()'s n_modes convention),
      "theta_k":      (n, n_z) float64 — DIMENSIONAL per-mode axial profiles
                       Θ·θ̂ₙ(z/L) in kelvin (Θ = 1 for driven solves),
      "radial_basis": (n, n_r) float64 — J₀(xₙ·r/R); row of ones for x₀ = 0,
      "f_hat":        (n,) float64 — dimensionless radial projections f̂ₙ
                       (f̂₀ = 1 for the constant mode; zeros for driven solves),
    }
    Invariant: np.einsum('ni,nj->ij', theta_k, radial_basis) equals
    delta_t(r[None, :], z[:, None]) exactly; the first-N row partial sum
    equals the n_modes = N solution exactly (modes are independent).
    """
```

Tests (extend `tests/test_thermal_cylinder.py`):

1. **Reconstruction parity** — einsum of the returned matrices == `delta_t` on the F3
   grid at machine precision (rtol 1e-12), for (a) a Robin-side worked-example config and
   (b) a Bi_s = 0 config (constant mode present) and (c) a driven S0-style solve.
2. **Truncation identity** — sum of the first N rows == `solve(..., n_modes=N)` field on
   the same grid at machine precision, for N ∈ {4, 16} (the mode-count-slider licence).
3. **Conventions** — `x_n` ascending; shapes consistent; `x_n[0] == 0` iff Robin side
   with h = 0; `f_hat` matches the flood closed form for a spot value.

`f_hat` is included now (V2 panel 2 needs it; it already sits on `_modes.f_hat`) so the
accessor is touched once, not twice.

---

## 3. Bundle schemas

### 3.1 Common envelope (every bundle)

```jsonc
{
  "viz_bundle_schema_version": 1,        // stable keys are contract; readers refuse
                                         // versions they do not implement
  "view": "heatmap",                     // heatmap | modes | margin_turnover | s_ladder
  "generator": "cavity.viz.bundles:heatmap_bundle",
  "inputs": {                            // INPUT identity — never clock, never HEAD sha
    "constants": {"K_PTP.k_mid_w_m_k": 0.31622776601683794, ...},  // name → value,
                                         // emitted from the imported objects
    "solver": {"n_modes": 64, "grid_r": 121, "grid_z": 161}
  },
  "caption": "<f3_delta_t_map.CAPTION verbatim, imported>",
  "status_flags": ["ILLUSTRATIVE", "UNSOURCED-SCOPING", ...],   // committed constants
                                         // from cavity/viz/captions.py (R4) —
                                         // never retyped inline
  "payload": { ... }                     // per-view, below
}
```

When the export CLI runs it prints the current HEAD SHA and UTC time **to stdout** (the
local-experimentation record, e.g. against a dirty tree); they are never embedded in a
bundle (R3).

Serialisation (deterministic bytes — the hash-pin substrate):

- canonical JSON: `json.dumps(obj, sort_keys=True, separators=(",", ":"),
  ensure_ascii=True) + "\n"`, UTF-8;
- arrays: little-endian float32 row-major raw bytes, base64, stored as
  `{"dtype": "f4", "shape": [n, m], "b64": "..."}` (float64 only where a pin needs it);
- scalar floats: native JSON via Python repr (shortest-repr, stable on CPython 3);
- SHA-256 of the canonical bytes of every bundle is recorded in `index.json`;
  `tests/test_viz_bundles.py` pins the index hash and regenerates + verifies the full
  set in CI (all-closed-form; seconds).

Delivery format (the `file://` constraint, §5): each bundle is committed as
`viz/data/<name>.js` containing
`window.VIZ_DATA["<name>"] = "<base64(gzip(canonical JSON))>";` — script-tag loadable
(no fetch on `file://`), decompressed in-browser via native `DecompressionStream`
(no dependency). The hash pin is on the **decompressed canonical JSON**, so gzip/zlib
version drift can never silently change pinned content. If measured gzip saving < 30%,
drop compression and embed base64 of the plain JSON (Phase 1 measures; decision rule
stated here so it isn't re-litigated).

### 3.2 V1 heatmap bundles

`viz/data/index.json(.js)` — the manifest:

- axes: the §1.5 table as data — per axis: id, committed source name, ordered values,
  display labels, per-value flag strings. The `radial_profile` axis ships with the
  single populated value `flood` (D3, the F3-pinned choice); `disc` and `gaussian` are
  **reserved slot names in the schema, unpopulated** (R2 — populating them requires a
  committed parameter source that does not exist for the maser geometry);
- scenario list: deterministic lexicographic order over axis indices; per scenario:
  `id` (slug, e.g. `k-mid_bl-200um_hc-20_rad-on_base-dir`), axis coordinates,
  `basis_id`, sha256, scalar summary (peak_k, vol_avg_k at P_ref);
- shared: `r_mm` (121), `z_mm` (161), `p_ref_w` = 0.05 (ILLUSTRATIVE), LUT
  (`SEQUENTIAL_THERMAL` = magma, 256×3 uint8, exported once — colormap parity),
  default scenario id (= the F3 worked-example stack), max energy deficit across the
  lattice, schema version.

`viz/data/bases/<basis_id>.json(.js)` — deduplicated radial bases keyed by
(side-BC kind, Bi_s): `x_n` (float64 — exact eigenvalues are cheap and pin-friendly),
`radial_basis` (n×121 f32). 16 distinct bases for the §4 lattice (computed: 1 for
Bi_s = 0 shared across k, plus 5 nonzero h_eff × 3 k with no h/k collisions).

`viz/data/scenario/<id>.json(.js)` — per scenario:

- `theta_k` (n_kept × 161 f32), `basis_id`, `n_kept`, `truncation_bound_rel`
  (see below), `f_hat` (n_kept f32);
- scalars at P_ref: `peak_k`, `vol_avg_k`, `boundary_power_w` {top, base, side, total},
  `deficit_rel` (= |P − total|/P — the energy panel's residual), `tail_estimate_rel`;
- `n_grid_scalars`: {N: {peak_k, vol_avg_k, deficit_rel}} for N ∈ {4, 8, 16, 32, 48, 64}
  — computed by re-calling `solve()` at each N (pure committed calls; keeps volume/energy
  partial-sum arithmetic in Python. The field + peak partial sums are continuous in N
  client-side via row sums; vol-avg/deficit readouts step this N-grid).

**Mode truncation (recorded, never silent):** rows with per-mode field contribution
< 1e-9 relative to the peak are dropped; `n_kept` and the summed dropped-tail bound
`truncation_bound_rel` ride the bundle and the UI mode-slider caps at `n_kept` with the
bound displayed. Parity budget: float32 transport (~1.2e-7/element) + 1e-9 truncation
≪ the 1e-6 acceptance bound.

**Client-side reconstruction (the only licensed JS arithmetic):**
`field[i][j] = Σₙ theta_k[n][i] · radial_basis[n][j]`, × P/P_ref (exact linearity —
the F3 caption's own licence), partial sums over n ≤ N. No Bessel evaluation, no
formulae, no physics in JS.

### 3.3 V2 modes bundle (`viz/data/modes.json(.js)`)

All arrays precomputed in Python (scipy `j0`/`j1` sampling for display curves is
exporter-side library evaluation, same class as the LUT — no new physics; **no
root-finding or Bessel evaluation in JS**):

- `eigencondition`: x grid (0 → j₀,₁₆ say, 800 pts), curves `x·J1(x)` and, per Bi_s in a
  display grid ({0} ∪ logspace(−3, 3, 25)), `Bi·J0(x)`; root loci `x_n(Bi_s)` for
  n = 1..16 via the public `robin_radial_eigenvalues` (float64). The Bi_s axis is ruled
  acceptable (R7) as a mathematical axis, not a device-parameter control, under three
  binding conditions: (i) labelled derivation-note/illustrative **on-canvas**; (ii) the
  physical device band 0.0075–0.383 overlaid as a highlighted region so a viewer
  immediately sees where reality sits on the sweep; (iii) V2's Bi_s state never feeds V1
  or any device-parameter readout — the tabs share nothing on this axis;
- `mode_shapes`: `radial_basis` rows of the V1 default scenario (reuse its basis bundle —
  no duplicate export), + `f_hat` per radial profile that exists in the lattice (flood
  only — R2);
- `convergence`: none exported — panel 3 reads the V1 default scenario's `theta_k`
  (per-mode |θₙ(0)| = |theta_k[n][0]|, partial sums as in V1). This is what makes the
  V2↔V1 exact-agreement acceptance check meaningful rather than trivially true.

### 3.4 V3 margin/turnover bundle (Phase 4; **entry condition: WP3 regeneration merged**)

Schema is provisional until WP3's data shapes land; committed intent:

- planning point: exactly `f5_margin_waterfall.build_data()`'s dict (already pinned by
  `test_f5_data_pins`), embedded verbatim, + the three `PLANNING_C0_ROWS` Δf_max values;
- curves: Δf_max vs C₀ dense samples (C₀ grid TBD with WP3) × {κs lo, point, hi} ×
  {κc branch: composed-Booth, Wu-print} with per-branch provenance strings; C₀ = 190 as a
  **marked abscissa, never a claimed value** (MQ1);
- turnover: the `report_turnover` Q_L-map rows (Q_L, κc/κs, C₀, Δf_max, E), crossing
  roots Q₋/Q₊, operating point + exponent, fixed-G convention string — via a pure data
  function **on the viz side** (`cavity.viz.bundles`) importing from `report_turnover`
  (R6, kept entirely out of WP3's changeset — that diff rides a ratification cycle to
  Mark). The one permitted `src/cavity/thermal` change is the output-identical rename
  `_Q_L_GRID` → `Q_L_GRID`, its own micro-commit (viz re-declaring its own Q_L grid
  would be a silent-divergence bug waiting to happen). If WP3 later lands a turnover
  figure module with `build_data()`, the viz shim is deleted in favour of it;
- hover readout interpolates **exported samples only** — the threshold formula is never
  reimplemented in JS;
- hard exclusions carried as tests: no `P_max` key anywhere in the bundle (asserted); the
  UNRATIFIED flag string present until the committed constant changes.

### 3.5 V5 S-ladder bundle (Phase 6)

- per rung (S0, S1, S1b, S4-insulated-side, S4-side-cold): a `spec` dict (BC classes +
  values, deposition form, k, drive), a V1-style modal field bundle at that rung's
  committed solver params (S1 N = 256, S4 N = 1024 — mode truncation is what keeps these
  committable; sizes measured at Phase 6 entry), and the rung's scalar table from the
  `report_s_ladder` module functions (bracket pairs, deficits, tails);
- `assumption_diffs`: computed pairwise diffs of the `spec` dicts (the diff **is** the
  content — never hand-authored);
- `S4_SYSTEMATIC` imported verbatim; ballpark-tier flag on every rung (constant lift
  per R8);
- **no inter-rung interpolation of parameters or fields anywhere in the schema** — the
  bundle carries per-rung data only; crossfade is a pure client-side alpha blend.

---

## 4. The V1 scenario lattice, enumerated

Axes (all values from §1.5's committed sources; radial profile is **flood-only, ruled
R2** — `disc`/`gaussian` are reserved schema slots, unpopulated. The only committed beam
parameter, `WU_PUMP_BEAM`, is scoped to the Wu comparison branch: it reaches V5 per-rung
through committed S-ladder code automatically, and licenses no V1 control):

| # | axis | values | count |
|---|---|---|---|
| 1 | k | K_PTP {lo, geometric mid, hi} | 3 |
| 2 | deposition | beer_lambert × l_abs ∈ L_ABS_PUMP grid (6) ∪ {uniform} ∪ {surface} | 8 |
| 3 | h_conv | {0 (§7.T4 floor), 5, 20} | 3 |
| 4 | h_rad | {off, on(ε = 0.90, 300 K) → +5.511603935447267} | 2 |
| 5 | base BC | {Dirichlet (D1 worked example), Robin(h_eff)} | 2 |

Structural choices (stated so they're ratified, not implicit):

- **h_eff = h_conv + h_rad applies jointly to side + top** (one stepper, matching the F3
  worked example); independent per-surface h steppers are out of scope v1.
- **The D1 fork is base-only.** Side and top stay Robin: a Dirichlet side flips the
  radial basis to the J₀-zeros branch where flood deposition has the documented ~1/N
  energy-deficit tail (≈0.6% at N = 64, `boundary_power_w` docstring) — it would fail
  the energy-panel acceptance bound and needs its own convergence treatment. Excluded
  from v1, documented here.
- Robin base takes the same h_eff as side/top.

Constraints: base = Robin ∧ h_eff = 0 → all-insulated, rejected by `CylinderSpec`
(no steady state) → those 3 k × 8 dep = 24 cells are excluded (recorded in the manifest
as structurally invalid, not silently missing). `surface` deposition is valid everywhere
in this lattice (top is never Dirichlet).

**Count: 3 × 8 × 3 × 2 × 2 = 288 − 24 = 264 scenarios**, 16 distinct radial bases.
All closed-form solves at N = 64; full-lattice export ≈ seconds-to-minutes, licence-free
(the F3 docstring's own statement).

Storage arithmetic (pre-truncation, computed): theta 64×161 f32 = 41.2 kB → b64
55 kB/scenario → ≈ 15 MB total; bases 16 × 41 kB ≈ 0.7 MB. With the 1e-9 mode
truncation (flood f̂ₙ decay ~Bi_s/xₙ² ⇒ expected n_kept ≈ 20–35) plus optional gzip,
the expected committed footprint is **≈ 3–6 MB**; Phase 1 records the measured number in
`index.json` and the PR description.

**Stop rule (R1 — bundles are committed; "stop" defined):** Phase 1 measures the total
size of `viz/data/` after truncation (+compression, if adopted). If it exceeds
**10 MB**, Phase 1 **halts before `git add` of any bundle** and re-presents a pruned
lattice — pruning is the mandated response, not a storage-mechanism switch. Prune
levers, in order:

1. Physically meaningless cross-product combos. The v1 lattice already avoids the
   obvious one structurally — `PumpSource` rejects `l_abs_m` off the
   beer_lambert/side_chord forms, so `surface` and `uniform` enter as single variants,
   never × l_abs — but the halt pass re-audits the cross-product for others.
2. **Exact k-degeneracy at h_eff = 0** (identified this pass): with h_eff = 0 every
   Robin surface is insulated and the base is Dirichlet, so all Biot numbers are fixed
   (0 or Dirichlet) and the three k members of each such cell share ONE dimensionless
   field, differing only by the exact 1/k prefactor. 16 of those 24 cells collapse to
   per-k scalars recorded in the manifest (the client multiplies by an exported scalar —
   licensed arithmetic, bit-honest).
3. Genuine lattice cuts, re-presented for approval before committing.

**git-lfs is forbidden for `viz/data/`** — a fresh clone without `lfs pull` would
silently break the viewer, a regression against the very reason bundles are committed.
Manifest + default-scenario-only is the fallback of last resort only, since it demotes
the app from "open index.html" to "run the export CLI first".

Client-continuous controls (exact, licensed): P (linearity; default 50 mW ILLUSTRATIVE,
display range 0–200 mW as a stated display choice) and mode count n ≤ n_kept.
Everything else is a discrete graded stepper labelled with its flag strings.

---

## 5. File layout and front-end decisions

```
src/cavity/viz/
    __init__.py        # contract docstring (mirrors figures/__init__.py bright line)
    captions.py        # committed flag-string constants, derived + subordinate (R4)
    bundles.py         # pure build_bundle() functions; no matplotlib
    export.py          # CLI: python -m cavity.viz.export [view ...] [--out viz/data]
                       #      [--check]  (verify hashes, write nothing — the CI hook);
                       #      lazy-Agg matplotlib import ONLY for the LUT export
viz/
    PLAN.md            # this file
    README.md          # presentation-layer status + exclusions (VIZ_SCOPE §3.5 wording)
    index.html         # single page, tabs; classic scripts (see below)
    app/               # hand-written JS, IIFE-namespaced classic scripts, no build step
    vendor/            # (Phase 5 only) pinned three.js, hash noted in README
    data/              # committed .js-wrapped bundles + index.json (+ .js twin)
tests/
    test_viz_bundles.py  # parity + hash pins + flag/caption imports + exclusion asserts
```

Front-end decisions forced by the `file://` acceptance criterion:

1. **`fetch()` is unavailable on `file://`** → all data ships as script-tag-loadable
   `.js` wrappers (§3.1). `index.html` enumerates the scenario `.js` files from the
   manifest (static `<script>` injection — allowed; still no network).
2. **ES modules are blocked on `file://` in Chromium** (opaque-origin CORS) → the app
   uses classic scripts with IIFE namespacing (`window.VIZ.*`), not `import`. This
   deviates from VIZ_SCOPE §1.2's "plain ES modules" wording in letter, not spirit
   (no bundler, no npm, hand-written files).
3. **V4/three.js (R5 — steer recorded now, executed at Phase 5):** preferred solution is
   pinning an older classic/UMD three.js build — the feature needs are trivial (mesh,
   vertex colours, orbit controls; nothing needs a recent r-version) — which preserves
   the `file://` guarantee. Only if that proves unworkable: document
   `python -m http.server` in the README and relax the `file://` guarantee **for the V4
   tab only**; V1–V3 stay dependency-free and must never inherit V4's loading
   constraints.
4. Colormap parity: the exported 256×RGB magma LUT is the only colour source for field
   rendering in JS; normalisation (shared min/max convention per scenario/state) is part
   of the V1↔V4 shared-state contract.
5. Theme/host: plain light background matching `_style` figure surfaces; no theming
   machinery.

---

## 6. Per-phase task list (acceptance checks copied from VIZ_SCOPE §4, refinements marked)

**Phase 0 — this document.** Output: `viz/PLAN.md`. Ratified 2026-07-21 (this
revision).

**Phase 1 — accessor + exporter + first bundles (~half day).**
Tasks: (1) `CylinderSolution.modal_decomposition` + the three §2 test groups;
(2) `cavity.viz` package skeleton + `captions.py` under the R4 conditions;
(3) `heatmap_bundle(scenario)` + lattice enumeration + `index` builder + canonical
serialiser + `.js` wrapper writer; (4) `python -m cavity.viz.export heatmap` (stdout
SHA/UTC print, R3); (5) `tests/test_viz_bundles.py`; (6) the size measurement and the
R1 stop gate (§4) **before** any bundle is committed.
*Acceptance (verbatim from VIZ_SCOPE):* (a) parity test — outer-product reconstruction
from the bundle matrices matches `sol.delta_t` on the grid to ≤1e-6 relative (float32
transport bound); (b) energy check — `boundary_power_w` residual within the
solver-truncation tolerance the F3 caption claims; (c) bundle bytes hash-pinned;
(d) `ruff`/existing test suite green.
*Refinements:* parity uses atol = 1e-6·peak near Dirichlet zeros; (b) asserts
`deficit_rel ≤ 1e-6` across all 264 scenarios (Robin-side lattice — the documented
fast-tail regime); truncation bound recorded per scenario; measured committed size
reported in the PR.

**Phase 2 — static shell + V1 (~1 day).**
Tasks: `viz/index.html` + tab scaffold; canvas heatmap with LUT parity; graded steppers
with per-value flag labels; P + mode-count sliders; verbatim flag strip (imported
caption/flags rendered from the bundle, never typed in JS); energy panel (residual +
top/base/side split); peak/⟨ΔT⟩ readouts; `viz/README.md`.
*Acceptance (verbatim):* side-by-side screenshot of V1 (defaults) vs
`docs/figures/f3_delta_t_map.png` is visually indistinguishable in field + colormap;
flags render verbatim; works from `file://` with no network.
*Refinements:* default scenario id == the F3 stack (asserted in tests); invalid lattice
cells (all-insulated) render as a labelled disabled state, not an error.

**Phase 3 — V2 mode viewer (~half day).**
Tasks: `modes_bundle()` (§3.3) + export; three linked panels with the R7 conditions
(on-canvas derivation-note label, highlighted device band 0.0075–0.383, no Bi_s state
shared with V1 — structurally: the modes tab holds no reference to the scenario state
object); link panel 3 to V1's mode-count state.
*Acceptance (verbatim):* Bi_s→0 limit shows x₀=0 + J₁ zeros; Bi_s→large approaches J₀
zeros; convergence panel's partial sums agree with V1's mode-count slider readout
exactly.
*Refinement:* "exactly" = identical floating-point sums of the same exported rows (same
data, same summation order in the shared JS helper).

**Phase 4 — V3 margin/turnover tab (entry: WP3 merged; ~half day).**
Tasks: the R6 shim — the `_Q_L_GRID` → `Q_L_GRID` output-identical rename as its own
micro-commit, then the viz-side pure data function importing from `report_turnover`;
`margin_turnover_bundle()`; tab with C₀-axis curves + κs whiskers + κc branch toggle +
turnover map + sample-based hover readout. Nothing in this phase touches WP3's
changeset.
*Acceptance (verbatim):* every displayed number traceable to a regenerated committed
record; the two κc branches labelled with provenance; unratified flag present; no P_max
anywhere.
*Refinement:* "no P_max anywhere" is enforced in `tests/test_viz_bundles.py` (key +
string sweep over the bundle), not just by review.

**Phase 5 — V4 cutaway (~half day).**
Tasks: execute the R5 steer (pinned classic/UMD three.js preferred; fallback per §5
item 3); vendored pinned three.js (hash in README); revolved mesh (270°, cutaway wedge)
coloured by the shared LUT; camera-only controls; shared scenario state with V1.
*Acceptance (verbatim):* colour scale identical to V1 for the same scenario; camera-only
controls.

**Phase 6 — V5 S-ladder (~1 day).**
Tasks: the R8 constant lift — its own micro-commit, output-identical, with the existing
`report_s_ladder` hash pin staying green as the proof (if the report bytes move,
something else moved and the commit is rejected); then `s_ladder_bundle()` (§3.5; rung
fields with recorded mode truncation — sizes measured at entry); crossfade +
assumption-diff panel + animated bracket bars; ballpark flag on every frame.
*Acceptance (verbatim):* the five-second discreteness test; ballpark flag on every
frame; no interpolated parameter values ever displayed.
*Refinement:* the bundle schema itself cannot express an interpolated rung (per-rung
payloads only) — the acceptance is structural, then visual.

---

## 7. Rulings record (2026-07-21 — all eight Phase-0 open questions resolved)

Operative text lives in the body sections cited; this section is the decision record.

- **R1 — data footprint: COMMIT ALL, stop rule defined** (§4). Committed bundles are
  what the report-pinning precedent implies and what keeps `file://` working from a bare
  clone. >10 MB ⇒ halt before `git add`, prune the lattice (meaningless-combo audit;
  the h_eff = 0 exact k-degeneracy lever), re-present. **git-lfs forbidden** (fresh
  clone without `lfs pull` silently breaks the viewer). Manifest+default-only = last
  resort only.
- **R2 — radial profile: flood-only CONFIRMED** (§3.2, §4). No committed a/w exists;
  the F3 caption pins flood as D3; an invented beam radius is exactly the
  unsourced-parameter smuggling the steppers exist to prevent. `disc`/`gaussian` stay
  reserved schema slots, unpopulated. `WU_PUMP_BEAM` is Wu-branch-scoped: V5 inherits it
  per-rung through committed S-ladder code; it licenses no V1 control.
- **R3 — header: `commit_sha` + `generated_utc` DROPPED** (§1.4, §3.1) — the VIZ_SCOPE
  §1.1 fields are withdrawn as a mistake (clock breaks byte-determinism; HEAD-sha is
  chicken-and-egg for a bundle committed in the same commit). Git history is the
  SHA/timestamp record; the hash pin is the integrity mechanism. Deterministic fields
  kept (generator, constants refs, caption, flags); the export CLI prints SHA/UTC to
  stdout for dirty-tree experimentation, never embeds.
- **R4 — `cavity/viz/captions.py` APPROVED, two hard conditions on the cross-pin test**
  (§3.1, Phase 1): (a) every token must appear **verbatim as a substring of its source
  CAPTION**, and the test **fails on orphan tokens** with no caption source — the flag
  list must not be able to drift ahead of the captions; (b) the module docstring states
  it is derived and subordinate — on any conflict, captions win and the token list
  changes, never the reverse. The deeper refactor (tokens in provenance, captions
  composing from them) is deliberately not taken: it would touch pinned figure modules
  and the one-pager pin.
- **R5 — V4 loading: deferred with the steer recorded** (§5 item 3): prefer a pinned
  older classic/UMD three.js build (feature needs are trivial — mesh, vertex colours,
  orbit controls); fallback = README `python -m http.server` note relaxing `file://`
  for the V4 tab only; V1–V3 never inherit V4's loading constraints.
- **R6 — V3 data generator: Phase 4 sibling, OUT of WP3's scope** (§3.4, Phase 4).
  (a) V3 consumes figure-contract `build_data()` dicts wherever WP3 produces them;
  (b) where only the report exists (turnover), the pure data function lives viz-side,
  importing from `report_turnover`; (c) the only permitted src change is the
  output-identical `_Q_L_GRID` → `Q_L_GRID` promotion, its own micro-commit (a viz-side
  re-declared grid would be a silent-divergence bug); (d) if WP3 later lands a turnover
  figure module with `build_data()`, the viz shim is deleted in favour of it.
- **R7 — V2 Bi_s axis: ACCEPTABLE** (§3.3) — the discrete-controls rule governs
  device-parameter controls; this is a mathematical derivation-note axis. Three binding
  conditions: on-canvas derivation-note/illustrative label; highlighted device-band
  overlay (0.0075–0.383); V2's Bi_s state never feeds V1 or any device-parameter
  readout.
- **R8 — S-ladder status-string lift: APPROVED at Phase 6** (§1.3, §3.5, Phase 6) —
  own micro-commit labelled output-identical; proof of output-identity is the existing
  report hash pin staying green through the refactor. If extracting the sentence
  changes the report bytes, something else moved and the commit is rejected.

---

*Ratified 2026-07-21. No code, bundles, or HTML exists as of this revision. Phase 1 is
unblocked and runs as its own session, honouring the WP1/WP2 scheduling rule in
VIZ_SCOPE §0 — the R1 stop gate sits inside Phase 1, before any bundle is committed.*
