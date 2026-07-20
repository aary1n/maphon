"""Cowley-Semple reply metadata schema — blocker-independent tier of
docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md §2.

Typed, nullable-with-grade metadata records so a PARTIAL reply ingests
cleanly: every slot is a `GradedField` that either holds (value, grade,
quote) or is absent, and `missing_fields_report` states exactly what is
still open, ranked by load-bearing order (thickness → power plane → spot →
settling → CPW/vias → bond line). Informal ranges are read per D5
(UNIFORM band, wording quoted) — the reading helper lives with the field.

NON-TRANSFERABLE discipline unchanged: nothing here migrates to
`cavity/provenance/constants.py`, and this module imports nothing from
`cavity` at all. Static graded constants for the 2026-07-14 dataset stay
in `calibration/constants.py`; this schema exists for the NEXT reply and
never edits those.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum


class Grade(Enum):
    """The §2 grade vocabulary (calibration/constants.py docstring), plus
    MEASURED-BY-COLLABORATOR for stated actual measurements."""

    COLLABORATOR_CONFIRMED = "collaborator-confirmed"
    COLLABORATOR_SUGGESTED = "collaborator-suggested"
    MEASURED_BY_COLLABORATOR = "measured-by-collaborator"
    FIGURE_STATED = "figure-stated"
    PLANNING_ASSUMPTION = "planning-assumption"


class PowerPlane(Enum):
    """Where the quoted optical powers were measured (plan §2)."""

    AT_SAMPLE = "at-sample"
    DIODE_OUTPUT = "diode-output"
    AFTER_FIBRE = "after-fibre"
    OTHER = "other"
    UNKNOWN = "unknown"


class SchemaError(ValueError):
    """A reply-metadata record fails validation. Refusal, not repair."""


@dataclass(frozen=True)
class GradedField:
    """One metadata slot: value + grade + the verbatim wording it came
    from. Absent = value is None (grade/quote must then be empty too)."""

    value: object | None = None
    grade: Grade | None = None
    quote: str = ""

    def __post_init__(self) -> None:
        if self.value is None:
            if self.grade is not None or self.quote:
                raise SchemaError(
                    "absent field must be fully absent (no grade, no quote)"
                )
            return
        if self.grade is None:
            raise SchemaError(f"value {self.value!r} carries no grade")
        if self.grade is not Grade.PLANNING_ASSUMPTION and not self.quote.strip():
            raise SchemaError(
                f"grade {self.grade.value} requires the verbatim quote "
                "(planning assumptions are ours and may omit it)"
            )

    @property
    def present(self) -> bool:
        return self.value is not None


def uniform_band_field(
    lo: float, hi: float, grade: Grade, quote: str
) -> GradedField:
    """D5 (user-ratified 2026-07-20): an informal range in the reply is
    read as a UNIFORM band [lo, hi], wording quoted — the single
    convention at every site."""
    if not (float(lo) < float(hi)):
        raise SchemaError(f"uniform band inverted: [{lo}, {hi}]")
    return GradedField(
        value=(float(lo), float(hi)),
        grade=grade,
        quote=f"D5 uniform reading of: {quote}",
    )


@dataclass(frozen=True)
class SampleMetadata:
    """Per-sample slots (plan §2)."""

    sample_id: str = ""
    isotope: GradedField = field(default_factory=GradedField)  # 'd14'/'h14'
    nominal_concentration: GradedField = field(default_factory=GradedField)
    growth_batch: GradedField = field(default_factory=GradedField)
    lateral_size_m: GradedField = field(default_factory=GradedField)
    thickness_m: GradedField = field(default_factory=GradedField)
    glued_face: GradedField = field(default_factory=GradedField)
    long_axis_orientation: GradedField = field(default_factory=GradedField)
    cpw_position: GradedField = field(default_factory=GradedField)
    distance_to_vias_m: GradedField = field(default_factory=GradedField)

    def __post_init__(self) -> None:
        if not self.sample_id.strip():
            raise SchemaError("sample_id is required")
        iso = self.isotope
        if iso.present and iso.value not in ("d14", "h14"):
            raise SchemaError(f"isotope must be 'd14'/'h14', got {iso.value!r}")


@dataclass(frozen=True)
class RigMetadata:
    """Shared-rig slots (plan §2)."""

    wavelength_nm: GradedField = field(default_factory=GradedField)
    power_plane: PowerPlane = PowerPlane.UNKNOWN
    power_plane_quote: str = ""
    power_calibration: GradedField = field(default_factory=GradedField)
    spot_diameter_m: GradedField = field(default_factory=GradedField)
    settling_time_s: GradedField = field(default_factory=GradedField)
    sweep_direction: GradedField = field(default_factory=GradedField)
    dwell_per_point_s: GradedField = field(default_factory=GradedField)
    trace_order: GradedField = field(default_factory=GradedField)
    repeats: GradedField = field(default_factory=GradedField)
    mw_power_fixed: GradedField = field(default_factory=GradedField)
    cpw_trace_width_m: GradedField = field(default_factory=GradedField)
    cpw_gap_m: GradedField = field(default_factory=GradedField)
    cpw_via_pitch_m: GradedField = field(default_factory=GradedField)
    cpw_termination: GradedField = field(default_factory=GradedField)
    glass_thickness_m: GradedField = field(default_factory=GradedField)
    bond_line_thickness_m: GradedField = field(default_factory=GradedField)

    def __post_init__(self) -> None:
        if self.power_plane is not PowerPlane.UNKNOWN and not (
            self.power_plane_quote.strip()
        ):
            raise SchemaError(
                "a stated power plane requires the verbatim quote "
                "(the plane is currently an OPEN Angus ask — resolving it "
                "without wording would be an invented answer)"
            )


@dataclass(frozen=True)
class ReplyMetadata:
    """One reply's metadata: samples + rig + provenance of the reply."""

    archive_ref: str
    fixture: bool
    samples: tuple[SampleMetadata, ...]
    rig: RigMetadata

    def __post_init__(self) -> None:
        if not self.archive_ref.strip():
            raise SchemaError("archive_ref is required (plan §1.1 step zero)")
        if self.fixture and "FIXTURE" not in self.archive_ref.upper():
            raise SchemaError(
                "fixture metadata must mark the archive ref with 'FIXTURE'"
            )
        ids = [s.sample_id for s in self.samples]
        if len(ids) != len(set(ids)):
            raise SchemaError(f"duplicate sample ids: {ids}")


