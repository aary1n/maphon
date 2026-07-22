"""Reply-ingestion scaffolding guards (cavity.sweep.reply_ingest).

The load-bearing assertions are the REFUSALS: no fixture value can enter
production provenance, resolve a real sentinel, or satisfy a solve-ready
exit; the Q13 fork keeps refusing arithmetic; invented precision and
unit-slips are rejected. The existing refusal-shape tests
(test_sweep_resolutions.py) are deliberately NOT re-scoped — nothing in
this module changes the resolved set (H5).
"""

from __future__ import annotations

import pytest

from cavity.provenance.constants import STO_HEIGHT_FORK
from cavity.sweep.dofs import (
    DesignMode,
    MockResolutionError,
    ResolutionContext,
    Rung,
    UnresolvedTodoTraceError,
)
from cavity.sweep.reply_ingest import (
    DryRunReport,
    ReplyClass,
    ReplyItemError,
    classify_q13,
    classify_q2,
    classify_q9,
    ingest_reply,
    p_tune_from_gap,
    uniform_band_from_informal,
)
from cavity.sweep.resolutions import RATIFIED_RESOLUTIONS, ratified_resolutions

ARCHIVE = "FIXTURE: synthetic transcription (no archive; resolves nothing)"


def _complete_fixture() -> dict:
    return {
        "archive": ARCHIVE,
        "items": {
            "Q13": {
                "height_m": 8.6e-3,
                "question_aware": True,
                "measured": False,
                "quote": "FIXTURE: use 8.6 mm",
            },
            "Q2": {
                "form": "internal_height",
                "nominal_m": 15e-3,
                "min_m": 12e-3,
                "max_m": 20e-3,
                "quote": "FIXTURE: travel 12-20 mm",
            },
            "Q9": {
                "axial_offset_nominal_m": 0.0,
                "axial_offset_band_m": (-0.5e-3, 0.5e-3),
                "centring_tolerance_m": 0.2e-3,
                "quote": "FIXTURE: centred within half a millimetre",
            },
        },
    }


class TestCompleteFixture:
    def test_all_three_full_but_downgraded_to_planning_rung(self):
        """Fixture data NEVER carries a supervisor rung (adversarial-review
        hardening 2026-07-20): outcomes are downgraded to
        PLANNING_ASSUMPTION and mint instructions are fixture-marked with
        FIXTURE-prefixed provenance."""
        report = ingest_reply(_complete_fixture(), fixture=True)
        assert [o.classification for o in report.outcomes] == [
            ReplyClass.FULL,
            ReplyClass.FULL,
            ReplyClass.FULL,
        ]
        assert all(
            o.rung is Rung.PLANNING_ASSUMPTION for o in report.outcomes
        )
        assert len(report.mint_instructions) == 3
        for mi in report.mint_instructions:
            assert mi.fixture
            assert mi.provenance.upper().startswith("FIXTURE")

    def test_fixture_resolves_nothing_real(self):
        """THE guarantee: after a full fixture ingest, the ratified
        register is untouched — Q2/Q11/Q13 as of 2026-07-21 (Q2 + Q13
        in-person measurements, written confirmation pending —
        provenance corrected 2026-07-22), with Q9 the sole remaining
        gate."""
        ingest_reply(_complete_fixture(), fixture=True)
        assert [r.question_id for r in RATIFIED_RESOLUTIONS] == [
            "Q2",
            "Q11",
            "Q13",
        ]
        with pytest.raises(UnresolvedTodoTraceError) as exc:
            ratified_resolutions().assert_solveable(
                DesignMode.BASELINE_D8, "training solves"
            )
        assert set(exc.value.question_ids) == {"Q9"}

    def test_fixture_mocks_are_refused_by_solve_ready_exits(self):
        report = ingest_reply(_complete_fixture(), fixture=True)
        # Mirror of the source's supersede-dedupe (2026-07-21 register
        # change): a re-answered question's stand-in replaces the
        # ratified entry — composing both would be a duplicate.
        minted_qids = {m.question_id for m in report.mint_instructions}
        hypothetical = ResolutionContext(
            resolutions=tuple(
                r
                for r in ratified_resolutions().resolutions
                if r.question_id not in minted_qids
            )
            + tuple(m.as_mock_resolution() for m in report.mint_instructions)
        )
        # presence-wise complete in both modes...
        assert hypothetical.unresolved(DesignMode.BASELINE_D8) == ()
        assert hypothetical.unresolved(DesignMode.DEGRADED_D7) == ()
        # ...and still refused, because every fixture resolution is a mock.
        with pytest.raises(MockResolutionError):
            hypothetical.assert_solveable(DesignMode.BASELINE_D8, "solves")

    def test_mint_instruction_validates_contract_without_registering(self):
        report = ingest_reply(_complete_fixture(), fixture=True)
        for mi in report.mint_instructions:
            mi.validate_contract()  # would raise on a bad payload
        assert [r.question_id for r in RATIFIED_RESOLUTIONS] == [
            "Q2",
            "Q11",
            "Q13",
        ]

    def test_report_markdown_sections_and_fixture_label(self):
        report = ingest_reply(_complete_fixture(), fixture=True)
        text = report.to_markdown()
        assert "FIXTURE" in text
        assert "## What was learned" in text
        assert "## Sentinels remaining unresolved" in text
        assert "## Downstream operations remaining prohibited" in text
        assert "## Work newly licensed" in text
        assert "Nothing below is minted by this tool." in text


