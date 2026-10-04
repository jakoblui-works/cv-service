import pytest

from app.render import tasks


@pytest.fixture
def fake_pdf() -> bytes:
    return b"%PDF-fake"


@pytest.fixture
def compile_calls(monkeypatch: pytest.MonkeyPatch, fake_pdf: bytes) -> list[str]:
    calls: list[str] = []

    async def fake_compile(source: str) -> bytes:
        calls.append(source)
        return fake_pdf

    monkeypatch.setattr(tasks, "compile_latex", fake_compile)
    return calls


@pytest.fixture
def upload_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, bytes]]:
    calls: list[tuple[str, bytes]] = []

    async def fake_upload(key: str, pdf: bytes) -> None:
        calls.append((key, pdf))

    monkeypatch.setattr(tasks, "upload_pdf", fake_upload)

    return calls
