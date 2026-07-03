# SPEC changeset — Bayliss resolution (2026-07-02)

**Apply against current repo state.** Hunks are keyed to section anchors, not line numbers. If a hunk is already applied (repo may be ahead of the uploaded copies), skip it. Where wording differs from repo, the *distinctions* below win; the prose may be adapted.

**Trigger:** Oxborrow forwarded the "linewidths" thread (2026-06-26, Glasgow/MIT/Imperial). §11.1 — the top open action — is resolved. The dataset also breaks one structural assumption (§7.2, hunk 5): the calibration observable is the **spin** resonance, not the cavity mode.

---

## Hunk 0 — Global rename + attribution convention

Everywhere: **"Baylis" → "Bayliss"**. Add once (convention block or §11.1):

> **Attribution convention.** "Bayliss" = Prof. Sam Bayliss, University of Glasgow (PI, QOS group) — the *group* the phenomenon lives in, not the measurer. The measurements are **Angus Cowley-Semple's** (PGR, Bayliss group). Refer to the calibration data as the **Cowley-Semple ODMR dataset**; "Bayliss-calibrated" as shorthand is acceptable but the byline is Cowley-Semple's. Context: shared in the "linewidths" thread (2026-06-26) for the host–guest paper with Max Attwood (MIT) and Ziqiu Huang (Imperial); Sarah Mann and Oxborrow cc'd.

---

## Hunk 1 — SPEC.md revision-note priority order

REPLACE the line "**Priority order:** (1) Baylis — who, does the frequency-shift data exist, is it accessible (§11.1); …" WITH:

> **Priority order:** (1) ~~Baylis identity/data~~ **RESOLVED 2026-07-02** — dataset identified and partially in hand (§11.1); remaining asks are calibration metadata, not existence; (2) build Phase 2 aimed at reproducing it; (3) Phase 3 on top. **If the 8-week clock squeezes, Phase 2 wins; Phase 3 tiers shrink first.**

ADD a rung to the **endorsement ladder** (do not merge into existing rungs):

> - **Oxborrow, independently on record (in-thread, 2026-06-26):** applied Lang 2007's ~−0.05 MHz/K to Cowley-Semple's shifts and inferred pump heating of "several tens of Celsius." The *mechanism inference* (shift = heating) is therefore his, publicly, in the collaboration. The *calibration-target plan* (Phase 2 reproduces this dataset quantitatively) remains **ours-communicated, unratified** — do not conflate the two.

---

## Hunk 2 — SPEC.md §11.1 (replace wholesale)

