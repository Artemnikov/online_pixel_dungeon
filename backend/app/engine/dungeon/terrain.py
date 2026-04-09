import random
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from app.engine.dungeon.constants import TileType, TrapType
from app.engine.dungeon.models import Room, SewersProfile, TrapInfo


class TerrainMixin:
    """Mixin for terrain decoration and trap/key placement."""

    def _apply_terrain(
        self,
        profile: SewersProfile,
        traps: Dict[Tuple[int, int], TrapInfo],
        excluded: Set[Tuple[int, int]],
    ):
        trap_positions = set(traps.keys())
        candidates: List[Tuple[int, int]] = []

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != TileType.FLOOR:
                    continue
                if (x, y) in excluded or (x, y) in trap_positions:
                    continue
                candidates.append((x, y))

        if not candidates:
            return

        random.shuffle(candidates)
        water_count = int(len(candidates) * profile.WATER_RATIO)
        grass_count = int(len(candidates) * profile.GRASS_RATIO)

        water_tiles = candidates[:water_count]
        remaining = candidates[water_count:]
        grass_tiles = remaining[:grass_count]

        for x, y in water_tiles:
            self.grid[y][x] = TileType.FLOOR_WATER
        for x, y in grass_tiles:
            self.grid[y][x] = TileType.FLOOR_GRASS

    def _spawn_sewers_traps(
        self,
        profile: SewersProfile,
        entrance_room: Room,
        exit_room: Room,
    ) -> Dict[Tuple[int, int], TrapInfo]:
        candidates: List[Tuple[int, int]] = []

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != TileType.FLOOR:
                    continue
                if entrance_room.contains(x, y) or exit_room.contains(x, y):
                    continue
                candidates.append((x, y))

        if not candidates:
            return {}

        random.shuffle(candidates)
        trap_count = min(len(candidates), random.randint(profile.TRAPS_MIN, profile.TRAPS_MAX))
        traps: Dict[Tuple[int, int], TrapInfo] = {}

        for x, y in candidates[:trap_count]:
            traps[(x, y)] = TrapInfo(x=x, y=y, trap_type=TrapType.WORN_DART)

        return traps

    def _pick_key_spawn_position(
        self,
        entrance_room: Room,
        exit_room: Room,
        hidden_rooms: List[Room],
        locked_doors: Dict[Tuple[int, int], str],
    ) -> Optional[Tuple[int, int]]:
        hidden_room_set = hidden_rooms
        locked_positions = set(locked_doors.keys())
        reachable: Set[Tuple[int, int]] = set()
        start = entrance_room.center
        q = deque([start])
        reachable.add(start)
        passable = {
            TileType.FLOOR,
            TileType.FLOOR_WATER,
            TileType.FLOOR_GRASS,
            TileType.FLOOR_COBBLE,
            TileType.DOOR,
            TileType.STAIRS_UP,
            TileType.STAIRS_DOWN,
        }

        while q:
            cx, cy = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in reachable:
                    continue
                if self.grid[ny][nx] not in passable:
                    continue
                reachable.add((nx, ny))
                q.append((nx, ny))

        candidates: List[Tuple[int, int]] = []
        for x, y in reachable:
            tile = self.grid[y][x]
            if tile not in (TileType.FLOOR, TileType.FLOOR_WATER, TileType.FLOOR_GRASS):
                continue
            if entrance_room.contains(x, y) or exit_room.contains(x, y):
                continue
            if any(room.contains(x, y) for room in hidden_room_set):
                continue
            if (x, y) in locked_positions:
                continue
            candidates.append((x, y))

        if not candidates:
            return None

        return random.choice(candidates)
