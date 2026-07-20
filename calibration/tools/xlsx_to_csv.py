"""Deterministic XLSX → CSV extraction (stdlib-only, deliberately narrow).

Plan §1.2: if Cowley-Semple's raw data arrives as XLSX, the archived file
stays as-sent and a committed, deterministic converter produces the
derived CSVs, with the pinned sheet/column mapping recorded in the derived
header. Neither `openpyxl` nor `pandas` is a project dependency, so this
is a minimal reader over the OOXML zip: worksheet cell values only.

REFUSALS (never silently coerced):
- formula cells without a cached value (we never evaluate formulas);
- unknown/rich cell types; shared-string indices out of range;
- sheets that don't exist.
Dates are NOT decoded and NOT detected (style/number-format inspection is
deliberately out of this reader's scope): a date-typed axis surfaces as
implausible raw serial numbers, which the derived-header unit and
plausibility checks in `calibration.raw_ingest` refuse downstream — the
correct resolution is asking for a plain values export, never guessing an
epoch. (Docstring corrected 2026-07-20: an earlier draft promised a
per-cell date warning this reader does not implement.)

`extract_trace_csv` is the graded conversion entry point: it glues
`read_sheet` to `calibration.raw_ingest.render_trace_csv`, recording the
pinned sheet/column mapping and the source workbook's SHA-256 in the
derived header (plan §1.2's "pinned sheet/column mapping recorded in the
derived header").
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = {
    "r": "http://schemas.openxmlformats.org/package/2006/relationships"
}
_R_ATTR = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
)


class XlsxError(ValueError):
    """The workbook cannot be read deterministically. Refusal, not repair."""


@dataclass(frozen=True)
class SheetGrid:
    """One worksheet as a dense row-major grid of str|float|None."""

    name: str
    rows: tuple[tuple[object, ...], ...]
    warnings: tuple[str, ...]


def _column_index(cell_ref: str) -> int:
    m = re.match(r"^([A-Z]+)\d+$", cell_ref)
    if not m:
        raise XlsxError(f"unparseable cell reference {cell_ref!r}")
    idx = 0
    for ch in m.group(1):
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def list_sheets(path: Path) -> tuple[str, ...]:
    with zipfile.ZipFile(path) as zf:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    return tuple(
        sheet.get("name", "")
        for sheet in workbook.findall("m:sheets/m:sheet", _NS)
    )


def _sheet_target(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_by_id = {
        rel.get("Id"): rel.get("Target")
        for rel in rels.findall("r:Relationship", _REL_NS)
    }
    for sheet in workbook.findall("m:sheets/m:sheet", _NS):
        if sheet.get("name") == sheet_name:
            target = rel_by_id.get(sheet.get(_R_ATTR))
            if not target:
                raise XlsxError(f"no relationship for sheet {sheet_name!r}")
            return "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
    raise XlsxError(
        f"sheet {sheet_name!r} not found; sheets: {list(rel_by_id)}"
    )


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    strings = []
    for si in root.findall("m:si", _NS):
        strings.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
    return strings


def read_sheet(path: Path, sheet_name: str) -> SheetGrid:
    """Extract one sheet's cell values as a dense grid."""
    warnings: list[str] = []
    with zipfile.ZipFile(path) as zf:
        shared = _shared_strings(zf)
        sheet_xml = ET.fromstring(zf.read(_sheet_target(zf, sheet_name)))
        cells: dict[tuple[int, int], object] = {}
        max_col = -1
        max_row = -1
        for row in sheet_xml.findall("m:sheetData/m:row", _NS):
            for cell in row.findall("m:c", _NS):
                ref = cell.get("r")
                if ref is None:
                    raise XlsxError("cell without a reference attribute")
                r_idx = int(re.sub(r"[A-Z]+", "", ref)) - 1
                c_idx = _column_index(ref)
                ctype = cell.get("t", "n")
                value_el = cell.find("m:v", _NS)
                formula_el = cell.find("m:f", _NS)
                if formula_el is not None and value_el is None:
                    raise XlsxError(
                        f"{ref}: formula cell without a cached value — "
                        "refused; ask for a values-only export"
                    )
                if ctype == "inlineStr":
                    # inline strings carry no <v>; the text lives in <is><t>
                    value: object = "".join(
                        t.text or ""
                        for t in cell.iter(f"{{{_NS['m']}}}t")
                    )
                elif value_el is None:
                    value = None
                elif ctype == "s":
                    idx = int(value_el.text or "-1")
                    if not (0 <= idx < len(shared)):
                        raise XlsxError(f"{ref}: shared string {idx} out of range")
                    value = shared[idx]
                elif ctype in ("n", ""):
                    value = float(value_el.text or "nan")
                elif ctype == "str":
                    value = value_el.text or ""
                elif ctype == "b":
                    value = float(value_el.text or "0")
                    warnings.append(f"{ref}: boolean cell read as {value}")
                else:
                    raise XlsxError(f"{ref}: unsupported cell type {ctype!r}")
                cells[(r_idx, c_idx)] = value
                max_col = max(max_col, c_idx)
                max_row = max(max_row, r_idx)
    rows = tuple(
        tuple(cells.get((r, c)) for c in range(max_col + 1))
        for r in range(max_row + 1)
    )
    return SheetGrid(name=sheet_name, rows=rows, warnings=tuple(warnings))


