"""SPEC §2 + §4 — eigenstudy config + wall-BC switch + mesh validation."""

from __future__ import annotations

import pytest

from cavity.forward_model import (
    ConvergenceCriterion,
    EigenStudyConfig,
    MeshConfig,
    WallBC,
)
from cavity.provenance import TARGET


class TestEigenStudyConfig:
    def test_default_is_impedance_at_design_frequency(self):
        cfg = EigenStudyConfig()
        assert cfg.wall_bc is WallBC.IMPEDANCE
        assert cfg.search_hz == pytest.approx(TARGET.f_design_hz)
        assert cfg.n_modes >= 1

    def test_pec_variant_only_changes_wall_bc(self):
        ibc = EigenStudyConfig()
        pec = EigenStudyConfig(wall_bc=WallBC.PEC)
        assert pec.search_hz == ibc.search_hz
        assert pec.n_modes == ibc.n_modes
        assert pec.target == ibc.target
        assert pec.wall_bc is WallBC.PEC

    @pytest.mark.parametrize("f", [0.0, -1.0e9])
    def test_rejects_non_positive_search_hz(self, f):
        with pytest.raises(ValueError, match="search_hz"):
            EigenStudyConfig(search_hz=f)

    @pytest.mark.parametrize("n", [0, -1])
    def test_rejects_bad_n_modes(self, n):
        with pytest.raises(ValueError, match="n_modes"):
            EigenStudyConfig(n_modes=n)


class TestMeshConfig:
    def test_curved_dielectric_boundary_default_true(self):
        cfg = MeshConfig()
        assert cfg.curved_dielectric_boundary is True

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"dielectric_max_h_m": 0.0},
            {"dielectric_max_h_m": -1.0e-4},
            {"air_max_h_m": 0.0},
            {"air_max_h_m": -1.0e-4},
        ],
    )
    def test_rejects_non_positive_element_size(self, kwargs):
        with pytest.raises(ValueError, match="mesh element sizes"):
            MeshConfig(**kwargs)


class TestConvergenceCriterion:
    def test_defaults_match_spec_targets(self):
        crit = ConvergenceCriterion()
        # SPEC §5: f to >=4 s.f. (Booth localises to 5 s.f.).
        assert crit.f_sig_figs >= 4
        # Q to ~3 s.f. (mesh-limited; Booth quotes 6,980 = 4 s.f. nominal).
        assert crit.q_sig_figs >= 3
        assert crit.max_refinements >= 1

    @pytest.mark.parametrize(
        "kwargs,match",
        [
            ({"f_sig_figs": 0}, "significant-figure"),
            ({"q_sig_figs": 0}, "significant-figure"),
            ({"max_refinements": 0}, "max_refinements"),
        ],
    )
    def test_rejects_bad_inputs(self, kwargs, match):
        with pytest.raises(ValueError, match=match):
            ConvergenceCriterion(**kwargs)
