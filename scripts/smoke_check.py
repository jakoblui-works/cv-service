import asyncio

from app.render.latex import compile_latex
from app.render.tasks import TEST_DOCUMENT


def main() -> None:
    pdf = asyncio.run(compile_latex(TEST_DOCUMENT))
    assert pdf.startswith(b"%PDF"), pdf[:20]
    print(f"compile ok: {len(pdf)} bytes")


if __name__ == "__main__":
    main()
