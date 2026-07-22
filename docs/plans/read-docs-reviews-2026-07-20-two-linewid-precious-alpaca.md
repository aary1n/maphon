# Voigt/multi-packet audit of the two-linewidth thermal margin (§7.T4)

## Context

The uncommitted session record `docs/reviews/two_linewidth_falsification_handoff.md` (preserve, do not edit) claims, from out-of-repo sandbox numerics: (1) the committed law `Δf_max = ((κc+κs)/2)·√(C0−1)` and its fixed-G exponent are correct as committed; (2) the single-packet mapping is **exact** for a Lorentzian inhomogeneous line (κs = hom + inhom) but **fails** for Gaussian/Voigt lines — margin −32 % (11.39 → 7.77 MHz) and the Q-margin exponent sign-inverts (+0.35 → ≈ −0.16) in the inhomogeneity-dominated scenario. This directly conditions the unratified headline of `docs/q_margin_two_linewidth_findings_note.md` (C2: "higher-Q builds have more thermal margin"). Task: independently re-derive/reproduce/falsify this in-repo, with correct normalisation, exact Voigt sizing, and convergence discipline — treating the handoff as untrusted hypotheses — and judge whether the findings note should be revised. No commits; no edits to SPEC, findings note, claim register, provenance constants, or existing reports/tests.

## Key facts grounded during exploration

- Law + exponent: `src/cavity/thermal/detuning.py:397-445` (`delta_f_max_hz`, `q_margin_exponent`); anchors A1–A14 in `tests/test_thermal_detuning.py` (A6 planning pins at 299-341; A12/A13 limit identities at 356-373); byte-pinned reports `thermal/reports/q_margin_planning_point.md` / `q_margin_turnover.md` via generators `report_margin.py` / `report_turnover.py` (pattern: deterministic `build_report()` string + `committed.read_text() == build_report()` test).
- Operating point (single-sourced): `own_model_point()` in `report_margin.py:79-100` (Q0 = 6764.5852, p_e, from the rejudge manifest), `q_loaded` (k = DELOAD_K = 0.2) → κc = `resonance_linewidth_hz(1.45e9, Q_L)` = 257.222 kHz cyclic-FWHM; κs = `KAPPA_S.kappa_s_hz` = 1.400 MHz (band 0.55–1.75); `PLANNING_C0 = 190.0` (report-local literal by design, `report_margin.py:62-63`).
- **Normalisation ruling exists**: ratified "amendment C" C0-import convention (`report_margin.py:211-219`, SPEC §7.T4 re-derivation block): C0 = 190 is the imported algebraic resonant cooperativity 4G²/(κc·κs_composite), never recomputed; sweeping κs at fixed imported C0 holds G²/κc fixed. ⇒ **fixed-G with G² = C0·κc·κs_comp/4 is the repo-consistent primary normalisation.** The handoff's check-6 margins instead used G²_th(Δ)/G²_th(0) = 190 (fixed on-resonance threshold ratio) — a different, secondary convention. Both get computed and labelled.
- The single-packet mapping is already flagged as an assumption (KAPPA_S docstring `constants.py:~921-926`, `q_margin_planning_point.md`, SPEC §7.T4); its resolution is the open D4 conjunction (`docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md:85`). No Voigt/multi-packet threshold code exists in-repo.
- scipy ≥ 1.10 is a declared dependency (`pyproject.toml`) and tests already import scipy ⇒ `scipy.special.wofz` (Faddeeva) and `scipy.optimize.brentq` are available.

## Physics/implementation design (mine, independent of the handoff's code)

Matched cyclic-MHz-FWHM units throughout (amplitude rates = FWHM/2 numerically; degree-1 homogeneity makes this exact; stated in docstrings). Spin line centred at 0, cavity at detuning Δ.

