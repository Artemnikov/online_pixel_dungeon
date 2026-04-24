"""StandardRoom: the "normal rooms" that host mobs, items, and stairs.

Mirrors SPD `rooms/standard/StandardRoom.java`. Size categories match SPD
exactly (NORMAL 4-10, LARGE 10-14, GIANT 14-18); `size_factor()` is used
by RegularBuilder to weight larger rooms onto the main path and out of
the branch pool.
"""

from __future__ import annotations

import enum
from typing import List, Optional

from app.engine.dungeon.rooms.room import Room


class SizeCategory(enum.Enum):
    NORMAL = (4, 10, 1)
    LARGE = (10, 14, 2)
    GIANT = (14, 18, 3)

    @property
    def min_dim(self) -> int: return self.value[0]
    @property
    def max_dim(self) -> int: return self.value[1]
    @property
    def room_value(self) -> int: return self.value[2]


class StandardRoom(Room):
    """Base for rooms that can be "normal" floor content.

    Set `size_cat` before placement; `min_width/height` and
    `max_width/height` pull their bounds from the category.
    """

    def __init__(self):
        super().__init__()
        self.size_cat: SizeCategory = SizeCategory.NORMAL

    def size_cat_probs(self) -> List[float]:
        """Weighted probability of each SizeCategory. Override for variety."""
        return [1.0, 0.0, 0.0]  # always NORMAL by default

    def set_size_cat(self, rng, max_room_value: Optional[int] = None) -> bool:
        """Roll a SizeCategory weighted by size_cat_probs.

        `max_room_value` caps the rolled size (used when a level has space
        budget for only a NORMAL room). Returns False if rolling failed
        (all probabilities zeroed out).
        """
        probs = list(self.size_cat_probs())
        cats = list(SizeCategory)
        if len(probs) != len(cats):
            return False
        if max_room_value is not None:
            for i, cat in enumerate(cats):
                if cat.room_value > max_room_value:
                    probs[i] = 0.0
        total = sum(probs)
        if total <= 0:
            return False
        roll = rng.random() * total
        acc = 0.0
        for i, p in enumerate(probs):
            acc += p
            if roll <= acc:
                self.size_cat = cats[i]
                return True
        self.size_cat = cats[-1]
        return True

    def min_width(self) -> int: return self.size_cat.min_dim
    def max_width(self) -> int: return self.size_cat.max_dim
    def min_height(self) -> int: return self.size_cat.min_dim
    def max_height(self) -> int: return self.size_cat.max_dim

    def size_factor(self) -> int:
        return self.size_cat.room_value

    def connection_weight(self) -> int:
        return self.size_factor() ** 2
