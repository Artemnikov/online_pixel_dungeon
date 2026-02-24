from collections import deque

from app.engine.dungeon.generator import RoomKind, TileType, TrapType
from app.engine.manager import GameInstance


WALKABLE_TILES = {
    TileType.FLOOR,
    TileType.DOOR,
    TileType.STAIRS_UP,
    TileType.STAIRS_DOWN,
    TileType.FLOOR_WOOD,
    TileType.FLOOR_WATER,
    TileType.FLOOR_COBBLE,
    TileType.FLOOR_GRASS,
}


def _find_tile(grid, tile_type):
    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == tile_type:
                return (x, y)
    return None


def _is_in_room(rooms, x, y):
    for room in rooms:
        if room.contains(x, y):
            return True
    return False


def _is_in_safe_room(rooms, x, y):
    if not rooms:
        return False
    return rooms[0].contains(x, y) or rooms[-1].contains(x, y)


def _reachable_from_start(grid, start):
    q = deque([start])
    visited = {start}

    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= ny < len(grid) and 0 <= nx < len(grid[0])):
                continue
            if (nx, ny) in visited:
                continue
            if grid[ny][nx] not in WALKABLE_TILES:
                continue
            visited.add((nx, ny))
            q.append((nx, ny))

    return visited


def test_sewers_room_allocation_and_layout_contracts():
    game = GameInstance("sewers-contracts")

    for _ in range(30):
        floor = game.generate_floor(1)
        meta = floor.generation_meta
        room_ids_by_kind = meta["room_ids_by_kind"]

        assert 4 <= len(room_ids_by_kind[RoomKind.STANDARD]) <= 6
        assert 1 <= len(room_ids_by_kind[RoomKind.SPECIAL]) <= 2
        assert len(room_ids_by_kind[RoomKind.HIDDEN]) == 2

        assert meta["layout_kind"] in {"loop", "figure_eight"}

        if meta["layout_kind"] == "figure_eight":
            room_by_id = {room.room_id: room for room in floor.rooms}
            standard_rooms = [room_by_id[rid] for rid in room_ids_by_kind[RoomKind.STANDARD]]
            largest = max(standard_rooms, key=lambda room: room.width * room.height)
            cx, cy = largest.center
            assert abs(cx - (game.width // 2)) <= 4
            assert abs(cy - (game.height // 2)) <= 4


def test_sewers_doors_keys_and_hidden_connections_contracts():
    game = GameInstance("sewers-doors")

    for _ in range(25):
        floor = game.generate_floor(1)
        room_by_id = {room.room_id: room for room in floor.rooms}
        room_ids_by_kind = floor.generation_meta["room_ids_by_kind"]

        door_positions = []
        for y, row in enumerate(floor.grid):
            for x, tile in enumerate(row):
                if tile in (TileType.DOOR, TileType.LOCKED_DOOR):
                    door_positions.append((x, y, tile))

        assert door_positions

        for x, y, _ in door_positions:
            room_neighbors = [room for room in floor.rooms if room.is_perimeter(x, y)]
            assert room_neighbors, f"Door at {(x, y)} is not on room perimeter"

            has_corridor_side = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= ny < len(floor.grid) and 0 <= nx < len(floor.grid[0])):
                    continue
                if floor.grid[ny][nx] in WALKABLE_TILES and not _is_in_room(floor.rooms, nx, ny):
                    has_corridor_side = True
                    break
            assert has_corridor_side, f"Door at {(x, y)} does not meet a corridor"

        for room_id in room_ids_by_kind[RoomKind.STANDARD]:
            room = room_by_id[room_id]
            visible_doors = []
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    if not room.is_perimeter(x, y):
                        continue
                    if floor.grid[y][x] in (TileType.DOOR, TileType.LOCKED_DOOR):
                        visible_doors.append((x, y))
            assert visible_doors, f"Standard room {room_id} has no visible doors"

        hidden_door_positions = set(floor.hidden_doors.keys())
        for room_id in room_ids_by_kind[RoomKind.HIDDEN]:
            room = room_by_id[room_id]
            room_hidden = [
                pos
                for pos in hidden_door_positions
                if room.is_perimeter(pos[0], pos[1])
            ]
            assert room_hidden, f"Hidden room {room_id} does not connect via hidden door"

        if floor.locked_doors:
            key_items = [item for item in floor.items.values() if getattr(item, "type", "") == "key"]
            key_by_key_id = {item.key_id: item for item in key_items}

            stairs_up = _find_tile(floor.grid, TileType.STAIRS_UP)
            assert stairs_up is not None
            reachable = _reachable_from_start(floor.grid, stairs_up)

            for _, key_id in floor.locked_doors.items():
                assert key_id in key_by_key_id
                key_item = key_by_key_id[key_id]
                assert key_item.pos is not None
                assert (key_item.pos.x, key_item.pos.y) in reachable


def test_sewers_terrain_and_trap_contracts():
    game = GameInstance("sewers-terrain")

    samples = 80
    terrain_total = 0
    water_total = 0
    grass_total = 0

    for _ in range(samples):
        floor = game.generate_floor(1)

        for y, row in enumerate(floor.grid):
            for x, tile in enumerate(row):
                if _is_in_safe_room(floor.rooms, x, y):
                    continue
                if tile not in (TileType.FLOOR, TileType.FLOOR_WATER, TileType.FLOOR_GRASS):
                    continue
                terrain_total += 1
                if tile == TileType.FLOOR_WATER:
                    water_total += 1
                elif tile == TileType.FLOOR_GRASS:
                    grass_total += 1

        assert 1 <= len(floor.traps) <= 3
        for trap in floor.traps.values():
            assert trap.trap_type == TrapType.WORN_DART

    assert terrain_total > 0
    water_ratio = water_total / terrain_total
    grass_ratio = grass_total / terrain_total

    assert abs(water_ratio - 0.30) <= 0.03
    assert abs(grass_ratio - 0.20) <= 0.03


def test_sewers_corridors_are_single_tile_wide():
    game = GameInstance("sewers-corridors")

    floor = game.generate_floor(1)
    corridor_tiles = set()

    for y, row in enumerate(floor.grid):
        for x, tile in enumerate(row):
            if tile not in (TileType.FLOOR, TileType.FLOOR_WATER, TileType.FLOOR_GRASS, TileType.FLOOR_COBBLE):
                continue
            if _is_in_room(floor.rooms, x, y):
                continue
            corridor_tiles.add((x, y))

    for y in range(game.height - 1):
        for x in range(game.width - 1):
            block = {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)}
            assert not block.issubset(corridor_tiles), "Found 2x2 corridor block"
