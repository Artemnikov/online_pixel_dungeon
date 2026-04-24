"""RegularPainter: the full per-room paint pipeline.

Port of SPD `levels/painters/RegularPainter.java`. Steps (in order):

1. Compute bounding box of all rooms + 1-tile padding, allocate the
   LevelCanvas at that size, shift every room so (0,0) sits at the
   top-left padding corner.
2. For each room (shuffled): place_doors() picks a door Point on each
   shared edge, then r.paint(level) stamps walls/floor/contents.
3. paint_doors() walks every connection exactly once and overwrites
   the door cell with the terrain matching Door.type. Hidden-door
   rolls are guarded by a BFS reachability check — hiding a door that
   isolates a StandardRoom from the rest of the graph is rolled back
   to UNLOCKED.
4. paint_water / paint_grass via Patch-CA blobs, masked by per-room
   canPlaceWater/Grass filters.
5. Region-specific decorate(), implemented by subclasses.
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, List, Optional, Set

from app.engine.dungeon.constants import TileType
from app.engine.dungeon.painters.level import LevelCanvas
from app.engine.dungeon.painters.patch import generate_patch
from app.engine.dungeon.painters.painter import Painter
from app.engine.dungeon.rooms.connection import ConnectionRoom
from app.engine.dungeon.rooms.room import Door, DoorType, Room


# Door.Type -> terrain tile ID.
_DOOR_TYPE_TILE = {
    DoorType.EMPTY: TileType.FLOOR,
    DoorType.TUNNEL: TileType.FLOOR,
    DoorType.WATER: TileType.FLOOR_WATER,
    DoorType.REGULAR: TileType.DOOR,
    DoorType.UNLOCKED: TileType.DOOR,
    DoorType.HIDDEN: TileType.SECRET_DOOR,
    DoorType.BARRICADE: TileType.WALL,  # remake has no barricade tile yet
    DoorType.LOCKED: TileType.LOCKED_DOOR,
    DoorType.CRYSTAL: TileType.LOCKED_DOOR,  # no crystal-door tile yet
    DoorType.WALL: TileType.WALL,
}


class RegularPainter(Painter):
    def __init__(self, rng, depth: int = 1):
        self.rng = rng
        self.depth = depth
        self.water_fill = 0.0
        self.water_smoothness = 0
        self.grass_fill = 0.0
        self.grass_smoothness = 0

    # ----- fluent setters ----------------------------------------------
    def set_water(self, fill: float, smoothness: int) -> "RegularPainter":
        self.water_fill = fill
        self.water_smoothness = smoothness
        return self

    def set_grass(self, fill: float, smoothness: int) -> "RegularPainter":
        self.grass_fill = fill
        self.grass_smoothness = smoothness
        return self

    # ----- main pipeline ------------------------------------------------
    def paint(self, level: LevelCanvas, rooms: List[Room]) -> bool:
        if not rooms:
            return False

        self._shift_rooms(rooms)
        self._allocate_level_for(level, rooms)

        order = list(rooms)
        self.rng.shuffle(order)
        for r in order:
            if not r.connected:
                # A placed room with zero connections is useless (can't enter).
                # SPD just logs it; we do the same and keep going.
                continue
            self._place_doors(r)
            r.paint(level)

        self._paint_doors(level, rooms)

        if self.water_fill > 0:
            self._paint_water(level, rooms)
        if self.grass_fill > 0:
            self._paint_grass(level, rooms)

        self.decorate(level, rooms)
        return True

    # Subclass hook.
    def decorate(self, level: LevelCanvas, rooms: List[Room]) -> None:
        pass

    # ----- setup --------------------------------------------------------
    def _shift_rooms(self, rooms: List[Room]) -> None:
        padding = 1
        left_most = min(r.left for r in rooms) - padding
        top_most = min(r.top for r in rooms) - padding
        for r in rooms:
            r.shift(-left_most, -top_most)

    def _allocate_level_for(self, level: LevelCanvas, rooms: List[Room]) -> None:
        padding = 1
        right_most = max(r.right for r in rooms) + padding
        bottom_most = max(r.bottom for r in rooms) + padding
        # +1 for inclusive coordinates; SPD does the same setSize math.
        level.resize(right_most + 1, bottom_most + 1)

    # ----- door placement ---------------------------------------------
    def _place_doors(self, r: Room) -> None:
        for n, existing in r.connected.items():
            if existing is not None:
                continue
            inter = r._intersect(n)
            if inter is None:
                continue
            il, it, ir, ib = inter
            candidates = [(x, y) for y in range(it, ib + 1) for x in range(il, ir + 1)
                          if r.can_connect_point((x, y)) and n.can_connect_point((x, y))]
            if not candidates:
                continue
            px, py = self.rng.choice(candidates)
            door = Door(px, py)
            r.connected[n] = door
            n.connected[r] = door

    # ----- door painting (tile overlay) -------------------------------
    def _paint_doors(self, level: LevelCanvas, rooms: List[Room]) -> None:
        # Depth-scaled hidden-door chance. SPD: min(1, depth/20).
        hidden_chance = 0.0 if self.depth <= 1 else min(1.0, self.depth / 20.0)

        processed: Set[int] = set()  # id(door) so symmetric entries paint once
        for r in rooms:
            for n, door in r.connected.items():
                if door is None or id(door) in processed:
                    continue
                processed.add(id(door))

                if door.type == DoorType.REGULAR:
                    if self.rng.random() < hidden_chance:
                        door.type = DoorType.HIDDEN
                        # Guard: if hiding isolates a StandardRoom, rollback.
                        if not _all_standard_rooms_reachable(rooms, r):
                            door.type = DoorType.UNLOCKED
                    else:
                        door.type = DoorType.UNLOCKED

                level.set_tile(door.x, door.y,
                               _DOOR_TYPE_TILE.get(door.type, TileType.DOOR))

    # ----- water / grass / decor --------------------------------------
    def _paint_water(self, level: LevelCanvas, rooms: List[Room]) -> None:
        blob = generate_patch(self.rng, level.width, level.height,
                              self.water_fill, self.water_smoothness, True)
        for r in rooms:
            for (x, y) in r.water_placeable_points():
                if blob[y][x] and level.grid[y][x] == TileType.FLOOR:
                    level.grid[y][x] = TileType.FLOOR_WATER

    def _paint_grass(self, level: LevelCanvas, rooms: List[Room]) -> None:
        blob = generate_patch(self.rng, level.width, level.height,
                              self.grass_fill, self.grass_smoothness, True)
        # Mark grass cells first, then upgrade to HIGH_GRASS by neighbour count.
        grass_cells: List = []
        for r in rooms:
            for (x, y) in r.grass_placeable_points():
                if blob[y][x] and level.grid[y][x] == TileType.FLOOR:
                    grass_cells.append((x, y))
        for (x, y) in grass_cells:
            count = 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < level.width and 0 <= ny < level.height and blob[ny][nx]:
                        count += 1
            if self.rng.random() < count / 12.0:
                level.grid[y][x] = TileType.HIGH_GRASS
            else:
                level.grid[y][x] = TileType.FLOOR_GRASS


def _all_standard_rooms_reachable(rooms: List[Room], start: Room) -> bool:
    """BFS over the connection graph using only non-HIDDEN doors.

    Mirrors SPD's Graph.buildDistanceMap-based guard in paintDoors.
    Called after a door is tentatively promoted to HIDDEN; if any
    StandardRoom becomes unreachable from `start`, the caller rolls back.
    """
    from app.engine.dungeon.rooms.standard import StandardRoom
    seen = {id(start)}
    q = deque([start])
    while q:
        cur = q.popleft()
        for other, door in cur.connected.items():
            if door is not None and door.type == DoorType.HIDDEN:
                continue
            if id(other) in seen:
                continue
            seen.add(id(other))
            q.append(other)
    for r in rooms:
        if isinstance(r, StandardRoom) and id(r) not in seen:
            return False
    return True
