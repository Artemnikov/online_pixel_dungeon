"""EntranceRoom: a StandardRoom that drops STAIRS_UP at a random interior cell."""

from app.engine.dungeon.rooms.room import DoorType
from app.engine.dungeon.rooms.standard.standard_room import StandardRoom


class EntranceRoom(StandardRoom):
    def is_entrance(self) -> bool:
        return True

    # Don't put traps in the room the player wakes up in.
    def can_place_trap(self, p):
        return False

    def paint(self, level) -> None:
        level.fill_rect(self.left, self.top, self.right, self.bottom, level.WALL)
        level.fill_rect(self.left + 1, self.top + 1, self.right - 1, self.bottom - 1, level.FLOOR)
        x, y = self.random(level.rng, margin=1)
        level.set_tile(x, y, level.STAIRS_UP)
        level.entrance = (x, y)
        for door in self.connected.values():
            if door is not None:
                door.set(DoorType.REGULAR)
