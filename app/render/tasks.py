import hashlib

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from app.core.broker import broker
from app.core.database import get_session
from app.render.latex import compile_latex
from app.render.models import CvPdf
from app.storage.s3 import upload_pdf

TEST_DOCUMENT = r"\documentclass{article}\begin{document}Hello\end{document}"


@broker.task(task_name="cv.compile_test.v1")
async def compile_test(session: AsyncSession = TaskiqDepends(get_session)) -> str:
    digest = hashlib.sha256(TEST_DOCUMENT.encode("utf-8")).hexdigest()
    key = f"{digest}.pdf"

    hit = await session.execute(
        update(CvPdf).where(CvPdf.digest == digest).values(last_used_at=func.now()).returning(CvPdf.digest)
    )
    found = hit.scalar_one_or_none()
    await session.commit()

    if found is not None:
        return key

    pdf = await compile_latex(TEST_DOCUMENT)

    await upload_pdf(key, pdf)

    await session.execute(
        insert(CvPdf).values(digest=digest, size_bytes=len(pdf)).on_conflict_do_nothing(index_elements=[CvPdf.digest])
    )
    await session.commit()
    return key
