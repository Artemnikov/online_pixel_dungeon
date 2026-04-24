"""Base class for "corridor rooms" — small rectangles that exist only to
route connections between StandardRooms. Mirrors SPD
`rooms/connection/ConnectionRoom.java`: default size 3-10, must have >= 2
connections (otherwise it's a dead-end corridor, which is pointless)."""

from typing import Dict

from app.engine.dungeon.rooms.room import Direction, Room


class ConnectionRoom(Room):
    MIN_WIDTH = 3
    MAX_WIDTH = 10
    MIN_HEIGHT = 3
    MAX_HEIGHT = 10
    MIN_CONNECTIONS: Dict[Direction, int] = {Direction.ALL: 2}
