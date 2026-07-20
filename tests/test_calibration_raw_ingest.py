"""Versioned raw-trace loader guards (calibration/raw_ingest.py).

The refusals ARE the product: ungraded/unversioned/ambiguous data does not
load. Fixtures are synthetic and FIXTURE-graded throughout — none of these
values can reach a production fit (grade + dataset_version travel with
every record)."""

from __future__ import annotations

import numpy as np
import pytest

from calibration.raw_ingest import (
    RawIngestError,
    REQUIRED_HEADER_KEYS,
    TraceRecord,
    load_dataset,
    load_trace,
    render_trace_csv,
)
from calibration.reply_schema import PowerPlane

FIXTURE_SHA = "0" * 64


def _header(**overrides) -> dict[str, str]:
    base = {
        "dataset_version": "FIXTURE-2026-07-20",
        "grade": "fixture",
        "source_archive": "FIXTURE: none",
        "source_member": "FIXTURE: synthetic",
        "source_sha256": FIXTURE_SHA,
        "sample_id": "d14",
        "optical_power_mw": "3.81",
        "power_plane": "unknown",
        "freq_unit": "Hz",
        "parser": "test fixture v1",
    }
    base.update(overrides)
    return base


def _write_trace(tmp_path, name="trace.csv", *, header=None, body=None):
    freq = np.linspace(1.4480e9, 1.4500e9, 21)
    signal = 1.0 - 0.05 / (1.0 + ((freq - 1.4490e9) / 0.7e6) ** 2)
    text = render_trace_csv(
        header=header or _header(), freq=freq, signal=signal
    )
    if body is not None:
        head, _, _ = text.partition("frequency_hz")
        text = head + body
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


class TestLoadTrace:
    def test_round_trip(self, tmp_path):
        record = load_trace(_write_trace(tmp_path))
        assert isinstance(record, TraceRecord)
        assert record.is_fixture
        assert record.power_plane is PowerPlane.UNKNOWN
        assert record.freq_hz.size == 21
        assert record.optical_power_mw == pytest.approx(3.81)

    @pytest.mark.parametrize("missing_key", REQUIRED_HEADER_KEYS)
    def test_each_missing_header_key_refused(self, tmp_path, missing_key):
        header = _header()
        header.pop(missing_key)
        path = tmp_path / "bad.csv"
        lines = [f"# {k}: {v}" for k, v in header.items()]
        lines += ["frequency_hz,signal", "1.0e9,1.0", "1.1e9,1.1", "1.2e9,1.2"]
        path.write_text("\n".join(lines), encoding="utf-8")
        with pytest.raises(RawIngestError, match="missing header"):
            load_trace(path)

    def test_unknown_grade_refused(self, tmp_path):
        with pytest.raises(RawIngestError, match="grade"):
            load_trace(
                _write_trace(tmp_path, header=_header(grade="just-trust-me"))
            )

    def test_emailed_table_requires_transcription_check(self, tmp_path):
        header = _header(grade="emailed-table-transcription")
        with pytest.raises(RawIngestError, match="transcription_check"):
            load_trace(_write_trace(tmp_path, header=header))
        header["transcription_check"] = "verified-against-archive"
        assert load_trace(_write_trace(tmp_path, header=header)).grade == (
            "emailed-table-transcription"
        )

    def test_non_monotonic_frequency_refused(self, tmp_path):
        path = _write_trace(
            tmp_path,
            body=(
                "frequency_hz,signal\n"
                "1.0e9,1.0\n1.2e9,1.1\n1.1e9,1.2\n1.3e9,1.0\n"
            ),
        )
        with pytest.raises(RawIngestError, match="monotonic"):
            load_trace(path)

    def test_non_finite_refused(self, tmp_path):
        path = _write_trace(
            tmp_path,
            body="frequency_hz,signal\n1.0e9,1.0\n1.1e9,nan\n1.2e9,1.0\n",
        )
        with pytest.raises(RawIngestError, match="finite"):
            load_trace(path)

    def test_bad_sha_refused(self, tmp_path):
        with pytest.raises(RawIngestError, match="hex"):
            load_trace(
                _write_trace(
                    tmp_path, header=_header(source_sha256="not-a-hash")
                )
            )

    def test_khz_unit_scales(self, tmp_path):
        header = _header(freq_unit="MHz")
        freq_mhz = np.linspace(1448.0, 1450.0, 11)
        signal = np.linspace(1.0, 0.9, 11)
        path = tmp_path / "mhz.csv"
        path.write_text(
            render_trace_csv(header=header, freq=freq_mhz, signal=signal),
            encoding="utf-8",
        )
        record = load_trace(path)
        assert record.freq_hz[0] == pytest.approx(1.448e9)


