# maphon thermal visualisation front-end — scoping brief

**Prepared:** 2026-07-21, against `aary1n/maphon` `main` @ `08709d2`. Grounded in:
`src/cavity/figures/` (module contract + `f3_delta_t_map`), `src/cavity/thermal/__init__.py`
(module map), the thermal reports (`q_margin_planning_point`, `q_margin_turnover`,
`s_ladder_ballpark`), and the 2026-07-20 decision memo.

**Status of this document:** planning input for a Claude Code session. Nothing here is
committed; Phase 0 below produces the ratified in-repo plan.

---

## 0. Positioning — what this is and when to build it

This is a **presentation layer, not evidence**. It must sit behind the same bright line the
figures package already declares for itself: *rendering only — no new physics, no solves, no
thermal or extraction changes*. It never appears in the claims register, is never referenced
by `publication.build`, and can never alter a claim grade.

Relative to the decision memo's discipline (§13/§14: drafting dominates; machinery is the
named distraction), the honest scheduling is:

- **Near-term leverage (WP-adjacent):** the interactive margin-vs-C₀ + turnover tab. It is
  the natural live demo for the pre-committed Mark meeting (day-10 deadline) and consumes
  exactly the WP3 re-presentation outputs (C₀-axis curves, both κc branches, κs whiskers).
  Build it *after* WP3's regeneration lands, from the same `build_data()` calls.
- **Reply-latency / low-cost:** the r–z heatmap view and the Bessel-mode viewer. Both are
  thin renderers over existing committed functions; the mode viewer doubles as a
  thesis/viva asset (it animates the no-skipped-steps derivation note).
- **Later (Paper 2 / outreach / thesis):** the 3D cutaway and the S-ladder morph. Candy and
  the most honesty-sensitive view respectively; neither moves a reviewer for Paper 1.

Rule of thumb: no viz work displaces WP1 (communications) or WP2 (drafting) hours. This is
what evenings and blocked afternoons are for.

## 1. Architecture

### 1.1 The seam: exporters as figure-contract siblings

The repo already has the right abstraction. Every figure module provides a **pure,
matplotlib-free `build_data() -> dict`**. The viz layer adds a sibling package:

```
src/cavity/viz/
    __init__.py        # contract docstring, mirrors figures/__init__.py
    bundles.py         # per-view build_bundle() functions (pure)
    export.py          # CLI: python -m cavity.viz.export [view ...]
viz/
    index.html         # single-page static app, tabbed views
    app/               # hand-written ES modules (no build step)
    vendor/            # pinned, vendored third-party JS (three.js only)
    data/              # exported JSON bundles (committed + hash-pinned)
    README.md          # states presentation-layer status + exclusions
```

Each `build_bundle()`:

1. calls **only** committed functions and constants (`cavity.thermal.cylinder.solve`,
   `cavity.thermal.detuning.*`, `cavity.provenance.constants.*`, existing figure
   `build_data()`s where they already compute the needed dict);
2. serialises to JSON with float32 arrays (base64 or flat lists — Claude Code's choice,
   but deterministic byte output is required so bundles can be hash-pinned like reports);
3. stamps a provenance header into every bundle:
   `{generator, commit_sha, constants_refs, caption, status_flags[], generated_utc}` —
   where `caption` and `status_flags` are **imported from the committed caption/constant
   objects, never retyped**.

Tests: one parity test and one hash-pin test per bundle (see acceptance checks, §4).

### 1.2 The front-end: static, no server, near-zero dependencies

- Single `index.html`, tabs per view, plain ES modules. No bundler, no framework, no npm
  in the research repo. Rationale: byte-stability and reviewability match the repo culture;
  a Vite/React stack would drag a lockfile and build artefacts into a provenance-pinned repo.
- 2D views (heatmap, mode viewer, margin/turnover curves) render on `<canvas>`/SVG by hand.
  A regular-grid heatmap is ~40 lines of canvas; no Plotly needed.
- The 3D cutaway is the one justified dependency: vendor a pinned `three.module.js` into
  `viz/vendor/` (committed, hash-noted in the README) so the app works offline forever.
