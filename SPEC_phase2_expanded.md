# SPEC §7 (expanded) — Thermal-Robustness / Budget Pipeline

**Replaces §7.** Self-contained: this specifies the *statistics*, not "port SiPhON." Where this and the top-level §7 disagree, this wins.

**Retargeted (2026-07-01 thermal pivot):** the previous version of this doc specified a *static fabrication-yield* pipeline — P(tune to spin line ∧ C > 1) across the build population. That output is superseded: at C ~ 190 the C > 1 question is trivially yes, so it is not the deliverable. **The deliverable is now the distribution of thermal operating margin** — per as-built cavity, how much pump-induced heating (ΔT, equivalently cavity detuning Δf) it absorbs before C falls through threshold — with error bars. The statistical *machinery* below (surrogate, CV gate, error budget, Sobol, tolerance curves, control-vs-noise taxonomy, operating-point evaluation) **transfers essentially intact**; what changes is the quantity aggregated at the end, one new analytic composition step (§7.3b), and one new error channel (§7.6). Cross-refs: the analytical thermal submodel is SPEC.md §7T; thermal provenance is SPEC.md §6T; the Q-vs-margin hypothesis is SPEC.md §7.T4.

---

## 7.0 What this is

Phase 2 is **forward uncertainty quantification (UQ) of the maser's thermal operating margin.** Inputs: fabrication + material scatter (and the thermal-model coefficients). Outputs, in a three-layer composition:

- **Layer A (intermediate).** Distributions of the EM figures of merit at the **tuned operating point** — chiefly the static cooperativity **C₀** and the **loaded cavity linewidth κc** — across the as-built population. (f, Q, V_mode, F_m also fall out.)
- **Layer B (new, analytic).** The map from pump illumination to differential cavity–spin detuning, ΔT → Δf, from the closed-form thermal submodel (SPEC.md §7T).
- **Layer C (owned result).** The **thermal-budget distributions** p(Δf_max), p(ΔT_max), p(P_max) — each with quantified error. Optionally a thermal yield if an operational heating level is defined (§7.3).

The literature reports point values of the FOMs and, at most, a single lumped operating ΔT (Wu). This reports the *distribution* of thermal margin over the realistic build population, at the operating point, with error bars — and the tolerance/design levers that set it. That is the missing quantity.

Register: standard UQ terminology (*surrogate / Gaussian process / polynomial chaos / Sobol*) — the field's own terms. (The old "no ML in comments" line is retired at the top of SPEC.md.)

---

## 7.1 SiPhON — plumbing, not science

SiPhON contributes a **sampling-and-aggregation skeleton only.**

**Transfers (port):** vectorised low-discrepancy sampler (LHS/Sobol → batch-evaluate → aggregate); proportion/distribution aggregation; histogram + margin-vs-tolerance plotting; the tolerance-sweep reporting pattern; the physics→numerics→result narrative spine.

**Does NOT transfer — build new (the Phase 2 content):**
- a multi-dimensional **validated** surrogate with predictive uncertainty (SiPhON: 2-D interpolation, no validation, no uncertainty);
- the **conditional / operating-point-correct** evaluation structure (§7.3) — SiPhON had a single flat threshold;
- the **analytic thermal composition** on top of the surrogate (§7.3b) — new;
- **emulator-uncertainty propagation** into the reported intervals (§7.6);
- global **variance-based sensitivity / Sobol** (§7.7);
- **axisymmetry-breaking inputs** (crystal centring eccentricity, §7.4);
- **material-parameter inference** from the literature Q spread (§7.4, optional).

→ SiPhON is the I/O + aggregation layer. Everything below is what makes Phase 2 a *result*.

---

## 7.2 Variable taxonomy — control vs noise vs model coefficient

