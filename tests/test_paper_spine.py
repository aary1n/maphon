"""Paper-spine guards (paper/): schema, cross-reference, and staleness
checks for the claim-evidence matrix, result register, and figure contract.

These tests guard TRACEABILITY, not physics: green means the spine's claims
point at artifacts, code, and tests that exist and still say what the spine
quotes. It does NOT mean any claim is scientifically validated, supervisor-
ratified, or publication-ready — that separation is the whole point of the
spine (and of `publication.build`'s four independent statuses).
"""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
PAPER = REPO / "paper"

MATRIX = PAPER / "claim_evidence_matrix.md"
CONTRACT = PAPER / "figure_contract.yaml"
REGISTER = PAPER / "result_register.md"
OUTLINE = PAPER / "manuscript_outline.md"
ATTACK = PAPER / "reviewer_attack_surface.md"

CATEGORY_VOCAB = {
    "measured",
    "derived",
    "fitted",
    "inferred",
    "planning-grade",
    "supervisor-unratified",
}

REQUIRED_CLAIM_KEYS = {
    "id",
    "title",
    "headline",
    "category",
    "rung",
    "artifacts",
    "producing_code",
    "guarding_tests",
    "evidence_chain",
    "blocker",
    "unlocked_by",
}


def _load_matrix_claims() -> list[dict]:
    text = MATRIX.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    assert len(blocks) == 1, "matrix must carry exactly one fenced yaml register"
    data = yaml.safe_load(blocks[0])
    assert data["schema"] == "paper-claims/v1"
    return data["claims"]


def _load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert data["schema"] == "figure-contract/v1"
    return data


class TestClaimRegister:
    def test_yaml_parses_with_required_keys_and_vocab(self):
        claims = _load_matrix_claims()
        assert len(claims) >= 15
        ids = [c["id"] for c in claims]
        assert len(ids) == len(set(ids)), "duplicate claim ids"
        for c in claims:
            missing = REQUIRED_CLAIM_KEYS - set(c)
            assert not missing, f"{c.get('id')}: missing keys {sorted(missing)}"
            assert isinstance(c["headline"], bool), c["id"]
            assert set(c["category"]) <= CATEGORY_VOCAB, c["id"]
            chain = c["evidence_chain"]
            assert chain == "complete" or chain.startswith("missing:"), c["id"]

    def test_headline_claims_are_currently_blocked(self):
        """Deliberate pin: every headline claim today has an incomplete
        chain (C1/C2/C9/C10). When a headline chain genuinely completes,
        re-scope this test in the same changeset — the repo's standing
        deliberate-re-scope discipline, not a formality."""
        claims = {c["id"]: c for c in _load_matrix_claims()}
        headline = {cid for cid, c in claims.items() if c["headline"]}
        assert headline == {"C1", "C2", "C9", "C10"}
        for cid in headline:
            assert claims[cid]["evidence_chain"].startswith("missing:"), (
                f"{cid} marked headline-complete — if real, re-scope this "
                "test deliberately; if not, the matrix is overclaiming"
            )

    def test_claim_artifact_paths_exist(self):
        for c in _load_matrix_claims():
            for rel in c["artifacts"]:
                assert (REPO / rel).exists(), f"{c['id']}: missing artifact {rel}"

    def test_guarding_test_files_exist(self):
        for c in _load_matrix_claims():
            for entry in c["guarding_tests"]:
                path = entry.split("::")[0]
                assert (REPO / path).exists(), f"{c['id']}: missing test file {path}"

    def test_producing_code_importable(self):
        for c in _load_matrix_claims():
            for mod in c["producing_code"]:
                importlib.import_module(mod)

    def test_verbatim_discipline_sentences_present(self):
        matrix_text = MATRIX.read_text(encoding="utf-8")
        assert "not required and not excluded" in matrix_text
        assert "OPEN EXPOSURE" in ATTACK.read_text(encoding="utf-8")
        outline_text = OUTLINE.read_text(encoding="utf-8")
        assert (
            "no prior\n  work modelled the maser's thermal operating margin"
            in outline_text
            or "no prior work modelled the maser's thermal operating margin"
            in outline_text.replace("\n  ", " ")
        )


