# SPEC §5a checkpoint — own-model solve at Booth's TE01δ point (2026-07-10)

**Status: FAILED — 2 gated row(s) FAIL.** Live lossy-wall COMSOL solve at the recovered Booth TE01δ geometry (refs/booth_geometry_recovery.md), judged by the committed §5 windows (`gate_targets.py`) — no new tolerances. Gate record: `gate_report.json` in this directory; regenerate this file with `render_checkpoint_markdown(checkpoint_manifest.json)` (byte-pinned in tests/test_report_5a.py).

## Geometry (gated)

- Box radius 12.28 mm, box height 18.42 mm; torus major radius 6.14 mm (= x/2, .mph-pinned free DOF), minor radius 2.456 mm (ratio-exact x/5; gates judged here), centred at the box mid-plane.
- Sensitivity diagnostic at the printed minor radius 2.46 mm (below).

## Material branches (ratified branch choice 1)

- FAITHFUL (gate-passage established here): eps_r' = 316.3, tan_delta = 1.053993e-04 (`BOOTH_MPH_TAN_DELTA`, the .mph-exact unrounded Debye value).
- CANONICAL (SPEC §2; companion — headline Q0 + margin-report feed): eps_r' = 316.3, tan_delta = 1.100000e-04.

## Gate verdicts (SPEC §5 windows, verbatim; faithful branch)

| Check | Measured | Window | Verdict |
|---|---|---|---|
| f at Booth geometry (Hz) | 1450382242.5 | [1.4495e+09, 1.4505e+09] | PASS |
| Q, Impedance walls | 6981.3163 | [6910.2, 7049.8] | PASS |
| V_mode global-max (m^3) | 6.557764e-07 | [4.0491e-07, 4.1309e-07] | FAIL |
| Q_diel (PEC arm) | 9511.4570 | [9000, 10000] | PASS |
| Wall-loss fraction | 0.266010 | [0.23, 0.27] | PASS |
| F_m | 7.1443e+06 | [1e+07, 1e+08] | FAIL |

Material identity: solved at eps_r' = 316.3 = TARGETS.booth pairing (checked by the gate's BoothPayload mismatch guard on every Booth-anchored row).
Gate windows referenced: ±0.5 MHz on f; ±1% on Q and V_mode (BOOTH_TWO_POINT_REL_TOL); TARGETS.q_diel/wall_fraction; F_m in [1e7, 1e8).
Gate tallies: n_pass = 3, n_fail = 2, n_deferred = 1 (confinement trend stays deferred — Breeze-side §7 sweep, out of §5a scope); phase1_complete = false (5-of-6 best case by construction).

## Both branches at the finest level (walls-on arm)

| Quantity | Faithful (gated) | Canonical (companion) |
|---|---|---|
| f' (Hz) | 1450382242.5 | 1450382242.0 |
| Q0 (unloaded) | 6981.3163 | 6764.5852 |
| V_mode global (m^3) | 6.557764e-07 | 6.557764e-07 |
| V_mode local (m^3) | 6.557764e-07 | 6.557764e-07 |
| p_e | 0.9974999897 | 0.9974999897 |
| F_m (global) | 7.144268e+06 | 6.922479e+06 |
| Q_diel (PEC arm) | 9511.4570 | 9113.6450 |
| wall fraction | 0.266010 | 0.257752 |
| record hash | `2b276c4424e49bb9` | `823e67969516bcf2` |

Branch delta, AS MEASURED: Q0_canonical / Q0_faithful = 0.968956 (-3.104%); the canonical branch was NOT judged against the Booth window — gate-passage is a faithful-branch statement only.

## Wall-loss split (§4, sigmas from the ladders)

| Branch | Q_total | Q_diel | Q_wall | sigma_Q_wall | wall fraction | below_resolution |
|---|---|---|---|---|---|---|
| faithful | 6981.3163 | 9511.4570 | 26244.5839 | 0.2072 | 0.266010 | false |
| canonical | 6764.5852 | 9113.6450 | 26244.5549 | 0.2117 | 0.257752 | false |

## Mesh-convergence evidence (full ladders, per branch per arm)

### Faithful — Impedance walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.5 mm | 2 mm | 640 | 1450413575.114388 | 103882.547653 | 6981.0262 | `096e3ba4cbc7ce95` |
| 1 | 0.35355 mm | 1.4142 mm | 1126 | 1450395711.980170 | 103879.044045 | 6981.1757 | `181a34a1d020d142` |
| 2 | 0.25 mm | 1 mm | 2152 | 1450386411.404348 | 103876.743272 | 6981.2855 | `55ae5c143a58fd43` |
| 3 | 0.17678 mm | 0.70711 mm | 3950 | 1450383424.000247 | 103876.168134 | 6981.3098 | `dc949be16dd4d9c3` |
| 4 | 0.125 mm | 0.5 mm | 7492 | 1450382242.546384 | 103875.986982 | 6981.3163 | `2b276c4424e49bb9` |

