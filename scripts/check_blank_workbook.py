"""Check that a requirements workbook is blank, so it is safe to keep in the repository.

The repository keeps one blank copy of the requirements workbook, as a template that people
download and upload to a private SharePoint or OneDrive folder. Answers are kept only in that
private copy. A workbook is blank when, on every section worksheet:

- every cell in the Answer, Expert and Notes columns is empty, and
- every cell in the Status column says "Not started".

    python3 scripts/check_blank_workbook.py docs/getbill-pipeline-questions.xlsx

The script exits with code 0 when the workbook is blank and 1 when it is not, and it names each
cell that holds an answer. It does not print what the cell says, so answers are never shown. It
uses only the Python standard library, so the pre-commit hook can run it on any computer.
"""

from __future__ import annotations

import re
import sys
import zipfile
from typing import Dict, List
from xml.etree import ElementTree

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
ANSWER_COLUMNS = ("Answer", "Expert", "Notes")
STATUS_COLUMN = "Status"
BLANK_STATUS = "Not started"
# The About and Summary worksheets hold instructions and formulas, not answers.
SKIPPED_SHEETS = {"About", "Summary"}


def _text(cell, shared: List[str]) -> str:
    """Return the text a cell shows, from a shared string, an inline string or a plain value."""
    kind = cell.get("t")
    if kind == "s":
        value = cell.find("m:v", NS)
        return shared[int(value.text)] if value is not None and value.text else ""
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{NS['m']}}}t"))
    value = cell.find("m:v", NS)
    formula = cell.find("m:f", NS)
    return (value.text if value is not None and value.text else "") or (
        "=" + formula.text if formula is not None and formula.text else "")


def find_answers(path: str) -> List[str]:
    """Return one description for each cell that holds an answer, such as "6 Security!E4"."""
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        shared: List[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.iter(f"{{{NS['m']}}}t"))
                      for item in root.findall("m:si", NS)]
        rels = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.get("Id"): rel.get("Target") for rel in rels.findall("p:Relationship", NS)}
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))

        problems: List[str] = []
        for sheet in workbook.find("m:sheets", NS).findall("m:sheet", NS):
            title = sheet.get("name")
            if title in SKIPPED_SHEETS:
                continue
            target = targets[sheet.get(f"{{{NS['r']}}}id")].lstrip("/")
            target = target if target.startswith("xl/") else f"xl/{target}"
            rows = ElementTree.fromstring(archive.read(target)).find("m:sheetData", NS)
            columns: Dict[str, str] = {}
            for row in rows.findall("m:row", NS):
                number = int(row.get("r"))
                for cell in row.findall("m:c", NS):
                    letter = re.match(r"[A-Z]+", cell.get("r")).group(0)
                    text = _text(cell, shared).strip()
                    if number == 1:
                        columns[letter] = text
                        continue
                    heading = columns.get(letter)
                    if heading in ANSWER_COLUMNS and text:
                        problems.append(f"{title}!{cell.get('r')} ({heading})")
                    elif heading == STATUS_COLUMN and text not in ("", BLANK_STATUS):
                        problems.append(f"{title}!{cell.get('r')} ({heading})")
            missing = [name for name in ANSWER_COLUMNS + (STATUS_COLUMN,) if name not in columns.values()]
            if missing:
                problems.append(f"{title} has no {', '.join(missing)} column, so it cannot be checked")
        return problems


def main(argv=None) -> int:
    paths = sys.argv[1:] if argv is None else argv
    if len(paths) != 1:
        print("Give the path of one workbook to check.", file=sys.stderr)
        return 2
    try:
        problems = find_answers(paths[0])
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError, AttributeError) as error:
        print(f"{paths[0]} could not be read as an Excel workbook: {error}", file=sys.stderr)
        return 1
    if problems:
        print(f"{paths[0]} is not blank. These cells hold answers or a status other than "
              f"\"{BLANK_STATUS}\":", file=sys.stderr)
        for problem in problems[:20]:
            print(f"  {problem}", file=sys.stderr)
        if len(problems) > 20:
            print(f"  ... and {len(problems) - 20} more.", file=sys.stderr)
        return 1
    print(f"{paths[0]} is blank.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
