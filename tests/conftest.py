import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Must be set before anything imports app.core.config: settings are read at import time.
os.environ["DATABASE__NAME"] = "cv_test"

from app.core.config import settings  # noqa: E402
from app.pdfs import cache  # noqa: E402

ALEMBIC_INI = Path(__file__).parents[1] / "alembic.ini"


async def _recreate_database() -> None:
    name = settings.database.name
    admin_url = make_url(settings.database.url).set(database="postgres")
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            await conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    if not settings.database.name.endswith("_test"):
        raise RuntimeError(f"Refusing to recreate non-test database {settings.database.name!r}")
    asyncio.run(_recreate_database())
    command.upgrade(Config(str(ALEMBIC_INI)), "head")


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(settings.database.url)
    async with engine.connect() as conn:
        outer = await conn.begin()
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False) as s:
            yield s
        await outer.rollback()
    await engine.dispose()


# Fakes for the PDF cache's compile/upload calls (patched where app.pdfs.cache looks them up).
@pytest.fixture
def fake_pdf() -> bytes:
    return b"%PDF-fake"


@pytest.fixture
def compile_calls(monkeypatch: pytest.MonkeyPatch, fake_pdf: bytes) -> list[str]:
    calls: list[str] = []

    async def fake_compile(source: str) -> bytes:
        calls.append(source)
        return fake_pdf

    monkeypatch.setattr(cache, "compile_latex", fake_compile)
    return calls


@pytest.fixture
def upload_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, bytes]]:
    calls: list[tuple[str, bytes]] = []

    async def fake_upload(key: str, pdf: bytes) -> None:
        calls.append((key, pdf))

    monkeypatch.setattr(cache, "upload_pdf", fake_upload)

    return calls
