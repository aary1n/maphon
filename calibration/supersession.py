"""D7 feed-supersession transaction — blocker-independent plumbing of
docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md §1.3.

Ruling D7 (user-ratified 2026-07-20): feed supersession is
archive-copy-then-regenerate-in-place on the stable canonical path —
before replacing `calibration/reports/observable_a_feed.json`, the
existing digitized-grade artifact is copied byte-identically to
`observable_a_feed_digitized_2026-07-14.json` (same directory), then the
canonical feed is regenerated from the selected raw dataset in the same
changeset. BOTH files carry explicit `dataset_version` and `provenance`
fields; the new canonical feed carries a `supersedes` pointer.

Supersession-vs-new-dataset rule (plan §1.3, fixed in advance): raw
traces of the SAME acquisitions supersede the digitized dataset; a NEW
acquisition is a NEW dataset version — both live, neither supersedes.
"Same acquisition" is NOT inferable from matching numbers or filenames
(audit finding, 2026-07-20): the relationship must be DECLARED explicitly
and the declaration is recorded in the new feed.

This module PLANS and DRY-RUNS the transaction. Executing against the
real canonical path requires `allow_in_place=True` — the flag the actual
reply changeset passes, with the archive already committed. Nothing here
runs at import time; the committed feed is untouched by any dry run.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SupersessionError(ValueError):
    """The transaction violates D7 / §1.3. Refusal, not repair."""


class DatasetRelationship(Enum):
    #: Raw traces of the SAME acquisitions that produced the superseded
    #: dataset — the only relationship that supersedes.
    SUPERSEDES_SAME_ACQUISITION = "supersedes-same-acquisition"
    #: A new acquisition: both datasets live; NO supersedes pointer.
    NEW_DATASET = "new-dataset"


@dataclass(frozen=True)
class SupersessionPlan:
    canonical_path: Path
    archive_copy_name: str
    new_feed: dict
    relationship: DatasetRelationship

    @property
    def archive_copy_path(self) -> Path:
        return self.canonical_path.parent / self.archive_copy_name


def plan_feed_supersession(
    canonical_path: Path,
    new_feed: dict,
    *,
    new_dataset_version: str,
    relationship: DatasetRelationship,
    same_acquisition_declaration: str = "",
    archive_copy_name: str | None = None,
) -> SupersessionPlan:
    """Validate and assemble the D7 transaction (no writes here).

    Requirements enforced:
    - the canonical feed exists and is parseable JSON;
    - the NEW feed carries `dataset_version` (== new_dataset_version),
      `provenance`, and — iff relationship is SUPERSEDES_SAME_ACQUISITION —
      a `supersedes` field naming the old dataset plus the explicit
      declaration text (who stated the acquisitions are the same, where);
    - a NEW_DATASET relationship must NOT carry a `supersedes` pointer
      (both datasets live; comparison is analysis, not merge).
    """
    if not canonical_path.is_file():
        raise SupersessionError(f"canonical feed missing: {canonical_path}")
    old = json.loads(canonical_path.read_text(encoding="utf-8"))
    old_dataset = str(old.get("dataset", old.get("dataset_version", "")))
    if not old_dataset:
        raise SupersessionError(
            "old feed carries no dataset identity — refuse to supersede blind"
        )

    if new_feed.get("dataset_version") != new_dataset_version:
        raise SupersessionError(
            "new feed must carry dataset_version == "
            f"{new_dataset_version!r}, got {new_feed.get('dataset_version')!r}"
        )
    if not str(new_feed.get("provenance", "")).strip():
        raise SupersessionError("new feed must carry a provenance field")

    if relationship is DatasetRelationship.SUPERSEDES_SAME_ACQUISITION:
        if not same_acquisition_declaration.strip():
            raise SupersessionError(
                "supersession requires the EXPLICIT same-acquisition "
                "declaration (not inferable from matching numbers/filenames)"
            )
        if new_feed.get("supersedes") != old_dataset:
            raise SupersessionError(
                f"new feed's supersedes field must name {old_dataset!r}, "
                f"got {new_feed.get('supersedes')!r}"
            )
        if new_feed.get("same_acquisition_declaration") != (
            same_acquisition_declaration
        ):
            raise SupersessionError(
                "the declaration must be recorded verbatim inside the new feed"
            )
    else:
        if "supersedes" in new_feed:
            raise SupersessionError(
                "a NEW dataset does not supersede: both live (plan §1.3); "
                "drop the supersedes field"
            )

    if archive_copy_name is None:
        stem = canonical_path.stem
        tag = old_dataset.replace(" ", "_").replace("(", "").replace(")", "")
        archive_copy_name = f"{stem}_{tag}.json"
    if archive_copy_name == canonical_path.name:
        raise SupersessionError("archive copy cannot shadow the canonical name")

    return SupersessionPlan(
        canonical_path=canonical_path,
        archive_copy_name=archive_copy_name,
        new_feed=dict(new_feed),
        relationship=relationship,
    )


def execute_supersession(
    plan: SupersessionPlan,
    *,
    out_dir: Path,
    allow_in_place: bool = False,
) -> tuple[Path, Path]:
    """Execute the transaction into `out_dir` (dry-run tier) or, with
    `allow_in_place=True`, onto the canonical path itself (the real reply
    changeset). Returns (archive_copy_path, new_canonical_path).

    Dry-run guarantee: with allow_in_place False (the default), writing
    into the canonical feed's own directory is REFUSED, so no test or
    rehearsal can clobber the committed artifact."""
    out_dir = Path(out_dir)
    in_place = out_dir.resolve() == plan.canonical_path.parent.resolve()
    if in_place and not allow_in_place:
        raise SupersessionError(
            "refusing to write into the canonical feed's directory without "
            "allow_in_place=True (dry runs go to temp)"
        )
    out_dir.mkdir(parents=True, exist_ok=True)

    original_bytes = plan.canonical_path.read_bytes()
    archive_copy = out_dir / plan.archive_copy_name
    if archive_copy.exists():
        raise SupersessionError(f"archive copy already exists: {archive_copy}")
    shutil.copyfile(plan.canonical_path, archive_copy)
    if archive_copy.read_bytes() != original_bytes:
        raise SupersessionError("archive copy is not byte-identical — abort")

    new_canonical = out_dir / plan.canonical_path.name
    new_canonical.write_text(
        json.dumps(plan.new_feed, indent=2) + "\n", encoding="utf-8"
    )
    if not in_place and plan.canonical_path.read_bytes() != original_bytes:
        raise SupersessionError("dry run mutated the committed canonical feed")
    return archive_copy, new_canonical
