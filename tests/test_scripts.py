"""The helper scripts: version bumps, document stamps, the CUR 2.0 sample file, and the
questionnaire exports, which must never carry answers into the repository."""

import csv
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


# ---------------------------------------------------------------- scripts/bump_version.py

@pytest.fixture
def bump(load_script):
    return load_script("bump_version")


@pytest.mark.parametrize("version, part, expected", [
    ("0.1.0a2", "pre", "0.1.0a3"),
    ("0.1.0a9", "pre", "0.1.0a10"),
    ("0.1.0a3", "patch", "0.1.1a1"),
    ("0.1.1a1", "minor", "0.2.0a1"),
    ("0.2.0a1", "major", "1.0.0a1"),
    ("1.0.0a1", "release", "1.0.0"),
    ("1.0.0", "patch", "1.0.1a1"),
])
def test_next_version(bump, version, part, expected):
    assert bump.next_version(version, part) == expected


@pytest.mark.parametrize("version, part", [("1.0.0", "pre"), ("1.0.0", "release"), ("one", "pre")])
def test_next_version_refuses_impossible_steps(bump, version, part):
    with pytest.raises(SystemExit):
        bump.next_version(version, part)


@pytest.mark.parametrize("version, shown, badge", [
    ("0.1.0a2", "0.1.0-alpha.2", "0.1.0--alpha.2"),
    ("1.2.3b4", "1.2.3-beta.4", "1.2.3--beta.4"),
    ("2.0.0rc1", "2.0.0-rc.1", "2.0.0--rc.1"),
    ("1.0.0", "1.0.0", "1.0.0"),
])
def test_how_versions_are_shown(bump, version, shown, badge):
    assert bump.display(version) == shown
    assert bump.badge(version) == badge


@pytest.fixture
def version_files(bump, tmp_path, monkeypatch):
    """Point the bump script at small copies of the files that show the version."""
    files = {
        "init": tmp_path / "__init__.py",
        "readme": tmp_path / "README.md",
        "page": tmp_path / "index.html",
    }
    files["init"].write_text('__version__ = "0.1.0a2"\n')
    files["readme"].write_text("# getBill v0.1.0-alpha.2\n"
                               "![version](https://img.shields.io/badge/version-0.1.0--alpha.2-FF9900)\n"
                               "`getbill --version` prints `0.1.0a2`.\n")
    files["page"].write_text('<span class="ver">v0.1.0-alpha.2</span>\n')
    monkeypatch.setattr(bump, "ROOT", tmp_path)
    monkeypatch.setattr(bump, "VERSION_FILE", files["init"])
    monkeypatch.setattr(bump, "SHOWN_IN", list(files.values()))
    # Record the call that stamps the documents instead of stamping the real project.
    stamp_calls = []
    monkeypatch.setattr(bump, "stamp_unpushed_documents", lambda: stamp_calls.append("stamped"))
    files["stamp_calls"] = stamp_calls
    return files


def test_bump_updates_every_place_the_version_is_shown(bump, version_files):
    assert bump.main([]) == 0
    assert version_files["init"].read_text() == '__version__ = "0.1.0a3"\n'
    readme = version_files["readme"].read_text()
    assert "# getBill v0.1.0-alpha.3" in readme
    assert "version-0.1.0--alpha.3-FF9900" in readme
    assert "`0.1.0a3`" in readme
    assert "alpha.2" not in readme and "0.1.0a2" not in readme
    assert "v0.1.0-alpha.3" in version_files["page"].read_text()
    assert version_files["stamp_calls"] == ["stamped"]


def test_bump_changes_no_file_when_one_does_not_show_the_version(bump, version_files):
    version_files["page"].write_text("<span>no version here</span>\n")
    with pytest.raises(SystemExit):
        bump.main([])
    assert version_files["init"].read_text() == '__version__ = "0.1.0a2"\n'
    assert "alpha.2" in version_files["readme"].read_text()
    assert version_files["stamp_calls"] == []


# ---------------------------------------------------------------- scripts/stamp_docs.py

@pytest.fixture
def stamp(load_script):
    return load_script("stamp_docs")


def test_markdown_gets_one_header_stamp_and_one_footer(stamp):
    once = stamp.stamp_markdown("# Title\n\nBody text.\n", "2026-01-01 09:00 EST")
    assert once.startswith("# Title\n\n_Last modified: 2026-01-01 09:00 EST_\n")
    assert once.count(stamp.FOOTER_START) == 1
    assert "Modified by: mbitar." in once
    twice = stamp.stamp_markdown(once, "2026-01-02 10:00 EST")
    assert twice.count(stamp.FOOTER_START) == 1
    assert twice.count("_Last modified:") == 1
    assert "2026-01-01" not in twice


