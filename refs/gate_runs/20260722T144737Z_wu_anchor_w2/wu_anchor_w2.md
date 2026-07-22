# W2 — Wu-anchor validation, dual-geometry session (2026-07-22)

**Status: PASS — Run A clears every gated W2 row; this record is the Wu anchor record.** Live COMSOL solves of the Phase 1b Wu-ring model (crystal + spacer sub-domains), judged strictly by the committed windows of `docs/w2_wu_anchor_windows.md` (ratified 2026-07-19; dual-geometry protocol pre-registered in the 2026-07-22 addendum BEFORE any solve — the 2e19187 O.D. hold was lifted by user decision of 2026-07-22, resolved by solving BOTH geometries, not by selecting a branch). No window was revised at solve time. Regenerate this file with `render_w2_markdown(checkpoint_manifest.json)` (byte-pinned in tests/test_report_w2.py).

## Declared deviations

- DECLARED DEVIATION from the pre-registered mesh ladder: base refined by sqrt(2)**1 to (dielectric 3.535534e-04 m, air 1.414214e-03 m) — the committed ConvergenceError's own 'refine further' remedy after the pre-registered base ladder was refused as non-asymptotic (coarse-end f'' delta wiggle; the refused attempt's failure record and solves are archived in their own dated run directory). No convergence criterion was weakened and no window changed.

## The two runs

- **Run A (GATED)** — ring O.D. 12 mm = the carried Wu 2020 print (`GEOM_WU_STO_RING`).
- **Run B (DIAGNOSTIC)** — ring O.D. 12.2 mm = the 2026-07-21 in-person caliper value (provenance corrected 2026-07-22; written confirmation pending; ring-identity claim Oxborrow-verbal). Binds no gate, creates no anchor record, selects no branch.

