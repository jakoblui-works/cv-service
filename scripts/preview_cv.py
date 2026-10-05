"""Render and compile a CV for one request from the real content.

Needs TeX Live, so run it in the image via scripts/preview_cv.sh:

    scripts/preview_cv.sh --title technical-lead --concept devops --skill python

Writes previews/<name>.pdf and previews/<name>.tex. Uses the contact details from .env,
so previews/ is git-ignored and must never be committed.
"""

import argparse
import asyncio
from pathlib import Path

from app.content.loader import load_content
from app.content.selection.pipeline import select
from app.content.selection.request import SelectionRequest
from app.core.config import settings
from app.render.compile import compile_latex
from app.render.cv import render_cv

OUT_DIR = Path("previews")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--title", required=True, help="title id")
    parser.add_argument("--concept", action="append", default=[], help="concept id (repeatable)")
    parser.add_argument("--skill", action="append", default=[], help="skill id (repeatable)")
    parser.add_argument("--name", help="output file name without extension (default: the title id)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    content = load_content()
    request = SelectionRequest.model_validate(
        {"title_id": args.title, "concept_ids": args.concept, "skill_ids": args.skill},
        context={"content": content},
    )

    source = render_cv(select(content, request), settings.contact)
    pdf = asyncio.run(compile_latex(source))

    OUT_DIR.mkdir(exist_ok=True)
    name = args.name or args.title
    (OUT_DIR / f"{name}.tex").write_text(source, encoding="utf-8")
    (OUT_DIR / f"{name}.pdf").write_bytes(pdf)
    print(f"wrote {OUT_DIR / name}.pdf ({len(pdf)} bytes)")


if __name__ == "__main__":
    main()
