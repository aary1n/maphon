"""SPEC §2 end-to-end on a live COMSOL licence (requires_comsol tier).

Nominal Booth puck geometry with a stated dielectric-height assumption
(gap #1, SPEC §11): height = 2 x radius (a/L = 0.5). The Kajfez
first-order estimate then puts TE01delta near ~3.1 GHz — NOT 1.45 GHz;
at the Booth radius (2.46 mm) no puck height reaches 1.45 GHz, which is
exactly the under-specified-cross-section gap §4 exists to close. The
search frequency here follows the physics estimate; the Booth Table 8
two-point gate lives separately in test_wall_loss_gate.py and stays
xfail until the real cross-section is pinned.

What this tier proves (the §2 definition of done):
  - build -> mesh -> solve -> field export -> mode-ID -> EXISTING §3
    extract() runs end-to-end and yields f, Q, V_mode (both variants),
    p_e, F_m;
  - the §1 cache short-circuits an identical re-run;
  - the convergence ladder reaches the asymptotic regime and emits a
    valid sigma;
  - the §4 wall-loss decomposition runs on the Impedance + PEC pair
    (smoke_test label: path sanity, not published-number validation).

The mesh ladder is deliberately coarse (COMSOL-time budget); the finest
ladder level is reused by the e2e solve via the cache.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from cavity.forward_model.build import build_model
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.gridding import GridSpec
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.runner import (
    run_convergence_study,
    run_forward_model,
    run_wall_loss_study,
)
from cavity.forward_model.solve import evaluate_eigen_spectrum
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.provenance import GEOM, STO, TARGETS
from cavity.provenance.constants import STOSingleCrystal
from cavity.validation.analytic import f_te_mnp

pytestmark = pytest.mark.requires_comsol

# a/L = 0.5 assumption for the unpinned Booth puck height (gap #1).
PUCK_HEIGHT_M = 2.0 * GEOM.dielectric_radius_m
# Kajfez estimate f[GHz] ~ (34 / (a[mm] sqrt(eps_r))) (a/L + 3.45).
KAJFEZ_HZ = (
    34.0
    / (GEOM.dielectric_radius_m * 1e3 * math.sqrt(STO.epsilon_r_real))
    * (0.5 + 3.45)
    * 1e9
)
SEARCH_HZ = 3.1e9
N_MODES = 12

BASE_MESH = MeshConfig(dielectric_max_h_m=5.0e-4, air_max_h_m=2.0e-3)
REFINE_FACTOR = 2.0
N_LEVELS = 3
FINEST_MESH = BASE_MESH.refined(REFINE_FACTOR ** (N_LEVELS - 1))
GRID_SPEC = GridSpec()


@pytest.fixture(scope="module")
def cache_root(tmp_path_factory):
    return tmp_path_factory.mktemp("solve_cache")


@pytest.fixture(scope="module")
def geom():
    return CavityGeometry.from_nominal(
        DielectricShape.PUCK, dielectric_height_m=PUCK_HEIGHT_M
    )


@pytest.fixture(scope="module")
def study():
    return EigenStudyConfig(
        wall_bc=WallBC.IMPEDANCE, search_hz=SEARCH_HZ, n_modes=N_MODES
    )


@pytest.fixture(scope="module")
def nominal_result(comsol_client, geom, study, cache_root):
    return run_forward_model(
        geom,
        study,
        mesh_cfg=FINEST_MESH,
        grid_spec=GRID_SPEC,
        client=comsol_client,
        cache_root=cache_root,
    )


class TestEndToEndExtraction:
    def test_all_section3_quantities_produced(self, nominal_result):
        ext = nominal_result.extraction
        # Order sanity against the Kajfez estimate — a grossly wrong
        # picked mode lands far outside; mode identity itself is
        # enforced by the field-symmetry filter inside the solve.
        assert 0.5 * KAJFEZ_HZ < ext.f_hz < 1.6 * KAJFEZ_HZ
        assert ext.complex_eigenfrequency_hz.imag > 0.0
        assert 0.0 < ext.q < 5.0e4
        assert 0.0 < ext.v_mode_local_m3 <= ext.v_mode_global_m3
        assert 0.0 < ext.p_e < 1.0
        assert ext.f_m_global > 0.0
        assert ext.f_m_local >= ext.f_m_global  # smaller V -> larger F_m

    def test_run_log_metadata(self, nominal_result):
        record = nominal_result.record
        assert not nominal_result.from_cache
        assert record.mesh_element_count > 0
        assert record.comsol_version
        assert record.interface_tag
        assert 0 <= record.picked_index < len(record.spectrum_f_real_hz)
        assert record.diagnostics  # the audit table rides along
        # The picked entry in the raw spectrum is the extraction's f.
        assert record.complex_eigenfrequency_hz == (
            nominal_result.extraction.complex_eigenfrequency_hz
        )

    def test_cache_short_circuits_resolve(
        self, comsol_client, geom, study, cache_root, nominal_result
    ):
        again = run_forward_model(
            geom,
            study,
            mesh_cfg=FINEST_MESH,
            grid_spec=GRID_SPEC,
            client=comsol_client,
            cache_root=cache_root,
        )
        assert again.from_cache
        assert again.record.record_hash == nominal_result.record.record_hash
        assert again.extraction == nominal_result.extraction


class TestConvergenceStudy:
    def test_ladder_reaches_asymptotic_regime_and_emits_sigma(
        self, comsol_client, geom, study, cache_root
    ):
        result = run_convergence_study(
            geom,
            study,
            base_mesh=BASE_MESH,
            n_levels=N_LEVELS,
            refine_factor=REFINE_FACTOR,
            grid_spec=GRID_SPEC,
            client=comsol_client,
            cache_root=cache_root,
        )
        # run_convergence_study raising ConvergenceError == not
        # asymptotic == this test fails, by design (SPEC §2: no sigma
        # from a non-converged mesh).
        assert result.sigma_q >= 0.0
        assert np.isfinite(result.sigma_q)
        assert result.assessment.sigma_f_imag_hz >= 0.0
        counts = [lvl.mesh_element_count for lvl in result.levels]
        assert all(a < b for a, b in zip(counts, counts[1:])), (
            f"refinement ladder did not grow the mesh: {counts}"
        )
        # Mode re-identified per level: every level's f is TE01delta-
        # adjacent, not a different family member per level.
        f_levels = [
            lvl.complex_eigenfrequency_hz.real for lvl in result.levels
        ]
        assert max(f_levels) - min(f_levels) < 0.1 * min(f_levels)


class TestAnalyticBenchmarkAnchor:
    """SPEC §8 traceability anchor, COMSOL side: the same build path
    that produces every §2 solve must reproduce the closed-form
    empty-cavity TE011 to < 0.1% (Oxborrow 2007 traceable-FEM
    principle; the pure-Python closed forms are CI-tested in
    test_analytic_benchmark.py). The 'dielectric' region is set to
    vacuum so the §2 builder solves a genuinely empty PEC box; the
    lossless spectrum bypasses mode-ID (Im(f) = 0 by construction)."""

    def test_empty_cavity_te011_under_0p1_percent(self, comsol_client):
        f_analytic = f_te_mnp(
            0, 1, 1, GEOM.box_radius_m, GEOM.box_height_m
        )
        geom = CavityGeometry.from_nominal(
            DielectricShape.PUCK, dielectric_height_m=PUCK_HEIGHT_M
        )
        vacuum = MaterialSpec(
            sto=STOSingleCrystal(
                epsilon_r_real=1.0, tan_delta=0.0, mu_r=1.0, sigma=0.0
            ),
            wall_pec=True,
        )
        study = EigenStudyConfig(
            wall_bc=WallBC.PEC, search_hz=f_analytic, n_modes=10
        )
        # ~lambda/24 uniform mesh at the ~30.9 GHz TE011 frequency.
        mesh = MeshConfig(dielectric_max_h_m=4.0e-4, air_max_h_m=4.0e-4)

        built = build_model(geom, vacuum, mesh, study, client=comsol_client)
        try:
            built.model.mesh(built.mesh)
            built.model.solve(built.study)
            spectrum = evaluate_eigen_spectrum(
                built.model, built.interface_tag
            )
        finally:
            try:
                comsol_client.remove(built.model)
            except Exception:
                pass

        rel_errors = np.abs(spectrum.f_real_hz / f_analytic - 1.0)
        assert float(np.min(rel_errors)) < TARGETS.empty_cavity_rel_error_max, (
            f"no eigenmode within 0.1% of closed-form TE011 = "
            f"{f_analytic/1e9:.6f} GHz; spectrum: "
            f"{np.sort(spectrum.f_real_hz)/1e9} GHz"
        )


@pytest.mark.smoke_test
class TestWallLossSmoke:
    """§4 path sanity on the nominal geometry — NOT the Booth Table 8
    validation (that gate stays xfail in test_wall_loss_gate.py)."""

    def test_decomposition_end_to_end(
        self, comsol_client, geom, study, cache_root
    ):
        result = run_wall_loss_study(
            geom,
            study,
            base_mesh=BASE_MESH,
            n_levels=N_LEVELS,
            refine_factor=REFINE_FACTOR,
            grid_spec=GRID_SPEC,
            client=comsol_client,
            cache_root=cache_root,
        )
        d = result.decomposition
        # Strict closed-cavity inequality: removing wall loss raises Q.
        assert d.q_diel > d.q_total
        assert d.q_wall > 0.0
        assert 0.0 < d.wall_fraction < 1.0
        assert d.sigma_q_wall >= 0.0
        # Both arms carried a convergence-residual sigma (never
        # fabricated): they exist because neither ladder raised.
        assert result.impedance.sigma_q >= 0.0
        assert result.pec.sigma_q >= 0.0
        # The two solves found the same mode family (frequencies within
        # a few % — the wall BC perturbs f only weakly).
        f_imp = result.impedance.finest.extraction.f_hz
        f_pec = result.pec.finest.extraction.f_hz
        assert abs(f_imp - f_pec) < 0.05 * f_pec
