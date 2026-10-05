from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from app.render.latex_text import Latex, escape_latex

MONTHS = ("Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.")


def month_year(day: date) -> str:
    return f"{MONTHS[day.month - 1]} {day.year}"


def finalize(value: object) -> Latex:
    if value is None:
        raise ValueError("Missing value")

    if isinstance(value, Latex):
        return value

    return escape_latex(str(value))


env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    block_start_string=r"\BLOCK{",
    block_end_string="}",
    variable_start_string=r"\VAR{",
    variable_end_string="}",
    comment_start_string=r"\#{",
    comment_end_string="}",
    undefined=StrictUndefined,
    finalize=finalize,
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)

env.filters["month_year"] = month_year
