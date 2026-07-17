"""L2 backends — mock solve fidelity to the schema/§8 conventions, and
the ComsolBackend licence gate (refusal enforced in code).
"""

from __future__ import annotations

import pytest

from cavity.forward_model.geometry import DielectricShape
from cavity.forward_model.study import WallBC
from cavity.provenance import DELOAD_K, GEOM_BOOTH_TE01D, STO
from cavity.sweep.backend import (
    MOCK_F_LEVERS_HZ,
    MOCK_Q_WALL,
    ComsolBackend,
    MockBackend,
    SWEEP_MESH_FINEST,
    SWEEP_STUDY,
    draw_solve_spec,
)
from cavity.sweep.dofs import (
    DesignMode,
    MockResolutionError,
    ResolutionContext,
    Rung,
    SentinelResolution,
    UnresolvedTodoTraceError,
    mock_resolutions,
)


def _theta(**overrides) -> dict:
    theta = {
        "box_radius_m": GEOM_BOOTH_TE01D.box_radius_m,
        "box_height_m": GEOM_BOOTH_TE01D.box_height_m,
        "torus_minor_radius_m": GEOM_BOOTH_TE01D.torus_minor_radius_m,
        "torus_major_radius_m": GEOM_BOOTH_TE01D.torus_major_radius_m,
        "epsilon_r": STO.epsilon_r_real,
        "tan_delta": STO.tan_delta,
    }
    theta.update(overrides)
    return theta