| Class | Variables | Treatment |
|---|---|---|
| **Noise** (sampled per device, θ) | box radius; STO ring outer radius; STO ring inner radius; STO ring height; crystal axial offset; **crystal centring eccentricity**; εr; tanδ *(re-worded 2026-07-18, geometry re-base: was "dielectric radius; dielectric height / minor radius; box width; box height; …" — the Booth-torus parameterisation; box HEIGHT left the noise set because the quantity IS the control p_tune (the piston position sets the internal height), and the ring height row is the Q13 print fork until resolved)* | as-built scatter, untunable → sampled from input distributions (§7.4) |
| **Control** (solved per device, *not* sampled) | tuning-plate position `p_tune` ∈ [p_min, p_max] | set post-build to pull f onto the spin line; read the FOMs there |
| **Model coefficient** (deterministic; scatter only if stretch) | thermal: df/dT (cavity, spin), p-terphenyl k/ρ/c_p, pump intensity (SPEC.md §6T) | fixed nominal in the baseline; enter Layer B, **not** the sampled noise. Their *uncertainty* is a separate error channel (§7.6), and their *scatter* across builds is stretch-scope (§7.9) |

**Consequence (unchanged):** do **not** sample the plate — for each device, *solve* for the plate position that hits f_spin, then read the FOMs (and the thermal budget) there. This is what makes metric-1 (tuning-range adequacy) well-posed and what makes the budget evaluated on-resonance rather than for a detuned device.

---

## 7.3 Output structure — conditional, at the tuned operating point (retargeted)

The FOMs — and therefore the thermal budget derived from them — must be evaluated at the **operating point** (f tuned to the spin line), not at nominal plate position. Moving the plate changes the boundary → V_mode, wall loading, gain-region H → **C₀ and κc**. Reading the budget at the nominal plate for an off-nominal device reports margin for a device that isn't on resonance. Wrong.

Therefore the surrogate is over **(θ, p_tune) jointly** — for f at minimum, ideally for C₀ and κc.

**Per-draw algorithm.** For each θ ~ p(θ):
1. `f̂(θ, p)` over p ∈ [p_min, p_max] (surrogate).
2. **Tuning-feasible** ⇔ ∃ p with f̂(θ,p) = f_spin (= 1.4493 GHz). Record required tuning range; if it exceeds [p_min, p_max] → **fails metric-1**.
3. If feasible: p* = root. Evaluate `Ĉ₀(θ, p*)` and `κ̂c(θ, p*)` (and Q̂, V̂_mode, F̂_m at p*).
4. **Thermal budget** (§7.3b): Δf_max = ((κ̂c + κs)/2)·√(Ĉ₀ − 1) (two-linewidth law — SPEC §7.T4 re-derivation 2026-07-13; κs per draw = the graded static planning branch `provenance.KAPPA_S`) → ΔT_max via Layer B → P_max.

**Aggregate:**
- **Tuning yield** `Y_tune = P(feasible)` — metric-1, unchanged, still a real gate on the build.
- **Thermal-budget distributions (owned)** — p(Δf_max), p(ΔT_max), p(P_max) *at the operating point, conditioned on feasibility.* These are the primary output.
- **FOM marginals** p(C₀), p(κc), p(Q), p(V_mode), p(F_m) at the operating point — supporting.
- *Note:* `Y_C = P(C₀ > 1 | feasible)` is retained only as a sanity check and is ≈ 1 (trivial at C ~ 190). It is **not** the deliverable.
- **Optional thermal yield** `Y_thermal = P(ΔT_max > ΔT_op | feasible)` — the fraction whose margin exceeds the *expected operating heating* ΔT_op. Meaningful **iff** ΔT_op is grounded in the real pump model (SPEC.md §6T / §11) — do not invent it. If ΔT_op is available this parallels the old yield but is now thermally substantive.

**Convention guard (single-source from provenance):** κc / C use the **loaded** cavity linewidth; F_m uses **unloaded** Q. Never mix. Δf_max carries κc (loaded) — apply the loaded/unloaded split consistently per draw. Δf_max additionally carries κs (cyclic-Hz FWHM, `provenance.KAPPA_S`; the 2π trap is guarded in anchor A6) under the 2026-07-13 two-linewidth law.

