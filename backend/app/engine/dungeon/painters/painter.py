"""Base Painter abstraction.

A Painter takes the finished Room layout and writes the tile grid. The
subclass order of operations is orchestrated here; region-specific
details (WALL_DECO above water, EMPTY_DECO scatter, etc.) live in
per-region subclasses' `decorate()`.
"""

from __future__ import annotations

from typing import List

from app.engine.dungeon.painters.level import LevelCanvas
from app.engine.dungeon.rooms.room import Room


class Painter:
    def paint(self, level: LevelCanvas, rooms: List[Room]) -> bool:
        raise NotImplementedError
