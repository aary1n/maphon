# SPEC — STO TE01δ Maser Cavity: Forward Model + Yield/Tolerance Pipeline

**Status:** authoritative source of truth for this repo. Derive CLAUDE.md / READMEs / module docs from this; do not contradict it. Where this spec and a paper's face value disagree, **this spec wins** (the disagreements are deliberate — see §6).

**Register:** physics terminology only — *surrogate*, *parameter-free forward model*, *Bayesian re-inference*. Do **not** use "machine learning" in code comments, docs, or commit messages. (Supervisor convention.)

---

## 0. Purpose & scope

Build a validated COMSOL forward model of the strontium-titanate (STO) TE01δ dielectric-ring maser resonator (**Phase 1**), then a surrogate-accelerated Monte Carlo tolerance/yield layer on top (**Phase 2**, the owned deliverable). 8-week UROP; **results are the priority, manuscript is post-placement.** Phase 1 reproduces published numbers; Phase 2 produces the thing the literature lineage left undone — error bars on the maser's figures of merit under fabrication and material-parameter scatter.

---

## 1. Architecture / stack

- **COMSOL Multiphysics, RF module**, driven via **LiveLink for Java / MPh (Python wrapper over COMSOL's Java API)** — validated available. Python owns sweeps, surrogate, Monte Carlo, analysis; COMSOL owns the FEM eigensolve only.
- **Transplant the SiPhON Monte Carlo yield infrastructure** (Latin-hypercube/Sobol sampling, surrogate fit, yield aggregation, sensitivity indices). Port, do not rewrite.
- COMSOL is **not** assumed available in CI. Solves run locally / on cluster. CI tests the Python layer (extraction maths, surrogate, MC, analytic benchmark) against cached/synthetic field data.
- **Reproducibility:** pin RNG seeds; log COMSOL version, mesh settings, and element count with every solve; persist raw complex eigen-solutions (not just scalars) so extraction can be re-run without re-solving.

---

## 2. Physics model (Phase 1)

- **2D axisymmetric (r, z), azimuthal index m = 0.** `Electromagnetic Waves, Frequency Domain` interface, **Eigenfrequency** study, search near 1.45 GHz.
- **Domains:** rectangular copper box in the r–z half-plane → **Impedance Boundary Condition** on walls (and a **PEC variant**, see §4). Air fill (εr = μr = 1, σ = 0). One dielectric region (STO).
- **STO material:** real permittivity εr′ = **316.3**; loss entered as **complex permittivity** εr = εr′(1 − i·tanδ), with **tanδ = 1.1×10⁻⁴** at 1.45 GHz. μr = 1, σ = 0. (Provenance: §6.)
- **Copper:** σ = **6.0×10⁷ S/m**, μr = 1, via Impedance BC (surface resistance R_s = √(ωμ₀ / 2σ)).
- **`dielectric_shape` ∈ {puck, torus} — switchable geometry parameter.** Booth's appendix under-specifies the cross-section (gap #1, §11): her prose says "toroidal" / "circular area" / "ring" but tabulates only one radius. Implement both and let §4 decide which reproduces the targets.
- **Nominal geometry** (Booth App. A, STO TE01δ): box width **12.28 mm** (→ box radius 6.14 mm), box height **18.42 mm**, dielectric radius **2.46 mm**. The **dielectric height (puck) / minor radius (torus) is UNPINNED** — expose as a parameter, sweep it, and/or await Booth's `.mph`.
- **Mesh:** extremely fine, **fully curved dielectric boundary** (edge-element FEA mishandles sharp corners — Booth flags this explicitly). Run a convergence study: refine until f and Q are stable to the target significant figures; record the converged element count.
- **Mode identification:** identify TE01δ by **field pattern**, not eigenvalue order — azimuthal E (toroidal), axial H antinode on the symmetry axis, H circulating in r–z. Implement an automatic field-symmetry check; reject and re-pick if the symmetry test fails.

---

## 3. Extraction — the careful core (axisymmetric Jacobian made explicit)

Every volume integral in 2D axisymmetric form carries the **2πr Jacobian**: ∭ g dV = 2π ∬ g · r dr dz. Get this right or every mode volume is wrong by an r-weighting.

- **f** = Re(eigenfrequency).
- **Q** — COMSOL returns a complex eigenfrequency f = f′ + i·f″ and exposes a built-in `emw.Qfactor`. Booth's definition is Q = ω/(2|δ|) with eigenvalue λ = δ − iω, i.e. **Q = f′ / (2 f″)** with sign care. **Do not trust the convention blind:** assert it against §8 (in the PEC + lossy-dielectric limit Q must equal 1/(p_e·tanδ)).
- **V_mode** (magnetic mode volume) = [∭ |H|² dV] / |H|²_max = 2π∬ |H|²·r dr dz / max(|H|²). **Report two variants**: |H|²_max taken (a) globally over the cavity, (b) locally over the dielectric/gain region. The literature's 0.2–0.41 cm³ spread is partly this definitional choice — quantify it rather than inherit one convention silently.
- **p_e** (electric energy filling factor) = [∭_dielectric ε|E|² dV] / [∭_all ε|E|² dV]. Directly COMSOL-extractable. **Required to interpret Q** (§4, §6).
- **F_m** (magnetic Purcell factor) — **use the standard Purcell form, not Breeze's printed prefactor** (which is dimensionally inconsistent — provenance trap). The form that reproduces Breeze Table 1 is:

  **F_m = (3 / 4π²) · λ³ · (Q / V_mode)**, with λ = c/f the free-space wavelength.

  Validation of the formula itself (do this once, in the analytic/benchmark tests): Breeze STO row Q = 10⁴, V_mode = 0.2 cm³, f = 1.45 GHz → λ = 20.69 cm, λ³ = 8.86×10³ cm³ → F_m = 0.0760 × 8.86×10³ × (10⁴/0.2) = **3.4×10⁷** vs Breeze's tabulated 3.6×10⁷. Match. If your implementation can't reproduce ~3.6×10⁷ from Breeze's Q and V, the formula or units are wrong — stop and fix before trusting any F_m.

---

## 4. Wall-loss decomposition (closes the geometry gap empirically)

Run the nominal geometry **twice**:
- (a) Impedance-BC walls → **Q_total**.
- (b) PEC walls (σ → ∞) → **Q_diel** (radiation = 0 in a closed cavity, so PEC isolates dielectric loss).

Then **1/Q_wall = 1/Q_total − 1/Q_diel**.

**Acceptance:** for Booth's geometry at tanδ = 1.1×10⁻⁴, expect **Q_diel ≈ 9,000–10,000** and a **wall-loss fraction ~23–27%**, giving **Q_total ≈ 6,980** (Booth Table 8). If the assumed cross-section reproduces this, **gap #1 is closed from the physics side** — the geometry is right. If not, vary dielectric height/shape until it does. This is also the proof that the model's confinement physics is correct *before* Phase 2 leans on it.

Why this works (and why the 30% Breeze/Booth Q gap is **not** a loss-tangent difference): Breeze's modelled Q = 10,000 sits at the dielectric ceiling for the same tanδ (walls negligible, V_mode = 0.2). Booth's 6,980 = identical dielectric loss **plus** ~25% wall loss, because her looser-confined mode (V_mode = 0.409, magnetic field spilling out of the dielectric toward the copper) loads the walls. One mechanism — magnetic confinement — sets both V_mode and Q. (Full derivation in §6.)

---

## 5. Validation gate (Phase 1 complete = all pass)

| Check | Target | Source |
|---|---|---|
| Analytic benchmark passes | empty-cavity TE011 < 0.1% error | §8, build FIRST |
| f | 1.45 GHz, ≥4 s.f. (Booth localises to 5 s.f.) | Booth, Breeze |
| Booth two-point | Q ≈ **6,980**, V_mode ≈ **0.409 cm³** at Booth geometry (walls on) | Booth Table 8 + App. A |
| Confinement trend | tightening toward V_mode ≈ 0.2 raises Q toward **~10,000** | Breeze Table 1 |
| Wall-loss split | Q_diel ≈ 9–10k, wall fraction ~23–27% | §4 |
| F_m | order 10⁷ via §3 formula | Breeze (STO F_m = 3.6×10⁷) |

**The gap must reproduce as a continuous confinement trend, not two unrelated points.** That trend *is* the validation that the wall-loss physics is right.

### 5b. Phase 1b — bore + crystal (required for §7, not for the gate)

Add the central **bore** (the real device is a hollow ring) and the **pentacene:p-terphenyl crystal** sub-domain (3 mm diameter × 8 mm, 0.053% doping; Breeze 2017). Crystal εr < 5, μr ≈ 1 — Booth argues it barely perturbs the mode; **verify** rather than assume. Purpose: extract the field the spins actually see (gain-region H) for the coupling handshake (§7). Booth skipped this; it is required for any cooperativity output.

---

## 6. Parameter provenance (authoritative — use these, not paper face values)

Live source-of-truth is `pentacene_maser_parameter_provenance.md` (graded). Summary of the load-bearing findings:

- **εr:** standardise on **316.3–318** (Breeze 318 / Booth 316.3 / Wu 312). The 0.5% Breeze/Booth difference is Q-irrelevant. The full 1.9% spread shifts f by **~14 MHz** at 1.45 GHz (f ∝ εr^(−1/2) ⇒ Δf/f ≈ −½·Δεr/εr) — that's 35–85 cavity linewidths, i.e. a **tuning-range** matter, **not** a yield pass/fail (see §7).
- **tanδ:** nominal **1.1×10⁻⁴** at 1.45 GHz. Provenance: Booth takes a 22-GHz literature value (1.6×10⁻³) and scales ∝ f (Debye, ω_τ,ionic ≫ ω_cavity). This sits at the **optimistic end**. Measured-device effective loss spans **1.0–2.3×10⁻⁴**: de-loading measured Q with k = 0.2 gives Breeze Q₀ ≈ 10,700 (tanδ ≤ 0.94×10⁻⁴) vs Wu Q₀ ≈ 4,320 (tanδ ≤ 2.3×10⁻⁴) — a ~2.5× spread across nominally identical flame-fusion STO.
- **Modelled Q = tanδ × confinement** (the key correction to naive reading): Breeze 10,000 ≈ dielectric ceiling (walls negligible, V = 0.2); Booth 6,980 = same tanδ + ~25% wall loss (V = 0.409). **The 30% gap is confinement, not loss tangent.** Both used ~1.1×10⁻⁴. (Arithmetic: ceiling 1/(1.1×10⁻⁴) = 9,090; 1/6,980 − 1/9,090 = 0.333×10⁻⁴ → Q_wall ≈ 30,000 ≈ 23% of loss.)
- **Cu:** σ = 6.0×10⁷ S/m.
- **Crystal:** pentacene:p-terphenyl, 3 mm × 8 mm, 0.053%; εr < 5 (Breeze 2017).
- **De-loading convention:** k = 0.2 (Breeze 2017), Q₀ = Q_L(1 + k). Wu's coupling is unstated — flagged (§11).

---

## 7. Phase 2 — yield/tolerance (the deliverable)

**Pipeline:** validated nominal model → parametric COMSOL sweep over DOFs → fit **surrogate** (polynomial / GP) per output (f, Q, V_mode, F_m) → LHS/Sobol sample the surrogate (10⁴–10⁵ draws) → aggregate yield. SiPhON infrastructure transplant; COMSOL is called only to build the sweep that trains the surrogate, not per Monte Carlo draw.

**DOFs + input distributions (grounded in §6):**
- εr ∈ [312, 318] → drives f (→ tuning-range output).
- tanδ ∈ [1.0, 2.3]×10⁻⁴ → drives Q, C (→ hard yield).
- Geometry: dielectric radius, height, box dimensions, **bore radius + eccentricity** (a polished hollow cylinder — bore-centring and wall-thickness tolerance are physically real and untunable), lid/tuning-plate position. Machining tolerances parameterised (start ±25 µm nominal; refine with supervisor).

**Outputs / yield metrics — report BOTH; the second is the novel one:**
1. **f-detuning vs available tuning range.** f is *tunable* (servo plate, Breeze), so the question is tuning-range adequacy: what fraction of as-built devices need more than |tuner range| to reach the 1.4493 GHz spin line. Required range ≳ ±15 MHz to absorb εr + geometry scatter.
2. **Untunable figure-of-merit yield.** Scatter in **Q, F_m, cooperativity C**; fraction with **C > 1** (above maser threshold). These cannot be tuned post-build. **This is the owned result** — the literature has no error bars on the maser's figures of merit.

**Sensitivity ranking** (Sobol indices) → **tolerance budget** (how tight radius / εr / tanδ must be for X% yield). Expectation: εr + dimensions dominate f; tanδ + confinement dominate C. Deliverable explains the literature's own 2× / 30% spread as tolerance- and provenance-driven.

**Framing note (state precisely, don't overclaim):** Booth named "a Monte Carlo simulation or gradient descent" as future work, but for **dielectric-ring shape optimisation** (searching geometry space for the best shape), and did **not** execute it. The **tolerance/yield** interpretation is the novel contribution. Do not assert Booth specified yield analysis.

---

## 8. Analytic benchmark (traceability anchor — build and pass FIRST)

Validate the solver against closed-form modes **before** trusting it on the STO ring. This is the Oxborrow-2007 "traceable FEM" principle and the answer to "how do you know your COMSOL result is right."

- **Empty (air-filled) right-circular copper cylinder**, radius a, length L. Closed-form eigenfrequencies:
  - TM_mnp: f = (c/2π)·√[(x_mn/a)² + (pπ/L)²], x_mn = nth zero of J_m.
  - TE_mnp: f = (c/2π)·√[(x′_mn/a)² + (pπ/L)²], x′_mn = nth zero of J_m′.
  - **TE011** uses x′_01 = 3.8317.
  Claude Code tabulates these and compares to an empty-cavity COMSOL solve at the same a, L. **Target: < 0.1% agreement** (mesh-limited). This is a pure-Python computation (Bessel zeros from scipy) — fully testable in CI without COMSOL.
- **Q-from-tanδ closed checks:** homogeneously dielectric-filled cavity → Q_diel = 1/tanδ; with filling factor → Q = 1/(p_e·tanδ). Assert COMSOL recovers these in the appropriate limits — this is what pins the Q convention (§3).
- Method/traceability citation: **Oxborrow 2007, IEEE Trans. Microw. Theory Tech. 55, 1209** ("Traceable 2-D finite-element simulation of the whispering-gallery modes of axisymmetric electromagnetic resonators"). Not a repo file — add the PDF if obtained (supervisor linked the IEEE stamp URL).

---

## 9. Non-goals / out of scope

- No 3D. Axisymmetric m = 0 suffices for the eigenmode; the coupling loop/port is out of scope.
- **No metallic / loop-gap resonators** — that is Zangwill's active project; do not overlap.
- **No Maxwell–Bloch time evolution** — that is Niall/Nina's project (arXiv 2412.21166). This repo **feeds** it via §7; it does not reimplement it.
- No spin dynamics / PyCCE.
- No assumption of a COMSOL license in CI.

---

## 10. Suggested module shape (agent finalises — not prescriptive)

Logical components, layout at your discretion: `forward_model` (build + solve, returns complex eigenvalue + field handles) · `extraction` (the §3 integrals, Jacobian-correct) · `validation` (the §5 gate + §8 analytic benchmark) · `sweep` (parametric driver over §7 DOFs) · `surrogate` (fit / predict) · `mc_yield` (sample + aggregate + Sobol; SiPhON port) · `provenance` (the §6 constants as one typed, single-source config object). Keep the §6 numbers in exactly one place; everything imports them.

---

## 11. Open gaps to resolve (flagged, do not paper over)

1. **Booth's dielectric cross-section is under-specified** (height / puck-vs-torus). → Obtain **Booth's `.mph` from the supervisor** and drop it in `refs/`; until then, the `dielectric_shape` switch + height sweep, with §4 as the empirical closure test.
2. **22-GHz STO tanδ primary source** (Booth refs 16 / 20–24; likely Geyer et al., JAP 97, 104111 (2005)) — pull for the writeup; the ∝f scaling is approximate for an incipient ferroelectric.
3. **Wu coupling coefficient unstated** → de-loading assumes k ≈ 0.2.
4. **COMSOL complex-eigenfrequency sign/convention for Q** → must be asserted via §8 before any Q is trusted.
