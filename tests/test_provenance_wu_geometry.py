"""Wu STO-ring build geometry (geometry re-base changeset, 2026-07-18).

Pins `provenance.GEOM_WU_STO_RING` to the literature prints re-verified
against the archived PDFs (calibration/data/raw/wu_build_papers_2026-07-18/),
and exercises the `ForkedConstant` refusal machinery that keeps the
{8.5, 8.6} mm ring-height print fork from ever being selected silently
(Q13 — SENTINEL_Q13 in cavity.sweep.dofs carries the gate side).
"""

from __future__ import annotations

import pytest

from cavity.provenance import (
    CLPS,
    CRYSTAL,
    GEOM_STD_RING,
    GEOM_WU_STO_RING,
    STO_HEIGHT_FORK,
    TOL,
    ForkedConstant,
)


# ---------------------------------------------------------------------------
# Literature pins (each value re-verified against the archived PDFs)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field, value",
    [
        ("sto_outer_radius_m", 6.0e-3),  # Wu 2020 "O.D. = 12.0 mm"
        ("sto_inner_radius_m", 2.025e-3),  # Wu 2020 "I.D. = 4.05 mm"
        ("box_inner_radius_m", 14.0e-3),  # Wu 2020 Fig. 6 caption
        ("box_internal_height_asoperated_m", 15e-3),  # Fig. 6 caption; SM ~15 mm
        ("deck_clearance_m", 3.0e-3),  # "3 mm above a copper conducting plane"
        ("piston_radius_m", 13.0e-3),  # PRL SM "26-mm dia. copper disk"
    ],
)
def test_literature_pins(field, value):
    assert getattr(GEOM_WU_STO_RING, field) == value


# ---------------------------------------------------------------------------
# The ring-height print fork (Q13): machine-readable, never coercible
# ---------------------------------------------------------------------------


def test_fork_candidates_are_8p5_and_8p6_mm():
    assert STO_HEIGHT_FORK.candidates == (8.5e-3, 8.6e-3)
    assert GEOM_WU_STO_RING.sto_height_m is STO_HEIGHT_FORK


def test_wu_height_fork_evidence_favoured_is_8p6():
    # Two independent prints (Wu 2020 text + PRL Fig. 1(c) label) against
    # the SM text's one — evidence-favoured, NOT resolved.
    assert STO_HEIGHT_FORK.evidence_favoured == 8.6e-3
    assert "Q13" in STO_HEIGHT_FORK.resolution_route


def test_forked_constant_refuses_float_coercion():
    with pytest.raises(TypeError, match="refuses silent selection"):
        float(GEOM_WU_STO_RING.sto_height_m)
    with pytest.raises(TypeError):
        GEOM_WU_STO_RING.sto_height_m * 2.0  # arithmetic fails loudly


def test_forked_constant_validates_candidates_and_sources():
    with pytest.raises(ValueError, match=">= 2 candidates"):
        ForkedConstant((1.0,), ("one",), 1.0, "Qx")
    with pytest.raises(ValueError, match="per candidate"):
        ForkedConstant((1.0, 2.0), ("one",), 1.0, "Qx")
    with pytest.raises(ValueError, match="one of the candidates"):
        ForkedConstant((1.0, 2.0), ("one", "two"), 3.0, "Qx")
    with pytest.raises(ValueError, match="resolution_route"):
        ForkedConstant((1.0, 2.0), ("one", "two"), 1.0, "")


# ---------------------------------------------------------------------------
# Spacer (Fig. 6 digitized seat) and the Wu-build crystal planning fields
# ---------------------------------------------------------------------------


def test_spacer_fields_match_fig6_digitization():
    g = GEOM_WU_STO_RING
    # Figure-derived (+/- ~0.3 mm) vector-path extraction, cyan-calibrated.
    assert g.spacer_base_inner_radius_m == 2.5e-3
    assert g.spacer_base_outer_radius_m == 8.1e-3
    assert g.spacer_base_height_m == 3.0e-3
    assert g.spacer_lip_inner_radius_m == 6.1e-3
    assert g.spacer_lip_outer_radius_m == 8.1e-3
    assert g.spacer_lip_height_m == 1.5e-3
    # The ring seats on the BASE (base height IS the deck clearance) and
    # the lip wraps OUTSIDE the ring — the seat is not a bore plug.
    assert g.spacer_base_height_m == g.deck_clearance_m
    assert g.spacer_lip_inner_radius_m >= g.sto_outer_radius_m


