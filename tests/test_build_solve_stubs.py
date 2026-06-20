"""SPEC §1 — `build`/`solve` modules must import without COMSOL/MPh.

Pure-Python contract: importing `cavity.forward_model.build` and
`cavity.forward_model.solve` on a host without MPh installed must
succeed. Calls into the COMSOL-touching surface raise either
`ComsolUnavailable` (when MPh is missing) or `NotImplementedError`
(when MPh is present but the stub hasn't been wired yet).

`EigenResult.q_factor` is pure Python (the §3 Q = f' / (2 f'')
definition) and is tested without COMSOL.
"""

from __future__ import annotations

import pytest

from cavity.forward_model.build import (
    ComsolUnavailable,
    build_model,
    is_comsol_available,
)
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.solve import EigenResult, solve_eigenfrequency
from cavity.forward_model.study import EigenStudyConfig


class TestIsComsolAvailable:
    def test_returns_bool_and_does_not_raise(self):
        assert isinstance(is_comsol_available(), bool)


class TestBuildModelStub:
    def test_raises_with_helpful_error(self):
        geom = CavityGeometry.from_nominal(
            DielectricShape.PUCK, dielectric_height_m=4.0e-3
        )
        with pytest.raises((ComsolUnavailable, NotImplementedError)):
            build_model(geom, MaterialSpec(), MeshConfig(), EigenStudyConfig())


class TestSolveStub:
    def test_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            solve_eigenfrequency(model=None, study=EigenStudyConfig())


class TestEigenResultQ:
    """Q = f' / (2 f'') per SPEC §3, sign-checked against SPEC §8."""

    def test_q_definition(self):
        # 1/(p_e tan_delta) at p_e = 1, tan_delta = 1.1e-4 -> Q ~ 9091.
        # f'' = f' * tan_delta / 2  =>  Q = 1/tan_delta.
        f_prime = 1.45e9
        f_double_prime = 0.5 * f_prime * 1.1e-4
        r = EigenResult(
            complex_eigenfrequency_hz=complex(f_prime, f_double_prime),
            mesh_element_count=0,
            comsol_version="stub",
        )
        assert r.q_factor == pytest.approx(1.0 / 1.1e-4, rel=1e-12)

    def test_rejects_non_positive_imag(self):
        r = EigenResult(
            complex_eigenfrequency_hz=complex(1.45e9, -1.0),
            mesh_element_count=0,
            comsol_version="stub",
        )
        with pytest.raises(ValueError, match="Im\\(f\\)"):
            _ = r.q_factor
