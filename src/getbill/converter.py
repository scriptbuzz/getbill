"""Convert a CSV or Parquet file on disk into a formatted Excel workbook on disk.

This module has no knowledge of S3, so it can be tested and reused on its own.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import List, Union

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLUMNS = 16_384
MIN_COLUMN_WIDTH = 8
MAX_COLUMN_WIDTH = 60
# Excel keeps only 15 significant digits, so longer whole numbers stay text to avoid
# silently changing values such as card or order numbers.
MAX_SAFE_DIGITS = 15

# A whole number without leading zeros, such as 0, 42 or -7. "007" does not match.
_INTEGER = re.compile(r"^-?(0|[1-9][0-9]*)$")
# A decimal number without leading zeros, such as 3.14, -0.5, .25 or 1.5E-7.
_DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)?\.[0-9]+([eE][-+]?[0-9]+)?$")
# A column heading that names an identifier, such as "line_item_usage_account_id",
# "AccountId" or "Invoice ID". Values in these columns always stay text, so Excel does
# not show a 12-digit AWS account ID as 1.23457E+11.
# The match is case-sensitive, so a heading such as "amount_paid" is not an identifier.
_ID_HEADER = re.compile(r"(^|[_\s.-])(id|Id|ID)$|[a-z](Id|ID)$")
_SHEET_NAME_FORBIDDEN = re.compile(r"[\[\]:*?/\\]")

PathLike = Union[str, Path]

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


CSV_SUFFIX = ".csv"
PARQUET_SUFFIX = ".parquet"
SUPPORTED_SUFFIXES = (CSV_SUFFIX, PARQUET_SUFFIX)
# Compression names that tools put in Parquet file names, as in "part-00001.snappy.parquet".
_PARQUET_COMPRESSION_NAMES = (".snappy", ".gz", ".gzip", ".zstd", ".lz4", ".brotli")
DATETIME_FORMAT = "yyyy-mm-dd hh:mm:ss"
PARQUET_BATCH_ROWS = 10_000


class ConversionError(Exception):
    """The file cannot be turned into an Excel workbook."""


@dataclass
class ConversionResult:
    rows: int
    columns: int
    file_format: str = "CSV"
    encoding: str = ""
    delimiter: str = ""


def is_supported(name: str) -> bool:
    """Return True for file names the tool can convert, such as data.csv or part.snappy.parquet."""
    return name.lower().endswith(SUPPORTED_SUFFIXES)


def output_stem(name: str) -> str:
    """Return the file name without its type, used to name the workbook and its sheet.

    "report.csv" gives "report", and "part-00001.snappy.parquet" gives "part-00001".
    """
    lower = name.lower()
    for suffix in SUPPORTED_SUFFIXES:
        if lower.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if lower.endswith(PARQUET_SUFFIX):
        for compression in _PARQUET_COMPRESSION_NAMES:
            if name.lower().endswith(compression):
                return name[: -len(compression)]
    return name


def detect_encoding(path: PathLike) -> str:
    """Return "utf-8-sig" when the file is valid UTF-8, otherwise "cp1252" or "latin-1"."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=encoding) as handle:
                while handle.read(1024 * 1024):
                    pass
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"  # Every byte sequence is valid latin-1, so this never fails.


def detect_delimiter(path: PathLike, encoding: str) -> str:
    """Guess whether the file separates values with commas, semicolons, tabs or pipes."""
    with open(path, encoding=encoding, newline="") as handle:
        sample = handle.read(64 * 1024)
    if not sample:
        return ","
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def to_cell_value(text: str, detect_numbers: bool) -> Union[str, int, float]:
    """Return a number for number-like text, and the cleaned text for everything else."""
    if detect_numbers:
        candidate = text.strip()
        # Count significant digits only: the zeros in 0.0000004 do not count.
        mantissa = re.split("[eE]", candidate)[0]
        digits = len(mantissa.lstrip("-").replace(".", "").lstrip("0"))
        if _INTEGER.match(candidate) and digits <= MAX_SAFE_DIGITS:
            return int(candidate)
        if _DECIMAL.match(candidate) and digits <= MAX_SAFE_DIGITS:
            return float(candidate)
    # Excel rejects control characters such as NUL, so they are removed.
    return ILLEGAL_CHARACTERS_RE.sub("", text)


