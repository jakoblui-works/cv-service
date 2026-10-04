import pytest

from tests.content.builder import Builder


@pytest.fixture
def build() -> Builder:
    return Builder()
