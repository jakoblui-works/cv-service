from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st
from jinja2 import UndefinedError

from app.render.environment import env
from app.render.latex_text import Latex, escape_latex


def render(source: str, **values: object) -> str:
    return env.from_string(source).render(**values)


def test_plain_text_is_escaped() -> None:
    assert render(r"\VAR{x}", x="R&D") == r"R\&D"


@given(st.text())
def test_values_are_escaped_like_escape_latex(text: str) -> None:
    assert render(r"\VAR{x}", x=text) == escape_latex(text)


def test_latex_passes_through_unchanged() -> None:
    assert render(r"\VAR{x}", x=Latex(r"\textbf{a}")) == r"\textbf{a}"


def test_non_string_values_are_converted() -> None:
    assert render(r"\VAR{x}", x=42) == "42"


def test_none_raises() -> None:
    with pytest.raises(ValueError):
        render(r"\VAR{x}", x=None)


def test_undefined_raises() -> None:
    with pytest.raises(UndefinedError):
        render(r"\VAR{x}")


def test_block_and_comment_lines_leave_no_blank_lines() -> None:
    source = r"""\#{ items }
\BLOCK{for item in items}
\item \VAR{item}
\BLOCK{endfor}
done
"""

    assert render(source, items=["a_b", "c"]) == "\\item a\\_b\n\\item c\ndone\n"


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 1, 1), "Jan. 2026"),
        (date(2025, 5, 1), "May 2025"),
        (date(2024, 12, 1), "Dec. 2024"),
    ],
)
def test_month_year(day: date, expected: str) -> None:
    assert render(r"\VAR{d | month_year}", d=day) == expected
