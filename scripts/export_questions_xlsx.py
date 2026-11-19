"""Export the requirements questionnaire as a formatted Excel workbook.

The questionnaire in docs/getbill-pipeline-questions.md is the master copy of the questions. This script
reads its tables and writes an empty workbook, docs/getbill-pipeline-questions.xlsx, with these worksheets:

- About: what the workbook is, how to fill it in, and what each status means.
- Summary: how many questions each section has, and how many have each status. The counts are
  formulas, so they update while people answer.
- One worksheet for each section of the questionnaire, with one row for each question.

    python3 scripts/export_questions_xlsx.py

The repository keeps this blank workbook as a template. People download it and upload it to a
private SharePoint or OneDrive folder, where they answer it. That private copy is the source of
truth for the answers. The secret check that runs before every commit refuses the template as soon
as it holds any answer, using scripts/check_blank_workbook.py.

The script refuses to replace a workbook that already exists, so a filled-in copy cannot be
overwritten by accident. Pass --force to replace it anyway.

The script needs openpyxl, which getBill already installs.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bump_version import display, read_version  # noqa: E402
from export_questions import SOURCE, QuestionnaireError, parse_questions  # noqa: E402

TARGET = SOURCE.with_suffix(".xlsx")
MODIFIED_BY = "mbitar"

# Short worksheet names, by section number. Excel allows at most 31 characters.
SHEET_NAMES = {
    "0": "0 Goals", "1": "1 People", "2": "2 Accounts and access",
    "3": "3 Cost data", "4": "4 Allocation", "5": "5 Pricing and invoicing",
    "6": "6 Reporting", "7": "7 Delivery", "8": "8 Anomalies",
    "9": "9 Budgets and forecasts", "10": "10 Unit economics", "11": "11 Commitments and rates",
    "12": "12 Workload optimization", "13": "13 Licenses and SaaS", "14": "14 Sustainability",
    "15": "15 Governance", "16": "16 Onboarding", "17": "17 Security",
    "18": "18 Quality and month close", "19": "19 Retention", "20": "20 Integrations",
    "21": "21 Operations", "22": "22 Today's process",
}

# The status choices, with the fill color each one gets in the Status column.
STATUSES = {
    "Not started": "EDEDED",
    "Answered": "DDEBF7",
    "Needs discussion": "FCE4D6",
    "Agreed": "E2EFDA",
}
STATUS_MEANINGS = {
    "Not started": "Nobody has answered the question yet.",
    "Answered": "An expert has written an answer, but the group has not agreed to it yet.",
    "Needs discussion": "The answer is unclear or disputed, and the group needs to talk about it.",
    "Agreed": "The group has accepted the answer, and it can be used in the requirements.",
}

# Question worksheet columns: header, width, and the question field that fills it.
COLUMNS = [
    ("ID", 7, "id"),
    ("Question", 48, "question"),
    ("Why it matters", 38, "why"),
    ("Examples of possible answers", 38, "examples"),
    ("Answer", 45, "answer"),
    ("Expert", 20, None),
    ("Status", 17, None),
    ("Notes", 30, None),
]
GROUP_COLUMN = ("Group", 22, "group")
TO_FILL_IN = {"Answer", "Expert", "Notes"}
LAST_ROW = 1000  # The last row that the drop-down, the colors and the Summary counts cover.

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
INPUT_FILL = PatternFill("solid", fgColor="FFF9E5")
TITLE_FONT = Font(bold=True, size=16, color="1F4E78")
BOLD = Font(bold=True)
MUTED = Font(italic=True, color="595959")
WRAP_TOP = Alignment(wrap_text=True, vertical="top")
THIN = Side(style="thin", color="BFBFBF")
GRID = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def footer_text(stamp: str) -> str:
    """The footer of every worksheet, with the getBill version in the form people see."""
    return (f"Internal use only. Version: {display(read_version())}. Last modified: {stamp}. "
            f"Modified by: {MODIFIED_BY}.")


def set_print_layout(sheet, stamp: str, title_rows: str | None = None) -> None:
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    if title_rows:
        sheet.print_title_rows = title_rows
    sheet.oddFooter.left.text = footer_text(stamp)
    sheet.oddFooter.left.size = 8
    sheet.oddFooter.right.text = "Page &P of &N"
    sheet.oddFooter.right.size = 8


def write_header(sheet, headers) -> None:
    for column, (header, width, _) in enumerate(headers, start=1):
        cell = sheet.cell(row=1, column=column, value=header)
        cell.font, cell.fill, cell.border = HEADER_FONT, HEADER_FILL, GRID
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        sheet.column_dimensions[get_column_letter(column)].width = width
    sheet.row_dimensions[1].height = 22


def add_question_sheet(workbook, name: str, questions, stamp: str):
    sheet = workbook.create_sheet(name)
    headers = list(COLUMNS)
    if any(item["group"] for item in questions):
        headers.insert(1, GROUP_COLUMN)
    write_header(sheet, headers)

    for row, item in enumerate(questions, start=2):
        for column, (header, _, field) in enumerate(headers, start=1):
            value = item[field] if field else ("Not started" if header == "Status" else None)
            cell = sheet.cell(row=row, column=column, value=value or None)
            cell.alignment, cell.border = WRAP_TOP, GRID
            if header in TO_FILL_IN:
                cell.fill = INPUT_FILL
        sheet.cell(row=row, column=1).font = BOLD

    last_row = len(questions) + 1
    status = get_column_letter(next(i for i, h in enumerate(headers, 1) if h[0] == "Status"))
    # The drop-down and the colors also cover empty rows, so questions added later get them too.
    status_range = f"{status}2:{status}{LAST_ROW}"
    choices = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True,
                             showErrorMessage=True, errorTitle="Status",
                             error="Pick one of the statuses in the list.")
    choices.add(status_range)
    sheet.add_data_validation(choices)
    for label, color in STATUSES.items():
        sheet.conditional_formatting.add(
            status_range,
            FormulaRule(formula=[f'{status}2="{label}"'], fill=PatternFill("solid", bgColor=color)))

    sheet.freeze_panes = "C2" if headers[1] == GROUP_COLUMN else "B2"
    sheet.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{last_row}"
    set_print_layout(sheet, stamp, title_rows="1:1")
    return sheet, status


def add_about_sheet(workbook, stamp: str, total: int) -> None:
    sheet = workbook.active
    sheet.title = "About"
    sheet.column_dimensions["A"].width = 22
    sheet.column_dimensions["B"].width = 95
    sheet["A1"] = "getBill requirements questionnaire"
    sheet["A1"].font = TITLE_FONT
    sheet["A2"] = f"Last modified: {stamp}"
    sheet["A2"].font = MUTED

    lines = [
        ("What this is", f"This workbook holds the {total} questions that the product owner and the "
                         "experts answer to set the requirements for getBill. Each section of the "
                         "questionnaire has its own worksheet."),
        ("How to answer", "Write the answer in the Answer column, type your name in the Expert "
                          "column, and set the Status. The shaded columns are the ones to fill in."),
        ("Adding a question", "Add a row at the bottom of the right worksheet. Give it the next free "
                              "ID in that section, for example S17 after S16."),
        ("Who changed what", "Store the workbook in SharePoint or OneDrive and edit it there. Excel "
                             "then records who changed each cell and when, under Review › Show "
                             "Changes. Excel keeps that history for about 60 days."),
        ("Summary", "The Summary worksheet counts the questions in each section by status. Its "
                    "numbers update by themselves."),
    ]
    row = 4
    for label, text in lines:
        sheet.cell(row=row, column=1, value=label).font = BOLD
        sheet.cell(row=row, column=2, value=text)
        row += 1

    row += 1
    sheet.cell(row=row, column=1, value="Status").font = HEADER_FONT
    sheet.cell(row=row, column=2, value="What it means").font = HEADER_FONT
    for column in (1, 2):
        sheet.cell(row=row, column=column).fill = HEADER_FILL
    for label, color in STATUSES.items():
        row += 1
        sheet.cell(row=row, column=1, value=label).fill = PatternFill("solid", fgColor=color)
        sheet.cell(row=row, column=2, value=STATUS_MEANINGS[label])

    row += 2
    sheet.cell(row=row, column=1, value=footer_text(stamp)).font = MUTED
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
    for cells in sheet.iter_rows(min_row=4, max_row=row, max_col=2):
        for cell in cells:
            cell.alignment = WRAP_TOP
    set_print_layout(sheet, stamp)


def add_summary_sheet(workbook, sections, stamp: str) -> None:
    sheet = workbook.create_sheet("Summary", 1)
    headers = [("Section", 40, None), ("Worksheet", 16, None), ("Questions", 12, None)]
    headers += [(label, 14, None) for label in STATUSES]
    write_header(sheet, headers)

    for row, (title, name, status) in enumerate(sections, start=2):
        reference = f"'{name}'!"
        values = [title, name, f"=COUNTA({reference}A2:A{LAST_ROW})"]
        values += [f'=COUNTIF({reference}{status}2:{status}{LAST_ROW},"{label}")' for label in STATUSES]
        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=row, column=column, value=value)
            cell.border = GRID
        sheet.cell(row=row, column=2).hyperlink = f"#{reference}A1"
        sheet.cell(row=row, column=2).font = Font(color="0563C1", underline="single")

    total = len(sections) + 2
    sheet.cell(row=total, column=1, value="All sections").font = BOLD
    for column in range(3, len(headers) + 1):
        letter = get_column_letter(column)
        cell = sheet.cell(row=total, column=column, value=f"=SUM({letter}2:{letter}{total - 1})")
        cell.font, cell.border = BOLD, GRID
    sheet.cell(row=total, column=1).border = sheet.cell(row=total, column=2).border = GRID
    sheet.freeze_panes = "A2"
    set_print_layout(sheet, stamp, title_rows="1:1")


def build(markdown: str, stamp: str) -> Workbook:
    questions = list(parse_questions(markdown))
    if not questions:
        raise SystemExit(f"No questions were found in {SOURCE}.")
    by_section: dict[str, list] = {}
    titles = {}
    for item in questions:
        by_section.setdefault(item["number"], []).append(item)
        titles[item["number"]] = f"{item['number']}. {item['section']}"

    workbook = Workbook()
    add_about_sheet(workbook, stamp, len(questions))
    sections = []
    for number, items in by_section.items():
        name = SHEET_NAMES.get(number, f"{number} Section")[:31]
        _, status = add_question_sheet(workbook, name, items, stamp)
        sections.append((titles[number], name, status))
    add_summary_sheet(workbook, sections, stamp)

    workbook.properties.title = "getBill requirements questionnaire"
    workbook.properties.creator = MODIFIED_BY
    workbook.properties.lastModifiedBy = MODIFIED_BY
    return workbook


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export the questionnaire as an Excel workbook.")
    parser.add_argument("--output", default=str(TARGET), help="Where to write the workbook.")
    parser.add_argument("--force", action="store_true",
                        help="Replace the workbook if it already exists. Any answers in it are lost.")
    args = parser.parse_args(argv)

    if Path(args.output).exists() and not args.force:
        raise SystemExit(
            f"{args.output} already exists and may hold answers, so it was not replaced. "
            "Move it away first, or pass --force to replace it.")
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    try:
        workbook = build(SOURCE.read_text(encoding="utf-8"), stamp)
    except QuestionnaireError as error:
        raise SystemExit(str(error))
    workbook.save(args.output)
    questions = sum(sheet.max_row - 1 for sheet in workbook.worksheets[2:])
    print(f"Wrote {questions} questions on {len(workbook.worksheets) - 2} section worksheets "
          f"to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
