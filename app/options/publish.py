from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.models import Content
from app.options.form import VERSION, build_form_options
from app.options.models import PublishedOptions


async def publish_options(session: AsyncSession, content: Content) -> None:
    options = build_form_options(content).model_dump(mode="json")

    stmt = insert(PublishedOptions).values(
        version=VERSION,
        options=options,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[PublishedOptions.version], set_={"options": stmt.excluded.options, "updated_at": func.now()}
    )

    await session.execute(stmt)
    await session.commit()
