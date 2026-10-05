from taskiq import TaskiqEvents, TaskiqState

import app.core.database  # noqa: F401  # registers the DB startup hook first; this hook needs state.session_factory
from app.content.loader import load_content
from app.core.broker import broker
from app.options.publish import publish_options


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def publish_options_on_startup(state: TaskiqState) -> None:
    async with state.session_factory() as session:
        await publish_options(session, load_content())
