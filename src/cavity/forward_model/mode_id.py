"""SPEC §2 mode identification — TE01delta by field pattern, never by
eigenvalue proximity.

The lossy reference spectrum has modes ~70 MHz apart near 1.45 GHz;
picking the eigenvalue closest to the search frequency is a known trap
(the nearest neighbour is routinely a TM-family mode). The filter here
is physical:

  1. Azimuthal-E dominance. For m = 0 the axisymmetric eigenproblem
     splits exactly into a TE family (E_phi, H_r, H_z) and a TM family
     (E_r, E_z, H_phi). TE01delta lives in the TE family, so the
     electric energy must sit almost entirely in E_phi.
  2. Axial H antinode on the axis. |H_z| along r = 0 must be a global-
     scale antinode (the mode's return flux threads the axis).
  3. Single axial lobe. The fundamental axial index (delta < 1) means
     H_z on the axis does not change sign; one sign flip would be a
     TE01(delta+1)-like axial overtone.

Energy fractions are proper §3 volume integrals (routed through
`axisymmetric_volume_integral`, the single Jacobian site) — not raw
nodal sums.

Selection: every candidate is scored, failures are rejected, and if no
candidate passes a `ModeIdentificationError` carries the full
diagnostic table. Proximity to the search frequency is used ONLY to
break ties among candidates that already passed the field test —
never as the primary filter.

Pure Python/numpy — synthetic-testable without COMSOL. `solve.py`
supplies the per-mode field arrays.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from cavity.extraction.quadrature import axisymmetric_volume_integral


class ModeIdentificationError(RuntimeError):
    """No eigenmode candidate passed the TE01delta field-symmetry test."""


@dataclass(frozen=True)
class TE01DeltaCriteria:
    """Thresholds for the SPEC §2 field-symmetry test.

    `min_azimuthal_e_energy_fraction`: integral |E_phi|^2 share of the
    total electric-field energy. The m = 0 family split is exact, so a
    converged TE mode sits at ~1 minus discretisation noise; 0.99
    leaves room for coarse meshes while still killing every TM-family
    candidate (whose fraction is ~0).

    `min_axis_hz_antinode_ratio`: max |H_z| on the axis over the global
    max |H_z|. TM-family modes have H_z = 0 identically; hybrid or
    higher-radial TE modes concentrate H_z off-axis.

    `max_axis_hz_sign_changes`: 0 for the fundamental axial index
    (delta < 1). Sign changes are counted on the phase-aligned real
    part of H_z along the axis, ignoring samples below
    `axis_noise_floor_fraction` of the axis maximum so numerical noise
    in near-zero tails cannot fake a lobe.
    """

    min_azimuthal_e_energy_fraction: float = 0.99
    min_axis_hz_antinode_ratio: float = 0.5
    max_axis_hz_sign_changes: int = 0
    axis_noise_floor_fraction: float = 0.1

    def __post_init__(self) -> None:
        if not 0.0 < self.min_azimuthal_e_energy_fraction <= 1.0:
            raise ValueError(
                "min_azimuthal_e_energy_fraction must be in (0, 1]"
            )
        if not 0.0 < self.min_axis_hz_antinode_ratio <= 1.0:
            raise ValueError("min_axis_hz_antinode_ratio must be in (0, 1]")
        if self.max_axis_hz_sign_changes < 0:
            raise ValueError("max_axis_hz_sign_changes must be >= 0")
        if not 0.0 < self.axis_noise_floor_fraction < 1.0:
            raise ValueError("axis_noise_floor_fraction must be in (0, 1)")


@dataclass(frozen=True)
class ModeDiagnostics:
    """Field-symmetry scores for one eigenmode candidate."""

    complex_eigenfrequency_hz: complex
    azimuthal_e_energy_fraction: float
    axis_hz_antinode_ratio: float
    axis_hz_sign_changes: int

    def passes(self, criteria: TE01DeltaCriteria) -> bool:
        return (
            self.azimuthal_e_energy_fraction
            >= criteria.min_azimuthal_e_energy_fraction
            and self.axis_hz_antinode_ratio
            >= criteria.min_axis_hz_antinode_ratio
            and self.axis_hz_sign_changes
            <= criteria.max_axis_hz_sign_changes
        )

    def summary(self) -> str:
        f = self.complex_eigenfrequency_hz
        return (
            f"f = {f.real / 1e9:.6f} + {f.imag / 1e9:.3e}i GHz | "
            f"E_phi energy fraction = "
            f"{self.azimuthal_e_energy_fraction:.4f} | "
            f"axis Hz antinode ratio = {self.axis_hz_antinode_ratio:.3f} | "
            f"axis Hz sign changes = {self.axis_hz_sign_changes}"
        )


def _axis_column_mask(r_m: NDArray[np.floating]) -> NDArray[np.bool_]:
    """Nodes on (or numerically at) the r = 0 axis column."""
    r_min = float(np.min(r_m))
    tol = 1e-9 * max(float(np.max(r_m)) - r_min, 1.0e-30)
    return r_m <= r_min + tol


def _phase_aligned_sign_changes(
    values: NDArray[np.complexfloating],
    noise_floor_fraction: float,
) -> int:
    """Sign changes of a complex profile after global phase alignment.

    A low-loss eigenvector is (to numerical precision) a real spatial
    pattern times one global complex phase. Rotating by the phase at
    the largest-magnitude sample makes the pattern real; sign changes
    of that real part, restricted to samples above the noise floor,
    count the spatial lobes.
    """
    mags = np.abs(values)
    peak = float(np.max(mags))
    if peak == 0.0:
        return 0
    anchor = values[int(np.argmax(mags))]
    aligned = np.real(values * np.exp(-1j * np.angle(anchor)))
    significant = aligned[mags > noise_floor_fraction * peak]
    if significant.size < 2:
        return 0
    signs = np.sign(significant)
    return int(np.count_nonzero(signs[1:] * signs[:-1] < 0))


def compute_mode_diagnostics(
    complex_eigenfrequency_hz: complex,
    e_complex: NDArray[np.complexfloating],
    h_complex: NDArray[np.complexfloating],
    r_m: NDArray[np.floating],
    z_m: NDArray[np.floating],
    weights_m2: NDArray[np.floating],
    *,
    axis_noise_floor_fraction: float = TE01DeltaCriteria().axis_noise_floor_fraction,
) -> ModeDiagnostics:
    """Score one candidate. Arrays follow the `FieldSample` contract:
    (N, 3) complex fields ordered (r, phi, z), (N,) coordinates and
    r-z plane weights in m^2.
    """
    if e_complex.shape != h_complex.shape or e_complex.shape[1:] != (3,):
        raise ValueError(
            "e_complex and h_complex must both be (N, 3); got "
            f"{e_complex.shape} and {h_complex.shape}"
        )

    # Vacuum-permittivity-free electric energy split: the eps_0/eps_r
    # weighting is common to all three components at every node, so it
    # cancels in the fraction and |E|^2 integrals suffice. The §3
    # primitive returns Python complex with imag exactly 0 for the real
    # |E|^2 integrand; .real loses nothing.
    energies = [
        axisymmetric_volume_integral(
            np.abs(e_complex[:, k]) ** 2, r_m, weights_m2
        ).real
        for k in range(3)
    ]
    total = sum(energies)
    if total <= 0.0:
        raise ValueError("candidate has identically zero electric field")
    e_phi_fraction = energies[1] / total

    hz = h_complex[:, 2]
    abs_hz = np.abs(hz)
    global_max = float(np.max(abs_hz))
    axis = _axis_column_mask(np.asarray(r_m))
    if not np.any(axis):
        raise ValueError("no nodes found on the r = 0 axis column")
    axis_max = float(np.max(abs_hz[axis])) if global_max > 0.0 else 0.0
    antinode_ratio = axis_max / global_max if global_max > 0.0 else 0.0

    order = np.argsort(np.asarray(z_m)[axis])
    hz_axis_sorted = hz[axis][order]
    sign_changes = _phase_aligned_sign_changes(
        hz_axis_sorted, axis_noise_floor_fraction
    )

    return ModeDiagnostics(
        complex_eigenfrequency_hz=complex_eigenfrequency_hz,
        azimuthal_e_energy_fraction=float(e_phi_fraction),
        axis_hz_antinode_ratio=float(antinode_ratio),
        axis_hz_sign_changes=sign_changes,
    )


def identify_te01delta(
    diagnostics: list[ModeDiagnostics],
    search_hz: float,
    criteria: TE01DeltaCriteria = TE01DeltaCriteria(),
) -> int:
    """Return the index of the TE01delta candidate.

    Every candidate is scored against `criteria`; the field test is the
    only filter. If several candidates pass (repeated eigenvalues,
    solver duplicates), the passing candidate whose Re(f) lies closest
    to `search_hz` is returned — proximity enters only as a tiebreak
    among field-verified candidates, per the SPEC §2 anti-trap rule.

    Raises:
        ModeIdentificationError: if no candidate passes. The message
            carries the per-candidate diagnostic table so the failure
            is debuggable from the log alone.
    """
    if not diagnostics:
        raise ModeIdentificationError(
            "no eigenmode candidates supplied to identify_te01delta"
        )
    passing = [i for i, d in enumerate(diagnostics) if d.passes(criteria)]
    if not passing:
        table = "\n".join(
            f"  [{i}] {d.summary()}" for i, d in enumerate(diagnostics)
        )
        raise ModeIdentificationError(
            "No eigenmode candidate passed the TE01delta field-symmetry "
            f"test (SPEC §2). Criteria: {criteria}. Candidates:\n{table}"
        )
    return min(
        passing,
        key=lambda i: abs(
            diagnostics[i].complex_eigenfrequency_hz.real - search_hz
        ),
    )
