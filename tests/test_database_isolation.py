import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.render.models import CvPdf

DIGEST = "a" * 64
SIZE_BYTES = 2500


@pytest.mark.asyncio
async def test_commit_is_visible_within_test(session: AsyncSession) -> None:
    cvpdf = CvPdf(digest=DIGEST, size_bytes=SIZE_BYTES)
    session.add(cvpdf)
    await session.commit()

    loaded = await session.scalar(select(CvPdf).where(CvPdf.digest == DIGEST))

    assert loaded is not None


@pytest.mark.asyncio
async def test_previous_test_rolled_back(session: AsyncSession) -> None:
    cvpdf = await session.scalar(select(CvPdf).where(CvPdf.digest == DIGEST))

    assert cvpdf is None
