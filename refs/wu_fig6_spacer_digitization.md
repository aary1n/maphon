# Wu 2020 Fig. 6 vector digitization — the spacer is a stepped annular seat

**Date:** 2026-07-18. **Source PDF:** Wu et al., PR Applied 14, 064017 (2020),
archived at `calibration/data/raw/wu_build_papers_2026-07-18/wu2020_pra_14_064017.pdf`
(sha256 `fb39bc6c…` pinned in that archive's MANIFEST; Zotero attachment 8ZL66UT2,
parent X4MH9DCL). **Extraction script:** `refs/wu_fig6_spacer_extract.py` — every
number below is that script's output; re-run it rather than editing this file
(house rule: scoping numbers are computed and re-fittable, never eyeballed).
**Why this exists:** the spacer's form and dimensions appear in no print anywhere
in either Wu paper; Fig. 6 is the only source. Without this record + script the
`WuSTORingGeometry.spacer_*` constants would be eyeballed values. The script also
serves as the STOP tripwire — it exits non-zero if the committed constants ever
disagree with a re-extraction.

## Method

Fig. 6 (journal page 064017-6, PDF page index 5) overlays three coloured outlines
on the simulated |E| map. All three are **vector paths in the PDF** (stroke paths in
the page drawing list), not raster content, so their coordinates are recoverable
exactly:

- **cyan** `RGB (0, 1, 1)` — one rectangle: the STO ring cross-section (the
  calibration object);
- **red** `RGB (1, 0, 0)` — one 6-segment polyline: the cross-linked-polystyrene
  spacer;
- **magenta** `RGB (1, 0.416, 0.973)` — one rectangle: the crystal as drawn in
  Wu's own COMSOL model.

**Calibration** maps PDF points to (r, z) mm via the cyan rectangle alone, using
only literature prints that are independent of the spacer values being derived:
its x-extent spans r = 2.025 → 6.0 mm (I.D. 4.05 mm / O.D. 12.0 mm, Wu 2020
§III.C) and its y-extent spans z = 3.0 → 3.0 + h mm (3 mm deck clearance, Wu 2020;
ring height h **forked** {8.5, 8.6} mm, Q13). Every z-dependent quantity is
computed for **both fork branches** and must agree after rounding to 0.1 mm.
Radial scale: 9.0772 pt/mm.

**Grade: FIGURE-DERIVED, ±≈0.3 mm.** The overlays are hand-placed annotations:
the y/x aspect mismatch vs the printed ring dimensions is +3.3 % (8.5 branch) /
+2.1 % (8.6 branch), i.e. the drawn ring is ~2–3 % taller than the prints imply.
That systematic bounds the trustworthiness of every derived dimension at a few
tenths of a mm; 0.1 mm rounding is reporting resolution, not accuracy.

## Extracted vertices (script output, both branches)

Red spacer polyline, (r, z) mm:

| branch | vertices |
|---|---|
| h = 8.5 | (2.50, 2.98) → (2.50, 0.16) → (8.10, 0.16) → (8.10, 4.50) → (6.12, 4.50) → (6.12, 2.99) → (2.50, 2.99) |
| h = 8.6 | (2.50, 2.98) → (2.50, 0.12) → (8.10, 0.12) → (8.10, 4.52) → (6.12, 4.52) → (6.12, 2.99) → (2.50, 2.99) |

Radial stations are branch-independent (2.50 / 6.12 / 8.10); z-stations shift by
< 0.05 mm between branches. Magenta crystal rectangle: r −0.08…1.95 mm
(axis-touching within slop, dia ≈ 3.9 mm) × z 3.00…11.47 (8.5 branch) /
3.00…11.57 (8.6 branch) — i.e. **full ring height**.

## Findings

1. **The spacer is a stepped ANNULAR SEAT, not a bore plug** — the
   pedestal-vs-plug fork is settled by direct inspection. There is **no red
   material at r < 2.5 mm**: nothing under the bore. The seat comprises a base
   annulus (r 2.5 → 8.1 mm) spanning the deck clearance, plus an **outer
   registration lip** (r 6.1 → 8.1 mm) rising ≈1.5 mm beside the ring's outside
   wall — matching the PRL SM's "held the STO ring … concentrically with respect
   to the cavity's side wall".
2. **Derived constants** (0.1 mm rounding, stable across both fork branches),
   matching `WuSTORingGeometry` field-for-field — the script asserts this:

   | field | derived (mm) | constant |
   |---|---|---|
   | `spacer_base_inner_radius_m` | 2.5 | `2.5e-3` ✓ |
   | `spacer_base_outer_radius_m` | 8.1 | `8.1e-3` ✓ |
   | `spacer_lip_inner_radius_m` | 6.1 | `6.1e-3` ✓ |
   | `spacer_lip_outer_radius_m` | 8.1 | `8.1e-3` ✓ |
   | `spacer_lip_height_m` | 1.5 | `1.5e-3` ✓ |

   `spacer_base_height_m = 3.0e-3` is the **seat identification**, not a drawn
   span: the ring underside seats on the base top, so the base occupies the full
   printed 3 mm deck clearance. Checkable from the figure: the seat top digitizes
   to 2.98–2.99 mm → rounds to 3.0 ✓. The drawn base **bottom** floats
   0.12–0.16 mm above the deck plane — hand-placed-annotation slop, within the
   ±0.3 grade; recorded, not modelled.
3. **Residual tension, recorded not resolved:** the PRL SM's "post … mounted into
   a hole in the PCB" suggests a column continuing below deck level. The figure's
   simulated region stops at the PCB plane (z = 0), so the sub-deck form is
   unmodelled either way.
4. **The magenta crystal is the 5th bore-filling indicator** feeding the R5
   cross-build-transfer flag: Wu's own simulation draws the crystal at
   dia ≈ 3.9 mm × full ring height — bore-filling, and TALLER than Breeze's
   8.0 mm. Feeds the crystal-dimension ask in the Oxborrow email queue; resolves
   nothing here.

## Reproduction

```
python refs/wu_fig6_spacer_extract.py
```

Exits 0 with `PASS` when every derived value matches the committed constant;
exits 1 with `STOP` otherwise (never silently adjust either side — a mismatch
means either the archived PDF changed or the constants did, and both are
provenance events).