def safe_sheet_name(name: str) -> str:
    """Make a name Excel accepts for a sheet: at most 31 characters, no []:*?/\\."""
    cleaned = _SHEET_NAME_FORBIDDEN.sub("_", name).strip("'").strip()
    return cleaned[:31] or "Sheet1"


def _make_cell(sheet, value, bold: bool) -> WriteOnlyCell:
    cell = WriteOnlyCell(sheet, value=value)
    if isinstance(value, str) and value.startswith("="):
        # Store text that starts with "=" as plain text. Otherwise Excel would run it
        # as a formula, which is a known way to attack people who open CSV exports.
        cell.data_type = "s"
    if isinstance(value, datetime):
        cell.number_format = DATETIME_FORMAT
    if bold:
        cell.font = Font(bold=True)
    return cell


def _set_layout(sheet, widths: List[int], row_count: int, column_count: int) -> None:
    """Set column widths, freeze the header row, and add filter buttons to the header."""
    for index, width in enumerate(widths, start=1):
        letter = get_column_letter(index)
        sheet.column_dimensions[letter].width = min(max(width + 2, MIN_COLUMN_WIDTH), MAX_COLUMN_WIDTH)
    if row_count > 1:
        sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(column_count)}{row_count}"


def _check_size(row_count: int, column_count: int) -> None:
    if row_count > EXCEL_MAX_ROWS:
        raise ConversionError(
            f"The file has {row_count:,} rows, but an Excel sheet holds at most {EXCEL_MAX_ROWS:,}."
        )
    if column_count > EXCEL_MAX_COLUMNS:
        raise ConversionError(
            f"The file has {column_count:,} columns, but an Excel sheet holds at most {EXCEL_MAX_COLUMNS:,}."
        )


def convert_csv_to_xlsx(
    csv_path: PathLike,
    xlsx_path: PathLike,
    sheet_name: str = "Sheet1",
    detect_numbers: bool = True,
    formatting: bool = True,
) -> ConversionResult:
    """Write the CSV at csv_path as an Excel workbook at xlsx_path.

    The file is read twice: the first pass measures the row count and column widths,
    the second pass writes the cells. This keeps memory use low for large files.
    """
    encoding = detect_encoding(csv_path)
    delimiter = detect_delimiter(csv_path, encoding)

    row_count = 0
    column_count = 0
    widths: List[int] = []
    with open(csv_path, encoding=encoding, newline="") as handle:
        for row in csv.reader(handle, delimiter=delimiter):
            row_count += 1
            column_count = max(column_count, len(row))
            for index, value in enumerate(row):
                longest_line = max((len(line) for line in value.splitlines()), default=0)
                if index >= len(widths):
                    widths.append(longest_line)
                elif longest_line > widths[index]:
                    widths[index] = longest_line

    _check_size(row_count, column_count)

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(title=safe_sheet_name(sheet_name))

    if formatting and row_count:
        _set_layout(sheet, widths, row_count, column_count)

    id_columns = set()
    with open(csv_path, encoding=encoding, newline="") as handle:
        for row_number, row in enumerate(csv.reader(handle, delimiter=delimiter)):
            is_header = row_number == 0
            if is_header:
                id_columns = {index for index, heading in enumerate(row) if _ID_HEADER.search(heading.strip())}
            cells = [
                _make_cell(
                    sheet,
                    # The header row and identifier columns always stay text.
                    to_cell_value(value, detect_numbers and not is_header and index not in id_columns),
                    bold=formatting and is_header,
                )
                for index, value in enumerate(row)
            ]
            sheet.append(cells)

    workbook.save(xlsx_path)
    return ConversionResult(rows=row_count, columns=column_count, encoding=encoding, delimiter=delimiter)


# ---------------------------------------------------------------- Parquet