def test_html_and_svg_stamps_are_replaced_in_place(stamp):
    page = '<p id="last-modified">old</p>\n<footer id="document-footer">old</footer>\n'
    stamped = stamp.stamp_tagged(page, "2026-01-01 09:00 EST")
    assert '<p id="last-modified">Last modified: 2026-01-01 09:00 EST</p>' in stamped
    assert '<footer id="document-footer">Internal use only. Last modified: 2026-01-01 09:00 EST. Modified by: mbitar.</footer>' in stamped


def test_markdown_gets_one_version_line_under_the_stamp(stamp):
    once = stamp.stamp_markdown("# Title\n\nBody text.\n", "2026-01-01 09:00 EST", "0.1.0-alpha.2")
    assert once.startswith("# Title\n\n_Last modified: 2026-01-01 09:00 EST_\n\n_Version: 0.1.0-alpha.2_\n")
    assert "Internal use only. Version: 0.1.0-alpha.2. Last modified: 2026-01-01 09:00 EST." in once
    twice = stamp.stamp_markdown(once, "2026-01-02 10:00 EST", "0.1.0-alpha.3")
    assert twice.count("_Version:") == 1
    assert twice.count(stamp.FOOTER_START) == 1
    assert "0.1.0-alpha.2" not in twice


def test_html_and_svg_stamps_show_the_version(stamp):
    page = '<p id="last-modified">old</p>\n<footer id="document-footer">old</footer>\n'
    stamped = stamp.stamp_tagged(page, "2026-01-01 09:00 EST", "0.1.0-alpha.2")
    assert '<p id="last-modified">Last modified: 2026-01-01 09:00 EST. Version: 0.1.0-alpha.2.</p>' in stamped
    assert ("Internal use only. Version: 0.1.0-alpha.2. Last modified: 2026-01-01 09:00 EST. "
            "Modified by: mbitar.</footer>") in stamped


def test_plain_text_version_is_replaced_not_repeated(load_script):
    stamp_plain = load_script("stamp_docs").stamp_plain
    once = stamp_plain("TITLE\n\nBody text.\n", "2026-01-01 09:00 EST", "0.1.0-alpha.2")
    assert once.startswith("TITLE\n\nLast modified: 2026-01-01 09:00 EST\nVersion: 0.1.0-alpha.2\n\nBody text.\n")
    twice = stamp_plain(once, "2026-01-02 10:00 EST", "0.1.0-alpha.3")
    assert twice == once.replace("2026-01-01 09:00", "2026-01-02 10:00").replace("alpha.2", "alpha.3")


def test_a_page_without_stamp_elements_is_reported(stamp):
    with pytest.raises(ValueError, match="last-modified"):
        stamp.stamp_tagged("<p>No stamps here</p>", "2026-01-01 09:00 EST")


# ---------------------------------------------------------------- scripts/generate_cur2_sample.py

def test_sample_file_is_repeatable_and_shaped_like_cur2(load_script, tmp_path):
    generator = load_script("generate_cur2_sample")
    first, again, other_seed = (tmp_path / name for name in ("first.csv", "again.csv", "other.csv"))
    generator.main(["--rows", "50", "--output", str(first)])
    generator.main(["--rows", "50", "--output", str(again)])
    generator.main(["--rows", "50", "--seed", "8", "--output", str(other_seed)])
    assert first.read_bytes() == again.read_bytes()
    assert first.read_bytes() != other_seed.read_bytes()

    with first.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows[0]) == 58
    assert sum(row["line_item_line_item_type"] == "Usage" for row in rows) == 50
    assert {row["line_item_line_item_type"] for row in rows} == {"Usage", "Tax", "Credit"}
    assert "line_item_blended_cost" not in rows[0]


# ------------------------------------- scripts/export_questions.py and export_questions_xlsx.py

QUESTIONNAIRE = """# Questionnaire

## 0. Goals and users

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| G1 | What is the **main** goal? | It sets `scope`. | Fewer manual steps. |

## 1. Source: where the files come from

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| S1 | Who owns the data? | Someone must fix late files. | The finance team. |

## 10. Scenarios and use cases

### Everyday use

| # | Question | Why it matters | Examples of possible answers |
| --- | --- | --- | --- |
| U1 | What happens each month? | It sets the schedule. | A file each month. |
"""


def test_csv_export_keeps_the_section_title_and_subgroup(load_script):
    rows = list(load_script("export_questions").read_questions(QUESTIONNAIRE))
    assert [row["Question ID"] for row in rows] == ["G1", "S1", "U1"]
    assert rows[0]["Title"] == "What is the main goal?"
    assert rows[0]["Why it matters"] == "It sets scope."
    assert rows[1]["Section"] == "1. Source: where the files come from"
    assert all(row["Answer"] == "" for row in rows)
    assert rows[2]["Section"] == "10. Scenarios and use cases: Everyday use"


