# Reference COMSOL models

Supervisor-supplied `.mph` files that the local Python build cannot regenerate
(cf. `.gitignore`: `!refs/**/*.mph`). Tracked via Git LFS — run `git lfs install`
in any fresh clone before pulling. **Do not solve & save** into these files;
keep them as handed over so the geometry/material numbers below remain stable.

Geometry numbers below were read off in COMSOL and recorded here so future
inspections don't need to re-launch the GUI to find out what each file is.

---

## `booth/2D Resonator Lossy.mph`

**STO TE01δ resonator, torus dielectric in a copper cavity.** Closes the
**`dielectric_shape = torus`** half of SPEC §11 gap #1 (Booth's appendix is
ambiguous between puck and torus; this is the torus implementation). The
published-paper dimensions are still outstanding — see "deviations" below.

| | Value |
|---|---|
| Model space | 2D-axisymmetric (r ≥ 0, z ∈ ℝ); revolved about z-axis |
| Cavity rectangle | (r, z) ∈ [0, 22.36] mm × [−16.77, +16.77] mm (symmetric about z = 0) |
| Cavity walls | Copper (impedance boundary) |
| Dielectric cross-section | Circle, center (r = 11.18 mm, z = 0), radius 4.472 mm |
| Torus major radius R | **11.18 mm** (axis → cross-section centroid; sits at the cavity radial midpoint, R = cavity_width / 2) |
| Torus minor radius a | **4.472 mm** |
| Dielectric material | SrTiO₃, εr = 316.3 − j·0.0333378 ⇒ tan δ ≈ 1.054×10⁻⁴ |
| Study | Eigenfrequency, 6 modes around 1.45 GHz, ARPACK |

**Q convention (supervisor-confirmed, in person, 2026-07-02).** This model's Q
is **f′/(2 f″)** from the complex eigenfrequency — the supervisor pointed to
the solved frequencies and had Q computed from them directly. An earlier probe
reading of `imag(emw.freq) = 0` on this file was a **script bug**
(indexing/eval-path), not a genuine energy-method convention — retracted; do
not re-introduce. SPEC §11 gap #4 is resolved on this basis.

**Eval-path mechanism (pinned 2026-07-03, on this file).** In results
evaluation COMSOL realifies the interface-scoped `emw.freq` per solution
number — `imag(emw.freq)` reads 0 for every mode of this lossy solve. The
complex eigenfrequency lives in the **bare solver variable `freq`**
(= iλ/(2π), λ = δ − iω): `imag(freq)` is positive mode-by-mode and
f′/(2 f″) from it reproduces `emw.Qfactor` exactly (e.g. 1.451348 GHz →
Q = 9581.37). This is what the retracted probe got wrong — one prefix.
Guarded in `tests/test_comsol_mph_server.py` (requires_comsol tier).

**Deviations from SPEC §11 Booth nominals (App. A):** box height is 1.82×
Booth's 18.42 mm, dielectric cross-section radius is 1.82× Booth's 2.46 mm,
but cavity radial extent is **3.64×** Booth's 6.14 mm — i.e. *not* a uniform
scale of her published numbers. Treat as a Booth-tradition torus reference,
not as a drop-in replacement for her paper geometry.

**What this anchors in the repo.** This is the first concrete supervisor-
provided STO model with the **right material physics + torus topology** at
the right target frequency. Once §4 (wall-loss decomposition) is wired up,
this model is the natural pin for:
- §3 extraction primitives (`axisymmetric_volume_integral`, `mode_volumes`,
  `electric_filling_factor`, `q_from_eigenfrequency`) against a *real*
  COMSOL eigensolution rather than synthetic fields.
- §8 PEC + lossy-dielectric Q identity: in the PEC limit (copper → PEC),
  `q_from_eigenfrequency` should satisfy `1/(p_e · tan δ)` to within
  `EXTRACTION_TOL.q_pec_lossy_rel_tol`.

---

## `oxborrow/Radiating_Dielectric_mo1.mph`

Oxborrow-library example: open-boundary radiating dielectric resonator
("mo1" mode label). Loss channel is **radiation**, not dielectric tan δ or
wall conduction — a different physics regime from the Booth/STO maser
problem. Useful as a methodological cross-check that `q_from_eigenfrequency`
handles a non-Booth loss mechanism cleanly. **Not load-bearing for Phase 1.**

## `oxborrow/sapphire_ring_1p45_mag_GHz.mph`

Sapphire ring resonator tuned to ~1.45 GHz. εr ≈ 9–10, so geometrically
much larger than the STO equivalent (linear scale ~√(316/10) ≈ 5.6× a same-
mode STO cavity). Anchors the m = 0 axisymmetric ring-mode extraction
protocol at the maser target frequency. **Not** an STO physics analog —
loss mechanisms and field profiles differ.

**Method-reference only (supervisor, 2026-07-02):** weak-form implementation,
lossless, no Q — never a convention source. The STO model is built in the
packaged RF interface (`Electromagnetic Waves, Frequency Domain`, tag `emw`),
per supervisor confirmation; do not derive interface or Q conventions from
this file.

---

## What's still missing (open asks)

1. **Booth's actual paper-geometry `.mph`** — the published (12.28 × 18.42
   mm cavity, 2.46 mm dielectric radius) numbers from SPEC §11 line 31.
   The torus file above does not supply these dimensions.
2. **The `dielectric_shape = puck` variant** — needed for the SPEC §11
   "implement both and let §4 decide" plan.
3. **The Oxborrow 2007 PDF itself** — SPEC §8/§11 line 128 names it as the
   traceability citation; not in the repo yet.
