import asyncio

from app.core.broker import broker
from app.render.tasks import compile_test


async def main() -> None:
    try:
        await broker.startup()
        task = await compile_test.kiq()
        result = await task.wait_result(timeout=60)
        print(result.return_value)
    finally:
        await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
