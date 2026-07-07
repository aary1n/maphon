# Singh Fig. 2B(iii) vector reanalysis — T_xz ODMR peak vs temperature

**Date:** 2026-07-04. **Source PDF:** Singh et al., Nat. Commun. 16, 10530 (2025),
doi 10.1038/s41467-025-65508-2, journal PDF p. 3 (Zotero attachment X7C3YSRW, parent
FC5RCNEF). **Companion data:** `singh_fig2biii_vector_extraction.csv` (197 points).
**Why this exists:** neither the main text nor the SI (41467_2025_65508_MOESM1_ESM.pdf,
Zotero NNMUUWX5) prints any uncertainty on the region-III T_xz slope (−101 kHz/K quoted
bare in text and SI Table S1); the raw-data Zenodo record (10.5281/zenodo.17231876,
681.8 kB) has **restricted files**. The figure, however, is pure vector graphics
(10,814 paths, zero raster images on the page), so the plotted data are recoverable at
near-source precision.

## Method

Extraction with PyMuPDF from the page's vector drawing list, panel 2B(iii)
(bounding box x ∈ [240, 365], y ∈ [220, 315] in PDF points):

- **Data markers:** 197 fill+stroke paths of size 2.9 × 2.6 pt (green fill); marker
  centre = bbox centre.
- **Axis calibration from the tick-mark vector segments (not the label glyphs):**
  x-ticks at 260.3 / 302.9 / 345.6 pt ↦ 100 / 200 / 300 K (cold-finger);
  y-ticks at 289.7 / 266.1 / 242.5 pt ↦ 1446 / 1450 / 1454 MHz.
  Linearity self-check: middle tick reproduces as 199.88 K and 1450.000 MHz.
- **Paper's fit line:** the only red stroke in the panel is a 3-segment polyline
  spanning cold-finger **254.1 → 323.1 K** with constant slope **−112 kHz/K** in axis
  units.
- **Phase-transition marker:** the dashed "abs. T 193 K" guide is drawn at
  x = 276.7 pt ⇒ cold-finger **≈ 138.5 K**.

RMS residual of the extracted points about the drawn red line over 250–324 K is
232 kHz (≈ 1.3 pt), consistent with marker-size resolution.

## Results

Ordinary least squares on the extracted points (slope ± statistical s.e.):

| fit window (cold-finger K) | slope (kHz/K) | RMSE (kHz) | n |
|---|---|---|---|
| 150–330 (shared region-III span, all 3 panels — see Finding 6) | −68.4 ± 1.7 | 930 | 173 |
| 195–330 | −86.3 ± 1.4 | 544 | 155 |
| 200–330 | −88.0 ± 1.3 | 509 | 153 |
| 220–330 | −96.9 ± 1.2 | 362 | 140 |
| 254–324 (the drawn red line's own span) | **−111.9 ± 1.1** | 204 | 109 |

Local slopes (30 K sliding windows): ≈ −68 kHz/K at 90–120 K (triclinic, region I);
the transition feature (ν jumps *up* ~1.3 MHz) at cold-finger ~125–150 K; then a
near-flat stretch (−2 to −4 kHz/K) at 170–210 K, steepening monotonically to
−131 ± 2 kHz/K at 290–320 K. The curvature in "region III" is real and large.

## Findings

1. **No printed ± exists anywhere** (main text, SI, Table S1). Statistical error on
   any single-window fit is ±1–2 kHz/K — negligible. The dominant uncertainty is the
   **fit-window systematic**: −68 → −112 kHz/K depending on where "region III" starts.
2. **The printed −101 kHz/K matches no stated window and disagrees with the paper's
   own drawn fit line (−112 kHz/K over 254–324 K).** −101 would correspond to an
   unstated window starting near cold-finger ~235 K.
3. **The temperature axis is the cryostat cold-finger.** The 193 K (absolute) marker
   drawn at cold-finger ≈ 138.5 K implies a laser-heating offset of **≈ +55 K** at the
   stated 110 mW cw at sample (Methods p. 6; SI Table S1). The −101/−112 window
   therefore samples actual sample temperatures ≈ 310–380 K, **above room temperature**.
4. **Offset-corrected RT-local slope:** actual 295 K ↦ cold-finger ≈ 240 K (constant-
   offset assumption), where the local slope reads **≈ −70…−80 kHz/K** — consistent
   with Lang 2007 (−70 average) and W20's −80, not with −101.
5. **Against offset constancy:** the flat stretch at cold-finger 170–210 K maps to
   actual ≈ 225–265 K, where Lang's curve is ≈ −50 kHz/K, not ~0. Either the heating
   offset varies with T (contradicting the authors' "constant offset" assertion —
   plausible, since crystal k and boundary couplings are T-dependent) or the samples
   genuinely differ. Both readings argue against importing −101 as a local RT
   coefficient; a growing offset also stretches the axis and inflates |slope| at the
   high-T end.

6. **Correction (2026-07-07): the "150-330 K" bound is not table-sourced for X-Z.**
   Word-position extraction of SI page 4 (Table S1, x-column ≈382-387 pt = the
   df/dT column) shows three footnoted values stacked in the **X-Y** row —
   `6.8a` (y=339.9), `247b` (y=352.8), `8.7c` (y=365.8) — against footnotes a/b/c
   = 77-125 / 125-150 (phase transition) / 150-330 [K, printed as "150-330oC" —
   almost certainly a degree-symbol extraction artifact, not literal Celsius: 77
   is the canonical LN2 cold-finger start, and 330°C exceeds p-terphenyl's
   melting point]. The **X-Z** row's df/dT entry, `101` (y=423.5, same column),
   carries **no footnote at all**. Table S1 never states a window for the X-Z
   slope; footnote (c)'s "150-330" belongs to a different transition's
   high-T sub-value entirely. Main-text Table 1 doesn't tabulate 101 either
   (only 247-XY with the phase-transition asterisk) — the -101 kHz/K figure
   exists only as prose ("101 kHz/K for Txz in region III... red line in Fig.
   2B(iii)"), with no numeric window given anywhere in the paper.
   **Consequence:** every "150-330 K, the SI's region III" framing above (this
   file, SPEC §6T, `constants.py`) is better read as *the shared region I/II/III
   partition drawn across all three Fig. 2B panels* (same crystal, same 193 K
   phase transition, same cold-finger axis) — a reasonable inference, since
   regions are a lattice-phase property not a per-transition one — rather than
   a number read off a footnote attached to the X-Z entry. It was previously
   cited as if it were the latter; it isn't. The downstream numbers (OLS fits,
   the -101-as-band-edge verdict) are unchanged, since they come from the
   vector extraction of the figure itself, not from the table.

**Verdict for §6T:** keep −101 kHz/K as the conservative band edge of the
−50…−101 kHz/K prior; do not promote it to an RT-local value. The band framing is now
empirically supported by Singh's own plotted data, not merely prudent.

## Reproduction

```python
import fitz  # PyMuPDF
doc = fitz.open("<Singh journal PDF>")
page = doc[2]                      # journal p. 3
for d in page.get_drawings():
    r = d["rect"]                  # panel: 240<=x<=365, 220<=y<=315
    # markers: d["type"]=="fs" and r.width<5 and r.height<5 -> centre of r
    # red fit line: stroke colour ~ (0.92, 0.15, 0.16)
# calibration: T = 100 + (x-260.3)*200/(345.6-260.3)
#              nu = 1446 + (289.7-y)*8/(289.7-242.5)
```
