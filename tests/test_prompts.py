"""The terminal questions: valid answers are accepted, and invalid ones are asked again."""

import pytest

from getbill.prompts import ask_choice, ask_letter, ask_selection, ask_text, ask_yes_no, parse_selection


def scripted(monkeypatch, *answers):
    """Make input() return these answers in order. Asking once more than expected fails the test."""
    replies = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(replies))


@pytest.mark.parametrize("text, count, expected", [
    ("1", 3, [0]),
    ("all", 3, [0, 1, 2]),
    ("A", 2, [0, 1]),
    ("*", 2, [0, 1]),
    ("3,1", 3, [0, 2]),
    ("1-3", 3, [0, 1, 2]),
    ("2, 2", 3, [1]),
    (" 1 , 3 ", 3, [0, 2]),
])
def test_selection_accepts_numbers_ranges_and_all(text, count, expected):
    assert parse_selection(text, count) == expected


@pytest.mark.parametrize("text", ["", ",", "0", "4", "x", "3-1", "1-x"])
def test_selection_rejects_answers_outside_the_list(text):
    with pytest.raises(ValueError):
        parse_selection(text, 3)


def test_selection_question_repeats_until_the_answer_is_valid(monkeypatch, capsys):
    scripted(monkeypatch, "9", "1-2")
    assert ask_selection("Which files", 2) == [0, 1]
    assert "9 is not in the list" in capsys.readouterr().out


def test_choice_repeats_until_a_listed_number(monkeypatch, capsys):
    scripted(monkeypatch, "9", "x", "2")
    assert ask_choice("Pick one", ["a", "b"]) == 1
    assert capsys.readouterr().out.count("Please type a number from 1 to 2.") == 2


def test_choice_enter_takes_the_default(monkeypatch):
    scripted(monkeypatch, "")
    assert ask_choice("Pick one", ["a", "b"], default_index=1) == 1


@pytest.mark.parametrize("typed, default, expected", [
    ("", True, True),
    ("", False, False),
    ("Y", False, True),
    ("no", True, False),
])
def test_yes_no(monkeypatch, typed, default, expected):
    scripted(monkeypatch, typed)
    assert ask_yes_no("Continue?", default=default) is expected


def test_yes_no_repeats_on_other_answers(monkeypatch, capsys):
    scripted(monkeypatch, "maybe", "y")
    assert ask_yes_no("Continue?") is True
    assert "Please answer y or n." in capsys.readouterr().out


def test_text_uses_the_default_or_allows_empty(monkeypatch):
    scripted(monkeypatch, "", "")
    assert ask_text("Folder", default="reports") == "reports"
    assert ask_text("Folder", allow_empty=True) == ""


def test_text_without_a_default_repeats_until_answered(monkeypatch, capsys):
    scripted(monkeypatch, "", "reports")
    assert ask_text("Folder") == "reports"
    assert "Please type an answer." in capsys.readouterr().out


def test_letter_ignores_case_and_repeats_on_unknown_letters(monkeypatch, capsys):
    scripted(monkeypatch, "z", "T")
    assert ask_letter("What now?", {"o": "Overwrite", "t": "Add the time"}) == "t"
    assert "Please type one of: o, t." in capsys.readouterr().out
