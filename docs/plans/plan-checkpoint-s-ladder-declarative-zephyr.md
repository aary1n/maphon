# PLAN — S-ladder: thermal scenario ladder S0/S1/S4 on `cavity.thermal.cylinder`

**Status: RATIFIED WITH AMENDMENTS 2026-07-19 — implementation authorized (three-prompt discipline, prompt 2).**
*(Status update 2026-07-19, dated — EXECUTED same day, branch `s-ladder`, commits 8906bb9 / 7a345ff / c113346, unpushed for review. Collected 843 → 873 exactly as amended. Deviation from §Ordered-sequence step 7: plan commits (i)+(ii) merged into one solver commit — the band and driven changes are entangled in cylinder.py — with amendment 1 landing as its own provenance commit; three commits total, contents as planned. In-flight numerical findings fixed before pinning, both caught by the T1/T4 gates: the profile quadrature needed 48ℓ (not 16ℓ) shell grading plus a ρ = β + u² cusp substitution at the beam edge; the S1 volume-average stability assertion re-based from a fixed tolerance to the true ~1/N² contrast law; the report's deficit bookkeeping split by side-BC column (the side-Dirichlet boundary-sliver deficit ~(R/x_max)/l_abs, attributed) and the upper-bracket members labelled by patch shape (uniform disc vs Gaussian) with both half-space anchors so the conservative-hot claim is stated within-shape.)* Amendments of record:
1. The PRL-SM beam/prism dims (h_b = 2.0 mm, w_b = 1.2 mm, A_p ≈ 1.9 mm²) land as a graded provenance dataclass (`WuPumpBeamGeometry` / `WU_PUMP_BEAM`: LITERATURE, proof-copy note, uniform-intensity planning caveat in the docstring), consumed by the report generator rather than as generator literals; +1 pin test in `tests/test_provenance_wu_geometry.py`. **After-count: 873, not 872** (delta +30).
2. Step-0 collision grep word-boundary and/or path-scoped to `src/cavity/thermal/` + its two test files (`dt_k` substring-matches `probe_average_dt_k` in the calibration tests — not a true collision; the grep must not spuriously STOP).
3. STOP labels S1–S5 renamed **T1–T5** (avoid colliding with scenario names S0–S5); T0 unchanged.
S1b companion column accepted as proposed. Commits per the plan's sequence, unpushed for review.
Prompt of record: PLAN CHECKPOINT 2026-07-19. Ballpark tier, zero-licence: no COMSOL anywhere in this block. Authority: SPEC.md 2026-07-16 meeting block, outcome 5 (late-recorded 2026-07-19; Oxborrow-VERBAL — "think deep, not about details. Ballpark estimates"); archived notes `calibration/data/raw/oxborrow_meeting_notes_2026-07-16/`; the solver `src/cavity/thermal/cylinder.py`.

---

## Context

Outcome 5 of the 2026-07-16 meeting directs a ballpark-tier ladder of idealised thermal scenarios for the crystal assembly, extending `cavity.thermal.cylinder`. Ratified scoping (not re-litigated here): **S0** — 1D anchor, insulated sides (Bi_s → 0 branch), imposed T_top and T_bottom, role = the ladder's analytic cross-check. **S1** — 3D end-fired reading: hot imposed T on top, cold imposed T on sides and bottom (the blown-air imposed-T limit); a BC configuration, not a source extension. **S4** — side-fired, extension (A) only: azimuthally-smeared side deposition at m = 0, Beer-Lambert along horizontal chords averaged over azimuth, axial factor a band at beam height; the separable P·f(r)·g(z) structure and the Robin eigenbasis retained; m > 0 deferred (logged, eccentricity-route discipline). **S3** label reserved (numbering/content pending Oxborrow, Email B) — nothing planned. **S5** logged-deferred. Modelled body: the homogeneous crystal cylinder at planning dims (`provenance.CRYSTAL`), Wu cross-build-transfer flag riding; composite crystal+STO+spacer bodies are above ballpark tier — out of scope, recorded as such.

S4 stakes (carried): the Wu build itself is side-fired — PRL SM: pump through the 3-mm hole in the cavity wall, illuminated prism across the bore — so S4 is the pump geometry of the modelled build and carries future validation weight, not ladder-completeness only.

S4 systematic, VERBATIM (rides this plan and every S4 output):

> "In side-fire the heat source and the gain region are the same illuminated prism; the g^2-weighted observable samples exactly the hot spot, and the azimuthal smear dilutes it — the m = 0 result is a structural LOWER bracket on gain-weighted heating, not a neutral approximation."

The plan therefore includes an UPPER bracket deliverable: a simple spot estimate (strip/line-source conduction class, 3a-adjacent machinery), assumptions stated at planning rung.

---

## What was READ this session vs assumed

**Read in full, this session:**
- `src/cavity/thermal/cylinder.py` — entire module: docstring (geometry/conventions, source-term D2–D4 conventions, radial eigenproblem, dimensionless formulation, convergence caveats, SPEC-silent decisions D1–D7) and the complete implementation (`SurfaceBC`, `CylinderSpec`, `PumpSource`, `robin_radial_eigenvalues`, `_radial_projection`, `_AxialModes`, `_ConstantMode`, `CylinderSolution`, `solve`).
- `calibration/data/raw/oxborrow_meeting_notes_2026-07-16/cont_notes_oxborrow_1607.md` — the archived contemporaneous notes, in full (the S0/S1/S3/S4/S5 bullet run, the imposed-T/blown-air framing, the no-heat-flow-side framing, the Vaseline/paste stack, the CPW material).
- SPEC.md: the full 2026-07-16 outcome block (items 1–5, incl. the late-recorded outcome 5 and its no-paste rider), §6 + §6T (K_PTP, L_ABS_PUMP context, pump-illumination bullet), §7/§7.T1–§7.T7, §11 items 5–9, the 2026-07-17/18 re-base block.
- Wu 2021 PRL SM (proof copy, archived `calibration/data/raw/wu_build_papers_2026-07-18/wu2021_prl_sm_proof.pdf`), §I in full — the pump/prism paragraph read verbatim this session: 590-nm long-pulsed dye laser, collimated beam ∼2 mm dia through a 3-mm hole in the copper wall; STO ring acts as cylindrical beam compressor (×∼0.61 width) with the STO–crystal interface as compensating diverging lens; beam through the crystal near-collimated, elliptical cross-section ∼2 mm height (major) × ∼1.2 mm width (minor), A_p ∼ 1.9 mm²; illuminated volume ≈ elliptical prism, ≤ 4 mm length through the crystal, end-face centres at opposite azimuths on the equatorial circle half way up the STO inner wall; |B| ≥ 90% of max over the prism. Shot structure: three 150 µs pulses at 500 µs intervals; 2.4 J total per shot (calibrated bolometer). Eq. (S2)→(S3): for a sufficiently powerful pump the crystal is **bleached and optically thin**, 1 − e^(−lα) ≈ lα.
- Wu 2021 PRL main text (archived PDF), searched for pump energetics: Fig. 2(a) single pulse ∼300 µs integrating 250 mJ; Fig. 4 = response to one three-pulse shot, "average of 11 consecutive measurements". **No shot repetition rate appears in print** (searched: repetition/duty/shot/Hz/energy contexts).
- `src/cavity/provenance/constants.py`: `Crystal` (3.0 mm dia × 8.0 mm; nominal-doping caveat; Vaseline half of the contact stack + 2026-07-17 no-paste supersession), `PTerphenylThermalConductivity` (`K_PTP`: floor 0.1, band 0.1–1.0 W m⁻¹K⁻¹, geometric mid 0.3162, anisotropy_factor 2.0 folded into band), `PumpAbsorptionLength` (`L_ABS_PUMP`: scoping grid 5/10/20/50/100/200 µm, grade UNSOURCED-SCOPING, brackets 520–590 nm penetration; Takeda 2002 / Breeze-era named as the likely primaries, deliberately unpulled), `FreeConvectionAir` (2026-07-16 nonlinearity append), `RigSampleGeometry`.
- `thermal/reports/q_margin_planning_point.md` — the report-artifact precedent (status-notes + numbers + regeneration line + byte-pin).
- `docs/plans/plan-checkpoint-spec-zany-pizza.md` — the house plan-checkpoint format and the test-count lineage.

**Delegated to Codex this session (mechanical inventory, task-level read-only; repo verified unmodified after the run):** results now in hand and folded into the sizing below —
- `pytest --collect-only`: **"843 tests collected"** verbatim — the prompt's before-count is verified live, this session.
- `tests/test_thermal_cylinder.py`: 23 collected, 558 lines, **flat functions, no classes** (new tests follow that convention); it and `test_thermal_detuning.py` are the only thermal tests importing `cavity.thermal.cylinder` (names consumed: `CylinderSpec`, `PumpSource`, `SurfaceBC`, `robin_radial_eigenvalues`, `solve`).
- Report precedent mechanics: generators are `python -m cavity.thermal.report_margin|report_turnover [--out thermal/reports]`, writing `build_report()` via `write_text(..., encoding="utf-8", newline="\n")`; the "byte pin" is a UTF-8 `read_text()` equality assertion (`test_a11_report_status_notes_and_byte_pin`, `test_a14_turnover_report_byte_pin` in `tests/test_thermal_detuning.py`). `report_s_ladder.py` mirrors all of this.
- `src/cavity/thermal/__init__.py` is **docstring-only** (no exports, no `__all__`) — new modules need no export wiring.
- `layered.py` (610 lines) API confirmed for the upper-bracket reuse: `Layer(thickness_m, k_w_m_k)` stacks grounded by an isothermal base; `delta_t_disk_center(layers, p_w, a_m, h_top=0)` (uniform-flux disc), `delta_t_gaussian(...)`, and `delta_t_gaussian_volumetric(r_m, layers, p_w, w_m, l_abs_m, h_top=0)` (truncated-renormalised Beer-Lambert in the top layer).
- Name-collision grep: **no hits** for `side_chord`/`side_fire`/`f_side`/`band`-near-PumpSource/`dt_k`-class names in `src/cavity/thermal/` (only the prose word "driven" appears, in unrelated files).
- Line counts: `cylinder.py` 766, `detuning.py` 706, `report_margin.py` 323, `report_turnover.py` 221 — the new-module size estimates below are calibrated against these.

**Assumed (stated, not read):** nothing load-bearing. The 590-nm elliptical-prism intensity profile is taken UNIFORM over the ellipse (the SM prints dims only — planning assumption, flagged in the numbers table). The beam height z_b is taken at crystal mid-height L/2, reading the SM's "half way up the inner cylindrical wall" onto the planning crystal (crystal axial placement itself is Q9-open — rider carried).

---

## Physics design (the four design points, resolved)

### Design point 1 — BC-driven S0/S1: driven-Dirichlet end values, not a new solver

`solve()` today requires `PumpSource` with p_w > 0; S0/S1 have **no volumetric source and imposed temperatures**. The minimal honest path is a **driven-Dirichlet mode of the existing per-mode machinery** — not a superposition decomposition, and not a second eigenbasis.

**Maths.** With no source, ΔT is harmonic: k_r·(1/r)∂_r(r∂_rΔT) + k_z∂²_zΔT = 0. Keep ΔT ≡ T − T_cold (bath = the cold imposed temperature, so cold surfaces are the existing exact Dirichlet ΔT = 0). The hot face carries the imposed constant ΔT_hot = T_top − T_cold. Expand the constant top data in the ACTIVE radial basis (whatever the side BC selects — the machinery cylinder.py already owns):

- expansion of unity: 1 = Σₙ uₙ·J₀(xₙρ) with uₙ = (1/N̂ₙ)∫₀¹ J₀(xₙρ)ρ dρ = J₁(xₙ)/(xₙ·N̂ₙ), and u₀ = 1 for the Bi_s = 0 constant mode.
- per positive mode, the axial problem is the **homogeneous** ODE θ̂ₙ'' − mₙ²θ̂ₙ = 0 with **inhomogeneous end values** θ̂ₙ(0) = ΔT_hot·uₙ, θ̂ₙ(1) = 0 — exactly the existing overflow-free scaled basis Aₙe^(−mₙζ) + Bₙe^(−mₙ(1−ζ)) with the existing 2×2 Cramer end-solve; only the RHS of that 2×2 system changes (imposed values instead of flux conditions). No particular solution, no confluent branch.
- constant mode (Bi_s = 0): θ̂₀'' = 0 with θ̂₀(0) = ΔT_hot, θ̂₀(1) = 0 ⇒ θ̂₀ = ΔT_hot(1 − ζ).

**S0 is exact in this machinery.** With Bi_s = 0, the positive modes are J₁-zeros, so uₙ = J₁(xₙ)/(xₙN̂ₙ) = 0 **exactly** — the constant mode carries the entire solution and the solver reproduces the closed-form 1D linear profile ΔT = ΔT_hot(1 − z/L) with **zero truncation error**. The analytic cross-check is exact, not approximate: axial conductance G_S0 = k_z·πR²/L, checked to machine precision. This is the ladder's anchor rung, and it confirms outcome 5's expectation that S0 is "representable with existing machinery or minimally beyond it".

**S1** (Dirichlet side + base at 0, driven top): basis xₙ = j₀,ₙ, uₙ = 2/(xₙJ₁(xₙ)), θ̂ₙ(ζ) = ΔT_hot·uₙ·sinh(mₙ(1−ζ))/sinh(mₙ) in the scaled basis.

**Known, stated in advance — the sharp-corner divergence.** The S1 idealisation is discontinuous along the top rim (ΔT_hot meets 0 at r = R, z = 0). Consequences the plan commits to documenting, not discovering: (i) pointwise convergence near the rim is Gibbs-slow (same class as the documented flood-under-Dirichlet caveat); interior values and integrated averages converge fine. (ii) The **total top inflow is log-divergent**: per mode, p_top,ₙ ∝ mₙuₙ·J₁(xₙ)/xₙ = 2mₙ/xₙ² ≈ 2Λ/xₙ, and Σ1/xₙ diverges — the classic mixed-boundary edge singularity. A total "conductance" is therefore **not a well-posed observable of sharp S1**; the truncated series grows ∼ log N (a test demonstrates the monotone growth so nobody later mistakes it for slow convergence). S1's deliverables are the convergent field observables: ΔT(r,z)/ΔT_hot at named points, volume average, and the band average — per kelvin of drive.

**Power coupling for the imposed-T scenarios** (feeds design points 3/4): S0 inverts exactly (ΔT_hot = P/G_S0). For S1 the plan proposes a **flux-conjugate companion column, S1b**, computed with machinery that exists TODAY (zero new code): `axial_form='surface'` flood deposition of power P on the top face with Dirichlet side + base — the "certain mW absorbed in the top few hundred microns; where does the heat flow" reading straight from the archived notes. S1 stays defined as ratified (imposed-T); S1b is a clearly-labelled companion supplying the ballpark ΔT-for-stated-P that a pure imposed-T scenario cannot produce. (If ratification prefers S1 imposed-T-only, S1b is one deleted column — nothing else moves.)

**API (proposal).** `SurfaceBC` gains `dt_k: float = 0.0`, valid only with `kind='dirichlet'` (Robin + dt → ValueError; all existing constructions unchanged — default 0.0 is today's behaviour). `solve(spec, source=None, ...)`: `source=None` requires at least one nonzero `dt_k`; source AND drive together → ValueError (superpose two solves at call level — the linearity note lands in the docstring); nonzero `dt_k` on the SIDE → ValueError with a named message (no ladder scenario needs it; extension point recorded). Driven solutions carry `_theta_unit = 1.0` (fields in kelvin; the drive coefficients carry ΔT_hot). `boundary_power_w()` unchanged in formulas; docstring notes that for driven solves "total" is the NET flux (≈ 0 = the conservation diagnostic) and that sharp-S1 top/side entries grow with N per the divergence above. `peak_k`'s top-heated assumption note gains the driven-mode line.

### Design point 2 — f_side(r): chord-averaged Beer-Lambert, fixed quadrature + closed-form thin limit

**Geometry.** Side beam: horizontal, near-collimated (SM), width w_b = 1.2 mm (minor axis, horizontal), height h_b = 2.0 mm (major axis, vertical → the axial band), traversing the crystal disc of radius R along chords. Rays along +x entering the disc r ≤ R at x_entry(y) = −√(R²−y²); in-crystal path to the point (x, y) is s = x + √(R²−y²); Beer-Lambert deposition per unit length ∝ (1/l_abs)e^(−s/l_abs). Intensity uniform across the beam width (planning assumption, stated). The m = 0 (azimuthally smeared) radial profile is the azimuthal average of the fixed-beam deposition field, with x = r cosφ, y = r sinφ:

  f_raw(r) ∝ (1/2π) ∫₀^{2π} 1{|r sinφ| ≤ w_b/2} · exp(−[r cosφ + √(R² − r² sin²φ)]/l_abs) dφ

then **truncated-renormalised** to the module's D4-consistent radial convention: f_side(r) = C·f_raw(r) with 2π∫₀^R f_side(r) r dr = 1 — so the deposited power is **exactly P = absorbed power**, identical in meaning to the end-fire Beer-Lambert convention (`layered.volumetric_depth_pdf` lineage; the transmit-the-remainder alternative rejected for the same consistency reason cylinder.py already records). The incident→absorbed mapping (chord absorbed fraction 1 − e^(−2√(R²−y²)/l_abs)) is a diagnostics line in the report, never a solver input.

**Separability is exact after the smear.** The beam is collimated and z-independent within the band, so the smeared m = 0 source is exactly P·f_side(r)·g_band(z) — the separable structure and the Robin eigenbasis are retained as ratified. (The UNsmeared prism is not separable and not axisymmetric — that content is precisely the deferred m > 0 remainder.)

**Closed form vs quadrature.** No closed form exists for general l_abs (exp of a square root); the module already accepts fixed Gauss–Legendre for smooth radial profiles (the Gaussian precedent), so: fixed G-L in φ (quarter-range by symmetry, split at the indicator kinks sinφ = ±w_b/(2r)), fixed G-L in ρ for normalisation and the modal projections f̂ₙ, node counts following the existing x_max-scaled rule. Two exact anchors pin the quadrature:
- **Optically-thin limit** (l_abs → ∞): deposition uniform along chords, so f_side^∞(r) ∝ azimuthal beam fraction — closed form: 1 for r ≤ w_b/2, (2/π)·arcsin(w_b/(2r)) for r > w_b/2 (renormalised). Asserted against the quadrature.
- **Normalisation exactness** 2π∫f_side r dr = 1 at every grid l_abs.

**l_abs axis (sources + rungs).** {5, 10, 20, 50, 100, 200 µm} = `L_ABS_PUMP.l_abs_scoping_grid_m`, grade **UNSOURCED-SCOPING** (its docstring explicitly brackets 520–590 nm penetration — the S4 pump is 590 nm; none of these numbers may back an absolute ΔT claim) — **plus the optically-thin limit column (l_abs = ∞)**, whose regime backing is the SM's own printed statement that the crystal under the maser pump is bleached and optically thin (Eq. S2→S3). The two ends carry different physics readings, stated in the report: the µm grid = unbleached small-signal penetration scoping; the ∞ column = the Wu operating-regime reading. Bleaching is intensity-dependent (nonlinear) — the ladder stays linear-in-P by construction, so l_abs is a swept PARAMETER, never a computed function of P. Sharp-l_abs numerics sized in advance: l_abs = 5 µm concentrates deposition in a ∼5 µm shell at r ≈ R, needing x_max ∼ πR/l_abs ≈ 900, i.e. n_modes ≈ 300–1024; per-point n_modes is chosen by `tail_estimate_rel ≤ 1e-6` + the `boundary_power_w` deficit diagnostic, and the report records n_modes per cell (no silent cap — house discipline).

**Axial band form.** New `axial_form='band'`: g(z) = 1/(z_hi − z_lo) on [z_lo, z_hi] ⊆ [0, L], zero outside (NOT exponential-from-top — ratified). Per-mode particular solution in closed form via the Green kernel: θ̂_p(ζ) = (f̂ĝ/2mₙ)·∫_a^b e^(−mₙ|ζ−s|) ds — elementary piecewise exponentials with **non-positive exponents only** (overflow-free, in-module discipline; no difference-of-squares denominators, no confluent branch). Constant-mode Ĝ₁/Ĝ₂ piecewise linear/quadratic. `axial_form='uniform'` is the band = [0, L] special case — a machine-precision regression bridge test. Band parameters: `band_lo_m`, `band_hi_m` on `PumpSource` (required iff band; validated ordered and inside [0, L]).

**PumpSource combinations.** `radial_form='side_chord'` requires `beam_width_m` (≤ 2R) and `l_abs_m` (> 0, `math.inf` allowed = the thin-limit closed-form branch), and is allowed ONLY with `axial_form ∈ {'band', 'uniform'}` (chord absorption + axial Beer-Lambert would claim two absorption directions at once — rejected with a named error). All existing form combinations byte-for-byte untouched.

**Module placement.** New small module `src/cavity/thermal/side_deposition.py` owns the profile construction (raw integrand, kink-split quadrature, thin-limit closed form, projection helper); `cylinder.py` consumes it in `_radial_projection` — keeps the solver diff reviewable and the profile testable in isolation.

### Design point 3 — deliverable shape

**One report artifact** on the `thermal/reports/` precedent (`q_margin_planning_point.md` pattern): generator `src/cavity/thermal/report_s_ladder.py`, invoked `python -m cavity.thermal.report_s_ladder [--out thermal/reports]` (the report_margin CLI convention), writing **`thermal/reports/s_ladder_ballpark.md`** via `write_text(..., encoding="utf-8", newline="\n")`, pinned in tests by the house exact-content pin (UTF-8 `read_text()` equality — the `test_a11…byte_pin` precedent), every number regenerated by the generator and re-derived independently in the pins (scoping-numbers-are-computed rule). Structure:

- **Status notes head** (the precedent's pattern): Oxborrow-VERBAL (2026-07-16, late-recorded) rung on the ladder itself; ballpark tier; steady-state reading statement (below); modelled body = homogeneous crystal cylinder, planning dims + cross-build-transfer flag; composite bodies above-tier, recorded; the D8 common-ΔT and H-weighting boundaries untouched (band averages are UNWEIGHTED, stated).
- **S0** — the anchor: closed-form 1D profile and G_S0 = k_z·πR²/L vs the solver (machine-verified in CI, result line printed); ΔT_hot = P/G_S0 across the power grid × k band. Next to it, the imposed-T realisability note.
- **S1** — imposed-T (ratified definition): field ratios per kelvin (centre-top, mid-volume, band average, volume average), the sharp-corner divergence caveat verbatim-class; **cold-bottom realisability rider recorded here** (SPEC outcome 5): the current build's seat is insulating cross-linked polystyrene, no paste — an imposed-cold BOTTOM is a blown-air/forced-contact idealisation, not the as-built seat. **S1b companion column** (existing machinery): top-face flux P, cold side+base — ballpark ΔT(P) directly.
- **S4** — the bracket pair, with the verbatim systematic sentence at the head of the section and beside the numbers:
  - LOWER (m = 0 smear): solve(side_chord × band) with cold top+base (Dirichlet 0 — outcome 5's "cooled top and bottom"), side insulated (h = 0) as headline + side Dirichlet 0 as the maximal-side-cooling bounding column (the two columns bracket the unmodelled crystal→STO side path, D7); peak, volume average, and **band average** (the unweighted stand-in for the gain-region observable, stated) across l_abs axis × k band × power grid.
  - UPPER (spot estimate, 3a-adjacent — **existing `layered.py` functions, zero new solver code**): the illuminated entry patch as an equivalent-area disc a_eq = √((h_b/2)(w_b/2)) = √(1.0 mm × 0.6 mm) = 0.775 mm on a single-`Layer` slab of thickness 2R = 3.0 mm (isothermal-grounded far face — layered.py's native base BC); surface member = `delta_t_disk_center(layers, P, a_eq)`; buried member = `delta_t_gaussian_volumetric(0, layers, P, w=a_eq, l_abs)` over the same l_abs axis (w = a_eq stated as the equal-area equivalence); sanity-anchored by the closed-form half-space uniform-flux disc centre rise ΔT_peak = P/(π·a_eq·k). Assumptions stated at planning rung: planar slab vs curved wall; all P through one patch (single-sided; the azimuthal smear is absent — that is what makes it an upper member); the surface member is the conservative-hot branch; adiabatic elsewhere. Direction statement: smear dilutes (lower), spot concentrates (upper); the true gain-weighted number lies between — a bracket pair, not an error bar.
  - S4 stakes note (verbatim-class, from the scoping): side-fire is the modelled build's pump geometry (PRL SM: 3-mm wall hole, prism across the bore) — validation weight, not ladder-completeness.
  - **m > 0 deferral log**: averaged main result now; bounded side-study + decision gate before heavier machinery (eccentricity-route discipline); recorded here and in the D2 docstring annotation (below).
- **S3 / S5**: S3 label reserved (numbering fork S3-vs-S4 rides Email B — the SPEC outcome's NUMBERING UNCONFIRMED caveat restated); S5 logged-deferred. No numbers.

### Design point 4 — what "ballpark" pins numerically

- **Power axis: P = ABSORBED power, {10 mW, 100 mW, 1 W}** (log grid; the solver is exactly linear in P so every cell rescales exactly — stated). Grid choice is a scoping convention, not a claim.
- **Steady-state reading, STATED not slipped in:** the ladder computes steady-state ΔT for a continuously-absorbed power P. The Wu SM per-shot energetics are literature context lines: 2.4 J/shot over 3 × 150 µs (⇒ ∼5.3 kW instantaneous incident during pulses: 2.4 J / 450 µs); Fig. 2's 250 mJ/∼300 µs single-pulse example. **No shot repetition rate is in print** (searched this session), so no time-averaged CW power is derivable from the published record — any steady P chosen from Wu energetics would smuggle in a duty assumption; the report says exactly this and keeps the power axis a stated grid. Pulse-train transients are OUT of ladder scope twice over: the solver is steady-only by design (no heat capacity), and a per-shot adiabatic rise would need ρ (the one §6T pull still open, SPEC §11 item 7) — recorded, not estimated.
- **Geometry:** R = 1.5 mm, L = 8.0 mm — `provenance.CRYSTAL` (Breeze 2017), PLANNING-ASSUMPTION with the Wu cross-build-transfer flag riding (five published Wu-side indicators lean ~4 mm bore-filling; note the SM's pump path "≤ 4 mm" vs the planning chord 2R = 3 mm — same flag, stated in the report).
- **k axis:** {0.1, 0.3162, 1.0} W m⁻¹K⁻¹ = `K_PTP` band edges + geometric mid; isotropic (D6); the ~2× anisotropy stays folded in the band (K_PTP docstring), not swept.
- **Beam:** h_b = 2.0 mm, w_b = 1.2 mm, A_p ≈ 1.9 mm² — PRL SM p. 1 (proof copy, archive-noted), LITERATURE; uniform-over-ellipse intensity = planning assumption; band centre z_b = L/2 — SM "half way up the inner cylindrical wall", planning reading (crystal axial placement Q9-open, rider).
- **l_abs axis:** the `L_ABS_PUMP` scoping grid (UNSOURCED-SCOPING) ∪ {∞} (bleached optically-thin regime — SM Eq. S2→S3, literature-backed regime statement, no number).
- **Drive axis (S0/S1):** reported per kelvin of ΔT_hot; power-implied drives via G_S0 inversion. Worked scoping arithmetic (computed, re-derived in pins): G_S0 = k·πR²/L; at k = 0.3162: 0.3162 × 7.0686e-6 m² / 8.0e-3 m = 2.794e-4 W/K ⇒ ΔT_hot(10 mW) = 35.8 K — squarely in the meeting's "20–50 K likely buoyancy-enhanced" class (`H_CONV_AIR` append), which the report cross-references as context.

---

## File-by-file diff summary

| # | File | Nature | Est. size |
|---|---|---|---|
| 1 | `src/cavity/thermal/side_deposition.py` | NEW — chord-averaged profile: raw integrand, kink-split φ quadrature, thin-limit closed form, ρ-projection helper | ~150 |
| 2 | `src/cavity/thermal/cylinder.py` | `SurfaceBC.dt_k` + validation; `PumpSource` band/side_chord params + combination validation; `_AxialModes` band particular (Green-kernel piecewise) + driven end-value RHS; `_ConstantMode` band Ĝ₁/Ĝ₂ + driven ends; `_radial_projection` side_chord branch (via side_deposition); `solve(source=None)` driven path; docstring: driven-mode maths + S1 divergence caveat + band/side_chord conventions + **dated D2 annotation** (below) | ~+230 / −10 |
| 3 | `src/cavity/thermal/report_s_ladder.py` | NEW — the ladder generator (status notes, S0 anchor check, S1(+S1b), S4 bracket pair incl. the layered.py spot member, S3/S5 stubs, verbatim systematic sentence, n_modes/tail bookkeeping; `--out` CLI + `write_text` utf-8/`\n` per the report_margin precedent) | ~250 (report_margin is 323) |
| 4 | `thermal/reports/s_ladder_ballpark.md` | NEW — generated artifact | generated |
| 5 | `tests/test_thermal_cylinder.py` | +driven-BC, +band-form, +side_chord solve-level anchors (enumerated below; flat-function convention, current file 23 tests / 558 lines) | ~+330 |
| 6 | `tests/test_thermal_s_ladder.py` | NEW — profile anchors + bracket ordering + report exact-content pin + independent recomputation pins | ~+280 |
| 7 | `SPEC.md` | outcome 5 gains a dated status parenthetical at implementation completion (BUILT: S0 anchor exact, S1 field ratios + divergence record, S4 m=0 + bracket pair; S3 reserved, S5 deferred; artifact path); §7.T1 status parenthetical sentence for the m=0 side-fire extension | ~+14 |

*(No `thermal/__init__.py` change: Codex confirmed it is docstring-only — the package has no export convention to extend.)*

**D2 annotation (required, annotate-never-delete):** `cylinder.py`'s D2 currently records side-pumping as "not axisymmetric … outside this eigenbasis: EXCLUDED, a structural limitation". The S4 extension changes the true boundary: the **m = 0 azimuthal smear of side-fire is now representable inside the eigenbasis** (this changeset); the **m > 0 content remains structurally outside** (deferred with a decision gate). D2 gains a dated annotation saying exactly that (2026-07-16 outcome 5 authority); the original text stays verbatim.

**Untouched by design:** `layered.py` (consumed as-is by the report generator), `volumetric_3a.py`, `identifiability.py`, `broadening.py`, `detuning.py`, `radiation.py`, all report modules, `thermal/reports/` existing artifacts, `calibration/**`, `provenance/constants.py` (every number the ladder needs already exists graded — **no new constants land**), all archived records.

---

## Test delta

**Before: 843 collected — VERIFIED live this session** (Codex delegation, `pytest --collect-only -q -p no:cacheprovider`: "843 tests collected", verbatim). **After: 872. Delta: +29** (29 new test functions; 0 existing tests edited, deleted, or renamed). `tests/test_thermal_cylinder.py` goes 23 → 42; `tests/test_thermal_s_ladder.py` is new at 10.

`tests/test_thermal_cylinder.py` (+19):

Driven-BC (9): `test_driven_requires_drive_or_source`, `test_driven_rejects_source_and_drive_together`, `test_driven_rejects_robin_dt`, `test_driven_rejects_side_drive`, `test_s0_exact_linear_profile_machine_precision`, `test_s0_conductance_matches_k_pi_r2_over_l`, `test_s0_positive_modes_carry_exactly_zero`, `test_s1_interior_matches_independent_series` (brute-force sinh/J₀ series recomputed in-test), `test_s1_top_inflow_grows_with_n_modes_log_divergence_documented`.

Band axial form (5): `test_band_equals_uniform_on_full_height`, `test_band_deposits_exactly_p` (boundary-power total), `test_band_particular_matches_independent_quadrature`, `test_band_validation_bounds`, `test_band_segment_integral_closed_form`.

side_chord at solve level (5): `test_side_chord_solve_energy_diagnostic`, `test_side_chord_requires_beam_width_and_l_abs`, `test_side_chord_forbidden_with_beer_lambert_axial`, `test_side_chord_beam_width_within_diameter`, `test_side_chord_sharp_labs_converges_at_sized_n_modes` (the 5 µm cell at the sized n_modes, tail + deficit gates).

`tests/test_thermal_s_ladder.py` (NEW, +10):

Profile (4): `test_f_side_normalisation_exact_across_grid`, `test_f_side_thin_limit_matches_arcsin_closed_form`, `test_f_side_projection_matches_independent_quadrature`, `test_f_side_centroid_moves_outward_as_l_abs_shrinks`.

Bracket + report (6): `test_s4_upper_bracket_exceeds_m0_lower_across_grid`, `test_spot_estimate_anchored_to_half_space_closed_form`, `test_report_regenerates_byte_identical`, `test_report_numbers_match_independent_recomputation` (grid spot-checks re-derived from first principles in-test), `test_report_carries_verbatim_s4_systematic_sentence`, `test_report_reserves_s3_and_defers_s5_and_states_steady_reading`.

Existing tests: **0 edited, 0 deleted, 0 renamed** — every existing form/BC combination is untouched by construction (new fields defaulted; new forms opt-in).

---

## Ordered implementation sequence (with STOP points)

0. **Pre-flight:** working branch; `pytest --collect-only -q` — **STOP T0** if ≠ 843 (re-base the count, re-ratify the delta). Re-grep `side_chord|band_lo_m|dt_k|side_deposition` (must be absent — Codex collision grep already ran at plan time; re-verify at implementation time).
1. **`side_deposition.py` + profile tests** (test_thermal_s_ladder.py profile block). Pure functions, no solver contact. **STOP S1** if the thin-limit closed form and quadrature disagree beyond tolerance (quadrature design error — fix before anything consumes it).
2. **Band axial form** in cylinder.py + its 5 tests. **STOP S2** if any previously-green cylinder test changes outcome (regression in the untouched forms).
3. **Driven-BC mode** + its 9 tests. **STOP S3** if the S0 exact cross-check disagrees with the solver beyond machine tolerance — that is a solver defect finding, to be reported, never tuned around.
4. **side_chord solve-level wiring** + its 5 tests (n_modes sizing exercised here).
5. **`report_s_ladder.py` + artifact + report tests.** **STOP S4** if the byte-pin's independent recomputation disagrees with the generator (generator bug or convention slip — resolve before pinning).
6. **SPEC + D2 annotations** (docs pass — after numbers exist, so the status parenthetical states what ran).
7. **Full suite:** `pytest --collect-only -q` must report **872** — **STOP S5** on any other number; full run green. Commits: (i) `thermal: side-deposition profile + band axial form`, (ii) `thermal: driven-Dirichlet BC mode - S0 exact anchor, S1`, (iii) `thermal+reports+SPEC: S-ladder ballpark report, S4 bracket pair, D2 m=0 annotation`. No AI attribution trailers (house rule).

---

## Out of scope (restated)

Any COMSOL solve (zero-licence block); κ_s(ΔT) feedback; composite crystal+STO+spacer bodies (above ballpark tier — recorded, not modelled; the no-paste/insulating-seat rider enters ONLY as the S1 cold-bottom realisability note); m > 0 azimuthal harmonics (deferred, decision-gate discipline); S3 (label reserved, Email B); S5 (logged-deferred); pulse-train/transient thermal response (steady solver; ρ unsourced — §11 item 7); any bleaching/intensity-dependent absorption model (l_abs is a parameter axis); beam-optics modelling beyond the SM's printed dims; crystal→STO Vaseline contact conductance (D7 hook untouched); opportunistic refactors.