class TestPartialFixture:
    def test_partial_reply_classifications(self):
        report = ingest_reply(
            {
                "archive": ARCHIVE,
                "items": {
                    "Q13": {
                        "height_m": 8.6e-3,
                        "question_aware": False,
                        "quote": "FIXTURE: the ring is 8.6 mm tall (summary)",
                    },
                    "Q2": {
                        "form": "gap",
                        "gap_min_m": 5e-3,
                        "gap_max_m": 10e-3,
                        "quote": "FIXTURE: gap 5-10 mm",
                    },
                    "Q9": {
                        "axial_offset_nominal_m": 0.0,
                        "quote": "FIXTURE: roughly mid-height, hand-placed",
                    },
                },
            },
            fixture=True,
        )
        by_q = {o.question_id: o for o in report.outcomes}
        assert by_q["Q13"].classification is ReplyClass.NON_RESPONSIVE
        # 2026-07-21 register change: RESOLUTION_Q13 supplies the height
        # (data-driven, reply_ingest.py's ratified-Q13 fallback), so the
        # gap form is now CONVERTIBLE and the gap-ends-without-nominal
        # rule fires — PARTIAL (never midpoint), no longer
        # DEFERRED_FULL-on-missing-height.
        assert by_q["Q2"].classification is ReplyClass.PARTIAL
        assert by_q["Q9"].classification is ReplyClass.PARTIAL
        assert report.mint_instructions == ()
        unresolved = report.unresolved_after_mint["baseline-d8"]
        assert set(unresolved) == {"Q9"}

    def test_absent_items_are_absent(self):
        report = ingest_reply({"archive": ARCHIVE, "items": {}}, fixture=True)
        assert all(
            o.classification is ReplyClass.ABSENT for o in report.outcomes
        )


