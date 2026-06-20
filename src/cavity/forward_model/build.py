"""SPEC §2 — model assembly via MPh.

This module touches COMSOL through the MPh wrapper. MPh is lazy-imported
because SPEC §1 forbids assuming COMSOL is available in CI; importing
this module without MPh installed must not error. Calling `build_model`
without MPh raises `ComsolUnavailable` with the install hint.
"""

from __future__ import annotations

from typing import Any

from cavity.forward_model.geometry import CavityGeometry
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.study import EigenStudyConfig


class ComsolUnavailable(RuntimeError):
    """Raised when MPh/COMSOL is required but unavailable.

    SPEC §1: COMSOL is not assumed available in CI. The pure-Python
    parts of `forward_model` (geometry, materials, mesh, study) and all
    of `validation.analytic` work without it; `build_model` and
    `solve_eigenfrequency` do not.
    """


def is_comsol_available() -> bool:
    """True if MPh imports cleanly. Does not start a COMSOL session."""
    try:
        import mph  # noqa: F401
    except ImportError:
        return False
    return True


def _require_mph() -> Any:
    try:
        import mph
    except ImportError as exc:  # pragma: no cover -- exercised on COMSOL-less hosts
        raise ComsolUnavailable(
            "MPh is required for COMSOL model assembly. "
            "Install with: pip install mph"
        ) from exc
    return mph


def build_model(
    geom: CavityGeometry,
    materials: MaterialSpec,
    mesh_cfg: MeshConfig,
    study: EigenStudyConfig,
) -> Any:
    """Assemble the §2 axisymmetric model via MPh and return a model handle.

    Stub. The full implementation lands once the analytic benchmark
    (SPEC §8) has anchored the convention and the supervisor's `.mph`
    can be diffed against it.
    """
    _require_mph()
    raise NotImplementedError(
        "build_model is not yet implemented; SPEC §2 specifies the model "
        "(axisymmetric m = 0, IBC/PEC walls per study.wall_bc, complex "
        "eps_r STO via materials.sto_complex_eps_r)."
    )
