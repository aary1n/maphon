"""SPEC §1 persistence tests — raw solves keyed by parameter hash.

The load-bearing property: `extract(loaded.field_sample)` reproduces
the §3 quantities from disk with no COMSOL licence — the re-derivation
path SPEC §1 requires. Plus hash discipline: identical inputs collide,
any physics-relevant perturbation does not.
"""

from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pytest

from cavity.extraction import extract
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.gridding import GridSpec
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.persistence import (
    SolveRecord,
    load_solve_record,
    record_dir,
    save_solve_record,
    solve_fingerprint,
    solve_hash,
    utc_timestamp,
)
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.extraction.fields import FieldSample
from cavity.provenance.constants import STOSingleCrystal

GEOM = CavityGeometry.from_nominal(
    DielectricShape.PUCK, dielectric_height_m=4.92e-3
)
MATERIALS = MaterialSpec()
MESH = MeshConfig()
STUDY = EigenStudyConfig()
GRID_SPEC = GridSpec(n_r=15, n_z=21)


def _synthetic_record(with_q_emw: bool = True) -> SolveRecord:
    """A physically plausible fake solve in the real record schema."""
    grid = GRID_SPEC.build(GEOM.box_radius_m, GEOM.box_height_m)
    mask = GEOM.dielectric_mask(grid.r_m, grid.z_m)
    assert np.any(mask)

    w = 0.4 * GEOM.dielectric_radius_m
    z0 = GEOM.dielectric_centre_z_m
    envelope = np.exp(
        -(grid.r_m**2 + (grid.z_m - z0) ** 2) / (2.0 * w**2)
    )
    e = np.zeros((grid.n_nodes, 3), dtype=np.complex128)
    h = np.zeros((grid.n_nodes, 3), dtype=np.complex128)
    e[:, 1] = grid.r_m * envelope
    h[:, 2] = envelope
    eps = np.where(
        mask, MATERIALS.sto_complex_eps_r, complex(1.0, 0.0)
    ).astype(np.complex128)

    spectrum_re = np.array([3.02e9, 3.11e9, 3.35e9])
    spectrum_im = np.array([1.9e5, 1.7e5, 2.4e5])
    picked = 1
    f_picked = complex(spectrum_re[picked], spectrum_im[picked])
    q_emw = spectrum_re / (2.0 * spectrum_im) if with_q_emw else None

    field_sample = FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=eps,
        weights_m2=grid.weights_m2,
        dielectric_mask=mask,
        complex_eigenfrequency_hz=f_picked,
        q_emw_cross_check=float(q_emw[picked]) if with_q_emw else None,
    )
    fingerprint = solve_fingerprint(GEOM, MATERIALS, MESH, STUDY, GRID_SPEC)
    return SolveRecord(
        fingerprint=fingerprint,
        record_hash=solve_hash(fingerprint),
        comsol_version="COMSOL 6.2 (synthetic)",
        mesh_element_count=12_345,
        interface_tag="emw",
        picked_index=picked,
        spectrum_f_real_hz=spectrum_re,
        spectrum_f_imag_hz=spectrum_im,
        spectrum_q_emw=q_emw,
        field_sample=field_sample,
        created_at_utc=utc_timestamp(),
        diagnostics=[
            {
                "f_real_hz": 3.11e9,
                "f_imag_hz": 1.7e5,
                "azimuthal_e_energy_fraction": 1.0,
                "axis_hz_antinode_ratio": 1.0,
                "axis_hz_sign_changes": 0,
            }
        ],
    )