**Simplification permitted *iff measured*:** if ∂C₀/∂p_tune and ∂κc/∂p_tune over the tuning range are small (measure in Phase 1b, SPEC.md §5b), decouple — evaluate C₀/κc at nominal and treat tuning as a pure frequency question, composing the budget once per θ. Do **not** assume; measure the plate-sensitivity first and state it.

---

## 7.3b Thermal budget — analytic composition on top of the surrogate (NEW)

The thermal layer sits **on top of** the EM surrogate; it is not itself surrogated.

- **What is surrogated:** the EM outputs C₀(θ, p) and κc(θ, p) (and f, V_mode) — the expensive COMSOL quantities.
- **What is closed-form:** the thermal submodel (SPEC.md §7T) is already cheap analytic; do **not** spend COMSOL solves or a surrogate on it. It supplies the ΔT → Δf coefficient (via df/dT, SPEC.md §6T), weighted by the gain-region H the spins see.
- **Composition, per draw:**
  1. Δf_max = ((κ̂c + κs)/2)·√(Ĉ₀ − 1) — max cavity–spin detuning before the pulled-oscillator threshold C₀ = 1 + 4Δ²/(κc+κs)² is crossed (SPEC §7.T4 re-derivation 2026-07-13; the old cavity-only Lorentzian roll-off C(Δ) = C₀/(1 + (2Δ/κc)²) is the κs → 0 limit; κs per draw = `provenance.KAPPA_S`, static planning branch).
  2. ΔT_max = Δf_max / |df_cavity/dT − df_spin/dT| — the *differential* detuning is what breaks resonance (cavity moves faster than spins).
  3. P_max = ΔT_max / (dΔT/dP_pump) — pump-power budget, from Layer B's ΔT(P_pump).

