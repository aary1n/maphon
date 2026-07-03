"""SPEC §2 mode-identification tests — field pattern beats proximity.

The load-bearing regression here is the proximity trap: the lossy
reference spectrum has modes ~70 MHz apart near 1.45 GHz and the
eigenvalue nearest the search frequency is routinely a TM-family mode.
`identify_te01delta` must pick the field-verified TE candidate even
when a TM candidate sits closer to the search frequency, and the test
asserts explicitly that naive nearest-eigenvalue picking would have
chosen the wrong mode.

Synthetic m = 0 candidates are built from the exact family split:
TE (E_phi, H_r, H_z) vs TM (E_r, E_z, H_phi).
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.forward_model.gridding import StructuredGrid, structured_grid
from cavity.forward_model.mode_id import (
    ModeDiagnostics,
    ModeIdentificationError,
    TE01DeltaCriteria,
    compute_mode_diagnostics,
    identify_te01delta,
)

R_MAX = 6.14e-3
Z_MAX = 18.42e-3
Z_MID = 0.5 * Z_MAX


@pytest.fixture(scope="module")
def grid() -> StructuredGrid:
    return structured_grid(R_MAX, Z_MAX, n_r=41, n_z=61)


def _zero_fields(n: int) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.zeros((n, 3), dtype=np.complex128),
        np.zeros((n, 3), dtype=np.complex128),
    )


def _te_like_fields(
    grid: StructuredGrid,
    axial_lobes: int = 1,
    global_phase: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """TE-family candidate: E_phi only; H_z peaking on the axis.

    `axial_lobes = 1` is the TE01delta pattern (single axial antinode,
    no sign change); `axial_lobes = 2` makes H_z odd about the
    mid-plane — one sign change on the axis, the TE01(delta+1)-like
    axial overtone the sign-change criterion must reject.
    """
    r, z = grid.r_m, grid.z_m
    w = 0.3 * R_MAX
    envelope = np.exp(-((z - Z_MID) ** 2) / (2.0 * w**2))
    e, h = _zero_fields(grid.n_nodes)
    e[:, 1] = r * np.exp(-(r**2) / (2.0 * w**2)) * envelope
    hz = np.exp(-(r**2) / (2.0 * w**2)) * envelope
    if axial_lobes == 2:
        hz = hz * (z - Z_MID) / w
    h[:, 2] = hz
    phase = np.exp(1j * global_phase)
    return e * phase, h * phase


def _tm_like_fields(grid: StructuredGrid) -> tuple[np.ndarray, np.ndarray]:
    """TM-family candidate: (E_r, E_z, H_phi) only — zero E_phi, zero H_z."""
    r, z = grid.r_m, grid.z_m
    w = 0.3 * R_MAX
    envelope = np.exp(
        -(r**2 + (z - Z_MID) ** 2) / (2.0 * w**2)
    )
    e, h = _zero_fields(grid.n_nodes)
    e[:, 0] = r * envelope
    e[:, 2] = envelope
    h[:, 1] = r * envelope
    return e, h


def _diagnostics(
    grid: StructuredGrid,
    e: np.ndarray,
    h: np.ndarray,
    f_hz: complex,
) -> ModeDiagnostics:
    return compute_mode_diagnostics(
        f_hz, e, h, grid.r_m, grid.z_m, grid.weights_m2
    )


class TestComputeModeDiagnostics:
    def test_te_candidate_scores(self, grid):
        e, h = _te_like_fields(grid)
        d = _diagnostics(grid, e, h, complex(1.52e9, 7.6e4))
        assert d.azimuthal_e_energy_fraction == pytest.approx(1.0)
        assert d.axis_hz_antinode_ratio == pytest.approx(1.0)
        assert d.axis_hz_sign_changes == 0
        assert d.passes(TE01DeltaCriteria())

    def test_tm_candidate_scores(self, grid):
        e, h = _tm_like_fields(grid)
        d = _diagnostics(grid, e, h, complex(1.46e9, 7.3e4))
        assert d.azimuthal_e_energy_fraction == pytest.approx(0.0)
        assert d.axis_hz_antinode_ratio == 0.0
        assert not d.passes(TE01DeltaCriteria())

    def test_axial_overtone_rejected_by_sign_change(self, grid):
        e, h = _te_like_fields(grid, axial_lobes=2)
        d = _diagnostics(grid, e, h, complex(1.9e9, 9.5e4))
        assert d.azimuthal_e_energy_fraction == pytest.approx(1.0)
        assert d.axis_hz_sign_changes >= 1
        assert not d.passes(TE01DeltaCriteria())

    def test_global_phase_invariance(self, grid):
        """Eigenvectors carry an arbitrary global phase; the scores
        (including the phase-aligned sign-change count) must not."""
        e0, h0 = _te_like_fields(grid, axial_lobes=2)
        e1, h1 = _te_like_fields(grid, axial_lobes=2, global_phase=0.7)
        f = complex(1.9e9, 9.5e4)
        d0 = _diagnostics(grid, e0, h0, f)
        d1 = _diagnostics(grid, e1, h1, f)
        assert d1.azimuthal_e_energy_fraction == pytest.approx(
            d0.azimuthal_e_energy_fraction
        )
        assert d1.axis_hz_sign_changes == d0.axis_hz_sign_changes

    def test_rejects_shape_mismatch(self, grid):
        e, h = _te_like_fields(grid)
        with pytest.raises(ValueError, match="\\(N, 3\\)"):
            compute_mode_diagnostics(
                complex(1.5e9, 1e5),
                e[:, :2],
                h[:, :2],
                grid.r_m,
                grid.z_m,
                grid.weights_m2,
            )

    def test_rejects_zero_electric_field(self, grid):
        e, h = _zero_fields(grid.n_nodes)
        h[:, 2] = 1.0
        with pytest.raises(ValueError, match="zero electric field"):
            _diagnostics(grid, e, h, complex(1.5e9, 1e5))


class TestIdentifyTE01Delta:
    SEARCH_HZ = 1.45e9

    def test_proximity_trap(self, grid):
        """The known trap: a TM mode 10 MHz from the search frequency
        vs the true TE01delta 70 MHz away. Nearest-eigenvalue picking
        chooses the TM mode; the field-symmetry filter must not."""
        e_tm, h_tm = _tm_like_fields(grid)
        e_te, h_te = _te_like_fields(grid)
        f_tm = complex(1.46e9, 7.3e4)   # 10 MHz from search
        f_te = complex(1.52e9, 7.6e4)   # 70 MHz from search
        diags = [
            _diagnostics(grid, e_tm, h_tm, f_tm),
            _diagnostics(grid, e_te, h_te, f_te),
        ]

        # Demonstrate the trap: proximity alone picks the wrong mode.
        by_proximity = int(
            np.argmin(
                [
                    abs(d.complex_eigenfrequency_hz.real - self.SEARCH_HZ)
                    for d in diags
                ]
            )
        )
        assert by_proximity == 0, "trap premise broken: TM should be nearer"

        picked = identify_te01delta(diags, self.SEARCH_HZ)
        assert picked == 1, (
            "identify_te01delta fell into the eigenvalue-proximity trap"
        )

    def test_proximity_breaks_ties_among_passing_only(self, grid):
        e_te, h_te = _te_like_fields(grid)
        diags = [
            _diagnostics(grid, e_te, h_te, complex(1.60e9, 8.0e4)),
            _diagnostics(grid, e_te, h_te, complex(1.44e9, 7.2e4)),
        ]
        assert identify_te01delta(diags, self.SEARCH_HZ) == 1

    def test_raises_when_nothing_passes(self, grid):
        e_tm, h_tm = _tm_like_fields(grid)
        diags = [
            _diagnostics(grid, e_tm, h_tm, complex(1.46e9, 7.3e4)),
            _diagnostics(grid, e_tm, h_tm, complex(1.39e9, 7.0e4)),
        ]
        with pytest.raises(
            ModeIdentificationError, match="field-symmetry"
        ) as excinfo:
            identify_te01delta(diags, self.SEARCH_HZ)
        # The error must carry the per-candidate diagnostic table.
        assert "E_phi energy fraction" in str(excinfo.value)

    def test_raises_on_empty_candidate_list(self):
        with pytest.raises(ModeIdentificationError, match="no eigenmode"):
            identify_te01delta([], self.SEARCH_HZ)


class TestCriteriaValidation:
    def test_rejects_bad_energy_fraction(self):
        with pytest.raises(ValueError):
            TE01DeltaCriteria(min_azimuthal_e_energy_fraction=0.0)

    def test_rejects_bad_noise_floor(self):
        with pytest.raises(ValueError):
            TE01DeltaCriteria(axis_noise_floor_fraction=1.0)

    def test_rejects_negative_sign_changes(self):
        with pytest.raises(ValueError):
            TE01DeltaCriteria(max_axis_hz_sign_changes=-1)
