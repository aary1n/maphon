"""SPEC §3 typed input contract for the extraction layer.

A `FieldSample` packs everything an axisymmetric (r, z) eigenmode needs
for the §3 volume integrals: node coordinates in metres, complex SI E
and H fields, the complex relative permittivity at each node, the
dielectric domain mask, the gain-region mask (optional, defaults to the
dielectric), explicit r-z plane quadrature weights in m^2, the complex
eigenfrequency in Hz, and an optional COMSOL `emw.Qfactor` scalar for
cross-checking the primary Q.

Why explicit quadrature weights:
  SPEC §3 forbids integrating raw nodal samples — the 2*pi*r Jacobian
  and the r-z plane element area must both be accounted for. Either
  COMSOL builds the integrals on its side with `2*pi*r * <integrand>`
  operators and returns the scalars, or arrays are exported with each
  node's r-z area attached. This module is the second path: the
  primitive `axisymmetric_volume_integral` consumes (g, r, weights)
  and produces 2*pi * sum(w_i * r_i * g_i). Raw `numpy.trapz` on
  unstructured-mesh nodes is forbidden.

All coordinates are metres, all frequencies are Hz, all volumes
returned by `cavity.extraction` are m^3.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class FieldSample:
    """Cached axisymmetric eigenmode snapshot.

    Attributes:
        r_m: (N,) node radii in metres (>= 0; the axisymmetric half-plane
            lives in r >= 0).
        z_m: (N,) node axial coordinates in metres.
        e_complex: (N, 3) complex (E_r, E_phi, E_z) in V/m.
        h_complex: (N, 3) complex (H_r, H_phi, H_z) in A/m.
        eps_r_complex: (N,) relative permittivity at each node. Re part
            > 0; Im part typically -eps_r' * tan_delta inside the
            dielectric, 0 elsewhere (SPEC §2 sign convention).
        weights_m2: (N,) r-z plane quadrature weights in m^2 (> 0); the
            2*pi*r Jacobian is applied separately in the primitive.
        dielectric_mask: (N,) bool — True inside the STO domain.
        complex_eigenfrequency_hz: f' + i f''. Re must be > 0; Im is
            checked separately in `qfactor.q_from_eigenfrequency`
            against the SPEC §3 convention before any Q is trusted.
        gain_region_mask: (N,) bool — V_mode local takes its H^2
            maximum here. Defaults to `dielectric_mask`; Phase 1b
            (§5b) overrides with the pentacene crystal sub-domain.
        spacer_mask: optional (N,) bool — True inside the Wu-ring
            polystyrene seat sub-domain (2026-07-18 re-base). Audit
            trail only: no extraction primitive consumes it — p_e stays
            STO-only by definition — but the exported eps_r_complex
            carries the spacer permittivity at these nodes, so the mask
            records which nodes those are.
        q_emw_cross_check: optional COMSOL emw.Qfactor scalar from the
            same solve. Compared against f'/(2 f'') in `qfactor`;
            never used as the primary Q.
    """

    r_m: NDArray[np.floating]
    z_m: NDArray[np.floating]
    e_complex: NDArray[np.complexfloating]
    h_complex: NDArray[np.complexfloating]
    eps_r_complex: NDArray[np.complexfloating]
    weights_m2: NDArray[np.floating]
    dielectric_mask: NDArray[np.bool_]
    complex_eigenfrequency_hz: complex
    gain_region_mask: NDArray[np.bool_] | None = None
    q_emw_cross_check: float | None = None
    spacer_mask: NDArray[np.bool_] | None = None

    def __post_init__(self) -> None:
        n = self.r_m.shape[0]
        if self.r_m.ndim != 1:
            raise ValueError(f"r_m must be 1D; got shape {self.r_m.shape}")
        if self.z_m.shape != (n,):
            raise ValueError(
                f"z_m shape {self.z_m.shape} must match r_m {self.r_m.shape}"
            )
        if self.e_complex.shape != (n, 3):
            raise ValueError(
                f"e_complex shape must be ({n}, 3); got {self.e_complex.shape}"
            )
        if self.h_complex.shape != (n, 3):
            raise ValueError(
                f"h_complex shape must be ({n}, 3); got {self.h_complex.shape}"
            )
        if self.eps_r_complex.shape != (n,):
            raise ValueError(
                f"eps_r_complex shape must be ({n},); got {self.eps_r_complex.shape}"
            )
        if self.weights_m2.shape != (n,):
            raise ValueError(
                f"weights_m2 shape must be ({n},); got {self.weights_m2.shape}"
            )
        if self.dielectric_mask.shape != (n,):
            raise ValueError(
                f"dielectric_mask shape must be ({n},); got {self.dielectric_mask.shape}"
            )
        if (
            self.gain_region_mask is not None
            and self.gain_region_mask.shape != (n,)
        ):
            raise ValueError(
                f"gain_region_mask shape must be ({n},); "
                f"got {self.gain_region_mask.shape}"
            )
        if self.spacer_mask is not None:
            if self.spacer_mask.shape != (n,):
                raise ValueError(
                    f"spacer_mask shape must be ({n},); "
                    f"got {self.spacer_mask.shape}"
                )
            if np.any(self.spacer_mask & self.dielectric_mask):
                raise ValueError(
                    "spacer_mask overlaps dielectric_mask — the seat "
                    "must never enter the STO domain (p_e integrity)"
                )

        if np.any(self.r_m < 0):
            raise ValueError(
                "r_m must be non-negative (axisymmetric half-plane r >= 0)"
            )
        if np.any(self.weights_m2 <= 0):
            raise ValueError("weights_m2 must be strictly positive")
        if np.any(np.real(self.eps_r_complex) <= 0):
            raise ValueError("Re(eps_r) must be positive at every node")
        if not np.any(self.dielectric_mask):
            raise ValueError(
                "dielectric_mask is empty — p_e and V_mode local undefined"
            )
        if self.complex_eigenfrequency_hz.real <= 0:
            raise ValueError(
                f"Re(eigenfrequency) must be positive; "
                f"got {self.complex_eigenfrequency_hz.real} Hz"
            )
        if (
            self.q_emw_cross_check is not None
            and self.q_emw_cross_check <= 0
        ):
            raise ValueError(
                f"q_emw_cross_check must be positive; "
                f"got {self.q_emw_cross_check}"
            )

    @property
    def effective_gain_mask(self) -> NDArray[np.bool_]:
        """Gain-region mask, defaulting to the dielectric mask."""
        return (
            self.dielectric_mask
            if self.gain_region_mask is None
            else self.gain_region_mask
        )