def test_workbook_has_one_worksheet_per_section(load_script):
    workbook = load_script("export_questions_xlsx").build(QUESTIONNAIRE, "2026-01-01 09:00 EST")
    assert workbook.sheetnames == ["About", "Summary", "0 Goals", "1 People", "10 Unit economics"]
    assert workbook["About"]["A2"].value == "Last modified: 2026-01-01 09:00 EST"

    goals = workbook["0 Goals"]
    assert [cell.value for cell in goals[1]] == [
        "ID", "Question", "Why it matters", "Examples of possible answers", "Answer", "Expert",
        "Status", "Notes"]
    assert [cell.value for cell in goals[2]][:2] == ["G1", "What is the main goal?"]
    assert goals["G2"].value == "Not started"
    assert str(goals.data_validations.dataValidation[0].sqref) == "G2:G1000"

    scenarios = workbook["10 Unit economics"]
    assert [cell.value for cell in scenarios[1]][:3] == ["ID", "Group", "Question"]
    assert scenarios["B2"].value == "Everyday use"
    assert scenarios["H2"].value == "Not started"

    summary = workbook["Summary"]
    assert summary["C4"].value == "=COUNTA('10 Unit economics'!A2:A1000)"
    assert summary["D4"].value == "=COUNTIF('10 Unit economics'!H2:H1000,\"Not started\")"
    assert summary["A5"].value == "All sections"


# ------------------------------------- answers stay out of the repository

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def test_a_question_row_with_an_answer_column_is_refused(load_script):
    module = load_script("export_questions")
    five_cells = QUESTIONNAIRE.replace("| Fewer manual steps. |", "| Fewer manual steps. | Finance |")
    with pytest.raises(module.QuestionnaireError):
        list(module.read_questions(five_cells))


def test_the_questionnaire_holds_questions_only(load_script):
    markdown = (DOCS / "getbill-pipeline-questions.md").read_text(encoding="utf-8")
    question_lines = [line for line in markdown.splitlines() if re.match(r"^\| [A-Z]\d+ \|", line)]
    rows = list(load_script("export_questions").read_questions(markdown))
    assert len(rows) == len(question_lines) > 0
    assert len({row["Question ID"] for row in rows}) == len(rows)  # Question IDs are unique.


def test_the_committed_lists_file_matches_the_questionnaire_and_has_no_answers(load_script):
    markdown = (DOCS / "getbill-pipeline-questions.md").read_text(encoding="utf-8")
    expected = list(load_script("export_questions").read_questions(markdown))
    with (DOCS / "getbill-pipeline-questions-for-microsoft-lists.csv").open(encoding="utf-8-sig", newline="") as handle:
        committed = list(csv.DictReader(handle))
    assert committed == expected
    assert all(row["Answer"] == "" and row["Notes"] == "" for row in committed)
    assert all(row["Classification"] == "Internal use only" for row in committed)


# ------------------------------------- the internal-use notice on every document

NOTICE = "Internal use only"
TEXT_DOCUMENTS = sorted({*ROOT.glob("*.md"), *DOCS.glob("*.md"), *DOCS.glob("*.svg"),
                         *DOCS.glob("*.html"), ROOT / "LICENSE"})


STAMP_TEXT = re.compile(r"Last modified: \d{4}-\d{2}-\d{2} \d{2}:\d{2} [A-Z]{2,5}")
FOOTER_TEXT = re.compile(STAMP_TEXT.pattern + r"\. Modified by: mbitar\.")
VERSION_TEXT = re.compile(r"Version: \d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?")


@pytest.mark.parametrize("path", TEXT_DOCUMENTS, ids=lambda path: path.name)
def test_every_text_document_has_the_notice_the_stamp_and_the_author(path):
    text = path.read_text(encoding="utf-8")
    assert NOTICE in text
    assert len(STAMP_TEXT.findall(text)) >= 2  # One under the title and one in the footer.
    assert FOOTER_TEXT.search(text)
    assert len(VERSION_TEXT.findall(text)) >= 2  # One with the stamp and one in the footer.