- Colormap parity: export the `_style.SEQUENTIAL_THERMAL` LUT (256×RGB) inside the heatmap
  bundle and use it verbatim in JS, so interactive and paper renders are visually identical.
- Hosting: opens from `file://`; optionally GitHub Pages later. No decision needed now.

### 1.3 In-repo vs separate repo

Recommendation: **in-repo**, as laid out above. The exporters must import `cavity` anyway,
and the pinning/tests machinery is already there. Mitigate bloat by vendoring only three.js
and keeping bundles small (see §2.1 — the modal factorisation keeps the heatmap bundle
~200 KB). If Mark objects to presentation assets in the research repo, the fallback is a
sibling `maphon-viz` repo that pins `maphon` by SHA — defer unless asked.

## 2. The five views

Priority order for building: V1 → V2 → V3 → V4 → V5.

### V1 — Interactive r–z heatmap (the load-bearing view)

**Data source.** A parameterised generalisation of `f3_delta_t_map.build_data()`:
`CylinderSpec` + `PumpSource` + `solve(spec, src, n_modes=64)`.

**The key trick — modal factorisation.** `solve()` returns ΔT(r,z) = Σₙ θₙ(z)·J₀(λₙr).
Instead of shipping a precomputed (161×121) field per scenario, ship two matrices per
scenario: `theta[n_modes][n_z]` and `radial_basis[n_modes][n_r]` (= J₀(λₙ rᵢ), evaluated in
Python). The browser reconstructs the field as one outer-product sum — **bit-identical to
the Python result, zero Bessel evaluation and zero physics in JS**. Bonus interactions this
enables for free:

- **P slider is exact and continuous** (ΔT strictly linear in P — same licence the F3
  caption already claims). Default P = 50 mW with the ILLUSTRATIVE flag displayed.
- **Mode-count slider** (partial sums n ≤ N) shows truncation convergence live — a genuine
  diagnostic, and it feeds V3 directly.

**Controls — discrete graded steppers, not free sliders.** This is the central UI-honesty
decision: the committed inputs are graded bands and discrete BC classes, so the UI steps
between committed values only:

- k: `K_PTP` {band-lo, geometric-mid, band-hi} (with the liquid-phase-floor caveat shown);
- l_abs: the `L_ABS_PUMP` scoping grid (each labelled UNSOURCED-SCOPING);
- h_top/h_side: `H_CONV_AIR` band ends ± `h_rad` toggle (ε from the ratified band);
- BC class per surface: Robin / Dirichlet (the D1 base-BC fork rendered as a labelled fork,
  not a slider);
- deposition: Beer–Lambert / uniform / surface-flux; radial profile: flood / sub-disc /
  Gaussian (D2/D3 labels attached).

Every stepper combination maps to one pre-exported scenario bundle. The lattice is small
(≈ 3 k × 6 l_abs × ~4 h/BC variants × 3 deposition ≈ low hundreds of closed-form solves,
seconds of compute, all licence-free — the F3 docstring is explicit that these are not
COMSOL solves). Only P and mode-count interpolate client-side, because only they are exact.

**Always-visible panels.** (a) The energy diagnostic: `boundary_power_w()["total"]` vs
P_abs, rendered as the residual — this surfaces the repo's own energy-accounting check in
the UI. (b) peak ΔT and ⟨ΔT⟩_vol. (c) The verbatim flag strip: the F3 caption's status
flags (ILLUSTRATIVE, UNSOURCED-SCOPING, D1–D7 pending §11 item-10) imported from the
committed caption constant.

### V2 — Bessel-mode viewer (cheap, high explanatory value)

Animates the derivation note. Three linked panels, all from precomputed arrays:

1. **Eigencondition panel:** curves x·J₁(x) and Bi_s·J₀(x) with their intersections; a
   Bi_s stepper (log-spaced grid from 0 → large) shows the roots migrating from the J₁
   zeros (insulated, including the x₀ = 0 constant mode) to the J₀ zeros (Dirichlet).
   Export root loci xₙ(Bi_s) as a table; no root-finding in JS.
