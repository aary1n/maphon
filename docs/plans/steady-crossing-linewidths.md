# Plan — the two-linewidth threshold pass (`steady-crossing-linewidths`)

**Status: RATIFIED 2026-07-13** (planning pass 2026-07-13; GO received same day with
three physics amendments A–C and a filesystem-safety contract, both folded in below).
Baseline reconciled pre-pass: tier-1 suite **528 passed / 21 skipped / 0 xfailed**
(20 COMSOL-licence skips + 1 MPh-installed environment skip). The `--comsol` tier
still lacks its clean post-figures capture (licence outage); this pass is COMSOL-free —
tier-1 governs.

## Why this pass exists

The committed detuning-margin law Δf_max = (κc/2)·√(C₀−1)
(`cavity.thermal.detuning.delta_f_max_hz`, SPEC §7.T4) is the κs → 0 limit of the
general linearised two-mode result, and the operating point is NOT in that limit:
own-model composed κc ≈ 257 kHz vs κs = 0.55–1.75 MHz from the Cowley-Semple
linewidth table (SPEC §11 item 5) puts κc/κs ≈ 0.15–0.47, the far side of the
turnover. An external review argument, verified here by independent derivation,
gives the general law and shows the §7.T4 1/√Q hypothesis inverts sign at our
operating point. This pass derives the correct law on the record, implements it, and
re-bases everything downstream of Δf_max. It does NOT start Layer A — Layer A stays
deferred until this law is settled, because its sweep design was shaped by the
cavity-only scaling.

## 1. The derivation (on the record, not cited)

**Model.** Linearised two-mode maser equations for the cavity field amplitude `a`
and the collective spin coherence `σ`, single homogeneous spin packet, inversion
adiabatically clamped (class-A):

    ȧ = −(κc/2 + iωc)·a − iG·σ
    σ̇ = −(κs/2 + iωs)·σ + iG·a        (inverted medium; G² = g²·N_eff·S_z > 0)

κc, κs are energy decay rates = FWHM linewidths (amplitudes decay at κ/2).
Threshold = the eigenvalue λ of the 2×2 system crossing the imaginary axis, λ = iω:

    (κc/2 + i(ω−ωc)) · (κs/2 + i(ω−ωs)) = G²

**Imaginary part** ⇒ the oscillation frequency is forced (not chosen):
ω = (κc·ωs + κs·ωc)/(κc + κs) — the linewidth-weighted mean, weighted toward the
narrower resonance. **Real part**, after substituting the pulled ω, with
Δ = ωc − ωs:

    G² = (κc·κs/4) · [1 + 4Δ²/(κc + κs)²]

With C₀ ≡ 4G²/(κc·κs) (resonant cooperativity; threshold C₀ = 1 at Δ = 0):

    C₀(threshold) = 1 + 4Δ²/(κc + κs)²    ⇒    Δf_max = ((κc + κs)/2)·√(C₀ − 1)

Cross-checks, each a CI anchor (§7 below):

- **κs → 0 limit:** ω → ωs (the oscillator clamps to the spin line; the cavity
  Lorentzian rolls off the effective gain) and the law reduces EXACTLY to the
  committed (κc/2)·√(C₀−1). The committed Lorentzian roll-off
  C(Δ) = C₀/(1+(2Δ/κc)²) is precisely the κs → 0 shadow of the real-part
  condition. The old law is recorded, dated, as this limit — never deleted.
- **Symmetric point** κc = κs = κ: Δf_max = κ·√(C₀−1), twice the committed value.
- **Large-C₀ asymptote:** Δf_max ≈ G·(√(κc/κs) + √(κs/κc)) — the review's
  (G/√κs)(√κc + κs/√κc), same expression.