def test_every_lists_row_carries_the_notice_and_the_questionnaire_stamp():
    markdown = (DOCS / "getbill-pipeline-questions.md").read_text(encoding="utf-8")
    stamp = re.search(r"^_Last modified: ([^_\n]+)_$", markdown, re.MULTILINE).group(1)
    with (DOCS / "getbill-pipeline-questions-for-microsoft-lists.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows and all(row["Classification"] == NOTICE for row in rows)
    assert all(row["Questions last modified"] == stamp and row["Questions modified by"] == "mbitar" for row in rows)


def test_every_worksheet_of_the_workbook_has_the_notice_the_stamp_and_the_author():
    pytest.importorskip("openpyxl")
    from openpyxl import load_workbook
    workbook = load_workbook(DOCS / "getbill-pipeline-questions.xlsx")
    assert all(FOOTER_TEXT.search(sheet.oddFooter.left.text or "") for sheet in workbook.worksheets)
    assert all(VERSION_TEXT.search(sheet.oddFooter.left.text or "") for sheet in workbook.worksheets)
    about = [str(cell.value) for row in workbook["About"].iter_rows() for cell in row if cell.value]
    assert any(STAMP_TEXT.fullmatch(value) for value in about)
    assert any(FOOTER_TEXT.search(value) and NOTICE in value for value in about)


def test_restamping_a_plain_text_file_does_not_repeat_the_stamps(load_script):
    stamp_plain = load_script("stamp_docs").stamp_plain
    once = stamp_plain("TITLE\n\nBody text.\n", "2026-01-01 09:00 EST")
    twice = stamp_plain(once, "2026-01-02 10:00 EST")
    assert once.startswith("TITLE\n\nLast modified: 2026-01-01 09:00 EST\n\nBody text.\n")
    assert once.endswith("\n---\nInternal use only. Last modified: 2026-01-01 09:00 EST. Modified by: mbitar.\n")
    assert twice == once.replace("2026-01-01 09:00", "2026-01-02 10:00")


def test_the_workbook_script_does_not_replace_an_existing_workbook(load_script, tmp_path):
    existing = tmp_path / "answered.xlsx"
    existing.write_bytes(b"answers that must survive")
    with pytest.raises(SystemExit, match="already exists"):
        load_script("export_questions_xlsx").main(["--output", str(existing)])
    assert existing.read_bytes() == b"answers that must survive"


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is not installed.")
@pytest.mark.parametrize("name, ignored", [
    ("docs/getbill-pipeline-questions.xlsx", False),  # The blank template is kept.
    ("docs/getbill-pipeline-questions-answered.xlsx", True),
    ("docs/other.xlsx", True),
    ("pipeline-questions.xlsx", True),
])
def test_git_keeps_only_the_blank_workbook_template(name, ignored):
    # In the CI container the checkout belongs to another user, and Git refuses such a folder
    # unless it is marked safe. The setting applies to this one Git command only.
    env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="safe.directory", GIT_CONFIG_VALUE_0="*")
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", name], cwd=ROOT, capture_output=True, text=True, env=env,
    )
    # Exit code 0 means ignored and 1 means not ignored. Any other code means Git itself failed.
    assert result.returncode in (0, 1), result.stderr
    assert (result.returncode == 0) is ignored


# ------------------------------------- scripts/check_blank_workbook.py

TEMPLATE = DOCS / "getbill-pipeline-questions.xlsx"


def answered_copy(tmp_path, sheet, heading, value):
    """Save a copy of the template with one cell filled in under the given column heading."""
    from openpyxl import load_workbook
    workbook = load_workbook(TEMPLATE)
    worksheet = workbook[sheet]
    column = [cell.value for cell in worksheet[1]].index(heading) + 1
    worksheet.cell(row=2, column=column, value=value)
    path = tmp_path / "answered.xlsx"
    workbook.save(path)
    return path


def test_the_committed_workbook_is_blank_and_holds_every_question(load_script):
    pytest.importorskip("openpyxl")
    from openpyxl import load_workbook
    assert load_script("check_blank_workbook").find_answers(str(TEMPLATE)) == []
    markdown = (DOCS / "getbill-pipeline-questions.md").read_text(encoding="utf-8")
    expected = [row["Question ID"] for row in load_script("export_questions").read_questions(markdown)]
    workbook = load_workbook(TEMPLATE)
    found = [row[0] for sheet in workbook.worksheets[2:]
             for row in sheet.iter_rows(min_row=2, values_only=True) if row[0]]
    assert found == expected  # Regenerate the template after changing the questionnaire.


@pytest.mark.parametrize("sheet, heading, value", [
    ("17 Security", "Answer", "FedRAMP Moderate"),
    ("0 Goals", "Expert", "A. Person"),
    ("1 People", "Notes", "Ask finance."),
    ("10 Unit economics", "Status", "Agreed"),
])
def test_a_workbook_with_any_answer_is_not_blank(load_script, tmp_path, sheet, heading, value):
    pytest.importorskip("openpyxl")
    path = answered_copy(tmp_path, sheet, heading, value)
    problems = load_script("check_blank_workbook").find_answers(str(path))
    assert len(problems) == 1 and problems[0].startswith(f"{sheet}!") and heading in problems[0]
    assert value not in problems[0]  # The answer itself is never shown.


def test_the_checker_refuses_a_file_that_is_not_a_workbook(load_script, tmp_path):
    path = tmp_path / "broken.xlsx"
    path.write_text("not a workbook")
    assert load_script("check_blank_workbook").main([str(path)]) == 1
