import asyncio

from app.core.broker import broker
from app.health.tasks import ping


async def main() -> None:
    try:
        await broker.startup()
        task = await ping.kiq("hello")
        result = await task.wait_result(timeout=10)
        print(result.return_value)
    finally:
        await broker.shutdown()


asyncio.run(main())