- **Exponent under the napkin scaling** (G, κs fixed; κc = f/Q_L; hence
  C₀ = 4G²/(κcκs) ∝ Q_L — exactly the existing anchor-A5 parameterisation
  C₀ = c·Q_L):

      E(Q_L) ≡ d ln Δf_max / d ln Q_L = −κc/(κc + κs) + C₀/(2(C₀ − 1))

  Limits: κc ≫ κs at large C₀ → **−1/2** (the committed hypothesis, recovered as a
  limit; A5's existing expression −1 + cQ/(2(cQ−1)) is the κs = 0 member);
  κc ≪ κs at large C₀ → **+1/2** (sign inversion); turnover E = 0 at
  κc/(κc+κs) = C₀/(2(C₀−1)), which → κc = κs exactly as C₀ → ∞; near threshold
  E → +∞ (the existing A5 positive-branch pin generalises). Closed-form turnover
  under the napkin parameterisation: E(Q) = 0 ⇔
  **Q² − (f/κs)·Q + 2(f/κs)/c = 0** — a quadratic in Q_L, roots exist iff
  C₀(at κc = κs) ≥ 8.

**Operating point:** own-model composed κc = 257.222 kHz, κs = 1.4 MHz ⇒
κc/κs ≈ 0.184 (band 0.147–0.468 across the κs band). At C₀ = 190:
E ≈ −0.1552 + 0.5026 = **+0.3474**. The §7.T4 1/√Q hypothesis inverts sign at our
operating point: higher-Q builds have MORE thermal frequency margin here, exponent
≈ +0.35, not −0.5. The finding is margin-favourable: the committed κs → 0 law was
the minimal member of the family — it understated Δf_max ×6.44 at the planning
point. At the planning calibration (c = 190/5637.15) the exponent curve is
genuinely non-monotone: +∞ near threshold → zero near Q_L ≈ 63 → a negative
(committed-law-like) valley → zero again near Q_L ≈ 973 → +0.347 at Q_L = 5637 →
+1/2 asymptotically. The large-C₀ turnover sits at Q_L = f/κs ≈ 1036.

**Stated assumptions (carried into the SPEC hunk and module docstrings):**

1. **Linear gain regime** — small-signal threshold analysis; exact AT threshold by
   construction; silent on above-threshold saturation.
2. **Single homogeneous spin packet** — κs is the FWHM of one effective Lorentzian
   package. The measured ODMR linewidths fold homogeneous + inhomogeneous +
   MW/laser power broadening into one number; mapping the table value onto κs is a
   graded approximation stated in the κs rung. O12's "few MHz" inhomogeneous width
   is NOT additionally stacked — the table value is taken as the total effective
   line FWHM of the planning branch.
3. **Both linewidths FWHM cyclic-Hz.** The threshold relation is homogeneous of
   degree 1 in (Δ, κc, κs) and C₀ is invariant under uniform 2π rescaling, so the
   angular derivation transfers verbatim to the committed cyclic convention
   (κc = f/Q_L, the existing guard). Cross-pin: FWHM-cyclic κs = 1/(πT₂) — O12's
   own convention (fitted Δf ≡ 1/(πT₂) ≈ 860 kHz). W20's "κ_s = 1.1 MHz" is
   ANGULAR (provenance table, trap 1) and additionally rate-vs-FWHM murky — never
   imported. Anchor A6 gets its κs 2π-trap sibling.
4. **C₀-import convention (planning):** C₀ = 190 remains the imported resonant
   cooperativity; κs does NOT recompute C₀ (no G² exists — Phase 1b field-integral
   work, out of scope). The turnover map, by contrast, is drawn at fixed G and κs
   with c calibrated so C₀(Q_L = planning) = 190 — the same napkin C ∝ Q assumption
   A5 already encodes. Both conventions stated where used. The joint C₀/κc/κs DOF
   dependence remains Layer A's job (§11 item 9) — untouched rung.

**Oscillator vs amplifier — ruled: free-running oscillator; pulling is an outcome,
not an option.** The maser has no injected signal and no external frequency clamp;
the operating frequency is the imaginary part of the marginal eigenvalue, which the
threshold analysis FORCES to the weighted mean — there is no self-consistent
zero-crossing at any other frequency. Physical corroboration already in the
provenance table: B15's measured 1.4493 GHz output is described there as the
cavity-pulled peak (row f_XZ), and with κs > κc the pulled frequency sits nearer
the cavity — consistent. **If ever reversed** (injection-locked / fixed-frequency
amplifier operation): threshold-at-fixed-ω is no longer an eigenvalue crossing;
the margin question becomes regenerative-gain-at-ω₀ through the product of both
Lorentzians and the law must be re-derived — recorded as a rider in §7.T4, no
implementation.

## 2. κs provenance — new graded constant

New frozen dataclass in `provenance/constants.py` (the `SpinFreqTempCoefficient`
pattern: long rung docstring, branch choice documented, band fields), instance
`KAPPA_S`:

- `kappa_s_hz = 1.4e6` — point, the **0.1% Pc-d₁₄:PTP-d₁₄ branch** of the
  Cowley-Semple linewidth table (§11 item 5, in-thread 2026-06-26, scraped).
  Argued: (i) it is the deuterated-sample branch the Phase-2 calibration chain
  lives on (same samples as the ν(I) series); (ii) it is interior to the band, per
  the DF_SPIN_DT edge→interior convention. Stated against it, in the rung: the
  maser crystal itself is 0.053% protonated (Breeze 2017, `Crystal`) — it matches
  no table row, and no κs measurement of that crystal exists (the provenance
  table's "sample-specific — not importable" warning on the T₂/κs row carries
  verbatim).
- `kappa_s_band_lo_hz = 0.55e6`, `kappa_s_band_hi_hz = 1.75e6` — the Pc:PTP-host
  rows only (0.01% d₁₄ / 0.1% d₁₄ / 0.1% protonated). Picene (7 MHz) and NAP
  (1.8 MHz) are different hosts — excluded from the band, said explicitly.
- Rung and caveats, all in the docstring: best-per-host at differing MW/laser
  powers — NOT a controlled comparison (SPEC's words, verbatim); scraped-thread
  depth, raw table = existing Angus raw-data rider, now load-bearing; ODMR FWHM
  conflates homogeneous 2/T₂ with inhomogeneous and power broadening — the
  single-packet mapping is a model assumption, not a data property; ensemble
  context (Yang 2000 FID 0.7 MHz at 0.01%, O12 fitted 860 kHz, W20's angular
  1.1×10⁶ s⁻¹ — context only, unit-trap flagged, never band-setting); direction of
  conservatism: at fixed imported C₀, smaller κs ⇒ smaller Δf_max, so the 0.55 MHz
  edge is the conservative side and the old κs → 0 law was the maximally
  conservative member; temperature dependence: κs is T-dependent in reality, and
  the §7.T2 output-3 broadening machinery computes exactly the thermally-added
  inhomogeneous width — this constant is the STATIC, T-independent planning
  branch; the κs(ΔT) feedback loop is the identified follow-on, not implemented.

No fresh literals anywhere else: report, figure, tests, and turnover map all
import `KAPPA_S`.

## 3. Implementation shape

- **`delta_f_max_hz(c0, kappa_c_hz, kappa_s_hz)` — breaking change, third argument
  required.** A κs = 0 default would silently keep every existing call site on a
  law now established as the wrong limit at the operating point — the exact
  silent-meaning-change the flag-carriage convention forbids. Requiring the
  argument forces every call site to declare its κs branch. `kappa_s_hz = 0.0`
  stays legal (the well-defined limit; the regression-continuity anchor and the
  §5a archive renderer use it explicitly); negative raises; C₀ ≤ 1 → 0.0
  unchanged.
- **New closed-form helper `q_margin_exponent(c0, kappa_c_hz, kappa_s_hz)`** in
  `detuning.py` returning E = −κc/(κc+κs) + C₀/(2(C₀−1)) — tested against a
  numerical log-slope of the actual map (independent check).
- **`delta_t_max_k` — confirmed unchanged.** It consumes Δf_max as an opaque input
  and inverts the differential map, which this pass does not touch; the Newton
  branch already covers the 30 K envelope scale (~88 MHz differential), so the new
  ~11.4 MHz budget is interior to its tested range. A4 gains the new planning value
  in its round-trip list.
- **The turnover map — the new §7.T4 object replacing the bare −1/2 exponent.**
  New module `cavity.thermal.report_turnover` rendering
  `thermal/reports/q_margin_turnover.md`, byte-pinned: the law and its dated
  derivation summary; Δf_max vs Q_L (log-spaced) at fixed G and κs with c
  calibrated at the planning point; E(Q_L) alongside; both E-zero crossings from
  the closed-form quadratic, cross-checked against the large-C₀ form Q_L = f/κs;
  the operating point marked; κs-band sensitivity of the crossings. No figure this
  pass (`q_margin_turnover.png` NOT created). Status notes carry the κs rung, the
  C₀-import vs fixed-G convention split, and the unchanged Layer-A boundary.
- **`report_5a.py` — the archive-immutability ruling.** `render_checkpoint_markdown`
  regenerates the two committed gate records byte-identically (pinned in
  `test_report_5a.py`); those records printed Δf_max under the record-time law,
  formula in-text. Ruling: the renderer calls
  `delta_f_max_hz(..., kappa_s_hz=0.0)` EXPLICITLY, with a dated comment: archived
  records are immutable historical documents rendering their own printed formula;
  the next §5a record minted switches to the general law. `test_report_5a.py`
  must pass UNCHANGED — needing to edit it means this branch failed (STOP).

## 4. Downstream re-bases (hand values; exact numbers through committed functions)

- **`report_margin.py` + `q_margin_planning_point.md`:** Δf_max =
  ((257.222 kHz + 1.4 MHz)/2)·√189 ≈ **11.3915 MHz** (was 1.7681 — ×6.44);
  ΔT_max ≈ **3.90 K** via the unchanged inversion (was 0.6030). Bands: κs band →
  Δf_max ∈ ≈[5.549, 13.797] MHz (linear in κs); §6T coefficient band at point-κs →
  ΔT_max ≈ [3.772, 4.819] K; outer envelope (κs-lo × coeff-hi … κs-hi × coeff-lo)
  ≈ [1.84, 5.84] K. The "sub-K regime / nonlinearity <0.1%" language dies: linear
  band arithmetic RETAINED as the band convention (invisible against the ×1.7
  spin-axis and κs-band systematics), with the linear-vs-true-inversion
  discrepancy at the new scale quantified and pinned (A10 sibling). New status
  notes: κs rung + not-controlled-comparison + static-planning-branch + C₀-import
  convention + amendment-C direction-of-bias + the sign-inversion finding line
  (derived, unratified).
- **F5 waterfall:** gains a κs stage (six mini-panels: Q₀ → Q_L → κc → κs →
  Δf_max → ΔT_max); κs bar carries band whiskers [0.55, 1.75] MHz and its rung
  note; the transform label becomes ((κc+κs)/2)·√(C₀−1); caption rewritten — κs
  provenance + caveat, the inversion finding, amendment-A envelope sentence, all
  existing flags retained. Regenerated into `docs/figures/`.
- **Anchors A4/A5/A6** re-derived/re-pinned (§7). **`test_figures.py`:** F5 stage
  pins re-pinned; `CAPTION_FLAGS["f5_margin_waterfall"]` gains κs-caveat and
  inversion-finding tokens.
- **`mc_yield/__init__.py`** docstring: per-draw formula updated, κs from
  `KAPPA_S` per draw (static branch), future κs(ΔT) coupling noted.
- **One-pager:** F5 caption block synced; margin sentence re-based; Asks gains the
  Q-margin derivation-update item.
- **`SPEC_phase2_expanded.md`:** the Δf_max formula sites updated to the general
  law with a pointer to the §7.T4 re-derivation.
- **The κs(ΔT) feedback loop** (broadening output → κs(ΔT) → threshold):
  identified and scoped as the coupling this pass enables, NOT implemented.
  Flagged in the SPEC §7.T4 hunk, the KAPPA_S docstring, and the mc_yield
  docstring as the follow-on pass. Deferral rationale: it needs the probe-weighted
  inhomogeneous width composed with the homogeneous line under a convolution model
  that `broadening.py` explicitly does not claim — a real modelling decision, not
  a wiring step.

## 5. SPEC hunks (all Fable-tier)

1. Revision-note dated block (2026-07-13): the two-linewidth pass — external-review
   argument checked by independent derivation; old law recorded as the κs → 0
   limit; sign inversion at the operating point; κs graded; downstream re-based;
   Layer A remains deferred pending this law.
2. §7.T4 rewrite: napkin paragraph stays as history, dated; general law +
   pulled-oscillator derivation summary appended; hypothesis re-graded — question
   endorsed (unchanged rung), answer now derived and sign-inverted at the
   operating point, unratified; turnover map named as the section's object; the
   two hazards updated (hazard 1 now explicitly includes κs in the joint-DOF
   requirement); fixed-frequency-amplifier rider; κs(ΔT) follow-on flag; linkage
   note clarified (observable unit stays cavity linewidths Δf·Q/f; the margin
   law's scale is the MEAN linewidth (κc+κs)/2 — do not conflate).
3. §7 Layer C item 1: formula updated to Δf_max(θ) = ((κc+κs)/2)·√(C₀−1) with κs
   source stated.
4. Endorsement-ladder honesty (revision note + §11 items 9/10): he blessed the
   QUESTION; the answer has now changed sign — stated symmetrically; the finding
   routes via the drafted note before any headline use.
5. §11 item 5 linewidth-table note: the table now feeds the threshold law (κs);
   its not-controlled-comparison caveat propagates; the raw-table ask gains
   load-bearing status.
6. §6T: κs bullet (the graded constant, cross-referencing the provenance-table
   T₂/κs row and its traps).

## 6. Ratification-flag inventory

| Item | Flag | Vehicle |
|---|---|---|
| Turnover/sign-inversion finding | Needs Oxborrow before headline use — revises the direction of a result whose question he verbally endorsed | `docs/q_margin_two_linewidth_findings_note.md`, drafted, NOT sent; one-pager ask; names-and-claims grep before commit |
| κs grading (point + band) | Scraped-thread rung; not-controlled-comparison caveat; raw table = Angus rider, now load-bearing | Constant docstring + §11 item 5 note |
| Pulled-oscillator ruling | Ours, derived; standard for free-running masers; B15 pulled-peak corroboration | §7.T4 rider (with reversal clause) |
| C₀-import convention | Planning assumption | Report status notes + §7.T4 |
| Old −1/2 exponent pins | Recorded as the κs → 0 limit — retained in CI as the limit anchor | Test docstrings + §7.T4 dated block |

## 7. Test/anchor plan — closed forms only

- Regression continuity: `delta_f_max_hz(c0, κc, 0.0) == (κc/2)·√(C₀−1)` exactly.
- Symmetric point: `delta_f_max_hz(c0, κ, κ) == κ·√(C₀−1) ==` 2× the κs→0 value.
- A5 re-derived: numerical log-slope of the actual map under (C₀ = cQ_L,
  κc = f/Q_L, κs fixed) equals the closed-form `q_margin_exponent`; limits → −1/2
  (κc ≫ κs, large C₀ — the old pins, now the limit branch), → +1/2 (κc ≪ κs);
  near-threshold positive branch retained; turnover located via the closed-form
  quadratic Q² − (f/κs)Q + 2(f/κs)/c = 0, both roots asserted zero-exponent, → f/κs
  as C₀ → ∞; operating-point exponent ≈ +0.3474 pinned.
- A6 re-pinned from the report composition (amendment B — one κc, one f, via
  `own_model_point()`): κc ≈ 257.222 kHz; Δf_max ≈ 11.3915 MHz; ΔT_max ≈ 3.90 K
  (code-exact, verified against the ±1% hand estimate); band pins; κs 2π-trap
  sibling: feeding angular 2π·κs (≈8.796 MHz) inflates Δf_max to ≈62.2 MHz —
  asserted far outside tolerance; negative-κs guard.
- A4 extension: round-trip through the UNCHANGED inversion at the new scale
  (≈11.39 MHz → ≈3.90 K → back, rel 1e-9).
- Nonlinearity pin (A10 sibling): linear-band arithmetic vs true inversion at the
  new O(4 K) point, quantified, bounded corridor.
- Report/figure pins: both committed reports byte-pinned to their generators; F5
  `build_data` pins; caption flags; `test_report_5a.py` archive byte-pins pass
  UNCHANGED (proof the archive branch survived the signature change).

## 8. Baseline

Captured fresh pre-pass: 528 passed / 21 skipped / 0 xfailed — reconciled exactly.
Post-pass expectation: 528 + new anchors / 21 skipped / 0 xfailed; every delta
named; any other delta → stop and reconcile.

---

## PHYSICS AMENDMENTS (ratified with the GO, 2026-07-13)

- **A. Whiskers:** κs whiskers on the κs stage, §6T coefficient whiskers on
  ΔT_max, outer envelope in report text — PLUS one F5 caption sentence:
  "combined κs × coefficient envelope ≈ 1.8–5.8 K" so the figure alone shows the
  honest spread.
- **B. One κc, one f:** consume κc exactly as `report_margin` composes it
  post-re-base and derive the A6 hand-pin from that same source — one consistent
  composition, never two f-conventions in one report.
- **C. κs-band direction-of-bias sentence in the status notes:** sweeping κs at
  fixed imported C₀ = 190 holds G²/κc fixed; at fixed G the growth is ~√κs, so the
  κs-hi edge of the Δf_max band is overstated under the import convention. State
  the direction so the band is never read as convention-independent.

## FILESYSTEM-SAFETY CONTRACT (ratified with the GO, 2026-07-13; binding)

1. **Worktree isolation.** Codex never receives write access in the primary
   checkout. Every write-capable Codex task runs in a disposable task-specific git
   worktree + branch (`git worktree add ../maphon-wt-<task> -b codex/<task>`),
   created, inspected, merged (cherry-pick — stated call), and removed by Claude.
   Worktree made runnable (`uv sync`) before test-running delegations. Codex's cwd
   is the worktree root; the primary checkout path never appears in its prompt.
2. **Master manifest** (verified at step 0: every MODIFY path exists, every CREATE
   path absent — PASSED 2026-07-13). MODIFY ONLY: SPEC.md, SPEC_phase2_expanded.md,
   docs/supervisor_onepager_2026-07.md, src/cavity/provenance/__init__.py,
   src/cavity/provenance/constants.py, src/cavity/thermal/__init__.py,
   src/cavity/thermal/detuning.py, src/cavity/thermal/report_margin.py,
   src/cavity/validation/report_5a.py, src/cavity/mc_yield/__init__.py,
   src/cavity/figures/f5_margin_waterfall.py, tests/test_thermal_detuning.py,
   tests/test_figures.py, thermal/reports/q_margin_planning_point.md,
   docs/figures/f5_margin_waterfall.png, docs/figures/f5_margin_waterfall.pdf.
   CREATE ONLY: docs/plans/steady-crossing-linewidths.md,
   src/cavity/thermal/report_turnover.py, thermal/reports/q_margin_turnover.md,
   thermal/reports/q_margin_turnover.png (only if the turnover report renders a
   figure — it does not this pass), docs/q_margin_two_linewidth_findings_note.md.
   CREATE DIRECTORIES: none. DELETE/RENAME: none. Out of bounds even though
   nearby: tests/test_report_5a.py (must pass UNCHANGED), refs/** (immutable),
   .claude/**, CLAUDE.md, .gitattributes, .gitignore, pyproject.toml, uv.lock,
   .git, docs/plans/* other than this doc.
3. **Per-phase manifests:** Phase 3-Terra (re-pins): tests/test_thermal_detuning.py,
   tests/test_figures.py. Phase 4-Terra (regeneration):
   thermal/reports/q_margin_planning_point.md, thermal/reports/q_margin_turnover.md,
   docs/figures/f5_margin_waterfall.{png,pdf} — generators run, not edited.
   Phase 5-Terra (mechanical sweeps): src/cavity/mc_yield/__init__.py,
   SPEC_phase2_expanded.md (drafted hunks applied verbatim),
   docs/supervisor_onepager_2026-07.md (F5 caption sync). Sol phase manifest:
   src/cavity/thermal/detuning.py, tests/test_thermal_detuning.py,
   src/cavity/thermal/report_turnover.py, src/cavity/thermal/report_margin.py.
   All other master-manifest files are Fable-tier, touched only by Claude.
4. **Codex prohibitions** (contract text included verbatim in every Codex prompt):
   no path outside the attached manifest, no reorganisation, no convenience
   folders, no move/rename, no deletion, no unrelated cleanup, no structural
   changes, no edits to orchestration files, agent instructions, git config,
   .git, environment files, or lockfiles. Banned commands: rm, rmdir, del,
   Remove-Item, mv, Move-Item, git clean, git reset --hard, destructive git
   restore/checkout, branch switching, committing, rebasing, merging, pushing.
   Scratch: OS temp only, absolute paths, never under the repo or worktree root.
   Unlisted path/rename/deletion/structural change seemingly necessary ⇒ STOP and
   report path, operation, why, and whether the plan completes without it.
5. **Post-delegation audit** (every Codex task, in its worktree, before merge):
   `git status --short`, `git diff --name-status`, `git diff --stat`,
   `git ls-files --others --exclude-standard` — compared against the phase
   manifest; any unexpected path is a HARD STOP. Four outputs recorded verbatim in
   the phase record.
6. The contract must not suppress planned outputs: every CREATE-ONLY artifact is
   required — a phase that "safely" produces nothing has also failed.
7. **Tier split (Sol added):** Sol (gpt-5.6-sol, xhigh, --write, worktree +
   contract): the numerics implementation — detuning.py (law + q_margin_exponent),
   the new closed-form anchors in test_thermal_detuning.py, report_turnover.py,
   report_margin.py numeric restructure. The ratified derivation is the fixed
   spec — Sol implements it verbatim, no re-derivation, no improvements; if Sol's
   implementation disagrees with the ratified law at any anchor, STOP and report
   rather than fix. Terra: numeric re-pins, regeneration runs, mechanical sweeps.
   Fable (Claude, primary checkout): KAPPA_S + rung, provenance/__init__.py
   export, thermal/__init__.py entry, report_5a.py archive branch, every
   SPEC/expanded-SPEC hunk, findings note, one-pager wording, F5 caption + figure
   module edit, adversarial review of every delegated diff before merge —
   including a grep of approx( tolerances in Sol's anchors against the plan's
   exactness claims.

**Serialization:** Sol's phase merges to main BEFORE Phase 3-Terra's worktree is
created (both touch tests/test_thermal_detuning.py) and BEFORE Fable layers the
status-note wording into report_margin.py (Sol: numerics; Fable: rung/caveat/
amendment-C wording, primary checkout, post-merge). Every worktree is cut from
post-merge main. No two write-capable workers hold overlapping files at any time.

**Execution sequence:** (0) manifest verify + this plan committed → (B1) KAPPA_S +
provenance export committed (Sol's base needs it) → Sol worktree → audit →
cherry-pick → Fable layering (report_5a, f5 module + caption, report_margin
wording, thermal/__init__, A11 note assertions) → commit B2 (transiently red on
regeneration-dependent byte-pins, named) → Terra-4 (regeneration) and Terra-3
(re-pins) worktrees cut from post-B2 main, disjoint manifests, run serially →
audits → cherry-picks → full suite green in primary → commit B3 → Terra-5
worktree from post-B3 main (mechanical sweeps, Fable-drafted hunks verbatim) →
audit → cherry-pick → Fable SPEC.md hunks + findings note + names-and-claims
grep → commit C → final full suite + porcelain diff vs baseline.

Note on the two-commit split: the ratified B-group lands as B1/B2/B3 because the
filesystem contract requires every worktree to be cut from committed post-merge
main — delegated phases therefore need committed bases mid-group. Content grouping
(B: law/constant/tests/reports/figures/report_5a; C: SPEC + notes + one-pager) is
preserved. Commits by Claude in the primary checkout only, no trailers.

**Out of scope, confirmed:** Layer A; κs(ΔT) feedback implementation; any COMSOL
solve; G²-from-field-integral (Phase 1b); materials study; manuscript prose. The
findings note is drafted, never sent.
