import asyncio

from app.content.loader import load_content
from app.content.selection.pipeline import select
from app.content.selection.request import SelectionRequest
from app.core.config import settings
from app.render.compile import compile_latex
from app.render.cv import render_cv


async def check() -> None:
    content = load_content()
    for title in content.titles:
        request = SelectionRequest.model_validate({"title_id": title.id}, context={"content": content})
        pdf = await compile_latex(render_cv(select(content, request), settings.contact))
        assert pdf.startswith(b"%PDF"), (title.id, pdf[:20])
        print(f"compile ok: {title.id} ({len(pdf)} bytes)")


def main() -> None:
    asyncio.run(check())


if __name__ == "__main__":
    main()