class TestQ13Rules:
    def test_question_unaware_never_resolves(self):
        out = classify_q13(
            {"height_m": 8.6e-3, "question_aware": False, "quote": "x"},
            archive_ref=ARCHIVE,
        )
        assert out.classification is ReplyClass.NON_RESPONSIVE
        assert out.payload is None

    def test_caliper_band_rides_payload_only_when_precision_stated(self):
        out = classify_q13(
            {
                "height_m": 8.58e-3,
                "question_aware": True,
                "measured": True,
                "precision_m": 0.02e-3,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert out.payload["sto_height_band_m"] == pytest.approx(
            (8.56e-3, 8.60e-3)
        )

    def test_measured_without_precision_omits_band_key(self):
        out = classify_q13(
            {
                "height_m": 8.58e-3,
                "question_aware": True,
                "measured": True,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert "sto_height_band_m" not in out.payload

    def test_invented_precision_on_written_answer_refused(self):
        with pytest.raises(ReplyItemError, match="precision"):
            classify_q13(
                {
                    "height_m": 8.6e-3,
                    "question_aware": True,
                    "measured": False,
                    "precision_m": 0.05e-3,
                    "quote": "x",
                },
                archive_ref=ARCHIVE,
            )

    def test_off_candidate_measurement_is_legal(self):
        """A caliper value that is NEITHER print candidate supersedes both
        prints (plan §1.1: the validator does not enforce fork membership)."""
        out = classify_q13(
            {
                "height_m": 8.58e-3,
                "question_aware": True,
                "measured": True,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert out.classification is ReplyClass.FULL
        assert out.payload["sto_height_m"] not in STO_HEIGHT_FORK.candidates

    def test_unit_slip_refused_with_units_hint(self):
        with pytest.raises(ReplyItemError, match="units"):
            classify_q13(
                {"height_m": 8.6, "question_aware": True, "quote": "x"},
                archive_ref=ARCHIVE,
            )


class TestQ2Rules:
    def test_gap_form_conversion_arithmetic(self):
        # p_tune = deck 3.0 mm + h + g
        assert p_tune_from_gap(6.4e-3, 8.6e-3) == pytest.approx(18.0e-3)

    def test_gap_form_refuses_the_fork_object(self):
        with pytest.raises(ReplyItemError):
            p_tune_from_gap(6.4e-3, STO_HEIGHT_FORK)  # fork refuses float

    def test_same_reply_q13_feeds_gap_form(self):
        fx = _complete_fixture()
        fx["items"]["Q2"] = {
            "form": "gap",
            "gap_min_m": 5e-3,
            "gap_max_m": 10e-3,
            "gap_nominal_m": 6.4e-3,
            "quote": "FIXTURE: gap 5-10 mm, usually 6.4",
        }
        report = ingest_reply(fx, fixture=True)
        q2 = {o.question_id: o for o in report.outcomes}["Q2"]
        assert q2.classification is ReplyClass.FULL
        assert q2.payload["p_tune_min"] == pytest.approx(3e-3 + 8.6e-3 + 5e-3)
        assert q2.payload["p_tune_max"] == pytest.approx(3e-3 + 8.6e-3 + 10e-3)
        assert q2.payload["p_tune_nominal"] == pytest.approx(
            3e-3 + 8.6e-3 + 6.4e-3
        )

    def test_gap_ends_without_nominal_is_partial_never_midpoint(self):
        """FULL requires nominal + both ends (plan §1.2); a midpoint
        nominal would be OUR invention (adversarial-review fix)."""
        fx = _complete_fixture()
        fx["items"]["Q2"] = {
            "form": "gap",
            "gap_min_m": 5e-3,
            "gap_max_m": 10e-3,
            "quote": "FIXTURE: gap 5-10 mm",
        }
        report = ingest_reply(fx, fixture=True)
        q2 = {o.question_id: o for o in report.outcomes}["Q2"]
        assert q2.classification is ReplyClass.PARTIAL
        assert any("never a silently invented midpoint" in n for n in q2.notes)

    def test_one_ended_internal_height_is_partial_not_error(self):
        out = classify_q2(
            {
                "form": "internal_height",
                "min_m": 12e-3,
                "quote": "can screw it down to 12 mm",
            },
            archive_ref=ARCHIVE,
        )
        assert out.classification is ReplyClass.PARTIAL
        assert any("no invented completion" in n for n in out.notes)

    def test_inverted_travel_refused(self):
        with pytest.raises(ReplyItemError, match="inverted"):
            classify_q2(
                {
                    "form": "internal_height",
                    "nominal_m": 15e-3,
                    "min_m": 20e-3,
                    "max_m": 12e-3,
                    "quote": "x",
                },
                archive_ref=ARCHIVE,
            )

    def test_non_15mm_nominal_notes_d3(self):
        out = classify_q2(
            {
                "form": "internal_height",
                "nominal_m": 18e-3,
                "min_m": 12e-3,
                "max_m": 20e-3,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert any("D3" in n for n in out.notes)

    def test_uncommitted_travel_stays_partial_with_d2_note(self):
        out = classify_q2({"quote": "typical 5-10 mm"}, archive_ref=ARCHIVE)
        assert out.classification is ReplyClass.PARTIAL
        assert any("D2" in n for n in out.notes)

    def test_screw_turns_always_partial_no_symmetric_reading(self):
        """The ±turns·pitch/2 symmetric reading was OUR convention, not
        ratified — retired (adversarial-review fix). Screw answers are
        mechanism colour regardless of stated pitch."""
        for item in (
            {"form": "screw_turns", "turns": 10, "quote": "x"},
            {
                "form": "screw_turns",
                "turns": 10,
                "pitch_m": 0.5e-3,
                "nominal_m": 15e-3,
                "quote": "x",
            },
        ):
            out = classify_q2(item, archive_ref=ARCHIVE)
            assert out.classification is ReplyClass.PARTIAL
            assert any("no symmetric" in n for n in out.notes)

    def test_gap_depth_rider_lands_in_payload_with_h1_note(self):
        out = classify_q2(
            {
                "form": "internal_height",
                "nominal_m": 15e-3,
                "min_m": 12e-3,
                "max_m": 20e-3,
                "piston_gap_depth_m": 2e-3,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert out.payload["piston_gap_depth_m"] == pytest.approx(2e-3)
        assert any("H1" in n for n in out.notes)


class TestQ9Rules:
    def test_informal_slack_covering_both_resolves_via_d5(self):
        out = classify_q9(
            {
                "informal_slack_m": 1e-3,
                "slack_covers_both": True,
                "nominal_m": 0.0,
                "quote": "give or take a millimetre",
            },
            archive_ref=ARCHIVE,
        )
        assert out.classification is ReplyClass.FULL
        assert out.payload["crystal_axial_offset_band_m"] == pytest.approx(
            (-1e-3, 1e-3)
        )
        assert out.payload["centring_tolerance_m"] == pytest.approx(1e-3)

    def test_slack_covering_one_coordinate_mints_nothing(self):
        out = classify_q9(
            {
                "informal_slack_m": 1e-3,
                "slack_covers_both": False,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert out.classification is ReplyClass.PARTIAL

    def test_informal_slack_without_explicit_nominal_refused(self):
        """No physical default: the transcriber must state the nominal
        (0.0 only when the reply itself says centred) — adversarial-review
        fix for the silent 0.0 default."""
        with pytest.raises(ReplyItemError, match="nominal_m"):
            classify_q9(
                {
                    "informal_slack_m": 1e-3,
                    "slack_covers_both": True,
                    "quote": "give or take a millimetre",
                },
                archive_ref=ARCHIVE,
            )

    def test_uniform_band_requires_quote_and_positive_slack(self):
        with pytest.raises(ReplyItemError):
            uniform_band_from_informal(0.0, 1e-3, "  ")
        with pytest.raises(ReplyItemError):
            uniform_band_from_informal(0.0, -1e-3, "quote")

    def test_inverted_band_refused(self):
        with pytest.raises(ReplyItemError, match="inverted"):
            classify_q9(
                {
                    "axial_offset_nominal_m": 0.0,
                    "axial_offset_band_m": (0.5e-3, -0.5e-3),
                    "centring_tolerance_m": 0.1e-3,
                    "quote": "x",
                },
                archive_ref=ARCHIVE,
            )

    def test_full_resolution_carries_h2_schedule_note(self):
        out = classify_q9(
            {
                "axial_offset_nominal_m": 0.0,
                "axial_offset_band_m": (-0.5e-3, 0.5e-3),
                "centring_tolerance_m": 0.2e-3,
                "quote": "x",
            },
            archive_ref=ARCHIVE,
        )
        assert any("H2" in n for n in out.notes)


class TestTranscriptionGuards:
    def test_missing_archive_ref_refused(self):
        with pytest.raises(ReplyItemError, match="archive"):
            ingest_reply({"items": {}}, fixture=True)

    def test_fixture_without_marker_refused(self):
        with pytest.raises(ReplyItemError, match="FIXTURE"):
            ingest_reply(
                {"archive": "calibration/data/raw/nope/", "items": {}},
                fixture=True,
            )

    def test_missing_quote_refused_everywhere(self):
        for qid, item in (
            ("Q13", {"height_m": 8.6e-3, "question_aware": True}),
            ("Q2", {"form": "internal_height"}),
            ("Q9", {"axial_offset_nominal_m": 0.0}),
        ):
            with pytest.raises(ReplyItemError, match="quote"):
                ingest_reply(
                    {"archive": ARCHIVE, "items": {qid: item}}, fixture=True
                )

    def test_report_type(self):
        assert isinstance(
            ingest_reply({"archive": ARCHIVE, "items": {}}, fixture=True),
            DryRunReport,
        )

    def test_non_fixture_requires_existing_manifested_archive(self):
        """Plan §0 step zero, enforced: a real ingest must cite a
        committed archive directory carrying MANIFEST.sha256."""
        with pytest.raises(ReplyItemError, match="MANIFEST"):
            ingest_reply(
                {
                    "archive": "calibration/data/raw/does_not_exist_2099-01-01/",
                    "items": {},
                },
                fixture=False,
            )


class TestD2EscapeHatch:
    """The armed D2 transaction (adversarial-review fix: mechanised, not
    narrated). Uses a real committed archive dir purely to exercise the
    existence validation; the produced instruction is a test-local object
    that registers nothing."""

    REAL_ARCHIVE = "calibration/data/raw/oxborrow_tuning_2026-07-16"

    def _kwargs(self, **over):
        base = dict(
            proposal_text=(
                "TEST-ONLY (not a real proposal): shall I take usable travel "
                "as gap 5-10 mm on the current build?"
            ),
            proposed_nominal_m=15e-3,
            proposed_min_m=12e-3,
            proposed_max_m=20e-3,
            followup_dates=("2026-07-25",),
            followup_archive_refs=(self.REAL_ARCHIVE,),
            no_reply_as_of="2026-08-10",
            elapsed_days=16.0,
        )
        base.update(over)
        return base

    def test_complete_escape_hatch_mints_planning_assumption(self):
        from cavity.sweep.reply_ingest import build_d2_escape_hatch

        mi = build_d2_escape_hatch(**self._kwargs())
        assert mi.question_id == "Q2"
        assert mi.rung is Rung.PLANNING_ASSUMPTION
        assert not mi.fixture
        for token in ("D2 ESCAPE HATCH", "TEST-ONLY", "2026-07-25", "No reply"):
            assert token in mi.provenance
        # still nothing registered
        assert [r.question_id for r in RATIFIED_RESOLUTIONS] == [
            "Q2",
            "Q11",
            "Q13",
        ]

    @pytest.mark.parametrize(
        "over,match",
        [
            ({"proposal_text": " "}, "proposal"),
            ({"followup_dates": ()}, "date"),
            ({"no_reply_as_of": ""}, "no-reply"),
            ({"elapsed_days": 0.0}, "elapsed"),
            (
                {"followup_archive_refs": ("calibration/data/raw/nope/",)},
                "MANIFEST",
            ),
            ({"proposed_min_m": 21e-3}, "inverted"),
        ],
    )
    def test_incomplete_escape_hatch_refused(self, over, match):
        from cavity.sweep.reply_ingest import build_d2_escape_hatch

        with pytest.raises(ReplyItemError, match=match):
            build_d2_escape_hatch(**self._kwargs(**over))
