"""TunnelRoom: L-shaped corridor through a ConnectionRoom.

Port of SPD `rooms/connection/TunnelRoom.java`. For each door, draws a
straight line inward from the door, then bends toward a shared centre
point (the centroid of all doors, clamped to the interior). The result
is visually a sparse set of corridors meeting in the middle of the
connection room — no filled floor, just paths.

Each door is requested as a TUNNEL type so the painter's paintDoors
doesn't put a door tile at the corridor boundary (tunnels spill into the
adjacent room through an open floor cell).
"""

from typing import Tuple

from app.engine.dungeon.rooms.connection.connection_room import ConnectionRoom
from app.engine.dungeon.rooms.room import DoorType


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(v, hi))


class TunnelRoom(ConnectionRoom):
    def paint(self, level) -> None:
        floor = level.tunnel_tile()

        doors = [d for d in self.connected.values() if d is not None]
        if not doors:
            return

        # Meeting point = door centroid, clamped to strict interior.
        mx = sum(d.x for d in doors) / len(doors)
        my = sum(d.y for d in doors) / len(doors)
        meet = (
            _clamp(round(mx), self.left + 1, self.right - 1),
            _clamp(round(my), self.top + 1, self.bottom - 1),
        )

        for door in doors:
            # Step one cell inward from the door so we don't write over it.
            start = self._step_inward((door.x, door.y))

            # L-shape: first go in along one axis until aligned with meet,
            # then along the other axis to the meet point.
            if door.x == self.left or door.x == self.right:
                mid = (meet[0], start[1])
            else:
                mid = (start[0], meet[1])

            _draw_line(level, start, mid, floor)
            _draw_line(level, mid, meet, floor)
            door.set(DoorType.TUNNEL)

    def _step_inward(self, p: Tuple[int, int]) -> Tuple[int, int]:
        x, y = p
        if x == self.left:    return (x + 1, y)
        if x == self.right:   return (x - 1, y)
        if y == self.top:     return (x, y + 1)
        if y == self.bottom:  return (x, y - 1)
        return (x, y)


def _draw_line(level, a: Tuple[int, int], b: Tuple[int, int], tile: int) -> None:
    """Bresenham-ish step along the dominant axis."""
    x, y = a
    bx, by = b
    dx, dy = bx - x, by - y
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        level.set_tile(x, y, tile)
        return
    sx = dx / steps
    sy = dy / steps
    fx, fy = float(x), float(y)
    for _ in range(steps + 1):
        level.set_tile(round(fx), round(fy), tile)
        fx += sx
        fy += sy
