"""SPEC §1/§2 contract tests on the COMSOL-touching surface — no licence.

`build`, `solve` and `runner` must import cleanly without a COMSOL
session, and everything checkable before COMSOL contact (the §4 wall-BC
consistency guard, the Q arithmetic, the float64-only evaluate
convention guard) is pinned here in the default synthetic tier.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from cavity.forward_model.build import (
    ComsolUnavailable,
    build_model,
    is_comsol_available,
    validate_wall_bc_consistency,
)
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.runner import material_spec_for
from cavity.forward_model.solve import (
    EigenResult,
    EigenSpectrum,
    _as_float64_modes,
)
from cavity.forward_model.study import EigenStudyConfig, WallBC


def _nominal_puck() -> CavityGeometry:
    return CavityGeometry.from_nominal(
        DielectricShape.PUCK, dielectric_height_m=4.92e-3
    )


class TestImportContract:
    def test_is_comsol_available_returns_bool(self):
        assert isinstance(is_comsol_available(), bool)

    def test_runner_imports_without_session(self):
        # Importing the full runner surface must not start COMSOL; the
        # import at module top already proved it, this pins the names.
        from cavity.forward_model import runner

        assert callable(runner.run_forward_model)
        assert callable(runner.run_convergence_study)
        assert callable(runner.run_wall_loss_study)


class TestWallBCConsistency:
    """The §4 decomposition dies silently if a solve is mislabelled;
    the guard must fire before any COMSOL contact."""

    def test_agreeing_impedance_passes(self):
        validate_wall_bc_consistency(
            MaterialSpec(wall_pec=False),
            EigenStudyConfig(wall_bc=WallBC.IMPEDANCE),
        )

    def test_agreeing_pec_passes(self):
        validate_wall_bc_consistency(
            MaterialSpec(wall_pec=True),
            EigenStudyConfig(wall_bc=WallBC.PEC),
        )

    @pytest.mark.parametrize(
        "wall_pec, wall_bc",
        [(True, WallBC.IMPEDANCE), (False, WallBC.PEC)],
    )
    def test_mismatch_raises(self, wall_pec, wall_bc):
        with pytest.raises(ValueError, match="wall-BC switch mismatch"):
            validate_wall_bc_consistency(
                MaterialSpec(wall_pec=wall_pec),
                EigenStudyConfig(wall_bc=wall_bc),
            )

    def test_build_model_checks_before_comsol_contact(self):
        # Raises ValueError (not ComsolUnavailable, not a COMSOL launch)
        # even on hosts where MPh is installed: the guard runs first.
        with pytest.raises(ValueError, match="wall-BC switch mismatch"):
            build_model(
                _nominal_puck(),
                MaterialSpec(wall_pec=True),
                MeshConfig(),
                EigenStudyConfig(wall_bc=WallBC.IMPEDANCE),
            )


class TestMaterialSpecFor:
    def test_derives_pec_switch_from_study(self):
        pec = material_spec_for(EigenStudyConfig(wall_bc=WallBC.PEC))
        imp = material_spec_for(EigenStudyConfig(wall_bc=WallBC.IMPEDANCE))
        assert pec.wall_pec is True
        assert imp.wall_pec is False

    def test_preserves_base_materials(self):
        base = MaterialSpec()
        derived = material_spec_for(
            EigenStudyConfig(wall_bc=WallBC.PEC), base
        )
        assert derived.sto == base.sto
        assert derived.copper == base.copper
        # And both derived variants agree with the guard:
        validate_wall_bc_consistency(
            derived, EigenStudyConfig(wall_bc=WallBC.PEC)
        )


class TestEigenResultQ:
    """Q = f' / (2 f'') per SPEC §3, sign-checked against SPEC §8."""

    def test_q_definition(self):
        # f'' = f' * tan_delta / 2  =>  Q = 1/tan_delta ~ 9091.
        f_prime = 1.45e9
        f_double_prime = 0.5 * f_prime * 1.1e-4
        r = EigenResult(
            complex_eigenfrequency_hz=complex(f_prime, f_double_prime),
            mesh_element_count=0,
            comsol_version="synthetic",
        )
        assert r.q_factor == pytest.approx(1.0 / 1.1e-4, rel=1e-12)

    def test_rejects_non_positive_imag(self):
        # Regression on the retracted imag(emw.freq)=0 probe bug (SPEC
        # §11 gap #4): a zero/negative f'' must never yield a silent Q.
        for f_im in (0.0, -1.0):
            r = EigenResult(
                complex_eigenfrequency_hz=complex(1.45e9, f_im),
                mesh_element_count=0,
                comsol_version="synthetic",
            )
            with pytest.raises(ValueError, match="Im\\(f\\)"):
                _ = r.q_factor


class TestFloat64OnlyConvention:
    """model.evaluate() returns float64 only (proven MPh convention);
    anything complex means the eval path changed and must be caught."""

    def test_accepts_float_arrays(self):
        out = _as_float64_modes(np.array([1.0, 2.0]))
        assert out.dtype == np.float64
        assert out.shape == (2,)

    def test_promotes_scalar_to_1d(self):
        out = _as_float64_modes(3.0)
        assert out.shape == (1,)

    def test_rejects_complex(self):
        with pytest.raises(TypeError, match="float64"):
            _as_float64_modes(np.array([1.0 + 1j]))