2. **Mode-shape panel:** J₀(λₙr) radial shapes and the source spectrum Fₙ for each radial
   profile (flood / sub-disc(a) / Gaussian(w)) — shows *why* flood converges fast and a
   tight Gaussian doesn't.
3. **Convergence panel:** per-mode |θₙ(0)| and the partial sum of ΔT(0,0) vs n, linked to
   V1's mode-count slider.

**Non-goal:** no editable geometry here; it runs at the committed worked-example stack.

### V3 — Margin-vs-C₀ + turnover interactive (the supervisor demo)

**Entry condition: WP3's regeneration is merged** (the C₀-axis re-presentation and the
Wu-print κc branch). This tab then consumes those regenerated `build_data()` dicts:

- margin Δf_max vs C₀ curves with κs whiskers, C₀ = 190 as a *marked abscissa*, not a
  claimed value (MQ1 discipline);
- κc branch toggle: composed-Booth vs Wu-print — both labelled with their provenance
  chains (MQ2);
- the turnover map E(Q_L) with the operating point marked and the fixed-G convention
  stated on-canvas;
- a hover readout that evaluates Δf_max = ((κc+κs)/2)·√(C₀−1) via values exported from
  `cavity.thermal.detuning` (exported curve samples — the formula is not reimplemented
  in JS; hover interpolates the exported samples).

**Hard exclusions, mirroring the memo's "claims that must not appear":** no P_max headline
anywhere in this tab; no distributional language; planning-tier wording verbatim; the
unratified flag displayed until Mark's ratification lands (at which point the flag string
changes in the committed constants and the bundle regenerates — the UI never edits it).

### V4 — 3D cutaway cylinder

Pure presentation over V1's data: revolve the (n_z × n_r) field through 270°, cutaway wedge
exposing the r–z half-plane, three.js mesh coloured by the exported LUT with identical
normalisation to V1 (shared color scale + shared scenario selection state). Optional: one
or two ΔT isosurfaces (marching over the revolved grid). No new data, no new controls
beyond camera — it inherits V1's scenario state. Build last-but-one; it sells the geometry
in talks and the thesis, not in Paper 1.

### V5 — S-ladder scenario morphing (most honesty-sensitive; build last)

**Data:** per-rung parameter sets, fields (via V1-style bundles per rung), bracket
R-values from `report_s_ladder`'s data path. Ballpark-tier flag (supervisor mandate)
rendered verbatim on every frame.

**The honesty constraint that shapes the design:** rungs are discrete assumption sets. Do
**not** interpolate physical parameters or fields between rungs — a smooth morph through
intermediate parameter values would render pseudo-physics that no committed function ever
computed. Instead:

- **crossfade** between per-rung fields (a purely visual alpha blend, clearly transitional);
- an **assumption-diff panel** that lists exactly which assumptions changed between the two
  rungs (BC class, deposition, h value, …) — the diff *is* the content;
- bracket bars animate as bar-height transitions between per-rung scalars (fine: the
  endpoints are committed numbers; the transition is presentation).

If a reviewer of the UI cannot tell within five seconds that rungs are discrete, V5 has
failed its acceptance check.

## 3. Provenance and honesty guardrails (all views)

1. Rendering only. The viz layer contains no physics: no formula reimplementation in JS,
   no root-finding, no solving. Everything numerical arrives in a bundle produced by
   committed Python.
2. Captions and status flags are imported from committed constants and rendered verbatim.
   Grade vocabulary (ILLUSTRATIVE / UNSOURCED-SCOPING / planning-tier / ballpark-tier /
   pending-ratification) appears wherever the flagged quantity appears.
3. Bundles are deterministic, provenance-stamped (generator + commit SHA), committed, and
   hash-pinned by tests — same treatment as reports.
4. Discrete graded inputs get discrete controls. Continuous controls are allowed only
   where continuity is exact and licensed (P linearity; partial-sum mode count).
5. `viz/README.md` states: presentation layer; excluded from the claims register and from
   `publication.build`; nothing here is evidence.
6. Nothing in the viz layer ships a P_max headline, distributional language, or
   confirmed-tone wording for pending items.

