# viz/ — thermal visualisation front-end

**Presentation layer, not evidence.** Rendering only — no new physics, no solves,
no thermal or extraction changes. This layer is **excluded from the claims
register and from `publication.build`; nothing here is evidence** and it can
never alter a claim grade (VIZ_SCOPE §3 item 5; viz/PLAN.md Positioning).

Plan of record: `viz/PLAN.md` (RATIFIED 2026-07-21). Built phases:

| phase | content | status |
|---|---|---|
| 1 | `cavity.viz` exporters + the committed v1 bundle set (`viz/data/`) | done |
| 2 | static shell (`index.html`, tab scaffold) + V1 r–z heatmap | done |
| 3–6 | V2 modes · V3 margin/turnover · V4 cutaway · V5 S-ladder | not built |

## Running it

Open `viz/index.html` directly in a browser — it works from `file://` with the
network disabled (that is the acceptance criterion, PLAN §6 Phase 2). No server,
no build step, no npm, no network requests; the only browser requirement is
native `DecompressionStream` (any current Chromium/Firefox/Safari).

Data loads from the committed `viz/data/` bundles (script-tag wrappers;
gzip-or-plain payloads discriminated by magic bytes). Bundles are hash-pinned in
`tests/test_viz_bundles.py` and regenerate via `python -m cavity.viz.export`
(`--check` verifies without writing).

## Front-end constraints (PLAN §5)

- **Classic scripts, IIFE-namespaced (`window.VIZ.*`), not ES modules** — ES
  modules are blocked on `file://` in Chromium (opaque-origin CORS). This
  deviates from VIZ_SCOPE §1.2's "plain ES modules" wording in letter, not
  spirit: no bundler, no framework, hand-written files.
- Colour comes exclusively from the exported `SEQUENTIAL_THERMAL` (magma) LUT in
  the index bundle — colormap parity with the committed F3 figure.
- Captions and status flags render **verbatim from the bundles** — never retyped
  in JS (R4). Grade vocabulary appears wherever the flagged quantity appears.
- The only client-side arithmetic is licensed by PLAN §3.2: the outer-product
  partial sum over exported factor matrices, the exact-linearity × P/P_ref
  rescale, and min/max colour normalisation. No Bessel evaluation, no formula
  reimplementation, no root-finding in JS.
- Discrete graded inputs get discrete steppers; P and mode count are the only
  continuous controls (exact and licensed). Structurally invalid lattice cells
  (all-insulated) render as a labelled disabled state with the manifest's
  recorded reason.
- V1's scenario state lives inside the V1 module closure; no scenario-state
  reference escapes the tab (R7).

## Exclusions (VIZ_SCOPE §3, §6)

No P_max headline, no distributional language, no confirmed-tone wording for
pending items; no free sliders over unsourced parameters; no inter-rung
interpolation (V5, when built); no claims-register or `publication.build`
integration; git-lfs is forbidden for `viz/data/` (R1).
