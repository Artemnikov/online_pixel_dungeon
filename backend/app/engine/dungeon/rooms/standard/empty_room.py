"""EmptyRoom: the simplest StandardRoom. Walls on the border, floor inside.

Mirrors SPD `rooms/standard/EmptyRoom.java`. This is the fallback room
when nothing more specific is wanted. Every connection is requested as a
REGULAR door (the painter's paint_doors step decides UNLOCKED vs HIDDEN
based on depth + reachability).
"""

from app.engine.dungeon.rooms.room import DoorType
from app.engine.dungeon.rooms.standard.standard_room import StandardRoom


class EmptyRoom(StandardRoom):
    def paint(self, level) -> None:
        level.fill_rect(self.left, self.top, self.right, self.bottom, level.WALL)
        level.fill_rect(self.left + 1, self.top + 1, self.right - 1, self.bottom - 1, level.FLOOR)
        for door in self.connected.values():
            if door is not None:
                door.set(DoorType.REGULAR)
