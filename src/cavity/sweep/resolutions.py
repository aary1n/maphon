"""Ratified sentinel resolutions — the non-mock register.

Strictly separate from `mock_resolutions()` (dofs.py): every entry
here is a RATIFIED answer on the record, carried at its stated rung
and entering the machinery through `SentinelResolution` — the only
path. Q2/Q9 land here when they resolve. The context this module
builds is PARTIAL by construction (Q11 only, as of 2026-07-17):
Q2/Q9 remain unresolved, so every solve-ready exit still refuses.

2026-07-21 continuation: Q13 and Q2 landed — both in-person caliper
measurements made live during the 2026-07-21 meeting, witnessed
first-hand by the repo author (provenance corrected 2026-07-22 —
docs/commit_errata_2026-07-22.md; the initial mint under-graded them
as verbally-reported); contemporaneous notes + photos archived at
calibration/data/raw/oxborrow_meeting_notes_2026-07-21/; written
confirmation pending — rides the confirmation email. The register
now holds Q2 + Q11 + Q13 in question order; the context remains
PARTIAL by construction — Q9 is unresolved, so every solve-ready
exit still refuses, now naming Q9 alone.
"""

from __future__ import annotations

from cavity.sweep.dofs import ResolutionContext, Rung, SentinelResolution

RESOLUTION_Q2 = SentinelResolution(
    question_id="Q2",
    payload={
        "p_tune_nominal": 15e-3,
        "p_tune_min": 15e-3,
        "p_tune_max": 25e-3,
        "mechanism": (
            "box internal height / piston position on the brass screw "
            "(Wu 2020 screw-suspended ceiling; PRL SM 26-mm piston); "
            "travel band [15, 25] mm measured in person, live during "
            "the 2026-07-21 meeting, witnessed first-hand (provenance "
            "corrected 2026-07-22), notes archived at "
            "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/; "
            "nominal = the recorded as-operated 15 mm = "
            "GEOM_WU_STO_RING.box_internal_height_asoperated_m, "
            "sitting AT the band's lower edge (accepted: no validator "
            "requires strict interiority — checked 2026-07-22). "
            "RIDER STILL OPEN: the piston-step annular-gap DEPTH "
            "(optional piston_gap_depth_m payload key) was NOT "
            "obtained 2026-07-21 — still an ask, does not block this "
            "resolution."
        ),
    },
    rung=Rung.SUPERVISOR_CONFIRMED,
    mock=False,
    provenance=(
        "Travel band [15, 25] mm — IN-PERSON CALIPER MEASUREMENT "
        "during the 2026-07-21 meeting, performed/witnessed "
        "first-hand by the repo author (provenance corrected "
        "2026-07-22, docs/commit_errata_2026-07-22.md — the initial "
        "mint under-graded this as a verbal report; contemporaneous "
        "notes + photos archived at "
        "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/; "
        "written confirmation pending — rides the confirmation "
        "email). Single readings: NO measurement band on the "
        "endpoints (no repeats, no stated caliper placement) — the "
        "caliper-band ask stays open. "
        "Answers the 2026-07-18 travel-band email in person. "
        "Consistency (informational): as-operated 15 mm = lower "
        "edge; the 2026-07-17 emailed cavity height 18 mm "
        "(calibration/data/raw/oxborrow_sto_2026-07-17/"
        "stogeometry.md) sits interior; ring 8.6 mm + 3 mm deck = "
        "11.6 mm occupied, so the band implies ceiling-to-STO "
        "clearance 3.4-13.4 mm, bracketing the stated 5-10 mm "
        "typical plate-to-STO operating separation (same archive, "
        "and oxborrow_tuning_2026-07-16/stotuningmech.md)."
    ),
)

