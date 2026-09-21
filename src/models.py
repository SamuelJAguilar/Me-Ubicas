from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Classification:
    id: int
    slug: str
    name: str
    multi_select: bool
    sort_order: int = 0


@dataclass(frozen=True)
class ClassificationValue:
    id: int
    classification_id: int
    name: str


@dataclass
class Character:
    id: int
    name: str
    image_path: str
    traits: dict[int, set[int]] = field(default_factory=dict)

    def value_ids(self) -> set[int]:
        owned: set[int] = set()
        for values in self.traits.values():
            owned.update(values)
        return owned
