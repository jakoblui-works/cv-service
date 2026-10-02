import hashlib

from app.core.broker import broker
from app.render.latex import compile_latex
from app.storage.s3 import upload_pdf

TEST_DOCUMENT = r"\documentclass{article}\begin{document}Hello\end{document}"


@broker.task(task_name="cv.compile_test.v1")
async def compile_test() -> str:
    digest = hashlib.sha256(TEST_DOCUMENT.encode("utf-8")).hexdigest()
    key = f"{digest}.pdf"

    pdf = await compile_latex(TEST_DOCUMENT)

    await upload_pdf(key, pdf)

    return key
