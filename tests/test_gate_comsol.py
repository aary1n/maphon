"""SPEC §5 gate, live tier (requires_comsol): the same gate code path
fed by real solves.

Wired live: the §8 empty-cavity TE011 anchor (the exact build path of
TestAnalyticBenchmarkAnchor in test_forward_model_comsol.py) and the
§8 PEC + lossy-dielectric closed check (geometry-independent, so it
runs at the assumed a/L = 0.5 puck through run_forward_model — the
full §1 SolveRecord persists under solves/). With both sub-checks
judged live, the analytic-benchmark row must PASS outright.

Everything blocked on SPEC §11 gap #1 (f, Booth two-point, wall-loss
split) and the §7 sweep (confinement trend) must report
deferred_requires_comsol, never fail, never silently vanish. The
Booth Table 8 numerical gate remains the strict xfail in
test_wall_loss_gate.py.
"""

from __future__ import annotations

import json

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


@pytest.fixture(scope="module")
def live_run(comsol_client, tmp_path_factory):
    runs_root = tmp_path_factory.mktemp("runs")
    run_dir = create_run_dir(runs_root, "live_comsol")
    provider = LiveComsolProvider(
        client=comsol_client, solve_root=run_dir / "solves"
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

    def test_blocked_rows_defer_not_fail(self, live_run):
        report, _ = live_run
        by_id = {row.row_id: row for row in report.rows}
        for row_id in (
            "f",
            "booth_two_point",
            "confinement_trend",
            "wall_loss_split",
            "f_m",
        ):
            assert by_id[row_id].status is CheckStatus.DEFERRED
        assert not report.phase1_complete
        assert report.n_pass == 1
        assert report.n_deferred == 5

    def test_spec_1_reproducibility_recorded(self, live_run):
        report, run_dir = live_run
        repro = report.reproducibility
        assert repro.comsol_version
        assert repro.mesh_element_counts
        assert all(n > 0 for n in repro.mesh_element_counts)
        assert repro.mesh_settings
        # Raw complex eigensolutions persisted (SPEC §1): the TE011
        # spectrum npz plus the PEC+lossy full SolveRecord.
        solves = run_dir / "solves"
        assert (solves / "empty_cavity_te011.npz").is_file()
        assert len(repro.solve_record_hashes) == 1
        record_dir = solves / repro.solve_record_hashes[0]
        assert (record_dir / "meta.json").is_file()
        assert (record_dir / "fields.npz").is_file()

    def test_artifact_written(self, live_run):
        report, run_dir = live_run
        out = write_gate_report(report, run_dir=run_dir)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["provider_kind"] == "live_comsol"
        assert len(data["rows"]) == 6
        assert data["reproducibility"]["solve_record_hashes"]
