"""Send a cv.generate.v1 task through the broker and print the resulting PDF key.

python -m scripts.send_generate --title technical-lead --concept devops
"""

import argparse
import asyncio

from app.core.broker import broker
from app.generate.tasks import generate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--title", default="technical-lead", help="title id")
    parser.add_argument("--concept", action="append", default=[], help="concept id (repeatable)")
    parser.add_argument("--skill", action="append", default=[], help="skill id (repeatable)")
    return parser.parse_args()


async def main(request: dict[str, object]) -> None:
    try:
        await broker.startup()
        task = await generate.kiq(request=request)
        result = await task.wait_result(timeout=60)
        if result.is_err:
            raise SystemExit(f"task failed: {result.error!r}")
        print(result.return_value)
    finally:
        await broker.shutdown()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main({"title_id": args.title, "concept_ids": args.concept, "skill_ids": args.skill}))
