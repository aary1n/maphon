"""L2 driver — per-draw pipeline, RAW-only row store (allowlist +
derived-key deny-list), audit keys, and the CLI's two tiers.
"""

from __future__ import annotations

import json

import pytest

from cavity.export.schema import REQUIRED_SUMMARY_KEYS, validate_bundle
from cavity.sweep.backend import MockBackend
from cavity.sweep.design import DesignBlock, generate_design
from cavity.sweep.dofs import (
    DesignMode,
    ResolutionContext,
    Rung,
    SentinelResolution,
    UnresolvedTodoTraceError,
    mock_resolutions,
)
from cavity.sweep.driver import (
    DESIGN_ROW_KEYS,
    RawRowContractError,
    append_raw_row,
    load_raw_rows,
    main,
    run_sweep,
    validate_raw_row,
)

SEED = 20260715


@pytest.fixture(scope="module")
def mock_run(tmp_path_factory):
    design = generate_design(
        DesignMode.BASELINE_D8,
        DesignBlock.TRAINING,
        mock_resolutions(),
        seed=SEED,
        n_draws=4,
    )
    out = tmp_path_factory.mktemp("sweep_run")
    return design, run_sweep(design, MockBackend(), out)


def test_run_sweep_writes_manifest_rows_and_bundles(mock_run):
    design, result = mock_run
    assert result.n_rows == 4
    assert result.raw_rows_path.is_file()
    assert result.manifest_path.is_file()
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["design"]["any_mock"] is True
    assert manifest["backend"] == "MockBackend"
    assert len(result.bundle_dirs) == 4


def test_bundles_are_schema_valid(mock_run):
    _, result = mock_run
    bundle = validate_bundle(result.bundle_dirs[0])
    # Mock bundles are honest schema examples, never physics.
    assert bundle.meta["summary"]["gain_mask_is_fallback"] is True
    assert any("SCHEMA EXAMPLE" in n for n in bundle.meta["status_notes"])


def test_rows_carry_exactly_the_raw_contract(mock_run):
    design, result = mock_run
    rows = load_raw_rows(result.raw_rows_path)
    assert len(rows) == 4
    for row in rows:
        for key in REQUIRED_SUMMARY_KEYS:
            assert key in row
        for key in DESIGN_ROW_KEYS:
            assert key in row
        theta_keys = {k for k in row if k.startswith("theta_")}
        assert theta_keys == {
            f"theta_{name}" for name in design.dim_names
        }
        # nothing beyond the contract
        assert set(row) == (
            set(REQUIRED_SUMMARY_KEYS)
            | set(DESIGN_ROW_KEYS)
            | theta_keys
        )
        assert row["design_mock"] is True


def test_row_audit_chain_reaches_the_bundle(mock_run):
    design, result = mock_run
    rows = load_raw_rows(result.raw_rows_path)
    row = rows[2]
    bundle_dir = result.out_root / row["bundle_dir"]
    meta = json.loads(
        (bundle_dir / "export_meta.json").read_text(encoding="utf-8")
    )
    # SPEC §1 audit: row record_hash == bundle record_hash.
    assert row["record_hash"] == meta["summary"]["record_hash"]
    assert row["design_row_hash"] == design.row_hash(row["design_draw_index"])


# ---------------------------------------------------------------------------
# RAW-only contract — refusal pairs
# ---------------------------------------------------------------------------


def _valid_row(mock_run) -> dict:
    _, result = mock_run
    return dict(load_raw_rows(result.raw_rows_path)[0])


def test_derived_keys_are_refused_by_name(mock_run):
    row = _valid_row(mock_run)
    row["kappa_c_hz"] = 2.6e5
    with pytest.raises(RawRowContractError, match="law-agnosticism"):
        validate_raw_row(row)
    row = _valid_row(mock_run)
    row["c0"] = 190.0
    with pytest.raises(RawRowContractError, match="RAW"):
        validate_raw_row(row)


def test_unknown_keys_are_refused(mock_run):
    row = _valid_row(mock_run)
    row["surprise_column"] = 1.0
    with pytest.raises(RawRowContractError, match="outside the raw-row"):
        validate_raw_row(row)


def test_missing_schema_or_audit_keys_refused(mock_run):
    row = _valid_row(mock_run)
    del row["magnetic_filling_factor"]
    with pytest.raises(RawRowContractError, match="missing schema"):
        validate_raw_row(row)
    row = _valid_row(mock_run)
    del row["design_row_hash"]
    with pytest.raises(RawRowContractError, match="audit key"):
        validate_raw_row(row)


def test_append_raw_row_validates_before_writing(tmp_path, mock_run):
    path = tmp_path / "raw_rows.jsonl"
    bad = _valid_row(mock_run)
    bad["delta_f_max_hz"] = 1.0
    with pytest.raises(RawRowContractError):
        append_raw_row(path, bad)
    assert not path.exists()  # refused before any bytes hit disk


# ---------------------------------------------------------------------------
# Real-design paths through run_sweep
# ---------------------------------------------------------------------------


def _real_q9_context() -> ResolutionContext:
    """Hypothetical real Q9 + Q13 (the two d = 7 DOF rows); Q11 stays
    unresolved so the rider-R1 gate is what the tests below hit."""
    return ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q9",
                payload={
                    # MOCK axial-offset values (hypothetical, test only)
                    "crystal_axial_offset_nominal_m": 0.5e-3,
                    "crystal_axial_offset_band_m": (0.45e-3, 0.55e-3),
                    "centring_tolerance_m": 50e-6,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
            SentinelResolution(
                question_id="Q13",
                payload={
                    "sto_height_m": 8.6e-3,
                    "selection_evidence": "hypothetical (test only)",
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
        )
    )


def test_run_sweep_real_design_requires_context(tmp_path):
    ctx = _real_q9_context()
    design = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED
    )
    with pytest.raises(ValueError, match="ResolutionContext"):
        run_sweep(design, MockBackend(), tmp_path)


def test_run_sweep_real_design_hits_the_q11_gate(tmp_path):
    ctx = _real_q9_context()
    design = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED
    )
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        run_sweep(design, MockBackend(), tmp_path, context=ctx)
    assert exc.value.question_ids == ("Q11",)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_comsol_refuses_today(capsys):
    assert main(["--comsol", "--mode", "d8"]) == 2
    err = capsys.readouterr().err
    assert "REFUSED" in err and "Q2" in err and "Q11" in err


def test_cli_mock_dry_run_end_to_end(tmp_path, capsys):
    rc = main(
        [
            "--mock",
            "--mode",
            "d8",
            "--n",
            "16",
            "--n-held-out",
            "4",
            "--seed",
            str(SEED),
            "--out",
            str(tmp_path / "dry"),
        ]
    )
    assert rc == 0
    report = json.loads(
        (tmp_path / "dry" / "dry_run_report.json").read_text()
    )
    assert report["tier"].startswith("MOCK DRY RUN")
    assert report["n_training"] == 16 and report["n_held_out"] == 4
    # Rider R1: the gate report prints its κs branch.
    assert report["cv_gate"]["kappa_s_branch"] == "point"
    assert report["cv_gate"]["kappa_s_hz"] == 1.4e6
    assert "r4_projection_invariance" in report
    assert (tmp_path / "dry" / "derived_rows.jsonl").is_file()
