# Interpretation addendum — CPW via-contact caveat (2026-07-16, Oxborrow-verbal)

**Applies to:** `ratio_test_digitized.md` (T4 ratio discrimination test, digitized grade) and
the verdict context carried into `observable_a_feed.json`. **The verdict and its claim level
are UNCHANGED:** GEOMETRY-SUFFICIENT under the pre-fixed three-way criterion; discriminating
power LOW (the model band [0.584, 2.329] brackets the measured ratio from both sides); an
intrinsic deuteration effect is NOT REQUIRED and NOT EXCLUDED by this dataset. This addendum
adds interpretation only; no number in the report is re-derived or re-judged.

**The verbal record — Oxborrow (in person, 2026-07-16):** heat extraction on the coplanar
waveguide depends on whether the sample spans onto via'd copper regions of the board — a
narrower sample that does not reach the vias runs hotter; orientation of the sample on the CPW
also matters.

**Interpretation:** this adds a second geometry-dependent heat-sinking mechanism and further
weakens any deuteration-only attribution. It is consistent with the existing
geometry-sufficient verdict but is not quantified by the present ratio test and does not
increase that test's numerical discriminating power. It sits alongside the report's existing
"Residual confound: per-sample glue contact (does NOT cancel)" section — like the per-sample
glue-contact φ, via-contact coverage is a per-sample contact pathway the ratio test cannot
exclude, and it is directly relevant to that line of interpretation (the d14 vs h14 samples
may simply couple to the board differently through size/placement, independent of any
intrinsic isotope effect).

**Record homes:** this file (beside the T4 report) and the `calibration/rig_model.py` module
docstring. If the T4 report is ever regenerated, fold this caveat into its generator rather
than editing the dated report in place.