Deltas f' (Hz): [17863.134, 9300.576, 2987.404, 1181.454]; deltas f'' (Hz): [3.5036, 2.3008, 0.5751, 0.1812]. sigma_f' = 1181.454 Hz, sigma_f'' = 0.1812 Hz, sigma_Q = 0.0134.

### Faithful — PEC walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.5 mm | 2 mm | 640 | 1450441222.855929 | 76247.042967 | 9511.4588 | `07e3dcfadfe17996` |
| 1 | 0.35355 mm | 1.4142 mm | 1126 | 1450423357.145457 | 76246.110435 | 9511.4580 | `79cfb3b2429af5be` |
| 2 | 0.25 mm | 1 mm | 2152 | 1450414054.741373 | 76245.626723 | 9511.4574 | `7ed73f5a09a52232` |
| 3 | 0.17678 mm | 0.70711 mm | 3950 | 1450411066.914332 | 76245.471627 | 9511.4571 | `543412574beb28bd` |
| 4 | 0.125 mm | 0.5 mm | 7492 | 1450409885.339593 | 76245.410405 | 9511.4570 | `ef29422390a4ba7d` |

Deltas f' (Hz): [17865.710, 9302.404, 2987.827, 1181.575]; deltas f'' (Hz): [0.9325, 0.4837, 0.1551, 0.0612]. sigma_f' = 1181.575 Hz, sigma_f'' = 0.0612 Hz, sigma_Q = 0.0109.

### Canonical — Impedance walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.5 mm | 2 mm | 640 | 1450413574.545139 | 107210.709597 | 6764.3129 | `5b9230fcaf97b1c0` |
| 1 | 0.35355 mm | 1.4142 mm | 1126 | 1450395711.410928 | 107207.165287 | 6764.4532 | `4c1831a79b502793` |
| 2 | 0.25 mm | 1 mm | 2152 | 1450386410.835114 | 107204.843403 | 6764.5564 | `9d9190b3ff65e50d` |
| 3 | 0.17678 mm | 0.70711 mm | 3950 | 1450383423.431048 | 107204.261495 | 6764.5791 | `39839639044b6f7a` |
| 4 | 0.125 mm | 0.5 mm | 7492 | 1450382241.977115 | 107204.077671 | 6764.5852 | `823e67969516bcf2` |

Deltas f' (Hz): [17863.134, 9300.576, 2987.404, 1181.454]; deltas f'' (Hz): [3.5443, 2.3219, 0.5819, 0.1838]. sigma_f' = 1181.454 Hz, sigma_f'' = 0.1838 Hz, sigma_Q = 0.0128.

### Canonical — PEC walls

| level | diel h | air h | elements | f' (Hz) | f'' (Hz) | Q | record |
|---|---|---|---|---|---|---|---|
| 0 | 0.5 mm | 2 mm | 640 | 1450441222.319606 | 79575.237847 | 9113.6468 | `700c40a7287a7b4e` |
| 1 | 0.35355 mm | 1.4142 mm | 1126 | 1450423356.609134 | 79574.264610 | 9113.6460 | `edf0632201b15b32` |
| 2 | 0.25 mm | 1 mm | 2152 | 1450414054.205028 | 79573.759784 | 9113.6454 | `821e0d13d00572fe` |
| 3 | 0.17678 mm | 0.70711 mm | 3950 | 1450411066.378033 | 79573.597918 | 9113.6451 | `ccca2e814f2e6f3a` |
| 4 | 0.125 mm | 0.5 mm | 7492 | 1450409884.803289 | 79573.534024 | 9113.6450 | `7670ed7eabe1bb9a` |

Deltas f' (Hz): [17865.710, 9302.404, 2987.827, 1181.575]; deltas f'' (Hz): [0.9732, 0.5048, 0.1619, 0.0639]. sigma_f' = 1181.575 Hz, sigma_f'' = 0.0639 Hz, sigma_Q = 0.0104.

## Finest-level eigenspectrum + TE01δ criteria diagnostics (gated arm)

Faithful branch, Impedance walls, finest level; picked index = 11 (field-symmetry selection, proximity only as tiebreak).

| i | f' (Hz) | f'' (Hz) | picked |
|---|---|---|---|
| 0 | 37.1 | -39953.1668 |  |
| 1 | 405.2 | 14358.3740 |  |
| 2 | 627.1 | -34364.4403 |  |
| 3 | 678.5 | 29590.9154 |  |
| 4 | 879.2 | 6231.6573 |  |
| 5 | 2199.4 | 23622.8548 |  |
| 6 | 16912.3 | -2239.8592 |  |
| 7 | 26281.4 | 217.7626 |  |
| 8 | 31549.9 | -60.8404 |  |
| 9 | 37321.9 | 1158.9494 |  |
| 10 | 394796.8 | 183913.6563 |  |
| 11 | 1450382242.5 | 103875.9870 | **<-** |
| 12 | 2642682793.7 | 137933.8095 |  |
| 13 | 2772095583.5 | 152586.7711 |  |
| 14 | 2837496840.0 | 162044.4622 |  |

