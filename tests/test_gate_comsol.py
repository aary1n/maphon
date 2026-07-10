"""SPEC §5 gate, live tier (requires_comsol): the same gate code path
fed by real solves.

Wired live: the §8 empty-cavity TE011 anchor, the §8 PEC + lossy
closed check, and — since the 2026-07-10 geometry recovery — the
Booth-geometry rows (f / Booth two-point / wall-loss split / F_m) via
the §5a wall-loss study at the recovered torus.

The Booth ladder is fed from the FROZEN §5a archive
(refs/gate_runs/20260710T083340Z_live_comsol) as the solve cache: the
gate re-judges through the full live code path while every ladder
solve cache-hits (§1 re-derivation — extraction re-runs from the
persisted raw fields). This also pins the ARCHIVED VERDICTS: the
2026-07-10 run is a GATED FAIL (V_mode global-max ×1.60 high, F_m
below 1e7 as its arithmetic consequence) with f, Q and the §4 split
PASSING — the committed failure record is booth_5a_checkpoint.md in
the archive. Only the confinement-trend row still defers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cavity.provenance import EXTRACTION_TOL
from cavity.validation import (
    CheckStatus,
    LiveComsolProvider,
    create_run_dir,
    run_gate,
    write_gate_report,
)

pytestmark = pytest.mark.requires_comsol

RUN_5A_SOLVES = (
    Path(__file__).resolve().parent.parent
    / "refs"
    / "gate_runs"
    / "20260710T083340Z_live_comsol"
    / "solves"
)
# faithful-branch walls-on finest record of the §5a archive
_BOOTH_IMP_FINEST = "2b276c4424e49bb9"
_LFS_POINTER_PREFIX = b"version https://git-lfs"


def _booth_cache_or_skip() -> Path:
    """The frozen §5a solve cache, or skip — a cache MISS here would
    re-solve live and write fresh records into the frozen archive."""
    fields = RUN_5A_SOLVES / _BOOTH_IMP_FINEST / "fields.npz"
    if not fields.is_file():
        pytest.skip(
            f"§5a archive not present at {RUN_5A_SOLVES} — "
            "refs/gate_runs missing from this checkout"
        )
    with open(fields, "rb") as fh:
        head = fh.read(len(_LFS_POINTER_PREFIX))
    if head.startswith(_LFS_POINTER_PREFIX):
        pytest.skip(
            "§5a archive npz is an unsmudged git-lfs pointer — run "
            "`git lfs pull` (a cache miss would re-solve into the "
            "frozen archive)"
        )
    return RUN_5A_SOLVES


@pytest.fixture(scope="module")
def live_run(comsol_client, tmp_path_factory):
    booth_cache = _booth_cache_or_skip()
    runs_root = tmp_path_factory.mktemp("runs")
    run_dir = create_run_dir(runs_root, "live_comsol")
    provider = LiveComsolProvider(
        comsol_client,
        solve_root=run_dir / "solves",
        booth_cache_root=booth_cache,
    )
    report = run_gate(provider)
    return report, run_dir


def _check(report, name):
    return next(
        c for row in report.rows for c in row.checks if c.name == name
    )


class TestLiveGate:
    def test_te011_check_judged_live_and_passes(self, live_run):
        report, _ = live_run
        te011 = _check(report, "analytic_benchmark/te011")
        assert te011.status is CheckStatus.PASS
        assert te011.measured is not None
        assert te011.margin > 0.0

    def test_pec_lossy_check_judged_live_and_passes(self, live_run):
        report, _ = live_run
        check = _check(report, "analytic_benchmark/pec_lossy_q")
        assert check.status is CheckStatus.PASS
        assert check.measured is not None
        assert check.measured < EXTRACTION_TOL.q_pec_lossy_rel_tol
        assert check.margin > 0.0
        # Real solve inputs were recorded, not synthetic defaults.
        assert 0.0 < check.inputs["p_e"] < 1.0
        assert check.inputs["tan_delta"] == pytest.approx(1.1e-4)
        assert "numerical-residual headroom" in check.notes

    def test_analytic_benchmark_row_passes_outright(self, live_run):
        report, _ = live_run
        by_id = {row.row_id: row for row in report.rows}
        assert by_id["analytic_benchmark"].status is CheckStatus.PASS

    def test_booth_rows_reproduce_archived_verdicts(self, live_run):
        """The 2026-07-10 §5a verdicts, re-judged through the live gate
        path from the frozen records: f/Q/split PASS, V_mode and F_m
        FAIL — the committed red result, not a deferral."""
        report, _ = live_run
        by_id = {row.row_id: row for row in report.rows}
        assert by_id["f"].status is CheckStatus.PASS
        assert by_id["booth_two_point"].status is CheckStatus.FAIL
        assert by_id["wall_loss_split"].status is CheckStatus.PASS
        assert by_id["f_m"].status is CheckStatus.FAIL
        assert by_id["confinement_trend"].status is CheckStatus.DEFERRED

        f_check = _check(report, "f/f_at_booth_geometry")
        assert f_check.measured == pytest.approx(1450382242.55, rel=1e-9)
        q_check = _check(report, "booth_two_point/q")
        assert q_check.status is CheckStatus.PASS
        assert q_check.measured == pytest.approx(6981.316, rel=1e-6)
        v_check = _check(report, "booth_two_point/v_mode")
        assert v_check.status is CheckStatus.FAIL
        assert v_check.measured == pytest.approx(6.5578e-07, rel=1e-4)
        wall = _check(report, "wall_loss_split/wall_fraction")
        assert wall.measured == pytest.approx(0.26601, rel=1e-4)
        fm = _check(report, "f_m/order_of_magnitude")
        assert fm.status is CheckStatus.FAIL
        assert fm.measured == pytest.approx(7.1443e6, rel=1e-4)

        assert not report.phase1_complete
        assert report.n_pass == 3
        assert report.n_fail == 2
        assert report.n_deferred == 1

    def test_spec_1_reproducibility_recorded(self, live_run):
        report, run_dir = live_run
        repro = report.reproducibility
        assert repro.comsol_version
        assert repro.mesh_element_counts
        assert all(n > 0 for n in repro.mesh_element_counts)
        assert repro.mesh_settings
        assert "booth_impedance" in repro.mesh_settings
        assert "booth_pec" in repro.mesh_settings
        # Raw complex eigensolutions persisted (SPEC §1): the TE011
        # spectrum npz + the fresh PEC+lossy SolveRecord land under
        # the run dir; the Booth ladder records are the frozen §5a
        # archive (cache hits — nothing rewritten there).
        solves = run_dir / "solves"
        assert (solves / "empty_cavity_te011.npz").is_file()
        # hashes: booth impedance finest, booth pec finest, pec_lossy
        assert len(repro.solve_record_hashes) == 3
        assert repro.solve_record_hashes[0] == _BOOTH_IMP_FINEST
        pec_lossy_hash = repro.solve_record_hashes[2]
        record_dir = solves / pec_lossy_hash
        assert (record_dir / "meta.json").is_file()
        assert (record_dir / "fields.npz").is_file()

    def test_artifact_written(self, live_run):
        report, run_dir = live_run
        out = write_gate_report(report, run_dir=run_dir)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["provider_kind"] == "live_comsol"
        assert len(data["rows"]) == 6
        assert data["n_fail"] == 2
        assert data["reproducibility"]["solve_record_hashes"]
