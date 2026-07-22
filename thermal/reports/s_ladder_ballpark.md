# SPEC 2026-07-16 outcome 5 — S-ladder ballpark report (2026-07-19)

**Status: BALLPARK-tier scenario ladder — NOT device predictions.**
Regenerate with `python -m cavity.thermal.report_s_ladder`; pinned
content-exact in tests/test_thermal_s_ladder.py.

## Status notes

- Authority: SPEC 2026-07-16 meeting block outcome 5 (late-recorded 2026-07-19), Oxborrow-VERBAL — "think deep, not about details. Ballpark estimates." Zero-licence: no COMSOL anywhere in this block.
- Modelled body: the HOMOGENEOUS crystal cylinder at planning dims (`CRYSTAL`, Breeze 2017: R = 1.5 mm, L = 8 mm), cross-build-transfer flag riding (five published Wu-side indicators lean ~4 mm bore-filling; the SM pump path "<= 4 mm" vs the planning chord 2R = 3 mm rides the same flag). Composite crystal+STO+spacer bodies are ABOVE ballpark tier — out of scope, recorded.
- Steady-state reading, STATED: all numbers are steady-state ΔT for a continuously-ABSORBED power P; the solver is exactly linear in P, so every cell rescales exactly. Wu per-shot energetics are context only: 2.4 J/shot over three 150 us pulses at 500 us intervals (PRL SM; ~5.3 kW instantaneous incident during pulses = 2.4 J / 450 us), single-pulse example ~300 us / 250 mJ (PRL Fig. 2). NO SHOT REPETITION RATE IS IN PRINT — no time-averaged CW power is derivable from the published record without a duty assumption, so the power axis below is a stated scoping grid, not a Wu-derived operating point. Pulse-train transients are out of ladder scope (steady solver, no heat capacity; rho is the one open §6T pull — SPEC §11 item 7).
- k axis: `K_PTP` band [0.1, 1.0] W/m/K, geometric mid 0.3162 (floor-reading provenance; isotropic D6, ~2x anisotropy folded in the band, not swept). All ladder BCs are Dirichlet/insulated, so source-driven ΔT scales EXACTLY as 1/k and drive-driven field RATIOS are k-independent — band-edge values are exact arithmetic on the k_mid tables (x3.162 at the 0.1 floor, x0.3162 at 1.0).
- l_abs axis: `L_ABS_PUMP` scoping grid {5, 10, 20, 50, 100, 200} um — UNSOURCED-SCOPING, never an absolute-DT input — PLUS the optically-thin limit (l_abs = inf): the Wu SM's own bleached/optically-thin regime statement (Eq. S2->S3). The two ends carry different physics readings: the um grid = unbleached small-signal penetration scoping; the inf column = the Wu operating-regime reading. Bleaching is intensity-dependent; the ladder stays linear-in-P, so l_abs is a swept PARAMETER, never a computed function of P.
- Beam/prism: `WU_PUMP_BEAM` (PRL SM p. 1, LITERATURE, proof copy): band height h_b = 2 mm (major axis, vertical), chord width w_b = 1.2 mm (minor axis); band centre z_b = L/2 (the SM's "half way up the inner cylindrical wall" read onto the planning crystal — crystal axial placement itself Q9-open). Uniform-over-ellipse intensity is that constant's recorded planning assumption.
- Band averages are UNWEIGHTED sub-cylinder averages (`volume_average_k` over the band window) — the gain-region H-weighting of §7.T2 stays the consumer's job (module doctrine); the band average is the stated stand-in at ballpark tier.

## S0 — 1D anchor (insulated sides, imposed T_top/T_base)

The exact branch: with Bi_s = 0 the imposed-constant drive expands into the constant mode ONLY (J1 vanishes at its own zeros), so the solver reproduces the closed 1-D form ΔT = ΔT_hot·(1 − z/L) with zero truncation error.

- Analytic cross-check, computed this pass: max |solver − closed form| = 8.88e-16 K per K of drive (machine precision; asserted in CI).
- Conductance G_S0 = k·πR²/L, and the implied hot-face rise ΔT_hot = P/G_S0 at the power grid:

| k (W/m/K) | G_S0 (W/K) | ΔT_hot @ 10 mW (K) | @ 100 mW (K) | @ 1 W (K) |
|---|---|---|---|---|
| 0.1 | 8.8357e-05 | 113 | 1.13e+03 | 1.13e+04 |
| 0.3162 | 2.7941e-04 | 35.8 | 358 | 3.58e+03 |
| 1 | 8.8357e-04 | 11.3 | 113 | 1.13e+03 |

At the band mid-point, ~10 mW of conducted power already implies a ~36 K axial contrast — the meeting's "20-50 K likely buoyancy-enhanced" class (`H_CONV_AIR` append, 2026-07-16) is reached at tens of mW, not watts.

## S1 — 3D end-fired (hot imposed top; cold imposed sides+bottom)

BC configuration, not a source extension (blown-air imposed-T limit: forced air fast enough that the outer crust sits at air temperature — archived notes). Field ratios per kelvin of top drive (k-independent; N = 256):

- ΔT(0, L/2)/ΔT_hot = 0.0026
- volume average /ΔT_hot = 0.0607
- band-window average /ΔT_hot = 0.0017 (z in [3, 5] mm)

Sharp-corner caveat, stated in advance: the imposed-T idealisation is discontinuous along the top rim, so the TOTAL top inflow is log-divergent — the classic mixed-boundary edge singularity. Normalisation, dimensional (module Λ = (L/R)·sqrt(k_r/k_z), not its reciprocal): per mode |p_top,n| ≈ 4πR·sqrt(k_r·k_z)·ΔT_hot/xₙ W, so each mode-doubling adds ≈ 4·R·sqrt(k_r·k_z)·ΔT_hot·ln 2 W, approached from below at finite N — absolutely pinned in CI. A total conductance is NOT a well-posed observable of sharp S1; power coupling rides S0's exact G or the S1b flux conjugate below. Interior/integrated observables converge and are what S1 reports.

Cold-bottom realisability rider (SPEC outcome 5): the as-built seat is INSULATING cross-linked polystyrene with no paste (Oxborrow-WRITTEN 2026-07-17 supersession) — an imposed-cold BOTTOM is a blown-air/forced-contact idealisation, not the current build's seat.

### S1b — flux-conjugate companion (existing machinery)

Top-face flood deposition of absorbed power P, cold side+base — the "certain mW absorbed in the top few hundred microns; where does the heat flow" reading of the archived notes. Per absorbed watt at k_mid = 0.3162 (exact 1/k band scaling; N = 1024, Dirichlet-side flood energy deficit 0.04% — the documented ~1/N class):

- peak (top-face centre) = 359 K/W -> 3.6 K @ 10 mW
- volume average = 16 K/W -> 0.2 K @ 10 mW

## S4 — side-fired, extension (A): azimuthally-smeared m = 0

> In side-fire the heat source and the gain region are the same illuminated prism; the g^2-weighted observable samples exactly the hot spot, and the azimuthal smear dilutes it — the m = 0 result is a structural LOWER bracket on gain-weighted heating, not a neutral approximation.

Stakes (carried): the Wu build itself is SIDE-FIRED — PRL SM: pump through the 3-mm hole in the copper wall, illuminated prism across the bore at the equator — so S4 is the pump geometry of the modelled build and carries future validation weight, not ladder-completeness only.

Deposition: Beer-Lambert along horizontal chords, azimuthally averaged (m = 0), times a uniform axial band at beam height (NOT exponential-from-top); truncated-renormalised so P = absorbed power exactly (D4-consistent). BCs: cold imposed top and base (outcome 5 "cooled top and bottom"); side INSULATED as the headline (conservative-hot) with the side-Dirichlet maximal-side-cooling column bounding the unmodelled crystal->STO side path (D7).

### Lower bracket — m = 0 smear, per absorbed watt at k_mid (N = 1024)

| l_abs | peak@equator (K/W) | band avg (K/W) | vol avg (K/W) | peak@eq, side-cold | band avg, side-cold |
|---|---|---|---|---|---|
| 5 um | 842.2 | 745.6 | 438.1 | 0.8 | 0.6 |
| 10 um | 841.4 | 745.6 | 438.1 | 1.6 | 1.2 |
| 20 um | 839.8 | 745.6 | 438.1 | 3.2 | 2.4 |
| 50 um | 835.2 | 745.6 | 438.1 | 7.7 | 5.9 |
| 100 um | 828.0 | 745.6 | 438.1 | 15.0 | 11.3 |
| 200 um | 815.5 | 745.6 | 438.1 | 29.1 | 20.6 |
| inf (thin) | 821.6 | 745.6 | 438.1 | 147.4 | 55.8 |

Convergence bookkeeping (no silent cap): insulated-side columns — max energy deficit 4.0e-15 (the constant mode carries the deposited power EXACTLY under an insulated side); side-cold columns — max deficit 6.1e-02, at the sharpest l_abs, scaling ~(R/x_max)/l_abs: power deposited inside the unresolved ~R/x_max sliver at the cold wall exits without registering in the truncated basis. The bounding COLUMN's reading (maximal side cooling => near-cold interior) is unaffected in kind; its values understate interior ΔT by at most that class. Max 3-mode tail 1.1e-08 across all cells.

### Upper bracket — spot estimate (3a-adjacent `layered.py` machinery)

The illuminated entry patch on a single-layer slab of thickness 2R = 3 mm grounded cold at the far face, patch scale a_eq = sqrt((h_b/2)(w_b/2)) = 0.775 mm (equal-area equivalence). Assumptions at planning rung: planar slab vs curved wall; ALL absorbed P through one patch (single-sided — the azimuthal smear is absent, which is exactly what makes it an upper member); adiabatic elsewhere. Two patch SHAPES are carried — they are not interchangeable (a Gaussian of 1/e² radius a_eq concentrates more power on-axis than a uniform disc of radius a_eq, so its centre rise is higher); for a FIXED shape, burial only lowers the peak, so each shape's surface limit upper-bounds its buried variants:

- Uniform-disc surface member (`delta_t_disk_center`): 1184 K/W -> 12 K @ 10 mW at k_mid (exact 1/k scaling). Half-space closed-form anchor P/(π·a_eq·k) = 1299 K/W — the slab value sits below it (the cold far face only removes resistance; asserted in CI).
- Gaussian buried member (`delta_t_gaussian_volumetric`, w = a_eq), per absorbed watt at k_mid — monotone-decreasing with burial depth, bounded by the half-space Gaussian surface closed form P/(sqrt(2π)·a_eq·k) = 1629 K/W:

| l_abs | ΔT_peak (K/W) |
|---|---|
| 5 um | 1497 |
| 10 um | 1481 |
| 20 um | 1450 |
| 50 um | 1368 |
| 100 um | 1255 |
| 200 um | 1088 |

For l_abs = inf (bleached), burial along the chord only lowers the peak further: the surface limits above remain the bound.

### Bracket reading

The true gain-weighted heating lies BETWEEN the m = 0 lower bracket and the spot upper bracket — a structural bracket pair, not an error bar. The smear dilutes the prism over 2π azimuth (lower); the spot concentrates all P at one patch (upper). The upper bracket at each l_abs is the LARGER of the two members (they cross near the top of the scoping grid); asserted above the lower bracket's insulated-side peak in CI, per l_abs.

m > 0 azimuthal harmonics: DEFERRED (logged; same discipline as the eccentricity route — averaged main result now, bounded side-study + decision gate before heavier machinery). Recorded here and beside D2 in `cavity.thermal.cylinder`.

## S2 / S3 / S5

- S2: no such rung appears anywhere in the notes. (2026-07-21: the numbering ask is CLOSED AS UNRECOVERABLE — joint recall failure, neither Oxborrow nor the notetaker remembers; in-person meeting, notes archived at calibration/data/raw/oxborrow_meeting_notes_2026-07-21/. The numbering caveat is PERMANENT.)
- S3: label RESERVED — bare heading in the archived notes, content not captured; numbering (typed S4-for-side-fire vs sketch S3) rode the Oxborrow Email B ask, CLOSED AS UNRECOVERABLE 2026-07-21 (joint recall failure, archive above): content-lost, unrecoverable by recall; the label stays permanently reserved, no renumbering. Nothing planned, nothing computed.
- S5: logged-DEFERRED (SPEC outcome 5) — the "steam engine" coolant-channel brainstorm; out of scope (§9 cooling-channel exclusion). Nothing computed.