## 4. Phased Claude Code plan with acceptance checks

**Phase 0 — repo-grounded planning (one session, no code).**
Claude Code reads: `CLAUDE.md`, SPEC §7T + §11 item-10 bundle, `src/cavity/thermal/__init__.py`,
`src/cavity/figures/__init__.py` + `_style.py` + `f3_delta_t_map.py` + `f5`/turnover
generators, `report_margin.py`, `report_s_ladder.py`, `tests/test_figures.py`, and the
actual `cylinder.solve` return type (what modal internals `sol` exposes — if θₙ/λₙ aren't
public, Phase 1 adds a minimal, tested accessor rather than reaching into privates).
Output: `viz/PLAN.md` — refined file layout, bundle schemas, the scenario lattice
enumerated, per-phase task list. **You ratify PLAN.md before any code.**

**Phase 1 — exporter + first bundle (~half day).**
`src/cavity/viz/bundles.py` with `heatmap_bundle(scenario) -> dict`, `export.py` CLI,
JSON writer.
*Acceptance:* (a) parity test — outer-product reconstruction from the bundle matrices
matches `sol.delta_t` on the grid to ≤1e-6 relative (float32 transport bound);
(b) energy check — `boundary_power_w` residual within the solver-truncation tolerance the
F3 caption claims; (c) bundle bytes hash-pinned; (d) `ruff`/existing test suite green.

**Phase 2 — static shell + V1 (~1 day).**
`viz/index.html`, tab scaffold, canvas heatmap with LUT parity, graded steppers, P and
mode-count sliders, flag strip, energy panel.
*Acceptance:* side-by-side screenshot of V1 (defaults) vs `docs/figures/f3_delta_t_map.png`
is visually indistinguishable in field + colormap; flags render verbatim; works from
`file://` with no network.

**Phase 3 — V2 mode viewer (~half day).**
Root-loci + Fₙ + convergence bundles; three linked panels.
*Acceptance:* Bi_s→0 limit shows x₀=0 + J₁ zeros; Bi_s→large approaches J₀ zeros;
convergence panel's partial sums agree with V1's mode-count slider readout exactly.

**Phase 4 — V3 margin/turnover tab (entry: WP3 merged; ~half day).**
Consumes the regenerated margin/turnover `build_data()` dicts.
*Acceptance:* every displayed number traceable to a regenerated committed record; the two
κc branches labelled with provenance; unratified flag present; no P_max anywhere.

**Phase 5 — V4 cutaway (~half day).** Vendored three.js; shared scenario state with V1.
*Acceptance:* colour scale identical to V1 for the same scenario; camera-only controls.

**Phase 6 — V5 S-ladder (~1 day).** Crossfade + assumption-diff design per §2.
*Acceptance:* the five-second discreteness test; ballpark flag on every frame; no
interpolated parameter values ever displayed.

## 5. Kickoff prompt for Claude Code

Paste after opening the repo (adjust paths if PLAN.md relocates):

> Read VIZ_SCOPE.md at the repo root [or wherever you place this file], then execute
> Phase 0 only: read CLAUDE.md, SPEC.md §7T and the §11 item-10 bundle, ­
> src/cavity/thermal/__init__.py, src/cavity/figures/ (contract, _style, f3, f5, the
> turnover generator), src/cavity/thermal/report_margin.py and report_s_ladder.py,
> tests/test_figures.py, and the return type of cavity.thermal.cylinder.solve (establish
> whether modal internals θn, λn, and the radial basis are publicly reachable; if not,
> propose the minimal tested accessor). Then write viz/PLAN.md refining the scoping brief:
> exact bundle schemas, the enumerated scenario lattice with its size, the accessor
> decision, and a per-phase task list with the acceptance checks copied in. Do not write
> any other code. Stop after PLAN.md and summarise open questions for me.

## 6. Explicit non-goals

No new physics or solver changes; no COMSOL; no server or database; no framework/bundler;
no npm lockfile in the research repo; no free sliders over unsourced parameters; no
inter-rung interpolation; no claims-register or publication.build integration; no
deployment decisions now; no work displacing WP1/WP2 hours this week.