1. **Multi-packet threshold (class-A, quasi-static uniform inversion, weights = normalized composite line profile — stated explicitly).** Dispersion relation at marginal eigenvalue λ = −iω (free-running ruling): `1 = G²·S(ω)`, `S(ω) = S_spin(ω)/(a_c + i(Δ−ω))`. Threshold = min over real roots of Im S = 0 with Re S > 0 of `G²_th = 1/Re S(ω)` (first imaginary-axis crossing as G² grows from the stable G² = 0 spectrum — rigorous minimum argument goes in the docstring).
2. **Exact Voigt susceptibility — no grids/truncation** (upgrade over the handoff): for a Gaussian distribution (std σ_g) of Lorentzian packets with amplitude rate a_s (hom HWHM), `S_spin(ω) = √(π/2)/σ_g · wofz(ζ)`, `ζ = (ω + i·a_s)/(√2·σ_g)`; σ_g = 0 branch = closed form `1/(a_s − iω)`. (Derivation via the plasma-dispersion identity; I re-derive it in the module docstring.)
3. **Exact composite-FWHM sizing**: Voigt profile ∝ Re wofz((x+i·a_s)/(√2σ_g)); nested bisection solves σ_g so the composite FWHM = 1.400 MHz exactly given hom FWHM f_L (retires the handoff's Olivero–Longbothum ≈1.44/1.29 MHz imprecision). Sweep f_L ∈ {0.05, 0.10, 0.20, 0.35, 0.50, 0.70, 1.00, 1.20, 1.40} MHz (1.40 = pure-Lorentzian repo branch, σ_g = 0).
4. **Root scan**: Im S sign-change scan on a window covering [−W, Δ+W] (W ≈ 30 MHz, ~3000 nodes) + brentq (xtol 1e−12), min-over-roots; Δ = 0 symmetric case handled analytically (ω = 0 root). Scan-resolution/window doubling must leave margins invariant (pin).
5. **Margins, both normalisations**: `margin_fixed_g2(g2, …)` solves `G²_th(Δ) = G²` by brentq (primary: G² = C0·a_c·a_s,comp from amendment C); `margin_onres_ratio(c0, …)` solves `G²_th(Δ)/G²_th(0) = C0` (handoff convention, secondary). Single-packet identity: both coincide and equal `delta_f_max_hz` (pin).
6. **Fixed-G exponent, direct route**: E = dln Δf_max/dln Q_L at fixed G² and fixed spin line, κc = f/Q_L — central log-difference re-solving the margin at a_c/(1±ε), ε = 0.05 with an ε = 0.02 consistency check (calibrates finite-difference bias; the Lorentzian control must reproduce `q_margin_exponent` = +0.34743). Evaluate at both normalisation anchorings of G². The handoff's target∝Q shortcut becomes a verified identity (symmetric lines), not the implementation.
7. **Validation-only discrete ensembles (live in the test file, not src)**: quantile-sampled Lorentzian distribution (Γ) ⇒ must equal single-packet with κs_eff = κs_hom + 2Γ (FWHM add) — the handoff's gate identity; Gaussian grid ensemble ⇒ must converge to the exact wofz threshold under node/span doubling.

## Files (all new; nothing existing is modified)

1. `src/cavity/thermal/ensemble_threshold.py` — the module per design above (§7.T4 sensitivity audit; docstring states inversion/packet-weight assumptions, units, normalisation conventions with amendment-C cross-ref, far-wing caveat: at ~13 combined half-widths detuning ALL cases — including the committed Lorentzian law — carry the margin on far Lorentzian packet tails).
2. `tests/test_thermal_ensemble_threshold.py` — anchor map V1–V10 (§8 discipline, mirroring `test_thermal_detuning.py` style):
   - V1 single-packet ensemble route reproduces `delta_f_max_hz` + pulled frequency (closed form, rel ≤ 1e−9).
   - V2 degenerate σ_g → 0 Voigt = single packet (A12/A13-family continuity).
   - V3 Lorentzian-distribution identity (the gate): discrete quantile ensemble = single-packet κs_eff law, rel ≤ 1e−4.
   - V4 exact Voigt FWHM sizing: solved composite = 1.400 MHz to 1e−10; f_L = 1.4 ⇒ σ_g = 0; f_L → 0 ⇒ pure-Gaussian FWHM identity; Olivero–Longbothum agreement ≤ 1e−3 (diagnostic).
   - V5 normalisation identity on the Lorentzian branch (fixed-G ≡ on-res-ratio ≡ closed form) + strict inequality/ordering for Voigt cases.
   - V6 discrete-Gaussian-vs-wofz convergence: ≤ 1e−3 rel at base grid, improving under doubling; scan-window/resolution invariance ≤ 1e−6.
   - V7 fixed-G exponent control: numeric E on the Lorentzian branch = `q_margin_exponent(190, κc, κs)` within finite-difference bias; ε = 0.05 vs 0.02 consistency.
   - V8 target∝Q shortcut identity for symmetric lines (validates handoff check 7's substitution).
   - V9 handoff reproduction: their scenario probes (a_s = 0.05/0.25, σ = 1.39/2.35482, 1.00/2.35482, on-res-ratio normalisation) reproduce 7.77/7.51 MHz and E ≈ −0.16 within stated tolerance (~1e−2 rel; their formulation, my solver). If the sign flip does NOT reproduce → stop and report.
   - V10 regression pins on the new headline numbers (exact-FWHM sweep, both normalisations, units + convention stated in comments, absolute values) — values computed during implementation, cross-checked by an independent in-session recomputation before pinning (scoping-numbers discipline).
3. `src/cavity/thermal/report_voigt.py` — lean generator (imports `PLANNING_C0`, `own_model_point` from `report_margin`, κs from `KAPPA_S`; PASS_DATE 2026-07-20) emitting `thermal/reports/q_margin_voigt_sensitivity.md`: status notes (NOT a claim; D4 tie-in; scenario-probe rung; inversion/weight assumptions; normalisation conventions; far-wing caveat; findings-note implication left as recommendation only), parameters, the (f_L → margin, E) table under both normalisations with the E = 0 sign contour f_L* (bisected, both normalisations), Lorentzian row ≡ committed law row, handoff-reproduction note. Byte-pinned in the new test file (same pattern as A11/A14).
4. `thermal/reports/q_margin_voigt_sensitivity.md` — the generated artifact.

## Execution order

1. Module + V1–V8 anchors (physics machinery proven before any headline number).
2. Reproduce handoff numbers (V9). Stop-and-report triggers: sign flip fails to reproduce; normalisation grounding contradicts amendment C on inspection; scope balloons.
3. Compute the exact-FWHM sweep under both normalisations; independent recomputation cross-check; pin (V10).
4. Generator + report + byte-pin; run `python -m cavity.thermal.report_voigt`.
5. Adversarial self-check pass: convergence doublings, window sensitivity, ε sensitivity, min-over-roots branch audit at the largest Δ, sanity of far-wing asymptotics (Re S_spin → a_s/Δ² scaling).

## Verification

- `python -m pytest tests/test_thermal_ensemble_threshold.py -v` (new anchors + byte-pin).
- `python -m pytest tests/test_thermal_detuning.py tests/test_thermal_broadening.py` (no regression in the touched physics area), then the full suite `python -m pytest` (expected 1022+ pass / 21 skip baseline).
- `git status`/`git diff --stat` to enumerate the exact uncommitted files for review; confirm handoff untouched; no commits.

## Final report (to user)

Answers, in order: (1) what was implemented; (2) handoff claims reproduced/changed/failed — including that its margins used the secondary (on-res-ratio) normalisation while amendment C grounds fixed-G, with the quantitative difference; (3) the defensible conclusion (expected shape: margin reduction and E sign are conditional on the hom/inhom decomposition — the D4 unknown; committed +0.35 requires the Lorentzian-composite branch; exact numbers from the run); (4) remaining assumptions (uniform inversion/spectral-density weights, common a_s across packets, Lorentzian packet tails at 10+ widths, class-A, C0-import fiction); (5) test + convergence results; (6) recommendation on the findings note (revise/withhold/unchanged — decided by the numbers, not pre-committed); (7) exact uncommitted diff/file list.
