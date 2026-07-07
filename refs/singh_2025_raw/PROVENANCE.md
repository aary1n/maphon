# Singh 2025 raw Fig. 2B data — provenance note

**Date received:** 2026-07-07. **Sender:** Harpreet Singh (first author, Singh et al.,
*Nat. Commun.* 16, 10530 (2025), doi 10.1038/s41467-025-65508-2 — Ajoy group, Berkeley).
**Route:** via the Berkeley contact thread (Noella D'Souza / Joseph Garrett). **What was
asked:** the raw data behind the Fig. 2B transition-frequency-vs-temperature series —
the df/dT slopes whose printed values carry no uncertainty and no fit window anywhere in
print (main text, Table 1, SI Table S1; see `../singh_fig2biii_reanalysis.md`).

**Archival discipline:** the three `.txt` files are stored **verbatim, byte-for-byte as
received — never edit them**. Plain git (not LFS: `.gitattributes` routes only
`*.mph`/`*.pdf`/gate-run `*.npz` through LFS; small text data follows the
`singh_fig2biii_vector_extraction.csv` precedent), with EOL normalization disabled for
this directory (`refs/singh_2025_raw/** -text` in `.gitattributes`) so checkouts
reproduce the received bytes exactly. SHA-256 pins are asserted in
`tests/test_provenance_df_spin_dt.py`; all quantitative use routes through the committed
fit script `cavity.provenance.singh_raw_fits` (report: `fit_report.md` beside this note).

## Inventory

| file | transition | N | T range (file axis, K) | SHA-256 |
|---|---|---|---|---|
| `Fig2B_(iii)XZ_xztemp.txt` | X–Z, 1.45 GHz (**the maser transition — load-bearing**) | 197 | 80.05–329.57 | `9a0a513a59cb03bb3c335620f27c58c13bd729881fe552e75d6e26925bb98828` |
| `Fig2B(i)_XY_XYdata.txt` | X–Y, ~107 MHz | 260 | 79.21–330.08 | `73e61d6281ef155b6cc8676eb6e98b1a8ce5f02f41802c69c71fe593453e9fc2` |
| `Fig2B(ii)_YZ_YZdata.txt` | Y–Z, ~1.34 GHz | 356 | 79.48–305.07 | `2c24de00e9630e3cfae95a2e1524d5a752436c78facf1b02afb8fa01934d185d` |

Format observations (audit, 2026-07-07):

- **XZ:** sorted ascending in T, 5-decimal temperatures, frequency quantised to a
  0.1 MHz grid. Phase-transition feature: local minimum 1454.4 MHz at T = 123.8, sharp
  **+0.9 MHz jump between T = 130.41 and 133.62** (midpoint ≈ 132.0), plateau 1455.9 to
  ~146, monotone decline above ~150. N = 197 **exactly matches** the marker count of the
  Fig. 2B(iii) vector extraction.
- **XY:** same format family as XZ (sorted, 5-dp T, 0.1 MHz grid). **+1.5 MHz jump
  between T = 130.39 and 132.65** — same file-axis location as XZ (same crystal/axis).
  One internal blank row at T ≈ 194–195 (acquisition-session break? — open ask).
- **YZ:** different export path — header `#Temperature Frequency` (vs `#Temp .. Peak
  Freq ..`), temperatures to only 2 dp, **sorted by frequency, not temperature**, 2
  duplicate T values, no data above 305.07 K, and **CRLF line endings** (XZ/XY are LF
  with a trailing blank line — a third marker of the separate export path). Visibly
  noisier: fit RMSE ≈ 0.5 MHz (vs 0.2 for XZ over the red-line span); at fixed 0.1 MHz
  frequency bin the temperatures scatter with median span ≈ 21 K near RT.

## What these files are believed to be (and what cannot be known without metadata)

Believed: the **per-panel plotted point lists** exported from the authors' analysis
(evidence: XZ N = 197 = the figure's marker count; the 0.1 MHz frequency grid — a peak
position/sweep-step resolution; 5-dp processed temperature values). They are **not** raw
spectra or as-acquired peak logs. Unknowable without Harpreet metadata: which sensor the
T column reads (cold-finger vs sample stage vs recalibrated), the peak-fitting/averaging
applied per point, whether 0.1 MHz is the MW sweep step or export rounding, per-point
uncertainties, and why YZ follows a different export path.

## Temperature-axis finding (2026-07-07 — symmetric, unresolved)

Pairing the 197 XZ raw points with the 197 extracted Fig. 2B(iii) marker centres (rank
order in T): frequency residuals rms 40 kHz ≈ the 0.1 MHz quantisation floor (pairing
confirmed), while **the two temperature axes differ by an exact affine map,
T_fig = 0.9316·T_raw + 16.56 K (rms residual 0.09 K)**. Slopes expressed in figure-axis
units are therefore inflated ×1.073 relative to this file's axis — which reconciles the
printed −101 kHz/K (raw OLS over the red-line span: −102.3 ± 1.1) with the re-digitised
−112 (faithful reading of the figure). **Which side carries the calibrated sensor
reading is unresolved**: the file's 5-dp values look sensor-native (the likelier
reading), but a publication-side recalibration of the file data is the live alternative
— the metadata ask below decides it. Do not record either axis as "the correct one".

## Open metadata asks (route to Harpreet)

1. Which temperature is the T column: cold-finger sensor, sample-stage sensor, or a
   corrected/recalibrated sample temperature? The published Fig. 2B x-axis relates to
   this file's T by T_fig = 0.932·T_file + 16.6 K — which of the two is the direct
   sensor reading, and what produced the rescaling?
2. Are these files the as-plotted point lists or as-acquired peak centres? What
   per-point processing (peak-fit method, averaging)? Why 5-dp T for XZ/XY but 2-dp,
   frequency-sorted for YZ? What is the blank row at T ≈ 194 K in the XY file?
3. Is 0.1 MHz the ODMR sweep step (quantisation) or export rounding? Are per-point
   peak-fit uncertainties available?
4. What exact fit window (and which temperature axis) produced the printed
   −101 kHz/K X–Z slope?
5. Was the laser power at sample constant across the sweep (110 mW cw per Methods)?
   Any estimate of the cold-finger→sample offset and its temperature dependence?
6. Are these files identical in content to the restricted Zenodo record
   10.5281/zenodo.17231876?
7. XY / YZ / XZ: same crystal, same cooldown/run?

## Attribution

Acknowledgement/attribution for any use of this data is a conversation to broker via
Oxborrow **early, not at submission** — the same guard as the Cowley-Semple ODMR
dataset (SPEC §7-expanded §7.8 data-status guard; SPEC §11 item 5 co-authorship rider).
The data were shared person-to-person, not via the (restricted) public record.
