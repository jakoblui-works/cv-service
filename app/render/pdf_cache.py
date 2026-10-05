import hashlib

from sqlalchemy import func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.render.latex import compile_latex
from app.render.models import CvPdf
from app.storage.s3 import upload_pdf


async def get_or_compile_pdf(session: AsyncSession, source: str) -> str:
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    key = f"{digest}.pdf"

    hit = await session.execute(
        update(CvPdf).where(CvPdf.digest == digest).values(last_used_at=func.now()).returning(CvPdf.digest)
    )
    found = hit.scalar_one_or_none()
    await session.commit()

    if found is not None:
        return key

    pdf = await compile_latex(source)

    await upload_pdf(key, pdf)

    await session.execute(
        insert(CvPdf).values(digest=digest, size_bytes=len(pdf)).on_conflict_do_nothing(index_elements=[CvPdf.digest])
    )
    await session.commit()

    return key