class TestEigenSpectrum:
    def test_complex_assembly(self):
        s = EigenSpectrum(
            f_real_hz=np.array([1.45e9, 1.52e9]),
            f_imag_hz=np.array([7.0e4, 7.6e4]),
        )
        assert len(s) == 2
        assert s.complex_at(1) == complex(1.52e9, 7.6e4)

    def test_rejects_mismatched_shapes(self):
        with pytest.raises(ValueError, match="must match"):
            EigenSpectrum(
                f_real_hz=np.array([1.45e9]),
                f_imag_hz=np.array([7.0e4, 7.6e4]),
            )

    def test_rejects_mismatched_q_emw(self):
        with pytest.raises(ValueError, match="q_emw"):
            EigenSpectrum(
                f_real_hz=np.array([1.45e9]),
                f_imag_hz=np.array([7.0e4]),
                q_emw=np.array([1.0e4, 1.1e4]),
            )


@pytest.mark.skipif(
    is_comsol_available(),
    reason="MPh installed on this host; the unavailable path can't fire",
)
class TestComsolUnavailablePath:
    def test_build_model_raises_comsol_unavailable(self):
        study = EigenStudyConfig(wall_bc=WallBC.IMPEDANCE)
        with pytest.raises(ComsolUnavailable, match="pip install mph"):
            build_model(
                _nominal_puck(),
                material_spec_for(study),
                MeshConfig(),
                study,
            )


class TestWallLossStudyMaterialsPropagation:
    """§5a prerequisite: a custom base MaterialSpec (e.g. the Booth
    faithful-branch tan_delta) must reach BOTH §4 arms — the
    `materials=None` placeholder in run_wall_loss_study's common dict
    is overridden per-arm via material_spec_for(study, base)."""

    def test_custom_base_materials_reach_both_arms(self, monkeypatch):
        from types import SimpleNamespace

        from cavity.forward_model import runner as runner_mod
        from cavity.provenance import BOOTH_MPH_TAN_DELTA
        from cavity.provenance.constants import STOSingleCrystal

        captured: list[tuple[WallBC, MaterialSpec]] = []

        def fake_run_convergence_study(geom, study, materials=None, **kwargs):
            captured.append((study.wall_bc, materials))
            q = 9500.0 if study.wall_bc is WallBC.PEC else 7000.0
            return SimpleNamespace(
                finest=SimpleNamespace(extraction=SimpleNamespace(q=q)),
                sigma_q=1.0,
            )

        monkeypatch.setattr(
            runner_mod, "run_convergence_study", fake_run_convergence_study
        )
        custom_sto = STOSingleCrystal(tan_delta=BOOTH_MPH_TAN_DELTA)
        result = runner_mod.run_wall_loss_study(
            _nominal_puck(),
            EigenStudyConfig(),
            materials=MaterialSpec(sto=custom_sto),
        )
        assert len(captured) == 2
        by_bc = dict(captured)
        assert by_bc[WallBC.IMPEDANCE].sto == custom_sto
        assert by_bc[WallBC.PEC].sto == custom_sto
        # each arm re-derives ONLY the wall switch
        assert by_bc[WallBC.IMPEDANCE].wall_pec is False
        assert by_bc[WallBC.PEC].wall_pec is True
        assert result.decomposition.q_total == pytest.approx(7000.0)
        assert result.decomposition.q_diel == pytest.approx(9500.0)


class TestConvergenceStudySaveMph:
    """`save_mph_dir` reaches the FINEST ladder level only (the §5a
    archive keeps one raw .mph per gated arm, not the whole ladder)."""

    def test_save_mph_dir_finest_level_only(self, monkeypatch, tmp_path):
        from types import SimpleNamespace

        from cavity.forward_model import runner as runner_mod

        # monotonically shrinking deltas so assess_convergence passes
        freqs = [
            complex(1.45e9 + 4000.0, 7.0e4 + 40.0),
            complex(1.45e9 + 1000.0, 7.0e4 + 10.0),
            complex(1.45e9, 7.0e4),
        ]
        seen_dirs: list = []

        def fake_run_forward_model(
            geom, study, materials=None, mesh_cfg=None, **kwargs
        ):
            i = len(seen_dirs)
            seen_dirs.append(kwargs.get("save_mph_dir"))
            return SimpleNamespace(
                record=SimpleNamespace(
                    complex_eigenfrequency_hz=freqs[i],
                    mesh_element_count=100 * (i + 1),
                    record_hash=f"synthetic{i}",
                ),
                extraction=None,
                from_cache=False,
            )

        monkeypatch.setattr(
            runner_mod, "run_forward_model", fake_run_forward_model
        )
        runner_mod.run_convergence_study(
            _nominal_puck(),
            EigenStudyConfig(),
            n_levels=3,
            save_mph_dir=tmp_path,
        )
        assert seen_dirs == [None, None, tmp_path]


class TestRefinementLadderConfigs:
    def test_ladder_shrinks_both_sizes(self):
        from cavity.forward_model.mesh import refinement_ladder

        base = MeshConfig(dielectric_max_h_m=4e-4, air_max_h_m=1.6e-3)
        ladder = refinement_ladder(base, n_levels=3, factor=2.0)
        assert len(ladder) == 3
        assert ladder[0] == base
        for coarse, fine in zip(ladder, ladder[1:]):
            assert fine.dielectric_max_h_m == pytest.approx(
                coarse.dielectric_max_h_m / 2.0
            )
            assert fine.air_max_h_m == pytest.approx(
                coarse.air_max_h_m / 2.0
            )
            assert fine.curved_dielectric_boundary

    def test_refined_rejects_non_refining_factor(self):
        with pytest.raises(ValueError, match="> 1"):
            MeshConfig().refined(1.0)

    def test_ladder_rejects_bad_args(self):
        from cavity.forward_model.mesh import refinement_ladder

        with pytest.raises(ValueError):
            refinement_ladder(MeshConfig(), n_levels=0)
        with pytest.raises(ValueError):
            refinement_ladder(MeshConfig(), n_levels=3, factor=0.9)
