import hashlib
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.render.models import CvPdf
from app.render.tasks import TEST_DOCUMENT, compile_test


@pytest.mark.asyncio
async def test_compile_miss(
    session: AsyncSession,
    compile_calls: list[str],
    upload_calls: list[tuple[str, bytes]],
    fake_pdf: bytes,
) -> None:
    digest = hashlib.sha256(TEST_DOCUMENT.encode("utf-8")).hexdigest()

    key = await compile_test(session=session)

    assert key == f"{digest}.pdf"
    assert compile_calls == [TEST_DOCUMENT]
    assert upload_calls == [(key, fake_pdf)]

    cvpdf = await session.scalar(select(CvPdf).where(CvPdf.digest == digest))

    assert cvpdf is not None
    assert cvpdf.size_bytes == len(fake_pdf)


@pytest.mark.asyncio
async def test_compile_hit(
    session: AsyncSession,
    compile_calls: list[str],
    upload_calls: list[tuple[str, bytes]],
) -> None:
    digest = hashlib.sha256(TEST_DOCUMENT.encode("utf-8")).hexdigest()
    last_used_at = datetime(2000, 1, 1, tzinfo=UTC)

    existing_pdf = CvPdf(digest=digest, size_bytes=2500, last_used_at=last_used_at)

    session.add(existing_pdf)
    await session.commit()

    key = await compile_test(session=session)

    assert key == f"{digest}.pdf"
    assert compile_calls == []
    assert upload_calls == []

    await session.refresh(existing_pdf)

    assert existing_pdf is not None
    assert existing_pdf.last_used_at > last_used_at
