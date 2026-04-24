"""SecretRoom: a small hidden room reached only via a HIDDEN door.

Mirrors SPD `rooms/secret/SecretRoom.java`. SecretRooms request a HIDDEN
door type on every connection so the painter writes SECRET_DOOR tiles
(visually indistinguishable from walls) at the boundary. They're built
small (5x5..6x6) and contain something noteworthy at the center —
typically a chest, a small stash, or an alchemy pot in the full SPD set.
For the remake's first port, we paint a plain floor; future passes can
inject content (e.g. a key chest, a stash heap).
"""

from typing import Tuple

from app.engine.dungeon.rooms.room import Direction, DoorType
from app.engine.dungeon.rooms.standard.standard_room import StandardRoom


class SecretRoom(StandardRoom):
    MIN_WIDTH = 5
    MAX_WIDTH = 6
    MIN_HEIGHT = 5
    MAX_HEIGHT = 6
    # SPD secret rooms have a single connection only.
    MAX_CONNECTIONS = {Direction.ALL: 1, Direction.LEFT: 1, Direction.TOP: 1,
                        Direction.RIGHT: 1, Direction.BOTTOM: 1}

    def min_width(self) -> int: return self.MIN_WIDTH
    def max_width(self) -> int: return self.MAX_WIDTH
    def min_height(self) -> int: return self.MIN_HEIGHT
    def max_height(self) -> int: return self.MAX_HEIGHT

    # Secret rooms shouldn't host random water/grass blobs that could leak
    # into the outer world via the (visually-walled) hidden door.
    def can_place_water(self, p: Tuple[int, int]) -> bool: return False
    def can_place_grass(self, p: Tuple[int, int]) -> bool: return False
    # Traps make a secret room an unfair surprise — keep them out for now.
    def can_place_trap(self, p: Tuple[int, int]) -> bool: return False

    def paint(self, level) -> None:
        level.fill_rect(self.left, self.top, self.right, self.bottom, level.WALL)
        level.fill_rect(self.left + 1, self.top + 1, self.right - 1, self.bottom - 1, level.FLOOR)
        for door in self.connected.values():
            if door is not None:
                door.set(DoorType.HIDDEN)