class TestLoadDataset:
    def test_explicit_version_no_latest_magic(self, tmp_path):
        _write_trace(tmp_path, "a.csv", header=_header(optical_power_mw="3.81"))
        _write_trace(tmp_path, "b.csv", header=_header(optical_power_mw="6.06"))
        _write_trace(
            tmp_path,
            "other_version.csv",
            header=_header(
                dataset_version="FIXTURE-OTHER", optical_power_mw="9.99"
            ),
        )
        traces = load_dataset(tmp_path, "FIXTURE-2026-07-20")
        assert len(traces) == 2
        with pytest.raises(RawIngestError, match="no traces"):
            load_dataset(tmp_path, "nonexistent-version")

    def test_duplicate_sample_power_refused(self, tmp_path):
        _write_trace(tmp_path, "a.csv")
        _write_trace(tmp_path, "b.csv")
        with pytest.raises(RawIngestError, match="duplicate"):
            load_dataset(tmp_path, "FIXTURE-2026-07-20")


class TestRenderer:
    def test_render_refuses_incomplete_header(self):
        with pytest.raises(RawIngestError, match="missing header"):
            render_trace_csv(
                header={"dataset_version": "x"},
                freq=np.array([1.0, 2.0, 3.0]),
                signal=np.array([1.0, 1.0, 1.0]),
            )

    def test_render_is_deterministic(self):
        freq = np.linspace(1.448e9, 1.450e9, 5)
        signal = np.linspace(1.0, 0.9, 5)
        a = render_trace_csv(header=_header(), freq=freq, signal=signal)
        b = render_trace_csv(header=_header(), freq=freq, signal=signal)
        assert a == b


class TestSourceVerification:
    """The NON-fixture source-verification branch, exercised against the
    REAL committed cowley_semple_2026-07-14 archive (audit F2 regression,
    2026-07-20: `_PACKAGE_DIR` was undefined and every load reaching this
    branch died with NameError before the hash check ran).

    The spectrum body stays synthetic — no value here can enter a
    production fit — but the provenance header names a genuinely archived
    member with its manifest-pinned hash, so the SHA-256 verification
    actually executes. `dataset_version` deliberately carries no FIXTURE
    token — not even as a substring ("NONFIXTURE" would trip the guard,
    which errs toward the fixture side): that is the branch condition
    under test."""

    ARCHIVE = "calibration/data/raw/cowley_semple_2026-07-14"
    MEMBER = "thermal.eml"

    def _manifest_sha(self) -> str:
        from pathlib import Path

        from calibration.integrity import MANIFEST_NAME, parse_manifest

        repo_root = Path(__file__).resolve().parents[1]
        manifest = parse_manifest(repo_root / self.ARCHIVE / MANIFEST_NAME)
        return manifest[self.MEMBER]

    def _real_header(self, sha: str, member: str | None = None) -> dict[str, str]:
        return _header(
            dataset_version="verification-branch-audit-f2-2026-07-20",
            grade="raw-derived",
            source_archive=self.ARCHIVE,
            source_member=member or self.MEMBER,
            source_sha256=sha,
        )

    def test_verifies_against_committed_archive_member(self, tmp_path):
        header = self._real_header(self._manifest_sha())
        record = load_trace(_write_trace(tmp_path, header=header))
        assert record.source_verified is True
        assert not record.is_fixture

    def test_hash_mismatch_refused(self, tmp_path):
        header = self._real_header("1" * 64)
        with pytest.raises(RawIngestError, match="does not match"):
            load_trace(_write_trace(tmp_path, header=header))

    def test_missing_member_refused(self, tmp_path):
        header = self._real_header(self._manifest_sha(), member="no_such_member.csv")
        with pytest.raises(RawIngestError, match="not found"):
            load_trace(_write_trace(tmp_path, header=header))
