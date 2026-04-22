import math
import random
from collections import deque
from typing import Dict, List, Optional, Tuple

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
        self, room_a: Room, room_b: Room
    ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
        ax, ay = room_a.center
        bx, by = room_b.center

        if abs(bx - ax) >= abs(by - ay):
            if bx >= ax:
                ya = random.randint(room_a.y + 1, room_a.y + room_a.height - 2)
                yb = random.randint(room_b.y + 1, room_b.y + room_b.height - 2)
                door_a = (room_a.x + room_a.width, ya)
                outside_a = (door_a[0] + 1, ya)
                door_b = (room_b.x - 1, yb)
                outside_b = (door_b[0] - 1, yb)
            else:
                ya = random.randint(room_a.y + 1, room_a.y + room_a.height - 2)
                yb = random.randint(room_b.y + 1, room_b.y + room_b.height - 2)
                door_a = (room_a.x - 1, ya)
                outside_a = (door_a[0] - 1, ya)
                door_b = (room_b.x + room_b.width, yb)
                outside_b = (door_b[0] + 1, yb)
        else:
            if by >= ay:
                xa = random.randint(room_a.x + 1, room_a.x + room_a.width - 2)
                xb = random.randint(room_b.x + 1, room_b.x + room_b.width - 2)
                door_a = (xa, room_a.y + room_a.height)
                outside_a = (xa, door_a[1] + 1)
                door_b = (xb, room_b.y - 1)
                outside_b = (xb, door_b[1] - 1)
            else:
                xa = random.randint(room_a.x + 1, room_a.x + room_a.width - 2)
                xb = random.randint(room_b.x + 1, room_b.x + room_b.width - 2)
                door_a = (xa, room_a.y - 1)
                outside_a = (xa, door_a[1] - 1)
                door_b = (xb, room_b.y + room_b.height)
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
            jitter_x = random.randint(-4, 4)
            jitter_y = random.randint(-4, 4)
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
            angle = random.random() * 2 * math.pi
            radius = random.randint(7, max_radius)
            ax = int(host_cx + math.cos(angle) * radius)
            ay = int(host_cy + math.sin(angle) * radius)
            room = self._place_room_near_anchor((ax, ay), width, height, existing_rooms, padding)
            if room:
                return room

        return None

    def _create_room(self, room: Room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                floor_type = random.choice(
                    [
                        TileType.FLOOR,
                        TileType.FLOOR,
                        TileType.FLOOR,
                        TileType.FLOOR_WOOD,
                        TileType.FLOOR_WATER,
                        TileType.FLOOR_COBBLE,
                    ]
                )
                self.grid[y][x] = floor_type

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

        if random.random() < 0.5:
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

        def adjacent_to_room(px: int, py: int) -> bool:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = px + dx, py + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and room_mask[ny][nx] != -1:
                    return True
            return False

        for px, py in path:
            if adjacent_to_room(px, py):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = px + dx, py + dy
                if (nx, ny) in path_set:
                    continue
                if self._in_bounds(nx, ny) and self.grid[ny][nx] == TileType.VOID:
                    self.grid[ny][nx] = TileType.WALL
        for px, py in path:
            if adjacent_to_room(px, py):
                continue
            for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, ny = px + dx, py + dy
                if (nx, ny) in path_set:
                    continue
                if not (self._in_bounds(nx, ny) and self.grid[ny][nx] == TileType.VOID):
                    continue
                if dy < 0:
                    self.grid[ny][nx] = TileType.WALL_LEFT if dx < 0 else TileType.WALL_RIGHT
                else:
                    self.grid[ny][nx] = TileType.WALL_BOTTOM_LEFT if dx < 0 else TileType.WALL_BOTTOM_RIGHT

    def _classify_walls(self) -> None:
        walkable = {
            TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP,
            TileType.STAIRS_DOWN, TileType.FLOOR_WOOD, TileType.FLOOR_WATER,
            TileType.FLOOR_COBBLE, TileType.FLOOR_GRASS, TileType.LOCKED_DOOR,
        }
        # First pass: classify room wall rings by geometry — authoritative and
        # immune to corridor-adjacency ambiguity.
        room_classified: set = set()
        for room in self.rooms:
            top_y    = room.y - 1
            bottom_y = room.y + room.height
            left_x   = room.x - 1
            right_x  = room.x + room.width
            # Top row (face south toward room floor)
            if 0 <= top_y < self.height:
                for x in range(room.x - 1, room.x + room.width + 1):
                    if 0 <= x < self.width and self.grid[top_y][x] == TileType.WALL:
                        self.grid[top_y][x] = TileType.WALL_TOP
                        room_classified.add((x, top_y))
            # Bottom row (face north toward room floor)
            if 0 <= bottom_y < self.height:
                for x in range(room.x - 1, room.x + room.width + 1):
                    if 0 <= x < self.width and self.grid[bottom_y][x] == TileType.WALL:
                        self.grid[bottom_y][x] = TileType.WALL_BOTTOM
                        room_classified.add((x, bottom_y))
            # Left column (face east toward room floor)
            if 0 <= left_x < self.width:
                for y in range(room.y, room.y + room.height):
                    if 0 <= y < self.height and self.grid[y][left_x] == TileType.WALL:
                        self.grid[y][left_x] = TileType.WALL_LEFT
                        room_classified.add((left_x, y))
            # Right column (face west toward room floor)
            if 0 <= right_x < self.width:
                for y in range(room.y, room.y + room.height):
                    if 0 <= y < self.height and self.grid[y][right_x] == TileType.WALL:
                        self.grid[y][right_x] = TileType.WALL_RIGHT
                        room_classified.add((right_x, y))
        # Second pass: classify corridor walls that were not part of any room
        # wall ring, using neighbor-based heuristic.
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in room_classified or self.grid[y][x] != TileType.WALL:
                    continue
                south = y + 1 < self.height and self.grid[y + 1][x] in walkable
                north = y - 1 >= 0          and self.grid[y - 1][x] in walkable
                east  = x + 1 < self.width  and self.grid[y][x + 1] in walkable
                west  = x - 1 >= 0          and self.grid[y][x - 1] in walkable
                if south:        self.grid[y][x] = TileType.WALL_TOP
                elif north:      self.grid[y][x] = TileType.WALL_BOTTOM
                elif east:       self.grid[y][x] = TileType.WALL_LEFT
                elif west:       self.grid[y][x] = TileType.WALL_RIGHT
        # Final pass: fix room corners — top corners extend side walls, bottom corners cleared.
        for room in self.rooms:
            for cx, cy, tile in (
                (room.x - 1,          room.y - 1,          TileType.WALL_LEFT),
                (room.x + room.width,  room.y - 1,          TileType.WALL_RIGHT),
                (room.x - 1,          room.y + room.height, TileType.WALL_BOTTOM_LEFT),
                (room.x + room.width,  room.y + room.height, TileType.WALL_BOTTOM_RIGHT),
            ):
                if 0 <= cx < self.width and 0 <= cy < self.height:
                    self.grid[cy][cx] = tile