def extract_trace_csv(
    path: Path,
    *,
    sheet_name: str,
    freq_column: int,
    signal_column: int,
    skip_rows: int,
    header: dict[str, str],
) -> str:
    """Graded conversion entry point (plan §1.2): one (sheet, columns)
    mapping → one derived trace CSV via `raw_ingest.render_trace_csv`.
    The mapping and the source workbook's SHA-256 are recorded in the
    derived header; non-numeric cells in the mapped columns refuse."""
    import hashlib

    import numpy as np

    from calibration.raw_ingest import render_trace_csv

    grid = read_sheet(path, sheet_name)
    freq_vals: list[float] = []
    signal_vals: list[float] = []
    for row_index, row in enumerate(grid.rows):
        if row_index < skip_rows:
            continue
        try:
            f_val = row[freq_column]
            s_val = row[signal_column]
        except IndexError:
            raise XlsxError(
                f"row {row_index + 1}: mapped column out of range"
            ) from None
        if f_val is None and s_val is None:
            continue  # trailing blank row
        if not isinstance(f_val, float) or not isinstance(s_val, float):
            raise XlsxError(
                f"row {row_index + 1}: non-numeric cell in mapped columns "
                f"({f_val!r}, {s_val!r}) — ask for a values-only export"
            )
        freq_vals.append(f_val)
        signal_vals.append(s_val)
    workbook_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    full_header = dict(header)
    full_header.update(
        {
            "xlsx_sheet": sheet_name,
            "xlsx_freq_column": str(freq_column),
            "xlsx_signal_column": str(signal_column),
            "xlsx_skip_rows": str(skip_rows),
            "xlsx_workbook_sha256": workbook_sha,
        }
    )
    return render_trace_csv(
        header=full_header,
        freq=np.asarray(freq_vals),
        signal=np.asarray(signal_vals),
    )


def sheet_to_csv_text(grid: SheetGrid) -> str:
    """Deterministic CSV render (no quoting surprises: cells containing
    commas/newlines are refused — the scientific tables this exists for
    have none, and silent quoting is where determinism goes to die)."""
    lines = []
    for row in grid.rows:
        out = []
        for value in row:
            if value is None:
                out.append("")
            elif isinstance(value, float):
                out.append(repr(value))
            else:
                text = str(value)
                if "," in text or "\n" in text or '"' in text:
                    raise XlsxError(
                        f"cell value {text!r} needs quoting — refused for "
                        "determinism; ask for a plain export"
                    )
                out.append(text)
        lines.append(",".join(out))
    return "\n".join(lines) + "\n"
