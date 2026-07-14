"""Layer B calibration against the Cowley-Semple CW-ODMR dataset (observable-a).

Plan of record: docs/plans/layer_b_calibration_plan.md (ratified 2026-07-14).
SPEC anchors: §7.T5 (calibration observable (a)), §6T (graded coefficients).

PROVENANCE BOUNDARY (load-bearing). The calibration rig — PCB stripline,
crystal–rubber-cement–glass–HASL/Cu–FR-4 stack, enclosed ambient — is NOT
the maser cavity. Its thermal parameters do not transfer. Everything in
this workstream lives in this package; the dependency direction is one-way:

    calibration  →  cavity      (import shared thermal machinery: ALLOWED)
    cavity       →  calibration (FORBIDDEN — enforced by
                                 tests/test_calibration_import_boundary.py)

Calibration constants live in `calibration.constants`, graded exactly like
`cavity.provenance.constants`, every entry marked NON-TRANSFERABLE to the
cavity model. Nothing here may be added to `cavity/provenance/constants.py`.

`calibration/data/raw/` is read-only forever: every file is pinned in
MANIFEST.sha256 and re-verified in CI on every test run
(`calibration.integrity`; tests/test_calibration_integrity.py).
"""
