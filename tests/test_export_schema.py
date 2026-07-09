"""Export bundle contract (`cavity.export`) — schema §C/§D reference tests.

Round-trip bit-identity, validation refusals (version mismatch, missing
keys, broken invariants), metadata completeness (incl. the git_commit +
git_dirty reproducibility pair), and the end-to-end path from a cached
§1 SolveRecord — synthetic TE011 records for licence-free CI, plus the
frozen gate record (LFS npz, skip-with-reason if unsmudged). The writer
is a pure function of a SolveRecord: a COMSOL licence is needed only to
mint records, never to export.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from cavity.export import (
    EXPORT_SCHEMA_VERSION,
    FIELDS_FILENAME,
    META_FILENAME,
    REQUIRED_ARRAY_KEYS,
    REQUIRED_META_KEYS,
    REQUIRED_SUMMARY_KEYS,
    SCHEMA_DOC_FILENAME,
    SchemaValidationError,
    SchemaVersionError,
    export_bundle,
    load_bundle,
    validate_bundle,
)
from cavity.extraction import (
    FieldSample,
    SpinProjection,
    electric_filling_factor,
    extract,
    spin_arm_weight,
)
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.gridding import GridSpec, structured_grid
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.persistence import (
    SolveRecord,
    load_solve_record,
    save_solve_record,
    solve_fingerprint,
    solve_hash,
)
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.validation.analytic_fields import TE011Mode, te011_fields

from tests._gate_record_fixture import GATE_P_E, gate_record_or_skip

MODE = TE011Mode(radius_m=6.14e-3, length_m=18.42e-3)
N_R, N_Z = 81, 121


def _synthetic_record(with_gain_mask: bool = True) -> SolveRecord:
    """A schema-valid §1 SolveRecord built on closed-form TE011 fields.

    The fingerprint is a real `solve_fingerprint` (so hashing and the
    grid block behave exactly like production records); the arrays are
    the analytic vacuum fields with a synthetic Im(f), which is all the
    export contract needs. Materials in the fingerprint describe the
    nominal solve, not the vacuum arrays — this record tests the
    SCHEMA, not solver physics.
    """
    geom = CavityGeometry(
        dielectric_shape=DielectricShape.PUCK,
        box_radius_m=MODE.radius_m,
        box_height_m=MODE.length_m,
        dielectric_radius_m=2.46e-3,
        dielectric_height_m=4.92e-3,
    )
    study = EigenStudyConfig(
        wall_bc=WallBC.PEC, search_hz=MODE.f_hz, n_modes=3
    )
    materials = MaterialSpec(wall_pec=True)
    grid_spec = GridSpec(n_r=N_R, n_z=N_Z)
    fingerprint = solve_fingerprint(
        geom, materials, MeshConfig(), study, grid_spec
    )

    grid = structured_grid(MODE.radius_m, MODE.length_m, N_R, N_Z)
    e, h = te011_fields(MODE, grid.r_m, grid.z_m)
    tiny = 1.0e-12
    dielectric_mask = grid.r_m <= MODE.radius_m / 2.0 + tiny
    gain_mask = (
        (grid.r_m <= 0.3 * MODE.radius_m + tiny)
        & (grid.z_m >= 0.3 * MODE.length_m - tiny)
        & (grid.z_m <= 0.7 * MODE.length_m + tiny)
    )
    picked = 1
    f_real = np.array([0.8 * MODE.f_hz, MODE.f_hz, 1.3 * MODE.f_hz])
    f_imag = np.array(
        [MODE.f_hz / 1.0e4, MODE.f_hz / 2.0e4, MODE.f_hz / 3.0e4]
    )
    field = FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=np.ones(grid.r_m.size, dtype=np.complex128),
        weights_m2=grid.weights_m2,
        dielectric_mask=dielectric_mask,
        complex_eigenfrequency_hz=complex(f_real[picked], f_imag[picked]),
        gain_region_mask=gain_mask if with_gain_mask else None,
    )
    return SolveRecord(
        fingerprint=fingerprint,
        record_hash=solve_hash(fingerprint),
        comsol_version="none (synthetic analytic record)",
        mesh_element_count=1,
        interface_tag="emw",
        picked_index=picked,
        spectrum_f_real_hz=f_real,
        spectrum_f_imag_hz=f_imag,
        spectrum_q_emw=None,
        field_sample=field,
        created_at_utc="2026-07-09T00:00:00+00:00",
        diagnostics=None,
    )


@pytest.fixture()
def bundle_dir(tmp_path):
    return export_bundle(_synthetic_record(), tmp_path / "bundle")


class TestExportRoundTrip:
    def test_bundle_files_written(self, bundle_dir):
        assert (bundle_dir / FIELDS_FILENAME).is_file()
        assert (bundle_dir / META_FILENAME).is_file()
        assert (bundle_dir / SCHEMA_DOC_FILENAME).is_file()

    def test_validate_passes_and_round_trips(self, bundle_dir):
        bundle = validate_bundle(bundle_dir)
        assert bundle.meta["export_schema_version"] == EXPORT_SCHEMA_VERSION
        assert set(REQUIRED_ARRAY_KEYS) <= set(bundle.arrays)

    def test_arrays_bit_identical_to_source(self, bundle_dir):
        """Round trip preserves the arrays bit-for-bit: the stored
        fields are exactly source x the unit-energy scale factor."""
        record = _synthetic_record()
        bundle = load_bundle(bundle_dir)
        raw_total = bundle.meta["normalisation"]["raw_total_energy_j"]
        scale = 1.0 / np.sqrt(raw_total)
        field = record.field_sample
        assert np.array_equal(bundle.arrays["r_m"], field.r_m)
        assert np.array_equal(bundle.arrays["weights_m2"], field.weights_m2)
        assert np.array_equal(
            bundle.arrays["e_complex"], field.e_complex * scale
        )
        assert np.array_equal(
            bundle.arrays["h_complex"], field.h_complex * scale
        )
        assert np.array_equal(
            bundle.arrays["dielectric_mask"], field.dielectric_mask
        )
        assert np.array_equal(
            bundle.arrays["gain_region_mask"], field.gain_region_mask
        )
        assert np.array_equal(
            bundle.arrays["spectrum_f_real_hz"], record.spectrum_f_real_hz
        )

    def test_unit_energy_invariant(self, bundle_dir):
        """U_E + U_H recomputed from the stored arrays equals 1 J —
        the schema doc §5 normalisation declaration, from-file."""
        from scipy.constants import epsilon_0, mu_0

        from cavity.extraction.quadrature import axisymmetric_volume_integral

        b = load_bundle(bundle_dir)
        e2 = np.sum(np.abs(b.arrays["e_complex"]) ** 2, axis=1)
        h2 = np.sum(np.abs(b.arrays["h_complex"]) ** 2, axis=1)
        u_e = (
            epsilon_0
            / 4.0
            * axisymmetric_volume_integral(
                np.real(b.arrays["eps_r_complex"]) * e2,
                b.arrays["r_m"],
                b.arrays["weights_m2"],
            ).real
        )
        u_h = (
            mu_0
            / 4.0
            * axisymmetric_volume_integral(
                h2, b.arrays["r_m"], b.arrays["weights_m2"]
            ).real
        )
        assert u_e + u_h == pytest.approx(1.0, rel=1.0e-12)

    def test_u_e_fraction_half_at_resonance(self, bundle_dir):
        """TE011 closed-form fields: U_E = U_H, so the stored fraction
        sits at 0.5 to quadrature accuracy — the mode-health check."""
        meta = load_bundle(bundle_dir).meta
        assert meta["normalisation"]["u_e_fraction"] == pytest.approx(
            0.5, abs=1.0e-4
        )

    def test_deterministic_overwrite(self, bundle_dir):
        """Re-exporting the same record to the same dir reproduces the
        arrays exactly (timestamps/git state are runtime facts)."""
        before = load_bundle(bundle_dir)
        export_bundle(_synthetic_record(), bundle_dir)
        after = load_bundle(bundle_dir)
        for key in REQUIRED_ARRAY_KEYS:
            assert np.array_equal(before.arrays[key], after.arrays[key])


class TestMetadataCompleteness:
    def test_required_meta_and_summary_keys(self, bundle_dir):
        meta = load_bundle(bundle_dir).meta
        assert set(REQUIRED_META_KEYS) <= set(meta)
        assert set(REQUIRED_SUMMARY_KEYS) <= set(meta["summary"])

    def test_summary_matches_extraction(self, bundle_dir):
        record = _synthetic_record()
        extraction = extract(record.field_sample)
        summary = load_bundle(bundle_dir).meta["summary"]
        assert summary["q"] == pytest.approx(extraction.q, rel=1.0e-14)
        assert summary["p_e"] == pytest.approx(extraction.p_e, rel=1.0e-14)
        assert summary["p_e"] == pytest.approx(
            electric_filling_factor(record.field_sample), rel=1.0e-14
        )
        assert summary["v_mode_global_m3"] == pytest.approx(
            extraction.v_mode_global_m3, rel=1.0e-14
        )
        assert summary["f_real_hz"] == float(
            record.spectrum_f_real_hz[record.picked_index]
        )

    def test_git_state_recorded(self, bundle_dir):
        """Amendment: git_commit AND git_dirty both present. In this
        test environment git exists, so both must be real values —
        a 40-hex commit and a bool (nulls only when git is absent)."""
        exporter = load_bundle(bundle_dir).meta["exporter"]
        assert "git_commit" in exporter and "git_dirty" in exporter
        commit = exporter["git_commit"]
        dirty = exporter["git_dirty"]
        assert isinstance(commit, str) and len(commit) == 40
        assert isinstance(dirty, bool)
        if dirty:
            assert any(
                "DIRTY" in note for note in load_bundle(bundle_dir).meta[
                    "status_notes"
                ]
            )

    def test_mode_selection_block(self, bundle_dir):
        sel = load_bundle(bundle_dir).meta["mode_selection"]
        assert "field-symmetry" in sel["method"]
        assert set(sel["criteria"]) == {
            "min_azimuthal_e_energy_fraction",
            "min_axis_hz_antinode_ratio",
            "max_axis_hz_sign_changes",
            "axis_noise_floor_fraction",
        }
        assert "picked_index" in sel["picked_index_semantics"]

    def test_gain_fallback_labelling(self, tmp_path):
        """No Phase-1b gain mask => fallback flag + SCHEMA EXAMPLE note;
        with a real mask => neither."""
        fallback_dir = export_bundle(
            _synthetic_record(with_gain_mask=False), tmp_path / "fallback"
        )
        meta = load_bundle(fallback_dir).meta
        assert meta["summary"]["gain_mask_is_fallback"] is True
        assert any("SCHEMA EXAMPLE" in n for n in meta["status_notes"])
        # gain mask is still ALWAYS materialised in the arrays:
        arrays = load_bundle(fallback_dir).arrays
        assert np.array_equal(
            arrays["gain_region_mask"], arrays["dielectric_mask"]
        )

        masked_dir = export_bundle(
            _synthetic_record(with_gain_mask=True), tmp_path / "masked"
        )
        meta2 = load_bundle(masked_dir).meta
        assert meta2["summary"]["gain_mask_is_fallback"] is False
        assert not any("SCHEMA EXAMPLE" in n for n in meta2["status_notes"])

    def test_projection_recorded_and_applied(self, tmp_path):
        """Exporting with axis_projected(1) stores that projection and
        the |H_z|^2-only weight."""
        record = _synthetic_record()
        out = export_bundle(
            record,
            tmp_path / "projected",
            projection=SpinProjection.axis_projected(1.0),
        )
        bundle = validate_bundle(out)
        proj_meta = bundle.meta["weights"]["w_spin_per_m3"]["projection"]
        assert proj_meta["mode"] == "axis_projected"
        assert proj_meta["components"] == [[1.0, 1.0]]
        expected = spin_arm_weight(
            record.field_sample, SpinProjection.axis_projected(1.0)
        ).weight.values_per_m3
        assert np.array_equal(bundle.arrays["w_spin_per_m3"], expected)


class TestValidationRefusals:
    def test_version_mismatch_refused(self, bundle_dir):
        meta_path = bundle_dir / META_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["export_schema_version"] = EXPORT_SCHEMA_VERSION + 1
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        with pytest.raises(SchemaVersionError, match="Refusing"):
            load_bundle(bundle_dir)

    def test_missing_files_refused(self, tmp_path):
        with pytest.raises(SchemaValidationError, match=META_FILENAME):
            load_bundle(tmp_path)

    def test_missing_schema_doc_copy_refused(self, bundle_dir):
        (bundle_dir / SCHEMA_DOC_FILENAME).unlink()
        with pytest.raises(SchemaValidationError, match="self-contained"):
            validate_bundle(bundle_dir)

    def test_missing_array_key_refused(self, bundle_dir):
        with np.load(bundle_dir / FIELDS_FILENAME) as data:
            arrays = {k: data[k] for k in data.files if k != "w_e_per_m3"}
        np.savez_compressed(bundle_dir / FIELDS_FILENAME, **arrays)
        with pytest.raises(SchemaValidationError, match="w_e_per_m3"):
            validate_bundle(bundle_dir)

    def test_broken_normalisation_refused(self, bundle_dir):
        with np.load(bundle_dir / FIELDS_FILENAME) as data:
            arrays = {k: np.array(data[k]) for k in data.files}
        arrays["e_complex"] = arrays["e_complex"] * 1.01
        np.savez_compressed(bundle_dir / FIELDS_FILENAME, **arrays)
        with pytest.raises(SchemaValidationError, match="unit-energy"):
            validate_bundle(bundle_dir)

    def test_tampered_picked_mode_refused(self, bundle_dir):
        meta_path = bundle_dir / META_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["summary"]["f_real_hz"] = 1.0e9
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        with pytest.raises(
            SchemaValidationError, match="spectrum\\[picked_index\\]"
        ):
            validate_bundle(bundle_dir)

    def test_weight_outside_mask_refused(self, bundle_dir):
        with np.load(bundle_dir / FIELDS_FILENAME) as data:
            arrays = {k: np.array(data[k]) for k in data.files}
        w = arrays["w_spin_per_m3"].copy()
        outside = ~arrays["gain_region_mask"]
        w[np.argmax(outside)] = 1.0
        arrays["w_spin_per_m3"] = w
        np.savez_compressed(bundle_dir / FIELDS_FILENAME, **arrays)
        with pytest.raises(SchemaValidationError, match="outside"):
            validate_bundle(bundle_dir)


class TestFromCachedRecord:
    def test_export_from_persisted_record_round_trip(self, tmp_path):
        """The §1 re-derivation path end-to-end WITHOUT COMSOL: save a
        record with the persistence layer, load it back, export, and
        validate — the writer is a pure function of the SolveRecord."""
        record = _synthetic_record()
        save_solve_record(record, tmp_path / "solves")
        loaded = load_solve_record(tmp_path / "solves", record.record_hash)
        assert loaded is not None
        out = export_bundle(loaded, tmp_path / "bundle")
        bundle = validate_bundle(out)
        assert bundle.meta["solve"]["record_hash"] == record.record_hash

    def test_export_from_frozen_gate_record(self, tmp_path):
        """End-to-end from the frozen licence-session artifact: the
        exported bundle validates, its p_e closes the loop against the
        gate report's 0.9976566720273174, and the picked mode is
        consumed from the record — never re-selected."""
        record = gate_record_or_skip()
        out = export_bundle(record, tmp_path / "gate_bundle")
        bundle = validate_bundle(out)
        summary = bundle.meta["summary"]
        assert summary["p_e"] == pytest.approx(GATE_P_E, rel=1.0e-12)
        assert summary["f_real_hz"] == float(
            record.spectrum_f_real_hz[record.picked_index]
        )
        assert summary["f_imag_hz"] == float(
            record.spectrum_f_imag_hz[record.picked_index]
        )
        assert bundle.meta["solve"]["picked_index"] == record.picked_index
        assert summary["record_hash"] == record.record_hash
        # Pre-Phase-1b: fallback flagged, SCHEMA EXAMPLE + PEC notes on.
        assert summary["gain_mask_is_fallback"] is True
        notes = " ".join(bundle.meta["status_notes"])
        assert "SCHEMA EXAMPLE" in notes and "PEC" in notes
        # emw.Qfactor cross-check rode through extraction unharmed.
        assert summary["q_emw_cross_check"] == pytest.approx(
            record.field_sample.q_emw_cross_check, rel=1.0e-12
        )