Identical in every other input (pre-registered): I.D. 4.05 mm; height 8.6 mm (Q13, caliper, written confirmation pending); enclosure radius 14 mm; internal height 15 mm as-operated, flat ceiling; deck 3 mm; spacer ON (CLPS 2.53); crystal present, planning dims 3.0 x 8.0 mm, eps_r = 3 (Q11), axially centred on the ring mid-height plane (LABELLED PLANNING PLACEMENT; Q9 open); canonical materials (eps_r' 316.3, tan_delta 1.1e-4, Cu 6.0e7); 5-level sqrt(2) mesh ladder per arm; full input provenance in `checkpoint_manifest.json` (`input_provenance`).

## W2 verdicts (Run A binds; judged in the pre-registered order, W2.4 first)

| Row | Measured | Window | Verdict |
|---|---|---|---|
| W2.4/v_mode_local_over_global | 1.058353 | [0.9, 1.1] | PASS |
| W2.1/f | 1431191793.1 | [1.42776e+09, 1.47124e+09] | PASS |
| W2.2/q0 | 7152.0822 | [5400, 9000] | PASS |
| W2.3/v_mode_local | 3.492700e-07 | vs 3.20e-07 m^3 (no gate) | REPORT (no gate) |

W2.3 note (convention grade INFERENCE, ratified doc): v_mode_local normalises |H|^2 at the gain-region (crystal) maximum — the Breeze-family per-spin form the SM equations imply; the printed 0.32 cm^3 carries no stated convention, hence report-only.

## W2.1 residual and the eps_r band (stated per the ratified window)

- Run A f residual vs the printed anchor: -18.3082 MHz (-1.2631 %).
- First-order eps_r sensitivity at Run A's own p_e = 0.997693: df/deps_r = -2.2572 MHz per unit eps_r about the canonical 316.3.
- f reachable inside the eps_r band [312, 318]: [1.427355, 1.440898] GHz — the printed 1.4495 GHz is NOT reachable inside the band.

## Both runs at the finest level (walls-on arm)

| Quantity | Run A (print 12.0) | Run B (measured 12.2) |
|---|---|---|
| f' (Hz) | 1431191793.1 | 1413528906.9 |
| Q0 (unloaded) | 7152.0822 | 7102.5198 |
| V_mode local (m^3) | 3.492700e-07 | 3.599213e-07 |
| V_mode global (m^3) | 3.300129e-07 | 3.400930e-07 |
| local/global ratio | 1.058353 | 1.058303 |
| p_e | 0.9976927392 | 0.9977994991 |
| Q_diel (PEC arm) | 9111.9522 | 9111.4615 |
| wall fraction | 0.215088 | 0.220485 |
| record hash | `b8895aa479464763` | `22d36d91a235e9e1` |

## Run B diagnostic — O.D. sensitivity (a deliverable of the session regardless of pass/fail)

- delta O.D. = +0.2 mm (print -> measured).
- delta f = -17.6629 MHz => implied local sensitivity d f / d O.D. = -88.3144 GHz/m = -88.3144 MHz/mm.
- delta Q0 = -49.5624 => implied local sensitivity d Q0 / d O.D. = -247811.9657 /m = -247.8120 /mm.
- f residuals vs the printed 1.4495 GHz: Run A -18.3082 MHz, Run B -35.9711 MHz. Q0 residuals vs 7,200: Run A -47.9178, Run B -97.4802.
- INFORMATIONAL (no gate, no branch selection): the geometry whose f sits nearer the printed anchor is **Run A (print 12.0 mm)**.

## Wall-loss split (both runs, sigmas from the ladders)

| Run | Q_total | Q_diel | Q_wall | sigma_Q_wall | wall fraction | below_resolution |
|---|---|---|---|---|---|---|
| A (print) | 7152.0822 | 9111.9522 | 33251.9159 | 0.0843 | 0.215088 | false |
| B (measured) | 7102.5198 | 9111.4615 | 32213.1482 | 0.0809 | 0.220485 | false |

## Mesh-convergence evidence (full ladders, per run per arm)

### Run A — Impedance walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.35355 mm | 1.4142 mm | 1847 | 1431197455.847860 | 100056.609055 | 7151.9386 | `7f181da38404c9f1` |
| 1 | 0.25 mm | 1 mm | 2886 | 1431194216.815281 | 100055.056657 | 7152.0334 | `6b663c8fe345500c` |
| 2 | 0.17678 mm | 0.70711 mm | 5098 | 1431192653.255202 | 100054.460678 | 7152.0682 | `0d6f99f2c935a7aa` |
| 3 | 0.125 mm | 0.5 mm | 9126 | 1431191994.344308 | 100054.254520 | 7152.0796 | `226744cf60715e86` |
| 4 | 0.088388 mm | 0.35355 mm | 17217 | 1431191793.135127 | 100054.204132 | 7152.0822 | `b8895aa479464763` |

sigma_f' = 201.209 Hz, sigma_f'' = 0.0504 Hz, sigma_Q = 0.0037.

### Run A — PEC walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.35355 mm | 1.4142 mm | 1847 | 1431218987.747014 | 78535.252358 | 9111.9526 | `4e0a435e6fa6bf05` |
| 1 | 0.25 mm | 1 mm | 2886 | 1431215747.330348 | 78535.075954 | 9111.9524 | `6154062c41061261` |
| 2 | 0.17678 mm | 0.70711 mm | 5098 | 1431214183.255389 | 78534.991039 | 9111.9523 | `e57351b326159a02` |
| 3 | 0.125 mm | 0.5 mm | 9126 | 1431213524.172275 | 78534.955369 | 9111.9522 | `8524de1f182acf3e` |
| 4 | 0.088388 mm | 0.35355 mm | 17217 | 1431213322.923131 | 78534.944498 | 9111.9522 | `640eb28b5a987aff` |

sigma_f' = 201.249 Hz, sigma_f'' = 0.0109 Hz, sigma_Q = 0.0018.

### Run B — Impedance walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.35355 mm | 1.4142 mm | 1574 | 1413534816.265343 | 99511.386319 | 7102.3773 | `009ed75d57d4bda1` |
| 1 | 0.25 mm | 1 mm | 2750 | 1413531499.427141 | 99509.862763 | 7102.4693 | `1a9cf8fbd5ee279d` |
| 2 | 0.17678 mm | 0.70711 mm | 4978 | 1413529766.818848 | 99509.223238 | 7102.5063 | `39a19b0ee2980267` |
| 3 | 0.125 mm | 0.5 mm | 9236 | 1413529112.269841 | 99509.023397 | 7102.5173 | `40854fea6a2dd4fd` |
| 4 | 0.088388 mm | 0.35355 mm | 17529 | 1413528906.887195 | 99508.972664 | 7102.5198 | `22d36d91a235e9e1` |

sigma_f' = 205.383 Hz, sigma_f'' = 0.0507 Hz, sigma_Q = 0.0038.

### Run B — PEC walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.35355 mm | 1.4142 mm | 1574 | 1413556768.150067 | 77570.250498 | 9111.4619 | `4689e43d07d075fe` |
| 1 | 0.25 mm | 1 mm | 2750 | 1413553449.961251 | 77570.069944 | 9111.4617 | `9c9f7b5ca36697f2` |
| 2 | 0.17678 mm | 0.70711 mm | 4978 | 1413551716.803007 | 77569.975923 | 9111.4616 | `a97ad8e41b9ef118` |
| 3 | 0.125 mm | 0.5 mm | 9236 | 1413551062.088097 | 77569.940513 | 9111.4616 | `578157111a695765` |
| 4 | 0.088388 mm | 0.35355 mm | 17529 | 1413550856.665406 | 77569.929407 | 9111.4615 | `bf1115ef62df81c1` |

sigma_f' = 205.423 Hz, sigma_f'' = 0.0111 Hz, sigma_Q = 0.0019.

## Finest-level eigenspectrum + TE01delta diagnostics (Run A, gated arm)

Picked index = 9 (field-symmetry selection, proximity only as tiebreak).

| i | f' (Hz) | f'' (Hz) | picked |
|---|---|---|---|
| 0 | 56.5 | 66804.2537 |  |
| 1 | 282.7 | 41289.3863 |  |
| 2 | 535.9 | -51752.8673 |  |
| 3 | 3259.5 | 15824.2341 |  |
| 4 | 4229.5 | 4604.5470 |  |
| 5 | 36599.8 | -1019.8148 |  |
| 6 | 47212.1 | 86.2325 |  |
| 7 | 65747.6 | -492.0119 |  |
| 8 | 654927.2 | -97776.4630 |  |
| 9 | 1431191793.1 | 100054.2041 | **<-** |
| 10 | 2026931765.1 | 132543.8819 |  |
| 11 | 2384761270.5 | 128111.2509 |  |
| 12 | 2773396453.3 | 169574.5438 |  |
| 13 | 2937055992.1 | 165273.6924 |  |
| 14 | 2942327547.1 | 160872.6929 |  |

## Anchor-record disposition (pre-registered conditions)

Run A PASSED every gated row: **this archive is the Wu anchor record**, and the Wu-build sweep-centre record is created from it (design-doc 2026-07-19 addendum; pinned import-only in `cavity.sweep.wu_anchor`). Run B remains diagnostic: no anchor, no branch — the O.D. question stays with the confirmation email (which should the model carry, and is a caliper band available?).

## Reproducibility (SPEC §1)

- git commit at solve time: `550e83727f6a1b0664f60f8eea6e4eec50990e8a` (dirty: true — the session solves before its own commit by construction; the archive commit is the citation).
- COMSOL version: 6.0.
- All solve records under `solves/` (schema v3 — crystal fields in the fingerprint); finest-arm raw .mph under `mph/` (LFS); verdicts in `gate_report.json`; full structured summary in `checkpoint_manifest.json`.
