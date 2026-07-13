# Draft findings note — Q-margin re-derivation: the two-linewidth threshold law (for Oxborrow)

**Status: DRAFT, committed for review — NOT sent.** Reports the derived answer to the
Q-vs-margin question endorsed verbally on 2026-07-06 (SPEC §7.T4; §11 item 9). Prepared
2026-07-13 from the two-linewidth threshold pass (plan
`docs/plans/steady-crossing-linewidths.md`; turnover map
`thermal/reports/q_margin_turnover.md`).

---

Dear Mark,

The Q-vs-margin question you encouraged me to derive properly now has a derivation — and
the answer comes out with the opposite sign at our operating point, so I want to put it
in front of you before it appears anywhere as a headline.

**The derivation.** For the linearised cavity–spin two-mode system (single homogeneous
spin packet, small-signal), the oscillation threshold is the eigenvalue of the coupled
pair crossing the imaginary axis. The imaginary part forces the oscillation frequency to
the linewidth-weighted mean of the two resonances (frequency pulling — consistent with
Breeze's cavity-pulled output peak), and the real part then gives the threshold
condition

    C₀ = 1 + 4Δ²/(κc + κs)²    ⇒    Δf_max = ((κc + κs)/2)·√(C₀ − 1),

with both linewidths as FWHM and C₀ = 4G²/(κcκs) the resonant cooperativity. The
Δf_max = (κc/2)·√(C₀ − 1) I had been carrying is exactly the κs → 0 limit of this — the
cavity-Lorentzian roll-off picture is what remains when the spin line is treated as
infinitely narrow.

**Why the sign flips.** Under the same assumptions as the original napkin argument
(C₀ ∝ Q, everything else fixed), the log-derivative of Δf_max with respect to Q_L is

    E = −κc/(κc + κs) + C₀/(2(C₀ − 1)),

which reproduces the −1/2 scaling only for κc ≫ κs, reverses to +1/2 for κc ≪ κs, and
turns over near κc ≈ κs. Our operating point is on the far side of that turnover: the
own-model composed κc is ≈ 257 kHz, while the spin linewidths in Angus's table run
0.55–1.75 MHz (1.4 MHz for the 0.1% d₁₄ sample) — κc/κs ≈ 0.15–0.47. The exponent
evaluates to ≈ +0.35: **at this operating point, higher-Q builds have more thermal
frequency margin, not less.** The "higher Q ⇒ thinner margin" reading of the hypothesis
holds only in the cavity-linewidth-dominated regime, which this device is not in.

**What it does to the numbers.** At the planning point (C₀ = 190, own-model κc), the
detuning budget re-bases from Δf_max ≈ 1.77 MHz to ≈ 11.4 MHz, and the thermal budget
from ΔT_max ≈ 0.60 K to ≈ 3.9 K (spread ≈ 1.8–5.8 K across the κs band and the §6T
coefficient bands). The direction is margin-favourable — the old law was the maximally
conservative member of the family — so the "thin margin" framing softens, though the
margin is still finite and the linewidths-of-detuning observable you asked for is
untouched as the reporting unit.

**Standing of the result.** The question was yours-endorsed; the −1/√Q result was always
carried as unratified, and this is that flag doing its work. The new law is derived, not
fitted, and is pinned in CI against its closed-form limits (the old law is retained as
the κs → 0 anchor). Caveats I am carrying explicitly: κs comes from the linewidth table
in the thread (best-per-host at differing MW/laser powers — not a controlled comparison,
as flagged when it arrived), so the raw table from Angus has become genuinely
load-bearing; the threshold model maps the measured ODMR linewidth onto a single
homogeneous packet; and C₀ = 190 is still the planning import, not a measured number.

**Two asks.** (1) Does the derivation and the turnover framing get your blessing before
any of this becomes a headline — it revises the direction of a result you had endorsed
pursuing. (2) Does treating the table's ODMR linewidths as the κs in this law look right
to you, or should we press Angus for linewidths extrapolated to low MW/laser power?

Best,
Aaryan

---

## Provenance appendix (repo-internal, not part of the send)

- Derivation of record: SPEC §7.T4 (2026-07-13 block) and
  `docs/plans/steady-crossing-linewidths.md` §1; implemented in
  `cavity.thermal.detuning` (`delta_f_max_hz`, `q_margin_exponent`), anchors in
  `tests/test_thermal_detuning.py`.
- Turnover map: `thermal/reports/q_margin_turnover.md` (fixed G and κs, C₀ = c·Q_L
  calibrated at the planning point; exponent zero-crossings Q_L ≈ 63.2 and ≈ 972.5 at
  the planning calibration; large-C₀ turnover at Q_L = f/κs ≈ 1035.7).
- κs grading: `SpinResonanceLinewidth` / `KAPPA_S` in `provenance/constants.py` —
  point 1.4 MHz (0.1% d₁₄ branch choice), band [0.55, 1.75] MHz (Pc:PTP host rows
  only; picene and NAP excluded), cyclic-Hz FWHM, with the not-controlled-comparison
  and single-packet caveats.
- Re-based numbers: `thermal/reports/q_margin_planning_point.md` (Δf_max = 11.3915 MHz,
  ΔT_max = 3.8969 K at point-κs; κs band on Δf_max [5.549, 13.797] MHz; coefficient
  band [3.772, 4.819] K; outer envelope [1.837, 5.836] K).
- Rung: derivation ours (external-review argument checked independently, 2026-07-13);
  RESULT UNRATIFIED — this note is the ratification vehicle; the endorsement rung of
  the QUESTION (Oxborrow-verbal 2026-07-06) is unchanged.
- The κs(ΔT) feedback loop (thermal broadening → κs → threshold) is identified as the
  follow-on coupling and deliberately NOT implemented this pass.
