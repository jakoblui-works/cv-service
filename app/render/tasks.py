from app.core.broker import broker
from app.render.latex import compile_latex

TEST_DOCUMENT = r"\documentclass{article}\begin{document}Hello\end{document}"


@broker.task(task_name="cv.compile_test.v1")
async def compile_test() -> int:
    pdf = await compile_latex(TEST_DOCUMENT)
    return len(pdf)
