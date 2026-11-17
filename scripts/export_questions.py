"""Export the requirements questionnaire as a CSV file for Microsoft Lists.

The questionnaire in docs/getbill-pipeline-questions.md is the master copy of the questions. It holds no
answers: the answers are kept in a private workbook or list outside the repository. This script
reads the questionnaire's tables and writes one row for each question, with empty Answer and Notes
columns, a Status of "Not started", a Classification column that says "Internal use only", and
the questionnaire's last-modified date and author, so a private SharePoint list can be created
from it with New list › From CSV. Regenerate the file after the questionnaire changes, because the
tests check that the two match.

    python3 scripts/export_questions.py

The file is written as UTF-8 with a byte order mark, so Excel and Microsoft Lists show characters
such as curly apostrophes correctly. The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "getbill-pipeline-questions.md"
TARGET = ROOT / "docs" / "getbill-pipeline-questions-for-microsoft-lists.csv"
COLUMNS = ["Title", "Question ID", "Section", "Why it matters", "Examples of possible answers",
           "Answer", "Status", "Notes", "Classification", "Questions last modified",
           "Questions modified by"]
# A CSV file cannot carry a note above its header row, because Microsoft Lists reads the first
# row as the column names. So every row carries the internal-use notice, and the date and author
# of the questionnaire it was made from, in columns of its own. The names avoid "Modified" and
# "Modified By", which every SharePoint list already has for the last change to each row.
CLASSIFICATION = "Internal use only"
STAMP = re.compile(r"^_Last modified: ([^_\n]+)_$", re.MULTILINE)
AUTHOR = re.compile(r"Modified by: ([^.\s]+)\.")
SECTION = re.compile(r"^## (\d+)\. (.+)$")
GROUP = re.compile(r"^### (.+)$")
# A question row has four cells: ID, question, why it matters, and examples of possible answers.
QUESTION_LINE = re.compile(r"^\| [A-Z]\d+ \|")
ROW = re.compile(r"^\| ([A-Z]\d+) \| (.+?) \| (.+?) \| (.+?) \|$")


class QuestionnaireError(ValueError):
    """A question row in the questionnaire does not have the expected four cells."""


def plain(text: str) -> str:
    """Remove Markdown bold and code marks, which a SharePoint list would show as symbols."""
    return text.replace("**", "").replace("`", "").strip()


def parse_questions(markdown: str):
    """Yield each question with its section number, section title and subgroup kept apart."""
    number = section = group = ""
    for line in markdown.splitlines():
        if match := SECTION.match(line):
            number, section, group = match.group(1), match.group(2), ""
        elif match := GROUP.match(line):
            group = match.group(1)
        elif QUESTION_LINE.match(line):
            match = ROW.match(line)
            # A fifth cell would show up inside the examples. It means someone added an Answer
            # column back, and answers must not be kept in the repository.
            if not match or "|" in match.group(4):
                raise QuestionnaireError(
                    f"This question row must have exactly four cells (ID, question, why it matters, "
                    f"examples), and answers belong in the private workbook: {line[:80]}")
            question_id, question, why, examples = (plain(part) for part in match.groups())
            yield {"id": question_id, "question": question, "why": why, "examples": examples,
                   "answer": "", "number": number, "section": section, "group": group}


def read_questions(markdown: str):
    """Yield one CSV row for each question, in the columns a Microsoft List is created from."""
    stamp, author = STAMP.search(markdown), AUTHOR.search(markdown)
    modified = stamp.group(1).strip() if stamp else ""
    modified_by = author.group(1) if author else ""
    for item in parse_questions(markdown):
        section = f"{item['number']}. {item['section']}"
        yield {
            "Title": item["question"],
            "Question ID": item["id"],
            "Section": f"{section}: {item['group']}" if item["group"] else section,
            "Why it matters": item["why"],
            "Examples of possible answers": item["examples"],
            "Answer": "",
            "Status": "Not started",
            "Notes": "",
            "Classification": CLASSIFICATION,
            "Questions last modified": modified,
            "Questions modified by": modified_by,
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export the questionnaire as a CSV file for Microsoft Lists.")
    parser.add_argument("--output", default=str(TARGET), help="Where to write the CSV file.")
    args = parser.parse_args(argv)

    try:
        questions = list(read_questions(SOURCE.read_text(encoding="utf-8")))
    except QuestionnaireError as error:
        raise SystemExit(str(error))
    if not questions:
        raise SystemExit(f"No questions were found in {SOURCE}.")
    output = Path(args.output)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(questions)
    sections = len({row["Section"].split(":")[0] for row in questions})
    print(f"Wrote {len(questions)} questions from {sections} sections to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