**Linewidth caveat — RESOLVED 2026-07-13 (SPEC.md §7.T4 re-derivation; the old caveat's scaling claim was FALSE).** The two-linewidth law **Δf_max = ((κc + κs)/2)·√(C₀ − 1)** is the settled general form (step 1 above already carries it); the old cavity-only (κc/2)·√(C₀−1) is its κs → 0 limit. The superseded caveat claimed the combined linewidth "changes the constant, not the 1/√Q scaling" — wrong: κs is Q-independent, so the combined width saturates at κs at high Q and the Q-margin exponent inverts (−1/2 for κc ≫ κs → +1/2 for κc ≪ κs). It changes both the margin magnitude (the ×6.4 re-base at the operating point) and, crucially, its Q-dependence — it is not merely a prefactor correction. Derivation artifacts: `docs/derivations/maser_Q_detuning_margin_derivation_corrected.pdf` (the 2026-07-10 corrected derivation — supporting), with the SPEC.md §7.T4 re-derivation block (2026-07-13) as the implementation of record (governs on any numerical divergence); turnover map: `thermal/reports/q_margin_turnover.md`.

Everything downstream (error budget, Sobol, tolerance curves) operates on Δf_max / ΔT_max / P_max, computed this way per draw.

---

## 7.4 Input uncertainty models (grounded; not placeholders)

**Geometry / machining (noise).**
- *Shape:* per dimension, truncated Gaussian centred at nominal with ±3σ = tolerance band (process-centred), **or** uniform over the band (worst-case spec compliance). Report under both; the gap is informative. Default: Gaussian.
- *Magnitudes:* ±25 µm is a **placeholder** — replace with real workshop-achievable tolerances (Oxborrow / Imperial workshop). **ACTION.** Distinguish: uniform machining tolerance (turned diameters/heights) vs **crystal centring eccentricity** (separate, below) vs surface finish (feeds R_s → κc, secondary but now relevant since κc sets the budget).

**Crystal centring eccentricity (noise — and it breaks the model).** *(2026-07-16 reframe: the recovered Booth geometry contains a torus central opening — often termed the bore — but no separately constructed or independently parameterised bore; the eccentric element is the crystal within it.)*
- An off-centred crystal is a lateral displacement of the crystal sub-domain → **breaks the m=0 axisymmetry.** It **cannot be sampled in the 2-D axisymmetric solver directly.**
- Handling (pick + state): **(a)** first-order perturbation from the axisymmetric fields; **(b)** a *bounded* 3-D side-study — a handful of full-3-D solves, fit a local response, fold in as a correction; **(c)** if (a)/(b) show it negligible over the achievable centring tolerance, drop with justification. Do **not** silently carry it as if the axisymmetric model captures it. **ACTION / OPEN.**

**Material — εr, tanδ (noise).**
- *Baseline:* independent distributions over the §6 ranges — εr over [312, 318]; tanδ over [1.0, 2.3]×10⁻⁴. Shape: uniform (conservative) or triangular toward nominal. State choice; test sensitivity.
- *Correlation:* εr and tanδ may co-vary (same crystal quality). Default independent; flag that positive correlation tightens the joint tail. Note tanδ drives κc → the budget's √(C₀−1) *and* κc prefactor, so its scatter enters the margin twice.
- **Elevated — Bayesian re-inference** (the "Bayesian re-inference" hook): the measured Q across devices (Breeze ≈ 10.7k, Wu ≈ 4.3k, Qian ≈ 7.3k, Booth 6.98k) are samples of the *real* tanδ distribution, de-embedded through the model. Because Phase 1 gives Q(tanδ, geometry, wall split): **de-load** measured Q_L → Q₀ (k = 0.2 where known; Wu unstated — §11) → **de-embed** each cavity's own confinement → infer the posterior over tanδ. Use it as the input distribution instead of a flat range. Data-grounded, and **doubles as the mechanism explaining the literature's 2× Q spread.** Scope: **recommended-if-time.**

**Thermal coefficients (model inputs, not sampled noise — baseline).**
- df/dT (cavity, spin), p-terphenyl thermal properties, pump intensity enter Layer B at fixed nominal (SPEC.md §6T). Their *uncertainty* propagates as a distinct error channel (§7.6) — likely a dominant one. Their *scatter across builds* (e.g. doping-dependent absorption) is **stretch** (§7.9), not baseline.

---

## 7.5 Surrogate layer (validated; uncertainty-bearing)

**Design of experiments.**
- ~7–8 noise dims + 1 control dim ⇒ tensor grids infeasible. Use Sobol / LHS over (θ, p_tune).
- *Sizing:* start O(10·d), grow via active learning. **Hard COMSOL solve budget (binding): O(150–300) solves total.** Every solve logged per SPEC.md §1 (version, mesh, element count, raw complex eigenvalues). *The thermal submodel adds zero solves — it is closed-form (§7.3b).*

**Surrogate choice.**
- *Primary:* **polynomial chaos expansion (PCE).** Sobol indices fall out of the coefficients analytically (§7.7); cheap for 10⁴–10⁵ MC draws.
- *Secondary / cross-check + active learning:* **Gaussian process (GP).** Predictive variance drives active learning and emulator-uncertainty propagation (§7.6). Use where PCE struggles (sharp features near mode crossings / near f = f_spin and near the low-margin boundary).
- One surrogate per EM output (f, C₀, κc, V_mode; Q/F_m derived).

**Validation gate (do not trust an un-cross-validated surrogate).**
- Leave-one-out / k-fold CV per output; report Q² (predictive R²) + held-out test set.
- **Gate:** surrogate LOO error ≪ the decision tolerances — ≪ the f-tuning linewidth for f; **≪ the margin scale for C₀ and κc** (a surrogate error in C₀ or κc that materially moves Δf_max fails the gate). If not met → add solves where error concentrates.

**Active learning (spend COMSOL where it flips decisions).**
- Use GP variance to place new solves near the **decision boundaries**: f̂ ≈ f_spin (tuning feasibility), and — retargeted — where the **thermal budget is borderline** (Δf_max small, i.e. Ĉ₀ near 1 or κ̂c large; and, if ΔT_op is defined, near ΔT_max ≈ ΔT_op). That is where surrogate error actually changes the reported margins. Iterate fit → identify max-variance/boundary-adjacent points → solve → refit, until the gate holds within budget.

---

## 7.6 Error budget (the rigour that distinguishes this) — three channels

A margin number or distribution is meaningless without an interval. **Three error sources, all quantified** (was two; the thermal channel is new and may dominate):

1. **Monte Carlo sampling error** (finite N draws).
   - For any *proportion* (Y_tune, optional Y_thermal): **Wilson** or **Clopper–Pearson** interval. Pick N so this is ≤ ~1% (10⁴–10⁵ surrogate draws is cheap).
   - For the *distributions* p(ΔT_max) etc.: report CIs on the decision-relevant **quantiles** — e.g. the 5th-percentile margin ("the worst-off 5% of builds have margin < X") — by **bootstrapping the quantiles** over draws. The distribution's tail, not its mean, is what a tolerance budget acts on.

2. **Emulator (EM surrogate) error** — the surrogate is wrong by some amount → shifts Δf_max on borderline builds. Propagate:
   - *GP route:* draw K posterior realisations of the surrogate → run the full pipeline (incl. §7.3b composition) on each → {distribution_k} → report median + [2.5, 97.5] band on the quantiles/yields.
   - *PCE route:* bootstrap coefficients / LOO-error-inflated predictions to bound the same.

3. **Thermal-coefficient error (NEW)** — Layer B rests on df/dT, the pump model, and p-terphenyl properties, several of which are literature-uncertain or setup-dependent (SPEC.md §6T, §11). Propagate their uncertainty into ΔT_max / P_max as a coefficient-uncertainty band (Monte Carlo over the coefficient priors, or a sensitivity envelope). **Honesty point:** the budget's dominant uncertainty may well be df/dT or the pump-power model, not the EM surrogate — so report the decomposition and do not let a tight EM surrogate imply a tight budget. **Route status (2026-07-02):** the calibrated branch — propagate Cowley-Semple calibration residuals (SPEC.md §7.T5 checks 3a/3b) through this channel — is now the **likely** route, not hypothetical; but its width is still set by the df_spin/dT coefficient spread (−50…−80 kHz/K, SPEC.md §6T) and the laser-power metadata gap, both of which must propagate. The literature-prior envelope survives as the fallback *and* as the prior on df_spin/dT even within the calibrated branch.

**Report combined, contributions separated**, e.g. *"5th-percentile ΔT_max = 0.42 K, 95% CI [0.31, 0.55] (sampling + EM-emulator + thermal-coefficient), thermal-coefficient dominant."*

**Convergence diagnostics:** quantiles/yield vs N (sampling); surrogate Q² vs training size; Sobol vs N (§7.7). Seeds pinned (SPEC.md §1).

---

## 7.7 Sensitivity → tolerance / design budget

Three views; report all three — they answer different questions.

**Variance-based (Sobol) — the standard reportable.**
- First-order S_i and total-effect S_Ti for the budget outputs (Δf_max, ΔT_max) and the FOMs (f, C₀, κc), from PCE coefficients (analytic — free). *Hypothesis (then test):* εr + dimensions dominate f; tanδ + confinement (V_mode-driving geometry) dominate C₀ and κc, hence the thermal margin. Note the composition means a parameter can enter the margin through both C₀ and κc — total-effect indices capture that; first-order alone may mislead.

**Q-vs-margin scaling — the scientific hook (SPEC.md §7.T4).**
- Distinct from a tolerance curve: test the Q-dependence of the thermal margin. *(Re-based 2026-07-13, SPEC §7.T4: the "higher-Q ⇒ less margin" 1/√Q form is the κc ≫ κs limit; at the operating point κc/κs ≈ 0.18 the derived exponent is ≈ +0.35 — higher-Q builds have MORE margin there, with the turnover near κc ≈ κs. The regression below now tests the derived turnover map, not the bare −1/2.)* Two parts:
  - *Empirical (free):* regress sampled ΔT_max (and Δf_max) against sampled Q — determine the sign and local slope of the dependence, and compare against the two-linewidth turnover map at each draw's κc/κs.
  - *Derived (required before claiming):* get the *joint* dependence of C₀ and κc on the geometry DOFs from the surrogate — do **not** assume C₀ ∝ Q with N, g_s, κ_s fixed; those may carry their own geometry/Q dependence that breaks the clean scaling. Confirm the trend survives in ΔT space (folds in df/dT), not only Δf space.
- If it survives, this is the sharpest claim in the deliverable (§7.8, output 2).

**Tail / yield-gradient — what actually sets the budget.**
- Variance ≠ failure. Complement Sobol with ∂(low-margin-tail)/∂(tolerance_i) — sweep each tolerance, others fixed, read how the 5th-percentile margin (or Y_thermal) responds. The parameter whose tightening most raises margin is the budget priority — **not always** the top-variance parameter.

**Tolerance / design budget — the engineering output.**
- *Core:* **one-at-a-time budget curves** — margin (5th-percentile ΔT_max, or Y_thermal) vs each tolerance, others nominal. Read off "to guarantee ΔT_max ≥ X K for Y% of builds, radius ≤ ±A µm, εr spread ≤ B, tanδ ≤ C."
- *Stretch:* **constrained tolerance allocation** — minimise a manufacturing-difficulty cost subject to margin ≥ target.

---

## 7.8 Deliverables / scientific claims (state precisely; do not overclaim)

Four outputs, in order of novelty:
1. **Thermal-budget distribution with error bars (owned, novel).** First quantified distribution of thermal operating margin — p(Δf_max), p(ΔT_max), p(P_max) — for the STO TE01δ pentacene maser under realistic fabrication + material scatter, *at the tuned operating point.* Literature has FOM point values and, at most, a single lumped operating ΔT (Wu); no distribution, no error bars, no build-population view.
2. **Q-vs-margin scaling (novel; two-mode derivation DELIVERED 2026-07-13 — SPEC.md §7.T4; still conditional on the §7.7 joint-DOF derivation).** Branch-honest, not a single power law: the Q-margin exponent's **sign is set by the linewidth hierarchy** (turnover map `thermal/reports/q_margin_turnover.md`; crossings near Q_L ≈ 63 and ≈ 973 at current parameters). Under the ODMR κs branch (≈ 1.4 MHz, §6T `KAPPA_S`) the operating point (κc/κs ≈ 0.18) gives **E ≈ +0.35** — higher-Q builds have *more* margin there (planning-grade, **UNRATIFIED** — revises the direction of a question Oxborrow verbally endorsed 2026-07-06; findings note drafted, not sent — `docs/q_margin_two_linewidth_findings_note.md`; ratification pending). Under the FID branch the operating point sits near/across the turnover and the sign is **not established**. Angus's zero-power linewidth extrapolation is the branch discriminator. Do not lead with either exponent until the §7.7 derivation and the ratification land.
3. **Explanation of the literature Q spread.** The C₀/Q distribution under realistic tanδ + geometry scatter spans the Breeze→Wu range ⇒ the 2× Q / 30% gap is **tolerance- and provenance-driven, not a contradiction** between papers. Strengthened by §7.4 Bayesian re-inference if done.
4. **Tolerance / design budget.** The DOF tightness required for target thermal margin, with dominant DOFs identified (§7.7).

**Framing guard (carry + extend):** Booth named "Monte Carlo or gradient descent" as future work but for dielectric-ring **shape optimisation**, and did not execute it. Wu gave a single lumped operating ΔT, not a margin distribution. **No prior work modelled the maser's thermal operating margin across the build population, nor its scaling with Q.** The tolerance/yield interpretation *and* the thermal-margin framing are the novel contributions. Do not assert any prior work specified thermal yield or margin analysis. The resonator-shape / thermal-management optimisation Oxborrow raised is a *future-work pointer* (SPEC.md §9), not part of this deliverable.

- **Data status guard (updated 2026-07-02):** the Cowley-Semple ODMR dataset exists and has been shared *within the host–guest collaboration thread* — it was not produced for, or promised to, this project. Access to raw points + metadata is a live ask via Oxborrow (SPEC.md §11 item 5). Do not present it as this project's measurement; byline Cowley-Semple, Bayliss group. If used in the manuscript, co-authorship/acknowledgement is a conversation for Oxborrow to broker — flag early, not at submission.

---

## 7.9 Scope tiers + binding constraint

Binding constraint: **COMSOL solve budget (O(150–300)) and the 8-week clock.** The thermal layer is closed-form and adds no solves, but it adds derivation + sourcing work (df/dT, pump model, calibration). Tier so the result lands even if stretch is cut.

- **Core (must — = a publishable result):** §7.2–7.3b conditional evaluation + thermal composition at operating point; §7.4 geometry + material baseline distributions (assumed ranges) + fixed thermal coefficients; §7.5 PCE surrogate + CV gate; §7.6 budget distributions with sampling + EM-emulator + thermal-coefficient intervals; §7.7 Sobol + OaT budget curves + the *empirical* Q-vs-margin check; §7.8 outputs 1 + 3 + 4. Plus the thermal submodel itself (SPEC.md §7T).
- **Recommended (if time):** output 2's remaining chain — Layer-A joint-DOF validation of the turnover map (§7.7 "derived" half) → linewidth-branch discrimination (Angus zero-power κs extrapolation, external) → Oxborrow ratification (gate, pending); §7.4 Bayesian re-inference (→ output 3 strengthened); §7.5 GP active learning; §7.6 GP-posterior emulator interval; §7T/§7.T5 calibration against the Cowley-Semple ODMR dataset — **EXECUTED 2026-07-14** at graph-digitized-provisional grade (Layer B, calibration/reports/observable_a_feed.json; SPEC.md §11 item 5); re-run at raw-trace grade pending Angus's files.
- **Stretch:** §7.4 input correlation; §7.7 constrained tolerance optimisation; eccentricity 3-D side-study if perturbation insufficient; thermal-coefficient *scatter* as sampled noise; transient (pulsed-pump) thermal vs steady-state; operating temperature as a second control/noise variable.

---

## 7.10 Open gaps / actions

Carried:
1. **Real workshop machining tolerances** (replace ±25 µm). — Oxborrow / workshop. **ACTION.**
2. **Plate-sensitivity of C₀ *and* κc**, ∂/∂p_tune (decides §7.3 coupled vs decoupled). — measure in Phase 1b (SPEC.md §5b).
3. **Eccentricity method**: perturbation vs bounded 3-D vs drop (§7.4). — decide after a first-order estimate.
4. **Material distribution shape + εr–tanδ correlation** (§7.4). — assumption; test sensitivity.
5. **Primary 22-GHz STO tanδ source** (carry) for the writeup.

New (thermal — most live in SPEC.md §11; the statistics-specific ones here):
6. **ΔT_op — is there a defensible operational heating level?** Decides whether Y_thermal (§7.3) is reportable or whether the distribution stands alone. Grounded in the real pump model (SPEC.md §6T / §11.6), not invented.
7. **Thermal-coefficient error propagation method** (§7.6 channel 3): Monte Carlo over df/dT / pump / property priors vs sensitivity envelope. — decide once §6T values are graded.
8. **Quantile-CI method** for the distribution outputs (bootstrap vs analytic) — pick and state.
9. **Q-vs-margin derivation** (§7.7 / SPEC.md §7.T4) — required before output 2 is claimed; the §7.3b linewidth choice is SETTLED 2026-07-13 — combined (κc + κs), SPEC.md §7.T4 re-derivation; the open remainder is the joint C₀/κc/κs dependence on the geometry DOFs from Layer A.
10. **Depends on SPEC.md §11 upstream:** Cowley-Semple ODMR calibration data — identity/existence **resolved**, metadata pending (§11 item 5); pump illumination model (§11 item 6); thermal properties + df/dT sourcing, largely done, Nat. Commun. 2025 pull remaining (§11 item 7); pre-Phase-2 C₀/κc re-run (§11 item 8); Oxborrow's confirmation of the framing (§11 item 10).
