"""T0 — calibration archive integrity gate (calibration/integrity.py).

The first test IS the read-only-forever enforcement: it re-verifies the
real Cowley-Semple archive against MANIFEST.sha256 on every CI run, so any
future edit to calibration/data/raw/ turns the suite red. The remaining
tests exercise the verifier's failure modes on synthetic archives.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from calibration.integrity import (
    DEFAULT_ARCHIVE_DIR,
    CalibrationIntegrityError,
    main,
    parse_manifest,
    require_intact,
    sha256_file,
    verify_manifest,
)


def _make_archive(root: Path, files: dict[str, bytes], manifest_for: list[str]) -> Path:
    """Synthetic archive: write `files`, pin `manifest_for` (CRLF, GNU format,
    with a leading comment line — the real manifest's dialect)."""
    for name, payload in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    lines = ["# synthetic archive manifest (test fixture)"]
    for name in manifest_for:
        digest = hashlib.sha256(files[name]).hexdigest()
        lines.append(f"{digest}  {name}")
    (root / "MANIFEST.sha256").write_bytes(("\r\n".join(lines) + "\r\n").encode())
    return root


class TestRealArchive:
    def test_real_archive_intact(self):
        """THE read-only guard: the committed archive must verify, always."""
        report = verify_manifest(DEFAULT_ARCHIVE_DIR)
        assert report.ok, report.to_markdown()
        # 12 pinned files: 10 images + thermal.eml + thermal.md
        assert len(report.matched) == 12

    def test_cli_exit_zero_on_real_archive(self, capsys):
        assert main([str(DEFAULT_ARCHIVE_DIR)]) == 0
        assert "INTACT: 12 files" in capsys.readouterr().out

    def test_wu_build_papers_archive_intact(self):
        """Same read-only guard for the Wu-build primary-source archive
        (geometry re-base changeset, 2026-07-18): the two papers + PRL SM
        proof that ground every number in provenance.GEOM_WU_STO_RING."""
        archive = DEFAULT_ARCHIVE_DIR.parent / "wu_build_papers_2026-07-18"
        report = verify_manifest(archive)
        assert report.ok, report.to_markdown()
        # 3 pinned files: PRA 2020 + PRL 2021 main + PRL SM (proof copy)
        assert len(report.matched) == 3

    def test_oxborrow_sto_archive_intact(self):
        """Same read-only guard for the Oxborrow STO-dimensions written
        correspondence (2026-07-17 — the geometry re-base's written rung
        and the no-paste supersession record; the R10a rider)."""
        archive = DEFAULT_ARCHIVE_DIR.parent / "oxborrow_sto_2026-07-17"
        report = verify_manifest(archive)
        assert report.ok, report.to_markdown()
        # 2 pinned files: stogeometry.eml + stogeometry.md
        assert len(report.matched) == 2

    def test_oxborrow_meeting_notes_archive_intact(self):
        """Same read-only guard for the 2026-07-16 contemporaneous meeting
        notes (Oxborrow-VERBAL rung, late-archived 2026-07-19 — the source
        of the SPEC S-ladder fifth-outcome record)."""
        archive = DEFAULT_ARCHIVE_DIR.parent / "oxborrow_meeting_notes_2026-07-16"
        report = verify_manifest(archive)
        assert report.ok, report.to_markdown()
        # 2 pinned files: the docx verbatim + its paragraph-faithful transcript
        assert len(report.matched) == 2

    def test_oxborrow_tuning_archive_intact(self):
        """Same read-only guard for the Oxborrow 2026-07-16 tuning-mechanism
        email (STO tuning correspondence). Coverage gap found and closed
        2026-07-20: this archive had a manifest but no integrity test."""
        archive = DEFAULT_ARCHIVE_DIR.parent / "oxborrow_tuning_2026-07-16"
        report = verify_manifest(archive)
        assert report.ok, report.to_markdown()
        # 3 pinned files: stotuningmech.eml + stotuningmech.md + images/image.png
        assert len(report.matched) == 3

    def test_verify_all_covers_every_archive_dir(self):
        """The generic walk and the on-disk archive set must agree, so a
        newly-committed archive cannot silently escape verification."""
        from calibration.integrity import DEFAULT_RAW_ROOT, verify_all

        on_disk = {
            p.name
            for p in DEFAULT_RAW_ROOT.iterdir()
            if p.is_dir()
        }
        reports = verify_all()
        assert set(reports) == on_disk, (
            "raw archive without a MANIFEST.sha256 (or stray dir): "
            f"{sorted(on_disk ^ set(reports))}"
        )
        for name, report in reports.items():
            assert report.ok, f"{name}: {report.to_markdown()}"


class TestManifestParsing:
    def test_crlf_and_comments_tolerated(self, tmp_path):
        manifest = tmp_path / "MANIFEST.sha256"
        digest = "a" * 64
        manifest.write_bytes(
            (f"# comment\r\n\r\n{digest}  images/x.png\r\n{digest} *y.bin\r\n").encode()
        )
        entries = parse_manifest(manifest)
        assert entries == {"images/x.png": digest, "y.bin": digest}

    def test_malformed_line_is_an_error_not_a_skip(self, tmp_path):
        manifest = tmp_path / "MANIFEST.sha256"
        manifest.write_bytes(b"not-a-hash  file.txt\r\n")
        with pytest.raises(ValueError, match="malformed"):
            parse_manifest(manifest)

    def test_duplicate_entry_rejected(self, tmp_path):
        manifest = tmp_path / "MANIFEST.sha256"
        digest = "b" * 64
        manifest.write_bytes(f"{digest}  f.txt\r\n{digest}  f.txt\r\n".encode())
        with pytest.raises(ValueError, match="duplicate"):
            parse_manifest(manifest)


class TestFailureModes:
    def test_tampered_file_detected(self, tmp_path):
        _make_archive(tmp_path, {"a.txt": b"payload"}, ["a.txt"])
        (tmp_path / "a.txt").write_bytes(b"tampered")
        report = verify_manifest(tmp_path)
        assert not report.ok
        (name, expected, actual) = report.mismatched[0]
        assert name == "a.txt"
        assert expected == hashlib.sha256(b"payload").hexdigest()
        assert actual == hashlib.sha256(b"tampered").hexdigest()

    def test_missing_file_detected(self, tmp_path):
        _make_archive(tmp_path, {"a.txt": b"x", "b.txt": b"y"}, ["a.txt", "b.txt"])
        (tmp_path / "b.txt").unlink()
        report = verify_manifest(tmp_path)
        assert report.missing == ("b.txt",) and not report.ok

    def test_extra_file_detected(self, tmp_path):
        """Both directions: an unpinned file appearing inside raw/ is a
        failure — read-only-forever forbids additions, not just edits."""
        _make_archive(tmp_path, {"a.txt": b"x"}, ["a.txt"])
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "extra.txt").write_bytes(b"nope")
        report = verify_manifest(tmp_path)
        assert report.extra == ("sub/extra.txt",) and not report.ok

    def test_report_markdown_names_every_failure(self, tmp_path):
        _make_archive(tmp_path, {"a.txt": b"x", "b.txt": b"y"}, ["a.txt", "b.txt"])
        (tmp_path / "a.txt").write_bytes(b"tampered")
        (tmp_path / "b.txt").unlink()
        (tmp_path / "c.txt").write_bytes(b"extra")
        md = verify_manifest(tmp_path).to_markdown()
        assert "FAILED" in md and "a.txt" in md and "b.txt" in md and "c.txt" in md

    def test_require_intact_writes_report_and_raises(self, tmp_path):
        archive = _make_archive(tmp_path / "arc", {"a.txt": b"x"}, ["a.txt"])
        (archive / "a.txt").write_bytes(b"tampered")
        reports = tmp_path / "reports"
        with pytest.raises(CalibrationIntegrityError, match="1 mismatched"):
            require_intact(archive, reports_dir=reports)
        written = list(reports.glob("integrity_failure_*.md"))
        assert len(written) == 1 and "a.txt" in written[0].read_text(encoding="utf-8")

    def test_cli_exit_one_on_tampered_archive(self, tmp_path, capsys, monkeypatch):
        archive = _make_archive(tmp_path / "arc", {"a.txt": b"x"}, ["a.txt"])
        (archive / "a.txt").write_bytes(b"tampered")
        import calibration.integrity as integrity

        monkeypatch.setattr(integrity, "DEFAULT_REPORTS_DIR", tmp_path / "reports")
        assert main([str(archive)]) == 1
        assert "FAILED integrity" in capsys.readouterr().err
        # the monkeypatched dir must actually receive the report: the default
        # is resolved at call time — a def-time-bound default silently wrote
        # synthetic failure reports into the real calibration/reports/
        leaked = list((tmp_path / "reports").glob("integrity_failure_*.md"))
        assert len(leaked) == 1 and "a.txt" in leaked[0].read_text(encoding="utf-8")


class TestHashHelper:
    def test_sha256_file_streams_match_hashlib(self, tmp_path):
        payload = b"z" * (3 << 20)  # spans multiple 1 MiB chunks
        path = tmp_path / "big.bin"
        path.write_bytes(payload)
        assert sha256_file(path) == hashlib.sha256(payload).hexdigest()