def _json_default(value):
    """Turn values that JSON cannot hold, such as dates and decimals, into JSON-friendly ones."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def parquet_cell_value(value, is_map: bool = False, is_id: bool = False):
    """Turn one Parquet value into a value Excel can store.

    Parquet columns already have types, so numbers stay numbers and text stays text,
    without guessing. Maps, structs, and lists become JSON text, such as the
    resource_tags column in a CUR 2.0 export.
    """
    if value is None:
        return None
    if is_map:
        # pyarrow returns a map as a list of (key, value) pairs.
        value = {str(key): item for key, item in value}
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, default=_json_default, ensure_ascii=False)
        return ILLEGAL_CHARACTERS_RE.sub("", text)
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None  # Excel has no cell value for "not a number" or infinity.
        if is_id:
            # An ID stored as a whole floating-point number, such as 444455556666.0,
            # is written as 444455556666, without the ".0".
            return str(int(value)) if value.is_integer() else str(value)
        return value
    if isinstance(value, int):
        if is_id or len(str(abs(value))) > MAX_SAFE_DIGITS:
            return str(value)
        return value
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            # Excel cells have no time zone, so times are written in UTC.
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value
    if isinstance(value, (date, time)):
        return value
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return ILLEGAL_CHARACTERS_RE.sub("", str(value))


def _display_width(value) -> int:
    if value is None:
        return 0
    if isinstance(value, datetime):
        return 19  # Width of "2026-10-01 00:00:00".
    return max((len(line) for line in str(value).splitlines()), default=0)


def convert_parquet_to_xlsx(
    parquet_path: PathLike,
    xlsx_path: PathLike,
    sheet_name: str = "Sheet1",
    formatting: bool = True,
) -> ConversionResult:
    """Write the Parquet file at parquet_path as an Excel workbook at xlsx_path.

    The file is read in batches of rows, twice: the first pass measures column widths,
    the second pass writes the cells. This keeps memory use low for large files.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        raise ConversionError("Reading Parquet files needs the pyarrow library. Install it with: pip install pyarrow")

    try:
        parquet = pq.ParquetFile(str(parquet_path))
    except (pa.ArrowException, OSError) as error:
        raise ConversionError(f"The file is not a readable Parquet file: {error}")

    schema = parquet.schema_arrow
    headings = list(schema.names)
    column_count = len(headings)
    row_count = parquet.metadata.num_rows + 1  # Data rows plus the header row.
    _check_size(row_count, column_count)

    map_columns = {i for i, field in enumerate(schema) if pa.types.is_map(field.type)}
    id_columns = {i for i, heading in enumerate(headings) if _ID_HEADER.search(heading.strip())}

    def rows():
        for batch in parquet.iter_batches(batch_size=PARQUET_BATCH_ROWS):
            columns = [batch.column(i).to_pylist() for i in range(batch.num_columns)]
            for values in zip(*columns):
                yield [
                    parquet_cell_value(value, is_map=i in map_columns, is_id=i in id_columns)
                    for i, value in enumerate(values)
                ]

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(title=safe_sheet_name(sheet_name))

    if formatting:
        widths = [len(heading) for heading in headings]
        for row in rows():
            for i, value in enumerate(row):
                widths[i] = max(widths[i], _display_width(value))
        _set_layout(sheet, widths, row_count, column_count)

    sheet.append([_make_cell(sheet, heading, bold=formatting) for heading in headings])
    for row in rows():
        sheet.append([_make_cell(sheet, value, bold=False) for value in row])

    workbook.save(xlsx_path)
    return ConversionResult(rows=row_count, columns=column_count, file_format="Parquet")


def convert_to_xlsx(
    source_path: PathLike,
    xlsx_path: PathLike,
    sheet_name: str = "Sheet1",
    formatting: bool = True,
) -> ConversionResult:
    """Convert a CSV or Parquet file, choosing the reader from the file name."""
    name = str(source_path).lower()
    if name.endswith(PARQUET_SUFFIX):
        return convert_parquet_to_xlsx(source_path, xlsx_path, sheet_name=sheet_name, formatting=formatting)
    if name.endswith(CSV_SUFFIX):
        return convert_csv_to_xlsx(source_path, xlsx_path, sheet_name=sheet_name, formatting=formatting)
    raise ConversionError(f"Only CSV and Parquet files can be converted, not {Path(source_path).name}.")