class TestRoundTrip:
    def test_layout_and_metadata(self, tmp_path):
        record = _synthetic_record()
        out = save_solve_record(record, tmp_path)
        assert out == record_dir(tmp_path, record.record_hash)
        assert (out / "meta.json").is_file()
        assert (out / "fields.npz").is_file()

        loaded = load_solve_record(tmp_path, record.record_hash)
        assert loaded is not None
        assert loaded.fingerprint == record.fingerprint
        assert loaded.record_hash == record.record_hash
        assert loaded.comsol_version == record.comsol_version
        assert loaded.mesh_element_count == record.mesh_element_count
        assert loaded.interface_tag == record.interface_tag
        assert loaded.picked_index == record.picked_index
        assert loaded.created_at_utc == record.created_at_utc
        assert loaded.diagnostics == record.diagnostics
        assert (
            loaded.complex_eigenfrequency_hz
            == record.complex_eigenfrequency_hz
        )

    def test_arrays_roundtrip_exactly(self, tmp_path):
        record = _synthetic_record()
        save_solve_record(record, tmp_path)
        loaded = load_solve_record(tmp_path, record.record_hash)
        assert np.array_equal(
            loaded.spectrum_f_real_hz, record.spectrum_f_real_hz
        )
        assert np.array_equal(
            loaded.spectrum_f_imag_hz, record.spectrum_f_imag_hz
        )
        assert np.array_equal(loaded.spectrum_q_emw, record.spectrum_q_emw)
        for name in (
            "r_m",
            "z_m",
            "e_complex",
            "h_complex",
            "eps_r_complex",
            "weights_m2",
            "dielectric_mask",
        ):
            assert np.array_equal(
                getattr(loaded.field_sample, name),
                getattr(record.field_sample, name),
            ), name

    def test_extraction_rederivation_without_comsol(self, tmp_path):
        """SPEC §1: extraction re-runs from the persisted raw fields."""
        record = _synthetic_record()
        original = extract(record.field_sample)
        save_solve_record(record, tmp_path)
        loaded = load_solve_record(tmp_path, record.record_hash)
        rederived = extract(loaded.field_sample)
        assert rederived == original

    def test_q_emw_none_roundtrips_as_none(self, tmp_path):
        record = _synthetic_record(with_q_emw=False)
        save_solve_record(record, tmp_path)
        loaded = load_solve_record(tmp_path, record.record_hash)
        assert loaded.spectrum_q_emw is None
        assert loaded.field_sample.q_emw_cross_check is None
        assert loaded.field_sample.gain_region_mask is None


class TestCacheMissBehaviour:
    def test_missing_hash_returns_none(self, tmp_path):
        assert load_solve_record(tmp_path, "0" * 16) is None

    def test_incomplete_record_returns_none(self, tmp_path):
        record = _synthetic_record()
        out = save_solve_record(record, tmp_path)
        (out / "fields.npz").unlink()
        assert load_solve_record(tmp_path, record.record_hash) is None

    def test_schema_mismatch_returns_none(self, tmp_path):
        record = _synthetic_record()
        out = save_solve_record(record, tmp_path)
        meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
        meta["fingerprint"]["schema_version"] = -1
        (out / "meta.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
        assert load_solve_record(tmp_path, record.record_hash) is None


class TestHashDiscipline:
    def _base_fingerprint(self):
        return solve_fingerprint(GEOM, MATERIALS, MESH, STUDY, GRID_SPEC)

    def test_identical_inputs_collide(self):
        assert solve_hash(self._base_fingerprint()) == solve_hash(
            solve_fingerprint(GEOM, MATERIALS, MESH, STUDY, GRID_SPEC)
        )

    def test_every_physics_input_perturbs_the_hash(self):
        base = solve_hash(self._base_fingerprint())
        perturbed = [
            solve_fingerprint(
                CavityGeometry.from_nominal(
                    DielectricShape.PUCK, dielectric_height_m=5.0e-3
                ),
                MATERIALS,
                MESH,
                STUDY,
                GRID_SPEC,
            ),
            solve_fingerprint(
                CavityGeometry.from_nominal(
                    DielectricShape.TORUS, dielectric_minor_radius_m=2.0e-3
                ),
                MATERIALS,
                MESH,
                STUDY,
                GRID_SPEC,
            ),
            solve_fingerprint(
                GEOM,
                replace(
                    MATERIALS, sto=STOSingleCrystal(tan_delta=2.0e-4)
                ),
                MESH,
                STUDY,
                GRID_SPEC,
            ),
            solve_fingerprint(
                GEOM, MATERIALS, MESH.refined(2.0), STUDY, GRID_SPEC
            ),
            solve_fingerprint(
                GEOM,
                replace(MATERIALS, wall_pec=True),
                MESH,
                replace(STUDY, wall_bc=WallBC.PEC),
                GRID_SPEC,
            ),
            solve_fingerprint(
                GEOM, MATERIALS, MESH, replace(STUDY, n_modes=9), GRID_SPEC
            ),
            solve_fingerprint(
                GEOM, MATERIALS, MESH, STUDY, GridSpec(n_r=16, n_z=21)
            ),
        ]
        hashes = [solve_hash(fp) for fp in perturbed]
        assert base not in hashes
        assert len(set(hashes)) == len(hashes), "perturbations collided"