TE01δ criteria diagnostics (candidates with Im(f) > 0; azimuthal-E energy fraction / on-axis Hz antinode ratio / axis Hz sign changes):

| f' (Hz) | az-E fraction | antinode ratio | sign changes |
|---|---|---|---|
| 405.2 | 0.000000 | 1.000000 | 2 |
| 678.5 | 0.000000 | 1.000000 | 2 |
| 879.2 | 0.000000 | 1.000000 | 2 |
| 2199.4 | 0.000000 | 1.000000 | 2 |
| 26281.4 | 0.000000 | 1.000000 | 2 |
| 37321.9 | 0.000000 | 1.000000 | 2 |
| 394796.8 | 0.000000 | 1.000000 | 2 |
| 1450382242.5 | 1.000000 | 0.690033 | 0 |
| 2642682793.7 | 0.000000 | 0.020495 | 15 |
| 2772095583.5 | 1.000000 | 0.304229 | 1 |
| 2837496840.0 | 1.000000 | 0.439928 | 0 |

## Printed-2.46 sensitivity solve (diagnostic, not gated)

Faithful branch, walls on, finest mesh, minor radius = 2.46 mm (App. A's 3-s.f. print) vs the gated ratio-exact 2.456 mm:

- f' = 1448975016.7 Hz (delta vs gated: -1407225.9 Hz)
- Q = 6977.7446 (delta vs gated: -3.5717)
- record `74d09ff06761b6be`, 7484 elements.

This solve is the discriminator of the plan's dimension-precision interpretive key: if f under the printed minor radius moves by more than the f-window half-width, a ±0.004 mm print-precision ambiguity matters at gate resolution. Measured: the +0.004 mm print rounding moves f by -1.407 MHz (~2.8x the window half-width) — the f verdict is CONDITIONAL on the ratified ratio-exact 2.456 mm branch (pre-registered choice 3), and the minor radius is a stiff f-lever (~-0.35 MHz/µm).

## Failure analysis (pre-registered keys reviewed)

Observed pattern: f PASS, Q PASS, Q_diel PASS, wall fraction PASS; V_mode (global-max) FAIL (0.6558 cm³ vs Booth's 0.409 cm³, x1.6034); F_m FAIL as its direct arithmetic consequence (F_m ∝ Q/V_mode, 7.1443e+06 vs the [1e7, 1e8) window).

- This pattern is NOT one of the pre-registered interpretive keys (f >> 1.45 GHz => recovery refuted; f within ~1% but outside window => dimension precision; Q out with f/V in => loss model; wall fraction out with Q in => §4 window). Every pre-registered key's trigger quantity PASSED.
- What the passes support: the geometry recovery is EMPIRICALLY SUPPORTED (f lands 4-s.f. correct at the recovered torus; the old puck reading sat near 3.1 GHz), and the loss model is NOT indicted (Q within 0.02% of 6,980 on the faithful branch; §4 split inside both windows).
- V_mode diagnostics from the archived record (§1 re-derivation; NOT §3 outputs, NOT re-judgments): the local-max variant EQUALS the global (0.6558 cm³ — the |H|² max sits in/on the dielectric), so max-location does not explain the excess. E-based conventions do not reproduce Booth either: V_E = 0.8591 cm³ (x2.10), V_eps_E = 0.4804 cm³ (x1.17).
- UNRESOLVED, TWO-SIDED (symmetric statement, per the re-grade discipline): either Booth's printed V_mode uses a definition/normalisation not spanned by the variants above, or the model's field distribution genuinely spreads more than her solve's — f, Q and the loss split are energy-ratio quantities that can agree while the peak-normalised spread disagrees, so the passing rows cannot arbitrate. Neither side is adopted. Booth's V_mode definition is a new supervisor/Booth ask.

## Failure disposition (pre-registered discipline)

- Margin report UNTOUCHED: the cross-build composite (Booth 6,980 x Breeze k = 0.2) stays the headline of `thermal/reports/q_margin_planning_point.md`; no own-model number inherits "§5a-validated" status.
- Export bundle NOT re-minted; the PEC schema example remains the only bundle.
- The wall-loss xfail (`test_booth_table_8_wall_loss_split`) STAYS, reason updated to point at this record: the split itself landed inside both §4 windows, but the §5a pass as a whole is red and the green-path rewrite is not licensed.
- SPEC.md receives a dated FINDING hunk (not a status-cleared hunk); `phase1_complete` remains false (n_pass = 3, n_fail = 2, n_deferred = 1).
- No geometry retuning, no tolerance widening, no branch re-picking. A red result is a committed finding.

## §1 reproducibility

- git commit at solve time: `9d6cc22fd4177f675614bbe07117857b3e67177c` (dirty: true — the §5a pass solves before its own commit by construction; the archive commit is the citation).
- COMSOL version: 6.0.
- Gate report created: 2026-07-10T08:35:40+00:00.
- All §1 SolveRecords under `solves/`; finest gated-arm raw .mph + sensitivity .mph under `mph/` (LFS).