> **1. Cowley-Semple ODMR dataset — RESOLVED (identity + existence), metadata pending.**
> What exists (from the 2026-06-26 thread):
> - **Primary series (0.1% Pc-d₁₄:PTP-d₁₄):** CW-ODMR X–Z resonance vs laser drive current, same setup throughout: **1449.7 MHz @ 50 mA · 1449.4 @ 60 · 1449.1 @ 80 · 1448.6 @ 100** → LSQ slope **−21 kHz/mA**. Points scraped from thread figures — obtain raw.
> - **Control series (0.01% Pc-d₁₄:PTP-d₁₄):** same setup, visibly less sensitive (peak near-stationary 60–100 mA). Treat as an upper bound on its dν/dI until raw data lands.
> - **Linewidth table (feeds C-variance, not the thermal calibration):** 1.75 MHz (0.1% Pc:PTP) · 1.4 MHz (0.1% d₁₄) · **0.55 MHz (0.01% d₁₄)** · 7 MHz (picene) · 1.8 MHz (NAP). Best-per-host at differing MW/laser powers — not a controlled comparison; note it.
> - **ΔT inference (Oxborrow's, in-thread):** with dν/dT ≈ −0.05 MHz/K, the −21 kHz/mA slope ⇒ ~0.4 K/mA ⇒ **~13–30 K steady-state heating at 100 mA** across the coefficient spread (hunk 3) and plausible diode thresholds. "Several tens of Celsius."
> Remaining asks (via Oxborrow — request he loop us in with Angus directly):
> - **Raw ν(I)** for both concentrations (not scraped points), + uncertainties.
> - **Laser calibration:** wavelength; threshold current; slope efficiency (W/A) or measured power at each current. *Without this, absolute ΔT(P) is uncalibrated; the ν(I) slope and the concentration ratio still are.*
> - **Optical geometry:** spot size at sample (lens known: Thorlabs AC254-030-AB, f = 30 mm; NAP sample used C240TMD-B, f = 8 mm — different spot, do not pool).
> - **Sample:** crystal dimensions, mounting/substrate, ambient conditions.
> - **Any time-resolved traces** (shift vs time after laser on/off). Existence unknown; decides whether §7.4 check 3c is live.
> Sets (i) Phase 2's claim level (§7.4.3) and (ii) the §7.2 calibration model boundary — which is now **crystal + mount in the Glasgow ODMR rig**, not crystal→STO (hunk 5).

---

## Hunk 3 — SPEC.md §6T (targeted edits)

**df_spin/dT** — REPLACE the "confirm sign and magnitude" line WITH:

> - **df_spin/dT — pinned, with a spread to carry:** negative. **Lang, Sloop & Lin 2007 (JPCA 111, 4731) Fig. 4 — now in refs** (provenance doc "must-obtain" #5, obtained): X–Z transition, ~**−70 kHz/K** average over 230–296 K, **nonlinear** (steepens toward the 193 K transition) → fit *locally* around operating T, do not adopt a single global number. Spread across sources: Oxborrow in-thread quotes **−50 kHz/K** (RT); **W20 prints −80 kHz/K citing the same Fig. 4** — a ±40% spread on one curve depending on where it is read. Carry as the coefficient prior in §12.6 channel 3. Second primary to pull: **Nat. Commun. 2025, doi 10.1038/s41467-025-65508-2** (triplet-ODMR T & P sensing; Angus's in-thread reference — modern, error-barred). Magnitude check vs the cavity arm stands: |df_spin/dT| ~ 50–80 kHz/K ≪ df_cavity/dT ~ +2.6 MHz/K; **note opposite signs — the differential adds.**

**c_p** — REPLACE the Chang sentence WITH:

> - **c_p — primary in hand: Chang 1983** (adiabatic calorimetry). C_p = **0.94·T J K⁻¹ mol⁻¹ (200–480 K)** ⇒ c_p(300 K) ≈ **1225 J kg⁻¹ K⁻¹** (M = 230.29 g mol⁻¹). λ-transition peak **193.55 K** = hard low-T validity bound for the linear form (operating point is safely above; state it once). Note c_p is **not constrained by the calibration dataset** (hunk 6) — it enters transients only; Chang carries it alone.

**k** — ADD after the "k and ρ open" sentence:

> - **k — provenance floor found: Hedley, Milnes & Yanko 1970** (JCED 15, 122; in refs): ***liquid*** p-terphenyl k ≈ **0.134–0.136 W m⁻¹ K⁻¹ at 213–254 °C**. The unreferenced ~0.1 W m⁻¹ K⁻¹ crystal figure (Breeze-2018 lineage) coincides suspiciously with the liquid value — plausible provenance origin. Crystals conduct better than their melts ⇒ treat **0.1 as a floor**, keep the 0.1–1 band and ~2× anisotropy. **k is the parameter the CW calibration actually constrains** (steady-state ΔT ∝ 1/k for conduction-dominated transport) — the open literature gap and the new data point at the same quantity. (Stretch framing, do not headline unlabelled: with laser power + spot size calibrated, the fit is an effective-k constraint on doped p-terphenyl via triplet thermometry.)

**Dataset line** — REPLACE "Baylis dataset (calibration data to acquire, §11.1)" WITH:

> - **Cowley-Semple ODMR dataset (calibration target; status + asks in §11.1).** Observable: **spin** resonance vs laser current, steady-state CW, Glasgow rig (no STO, no cavity). Source-term corollary now empirically supported: 0.1% shifts ≫ 0.01% at identical power ⇒ **q̇ ∝ [Pc]·I_pump** (absorption in the pentacene, not host background).

---

## Hunk 4 — SPEC.md §7 deliverable-status paragraph

REPLACE "(Baylis's illumination-induced frequency shifts, never thermally modelled)" WITH:

> (the **Cowley-Semple ODMR shifts** — quantified ν_spin(I_laser), Bayliss group, Glasgow, 2026-06 thread — never thermally modelled; Oxborrow's in-thread inversion is a one-line coefficient division, not a transport model)

---

## Hunk 5 — SPEC.md §7.2 (the structural fix — replace the first bullet and the model-boundary bullet)

> - **Two observables; do not conflate (supersedes "Phase 2's Δf observable is cavity-dominated"):**
>   **(a) Calibration observable — spin, Glasgow geometry.** The Cowley-Semple measurement is the **spin transition** via ODMR in a rig containing **no STO and no cavity**. Chain: pump → crystal ΔT(r,z) → ν_spin shift via df_spin/dT (§6T), ΔT weighted over the optically probed volume (≈ the illuminated spot; excitation/collection co-located). **No cavity path, no STO, no mode weighting enters the calibration.** This isolates exactly the "how hot does the layer get" question, with the triplet as in-situ thermometer.
>   **(b) Prediction observable — cavity-dominated, our geometry.** In the maser, the *device-relevant* frequency response is the differential detuning: cavity arm (+2.6 MHz/K via STO εr(T), E-energy-weighted over the STO) vs spin arm (−50…−80 kHz/K, gain-region-H-weighted). The cavity arm dominates the *magnitude* — and remains **model-only**: nothing in the thread observes it. State this as the asymmetry it is: spin arm calibrated, cavity arm predicted.
> - **Model-boundary decision (recast):** the *calibration* model boundary is **crystal + mount in the ODMR rig** — the crystal→STO thermal-path extension (conduction through mount/air gap, radiation) is **not** needed to reproduce the Glasgow data. It **is** needed for the maser-geometry prediction (observable b) and for Phase 3's coefficients. Sequence accordingly: calibrate (a) first, then transfer the validated transport core to geometry (b). **ΔT numbers do not transfer between geometries; the transport model and dν/dT do.**
> - **Regime note:** the Glasgow data is **steady-state CW** — exactly the regime of the collaboration's cw-cooperativity projections (Ziqiu's final figure), and distinct from the pulsed-Xe Breeze/Booth transients. Both regimes stay in scope (§7.1 time resolution unchanged); the calibration lands in CW.

---

## Hunk 6 — SPEC.md §7.3 output 2 + §7.4 check 3

§7.3 output 2, REPLACE WITH:

> 2. **Predicted steady-state ν_spin(I_laser)** under Cowley-Semple's conditions, both concentrations — the validation observable. (Predicted Δf_cavity(t) for our device is an output of observable-b transfer, not of calibration.)

§7.4 check 3, REPLACE WITH:

> 3. **Primary, data now in hand at scraped-points level: reproduce Cowley-Semple.** Sub-checks, in order of what they test:
>    **(3a) Slope magnitude** — predicted dν/dI for the 0.1% sample within the df_spin/dT spread band (§6T), given calibrated laser power + spot size. Tests **k and the BCs**. *Constraint honesty:* steady-state points constrain k and boundary coefficients; they do **not** constrain ρc_p (Chang carries c_p independently) — say so in the paper; a matched slope is not a validated transient model.
>    **(3b) Concentration scaling** — ratio of 0.1% to 0.01% sensitivities. Same setup, same currents ⇒ **laser-power calibration cancels**; tests the q̇ ∝ [Pc] absorption model nearly free of the largest metadata uncertainty. The strongest cheap check in the project — do not skip it.
>    **(3c) Timescale — conditional:** only if time-resolved traces exist (§11.1 ask). If they do, they are the sole probe of α = k/ρc_p and promote the transient model from analytic-check-validated to data-validated.
>    **Claim levels (restated):** 3a+3b met → *"explains observed, previously unmodelled behaviour"* (strong). Without → checks 1–2 only, claim softens per the existing wording. **Timescale language is now conditional on 3c — remove "magnitude and timescale" as a blanket requirement.**

---

## Hunk 7 — SPEC.md §11.10 (awaiting-Oxborrow bundle) — amend the nobody-else check

> - **Nobody-else check — partially informed by the thread, still confirm explicitly:** in-thread, Angus *measures* (no transport model), Oxborrow *inverts a coefficient* (no transport model), **Ziqiu Huang (Imperial) simulates cw maser cooperativity from linewidths** for the host–guest paper — no thermal content visible, but this is the nearest active workstream to Phase 3's composition. Ask Oxborrow directly: does Ziqiu's simulation include any pump-heating/detuning term, and is anyone modelling heat transport in the gain medium. Also request the Angus introduction (§11.1 asks).

ADD to §11 as a new numbered item:

> - **Pull Nat. Commun. 2025 (doi 10.1038/s41467-025-65508-2)** — modern df_spin/dT primary with pressure dependence; supersedes single-point readings of Lang Fig. 4 for the local coefficient fit.

---

## Hunk 8 — SPEC_phase2_expanded.md (Phase 3 doc)

- §12.0 / §12.2 / §12.6: rename per hunk 0 ("Bayliss-calibrated"; channel-3 empirical route = "propagate Cowley-Semple calibration residuals").
- §12.6 channel 3: the calibrated branch is now the **likely** branch, not hypothetical — but its width is set by the coefficient spread (−50…−80 kHz/K) and the laser-power metadata; both propagate. The literature-prior envelope survives as the fallback *and* as the prior on df_spin/dT even in the calibrated branch.
- §12.8 framing guards, REPLACE "**Do not claim Baylis data was promised** — the phenomenon was raised; the data's existence/accessibility is an open ask" WITH:
> - **Data status guard (updated):** the dataset exists and has been shared *within the host–guest collaboration thread* — it was not produced for, or promised to, this project. Access to raw points + metadata is a live ask via Oxborrow (§11.1). Do not present it as this project's measurement; byline Cowley-Semple, Bayliss group. If used in the manuscript, co-authorship/acknowledgement is a conversation for Oxborrow to broker — flag early, not at submission.

---

## Distinctions this changeset must not lose (checklist for the applying agent)

1. Spin arm calibrated; cavity arm predicted. Never write "Bayliss data validates the cavity shift."
2. ΔT is geometry-specific; dν/dT and the transport model transfer; the 25 K number does not.
3. Coefficient spread −50/−70/−80 kHz/K traces to *readings of one nonlinear curve* (Lang Fig. 4); fit locally, carry the spread.
4. Steady-state CW constrains k + BCs, not ρc_p; c_p is Chang's alone.
5. Concentration-ratio check (3b) is power-calibration-independent; slope check (3a) is not.
6. Oxborrow's in-thread inversion = mechanism engagement on record ≠ ratification of the calibration-target plan.
7. Bayliss = PI/group; Cowley-Semple = measurer. Hedley 1970 k is **liquid**-phase — a floor, not a crystal value.
