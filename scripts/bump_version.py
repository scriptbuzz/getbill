"""Raise getBill's version number and update every place it is shown.

The version is set in one place, src/getbill/__init__.py, in Python's format, such as 0.1.0a2.
People see it in a longer form, such as v0.1.0-alpha.2, in the README title and badge, on both
demo web pages, and in the README banner. This script changes all of them together.

After it raises the version, the script stamps every document that differs from GitHub with the
date, the time and the new version (scripts/stamp_docs.py --unpushed).

Raise the version before every push to GitHub. The pre-push check in .githooks refuses a push
whose version matches the version already on GitHub.

    python3 scripts/bump_version.py            # next alpha: 0.1.0a2 becomes 0.1.0a3
    python3 scripts/bump_version.py patch      # next fix release: 0.1.0a3 becomes 0.1.1a1
    python3 scripts/bump_version.py minor      # next feature release: 0.1.1a1 becomes 0.2.0a1
    python3 scripts/bump_version.py major      # next major release: 0.2.0a1 becomes 1.0.0a1
    python3 scripts/bump_version.py release    # end the alpha: 1.0.0a1 becomes 1.0.0
    python3 scripts/bump_version.py --check    # show the current version and change nothing

The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "src" / "getbill" / "__init__.py"
# Files that show the version. Each must contain the current version in at least one form.
SHOWN_IN = [
    VERSION_FILE,
    ROOT / "README.md",
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "getbill-run-recording.html",
    ROOT / ".github" / "banner.svg",
]
VERSION_LINE = re.compile(r'^__version__ = "([^"]+)"$', re.MULTILINE)
PEP440 = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?$")
STAGE_NAMES = {"a": "alpha", "b": "beta", "rc": "rc"}


def read_version() -> str:
    match = VERSION_LINE.search(VERSION_FILE.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"No __version__ line was found in {VERSION_FILE.relative_to(ROOT)}.")
    return match.group(1)


def display(version: str) -> str:
    """Turn 0.1.0a2 into 0.1.0-alpha.2, the form people see. A final release stays as it is."""
    major, minor, patch, stage, number = PEP440.match(version).groups()
    base = f"{major}.{minor}.{patch}"
    return f"{base}-{STAGE_NAMES[stage]}.{number}" if stage else base


def badge(version: str) -> str:
    """The badge service reads "-" as a separator, so a dash inside the value is written "--"."""
    return display(version).replace("-", "--")


def next_version(version: str, part: str) -> str:
    match = PEP440.match(version)
    if not match:
        raise SystemExit(f"The version {version} is not in the form 1.2.3 or 1.2.3a4, so it cannot be raised.")
    major, minor, patch = (int(x) for x in match.group(1, 2, 3))
    stage, number = match.group(4), match.group(5)
    if part == "pre":
        if not stage:
            raise SystemExit(f"{version} is a final release. Use patch, minor or major to start the next one.")
        return f"{major}.{minor}.{patch}{stage}{int(number) + 1}"
    if part == "release":
        if not stage:
            raise SystemExit(f"{version} is already a final release.")
        return f"{major}.{minor}.{patch}"
    # A new patch, minor or major version starts again at alpha 1.
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}a1"
    if part == "minor":
        return f"{major}.{minor + 1}.0a1"
    return f"{major + 1}.0.0a1"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Raise getBill's version and update every place it is shown.")
    parser.add_argument("part", nargs="?", default="pre", choices=["pre", "patch", "minor", "major", "release"],
                        help="Which part to raise. The default, pre, raises the alpha number.")
    parser.add_argument("--check", action="store_true", help="Show the current version and change nothing.")
    args = parser.parse_args(argv)

    old = read_version()
    if args.check:
        print(f"Current version: {old} (shown as v{display(old)})")
        return 0
    new = next_version(old, args.part)

    # Replace the longer forms first, so that the short form inside them is not replaced twice.
    pairs = [(badge(old), badge(new)), (display(old), display(new)), (old, new)]
    # Work out every change before writing anything, so a problem leaves all files untouched.
    changes = []
    for path in SHOWN_IN:
        text = path.read_text(encoding="utf-8")
        updated = text
        for before, after in pairs:
            updated = updated.replace(before, after)
        if updated == text:
            raise SystemExit(f"{path.relative_to(ROOT)} does not show version {old}, so no file was changed. "
                             "Fix that file first.")
        changes.append((path, updated))
    for path, updated in changes:
        path.write_text(updated, encoding="utf-8")
        print(f"Updated {path.relative_to(ROOT)}")
    print(f"Version {old} (v{display(old)}) is now {new} (v{display(new)}).")
    # Stamp every document that the next push will change, so each one shows the new version.
    sys.path.insert(0, str(ROOT / "scripts"))
    import stamp_docs

    stamp_docs.main(["--unpushed"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
