from functools import cache
from pathlib import Path

import yaml

from app.content.models import Content

DATA_DIR = Path(__file__).parent / "data"
DATA_FILES = ("static", "skills", "concepts", "titles", "experience", "layout")


@cache
def load_content() -> Content:
    raw: dict[str, object] = {
        name: yaml.safe_load((DATA_DIR / f"{name}.yaml").read_text(encoding="utf-8")) for name in DATA_FILES
    }
    return Content.model_validate(raw)
