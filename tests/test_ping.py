import pytest

from app.health.tasks import ping


@pytest.mark.asyncio
async def test_ping() -> None:
    assert await ping("hello") == "pong: hello"