def test_clps_epsilon_r_pin_2p53():
    # Rexolite-class datasheet via the PRL SM's own "equivalent of
    # Rexolite" bridge; loss deliberately ungraded this pass.
    assert CLPS.epsilon_r_real == 2.53
    assert CLPS.tan_delta == 0.0


def test_crystal_planning_fields_equal_breeze_import():
    # PLANNING-ASSUMPTION with the cross-build-transfer flag (five
    # Wu-side ~4 mm bore-filling indicators in the class docstring).
    assert GEOM_WU_STO_RING.crystal_diameter_m == CRYSTAL.diameter_m == 3.0e-3
    assert GEOM_WU_STO_RING.crystal_height_m == CRYSTAL.height_m == 8.0e-3


# ---------------------------------------------------------------------------
# Standard-resonator record (2026-07-23 email archive) — record-only pins
# ---------------------------------------------------------------------------


def test_standard_resonator_record_pins():
    """GEOM_STD_RING pins the Oxborrow-WRITTEN standard-build prints
    (calibration/data/raw/oxborrow_std_resonator_2026-07-23/): a
    record-only class — NOT a modelled geometry, no crystal fields
    (the email states none; absence is part of the record) — and the
    Wu-build carried values are untouched by its existence."""
    g = GEOM_STD_RING
    assert g.sto_outer_radius_m == 6.1e-3  # "12.2 mm outer diameter"
    assert g.sto_inner_radius_m == 2.0e-3  # "4 mm inner diameter" as printed
    assert g.sto_height_m == 8.6e-3  # "8.6 mm high" (standard-build scope)
    assert g.enclosure_inner_radius_m == 14.0e-3  # "28 mm inner diameter"
    assert g.internal_height_m == 15.0e-3  # "15 mm high"
    assert g.support_clearance_m == 3.0e-3  # "(plastic) support 3 mm above"
    # Crystal ABSENT from the record, by construction.
    assert not hasattr(g, "crystal_diameter_m")
    assert not hasattr(g, "crystal_height_m")
    # Record-only guard is stated on the class itself.
    assert "NOT A MODELLED GEOMETRY" in type(g).__doc__
    # The Wu build's carried print and fork are unaffected.
    assert GEOM_WU_STO_RING.sto_outer_radius_m == 6.0e-3
    assert GEOM_WU_STO_RING.sto_height_m is STO_HEIGHT_FORK


# ---------------------------------------------------------------------------
# Gap #3 consequence: tan_delta_max re-derivation (independent arithmetic)
# ---------------------------------------------------------------------------


def test_tan_delta_max_rederivation_arithmetic():
    q_l = 3_600.0
    stated_k = 1.0  # Wu 2020: "inductive loop (coupling coefficient k = 1)"
    q_0 = q_l * (1.0 + stated_k)
    assert q_0 == 7_200.0  # PRL SM corroborates: "Q_0 ~= 2 Q_L = 7200"
    rederived_2sf = float(f"{1.0 / q_0:.1e}")  # 2-s.f. round, same convention
    assert rederived_2sf == 1.4e-4
    assert TOL.tan_delta_max == rederived_2sf

# ---------------------------------------------------------------------------
# Pump beam/prism dims (PRL SM p. 1; S-ladder amendment 1, 2026-07-19)
# ---------------------------------------------------------------------------


def test_wu_pump_beam_dims_match_prl_sm_prints():
    """WU_PUMP_BEAM pins the SM's elliptical prism cross-section: ~2 mm
    major (vertical -> the S4 band height), ~1.2 mm minor (horizontal ->
    the chord width), A_p ~ 1.9 mm^2 as printed (pi*1.0*0.6 = 1.885 mm^2
    consistency inside the tilde)."""
    from cavity.provenance import WU_PUMP_BEAM

    assert WU_PUMP_BEAM.beam_height_m == 2.0e-3
    assert WU_PUMP_BEAM.beam_width_m == 1.2e-3
    assert WU_PUMP_BEAM.beam_cross_section_m2 == 1.9e-6
    import math

    ellipse = math.pi * (WU_PUMP_BEAM.beam_height_m / 2.0) * (
        WU_PUMP_BEAM.beam_width_m / 2.0
    )
    assert abs(ellipse - WU_PUMP_BEAM.beam_cross_section_m2) < 0.02e-6
