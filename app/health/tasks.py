from app.core.broker import broker


@broker.task(task_name="cv.ping.v1")
async def ping(message: str) -> str:
    return f"pong: {message}"
