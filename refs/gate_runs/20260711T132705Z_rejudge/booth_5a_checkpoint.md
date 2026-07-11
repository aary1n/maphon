# SPEC §5a checkpoint — own-model solve at Booth's TE01δ point (2026-07-11)

**Status: GREEN — all live-judged rows PASS.** RE-JUDGMENT (no new solve) of the archived `20260710T083340Z_live_comsol` §5a solves under the re-based §5 windows: the booth_two_point/v_mode window's BASIS re-derived from Booth's actual V_mode definition (the 225/360 partial-revolution factor — SPEC §5a finding 2026-07-11, §11 item 8's reserved path) and the F_m row tightened to ±1% consistency vs BOOTH_IMPLIED_F_M; tolerances UNCHANGED (`gate_targets.py`). Every solve record cites the source archive, which is immutable. Gate record: `gate_report.json` in this directory; regenerate this file with `render_checkpoint_markdown(checkpoint_manifest.json)` (byte-pinned in tests/test_report_5a.py).

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
| V_mode global-max (m^3) | 6.557764e-07 | [6.47856e-07, 6.60944e-07] | PASS |
| Q_diel (PEC arm) | 9511.4570 | [9000, 10000] | PASS |
| Wall-loss fraction | 0.266010 | [0.23, 0.27] | PASS |
| F_m | 7.1443e+06 | [7.09197e+06, 7.23524e+06] | PASS |

Material identity: solved at eps_r' = 316.3 = TARGETS.booth pairing (checked by the gate's BoothPayload mismatch guard on every Booth-anchored row).
Gate windows referenced: ±0.5 MHz on f; ±1% on Q (BOOTH_TWO_POINT_REL_TOL); ±1% on V_mode about BOOTH_IMPLIED_V_MODE_M3 (the 225/360-corrected Table 8 print — window basis re-derived, tolerance unchanged); TARGETS.q_diel/wall_fraction; F_m ±1% vs BOOTH_IMPLIED_F_M (order-10^7 re-scoped to the confinement endpoint, deferred).
Gate tallies: n_pass = 5, n_fail = 0, n_deferred = 1 (confinement trend stays deferred — Breeze-side §7 sweep, out of §5a scope); phase1_complete = false (5-of-6 best case by construction).

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

## §5a checkpoint quantities (REPORTED, not gated)

AMENDMENT WORDING (carried verbatim into the margin report and the SPEC §5a hunk): headline = canonical-branch own-model Q0 (the SPEC §2 model Phase 2 runs); gate-passage established on the faithful branch; branch delta quoted as measured. "Own-model, §5a-validated" must never silently attach to a number the gate never saw — the canonical Q0 has NOT itself passed the Booth window.

- Own-model Q0 (canonical, walls-on finest) = 6764.5852; Q_L = Q0/(1 + k) = 5637.1544 with k = 0.2 — k is BREEZE'S coupling (Breeze 2017), carried as a flagged planning assumption: Booth's thesis (p. 8) uses unloaded Q throughout and states no coupling coefficient, so kappa_c below is COMPOSED (own-model Q0 x Breeze k), not fully own-model.
- kappa_c = f/Q_L = 257.2220 kHz (cyclic-Hz FWHM; never angular).
- Δf_max = (kappa_c/2)·sqrt(C0 − 1) at the planning C0 = 190: 1.7681 MHz (C0 stays the SPEC revision-note PLANNING value — a COMSOL solve cannot touch the spin side; §5a's "Booth's own C0" is delivered only in its kappa_c/Q arm).
- ΔT_max (integrated cavity arm + linear spin arm, D8, own-model p_e = 0.997500): 0.6030 K — compare the cross-build composite band [0.567, 0.725] K: the "decisively above threshold, thin thermal margin" story holds at order ~0.5 K.

## Honesty table (status after this pass)

| Quantity | Status | Basis / caveat |
|---|---|---|
| f at Booth point | OWN-MODEL | solve records, both branches |
| Q0 (= Q_total, unloaded) | OWN-MODEL | gated on faithful branch; canonical companion reported |
| Q_diel, Q_wall, wall fraction | OWN-MODEL | §4 two-solve split, ladder sigmas |
| p_e at Booth point | OWN-MODEL | walls-on; retires the 3.14 GHz PEC-puck placeholder |
| V_mode (global/local), F_m | OWN-MODEL | §3 extraction |
| Field record, w_E/w_s | OWN-MODEL | w_s still gain-mask = STO fallback (Phase 1b pending); \|H\|² default UNRATIFIED |
| kappa_c = f/Q_L | COMPOSED: own-model Q0 × k = 0.2 | k is Breeze's; Booth p. 8 is explicit that only unloaded Q is used and coupling is out of scope — the checkpoint does NOT make kappa_c fully own-model |
| C0 = 190 | PLANNING (unchanged) | revision-note value; N assumed, g_s derived, kappa_s fitted |
| eps_r = 316.3, tan_delta, sigma_Cu | LITERATURE INPUTS | own-model outputs are conditional on them |
| df_cavity/dT, df_spin/dT | LITERATURE/DERIVED §6T | untouched (read-only this pass) |
| Booth 6980 print / V_mode print 0.409 cm³ re-based to the implied 0.6544 cm³ (×360/225 — finding 2026-07-11) | LITERATURE anchors | comparison targets only; Booth-side written confirmation of the 225° mechanism PENDING |

## Layer A inheritance

Nominal centre for the Layer A sweep: recovered geometry + canonical materials + the finest ladder level (diel 0.125 mm / air 0.5 mm), named by record hash `823e67969516bcf2`. The convergence tables above are the mesh-level justification Layer A inherits.

## §1 reproducibility

- git commit at re-judgment time: `9e6cf9c459112062a5062793a4f8b6b3f1341053` (dirty: true — the re-judgment runs before its own commit by construction; this record's commit is the citation).
- Source archive: `refs/gate_runs/20260710T083340Z_live_comsol/` (solve-time commit `9d6cc22fd4177f675614bbe07117857b3e67177c`) — IMMUTABLE; no new solve occurred.
- Re-base basis: SPEC §5a finding 2026-07-11 — booth_two_point/v_mode window re-based on BOOTH_IMPLIED_V_MODE_M3 (Table 8 print corrected for the 225/360 partial-revolution factor, BOOTH_TABLE8_REVOLUTION_FACTOR); F_m row re-scoped to ±1% consistency vs BOOTH_IMPLIED_F_M (order-10^7 window moved to the confinement endpoint, deferred). Window BASIS re-derivation per §11 item 8 — tolerances unchanged.
- COMSOL version (of the archived solves): 6.0.
- Gate report created: 2026-07-11T13:27:06+00:00.
- All §1 SolveRecords under the source archive's `solves/`; raw .mph under its `mph/` (LFS). No solve artifacts in this directory.
