"""Reply-metadata schema guards (calibration/reply_schema.py)."""

from __future__ import annotations

import pytest

from calibration.reply_schema import (
    Grade,
    GradedField,
    MissingFieldsReport,
    PowerPlane,
    ReplyMetadata,
    RigMetadata,
    SampleMetadata,
    SchemaError,
    missing_fields_report,
    uniform_band_field,
)


class TestGradedField:
    def test_absent_field_is_fully_absent(self):
        assert not GradedField().present
        with pytest.raises(SchemaError):
            GradedField(value=None, grade=Grade.FIGURE_STATED)
        with pytest.raises(SchemaError):
            GradedField(value=None, quote="stray quote")

    def test_value_requires_grade(self):
        with pytest.raises(SchemaError, match="grade"):
            GradedField(value=0.5e-3)

    def test_collaborator_grades_require_quote(self):
        with pytest.raises(SchemaError, match="quote"):
            GradedField(value=0.5e-3, grade=Grade.COLLABORATOR_CONFIRMED)
        ok = GradedField(
            value=0.5e-3,
            grade=Grade.COLLABORATOR_CONFIRMED,
            quote="the crystal is half a millimetre thick",
        )
        assert ok.present

    def test_planning_assumption_may_omit_quote(self):
        assert GradedField(value=1e-3, grade=Grade.PLANNING_ASSUMPTION).present

    def test_d5_uniform_band(self):
        f = uniform_band_field(
            0.3e-3, 0.7e-3, Grade.COLLABORATOR_CONFIRMED, "0.3 to 0.7 mm ish"
        )
        assert f.value == (0.3e-3, 0.7e-3)
        assert "D5 uniform reading" in f.quote
        with pytest.raises(SchemaError, match="inverted"):
            uniform_band_field(0.7e-3, 0.3e-3, Grade.FIGURE_STATED, "q")


class TestRecords:
    def test_sample_requires_id_and_valid_isotope(self):
        with pytest.raises(SchemaError, match="sample_id"):
            SampleMetadata(sample_id=" ")
        with pytest.raises(SchemaError, match="isotope"):
            SampleMetadata(
                sample_id="s1",
                isotope=GradedField(
                    value="deuterated",
                    grade=Grade.COLLABORATOR_CONFIRMED,
                    quote="d14",
                ),
            )

    def test_power_plane_requires_quote(self):
        """Resolving the OPEN power-plane ask without wording would be an
        invented answer — refused at the schema level."""
        with pytest.raises(SchemaError, match="quote"):
            RigMetadata(power_plane=PowerPlane.AT_SAMPLE)
        RigMetadata(
            power_plane=PowerPlane.AT_SAMPLE,
            power_plane_quote="measured right at the sample position",
        )

    def test_reply_requires_archive_and_fixture_marker(self):
        rig = RigMetadata()
        with pytest.raises(SchemaError, match="archive"):
            ReplyMetadata(archive_ref=" ", fixture=False, samples=(), rig=rig)
        with pytest.raises(SchemaError, match="FIXTURE"):
            ReplyMetadata(
                archive_ref="calibration/data/raw/x/",
                fixture=True,
                samples=(),
                rig=rig,
            )

    def test_duplicate_sample_ids_refused(self):
        rig = RigMetadata()
        s = SampleMetadata(sample_id="d14")
        with pytest.raises(SchemaError, match="duplicate"):
            ReplyMetadata(
                archive_ref="FIXTURE", fixture=True, samples=(s, s), rig=rig
            )


class TestMissingFieldsReport:
    def test_empty_reply_reports_everything_ranked(self):
        meta = ReplyMetadata(
            archive_ref="FIXTURE: synthetic",
            fixture=True,
            samples=(SampleMetadata(sample_id="d14"),),
            rig=RigMetadata(),
        )
        report = missing_fields_report(meta)
        assert isinstance(report, MissingFieldsReport)
        assert "power_plane" in report.missing_rig
        assert "thickness_m" in report.missing_per_sample["d14"]
        # ranked stakes: thickness is the TOP residual gap
        assert report.stakes[0][0] == "thickness_m"
        text = report.to_markdown()
        assert "TOP residual gap" in text

    def test_present_fields_drop_out(self):
        meta = ReplyMetadata(
            archive_ref="FIXTURE: synthetic",
            fixture=True,
            samples=(
                SampleMetadata(
                    sample_id="d14",
                    thickness_m=GradedField(
                        value=0.6e-3,
                        grade=Grade.MEASURED_BY_COLLABORATOR,
                        quote="0.6 mm by caliper",
                    ),
                ),
            ),
            rig=RigMetadata(
                power_plane=PowerPlane.DIODE_OUTPUT,
                power_plane_quote="powers are the diode output",
            ),
        )
        report = missing_fields_report(meta)
        assert "thickness_m" not in report.missing_per_sample["d14"]
        assert "power_plane" not in report.missing_rig
        assert all(name != "thickness_m" for name, _ in report.stakes)
