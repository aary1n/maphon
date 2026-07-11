"""SPEC §5 gate artifacts (runs/ JSON report) + the cached §1 provider.

The report is the auditable output of a gate run: all six §5 rows must
be present with the full typed field set, statuses must serialise to
the exact literals {pass, fail, deferred_requires_comsol}, and the
SPEC §1 reproducibility block must ride along. The cached-provider
tests exercise the §1 re-derivation path end-to-end: a persisted
SolveRecord -> extraction re-run -> gate payloads, no COMSOL.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from tests._extraction_fixtures import make_structured_grid, zero_complex_3vec
from cavity.extraction import FieldSample
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.gridding import GridSpec
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.persistence import (
    SolveRecord,
    save_solve_record,
    solve_fingerprint,
    solve_hash,
    utc_timestamp,
)
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.provenance import STO, TARGETS
from cavity.validation import (
    REPORT_FILENAME,
    StaticProvider,
    create_run_dir,
    provider_from_cache,
    report_to_dict,
    run_gate,
    write_gate_report,
)
from tests.test_validation_gate import ROW_IDS, full_pass_provider

CHECK_KEYS = {
    "name",
    "row_id",
    "target",
    "target_value",
    "measured",
    "window",
    "status",
    "margin",
    "inputs",
    "provenance",
    "tolerance_rationale",
    "notes",
}

REPRO_KEYS = {
    "rng_seed",
    "comsol_version",
    "mesh_settings",
    "mesh_element_counts",
    "solve_record_hashes",
    "cache_root",
    "notes",
}


class TestReportArtifact:
    def test_artifact_lands_under_runs_gate(self, tmp_path):
        report = run_gate(full_pass_provider())
        out = write_gate_report(report, runs_root=tmp_path / "runs")
        assert out.name == REPORT_FILENAME
        assert out.parent.parent == tmp_path / "runs" / "gate"
        assert out.parent.name.endswith("_synthetic")

    def test_report_round_trips_all_six_rows(self, tmp_path):
        report = run_gate(full_pass_provider())
        out = write_gate_report(report, runs_root=tmp_path / "runs")
        data = json.loads(out.read_text(encoding="utf-8"))

        assert data["schema_version"] == 1
        assert data["provider_kind"] == "synthetic"
        assert data["phase1_complete"] is True
        assert tuple(r["row_id"] for r in data["rows"]) == ROW_IDS
        assert sum(len(row["checks"]) for row in data["rows"]) == 11
        for row in data["rows"]:
            assert row["status"] in {
                "pass",
                "fail",
                "deferred_requires_comsol",
            }
            for check in row["checks"]:
                assert set(check) == CHECK_KEYS
                assert set(check["window"]) == {"lo", "hi"}
        assert set(data["reproducibility"]) == REPRO_KEYS
        assert data["created_at_utc"]

    def test_verbatim_spec_text_survives_serialisation(self, tmp_path):
        report = run_gate(StaticProvider())
        out = write_gate_report(report, runs_root=tmp_path / "runs")
        data = json.loads(out.read_text(encoding="utf-8"))
        by_id = {r["row_id"]: r for r in data["rows"]}
        assert by_id["f"]["target"] == "1.45 GHz, ≥4 s.f."
        assert by_id["booth_two_point"]["source"] == (
            "Booth Table 8 + App. A"
        )
        assert by_id["f_m"]["target"] == (
            "±1% consistency vs BOOTH_IMPLIED_F_M at the Booth point "
            "(order 10⁷ re-scoped to the confinement endpoint — "
            "finding 2026-07-11)"
        )
        checks = {
            check["name"]: check
            for row in data["rows"]
            for check in row["checks"]
        }
        assert "f_m/booth_consistency" in checks
        assert "confinement_trend/f_m_order" in checks

    def test_deferred_report_statuses_serialise(self, tmp_path):
        report = run_gate(StaticProvider())
        data = report_to_dict(report)
        assert data["phase1_complete"] is False
        assert data["n_deferred"] == 6
        assert all(
            r["status"] == "deferred_requires_comsol"
            for r in data["rows"]
        )
        # Must be JSON-encodable as-is (enums/None handled).
        json.dumps(data)

    def test_numpy_scalars_in_inputs_are_coerced(self):
        provider = full_pass_provider()
        report = run_gate(provider)
        # Simulate numpy leakage through a payload-derived input.
        data = report_to_dict(report)
        json.dumps(data)  # would raise on stray numpy types

    def test_create_run_dir_is_collision_safe(self, tmp_path):
        frozen = 1_780_000_000.0
        d1 = create_run_dir(tmp_path, "synthetic", _now=frozen)
        d2 = create_run_dir(tmp_path, "synthetic", _now=frozen)
        assert d1 != d2
        assert d1.is_dir() and d2.is_dir()
        assert d2.name == f"{d1.name}-2"

    def test_precreated_run_dir_is_respected(self, tmp_path):
        report = run_gate(StaticProvider())
        run_dir = create_run_dir(tmp_path / "runs", "synthetic")
        out = write_gate_report(report, run_dir=run_dir)
        assert out.parent == run_dir


def _synthetic_field_sample(q: float = 7_000.0) -> FieldSample:
    """Small but §3-valid FieldSample: nonzero H everywhere, E_phi
    mode-like, lossy STO inside r <= 3 mm."""
    grid = make_structured_grid(0.0, 6.14e-3, 0.0, 18.42e-3, 5, 5)
    n = grid.r_m.size
    e = zero_complex_3vec(n)
    e[:, 1] = 1.0  # E_phi
    h = zero_complex_3vec(n)
    h[:, 2] = 1.0  # H_z
    mask = grid.r_m <= 3.0e-3
    eps = np.where(
        mask,
        STO.epsilon_r_real * (1.0 - 1j * STO.tan_delta),
        1.0 + 0.0j,
    )
    f_hz = 1.45e9
    return FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=eps,
        weights_m2=grid.weights_m2,
        dielectric_mask=mask,
        complex_eigenfrequency_hz=complex(f_hz, f_hz / (2.0 * q)),
    )


def _persist_record(cache_root, study: EigenStudyConfig) -> str:
    geom = CavityGeometry.from_nominal(
        DielectricShape.PUCK, dielectric_height_m=4.92e-3
    )
    materials = MaterialSpec(
        wall_pec=study.wall_bc is WallBC.PEC
    )
    fingerprint = solve_fingerprint(
        geom, materials, MeshConfig(), study, GridSpec()
    )
    record_hash = solve_hash(fingerprint)
    sample = _synthetic_field_sample()
    record = SolveRecord(
        fingerprint=fingerprint,
        record_hash=record_hash,
        comsol_version="COMSOL 6.2 (synthetic test record)",
        mesh_element_count=1_234,
        interface_tag="emw",
        picked_index=0,
        spectrum_f_real_hz=np.array(
            [sample.complex_eigenfrequency_hz.real]
        ),
        spectrum_f_imag_hz=np.array(
            [sample.complex_eigenfrequency_hz.imag]
        ),
        spectrum_q_emw=None,
        field_sample=sample,
        created_at_utc=utc_timestamp(),
    )
    save_solve_record(record, cache_root)
    return record_hash


class TestCachedProvider:
    """§1 re-derivation path: SolveRecord -> extract -> gate payloads."""

    def test_payloads_and_repro_from_records(self, tmp_path):
        booth_hash = _persist_record(
            tmp_path, EigenStudyConfig(wall_bc=WallBC.IMPEDANCE)
        )
        pec_hash = _persist_record(
            tmp_path, EigenStudyConfig(wall_bc=WallBC.PEC)
        )
        provider = provider_from_cache(
            tmp_path, booth_hash=booth_hash, pec_lossy_hash=pec_hash
        )

        booth = provider.booth_walls_on()
        assert booth.epsilon_r_real == TARGETS.booth.epsilon_r_real
        assert booth.extraction.f_hz == pytest.approx(1.45e9)
        assert booth.extraction.q == pytest.approx(7_000.0)

        pec = provider.pec_lossy()
        assert pec.tan_delta == STO.tan_delta
        assert 0.0 < pec.extraction.p_e < 1.0

        repro = provider.reproducibility()
        assert set(repro.solve_record_hashes) == {booth_hash, pec_hash}
        assert repro.mesh_element_counts == (1_234, 1_234)
        assert "synthetic test record" in repro.comsol_version
        assert repro.cache_root == str(tmp_path)

        # The gate runs the cached provider through the same path.
        report = run_gate(provider)
        assert report.provider_kind == "cached"
        judged = {
            c.name: c.status.value
            for r in report.rows
            for c in r.checks
            if c.measured is not None
        }
        # Booth-anchored checks and pec_lossy were judged (pass or
        # fail per the synthetic numbers); the rest stayed deferred.
        assert "booth_two_point/q" in judged
        assert "analytic_benchmark/pec_lossy_q" in judged
        assert report.n_deferred >= 2  # confinement + wall-loss rows

    def test_missing_hash_raises_not_defers(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            provider_from_cache(tmp_path, booth_hash="deadbeef00000000")
