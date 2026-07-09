"""SPEC §8 — closed-form TE011 field maps (`cavity.validation.analytic_fields`).

The anchors here pin the FIELD-level closed forms the §3 weight
functionals and the export normalisation lean on: the Maxwell-fixed
amplitude prefactor chain (module docstring, "Amplitude prefactor
chain" — the U_E = U_H test cites it), the Lommel radial and elementary
axial integrals, and the coaxial sub-region energy integrals.

Tolerance basis, stated per anchor (§8 discipline):
  - closed-form vs closed-form identities: CODATA-limited (~1e-10,
    since 2019-SI mu0/eps0 are measured) or exact algebra;
  - quadrature vs closed form on CONFORMING grids (grid edges on the
    region boundary): composite-trapezoid O(h^2) — measured 1e-5 class
    at 201x301, asserted at 1e-4 (~10x margin);
  - Lommel/axial closed forms vs scipy adaptive quadrature:
    integrator-limited (1e-9 rel).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.constants import epsilon_0 as EPS_0
from scipy.constants import mu_0 as MU_0
from scipy.integrate import quad
from scipy.special import jv

from cavity.extraction.quadrature import axisymmetric_volume_integral
from cavity.forward_model.gridding import structured_grid
from cavity.validation.analytic import bessel_zero_jprime, f_te_mnp
from cavity.validation.analytic_fields import (
    TE011Mode,
    cos_squared_axial_integral,
    lommel_jn_squared_integral,
    sin_squared_axial_integral,
    te011_electric_energy_fraction_inside_radius,
    te011_fields,
    te011_h2_subregion_integral,
    te011_h2_total_integral,
    te011_stored_energies,
)

# Booth-box half-plane dimensions (empty: TE011 lands near 30.87 GHz)
# plus a second aspect ratio so no identity passes by coincidence.
MODES = (
    TE011Mode(radius_m=6.14e-3, length_m=18.42e-3),
    TE011Mode(radius_m=10.0e-3, length_m=10.0e-3, e0_v_per_m=2.5),
)

# Quadrature anchors: conforming-grid composite trapezoid is O(h^2);
# measured ~1e-5 relative at this resolution, asserted with ~10x margin.
N_R, N_Z = 201, 301
QUAD_REL_TOL = 1.0e-4


def _grid_fields(mode: TE011Mode, n_r: int = N_R, n_z: int = N_Z):
    grid = structured_grid(mode.radius_m, mode.length_m, n_r, n_z)
    e, h = te011_fields(mode, grid.r_m, grid.z_m)
    return grid, e, h


class TestPrefactorChain:
    """Amendment guard: the E/H relative amplitudes are Maxwell-fixed."""

    @pytest.mark.parametrize("mode", MODES)
    def test_resonance_condition_closes_the_chain(self, mode):
        """kc^2 + kz^2 = omega^2 mu0 eps0 with f consumed from f_te_mnp.

        This is the condition under which the Ampere curl closes on the
        Faraday-derived prefactors (module docstring, step 3). CODATA
        mu0*eps0 limits the residual (~1e-10), not the algebra.
        """
        lhs = mode.k_c_per_m**2 + mode.k_z_per_m**2
        rhs = mode.omega_rad_per_s**2 * MU_0 * EPS_0
        assert lhs == pytest.approx(rhs, rel=1.0e-9)

    @pytest.mark.parametrize("mode", MODES)
    def test_h_amplitude_ratio_is_kc_over_kz(self, mode):
        """H_z/H_r amplitude ratio = kc/kz exactly — not a free choice."""
        assert mode.h_z_amp_a_per_m / mode.h_r_amp_a_per_m == pytest.approx(
            mode.k_c_per_m / mode.k_z_per_m, rel=1.0e-14
        )

    @pytest.mark.parametrize("mode", MODES)
    def test_h_r_prefactor_value(self, mode):
        assert mode.h_r_amp_a_per_m == pytest.approx(
            mode.k_z_per_m
            / (mode.omega_rad_per_s * MU_0)
            * mode.e0_v_per_m,
            rel=1.0e-14,
        )

    @pytest.mark.parametrize("mode", MODES)
    def test_frequency_consumed_from_closed_form(self, mode):
        assert mode.f_hz == f_te_mnp(
            0, 1, 1, mode.radius_m, mode.length_m
        )


class TestFieldStructure:
    """TE011 component structure, phases, and boundary conditions."""

    @pytest.mark.parametrize("mode", MODES)
    def test_te_family_components_only(self, mode):
        _, e, h = _grid_fields(mode, n_r=41, n_z=61)
        assert np.all(e[:, 0] == 0) and np.all(e[:, 2] == 0)  # E_r, E_z
        assert np.all(h[:, 1] == 0)  # H_phi

    @pytest.mark.parametrize("mode", MODES)
    def test_e_h_phase_quadrature(self, mode):
        """E real-phased, H purely imaginary: the -i/+i standing-wave
        phases of the prefactor chain (energy sloshes E <-> H)."""
        _, e, h = _grid_fields(mode, n_r=41, n_z=61)
        assert np.all(e.imag == 0)
        assert np.all(h.real == 0)

    @pytest.mark.parametrize("mode", MODES)
    def test_pec_boundary_conditions(self, mode):
        """E_phi = 0 on barrel (r = a) and end plates (z = 0, L)."""
        grid, e, _ = _grid_fields(mode, n_r=41, n_z=61)
        e_phi = np.abs(e[:, 1])
        scale = float(e_phi.max())
        on_barrel = np.isclose(grid.r_m, mode.radius_m)
        on_plates = np.isclose(grid.z_m, 0.0) | np.isclose(
            grid.z_m, mode.length_m
        )
        assert np.all(e_phi[on_barrel] <= 1.0e-12 * scale)
        assert np.all(e_phi[on_plates] <= 1.0e-12 * scale)

    @pytest.mark.parametrize("mode", MODES)
    def test_h_z_antinode_on_axis(self, mode):
        """|H_z| peaks on the axis (J0 max at 0) — the mode-ID criterion
        the §2 field-symmetry test uses."""
        grid, _, h = _grid_fields(mode, n_r=41, n_z=61)
        abs_hz = np.abs(h[:, 2])
        on_axis = grid.r_m == 0.0
        assert abs_hz.max() == pytest.approx(
            abs_hz[on_axis].max(), rel=1.0e-12
        )


class TestStoredEnergyIdentity:
    """U_E = U_H at resonance — THE prefactor-chain anchor.

    Cites `analytic_fields` module docstring, 'Amplitude prefactor
    chain': the equality holds only through the Maxwell-fixed
    kz/(omega mu0) and kc/(omega mu0) amplitudes plus the resonance
    condition. Three independent shape functions with unit amplitudes
    would fail this (or make it vacuous after re-normalisation) — the
    identity is what makes the field maps an anchor rather than
    plotting art.
    """

    @pytest.mark.parametrize("mode", MODES)
    def test_closed_form_equality(self, mode):
        """Each side through its own Lommel/axial/prefactor chain;
        residual is CODATA-limited (measured ~1e-12)."""
        u_e, u_h = te011_stored_energies(mode)
        assert u_e > 0
        assert u_e == pytest.approx(u_h, rel=1.0e-9)

    @pytest.mark.parametrize("mode", MODES)
    def test_quadrature_equality_on_export_class_grid(self, mode):
        """U_E = U_H recomputed through the §3 quadrature primitive on
        a 201x301 grid — doubles as the normalisation-convention check
        for `cavity.export` (same densities, same primitive)."""
        grid, e, h = _grid_fields(mode)
        e2 = np.sum(np.abs(e) ** 2, axis=1)
        h2 = np.sum(np.abs(h) ** 2, axis=1)
        u_e = (
            EPS_0
            / 4.0
            * axisymmetric_volume_integral(e2, grid.r_m, grid.weights_m2).real
        )
        u_h = (
            MU_0
            / 4.0
            * axisymmetric_volume_integral(h2, grid.r_m, grid.weights_m2).real
        )
        assert u_e == pytest.approx(u_h, rel=QUAD_REL_TOL)

    @pytest.mark.parametrize("mode", MODES)
    def test_quadrature_matches_closed_forms(self, mode):
        """Grid quadrature reproduces each closed-form energy."""
        grid, e, h = _grid_fields(mode)
        u_e_cf, u_h_cf = te011_stored_energies(mode)
        e2 = np.sum(np.abs(e) ** 2, axis=1)
        h2 = np.sum(np.abs(h) ** 2, axis=1)
        u_e_q = (
            EPS_0
            / 4.0
            * axisymmetric_volume_integral(e2, grid.r_m, grid.weights_m2).real
        )
        u_h_q = (
            MU_0
            / 4.0
            * axisymmetric_volume_integral(h2, grid.r_m, grid.weights_m2).real
        )
        assert u_e_q == pytest.approx(u_e_cf, rel=QUAD_REL_TOL)
        assert u_h_q == pytest.approx(u_h_cf, rel=QUAD_REL_TOL)


class TestClosedFormIntegrals:
    """Lommel and axial closed forms vs scipy adaptive quadrature."""

    @pytest.mark.parametrize("n", [0, 1, 2])
    @pytest.mark.parametrize("kb", [(500.0, 3.0e-3), (623.9, 6.14e-3)])
    def test_lommel_vs_adaptive_quadrature(self, n, kb):
        k, b = kb
        closed = lommel_jn_squared_integral(n, k, b)
        numeric, _ = quad(lambda r: jv(n, k * r) ** 2 * r, 0.0, b)
        assert closed == pytest.approx(numeric, rel=1.0e-9)

    def test_lommel_zero_radius(self):
        assert lommel_jn_squared_integral(1, 500.0, 0.0) == 0.0

    @pytest.mark.parametrize("bounds", [(0.0, 18.42e-3), (5.5e-3, 12.9e-3)])
    def test_axial_closed_forms_vs_quadrature(self, bounds):
        z_lo, z_hi = bounds
        k_z = math.pi / 18.42e-3
        s_cf = sin_squared_axial_integral(k_z, z_lo, z_hi)
        c_cf = cos_squared_axial_integral(k_z, z_lo, z_hi)
        s_num, _ = quad(lambda z: math.sin(k_z * z) ** 2, z_lo, z_hi)
        c_num, _ = quad(lambda z: math.cos(k_z * z) ** 2, z_lo, z_hi)
        assert s_cf == pytest.approx(s_num, rel=1.0e-12)
        assert c_cf == pytest.approx(c_num, rel=1.0e-12)

    def test_sin_cos_partition_full_length(self):
        """sin^2 + cos^2 integrates to the interval length exactly."""
        k_z = math.pi / 18.42e-3
        total = sin_squared_axial_integral(
            k_z, 0.0, 18.42e-3
        ) + cos_squared_axial_integral(k_z, 0.0, 18.42e-3)
        assert total == pytest.approx(18.42e-3, rel=1.0e-14)


class TestSubRegionAnchors:
    """Coaxial sub-region closed forms vs conforming-grid quadrature.

    The grids CONFORM to the sub-region (edges on its boundary), so the
    comparison is pure O(h^2) trapezoid — the mask-boundary staircase
    error class of full-domain masks is exercised (and stated) in
    tests/test_extraction_weights.py instead.
    """

    @pytest.mark.parametrize("mode", MODES)
    def test_electric_fraction_inside_radius(self, mode):
        b = mode.radius_m / 2.0
        frac_cf = te011_electric_energy_fraction_inside_radius(mode, b)
        sub = structured_grid(b, mode.length_m, N_R, N_Z)
        e_sub, _ = te011_fields(mode, sub.r_m, sub.z_m)
        e2_sub = np.sum(np.abs(e_sub) ** 2, axis=1)
        num = axisymmetric_volume_integral(
            e2_sub, sub.r_m, sub.weights_m2
        ).real
        u_e_cf, _ = te011_stored_energies(mode)
        den = 4.0 * u_e_cf / EPS_0
        assert num / den == pytest.approx(frac_cf, rel=QUAD_REL_TOL)

    @pytest.mark.parametrize("mode", MODES)
    def test_electric_fraction_limits_and_monotonicity(self, mode):
        assert te011_electric_energy_fraction_inside_radius(
            mode, mode.radius_m
        ) == pytest.approx(1.0, rel=1.0e-14)
        fracs = [
            te011_electric_energy_fraction_inside_radius(
                mode, x * mode.radius_m
            )
            for x in (0.2, 0.4, 0.6, 0.8, 1.0)
        ]
        assert all(a < b for a, b in zip(fracs, fracs[1:]))
        assert 0.0 < fracs[0] < 1.0

    @pytest.mark.parametrize("mode", MODES)
    def test_h2_subregion_vs_conforming_grid(self, mode):
        """Crystal-like sub-region (r < 0.3a, |z - L/2| < 0.2L): the
        spin-arm normalisation integral, closed form vs quadrature."""
        b = 0.3 * mode.radius_m
        z_lo, z_hi = 0.3 * mode.length_m, 0.7 * mode.length_m
        cf = te011_h2_subregion_integral(mode, b, z_lo, z_hi)
        sub = structured_grid(b, z_hi, N_R, N_Z, z_min_m=z_lo)
        _, h_sub = te011_fields(mode, sub.r_m, sub.z_m)
        h2_sub = np.sum(np.abs(h_sub) ** 2, axis=1)
        q = axisymmetric_volume_integral(h2_sub, sub.r_m, sub.weights_m2).real
        assert q == pytest.approx(cf, rel=QUAD_REL_TOL)

    @pytest.mark.parametrize("mode", MODES)
    def test_h2_total_consistent_with_stored_energy(self, mode):
        """Full-volume |H|^2 integral x mu0/4 = U_H, closed vs closed."""
        _, u_h = te011_stored_energies(mode)
        assert MU_0 / 4.0 * te011_h2_total_integral(mode) == pytest.approx(
            u_h, rel=1.0e-12
        )


class TestInputGuards:
    def test_mode_rejects_bad_dimensions(self):
        with pytest.raises(ValueError):
            TE011Mode(radius_m=0.0, length_m=1.0)
        with pytest.raises(ValueError):
            TE011Mode(radius_m=1.0, length_m=-1.0)
        with pytest.raises(ValueError):
            TE011Mode(radius_m=1.0, length_m=1.0, e0_v_per_m=0.0)

    def test_fields_reject_mismatched_arrays(self):
        mode = MODES[0]
        with pytest.raises(ValueError):
            te011_fields(mode, np.zeros(3), np.zeros(4))
        with pytest.raises(ValueError):
            te011_fields(mode, np.array([-1.0e-3]), np.array([0.0]))

    def test_subregion_bounds_checked(self):
        mode = MODES[0]
        with pytest.raises(ValueError):
            te011_h2_subregion_integral(
                mode, 2.0 * mode.radius_m, 0.0, mode.length_m
            )
        with pytest.raises(ValueError):
            te011_h2_subregion_integral(
                mode, mode.radius_m, 0.01, 0.001
            )
        with pytest.raises(ValueError):
            te011_electric_energy_fraction_inside_radius(mode, 0.0)

    def test_kc_uses_first_j1_zero(self):
        """kc = x'_01/a with x'_01 = 3.8317... (zero of J0' = -J1)."""
        mode = MODES[0]
        assert mode.k_c_per_m * mode.radius_m == pytest.approx(
            bessel_zero_jprime(0, 1), rel=1.0e-14
        )
