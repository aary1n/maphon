"""T0 — integrity gate for the Cowley-Semple raw archive.

Verifies `calibration/data/raw/cowley_semple_2026-07-14/` against its
MANIFEST.sha256 in BOTH directions: every manifest entry must exist on
disk with a matching SHA-256, and every file on disk (the manifest itself
excepted) must appear in the manifest. Nothing downstream (samples,
slope fit, ratio test, absolute fits) may read archive data unless this
gate passes — call `require_intact()` first.

Manifest format notes (learned from the archive itself, 2026-07-14):
- the file has CRLF line endings, so parsing uses universal newlines —
  naive `sha256sum -c` fails on all names with a trailing ``\\r``;
- lines starting with ``#`` are comments (the dated Finding-1 errata
  block lives inside the manifest as such);
- entry format is the GNU coreutils one: 64 hex digits, two-character
  separator (``"  "`` or ``" *"``), then the archive-relative POSIX path.

The read-only-forever guarantee is enforced two ways: the working tree is
re-verified in CI on every test run (tests/test_calibration_integrity.py),
and the archive is committed byte-for-byte (.gitattributes ``-text``; the
LFS oid of each binary equals the manifest's own SHA-256 pin).

CLI: ``python -m calibration.integrity`` — exit 0 iff intact; on failure
prints the report and writes it to ``calibration/reports/``.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_ARCHIVE_DIR = _PACKAGE_DIR / "data" / "raw" / "cowley_semple_2026-07-14"
DEFAULT_REPORTS_DIR = _PACKAGE_DIR / "reports"
MANIFEST_NAME = "MANIFEST.sha256"


class CalibrationIntegrityError(RuntimeError):
    """Raised by `require_intact` when the archive fails verification."""


@dataclass(frozen=True)
class IntegrityReport:
    """Outcome of one archive verification, all paths archive-relative POSIX."""

    archive_dir: Path
    matched: tuple[str, ...]
    mismatched: tuple[tuple[str, str, str], ...]  # (path, expected, actual)
    missing: tuple[str, ...]  # pinned in the manifest, absent on disk
    extra: tuple[str, ...]  # present on disk, not pinned in the manifest

    @property
    def ok(self) -> bool:
        return not (self.mismatched or self.missing or self.extra)

    def to_markdown(self) -> str:
        lines = [
            f"# Archive integrity report — {self.archive_dir.name}",
            "",
            f"Verdict: **{'INTACT' if self.ok else 'FAILED'}** "
            f"({len(self.matched)} matched, {len(self.mismatched)} mismatched, "
            f"{len(self.missing)} missing, {len(self.extra)} extra)",
            "",
        ]
        if self.mismatched:
            lines.append("## Hash mismatches (file edited after pinning?)")
            for path, expected, actual in self.mismatched:
                lines += [f"- `{path}`", f"  - pinned:   `{expected}`", f"  - on disk:  `{actual}`"]
            lines.append("")
        if self.missing:
            lines.append("## Pinned but absent on disk")
            lines += [f"- `{p}`" for p in self.missing]
            lines.append("")
        if self.extra:
            lines.append("## On disk but not pinned (raw/ is read-only forever)")
            lines += [f"- `{p}`" for p in self.extra]
            lines.append("")
        return "\n".join(lines)


def sha256_file(path: Path) -> str:
    """SHA-256 of the file's bytes (streamed; archive holds multi-MB files)."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_manifest(manifest_path: Path) -> dict[str, str]:
    """{archive-relative POSIX path: sha256 hex} from a GNU-format manifest.

    Universal-newline read (the archive manifest is CRLF); ``#`` comment
    lines and blank lines are skipped; a malformed non-comment line is an
    error, never silently dropped — a manifest that cannot be trusted to
    parse cannot anchor a read-only-forever guarantee.
    """
    entries: dict[str, str] = {}
    text = manifest_path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        digest, sep, name = line[:64], line[64:66], line[66:]
        if len(digest) == 64 and all(c in "0123456789abcdef" for c in digest.lower()) and sep in ("  ", " *") and name:
            if name in entries:
                raise ValueError(f"{manifest_path.name}:{lineno}: duplicate entry {name!r}")
            entries[name] = digest.lower()
        else:
            raise ValueError(f"{manifest_path.name}:{lineno}: malformed manifest line {line!r}")
    if not entries:
        raise ValueError(f"{manifest_path.name}: no entries parsed")
    return entries


def verify_manifest(
    archive_dir: Path = DEFAULT_ARCHIVE_DIR, manifest_name: str = MANIFEST_NAME
) -> IntegrityReport:
    """Verify archive_dir against its manifest, both directions. Pure check —
    no writes, no raise on failure (that is `require_intact`'s job)."""
    manifest_path = archive_dir / manifest_name
    pinned = parse_manifest(manifest_path)

    on_disk = {
        p.relative_to(archive_dir).as_posix()
        for p in archive_dir.rglob("*")
        if p.is_file() and p.name != manifest_name
    }

    matched: list[str] = []
    mismatched: list[tuple[str, str, str]] = []
    missing: list[str] = []
    for name, expected in sorted(pinned.items()):
        path = archive_dir / name
        if not path.is_file():
            missing.append(name)
            continue
        actual = sha256_file(path)
        if actual == expected:
            matched.append(name)
        else:
            mismatched.append((name, expected, actual))

    extra = sorted(on_disk - set(pinned))
    return IntegrityReport(
        archive_dir=archive_dir,
        matched=tuple(matched),
        mismatched=tuple(mismatched),
        missing=tuple(missing),
        extra=tuple(extra),
    )


def require_intact(
    archive_dir: Path = DEFAULT_ARCHIVE_DIR,
    manifest_name: str = MANIFEST_NAME,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
) -> IntegrityReport:
    """Verify, and on ANY failure write a dated report + raise.

    This is the gate every data-consuming calibration module calls before
    touching the archive. The report lands in `reports_dir` (default
    calibration/reports/) so the failure is a committed artifact, not a
    scrolled-away traceback.
    """
    report = verify_manifest(archive_dir, manifest_name)
    if report.ok:
        return report
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = reports_dir / f"integrity_failure_{stamp}.md"
    out_path.write_text(report.to_markdown(), encoding="utf-8")
    raise CalibrationIntegrityError(
        f"archive {archive_dir} FAILED integrity: "
        f"{len(report.mismatched)} mismatched, {len(report.missing)} missing, "
        f"{len(report.extra)} extra — report written to {out_path}"
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    archive_dir = Path(args[0]) if args else DEFAULT_ARCHIVE_DIR
    try:
        report = require_intact(archive_dir)
    except CalibrationIntegrityError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"INTACT: {len(report.matched)} files verified against {MANIFEST_NAME} in {archive_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