class TestFigureContract:
    def test_contract_schema_and_artifacts_exist(self):
        data = _load_contract()
        assert data["artifacts"], "empty contract"
        ids = [a["id"] for a in data["artifacts"]]
        assert len(ids) == len(set(ids)), "duplicate artifact ids"
        for a in data["artifacts"]:
            assert a["kind"] in {"generated", "record"}, a["id"]
            assert (REPO / a["path"]).exists(), f"{a['id']}: missing {a['path']}"
            if a["kind"] == "generated":
                assert a["generator"], f"{a['id']}: generated needs a generator"

    def test_contract_generators_import(self):
        for a in _load_contract()["artifacts"]:
            if a["generator"]:
                importlib.import_module(a["generator"])

    def test_contract_pin_tests_exist(self):
        for a in _load_contract()["artifacts"]:
            for entry in a["pin_tests"]:
                parts = entry.split("::")
                test_file = REPO / parts[0]
                assert test_file.exists(), f"{a['id']}: missing {parts[0]}"
                if len(parts) > 1:
                    assert parts[-1] in test_file.read_text(encoding="utf-8"), (
                        f"{a['id']}: {parts[-1]} not found in {parts[0]}"
                    )

    def test_contract_claim_ids_resolve(self):
        claim_ids = {c["id"] for c in _load_matrix_claims()}
        for a in _load_contract()["artifacts"]:
            for cid in a["claims"]:
                assert cid in claim_ids, f"{a['id']}: unknown claim {cid}"

    def test_required_caveats_present_in_artifacts(self):
        """Text artifacts must carry their caveat tokens verbatim; for
        binary artifacts the token must live in the generator's source
        (captions/status text are code there)."""
        for a in _load_contract()["artifacts"]:
            if not a["required_caveats"]:
                continue
            target = REPO / a["path"]
            if target.suffix in {".md", ".json", ".yaml", ".txt"}:
                haystack = target.read_text(encoding="utf-8")
            else:
                mod = importlib.import_module(a["generator"])
                haystack = Path(mod.__file__).read_text(encoding="utf-8")
            for token in a["required_caveats"]:
                assert token.lower() in haystack.lower(), (
                    f"{a['id']}: required caveat {token!r} absent"
                )


class TestResultRegisterStaleness:
    """Spot-checks that the register still quotes what the live artifacts
    say. Not exhaustive — enough that silent regeneration drift trips CI."""

    def test_turnover_quotes(self):
        text = (REPO / "thermal/reports/q_margin_turnover.md").read_text(
            encoding="utf-8"
        )
        # C0 = 200 era (2026-07-21): quotes track the regenerated
        # turnover report; the register PROSE is stale-flagged for the
        # margin re-presentation follow-on.
        assert "11.6890" in text
        assert "+0.3473" in text
        assert "Q_- = 59.83, Q_+ = 975.9" in text

    def test_s_ladder_quotes(self):
        text = (REPO / "thermal/reports/s_ladder_ballpark.md").read_text(
            encoding="utf-8"
        )
        assert "745.6" in text
        assert "8.88e-16" in text

    def test_feed_quotes(self):
        feed = json.loads(
            (REPO / "calibration/reports/observable_a_feed.json").read_text(
                encoding="utf-8"
            )
        )
        assert feed["t4_ratio_test"]["verdict"] == "geometry-sufficient"
        assert round(feed["t4_ratio_test"]["measured_ratio_d14_over_h14"], 3) == 1.343
        assert round(feed["samples"]["d14"]["heating_at_max_power_k"], 1) == 13.2
        assert round(feed["samples"]["h14"]["heating_at_max_power_k"], 1) == 9.8

    def test_provenance_constant_quotes(self):
        from cavity.provenance.constants import DF_CAVITY_DT, DF_SPIN_DT, KAPPA_S

        assert DF_CAVITY_DT.df_dt_hz_per_k == pytest.approx(2.73e6)
        assert DF_SPIN_DT.df_dt_hz_per_k == pytest.approx(-1.09e5)
        assert KAPPA_S.kappa_s_hz == pytest.approx(1.4e6)
        register_text = REGISTER.read_text(encoding="utf-8")
        assert "+2.73 MHz/K" in register_text
        assert "−109 kHz/K" in register_text
        assert "1.4 MHz" in register_text

    def test_planning_c0_flagged_as_ungraded(self):
        """The claim-trace finding (2026-07-20): PLANNING_C0 = 190 was a
        report-local literal, not a graded constant. RE-SCOPED 2026-07-22
        per this test's own instruction — the constant GRADUATED into
        provenance 2026-07-21 as `C0_PLANNING` = 200.0 (ELICITED /
        supervisor-verbal, notes archived, written confirmation pending):
        the module-level PLANNING_C0 is now an alias of the graded
        constant, and the spine's flag is the graduation record itself.
        The matrix prose still names PLANNING_C0 (stale-flagged for the
        margin re-presentation follow-on)."""
        from cavity.provenance.constants import C0_PLANNING
        from cavity.thermal import report_margin

        assert getattr(report_margin, "PLANNING_C0") == 200
        assert report_margin.PLANNING_C0 == C0_PLANNING.c0
        prov = (REPO / "src/cavity/provenance/constants.py").read_text(
            encoding="utf-8"
        )
        assert "class PlanningCooperativity" in prov
        assert "PLANNING_C0" in MATRIX.read_text(encoding="utf-8")
