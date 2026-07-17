"""T2 — thermal model of one dataset crystal in the Cowley-Semple rig.

Wraps the shared finite-cylinder solver (`cavity.thermal.cylinder`, the
SPEC §7T Bessel/Robin anchor) for the calibration geometry: the crystal as
an equivalent disc (radius mapping swept — `calibration.constants
.RadiusMapping`), top-hat spot deposited as a surface flux on the top face,
Robin h = 5 on top and side, effective Robin h_sub on the glued underside.
Analytic, licence-free; the ratified plan's COMSOL contingency trigger
(indeterminate T4 verdict AND verdict flips across the radius-mapping band
edges) is evaluated by `calibration.ratio_test`, not here.

Observable: the SPOT-AVERAGED top-surface temperature rise. ODMR probes
the optically excited volume and excitation/collection are co-located
(SPEC §7.T5(a)), so the probe weight is the excitation disc itself; the
surface-deposition headline branch makes the surface field the probed one.
Everything is exactly linear in absorbed power P, so the reduced scalar

    Θ_probe = <ΔT>_spot / P_abs      [K/W]

is computed once per configuration at P = 1 W.

NON-TRANSFERABLE: Θ values from this module are rig numbers. The transport
core (`cavity.thermal.cylinder`) and dν/dT transfer; ΔT does not (§7.T5).

CPW via-contact caveat — Oxborrow (verbal, in-person meeting 2026-07-16):
heat extraction on the coplanar waveguide depends on whether the sample
spans onto via'd copper regions of the board — a narrower sample that does
not reach the vias runs hotter, and orientation on the CPW also matters.
This adds a second geometry-dependent heat-sinking mechanism and further
weakens any deuteration-only attribution. It is consistent with the
existing geometry-sufficient verdict but is not quantified by the present
ratio test and does not increase that test's numerical discriminating
power. The T4 report's claim level — geometry-sufficient, low
discriminating power, deuteration neither required nor excluded — is
unchanged; see
calibration/reports/ratio_test_digitized_addendum_2026-07-16.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from calibration.constants import AMBIENT, EXPOSED
from calibration.samples import SampleConfig, SweepGrid
from cavity.provenance.constants import EMISSIVITY_PTP
from cavity.thermal.cylinder import CylinderSpec, PumpSource, SurfaceBC, solve
from cavity.thermal.radiation import h_rad_linearized

# 64-node Gauss-Legendre on (0, 1), reused for every spot average.
_GL_NODES, _GL_WEIGHTS = np.polynomial.legendre.leggauss(64)
_U_NODES = 0.5 * (_GL_NODES + 1.0)
_U_WEIGHTS = 0.5 * _GL_WEIGHTS


@dataclass(frozen=True)
class RigConfig:
    """One point of the T2 sweep for one sample (SI units)."""

    sample: SampleConfig
    thickness_m: float
    spot_diameter_m: float
    h_sub_w_m2_k: float
    k_w_m_k: float
    radius_factor: float
    include_radiation: bool = False  # ratified flagged branch, not headline

    @property
    def disc_radius_m(self) -> float:
        return self.sample.disc_radius_m(self.radius_factor)

    @property
    def spot_radius_m(self) -> float:
        return self.spot_diameter_m / 2.0

    @property
    def h_exposed_w_m2_k(self) -> float:
        h = EXPOSED.h_w_m2_k
        if self.include_radiation:
            h += h_rad_linearized(EMISSIVITY_PTP.eps_nominal, AMBIENT.t_inf_k)
        return h


def build_spec(config: RigConfig) -> CylinderSpec:
    if config.spot_radius_m > config.disc_radius_m:
        raise ValueError(
            f"spot radius {config.spot_radius_m} exceeds equivalent disc "
            f"radius {config.disc_radius_m} for sample {config.sample.name}"
        )
    return CylinderSpec(
        radius_m=config.disc_radius_m,
        height_m=config.thickness_m,
        k_r_w_m_k=config.k_w_m_k,
        side=SurfaceBC.robin(config.h_exposed_w_m2_k),
        top=SurfaceBC.robin(config.h_exposed_w_m2_k),
        base=SurfaceBC.robin(config.h_sub_w_m2_k),
    )


def build_source(config: RigConfig, p_w: float = 1.0) -> PumpSource:
    """Top-hat disc, surface deposition (headline branch; l_abs ≪ t)."""
    return PumpSource(
        p_w=p_w,
        axial_form="surface",
        radial_form="disc",
        disc_radius_m=config.spot_radius_m,
    )


def probe_average_dt_k(solution, spot_radius_m: float) -> float:
    """Spot-averaged top-surface rise <ΔT>_spot = (2/a²)∫₀^a ΔT(r,0) r dr.

    Fixed 64-node Gauss-Legendre in r on (0, a); the surface profile is a
    smooth Bessel series, far over-resolved at 64 nodes (pinned against a
    doubled rule in tests)."""
    r = _U_NODES * spot_radius_m
    dt = np.asarray(solution.delta_t(r, np.zeros_like(r)), dtype=float)
    return float(2.0 * np.dot(_U_WEIGHTS, dt * _U_NODES))


def theta_probe_k_per_w(config: RigConfig, n_modes: int = 64) -> float:
    """The reduced observable Θ_probe = <ΔT>_spot per absorbed watt (K/W)."""
    solution = solve(build_spec(config), build_source(config, p_w=1.0), n_modes=n_modes)
    return probe_average_dt_k(solution, config.spot_radius_m)


@dataclass(frozen=True)
class SweepResult:
    """Θ_probe over the T2 grid for one sample.

    `theta_k_per_w[i_shared, i_thickness]` with the shared axis flattened in
    C order over (spot, h_sub, k, radius_factor) — the same shared flat
    index for both samples, which is what the T4 ratio pairs on."""

    sample_name: str
    grid: SweepGrid
    theta_k_per_w: np.ndarray  # shape (n_shared, n_thickness)

    def shared_axes(self) -> list[tuple[float, float, float, float]]:
        """(spot_diameter, h_sub, k, radius_factor) per shared flat index."""
        return [
            (w, h, k, f)
            for w in self.grid.spot_diameter_m
            for h in self.grid.h_sub_w_m2_k
            for k in self.grid.k_w_m_k
            for f in self.grid.radius_factor
        ]


def sweep_sample(
    sample: SampleConfig,
    grid: SweepGrid,
    include_radiation: bool = False,
    n_modes: int = 64,
) -> SweepResult:
    """Run the T2 sweep for one sample. Cost: n_shared × n_thickness closed-
    form solves (no COMSOL, no licence)."""
    thetas = np.empty((grid.n_shared, len(grid.thickness_m)))
    i = 0
    for w in grid.spot_diameter_m:
        for h in grid.h_sub_w_m2_k:
            for k in grid.k_w_m_k:
                for f in grid.radius_factor:
                    for j, t in enumerate(grid.thickness_m):
                        config = RigConfig(
                            sample=sample,
                            thickness_m=t,
                            spot_diameter_m=w,
                            h_sub_w_m2_k=h,
                            k_w_m_k=k,
                            radius_factor=f,
                            include_radiation=include_radiation,
                        )
                        thetas[i, j] = theta_probe_k_per_w(config, n_modes=n_modes)
                    i += 1
    return SweepResult(sample_name=sample.name, grid=grid, theta_k_per_w=thetas)
