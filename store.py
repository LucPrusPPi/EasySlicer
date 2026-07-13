from __future__ import annotations

import json
from pathlib import Path

from engine import Recipe

USER_DIR = Path.home() / ".easy_slicer"
RECIPES_FILE = USER_DIR / "recipes.json"


def _ensure() -> None:
    USER_DIR.mkdir(parents=True, exist_ok=True)


def load_recipes() -> list[Recipe]:
    _ensure()
    if not RECIPES_FILE.is_file():
        return []
    try:
        data = json.loads(RECIPES_FILE.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else []
        return [Recipe.from_dict(x) for x in items]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def save_recipes(recipes: list[Recipe]) -> None:
    _ensure()
    RECIPES_FILE.write_text(
        json.dumps([r.to_dict() for r in recipes], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
