import json
from datetime import datetime

from openpyxl import load_workbook

from getbill import converter
from getbill.converter import (
    is_supported,
    ConversionError,
    convert_csv_to_xlsx,
    convert_to_xlsx,
    output_stem,
    parquet_cell_value,
    safe_sheet_name,
    to_cell_value,
)
from getbill.prompts import parse_selection

import pytest


def convert(tmp_path, text, encoding="utf-8", **kwargs):
    source = tmp_path / "in.csv"
    source.write_bytes(text.encode(encoding))
    target = tmp_path / "out.xlsx"
    result = convert_csv_to_xlsx(source, target, sheet_name="Data", **kwargs)
    return result, load_workbook(target)["Data"]


def test_numbers_are_detected_and_ids_with_leading_zeros_stay_text(tmp_path):
    result, sheet = convert(tmp_path, "id,amount,code,big\n001,12.50,42,1234567890123456\n")
    assert (result.rows, result.columns) == (2, 4)
    assert [c.value for c in sheet[2]] == ["001", 12.5, 42, "1234567890123456"]


def test_tiny_costs_and_exponents_become_numbers(tmp_path):
    _, sheet = convert(tmp_path, "cost,rate,amount_paid\n0.0000004,1.5E-7,12\n")
    assert [c.value for c in sheet[2]] == [0.0000004, 1.5e-7, 12]


def test_identifier_columns_stay_text(tmp_path):
    _, sheet = convert(tmp_path, "line_item_usage_account_id,AccountId,Invoice ID\n444455556666,123,9876543210\n")
    assert [c.value for c in sheet[2]] == ["444455556666", "123", "9876543210"]


def test_header_is_bold_frozen_and_filtered(tmp_path):
    _, sheet = convert(tmp_path, "name,2024\nAnn,5\n")
    assert sheet["A1"].font.bold and sheet["B1"].value == "2024"  # Header stays text.
    assert sheet.freeze_panes == "A2"
    assert sheet.auto_filter.ref == "A1:B2"


def test_plain_mode_keeps_text_and_skips_formatting(tmp_path):
    _, sheet = convert(tmp_path, "a\n5\n", detect_numbers=False, formatting=False)
    assert sheet["A2"].value == "5" and not sheet["A1"].font.bold and sheet.freeze_panes is None


def test_semicolons_cp1252_and_formula_text(tmp_path):
    result, sheet = convert(tmp_path, "name;note\nCafé;=SUM(A1)\n", encoding="cp1252")
    assert result.delimiter == ";" and result.encoding == "cp1252"
    assert sheet["A2"].value == "Café"
    assert sheet["B2"].data_type == "s" and sheet["B2"].value == "=SUM(A1)"


def test_empty_file_gives_empty_sheet(tmp_path):
    result, _ = convert(tmp_path, "")
    assert result.rows == 0


def test_control_characters_are_removed():
    assert to_cell_value("a\x00b", detect_numbers=True) == "ab"


def test_sheet_name_is_made_valid():
    assert safe_sheet_name("a/b:c" + "x" * 40) == ("a_b_c" + "x" * 40)[:31]


def test_output_stem_removes_file_type_and_compression_name():
    assert output_stem("report.csv") == "report"
    assert output_stem("part-00001.snappy.parquet") == "part-00001"
    assert output_stem("Data.PARQUET") == "Data"


def test_parquet_values_keep_their_types():
    assert parquet_cell_value([("team", "genai")], is_map=True) == '{"team": "genai"}'
    assert parquet_cell_value(444455556666, is_id=True) == "444455556666"
    assert parquet_cell_value(444455556666.0, is_id=True) == "444455556666"
    assert parquet_cell_value(1.25) == 1.25
    assert parquet_cell_value(float("nan")) is None
    assert parquet_cell_value("=SUM(A1)") == "=SUM(A1)"


def test_cur2_parquet_converts_with_types(tmp_path, cur2_parquet):
    source = tmp_path / "cur2.snappy.parquet"
    source.write_bytes(cur2_parquet)
    target = tmp_path / "out.xlsx"
    result = convert_to_xlsx(source, target, sheet_name="cur2")
    assert result.file_format == "Parquet" and result.columns == 58 and result.rows > 300

    sheet = load_workbook(target)["cur2"]
    headings = [cell.value for cell in sheet[1]]
    row = {heading: cell.value for heading, cell in zip(headings, sheet[2])}
    assert sheet["A1"].font.bold and sheet.freeze_panes == "A2"
    assert isinstance(row["line_item_unblended_cost"], float)
    assert isinstance(row["line_item_usage_account_id"], str) and len(row["line_item_usage_account_id"]) == 12
    assert isinstance(row["line_item_usage_start_date"], datetime)
    assert "servicename" in json.loads(row["product"])
    products = {sheet.cell(row=r, column=headings.index("line_item_product_code") + 1).value for r in range(2, sheet.max_row + 1)}
    assert {"AmazonBedrock", "AWSGlue"} <= products


def test_unsupported_and_broken_files_fail_clearly(tmp_path):
    with pytest.raises(ConversionError):
        convert_to_xlsx(tmp_path / "data.json", tmp_path / "out.xlsx")
    pytest.importorskip("pyarrow")
    broken = tmp_path / "broken.parquet"
    broken.write_bytes(b"this is not parquet")
    with pytest.raises(ConversionError):
        convert_to_xlsx(broken, tmp_path / "out.xlsx")


def test_parse_selection():
    assert parse_selection("1,3-4", 5) == [0, 2, 3]
    assert parse_selection("all", 3) == [0, 1, 2]
    with pytest.raises(ValueError):
        parse_selection("6", 5)


@pytest.mark.parametrize("text, expected", [
    ("42", 42),
    ("-7", -7),
    ("0", 0),
    (" 5 ", 5),
    ("3.14", 3.14),
    ("-.5", -0.5),
    ("1.5E-7", 1.5e-7),
    ("007", "007"),
    ("1,000", "1,000"),
    ("1e5", "1e5"),
    ("12345678901234567", "12345678901234567"),
    ("abc", "abc"),
])
def test_csv_values_that_look_like_numbers(text, expected):
    assert to_cell_value(text, detect_numbers=True) == expected


def test_number_detection_can_be_turned_off():
    assert to_cell_value("42", detect_numbers=False) == "42"


@pytest.mark.parametrize("name, supported", [
    ("report.csv", True),
    ("REPORT.CSV", True),
    ("part-00001.snappy.parquet", True),
    ("report.csv.gz", False),
    ("notes.txt", False),
])
def test_only_csv_and_parquet_files_are_supported(name, supported):
    assert is_supported(name) is supported


def test_too_many_rows_for_excel_fails_clearly(tmp_path, monkeypatch):
    monkeypatch.setattr(converter, "EXCEL_MAX_ROWS", 3)
    source = tmp_path / "big.csv"
    source.write_text("a\n1\n2\n3\n")
    with pytest.raises(ConversionError, match="at most 3"):
        convert_csv_to_xlsx(source, tmp_path / "out.xlsx")


def test_parquet_with_no_rows_gives_a_header_only_sheet(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    table = pa.table({"cost": pa.array([], pa.float64()), "line_item_usage_account_id": pa.array([], pa.string())})
    pq.write_table(table, tmp_path / "empty.parquet")
    result = convert_to_xlsx(tmp_path / "empty.parquet", tmp_path / "out.xlsx", sheet_name="empty")
    assert result.rows == 1
    sheet = load_workbook(tmp_path / "out.xlsx")["empty"]
    assert [cell.value for cell in sheet[1]] == ["cost", "line_item_usage_account_id"]
    assert sheet.max_row == 1