RESOLUTION_Q11 = SentinelResolution(
    question_id="Q11",
    payload={
        "crystal_epsilon_r": 3.0,
        # Nothing consumes the band yet: it rides as an extra key
        # (the validator permits extras) — machine-readable
        # uncertainty metadata for a future Phase 1b eps_r
        # sensitivity check, mirroring Q9's band-carrying pattern.
        "crystal_epsilon_r_band": (2.4, 4.1),
    },
    rung=Rung.PLANNING_ASSUMPTION,
    mock=False,
    provenance=(
        "(i) point 3.0 = round central planning value (band mid 3.25; "
        "anthracene isotropic mean 3.13); band [2.4, 4.1] = principal "
        "optical permittivities of crystalline anthracene, eps_xx 2.42 "
        "/ eps_yy 2.90 / eps_zz 4.07 (±0.05), Cummins & Dunmur 1974, "
        "J. Phys. D: Appl. Phys. 7, 451 (Zotero WNLM2C8X), immersion "
        "method — refractive-index-derived, i.e. OPTICAL-frequency "
        "values. (ii) Three-layer inference chain, each layer "
        "planning-tier: chemical-class analogy anthracene -> "
        "p-terphenyl; optical -> static/microwave extrapolation, "
        "justified only by both crystals being nonpolar rigid "
        "aromatics (no orientational/Debye contribution expected "
        "between optical and microwave); consequence of either layer "
        "failing bounded by Breeze 2017 <1% electric filling. "
        "(iii) Consistency: below CRYSTAL.epsilon_r_upper_bound "
        "(Breeze 'eps_r < 5') by construction. (iv) Negative space: "
        "direct p-terphenyl static/microwave permittivity NOT FOUND, "
        "literature trace 2026-07-17; Selvakumar et al. 2014 (J. Mol. "
        "Struct. 1056-1057, 152, Zotero KCDCRN4C) examined and "
        "REJECTED — eps_r 5760 @ 1 kHz is electrode/Maxwell-Wagner "
        "polarization per the paper's own attribution, unusable at "
        "any grade."
    ),
)

RESOLUTION_Q13 = SentinelResolution(
    question_id="Q13",
    payload={
        "sto_height_m": 8.6e-3,
        "selection_evidence": (
            "CALIPER, IN PERSON: the ring height was caliper-measured "
            "live, in situ during the 2026-07-21 meeting — a "
            "first-hand measurement performed/witnessed by the repo "
            "author (provenance corrected 2026-07-22; the initial "
            "mint under-graded this as a verbal report), 8.6 mm; "
            "contemporaneous notes + photos archived at "
            "calibration/data/raw/oxborrow_meeting_notes_2026-07-21/. "
            "This is the fork's named caliper route. 8.6 was already "
            "the evidence-favoured branch (two prints vs one); the "
            "measurement decides it. NO measured band was obtained "
            "(single reading, no repeats, no stated caliper "
            "placement): no sto_height_band_m key rides this payload, "
            "so the +/-25 um TOL.machining_tol_m placeholder "
            "materialises in design.materialise_dims — stated here, "
            "not implicit."
        ),
    },
    rung=Rung.SUPERVISOR_CONFIRMED,
    mock=False,
    provenance=(
        "In-person caliper measurement during the 2026-07-21 "
        "meeting, performed/witnessed first-hand by the repo author "
        "— measured live, in situ, same session as the archived "
        "contemporaneous notes and the four crystal-placement photos "
        "(calibration/data/raw/oxborrow_meeting_notes_2026-07-21/); "
        "NOT a verbal report of a measurement made elsewhere "
        "(provenance corrected 2026-07-22 — "
        "docs/commit_errata_2026-07-22.md; the initial mint "
        "under-graded this). Written confirmation from Oxborrow "
        "pending — rides the confirmation email. NO measurement "
        "band: single reading, no repeats, no stated caliper "
        "placement — the caliper-band ask stays open and the "
        "+/-25 um placeholder applies (see the payload). The verbal "
        "grade stays on the identity claim only: that the measured "
        "ring IS the Wu 2020 build's ring is Oxborrow's verbal "
        "assertion, not independently verified — graded separately "
        "from the measurement provenance. Collapses the "
        "{8.5, 8.6} mm print fork "
        "(provenance.STO_HEIGHT_FORK / SENTINEL_Q13) to 8.6 mm via "
        "the fork's caliper resolution route; the SM 8.5 print is "
        "superseded by the in-person caliper measurement (written "
        "confirmation pending), preserved as printed on the fork "
        "record. The fork object is NOT deleted — it remains the "
        "record; this resolution is the machinery's only entry path "
        "for the number."
    ),
)

#: Every ratified resolution on record, in question order.
RATIFIED_RESOLUTIONS: tuple[SentinelResolution, ...] = (
    RESOLUTION_Q2,
    RESOLUTION_Q11,
    RESOLUTION_Q13,
)


def ratified_resolutions() -> ResolutionContext:
    """Every ratified (non-mock) resolution on record — Q11 only as
    of 2026-07-17; Q2 + Q13 joined 2026-07-21 (first-hand in-person
    caliper measurements — provenance corrected 2026-07-22; written
    confirmation pending). PARTIAL by construction: Q9
    remains unresolved, so every solve-ready exit still refuses,
    naming Q9 alone."""
    return ResolutionContext(resolutions=RATIFIED_RESOLUTIONS)
