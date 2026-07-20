"""Deterministic XLSX reader guards (calibration/tools/xlsx_to_csv.py).

Synthetic workbooks are built in-test (stdlib zipfile + hand-rolled OOXML
parts) so the reader's refusals — formula-without-cached-value, unknown
sheet, quoting-hostile cells — are exercised without any binary fixture."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from calibration.tools.xlsx_to_csv import (
    XlsxError,
    list_sheets,
    read_sheet,
    sheet_to_csv_text,
)

_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="data" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WB_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

_SHARED = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2" uniqueCount="2">
<si><t>power_mW</t></si><si><t>centre_MHz</t></si>
</sst>"""


def _sheet_xml(rows_xml: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main"><sheetData>'
        f"{rows_xml}</sheetData></worksheet>"
    )


def _write_xlsx(path: Path, sheet_xml: str) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", _CT)
        zf.writestr("_rels/.rels", _ROOT_RELS)
        zf.writestr("xl/workbook.xml", _WORKBOOK)
        zf.writestr("xl/_rels/workbook.xml.rels", _WB_RELS)
        zf.writestr("xl/sharedStrings.xml", _SHARED)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return path


GOOD_ROWS = (
    '<row r="1">'
    '<c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
    '<row r="2"><c r="A2"><v>3.81</v></c><c r="B2"><v>1449.7</v></c></row>'
    '<row r="3"><c r="A3"><v>6.06</v></c><c r="B3"><v>1449.4</v></c></row>'
)


class TestReader:
    def test_reads_grid_and_lists_sheets(self, tmp_path):
        path = _write_xlsx(tmp_path / "ok.xlsx", _sheet_xml(GOOD_ROWS))
        assert list_sheets(path) == ("data",)
        grid = read_sheet(path, "data")
        assert grid.rows[0] == ("power_mW", "centre_MHz")
        assert grid.rows[1] == (3.81, 1449.7)
        assert grid.rows[2] == (6.06, 1449.4)

    def test_csv_render_deterministic(self, tmp_path):
        path = _write_xlsx(tmp_path / "ok.xlsx", _sheet_xml(GOOD_ROWS))
        grid = read_sheet(path, "data")
        assert sheet_to_csv_text(grid) == sheet_to_csv_text(grid)
        assert sheet_to_csv_text(grid).splitlines()[0] == "power_mW,centre_MHz"

    def test_unknown_sheet_refused(self, tmp_path):
        path = _write_xlsx(tmp_path / "ok.xlsx", _sheet_xml(GOOD_ROWS))
        with pytest.raises(XlsxError, match="not found"):
            read_sheet(path, "nope")

    def test_formula_without_cached_value_refused(self, tmp_path):
        rows = (
            '<row r="1"><c r="A1"><f>SUM(B1:B9)</f></c></row>'
        )
        path = _write_xlsx(tmp_path / "formula.xlsx", _sheet_xml(rows))
        with pytest.raises(XlsxError, match="formula"):
            read_sheet(path, "data")

    def test_formula_with_cached_value_uses_cache(self, tmp_path):
        rows = '<row r="1"><c r="A1"><f>1+1</f><v>2</v></c></row>'
        path = _write_xlsx(tmp_path / "cached.xlsx", _sheet_xml(rows))
        assert read_sheet(path, "data").rows[0] == (2.0,)

    def test_comma_cell_refused_in_csv_render(self, tmp_path):
        rows = '<row r="1"><c r="A1" t="inlineStr"><is><t>a,b</t></is></c></row>'
        path = _write_xlsx(tmp_path / "comma.xlsx", _sheet_xml(rows))
        grid = read_sheet(path, "data")
        with pytest.raises(XlsxError, match="quoting"):
            sheet_to_csv_text(grid)

    def test_extract_trace_csv_records_mapping_and_workbook_sha(self, tmp_path):
        """The graded conversion entry point (plan §1.2): pinned
        sheet/column mapping + workbook SHA-256 in the derived header."""
        import hashlib

        from calibration.raw_ingest import load_trace
        from calibration.tools.xlsx_to_csv import extract_trace_csv

        rows = (
            '<row r="1">'
            '<c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>'
            '<row r="2"><c r="A2"><v>1448.0</v></c><c r="B2"><v>1.0</v></c></row>'
            '<row r="3"><c r="A3"><v>1449.0</v></c><c r="B3"><v>0.95</v></c></row>'
            '<row r="4"><c r="A4"><v>1450.0</v></c><c r="B4"><v>0.99</v></c></row>'
        )
        path = _write_xlsx(tmp_path / "traces.xlsx", _sheet_xml(rows))
        text = extract_trace_csv(
            path,
            sheet_name="data",
            freq_column=0,
            signal_column=1,
            skip_rows=1,
            header={
                "dataset_version": "FIXTURE-XLSX",
                "grade": "fixture",
                "source_archive": "FIXTURE: none",
                "source_member": "traces.xlsx::data",
                "source_sha256": "0" * 64,
                "sample_id": "d14",
                "optical_power_mw": "3.81",
                "power_plane": "unknown",
                "freq_unit": "MHz",
                "parser": "xlsx fixture v1",
            },
        )
        assert "# xlsx_sheet: data" in text
        assert "# xlsx_freq_column: 0" in text
        expected_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert f"# xlsx_workbook_sha256: {expected_sha}" in text
        out = tmp_path / "trace.csv"
        out.write_text(text, encoding="utf-8")
        record = load_trace(out)
        assert record.freq_hz[0] == pytest.approx(1448.0e6)

    def test_sparse_cells_become_empty(self, tmp_path):
        rows = (
            '<row r="1"><c r="A1"><v>1</v></c><c r="C1"><v>3</v></c></row>'
        )
        path = _write_xlsx(tmp_path / "sparse.xlsx", _sheet_xml(rows))
        grid = read_sheet(path, "data")
        assert grid.rows[0] == (1.0, None, 3.0)
        assert sheet_to_csv_text(grid).splitlines()[0] == "1.0,,3.0"
