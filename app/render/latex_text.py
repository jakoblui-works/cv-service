import re

LATEX_ESCAPE_LOOKUP: dict[str, str] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

_LATEX_PATTERN = re.compile("|".join(re.escape(char) for char in LATEX_ESCAPE_LOOKUP))


class Latex(str):
    """Valid LaTeX source code - must not be escaped again."""


def escape_latex(text: str) -> Latex:
    """Escape LaTeX special characters in plain text."""
    return Latex(_LATEX_PATTERN.sub(lambda match: LATEX_ESCAPE_LOOKUP[match.group()], text))
