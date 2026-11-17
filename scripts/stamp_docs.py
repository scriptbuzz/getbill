"""Write the current date and time into the header stamp and footer of each document.

Every document carries two stamps:
  - A "Last modified" line directly under the title.
  - A footer that says the document is for internal use only, gives the same date and time,
    and names who modified it.

Supported documents are Markdown files, SVG diagrams, HTML pages, and the plain-text LICENSE file.
In an SVG diagram or an HTML page, the script updates the elements with id="last-modified" and
id="document-footer". In a plain-text file, it writes the stamp under the first line and the footer
after a line of three dashes at the end.

The Microsoft Lists CSV file cannot hold a title or a footer, so scripts/export_questions.py copies
the questionnaire's stamp into two columns of every row instead. Whenever this script stamps the
questionnaire, it also regenerates that CSV file, so the two always carry the same date.
Run the script after you change a document, so the stamps cannot fall out of date:

    python3 scripts/stamp_docs.py                  # stamps every document in the project
    python3 scripts/stamp_docs.py README.md        # stamps only the files you name
    python3 scripts/stamp_docs.py --changed        # stamps documents that git reports as changed

The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
MODIFIED_BY = "mbitar"
DOCUMENT_GLOBS = ["*.md", "docs/**/*.md", "docs/**/*.svg", "docs/**/*.html", "LICENSE"]
PLAIN_TEXT_NAMES = {"LICENSE"}
QUESTIONNAIRE = ROOT / "docs" / "getbill-pipeline-questions.md"
FOOTER_START = "<!-- document-footer -->"
FOOTER_END = "<!-- /document-footer -->"


def now_text() -> str:
    """Local date and time with the time zone, for example 2026-11-16 08:15 EST."""
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def footer_sentence(stamp: str) -> str:
    return f"Internal use only. Last modified: {stamp}. Modified by: {MODIFIED_BY}."


def stamp_markdown(text: str, stamp: str) -> str:
    """Update the stamp under the title and replace or add the footer block at the end."""
    header = f"_Last modified: {stamp}_"
    if re.search(r"^_Last modified: [^\n]*_$", text, flags=re.MULTILINE):
        text = re.sub(r"^_Last modified: [^\n]*_$", header, text, count=1, flags=re.MULTILINE)
    else:
        # Put the stamp directly under the first heading.
        text = re.sub(r"^(# [^\n]*\n)", rf"\1\n{header}\n", text, count=1, flags=re.MULTILINE)

    footer = f"{FOOTER_START}\n---\n\n_{footer_sentence(stamp)}_\n{FOOTER_END}\n"
    block = re.compile(re.escape(FOOTER_START) + r".*?" + re.escape(FOOTER_END) + r"\n?", flags=re.DOTALL)
    if block.search(text):
        return block.sub(lambda _: footer, text)
    return text.rstrip("\n") + "\n\n" + footer


def stamp_tagged(text: str, stamp: str) -> str:
    """Update the elements with id="last-modified" and id="document-footer" in SVG or HTML.

    Each element must hold plain text only, such as <text id="last-modified">…</text> in a
    diagram or <footer id="document-footer">…</footer> in a page.
    """
    for element_id, content in (
        ("last-modified", f"Last modified: {stamp}"),
        ("document-footer", footer_sentence(stamp)),
    ):
        pattern = re.compile(rf'(<(\w+)\b[^>]*\bid="{element_id}"[^>]*>)[^<]*(</\2>)')
        if not pattern.search(text):
            raise ValueError(f'The document has no element with id="{element_id}" to update.')
        text = pattern.sub(lambda m: m.group(1) + content + m.group(3), text, count=1)
    return text


def stamp_plain(text: str, stamp: str) -> str:
    """Update or add the stamp under the first line, and the footer at the end, of a text file."""
    header = f"Last modified: {stamp}"
    if re.search(r"^Last modified: [^\n]*$", text, flags=re.MULTILINE):
        text = re.sub(r"^Last modified: [^\n]*$", header, text, count=1, flags=re.MULTILINE)
    else:
        text = re.sub(r"^([^\n]*\n)", rf"\1\n{header}\n", text, count=1)

    footer = f"---\n{footer_sentence(stamp)}\n"
    existing = re.compile(r"\n---\nInternal use only\. Last modified: [^\n]*\n?\Z")
    if existing.search(text):
        return existing.sub(lambda _: "\n" + footer, text)
    return text.rstrip("\n") + "\n\n" + footer


def all_documents() -> List[Path]:
    found = set()
    for pattern in DOCUMENT_GLOBS:
        found.update(path for path in ROOT.glob(pattern) if ".venv" not in path.parts)
    return sorted(found)


def changed_documents() -> List[Path]:
    output = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    changed = {ROOT / line[3:].strip() for line in output.splitlines() if line[3:].strip()}
    return [path for path in all_documents() if path in changed]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Stamp the date, time, and footer into documents.")
    parser.add_argument("files", nargs="*", help="Documents to stamp. Without names, every document is stamped.")
    parser.add_argument("--changed", action="store_true", help="Stamp only documents that git reports as changed.")
    args = parser.parse_args(argv)

    if args.files:
        paths = [Path(name).resolve() for name in args.files]
    elif args.changed:
        paths = changed_documents()
    else:
        paths = all_documents()

    stamp = now_text()
    for path in paths:
        original = path.read_text(encoding="utf-8")
        if path.suffix == ".md":
            updated = stamp_markdown(original, stamp)
        elif path.suffix in (".svg", ".html"):
            updated = stamp_tagged(original, stamp)
        elif path.name in PLAIN_TEXT_NAMES:
            updated = stamp_plain(original, stamp)
        else:
            print(f"Skipped {path.relative_to(ROOT)}, because only .md, .svg, .html and LICENSE files are supported.")
            continue
        path.write_text(updated, encoding="utf-8")
        print(f"Stamped {path.relative_to(ROOT)} with {stamp}.")
        if path == QUESTIONNAIRE:
            sys.path.insert(0, str(ROOT / "scripts"))
            import export_questions  # The Lists file copies the questionnaire's stamp.
            export_questions.main([])
    if not paths:
        print("No documents needed a stamp.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
