# Booth TE01δ geometry recovery (2026-07-10)

**Status: document recovery from primary sources in hand, closed by in-repo
cross-checks.** This note is the provenance record behind
`cavity.provenance.constants.BoothTE01DeltaGeometry` / `GEOM_BOOTH_TE01D` and
the §5a checkpoint pass. It closes SPEC §11 gap #1 (Booth's dielectric
cross-section unpinned) from the document side; the §5a live solve provides the
empirical confirmation.

Primary: Booth's thesis, `MEng_thesis-01865045.pdf` (page numbers = PDF pages
of that file). Cross-check artifact: the supervisor-supplied
`refs/comsol/booth/2D Resonator Lossy.mph` (read-off values recorded in
`refs/comsol/README.md`, corrected this pass).

## The recovery, step by step

1. **Appendix A (p. 29) has TWO SrTiO₃ rows**, not one:

   | Row | Resonator Width | Resonator Height | Dielectric Radius |
   |---|---|---|---|
   | TE01δ | 12.28 mm | 18.42 mm | 2.46 mm |
   | Anapole | 22.36 mm | 33.54 mm | 4.472 mm |

2. **The supervisor `.mph` is the ANAPOLE row, verbatim.** The `.mph` read-off
   (README): cavity r ∈ [0, 22.36] mm, z ∈ ±16.77 mm (total height 33.54 mm),
   dielectric circle centre r = 11.18 mm, radius 4.472 mm. Every number matches
   the anapole row exactly **with "Resonator Width" read as the axisymmetric
   r-extent** (box radius), and its solved Q = 9581.37 matches Table 8's
   anapole Q = 9.58E+03 to 3 s.f. The README's earlier "1.82×-scaled torus
   variant / deviations" description was a misidentification produced by
   reading width as a diameter (corrected this pass).

3. **Therefore "Resonator Width" = box radius.** This refutes two committed
   readings simultaneously:
   - SPEC §2's parenthetical "box width 12.28 mm (→ box radius 6.14 mm)";
   - `geometry.py`'s docstring reading of App. A's 2.46 mm as the torus
     *major* radius.

4. **Table 4 (p. 15) fixes the construction ratios**: Box Width x, Box Height
   (3/2)x, Dielectric Radius x/5 — with the text stating "Resonator dimensions
   are always adjusted in a proportionate manner, ensuring set ratios are
   maintained." Checks: TE01δ 18.42 = 1.5 × 12.28 exactly; anapole
   33.54 = 1.5 × 22.36 exactly; anapole 4.472 = 22.36/5 exactly (the ratio
   value printed at 4 s.f.). The TE01δ row's 2.46 is the 3-s.f. print of
   12.28/5 = **2.456 mm** — the "Dielectric Radius" column is the torus
   **cross-section (minor) radius**.

5. **Torus form is Booth's own statement**: "the toroidal resonator" (p. 13);
   "torus-shaped dielectric ring" (p. 16). The puck reading retires at the
   Booth point.

6. **The torus major radius (ring-to-axis distance) is untabulated** — the one
   free DOF. The `.mph` pins it at the radial midpoint: 11.18 = 22.36/2, i.e.
   **x/2**; p. 17 confirms the ring-to-axis distance was never optimised (so
   the midpoint convention is the build convention, not a tuned value).

## Recovered TE01δ geometry (x = 12.28 mm)

| Quantity | Value | Basis |
|---|---|---|
| Box radius | 12.28 mm | App. A width = r-extent (step 3) |
| Box height | 18.42 mm | App. A (= 1.5x exactly, Table 4) |
| Torus minor radius | **2.456 mm** (ratio-exact; printed 2.46) | Table 4 x/5 (step 4) |
| Torus major radius | **6.14 mm** = x/2 | free DOF pinned by `.mph` (step 6) |
| Axial centre | box mid-plane | `.mph` (z = 0 symmetric) |

Gates are judged at the ratio-exact minor radius 2.456 mm (ratified branch
choice 3); one finest-mesh walls-on solve at the printed 2.46 mm is recorded as
a sensitivity diagnostic.

## Also settled from the thesis (same pass)

- **Booth's Q is UNLOADED** — p. 8: "Where losses from external factors like
  coupling are ignored, the resulting measured Q factor is referred to as
  'unloaded'. The unloaded Q factor is what is referred to throughout this
  project." Booth states **no** coupling coefficient (coupling out of scope,
  p. 13) ⇒ k = 0.2 remains Breeze's flagged planning assumption when composing
  κc = f/Q_L; the §5a checkpoint composes it with an own-model Q₀ but does not
  make κc fully own-model.
- **Copper σ = 6.00E+07 S/m printed in Table 3** — Booth-primary corroboration
  of the committed `Copper.sigma` (docstring note added; value untouched).
- **Booth's mesh**: "Extremely fine", max free-space element 1 mm.
- **Booth's Q convention**: Q = ω/(2|δ|) (p. 13) — the committed §3 convention.
- **Faithful-branch tan δ**: the `.mph` material node enters
  εr = 316.3 − j·0.0333378 ⇒ tan δ = 1.05400×10⁻⁴ — the unrounded Debye scaling
  of Table 1's 1.6×10⁻³ @ 22 GHz (Table 2's printed 1.1×10⁻⁴ is its 2-s.f.
  round). Single-sourced as `BOOTH_MPH_TAN_DELTA`; the canonical SPEC §2 value
  1.1×10⁻⁴ is unchanged.

## What this licenses / does not license

- Licenses: the §5a live solve at the recovered geometry (both material
  branches), gated by the committed §5 windows (`gate_targets.py`) — no new
  tolerances.
- Does not license: any claim about Booth's TE01δ numbers until the live gates
  pass; any geometry retuning if they fail (failure = a committed finding);
  the confinement-trend row (Breeze-side sweep, unaffected by this recovery).
