"""Versioned raw-trace ingestion — blocker-independent tier of
docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md §1/§3.

Loads per-trace spectra (frequency, signal) from graded, versioned derived
CSVs, in the `load_digitized` refusal tradition: an ungraded or
unversioned file does not load, ever. No "latest" magic — callers name the
`dataset_version` explicitly.

Dataset-version convention (plan §1.3):
    cowley_semple_<date>-digitized | cowley_semple_<date>-raw | ...
The existing digitized dataset is immutable and is SUPERSEDED, never
overwritten (see calibration/supersession.py for the D7 transaction).

Derived-trace file contract — leading '# key: value' header lines, then a
CSV body 'frequency_hz,signal':

    # dataset_version: cowley_semple_2026-08-01-raw
    # grade: raw-trace
    # source_archive: calibration/data/raw/cowley_semple_2026-08-01/
    # source_member: spectra/d14_3.81mW.csv
    # source_sha256: <64 hex>
    # sample_id: d14
    # optical_power_mw: 3.81
    # power_plane: unknown
    # freq_unit: Hz
    # parser: calibration.raw_ingest v1
    frequency_hz,signal
    1.4490e9,0.9987
    ...

Emailed-table transcriptions additionally require
'# transcription_check: verified-against-archive' (plan §1.2: every value
re-read against the archive by a second pass; the check recorded in the
header).

This module never writes production artifacts and never touches
`calibration/data/`; derived files are written by the (future) reply
changeset, dry-runs go to caller-chosen temp paths.
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from calibration.constants import EXCITATION
from calibration.reply_schema import PowerPlane

_HEADER_RE = re.compile(r"^#\s*([A-Za-z0-9_]+)\s*:\s*(.*)$")

REQUIRED_HEADER_KEYS: tuple[str, ...] = (
    "dataset_version",
    "grade",
    "source_archive",
    "source_member",
    "source_sha256",
    "sample_id",
    "optical_power_mw",
    "power_plane",
    "freq_unit",
    "parser",
)

#: Grades a trace file may carry. 'graph-digitized-provisional' stays legal
#: so the digitized record remains loadable through the same door.
ALLOWED_GRADES: tuple[str, ...] = (
    "raw-trace",
    "raw-derived",
    "emailed-table-transcription",
    "graph-digitized-provisional",
    "fixture",
)


class RawIngestError(ValueError):
    """A trace file fails the contract. Refusal, not repair."""


@dataclass(frozen=True)
class TraceRecord:
    """One loaded spectrum trace + its provenance header.

    `mw_power` and the acquisition-protocol keys (settling time, sweep
    direction, dwell, order — plan §2) ride the header verbatim; the two
    most load-bearing get typed accessors (adversarial-review fix,
    2026-07-20)."""

    dataset_version: str
    grade: str
    source_archive: str
    source_member: str
    source_sha256: str
    sample_id: str
    optical_power_mw: float
    power_plane: PowerPlane
    freq_hz: np.ndarray
    signal: np.ndarray
    header: dict[str, str]
    path: Path
    mw_power_dbm: float | None = None
    source_verified: bool = False

    @property
    def is_fixture(self) -> bool:
        return self.grade == "fixture" or "FIXTURE" in self.dataset_version.upper()

    @property
    def acquisition_metadata(self) -> dict[str, str]:
        keys = (
            "settling_time_s",
            "sweep_direction",
            "dwell_per_point_s",
            "trace_order",
            "repeat_index",
        )
        return {k: self.header[k] for k in keys if k in self.header}


def _parse_header_and_body(text: str, origin: str) -> tuple[dict[str, str], str]:
    header: dict[str, str] = {}
    body_lines: list[str] = []
    in_header = True
    for line in text.splitlines():
        if in_header:
            m = _HEADER_RE.match(line)
            if m:
                key = m.group(1).lower()
                if key in header:
                    raise RawIngestError(f"{origin}: duplicate header key {key!r}")
                header[key] = m.group(2).strip()
                continue
            in_header = False
        body_lines.append(line)
    missing = [k for k in REQUIRED_HEADER_KEYS if k not in header]
    if missing:
        raise RawIngestError(
            f"{origin}: ungraded/unversioned trace refused — missing header "
            f"keys {missing} (the load_digitized refusal tradition)"
        )
    if header["grade"] not in ALLOWED_GRADES:
        raise RawIngestError(
            f"{origin}: unknown grade {header['grade']!r}; "
            f"allowed: {ALLOWED_GRADES}"
        )
    if header["grade"] == "emailed-table-transcription" and header.get(
        "transcription_check"
    ) != "verified-against-archive":
        raise RawIngestError(
            f"{origin}: emailed-table transcription without "
            "'transcription_check: verified-against-archive' (plan §1.2 — "
            "every value re-read against the archive by a second pass)"
        )
    if not re.fullmatch(r"[0-9a-f]{64}", header["source_sha256"].lower()):
        raise RawIngestError(f"{origin}: source_sha256 is not 64 hex chars")
    return header, "\n".join(body_lines)


_FREQ_SCALE = {"hz": 1.0, "khz": 1e3, "mhz": 1e6, "ghz": 1e9}


def _parse_body(body: str, freq_unit: str, origin: str) -> tuple[np.ndarray, np.ndarray]:
    try:
        scale = _FREQ_SCALE[freq_unit.strip().lower()]
    except KeyError:
        raise RawIngestError(
            f"{origin}: freq_unit {freq_unit!r} not one of {sorted(_FREQ_SCALE)}"
        ) from None
    stream = io.StringIO(body)
    first = stream.readline().strip().lower()
    if not first.startswith("frequency"):
        raise RawIngestError(
            f"{origin}: body must start with a 'frequency*,signal' column "
            f"header, got {first!r}"
        )
    try:
        data = np.loadtxt(stream, delimiter=",", ndmin=2)
    except ValueError as exc:
        raise RawIngestError(f"{origin}: non-numeric body: {exc}") from exc
    if data.shape[0] < 3 or data.shape[1] != 2:
        raise RawIngestError(
            f"{origin}: need >= 3 rows of exactly (frequency, signal), "
            f"got shape {data.shape}"
        )
    freq = data[:, 0] * scale
    signal = data[:, 1]
    if not np.all(np.isfinite(freq)) or not np.all(np.isfinite(signal)):
        raise RawIngestError(f"{origin}: non-finite values in body")
    diffs = np.diff(freq)
    if not (np.all(diffs > 0) or np.all(diffs < 0)):
        raise RawIngestError(
            f"{origin}: frequency axis must be strictly monotonic"
        )
    return freq, signal


def load_trace(path: Path) -> TraceRecord:
    """Load one derived trace file under the full contract."""
    text = path.read_text(encoding="utf-8")
    header, body = _parse_header_and_body(text, origin=path.name)
    freq, signal = _parse_body(body, header["freq_unit"], origin=path.name)
    try:
        power = float(header["optical_power_mw"])
    except ValueError:
        raise RawIngestError(
            f"{path.name}: optical_power_mw not a number"
        ) from None
    # Unit-slip guard derived from the graded source (adversarial-review
    # fix: was a bare 10 W literal): the rig diode is EXCITATION
    # .max_power_mw = 15 mW; two orders of magnitude of headroom admits
    # any plausible future source while catching a W-vs-mW transcription.
    power_ceiling_mw = 100.0 * EXCITATION.max_power_mw
    if not (power == power and 0 < power < power_ceiling_mw):
        raise RawIngestError(
            f"{path.name}: implausible optical_power_mw {power} "
            f"(unit-slip guard: ceiling {power_ceiling_mw} mW = 100 x the "
            "graded diode maximum)"
        )
    plane_raw = header["power_plane"].strip().lower().replace("_", "-")
    try:
        plane = PowerPlane(plane_raw)
    except ValueError:
        raise RawIngestError(
            f"{path.name}: power_plane {header['power_plane']!r} not one of "
            f"{[p.value for p in PowerPlane]}"
        ) from None
    mw_power = None
    if "mw_power_dbm" in header:
        try:
            mw_power = float(header["mw_power_dbm"])
        except ValueError:
            raise RawIngestError(
                f"{path.name}: mw_power_dbm not a number"
            ) from None
    # Source-hash VERIFICATION (adversarial-review fix, 2026-07-20): a
    # syntactically valid sha is not provenance — for non-fixture grades
    # the named archive member must exist in the repo and hash-match.
    source_verified = False
    if (
        header["grade"] != "fixture"
        and "FIXTURE" not in header["dataset_version"].upper()
    ):
        repo_root = _PACKAGE_DIR.parent
        member = (
            repo_root
            / header["source_archive"].strip("/\\")
            / header["source_member"]
        )
        if not member.is_file():
            raise RawIngestError(
                f"{path.name}: source member "
                f"{header['source_archive']}/{header['source_member']} not "
                "found in the repo — archive the raw attachment first "
                "(plan §0 step zero)"
            )
        actual = hashlib.sha256(member.read_bytes()).hexdigest()
        if actual != header["source_sha256"].lower():
            raise RawIngestError(
                f"{path.name}: source_sha256 does not match the archived "
                f"member ({actual[:12]}… on disk)"
            )
        source_verified = True
    return TraceRecord(
        dataset_version=header["dataset_version"],
        grade=header["grade"],
        source_archive=header["source_archive"],
        source_member=header["source_member"],
        source_sha256=header["source_sha256"],
        sample_id=header["sample_id"],
        optical_power_mw=power,
        power_plane=plane,
        freq_hz=freq,
        signal=signal,
        header=header,
        path=path,
        mw_power_dbm=mw_power,
        source_verified=source_verified,
    )


def load_dataset(root: Path, dataset_version: str) -> tuple[TraceRecord, ...]:
    """Load every trace of ONE named dataset version under `root`
    (recursive). The version is EXPLICIT — no 'latest' resolution exists
    by design (plan §1.3). Selection parses each candidate's FULL header
    and compares the parsed dataset_version for exact equality
    (adversarial-review fix: no substring sniffing). Files without any
    trace header are ignored; zero matches is an error."""
    traces = []
    for path in sorted(root.rglob("*.csv")):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not text.lstrip().startswith("#"):
            continue  # not a trace-contract file
        try:
            header, _ = _parse_header_and_body(text, origin=path.name)
        except RawIngestError:
            continue  # carries comments but not the trace contract
        if header["dataset_version"] != dataset_version:
            continue
        traces.append(load_trace(path))
    if not traces:
        raise RawIngestError(
            f"no traces of dataset_version {dataset_version!r} under {root}"
        )
    keys = {(t.sample_id, t.optical_power_mw, t.mw_power_dbm) for t in traces}
    if len(keys) != len(traces):
        raise RawIngestError(
            f"duplicate (sample, optical power, MW power) traces in "
            f"{dataset_version!r}"
        )
    return tuple(traces)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def render_trace_csv(
    *,
    header: dict[str, str],
    freq: np.ndarray,
    signal: np.ndarray,
) -> str:
    """Deterministic serialisation of a derived trace (the writer half the
    reply changeset will use; fixtures use it in tests). Header keys are
    written in REQUIRED order then extras alphabetically."""
    missing = [k for k in REQUIRED_HEADER_KEYS if k not in header]
    if missing:
        raise RawIngestError(f"render refused — missing header keys {missing}")
    ordered = list(REQUIRED_HEADER_KEYS) + sorted(
        k for k in header if k not in REQUIRED_HEADER_KEYS
    )
    lines = [f"# {k}: {header[k]}" for k in ordered]
    lines.append("frequency_hz,signal")
    for f_hz, s in zip(freq, signal):
        lines.append(f"{f_hz:.6e},{s:.9e}")
    return "\n".join(lines) + "\n"