def _full_real_context() -> ResolutionContext:
    """Hypothetical REAL resolutions (test-only) to reach the backend's
    second gate; never solve-ready output."""
    return ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q2",
                payload={
                    "p_tune_nominal": 0.0,
                    "p_tune_min": -1e-3,
                    "p_tune_max": 1e-3,
                    "mechanism": "hypothetical (test only)",
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
            SentinelResolution(
                question_id="Q9",
                payload={
                    # MOCK axial-offset values (hypothetical, test only)
                    "crystal_axial_offset_nominal_m": 0.5e-3,
                    "crystal_axial_offset_band_m": (0.45e-3, 0.55e-3),
                    "centring_tolerance_m": 50e-6,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
            SentinelResolution(
                question_id="Q11",
                payload={"crystal_epsilon_r": 2.9},
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
        )
    )


# ---------------------------------------------------------------------------
# Committed sweep solve configuration (design doc §1/§6)
# ---------------------------------------------------------------------------


def test_sweep_study_matches_section_6():
    assert SWEEP_STUDY.search_hz == 1.45e9
    assert SWEEP_STUDY.n_modes == 12
    assert SWEEP_STUDY.wall_bc is WallBC.IMPEDANCE


def test_sweep_mesh_is_the_validated_finest_ladder_level():
    assert SWEEP_MESH_FINEST.dielectric_max_h_m == 1.25e-4
    assert SWEEP_MESH_FINEST.air_max_h_m == 5.0e-4


# ---------------------------------------------------------------------------
# θ → solve spec
# ---------------------------------------------------------------------------


def test_draw_solve_spec_builds_torus_geometry_and_sampled_materials():
    theta = _theta(epsilon_r=314.0, tan_delta=1.7e-4)
    spec = draw_solve_spec(theta)
    assert spec.geom.dielectric_shape is DielectricShape.TORUS
    # major radius maps onto the geometry's dielectric_radius_m.
    assert spec.geom.dielectric_radius_m == theta["torus_major_radius_m"]
    assert (
        spec.geom.dielectric_minor_radius_m
        == theta["torus_minor_radius_m"]
    )
    assert spec.materials.sto.epsilon_r_real == 314.0
    assert spec.materials.sto.tan_delta == 1.7e-4
    assert not spec.needs_phase1b_geometry


def test_draw_solve_spec_captures_phase1b_keys():
    spec = draw_solve_spec(_theta(crystal_axial_offset_m=0.5e-3, p_tune=0.4))
    assert spec.needs_phase1b_geometry
    assert set(spec.phase1b) == {"crystal_axial_offset_m", "p_tune"}


# ---------------------------------------------------------------------------
# Mock backend — convention fidelity
# ---------------------------------------------------------------------------


def test_mock_q_convention_and_loss_map():
    backend = MockBackend()
    result = backend.solve(draw_solve_spec(_theta()))
    record = result.record
    f = record.complex_eigenfrequency_hz
    # §8 convention 1: Q = f'/(2 f'') from the bare eigenfrequency.
    assert result.extraction.q == pytest.approx(
        f.real / (2.0 * f.imag), rel=1e-12
    )
    # Mock loss map is self-consistent with the EXTRACTED p_e (same §3
    # integrals): 1/Q0 = p_e·tanδ + 1/Q_wall_mock.
    p_e = result.extraction.p_e
    expected_q = 1.0 / (p_e * STO.tan_delta + 1.0 / MOCK_Q_WALL)
    assert result.extraction.q == pytest.approx(expected_q, rel=1e-9)


def test_mock_pec_variant_isolates_dielectric_loss():
    from dataclasses import replace

    backend = MockBackend()
    spec = draw_solve_spec(_theta())
    pec_spec = replace(
        spec,
        study=replace(spec.study, wall_bc=WallBC.PEC),
        materials=replace(spec.materials, wall_pec=True),
    )
    result = backend.solve(pec_spec)
    p_e = result.extraction.p_e
    assert result.extraction.q == pytest.approx(
        1.0 / (p_e * STO.tan_delta), rel=1e-9
    )


def test_mock_f_responds_to_the_minor_radius_lever():
    backend = MockBackend()
    delta = 10e-6  # 10 µm
    f0 = backend.solve(draw_solve_spec(_theta())).extraction.f_hz
    f1 = backend.solve(
        draw_solve_spec(
            _theta(
                torus_minor_radius_m=(
                    GEOM_BOOTH_TE01D.torus_minor_radius_m + delta
                )
            )
        )
    ).extraction.f_hz
    lever = MOCK_F_LEVERS_HZ["torus_minor_radius_m"]
    assert f1 - f0 == pytest.approx(lever * delta, rel=1e-9)


def test_mock_records_are_labelled_and_theta_distinct():
    backend = MockBackend()
    a = backend.solve(draw_solve_spec(_theta())).record
    b = backend.solve(
        draw_solve_spec(_theta(epsilon_r=313.0))
    ).record
    assert "MOCK" in a.comsol_version
    assert a.record_hash != b.record_hash  # εr is in the fingerprint
    assert a.field_sample.gain_region_mask is None  # honest fallback
    assert a.fingerprint["grid"] == {"n_r": 41, "n_z": 61}


# ---------------------------------------------------------------------------
# ComsolBackend — the licence gate, in code
# ---------------------------------------------------------------------------


def test_comsol_backend_refuses_construction_on_unresolved_sentinels():
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ComsolBackend(ResolutionContext(), DesignMode.BASELINE_D8)
    assert exc.value.question_ids == ("Q2", "Q9", "Q11")
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        ComsolBackend(ResolutionContext(), DesignMode.DEGRADED_D7)
    assert exc.value.question_ids == ("Q9", "Q11")


def test_comsol_backend_refuses_mock_resolutions():
    with pytest.raises(MockResolutionError):
        ComsolBackend(mock_resolutions(), DesignMode.BASELINE_D8)


def test_comsol_backend_refuses_phase1b_specs_naming_spec_5b():
    backend = ComsolBackend(_full_real_context(), DesignMode.BASELINE_D8)
    spec = draw_solve_spec(_theta(crystal_axial_offset_m=0.5e-3, p_tune=0.0))
    with pytest.raises(NotImplementedError, match="SPEC §5b"):
        backend.solve(spec)
