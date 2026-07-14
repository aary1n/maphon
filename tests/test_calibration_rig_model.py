"""T2 — rig thermal model anchors (calibration/rig_model.py), §8 discipline.

Closed-form and limit anchors first (the layered cross-check and the
Dirichlet-base limit), then the physical-direction assertions the T4
ratio mechanism leans on.
"""

from __future__ import annotations

import numpy as np
import pytest

from calibration.rig_model import (
    RigConfig,
    build_source,
    build_spec,
    probe_average_dt_k,
    sweep_sample,
    theta_probe_k_per_w,
)
from calibration.samples import D14, H14, default_grid
from cavity.thermal.cylinder import CylinderSpec, PumpSource, SurfaceBC, solve
from cavity.thermal.layered import Layer, delta_t_disk_average, delta_t_disk_center


def _config(sample=D14, **overrides) -> RigConfig:
    params = dict(
        sample=sample,
        thickness_m=0.6e-3,
        spot_diameter_m=400e-6,
        h_sub_w_m2_k=1e3,
        k_w_m_k=0.316,
        radius_factor=0.5642,
    )
    params.update(overrides)
    return RigConfig(**params)


class TestAnchors:
    def test_huge_h_sub_recovers_dirichlet_base(self):
        """Robin base with h_sub → ∞ must converge to the exact-Dirichlet
        base — the limit the h_sub sweep's top decade approaches."""
        config = _config(h_sub_w_m2_k=1e12)
        theta_robin = theta_probe_k_per_w(config)
        spec_dirichlet = CylinderSpec(
            radius_m=config.disc_radius_m,
            height_m=config.thickness_m,
            k_r_w_m_k=config.k_w_m_k,
            side=SurfaceBC.robin(config.h_exposed_w_m2_k),
            top=SurfaceBC.robin(config.h_exposed_w_m2_k),
            base=SurfaceBC.dirichlet(),
        )
        solution = solve(spec_dirichlet, build_source(config), n_modes=64)
        theta_dirichlet = probe_average_dt_k(solution, config.spot_radius_m)
        assert theta_robin == pytest.approx(theta_dirichlet, rel=1e-6)

    def test_wide_crystal_matches_layered_solver(self):
        """Wide-cylinder limit vs the independent Hankel/layered solver
        (SPEC §7.T1's other anchor): same slab, same disc source, insulated
        top, isothermal base. Independent formulations — a genuine
        cross-check, not a restatement."""
        k, t, a, p = 0.3, 0.5e-3, 0.2e-3, 1.0
        spec = CylinderSpec(
            radius_m=2e-3,  # R >> t: side wall out of reach of the spot field
            height_m=t,
            k_r_w_m_k=k,
            side=SurfaceBC.robin(0.0),
            top=SurfaceBC.robin(0.0),
            base=SurfaceBC.dirichlet(),
        )
        source = PumpSource(p_w=p, axial_form="surface", radial_form="disc", disc_radius_m=a)
        # centre converges slowest (one-sided modal truncation, measured
        # -1.5e-4 at 800 modes); the probe average is 30x tighter
        solution = solve(spec, source, n_modes=800)
        layers = (Layer(thickness_m=t, k_w_m_k=k),)
        center_layered = delta_t_disk_center(layers, p, a)
        center_cyl = float(solution.delta_t(0.0, 0.0))
        assert center_cyl == pytest.approx(center_layered, rel=5e-4)
        avg_layered = delta_t_disk_average(layers, p, a)
        avg_cyl = probe_average_dt_k(solution, a)
        assert avg_cyl == pytest.approx(avg_layered, rel=1e-4)

    def test_energy_balance(self):
        """Deposited P must exit through the surfaces (solver's own energy
        diagnostic, asserted at the rig configuration)."""
        config = _config()
        solution = solve(build_spec(config), build_source(config, p_w=1.0), n_modes=64)
        power = solution.boundary_power_w()
        assert power["total"] == pytest.approx(1.0, rel=1e-6)

    def test_probe_average_quadrature_converged(self):
        config = _config()
        solution = solve(build_spec(config), build_source(config), n_modes=64)
        a = config.spot_radius_m
        gl = probe_average_dt_k(solution, a)
        r = np.linspace(0.0, a, 4001)
        dt = np.asarray(solution.delta_t(r, np.zeros_like(r)))
        trapz = 2.0 * np.trapezoid(dt * r, r) / a**2
        assert gl == pytest.approx(trapz, rel=1e-7)


class TestPhysicalDirections:
    def test_linearity_in_power(self):
        config = _config()
        s1 = solve(build_spec(config), build_source(config, p_w=1.0), n_modes=64)
        s2 = solve(build_spec(config), build_source(config, p_w=2.0), n_modes=64)
        a = config.spot_radius_m
        assert probe_average_dt_k(s2, a) == pytest.approx(2.0 * probe_average_dt_k(s1, a), rel=1e-12)

    def test_monotone_decreasing_in_h_sub(self):
        thetas = [theta_probe_k_per_w(_config(h_sub_w_m2_k=h)) for h in (1e2, 1e3, 1e4, 1e5)]
        assert all(a > b for a, b in zip(thetas, thetas[1:]))

    def test_monotone_decreasing_in_k(self):
        thetas = [theta_probe_k_per_w(_config(k_w_m_k=k)) for k in (0.1, 0.316, 1.0)]
        assert all(a > b for a, b in zip(thetas, thetas[1:]))

    def test_monotone_increasing_in_thickness_at_weak_h_sub(self):
        """More crystal between spot and sink = more series resistance."""
        thetas = [theta_probe_k_per_w(_config(thickness_m=t)) for t in (0.2e-3, 0.6e-3, 1.0e-3)]
        assert all(a < b for a, b in zip(thetas, thetas[1:]))

    def test_probe_average_below_peak(self):
        config = _config()
        solution = solve(build_spec(config), build_source(config), n_modes=64)
        assert probe_average_dt_k(solution, config.spot_radius_m) < solution.peak_k

    def test_d14_hotter_than_h14_at_shared_parameters(self):
        """The T4 mechanism: the smaller crystal has less sink area, so at
        SHARED interface parameters it runs hotter per absorbed watt."""
        assert theta_probe_k_per_w(_config(sample=D14)) > theta_probe_k_per_w(
            _config(sample=H14)
        )

    def test_radiation_branch_reduces_theta(self):
        """The ratified flagged branch adds h_rad ≈ 5 W/m²/K to exposed
        faces — extra loss path, lower ΔT (small at these Biot numbers)."""
        base = theta_probe_k_per_w(_config())
        with_rad = theta_probe_k_per_w(_config(include_radiation=True))
        assert with_rad < base
        assert with_rad == pytest.approx(base, rel=0.05)  # a correction, not a regime change


class TestValidation:
    def test_spot_larger_than_crystal_rejected(self):
        config = _config(sample=D14, spot_diameter_m=1.3e-3, radius_factor=0.5)
        with pytest.raises(ValueError, match="exceeds equivalent disc"):
            build_spec(config)

    def test_sweep_shapes_and_shared_indexing(self):
        grid = default_grid(n_thickness=2, n_spot=1, n_h_sub=2, n_k=2)
        result = sweep_sample(D14, grid)
        assert result.theta_k_per_w.shape == (grid.n_shared, 2)
        axes = result.shared_axes()
        assert len(axes) == grid.n_shared
        # C-order convention: radius_factor is the fastest axis
        assert axes[0][3] == grid.radius_factor[0]
        assert axes[1][3] == grid.radius_factor[1]
        assert np.all(result.theta_k_per_w > 0.0)
