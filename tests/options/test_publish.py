from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.models import Content
from app.options.form import VERSION, build_form_options
from app.options.models import PublishedOptions
from app.options.publish import publish_options
from tests.content.builder import Builder


def _content(*title_ids: str) -> Content:
    build = Builder()
    return build.content(titles=[build.title(title_id) for title_id in title_ids])


async def _published(session: AsyncSession) -> list[dict[str, object]]:
    # Select the column, not the entity, so the result never comes from the session's identity map.
    rows = await session.scalars(select(PublishedOptions.options).where(PublishedOptions.version == VERSION))
    return list(rows)


@pytest.mark.asyncio
async def test_first_publish_creates_the_row(session: AsyncSession) -> None:
    content = _content("engineer")

    await publish_options(session, content)

    assert await _published(session) == [build_form_options(content).model_dump(mode="json")]


@pytest.mark.asyncio
async def test_publishing_again_replaces_the_options(session: AsyncSession) -> None:
    updated = _content("engineer", "lead")

    await publish_options(session, _content("engineer"))
    await publish_options(session, updated)

    assert await _published(session) == [build_form_options(updated).model_dump(mode="json")]
    assert await session.scalar(select(func.count()).select_from(PublishedOptions)) == 1


@pytest.mark.asyncio
async def test_publishing_again_bumps_updated_at(session: AsyncSession) -> None:
    # now() is constant within the test's outer transaction, so start from an explicitly old timestamp.
    old = datetime(2000, 1, 1, tzinfo=UTC)
    session.add(PublishedOptions(version=VERSION, options={}, updated_at=old))
    await session.commit()

    await publish_options(session, _content("engineer"))

    updated_at = await session.scalar(select(PublishedOptions.updated_at).where(PublishedOptions.version == VERSION))
    assert updated_at is not None
    assert updated_at > old
