from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Recipe:
    name: str = "Мой шаблон"
    split_char: str = ":"
    field_order: list[int] = field(default_factory=list)
    join_char: str = ";"
    min_parts: int = 0
    dedupe_first: bool = True
    skip_empty: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Recipe:
        known = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in known})

    def min_parts_effective(self) -> int:
        if self.min_parts > 0:
            return self.min_parts
        if not self.field_order:
            return 1
        return max(self.field_order) + 1


def split_line(line: str, char: str) -> list[str]:
    if char == "\\t":
        char = "\t"
    return [p.strip() for p in line.split(char)]


def detect_parts(sample: str, split_char: str) -> list[str]:
    line = sample.strip().lstrip("\ufeff")
    if not line:
        return []
    return split_line(line, split_char)


def transform_line(line: str, recipe: Recipe) -> str | None:
    line = line.strip().lstrip("\ufeff")
    if not line:
        return None
    if line.startswith("#"):
        return None

    parts = split_line(line, recipe.split_char)
    if len(parts) < recipe.min_parts_effective():
        return None
    if not recipe.field_order:
        return None

    picked: list[str] = []
    for idx in recipe.field_order:
        if idx < 0 or idx >= len(parts):
            return None
        val = parts[idx].strip()
        if not val:
            return None
        picked.append(val)

    join = "\t" if recipe.join_char == "\\t" else recipe.join_char
    return join.join(picked)


def process_text(text: str, recipe: Recipe) -> tuple[list[str], dict[str, int]]:
    stats = {"input": 0, "output": 0, "skipped": 0, "duplicates": 0}
    seen: set[str] = set()
    out: list[str] = []

    for raw in text.splitlines():
        if recipe.skip_empty and not raw.strip():
            continue
        stats["input"] += 1
        row = transform_line(raw, recipe)
        if row is None:
            stats["skipped"] += 1
            continue
        if recipe.dedupe_first:
            key = row.split(recipe.join_char if recipe.join_char != "\\t" else "\t")[0]
            if key in seen:
                stats["duplicates"] += 1
                continue
            seen.add(key)
        out.append(row)
        stats["output"] += 1

    return out, stats
