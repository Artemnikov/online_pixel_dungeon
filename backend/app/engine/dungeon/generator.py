import random
from collections import deque
from typing import Dict, List, Optional, Tuple

from app.engine.dungeon.constants import RoomKind, TileType, TrapType  # noqa: F401 — re-exported
from app.engine.dungeon.models import Room, SewersGenerationResult, SewersProfile, TrapInfo  # noqa: F401 — re-exported
from app.engine.dungeon.corridors import CorridorsMixin
from app.engine.dungeon.sewers_generation import SewersGenerationMixin
from app.engine.dungeon.terrain import TerrainMixin


class DungeonGenerator(SewersGenerationMixin, CorridorsMixin, TerrainMixin):
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[TileType.VOID for _ in range(width)] for _ in range(height)]
        self.rooms: List[Room] = []

    def generate(
        self, max_rooms: int, min_room_size: int, max_room_size: int
    ) -> Tuple[List[List[int]], List[Room]]:
        self.rooms = []

        max_retries = 10
        for _ in range(max_retries):
            self.grid = [[TileType.VOID for _ in range(self.width)] for _ in range(self.height)]
            self.rooms = []

            for _ in range(max_rooms):
                w = random.randint(min_room_size, max_room_size)
                h = random.randint(min_room_size, max_room_size)
                x = random.randint(1, self.width - w - 1)
                y = random.randint(1, self.height - h - 1)

                new_room = Room(x, y, w, h)

                if any(new_room.intersects(other) for other in self.rooms):
                    continue

                self._create_room(new_room)

                if self.rooms:
                    prev_center = self.rooms[-1].center
                    new_center = new_room.center
                    self._create_tunnel(prev_center, new_center)

                self.rooms.append(new_room)

            if self.is_connected() and len(self.rooms) > 1:
                break

        if self.rooms:
            up_x, up_y = self.rooms[0].center
            down_x, down_y = self.rooms[-1].center
            self.grid[up_y][up_x] = TileType.STAIRS_UP
            self.grid[down_y][down_x] = TileType.STAIRS_DOWN

        self._classify_walls()
        return self.grid, self.rooms

    def generate_sewers(self, profile: Optional[SewersProfile] = None) -> SewersGenerationResult:
        profile = profile or SewersProfile()

        for _ in range(120):
            try:
                return self._generate_sewers_attempt(profile)
            except RuntimeError:
                continue

        raise RuntimeError("Failed to generate Sewers layout after multiple attempts")

    def is_connected(self) -> bool:
        if not self.rooms:
            return True

        start_x, start_y = self.rooms[0].center
        if self.grid[start_y][start_x] == TileType.WALL:
            return False

        q = deque([(start_x, start_y)])
        visited = {(start_x, start_y)}

        while q:
            cx, cy = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited:
                    tile = self.grid[ny][nx]
                    if tile != TileType.WALL and tile != TileType.VOID:
                        visited.add((nx, ny))
                        q.append((nx, ny))

        for room in self.rooms:
            if room.center not in visited:
                return False
        return True

    def _bfs_distances(self, source: int, adjacency: Dict[int, List[int]]) -> Dict[int, int]:
        q = deque([source])
        dist = {source: 0}

        while q:
            node = q.popleft()
            for neigh in adjacency.get(node, []):
                if neigh in dist:
                    continue
                dist[neigh] = dist[node] + 1
                q.append(neigh)

        return dist

    def _center_distance(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height


if __name__ == "__main__":
    gen = DungeonGenerator(60, 40)
    result = gen.generate_sewers()
    grid = result.grid
    for row in grid:
        print(
            "".join(
                [
                    "#" if t == TileType.WALL else "." if t in (TileType.FLOOR, TileType.FLOOR_GRASS) else "U" if t == TileType.STAIRS_UP else "D" if t == TileType.STAIRS_DOWN else " "
                    for t in row
                ]
            )
        )