#: What each still-missing slot blocks, ranked by load-bearing order
#: (SPEC §11 item 5 ask ranking + the plans' hooks). Consumed by the
#: missing-fields report and by publication.build's sentinel section.
_FIELD_STAKES: tuple[tuple[str, str], ...] = (
    (
        "thickness_m",
        "TOP residual gap (ask 1): collapses the 0.2-1.0 mm sweep axis; "
        "decides w/t regime and 3b's geometric input",
    ),
    (
        "power_plane",
        "fixes eta_abs interpretation (T5); untested eta-cancellation "
        "condition in T4 until resolved",
    ),
    (
        "spot_diameter_m",
        "factorises the plate k*w product (identifiability 3a; needed to "
        "x3 multiplicative)",
    ),
    (
        "settling_time_s",
        "steady-state check (plan §6): short settling re-grades every "
        "steady-state fit to protocol-caveated",
    ),
    (
        "cpw_via_pitch_m",
        "via-proximity asymmetry (2026-07-16 caveat): second "
        "geometry-dependent heat-sinking mechanism",
    ),
    (
        "bond_line_thickness_m",
        "narrows the h_sub decade sweep to a computed series-resistance "
        "band (plan §4.6)",
    ),
)


@dataclass(frozen=True)
class MissingFieldsReport:
    archive_ref: str
    missing_rig: tuple[str, ...]
    missing_per_sample: dict[str, tuple[str, ...]]
    stakes: tuple[tuple[str, str], ...]

    def to_markdown(self) -> str:
        lines = [
            "# Missing-metadata report",
            "",
            f"Reply: `{self.archive_ref}`",
            "",
            "## Still missing (rig)",
        ]
        lines += [f"- {name}" for name in self.missing_rig] or ["- none"]
        for sid, missing in self.missing_per_sample.items():
            lines += ["", f"## Still missing (sample {sid})"]
            lines += [f"- {name}" for name in missing] or ["- none"]
        lines += ["", "## Stakes of the top missing fields"]
        for name, stake in self.stakes:
            lines.append(f"- **{name}** — {stake}")
        return "\n".join(lines) + "\n"


def missing_fields_report(meta: ReplyMetadata) -> MissingFieldsReport:
    missing_rig = tuple(
        f.name
        for f in fields(RigMetadata)
        if isinstance(getattr(meta.rig, f.name), GradedField)
        and not getattr(meta.rig, f.name).present
    )
    if meta.rig.power_plane is PowerPlane.UNKNOWN:
        missing_rig = ("power_plane",) + missing_rig
    missing_per_sample = {
        s.sample_id: tuple(
            f.name
            for f in fields(SampleMetadata)
            if isinstance(getattr(s, f.name), GradedField)
            and not getattr(s, f.name).present
        )
        for s in meta.samples
    }
    all_missing = set(missing_rig) | {
        name for names in missing_per_sample.values() for name in names
    }
    stakes = tuple((n, s) for n, s in _FIELD_STAKES if n in all_missing)
    return MissingFieldsReport(
        archive_ref=meta.archive_ref,
        missing_rig=missing_rig,
        missing_per_sample=missing_per_sample,
        stakes=stakes,
    )
