"""Publication build guards (publication/build.py).

Two tiers: unit tests of the stage functions (synthetic inputs, temp
dirs), and live checks against the real repo that pin the CURRENT honest
state — most importantly that publication readiness is REFUSED. When the
science genuinely unblocks, re-scope the refusal pin deliberately, in the
same changeset as the unblocking evidence (repo discipline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from publication.build import (
    BuildGuardError,
    ContractCheck,
    _assert_outside_protected,
    check_contract,
    claim_status,
    compose_verdicts,
    git_stamp,
    load_claims,
    sentinel_status,
    verify_archives,
    ArchiveStatus,
    RegenResult,
)

REPO = Path(__file__).resolve().parent.parent


class TestPathGuard:
    @pytest.mark.parametrize(
        "target",
        [
            "thermal/reports/x.md",
            "calibration/reports/x.json",
            "docs/figures/f1.png",
            "paper/claim_evidence_matrix.md",
            "refs/gate_runs/x",
            "calibration/data/raw/x",
        ],
    )
    def test_protected_dirs_refused(self, target):
        with pytest.raises(BuildGuardError, match="committed artifact tree"):
            _assert_outside_protected(REPO / target)

    def test_runs_dir_allowed(self, tmp_path):
        assert _assert_outside_protected(tmp_path / "build")


class TestLiveStages:
    def test_archives_verify(self):
        status = verify_archives()
        assert status.ok, status.detail
        assert "cowley_semple_2026-07-14" in status.per_archive
        assert "oxborrow_tuning_2026-07-16" in status.per_archive

    def test_git_stamp_shape(self):
        stamp = git_stamp()
        assert len(stamp.head_sha) == 40
        assert stamp.branch  # detached HEAD would fail loudly elsewhere

    def test_contract_check_clean_on_live_repo(self):
        contract = yaml.safe_load(
            (REPO / "paper" / "figure_contract.yaml").read_text(encoding="utf-8")
        )
        check = check_contract(contract)
        assert check.ok, check.problems

    def test_sentinel_status_names_open_questions(self):
        # 2026-07-21 register change: Q13 + Q2 ratified (in-person
        # measurements, written confirmation pending — provenance
        # corrected 2026-07-22) — Q9 is the sole open gate and the fork
        # line renders the register-derived "resolved" branch.
        status = sentinel_status()
        assert set(status.unresolved_by_mode["baseline-d8"]) == {"Q9"}
        assert set(status.unresolved_by_mode["degraded-d7"]) == {"Q9"}
        assert status.ratified == ("Q2", "Q11", "Q13")
        assert status.fork_state == "Q13 resolved"
        # F3 ruling (2026-07-20): the favoured branch is never named in a
        # publication-facing artifact — still negative-pinned.
        assert "favoured" not in status.fork_state.lower()

    def test_claim_status_live(self):
        claims = load_claims()
        status = claim_status(claims)
        assert status.n_claims >= 15
        assert set(status.headline_blocked) == {"C1", "C2", "C9", "C10"}
        assert "C2" in status.supervisor_unratified


class TestVerdictComposition:
    def _clean_inputs(self):
        archives = ArchiveStatus(ok=True, per_archive={"a": True}, detail="ok")
        regen = [RegenResult("X", True, True, "byte-identical to committed")]
        contract = ContractCheck(ok=True, problems=())
        sentinels = sentinel_status()
        return archives, regen, contract, sentinels

    def test_readiness_refused_while_headline_blocked(self):
        archives, regen, contract, sentinels = self._clean_inputs()
        claims = claim_status(load_claims())
        verdicts = compose_verdicts(archives, regen, contract, sentinels, claims)
        assert verdicts.artifact_reproducibility == "PASS"
        assert not verdicts.headline_ready
        assert verdicts.publication_readiness.startswith("REFUSED")
        # the four statuses are genuinely separated: repro PASS while
        # readiness REFUSED is the expected honest state today
        assert "incomplete evidence chains" in verdicts.publication_readiness

    def test_reproducibility_fail_propagates(self):
        archives, _, contract, sentinels = self._clean_inputs()
        regen = [RegenResult("X", True, False, "DRIFT")]
        claims = claim_status(load_claims())
        verdicts = compose_verdicts(archives, regen, contract, sentinels, claims)
        assert verdicts.artifact_reproducibility.startswith("FAIL")

    def test_synthetic_ready_state_flips_verdict(self):
        """A synthetic all-complete claim set with ALL sentinels resolved
        DOES produce READY — the refusal is data-driven, not hardcoded.
        (Adversarial-review re-scope: readiness now ALSO requires no
        unresolved sentinel and no unratified headline claim, so the
        synthetic state must resolve the sentinels too.)"""
        from publication.build import SentinelStatus

        archives, regen, contract, _ = self._clean_inputs()
        resolved_sentinels = SentinelStatus(
            unresolved_by_mode={"baseline-d8": (), "degraded-d7": ()},
            fork_state="Q13 resolved",
            ratified=("Q2", "Q9", "Q11", "Q13"),
            named_items={},
        )
        synthetic = [
            {
                "id": "S1",
                "headline": True,
                "category": ["derived"],
                "evidence_chain": "complete",
            }
        ]
        verdicts = compose_verdicts(
            archives,
            regen,
            contract,
            resolved_sentinels,
            claim_status(synthetic),
        )
        assert verdicts.headline_ready
        assert verdicts.publication_readiness.startswith("READY")

    def test_live_sentinels_block_readiness_even_with_complete_chains(self):
        """Negative pin (adversarial-review BLOCKER fix): complete
        headline chains do NOT suffice while Q2/Q9/Q13 are open."""
        archives, regen, contract, sentinels = self._clean_inputs()
        synthetic = [
            {
                "id": "S1",
                "headline": True,
                "category": ["derived"],
                "evidence_chain": "complete",
            }
        ]
        verdicts = compose_verdicts(
            archives, regen, contract, sentinels, claim_status(synthetic)
        )
        assert not verdicts.headline_ready
        assert "unresolved sentinels" in verdicts.publication_readiness

    def test_unratified_headline_blocks_readiness(self):
        from publication.build import SentinelStatus

        archives, regen, contract, _ = self._clean_inputs()
        resolved = SentinelStatus(
            unresolved_by_mode={"baseline-d8": (), "degraded-d7": ()},
            fork_state="Q13 resolved",
            ratified=("Q2", "Q9", "Q11", "Q13"),
            named_items={},
        )
        synthetic = [
            {
                "id": "S1",
                "headline": True,
                "category": ["derived", "supervisor-unratified"],
                "evidence_chain": "complete",
            }
        ]
        verdicts = compose_verdicts(
            archives, regen, contract, resolved, claim_status(synthetic)
        )
        assert not verdicts.headline_ready
        assert "unratified HEADLINE" in verdicts.publication_readiness

    def test_skipped_regeneration_caps_at_partial(self):
        """A skip is not a failure but is NOT the advertised full check
        either (adversarial-review fix): reproducibility caps at PARTIAL
        and readiness therefore stays refused."""
        archives, _, contract, sentinels = self._clean_inputs()
        regen = [RegenResult("X", False, None, "skipped (--skip-figures)")]
        claims = claim_status(load_claims())
        verdicts = compose_verdicts(archives, regen, contract, sentinels, claims)
        assert verdicts.artifact_reproducibility.startswith("PARTIAL")
        assert not verdicts.headline_ready


class TestCheapRegeneration:
    def test_turnover_report_regenerates_content_identical(self, tmp_path):
        """One end-to-end regeneration through the real recipe path: the
        cheapest byte-pinned generator must reproduce the committed
        content (newline-normalised) into a temp build dir."""
        from publication.build import regenerate_artifacts

        contract = {
            "artifacts": [
                {
                    "id": "R-turnover",
                    "path": "thermal/reports/q_margin_turnover.md",
                    "kind": "generated",
                    "generator": "cavity.thermal.report_turnover",
                    "byte_pinned": True,
                }
            ]
        }
        results = regenerate_artifacts(
            contract, tmp_path / "build", include_figures=False, include_slow=True
        )
        assert len(results) == 1
        assert results[0].regenerated
        assert results[0].matches_committed is True, results[0].detail

    def test_regeneration_never_touches_committed_reports(self, tmp_path):
        from publication.build import regenerate_artifacts

        committed = REPO / "thermal" / "reports" / "q_margin_turnover.md"
        before = committed.read_bytes()
        regenerate_artifacts(
            {
                "artifacts": [
                    {
                        "id": "R-turnover",
                        "path": "thermal/reports/q_margin_turnover.md",
                        "kind": "generated",
                        "generator": "cavity.thermal.report_turnover",
                        "byte_pinned": True,
                    }
                ]
            },
            tmp_path / "b2",
            include_figures=False,
            include_slow=True,
        )
        assert committed.read_bytes() == before


class TestDraftMode:
    def test_draft_labels_but_does_not_change_readiness(self, tmp_path):
        """--draft generates labelled outputs despite blockers; the
        readiness verdict is computed identically."""
        from publication.build import run_build

        build_dir, verdicts = run_build(
            build_root=tmp_path / "root",
            include_figures=False,
            include_slow=False,
            run_pins=False,  # executing the full pin set inside a test
            # would recurse pytest; the skip is surfaced as PARTIAL
            draft=True,
        )
        assert (build_dir / "DRAFT").is_file()
        assert "DRAFT MODE" in (build_dir / "build_report.md").read_text(
            encoding="utf-8"
        )
        assert verdicts.publication_readiness.startswith("REFUSED")
        report = json.loads(
            (build_dir / "build_report.json").read_text(encoding="utf-8")
        )
        assert report["draft"] is True
        assert (build_dir / "artifact_index.json").is_file()
