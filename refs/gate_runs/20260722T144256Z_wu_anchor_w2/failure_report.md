# W2 FAILURE — Run A ladder (2026-07-22)

**STOP condition (pre-registered): the mesh ladder is not in the asymptotic regime or the TE01delta mode could not be identified — no sigma fabricated, no window judged on unconverged numbers.**

Exception:

```
mesh sequence is not in the asymptotic regime — refusing to emit sigma (SPEC §2). f'' deltas not monotonically shrinking: (1.0928563246998237, 1.553170241342741, 0.5952060727286153, 0.20615832769544795). Eigenfrequencies (coarse->fine): ((1431201825.5559864+100057.70191106109j), (1431197455.847858+100056.60905473639j), (1431194224.703712+100055.05588449504j), (1431192653.2552023+100054.46067842231j), (1431191994.3443084+100054.25452009462j)). Refine further or inspect mode identification per level.
```

All solve records produced so far are under `solves/` in this directory for diagnosis. No anchor record is minted; the failure-triage ladder of docs/plans/oxborrow_reply_ingestion_and_wu_anchor.md §4.4 governs.
