import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.render.escape import LATEX_ESCAPE_LOOKUP, Latex, escape_latex

SPECIAL_CHARS = "".join(LATEX_ESCAPE_LOOKUP)


@pytest.mark.parametrize(("raw", "expected"), LATEX_ESCAPE_LOOKUP.items())
def test_each_special_char_is_escaped(raw: str, expected: str) -> None:
    assert escape_latex(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ],
)
def test_special_char_replacements(raw: str, expected: str) -> None:
    assert escape_latex(raw) == expected


def test_replacements_are_not_escaped_again() -> None:
    assert escape_latex("\\{") == r"\textbackslash{}\{"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("C#", r"C\#"),
        ("~30%", r"\textasciitilde{}30\%"),
        ("R&D", r"R\&D"),
        ("snake_case", r"snake\_case"),
    ],
)
def test_real_strings(raw: str, expected: str) -> None:
    assert escape_latex(raw) == expected


@given(st.text(alphabet=st.characters(exclude_characters=SPECIAL_CHARS)))
def test_text_without_special_chars_is_unchanged(text: str) -> None:
    assert escape_latex(text) == text


def test_empty_string_is_unchanged() -> None:
    assert escape_latex("") == ""


def test_returns_latex() -> None:
    assert isinstance(escape_latex("x"), Latex)
