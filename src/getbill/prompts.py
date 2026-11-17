"""Helpers that ask the user questions in the terminal and validate the answers."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence


def ask_text(question: str, default: Optional[str] = None, allow_empty: bool = False) -> str:
    """Ask for free text. Pressing Enter returns the default when one is given."""
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{question}{suffix}: ").strip()
        if answer:
            return answer
        if default:
            return default
        if allow_empty:
            return ""
        print("  Please type an answer.")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes-or-no question. Pressing Enter returns the default."""
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please answer y or n.")


def ask_choice(question: str, options: Sequence[str], default_index: int = 0) -> int:
    """Show a numbered list and return the zero-based index of the chosen option."""
    print(question)
    for number, option in enumerate(options, start=1):
        marker = "  (default)" if number - 1 == default_index else ""
        print(f"  {number}. {option}{marker}")
    while True:
        answer = input(f"Type a number [{default_index + 1}]: ").strip()
        if not answer:
            return default_index
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print(f"  Please type a number from 1 to {len(options)}.")


def ask_letter(question: str, choices: Dict[str, str]) -> str:
    """Ask the user to pick one option by its letter, for example o, s or t."""
    print(question)
    for letter, label in choices.items():
        print(f"  {letter}  {label}")
    allowed = "/".join(choices)
    while True:
        answer = input(f"Type {allowed}: ").strip().lower()
        if answer in choices:
            return answer
        print(f"  Please type one of: {', '.join(choices)}.")


def parse_selection(text: str, count: int) -> List[int]:
    """Turn an answer such as "1,3,5-7" or "all" into sorted zero-based indexes.

    Raises ValueError with a readable message when the answer is not valid.
    """
    text = text.strip().lower()
    if text in ("all", "a", "*"):
        return list(range(count))
    chosen = set()
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            start_text, _, end_text = part.partition("-")
            if not (start_text.isdigit() and end_text.isdigit()):
                raise ValueError(f'"{part}" is not a range of numbers such as 2-5.')
            start, end = int(start_text), int(end_text)
            if start > end:
                raise ValueError(f'The range "{part}" starts after it ends.')
            numbers = range(start, end + 1)
        else:
            if not part.isdigit():
                raise ValueError(f'"{part}" is not a number.')
            numbers = [int(part)]
        for number in numbers:
            if not 1 <= number <= count:
                raise ValueError(f"{number} is not in the list. Use numbers from 1 to {count}.")
            chosen.add(number - 1)
    if not chosen:
        raise ValueError("No files were chosen.")
    return sorted(chosen)


def ask_selection(question: str, count: int) -> List[int]:
    """Ask which items to use from a numbered list, accepting lists, ranges and "all"."""
    while True:
        answer = input(f"{question}: ").strip()
        try:
            return parse_selection(answer, count)
        except ValueError as error:
            print(f"  {error}")
