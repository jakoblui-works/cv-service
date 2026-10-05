import hashlib

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.render.tasks import generate

REQUEST: dict[str, object] = {
    "title_id": "technical-lead",
    "concept_ids": ["devops", "leadership"],
    "skill_ids": [],
}


@pytest.mark.asyncio
async def test_generate_compiles_and_returns_key(
    session: AsyncSession,
    compile_calls: list[str],
    upload_calls: list[tuple[str, bytes]],
) -> None:
    key = await generate(request=REQUEST, session=session)

    assert len(compile_calls) == 1
    assert key == f"{hashlib.sha256(compile_calls[0].encode('utf-8')).hexdigest()}.pdf"
    assert [uploaded_key for uploaded_key, _ in upload_calls] == [key]


@pytest.mark.asyncio
async def test_same_request_compiles_once(
    session: AsyncSession,
    compile_calls: list[str],
    upload_calls: list[tuple[str, bytes]],
) -> None:
    first = await generate(request=REQUEST, session=session)
    second = await generate(request=REQUEST, session=session)

    assert second == first
    assert len(compile_calls) == 1


@pytest.mark.asyncio
async def test_id_order_does_not_change_key(
    session: AsyncSession,
    compile_calls: list[str],
    upload_calls: list[tuple[str, bytes]],
) -> None:
    reordered = {**REQUEST, "concept_ids": ["leadership", "devops"]}

    assert await generate(request=reordered, session=session) == await generate(request=REQUEST, session=session)


@pytest.mark.asyncio
async def test_unknown_id_is_rejected(
    session: AsyncSession,
    compile_calls: list[str],
    upload_calls: list[tuple[str, bytes]],
) -> None:
    with pytest.raises(ValidationError):
        await generate(request={**REQUEST, "concept_ids": ["cobol"]}, session=session)

    assert compile_calls == []
