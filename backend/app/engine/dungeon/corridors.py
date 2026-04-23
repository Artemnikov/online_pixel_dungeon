import math
import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from app.engine.dungeon.constants import TileType
from app.engine.dungeon.models import Room


class CorridorsMixin:
    """Mixin for room painting, corridor routing, and wall classification."""

    def _paint_room(self, room: Room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                self.grid[y][x] = TileType.FLOOR

        corners = {
            (room.x - 1, room.y - 1),
            (room.x + room.width, room.y - 1),
            (room.x - 1, room.y + room.height),
            (room.x + room.width, room.y + room.height),
        }
        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
                if (x, y) in corners:
                    continue
                if 0 <= x < self.width and 0 <= y < self.height:
                    if self.grid[y][x] == TileType.VOID:
                        self.grid[y][x] = TileType.WALL

    def _build_room_mask(self, rooms: List[Room]) -> List[List[int]]:
        mask = [[-1 for _ in range(self.width)] for _ in range(self.height)]
        for room in rooms:
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    mask[y][x] = room.room_id
            # Also block wall ring so corridors cannot route through it
            for y in range(room.y - 1, room.y + room.height + 1):
                for x in range(room.x - 1, room.x + room.width + 1):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if mask[y][x] == -1:
                            mask[y][x] = room.room_id
        return mask

    def _select_connection_points(
        self, room_a: Room, room_b: Room,
        used_door_positions: Optional[Set[Tuple[int, int]]] = None,
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
        used = used_door_positions or set()
        ax, ay = room_a.center
        bx, by = room_b.center

        if abs(bx - ax) >= abs(by - ay):
            if bx >= ax:
                wall_xa = room_a.x + room_a.width
                cands_ya = [y for y in range(room_a.y + 1, room_a.y + room_a.height - 1)
                            if not any(abs(y - dy) <= 1 for (dx, dy) in used if dx == wall_xa)]
                ya = self.rng.choice(cands_ya) if cands_ya else self.rng.randint(room_a.y + 1, room_a.y + room_a.height - 2)
                wall_xb = room_b.x - 1
                cands_yb = [y for y in range(room_b.y + 1, room_b.y + room_b.height - 1)
                            if not any(abs(y - dy) <= 1 for (dx, dy) in used if dx == wall_xb)]
                yb = self.rng.choice(cands_yb) if cands_yb else self.rng.randint(room_b.y + 1, room_b.y + room_b.height - 2)
                door_a = (wall_xa, ya)
                outside_a = (door_a[0] + 1, ya)
                door_b = (wall_xb, yb)
                outside_b = (door_b[0] - 1, yb)
            else:
                wall_xa = room_a.x - 1
                cands_ya = [y for y in range(room_a.y + 1, room_a.y + room_a.height - 1)
                            if not any(abs(y - dy) <= 1 for (dx, dy) in used if dx == wall_xa)]
                ya = self.rng.choice(cands_ya) if cands_ya else self.rng.randint(room_a.y + 1, room_a.y + room_a.height - 2)
                wall_xb = room_b.x + room_b.width
                cands_yb = [y for y in range(room_b.y + 1, room_b.y + room_b.height - 1)
                            if not any(abs(y - dy) <= 1 for (dx, dy) in used if dx == wall_xb)]
                yb = self.rng.choice(cands_yb) if cands_yb else self.rng.randint(room_b.y + 1, room_b.y + room_b.height - 2)
                door_a = (wall_xa, ya)
                outside_a = (door_a[0] - 1, ya)
                door_b = (wall_xb, yb)
                outside_b = (door_b[0] + 1, yb)
        else:
            if by >= ay:
                wall_ya = room_a.y + room_a.height
                cands_xa = [x for x in range(room_a.x + 1, room_a.x + room_a.width - 1)
                            if not any(abs(x - dx) <= 1 for (dx, dy) in used if dy == wall_ya)]
                xa = self.rng.choice(cands_xa) if cands_xa else self.rng.randint(room_a.x + 1, room_a.x + room_a.width - 2)
                wall_yb = room_b.y - 1
                cands_xb = [x for x in range(room_b.x + 1, room_b.x + room_b.width - 1)
                            if not any(abs(x - dx) <= 1 for (dx, dy) in used if dy == wall_yb)]
                xb = self.rng.choice(cands_xb) if cands_xb else self.rng.randint(room_b.x + 1, room_b.x + room_b.width - 2)
                door_a = (xa, wall_ya)
                outside_a = (xa, door_a[1] + 1)
                door_b = (xb, wall_yb)
                outside_b = (xb, door_b[1] - 1)
            else:
                wall_ya = room_a.y - 1
                cands_xa = [x for x in range(room_a.x + 1, room_a.x + room_a.width - 1)
                            if not any(abs(x - dx) <= 1 for (dx, dy) in used if dy == wall_ya)]
                xa = self.rng.choice(cands_xa) if cands_xa else self.rng.randint(room_a.x + 1, room_a.x + room_a.width - 2)
                wall_yb = room_b.y + room_b.height
                cands_xb = [x for x in range(room_b.x + 1, room_b.x + room_b.width - 1)
                            if not any(abs(x - dx) <= 1 for (dx, dy) in used if dy == wall_yb)]
                xb = self.rng.choice(cands_xb) if cands_xb else self.rng.randint(room_b.x + 1, room_b.x + room_b.width - 2)
                door_a = (xa, wall_ya)
                outside_a = (xa, door_a[1] - 1)
                door_b = (xb, wall_yb)
                outside_b = (xb, door_b[1] + 1)

        if not self._in_bounds(*outside_a) or not self._in_bounds(*outside_b):
            return None

        return door_a, outside_a, door_b, outside_b

    def _find_corridor_path(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        room_mask: List[List[int]],
    ) -> Optional[List[Tuple[int, int]]]:
        q = deque([start])
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}

        while q:
            cx, cy = q.popleft()
            if (cx, cy) == goal:
                break

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in came_from:
                    continue

                if room_mask[ny][nx] != -1 and (nx, ny) not in (start, goal):
                    continue

                came_from[(nx, ny)] = (cx, cy)
                q.append((nx, ny))

        if goal not in came_from:
            return None

        path = []
        curr: Optional[Tuple[int, int]] = goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]

        path.reverse()
        return path

    def _place_room_near_anchor(
        self,
        anchor: Tuple[int, int],
        width: int,
        height: int,
        existing_rooms: List[Room],
        padding: int,
    ) -> Optional[Room]:
        ax, ay = anchor
        for _ in range(120):
            jitter_x = self.rng.randint(-4, 4)
            jitter_y = self.rng.randint(-4, 4)
            x = ax - width // 2 + jitter_x
            y = ay - height // 2 + jitter_y

            x = max(1, min(self.width - width - 2, x))
            y = max(1, min(self.height - height - 2, y))

            room = Room(x=x, y=y, width=width, height=height)
            if any(room.intersects(other, padding=padding) for other in existing_rooms):
                continue
            return room

        return None

    def _place_room_near_host(
        self,
        host: Room,
        width: int,
        height: int,
        existing_rooms: List[Room],
        padding: int,
    ) -> Optional[Room]:
        host_cx, host_cy = host.center
        max_radius = max(self.width, self.height) // 2

        for _ in range(180):
            angle = self.rng.random() * 2 * math.pi
            radius = self.rng.randint(7, max_radius)
            ax = int(host_cx + math.cos(angle) * radius)
            ay = int(host_cy + math.sin(angle) * radius)
            room = self._place_room_near_anchor((ax, ay), width, height, existing_rooms, padding)
            if room:
                return room

        return None

    def _create_room(self, room: Room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                self.grid[y][x] = TileType.FLOOR

        corners = {
            (room.x - 1, room.y - 1),
            (room.x + room.width, room.y - 1),
            (room.x - 1, room.y + room.height),
            (room.x + room.width, room.y + room.height),
        }
        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
                if (x, y) in corners:
                    continue
                if 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == TileType.VOID:
                    self.grid[y][x] = TileType.WALL

    def _create_tunnel(self, start: Tuple[int, int], end: Tuple[int, int]):
        x1, y1 = start
        x2, y2 = end

        if self.rng.random() < 0.5:
            self._h_tunnel(x1, x2, y1)
            self._v_tunnel(y1, y2, x2)
        else:
            self._v_tunnel(y1, y2, x1)
            self._h_tunnel(x1, x2, y2)

    def _h_tunnel(self, x1: int, x2: int, y: int):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if self.grid[y][x] == TileType.VOID:
                self.grid[y][x] = TileType.FLOOR
            elif self.grid[y][x] == TileType.WALL:
                self.grid[y][x] = TileType.DOOR

            if y > 0 and self.grid[y - 1][x] == TileType.VOID:
                self.grid[y - 1][x] = TileType.WALL
            if y < self.height - 1 and self.grid[y + 1][x] == TileType.VOID:
                self.grid[y + 1][x] = TileType.WALL

    def _v_tunnel(self, y1: int, y2: int, x: int):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if self.grid[y][x] == TileType.VOID:
                self.grid[y][x] = TileType.FLOOR
            elif self.grid[y][x] == TileType.WALL:
                self.grid[y][x] = TileType.DOOR

            if x > 0 and self.grid[y][x - 1] == TileType.VOID:
                self.grid[y][x - 1] = TileType.WALL
            if x < self.width - 1 and self.grid[y][x + 1] == TileType.VOID:
                self.grid[y][x + 1] = TileType.WALL

    def _add_corridor_walls(self, path: List[Tuple[int, int]], room_mask: List[List[int]]) -> None:
        path_set = set(path)

        for px, py in path:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = px + dx, py + dy
                if (nx, ny) in path_set:
                    continue
                if self._in_bounds(nx, ny) and self.grid[ny][nx] == TileType.VOID:
                    self.grid[ny][nx] = TileType.WALL

        for px, py in path:
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = px + dx, py + dy
                if (nx, ny) in path_set:
                    continue
                if not (self._in_bounds(nx, ny) and self.grid[ny][nx] == TileType.VOID):
                    continue
                self.grid[ny][nx] = TileType.WALL

