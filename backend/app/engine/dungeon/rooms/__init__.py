"""Room abstractions ported from SPD `levels/rooms/`.

A Room is a rectangle (left/top/right/bottom, inclusive on all sides like
SPD) plus connection metadata. Each subclass owns its `paint(level)`
implementation, which stamps the room's tiles into the level's grid.
The painter pipeline (see ../painters/) calls paint() per room and then
overwrites the door cells.
"""

from app.engine.dungeon.rooms.room import (  # noqa: F401
    Direction,
    Door,
    DoorType,
    Room,
)
