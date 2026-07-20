"""D7 supersession-transaction guards (calibration/supersession.py).

The committed digitized feed must be untouchable by any dry run; a
supersession without the explicit same-acquisition declaration must
refuse; a NEW dataset must not carry a supersedes pointer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from calibration.supersession import (
    DatasetRelationship,
    SupersessionError,
    execute_supersession,
    plan_feed_supersession,
)

REPO = Path(__file__).resolve().parent.parent
REAL_FEED = REPO / "calibration" / "reports" / "observable_a_feed.json"

DECLARATION = (
    "FIXTURE declaration: Angus states (archived email, FIXTURE) that the "
    "raw traces are the same acquisitions behind the 2026-07-14 figures"
)


def _new_feed(**overrides) -> dict:
    feed = {
        "dataset_version": "cowley_semple_FIXTURE-raw",
        "provenance": "FIXTURE raw-trace refit (synthetic)",
        "supersedes": "cowley_semple_2026-07-14-digitized",
        "same_acquisition_declaration": DECLARATION,
        "samples": {},
    }
    feed.update(overrides)
    return feed


def _plan(**kwargs):
    defaults = dict(
        new_dataset_version="cowley_semple_FIXTURE-raw",
        relationship=DatasetRelationship.SUPERSEDES_SAME_ACQUISITION,
        same_acquisition_declaration=DECLARATION,
    )
    defaults.update(kwargs)
    return plan_feed_supersession(REAL_FEED, _new_feed(), **defaults)


class TestPlanning:
    def test_valid_supersession_plan(self):
        plan = _plan()
        assert plan.archive_copy_path.parent == REAL_FEED.parent
        assert plan.archive_copy_path.name != REAL_FEED.name

    def test_missing_declaration_refused(self):
        with pytest.raises(SupersessionError, match="declaration"):
            _plan(same_acquisition_declaration="  ")

    def test_declaration_must_be_recorded_in_feed(self):
        feed = _new_feed()
        feed.pop("same_acquisition_declaration")
        with pytest.raises(SupersessionError, match="verbatim"):
            plan_feed_supersession(
                REAL_FEED,
                feed,
                new_dataset_version="cowley_semple_FIXTURE-raw",
                relationship=DatasetRelationship.SUPERSEDES_SAME_ACQUISITION,
                same_acquisition_declaration=DECLARATION,
            )

    def test_supersedes_pointer_must_name_old_dataset(self):
        feed = _new_feed(supersedes="something else entirely")
        with pytest.raises(SupersessionError, match="supersedes"):
            plan_feed_supersession(
                REAL_FEED,
                feed,
                new_dataset_version="cowley_semple_FIXTURE-raw",
                relationship=DatasetRelationship.SUPERSEDES_SAME_ACQUISITION,
                same_acquisition_declaration=DECLARATION,
            )

    def test_new_dataset_must_not_supersede(self):
        with pytest.raises(SupersessionError, match="both live"):
            plan_feed_supersession(
                REAL_FEED,
                _new_feed(),
                new_dataset_version="cowley_semple_FIXTURE-raw",
                relationship=DatasetRelationship.NEW_DATASET,
            )

    def test_new_dataset_without_pointer_is_legal(self):
        feed = _new_feed()
        feed.pop("supersedes")
        feed.pop("same_acquisition_declaration")
        plan = plan_feed_supersession(
            REAL_FEED,
            feed,
            new_dataset_version="cowley_semple_FIXTURE-raw",
            relationship=DatasetRelationship.NEW_DATASET,
        )
        assert plan.relationship is DatasetRelationship.NEW_DATASET

    def test_missing_dataset_version_refused(self):
        with pytest.raises(SupersessionError, match="dataset_version"):
            plan_feed_supersession(
                REAL_FEED,
                _new_feed(dataset_version="wrong"),
                new_dataset_version="cowley_semple_FIXTURE-raw",
                relationship=DatasetRelationship.SUPERSEDES_SAME_ACQUISITION,
                same_acquisition_declaration=DECLARATION,
            )


class TestExecution:
    def test_dry_run_to_temp_preserves_committed_feed(self, tmp_path):
        before = REAL_FEED.read_bytes()
        plan = _plan()
        copy_path, new_path = execute_supersession(plan, out_dir=tmp_path)
        assert REAL_FEED.read_bytes() == before
        assert copy_path.read_bytes() == before
        new = json.loads(new_path.read_text(encoding="utf-8"))
        assert new["dataset_version"] == "cowley_semple_FIXTURE-raw"
        assert new["supersedes"] == "cowley_semple_2026-07-14-digitized"
        assert new["same_acquisition_declaration"] == DECLARATION

    def test_in_place_refused_without_flag(self):
        plan = _plan()
        with pytest.raises(SupersessionError, match="allow_in_place"):
            execute_supersession(plan, out_dir=REAL_FEED.parent)
        # and the committed artifact is provably untouched
        assert json.loads(REAL_FEED.read_text(encoding="utf-8"))[
            "dataset"
        ] == "cowley_semple_2026-07-14 (digitized)"

    def test_existing_archive_copy_refused(self, tmp_path):
        plan = _plan()
        execute_supersession(plan, out_dir=tmp_path)
        with pytest.raises(SupersessionError, match="already exists"):
            execute_supersession(plan, out_dir=tmp_path)
