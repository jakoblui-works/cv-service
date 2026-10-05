from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from app.content.loader import load_content
from app.content.selection.pipeline import select
from app.content.selection.request import SelectionRequest
from app.core.broker import broker
from app.core.config import settings
from app.core.database import get_session
from app.pdfs.cache import get_or_compile_pdf
from app.render.cv import render_cv


@broker.task(task_name="cv.generate.v1")
async def generate(request: dict[str, object], session: AsyncSession = TaskiqDepends(get_session)) -> str:
    content = load_content()
    selection_request = SelectionRequest.model_validate(request, context={"content": content})
    source = render_cv(select(content, selection_request), settings.contact)

    return await get_or_compile_pdf(session, source)
