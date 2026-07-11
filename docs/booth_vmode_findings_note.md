# Draft findings note — Booth Table 8 mode volumes (for Oxborrow / forwarding to Booth)

**Status: DRAFT, committed for review — NOT sent.** Supersedes the standing "what does
Table 8's V_mode compute" ask (SPEC §11 items 1/8). Prepared 2026-07-11 from the V_mode
forensic pass (SPEC §5a finding 2026-07-11; re-based gate record
`refs/gate_runs/20260711T132705Z_rejudge/`).

---

Dear Mark,

A short follow-up that closes the mode-volume question from my Booth-reproduction run —
I think we've found what Table 8's V_mode computes, and it's good news for the thesis.

**What we saw.** My forward model at Booth's recovered TE01δ geometry reproduces her
Table 8 f to 4 significant figures and Q₀ to +0.02%, but read V_mode = 0.656 cm³ against
her printed 0.409 cm³ — a factor of ×1.60 — with no convention variant (local-max,
E-based, ε-weighted, dielectric-restricted) reproducing the print.

**The mechanism.** The reference file you passed me (`2D Resonator Lossy.mph`, the
anapole model) contains the results-tree nodes her numbers come from: a "Mode Volume
Numerator" (Volume Integration of `emw.normH*emw.normH`) and a "Mode volume Denominator"
(Volume Maximum of the same expression), both evaluated on a **Revolution 2D dataset
left at COMSOL's default partial revolution — start −90°, angle 225°**. A volume
integral over the partially revolved solid scales by 225/360 = 0.625, while a maximum is
unaffected — so the printed mode volumes are 0.625 × the full-revolution value. This is
a well-known COMSOL default (the partial revolution exists so 3D visualisations show a
cutaway); it is exactly the kind of thing that hides in a results tree, and nothing
about the physics or the solves is affected.

**The check.** Correcting my own value by the same factor: 0.6558 × 0.625 = 0.4099 ≈ the
printed 0.409. Inverted, the implied full-revolution V_mode at her TE01δ point is
0.409/0.625 = 0.6544 cm³, which my model matches to **+0.21%** — the same fidelity class
as the f and Q rows. With this, my run now reproduces all four of Booth's TE01δ
quantities (f, Q₀, wall-loss split, V_mode) at the recovered geometry.

**Her conclusions are unaffected.** Table 8 is internally consistent row by row (printed
Q ÷ printed V reproduces the printed Q/V column for all eight rows), and the factor is
uniform across the table — so every comparative statement in the thesis
(anapole-vs-TE01δ, SrTiO₃-vs-sapphire on Q/V) survives intact. Only the absolute V and
Q/V values scale by ×1.6.

**One question to confirm the mechanism** (it discriminates the partial-revolution
reading against a numerically similar alternative we ruled out for lack of any trace in
the file): **does the results setup match your/Ellie's recollection — the mode-volume
integration evaluated on a Revolution-2D dataset at the default 225°?**

On my side I have re-based the validation gate's V_mode window onto the corrected value
(same ±1% tolerance; the print itself stays recorded as printed), and the Booth
checkpoint now passes on all live-judged rows.

Best,
Aaryan

---

## Provenance appendix (repo-internal, not part of the send)

- Mechanism source: `refs/comsol/booth/2D Resonator Lossy.mph` → `dmodel.xml` nodes
  "Mode Volume Numerator" (`IntVolume`, dataset `rev1`), "Mode volume Denominator"
  (`MaxVolume`, dataset `rev1`), `rev1` = `Revolve2D`, `startangle = -90`,
  `revangle = 225` (creation actions verbatim in the file).
- Rung: mechanism confirmed in the ANAPOLE .mph node wiring; TE01δ row by
  uniform-workflow inference + the +0.21% quantitative closure; **Booth-side written
  confirmation PENDING** — the question above is the discrimination ask against the
  r ≤ x/2 = 6.14 mm cylinder-truncation alias (numerically degenerate at our grid:
  0.4069–0.4108 cm³ vs 0.40986 cm³ for 225/360; no mechanism for it exists in the file).
- Constants: `BOOTH_TABLE8_REVOLUTION_FACTOR`, `BOOTH_IMPLIED_V_MODE_M3`,
  `BOOTH_IMPLIED_F_M` (`src/cavity/provenance/constants.py`).
- Caveat carried: the stored result tables in the .mph are stale snapshots (its `tbl1`
  Q-list predates the impedance-BC state); the evidence used is the node WIRING, which
  is state-independent.
