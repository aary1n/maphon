"""SPEC §3 p_e (electric-energy filling factor) — analytic test (3).

Two-domain fixture: dielectric in r in [r_d_lo, r_d_hi] x [z_d_lo,
z_d_hi] with Re(eps_r) = eps_d and |E| = 1; vacuum elsewhere with
Re(eps_r) = 1 and |E| = 1. The closed-form filling factor is

    p_e = (eps_d * V_diel) / (eps_d * V_diel + 1 * V_vac),

where V_diel and V_vac are the axisymmetric volumes of the two regions
(computed by hand from the rectangular cross-sections).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cavity.extraction import FieldSample, electric_filling_factor

from tests._extraction_fixtures import make_structured_grid, zero_complex_3vec


def _axisymmetric_volume_rect(
    r_lo: float, r_hi: float, z_lo: float, z_hi: float
) -> float:
    """Closed-form axisymmetric volume of an r-z rectangle.

    int_V dV = 2*pi * int_{r_lo}^{r_hi} r dr * int_{z_lo}^{z_hi} dz
            = pi * (r_hi^2 - r_lo^2) * (z_hi - z_lo).
    """
    return math.pi * (r_hi ** 2 - r_lo ** 2) * (z_hi - z_lo)


class TestPEFillingFactor:
    """SPEC §3: p_e required, ratio in (0, 1], uses Re(eps_r)."""

    def _two_domain_field(
        self,
        eps_dielectric: float,
        e_amplitude: float = 1.0,
        n_r: int = 121,
        n_z: int = 181,
    ) -> tuple[FieldSample, float, float]:
        """Builds the two-domain fixture and returns (field, V_diel, V_vac).

        Cavity: [0, 6e-3] x [0, 18e-3]. Dielectric occupies
        [1e-3, 3e-3] x [4e-3, 14e-3]; vacuum elsewhere.
        """
        r_lo_box, r_hi_box = 0.0, 6.0e-3
        z_lo_box, z_hi_box = 0.0, 18.0e-3
        r_lo_d, r_hi_d = 1.0e-3, 3.0e-3
        z_lo_d, z_hi_d = 4.0e-3, 14.0e-3

        grid = make_structured_grid(
            r_lo_box, r_hi_box, z_lo_box, z_hi_box, n_r=n_r, n_z=n_z,
        )
        n = grid.r_m.size

        dielectric_mask = (
            (grid.r_m >= r_lo_d)
            & (grid.r_m <= r_hi_d)
            & (grid.z_m >= z_lo_d)
            & (grid.z_m <= z_hi_d)
        )

        eps_r = np.where(dielectric_mask, eps_dielectric, 1.0).astype(
            np.complex128
        )

        e = zero_complex_3vec(n)
        e[:, 1] = e_amplitude  # E_phi
        h = zero_complex_3vec(n)
        h[:, 2] = 1.0  # H_z, non-zero so V_mode is defined

        field = FieldSample(
            r_m=grid.r_m,
            z_m=grid.z_m,
            e_complex=e,
            h_complex=h,
            eps_r_complex=eps_r,
            weights_m2=grid.weights_m2,
            dielectric_mask=dielectric_mask,
            complex_eigenfrequency_hz=complex(1.45e9, 1.0e5),
        )

        v_diel = _axisymmetric_volume_rect(r_lo_d, r_hi_d, z_lo_d, z_hi_d)
        v_box = _axisymmetric_volume_rect(
            r_lo_box, r_hi_box, z_lo_box, z_hi_box
        )
        v_vac = v_box - v_diel
        return field, v_diel, v_vac

    def test_two_domain_ratio_matches_closed_form(self):
        """p_e tracks the continuous closed form within trapezoid bias.

        Tolerance ~3% absorbs the trapezoid mask boundary over-count: at
        N_r=121 the dielectric r-range (40 cells) is over-counted by
        1 + 1/40 = 2.5%; the z-range (100 cells) by 1%, compounding to
        ~3.5% in V_diel and ~1.7% in p_e. The bias scales as 1/N and
        vanishes in the dense-mesh limit (asserted in
        `test_p_e_converges_to_closed_form_as_mesh_refines`). The
        finite-mesh agreement here is the contract: extract() returns
        the right ratio of the right two integrals.
        """
        eps_d = 10.0
        field, v_diel, v_vac = self._two_domain_field(eps_dielectric=eps_d)
        p_e = electric_filling_factor(field)
        expected = (eps_d * v_diel) / (eps_d * v_diel + 1.0 * v_vac)
        assert p_e == pytest.approx(expected, rel=3e-2)

    def test_p_e_converges_to_closed_form_as_mesh_refines(self):
        """Coarser meshes should sit FURTHER from the closed form than finer
        ones — the trapezoid mask bias is O(1/N) and proves this is a
        quadrature artifact, not an extraction error."""
        eps_d = 10.0
        field_default, v_diel, v_vac = self._two_domain_field(
            eps_dielectric=eps_d
        )
        p_e_default = electric_filling_factor(field_default)
        expected = (eps_d * v_diel) / (eps_d * v_diel + 1.0 * v_vac)

        # Build a coarser mesh and confirm its p_e is further from the
        # closed form than the default-mesh p_e.
        coarse_field, _, _ = self._two_domain_field(
            eps_dielectric=eps_d, n_r=31, n_z=46
        )
        p_e_coarse = electric_filling_factor(coarse_field)
        assert abs(p_e_coarse - expected) > abs(p_e_default - expected)

    def test_higher_eps_drives_p_e_toward_one(self):
        """As eps_diel -> infinity, the dielectric hoards all electric
        energy and p_e -> 1.
        """
        _, _, _ = self._two_domain_field(eps_dielectric=1.0)
        p_e_low = electric_filling_factor(
            self._two_domain_field(eps_dielectric=2.0)[0]
        )
        p_e_high = electric_filling_factor(
            self._two_domain_field(eps_dielectric=1.0e4)[0]
        )
        assert p_e_low < p_e_high
        assert p_e_high == pytest.approx(1.0, abs=1e-2)

    def test_p_e_in_unit_interval(self):
        for eps in (2.0, 10.0, 100.0, 316.3):
            field, _, _ = self._two_domain_field(eps_dielectric=eps)
            p_e = electric_filling_factor(field)
            assert 0.0 < p_e <= 1.0

    def test_uses_real_part_of_eps_r(self):
        """Adding a loss-tangent imaginary part to eps_r must not shift p_e
        — the filling factor is a stored-energy ratio, not a dissipation
        weighting.
        """
        field_real, _, _ = self._two_domain_field(eps_dielectric=316.3)
        p_e_real = electric_filling_factor(field_real)

        # Copy the field, add an Im part to eps_r inside the dielectric.
        eps_lossy = field_real.eps_r_complex.copy()
        eps_lossy[field_real.dielectric_mask] *= (1.0 - 1j * 1.1e-4)
        field_lossy = FieldSample(
            r_m=field_real.r_m,
            z_m=field_real.z_m,
            e_complex=field_real.e_complex,
            h_complex=field_real.h_complex,
            eps_r_complex=eps_lossy,
            weights_m2=field_real.weights_m2,
            dielectric_mask=field_real.dielectric_mask,
            complex_eigenfrequency_hz=field_real.complex_eigenfrequency_hz,
        )
        p_e_lossy = electric_filling_factor(field_lossy)
        assert p_e_lossy == pytest.approx(p_e_real, rel=1e-12)
