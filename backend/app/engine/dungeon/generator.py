import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


class TileType:
    VOID = 0
    WALL = 1
    FLOOR = 2
    DOOR = 3
    STAIRS_UP = 4
    STAIRS_DOWN = 5
    FLOOR_WOOD = 6
    FLOOR_WATER = 7
    FLOOR_COBBLE = 8
    FLOOR_GRASS = 9
    LOCKED_DOOR = 10


class RoomKind:
    STANDARD = "standard"
    SPECIAL = "special"
    HIDDEN = "hidden"


class TrapType:
    WORN_DART = "worn_dart"


@dataclass
class SewersProfile:
    STANDARD_ROOMS_MIN: int = 4
    STANDARD_ROOMS_MAX: int = 6
    SPECIAL_ROOMS_MIN: int = 1
    SPECIAL_ROOMS_MAX: int = 2
    HIDDEN_ROOMS_COUNT: int = 2

    BASE_HIDDEN_DOOR_CHANCE: float = 0.1
    WATER_RATIO: float = 0.30
    GRASS_RATIO: float = 0.20

    TRAPS_MIN: int = 1
    TRAPS_MAX: int = 3
    TRAP_TYPES: Tuple[str, ...] = (TrapType.WORN_DART,)


@dataclass
class Room:
    x: int
    y: int
    width: int
    height: int
    kind: str = RoomKind.STANDARD
    template: str = "standard"
    tags: Set[str] = field(default_factory=set)
    room_id: int = -1

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def intersects(self, other: "Room", padding: int = 1) -> bool:
        return (
            self.x - padding <= other.x + other.width
            and self.x + self.width + padding >= other.x
            and self.y - padding <= other.y + other.height
            and self.y + self.height + padding >= other.y
        )

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def is_perimeter(self, x: int, y: int) -> bool:
        if not self.contains(x, y):
            return False
        return (
            x == self.x
            or x == self.x + self.width - 1
            or y == self.y
            or y == self.y + self.height - 1
        )


@dataclass
class TrapInfo:
    x: int
    y: int
    trap_type: str
    hidden: bool = True
    active: bool = True


@dataclass
class Edge:
    a: int
    b: int
    secret: bool = False
    locked_room_id: Optional[int] = None


@dataclass
class DoorInfo:
    x: int
    y: int
    room_id: int
    actual_tile: int
    can_hide: bool
    force_hidden: bool
    hidden: bool = False


@dataclass
class SewersGenerationMetadata:
    region: str
    layout_kind: str
    room_ids_by_kind: Dict[str, List[int]]
    room_connections: List[Tuple[int, int]]
    hidden_doors: Dict[Tuple[int, int], int]
    locked_doors: Dict[Tuple[int, int], str]
    key_spawns: Dict[str, Tuple[int, int]]
    traps: Dict[Tuple[int, int], TrapInfo]
    start_room_id: int
    end_room_id: int


@dataclass
class SewersGenerationResult:
    grid: List[List[int]]
    rooms: List[Room]
    metadata: SewersGenerationMetadata


class DungeonGenerator:
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

        return self.grid, self.rooms

    def generate_sewers(self, profile: Optional[SewersProfile] = None) -> SewersGenerationResult:
        profile = profile or SewersProfile()

        for _ in range(120):
            try:
                return self._generate_sewers_attempt(profile)
            except RuntimeError:
                continue

        raise RuntimeError("Failed to generate Sewers layout after multiple attempts")

    def _generate_sewers_attempt(self, profile: SewersProfile) -> SewersGenerationResult:
        self.grid = [[TileType.VOID for _ in range(self.width)] for _ in range(self.height)]

        standard_count = random.randint(profile.STANDARD_ROOMS_MIN, profile.STANDARD_ROOMS_MAX)
        special_count = random.randint(profile.SPECIAL_ROOMS_MIN, profile.SPECIAL_ROOMS_MAX)
        hidden_count = profile.HIDDEN_ROOMS_COUNT

        layout_kind = "loop"
        if standard_count >= 5 and random.random() < 0.5:
            layout_kind = "figure_eight"

        standard_rooms = self._place_standard_rooms(standard_count, layout_kind)
        special_rooms = self._place_special_rooms(special_count, standard_rooms)
        hidden_rooms = self._place_hidden_rooms(hidden_count, standard_rooms + special_rooms)

        all_rooms = standard_rooms + special_rooms + hidden_rooms
        for idx, room in enumerate(all_rooms):
            room.room_id = idx

        room_by_id = {room.room_id: room for room in all_rooms}

        core_edges = self._build_core_edges([r.room_id for r in standard_rooms], layout_kind)
        branch_edges = self._build_branch_edges(standard_rooms, special_rooms, hidden_rooms)
        edges = core_edges + branch_edges

        entrance_id, exit_id = self._pick_entrance_and_exit([r.room_id for r in standard_rooms], edges)

        for room in all_rooms:
            self._paint_room(room)

        room_mask = self._build_room_mask(all_rooms)
        hidden_doors: Dict[Tuple[int, int], int] = {}
        locked_doors: Dict[Tuple[int, int], str] = {}
        key_spawns: Dict[str, Tuple[int, int]] = {}

        door_infos: List[DoorInfo] = []
        room_door_positions: Dict[int, List[int]] = {}

        for edge in edges:
            room_a = room_by_id[edge.a]
            room_b = room_by_id[edge.b]

            connection = self._select_connection_points(room_a, room_b)
            if not connection:
                raise RuntimeError("Could not find valid corridor connection")

            door_a, outside_a, door_b, outside_b = connection
            path = self._find_corridor_path(outside_a, outside_b, room_mask)
            if not path:
                raise RuntimeError("Could not route corridor path")

            for px, py in path:
                if self.grid[py][px] in (TileType.VOID, TileType.WALL):
                    self.grid[py][px] = TileType.FLOOR

            lock_key_id = None
            lock_side_room_id = edge.locked_room_id
            if lock_side_room_id is not None:
                lock_key_id = f"sewers_key_{lock_side_room_id}"

            door_a_tile = TileType.DOOR
            door_b_tile = TileType.DOOR

            if lock_side_room_id == room_a.room_id:
                door_a_tile = TileType.LOCKED_DOOR
            elif lock_side_room_id == room_b.room_id:
                door_b_tile = TileType.LOCKED_DOOR

            idx_a = len(door_infos)
            door_infos.append(
                DoorInfo(
                    x=door_a[0],
                    y=door_a[1],
                    room_id=room_a.room_id,
                    actual_tile=door_a_tile,
                    can_hide=(door_a_tile == TileType.DOOR),
                    force_hidden=edge.secret,
                )
            )
            room_door_positions.setdefault(room_a.room_id, []).append(idx_a)

            idx_b = len(door_infos)
            door_infos.append(
                DoorInfo(
                    x=door_b[0],
                    y=door_b[1],
                    room_id=room_b.room_id,
                    actual_tile=door_b_tile,
                    can_hide=(door_b_tile == TileType.DOOR),
                    force_hidden=edge.secret,
                )
            )
            room_door_positions.setdefault(room_b.room_id, []).append(idx_b)

            if lock_key_id:
                if door_a_tile == TileType.LOCKED_DOOR:
                    locked_doors[(door_a[0], door_a[1])] = lock_key_id
                if door_b_tile == TileType.LOCKED_DOOR:
                    locked_doors[(door_b[0], door_b[1])] = lock_key_id

        hidden_prob = (0.5 + profile.BASE_HIDDEN_DOOR_CHANCE) / 2
        for info in door_infos:
            if info.force_hidden:
                info.hidden = True
            elif info.can_hide:
                info.hidden = random.random() < hidden_prob

        standard_room_ids = {room.room_id for room in standard_rooms}
        for room_id in standard_room_ids:
            door_indexes = room_door_positions.get(room_id, [])
            visible_standard_doors = [
                idx
                for idx in door_indexes
                if door_infos[idx].actual_tile == TileType.DOOR and not door_infos[idx].hidden
            ]
            if not visible_standard_doors:
                candidates = [
                    idx
                    for idx in door_indexes
                    if door_infos[idx].actual_tile == TileType.DOOR and not door_infos[idx].force_hidden
                ]
                if candidates:
                    chosen = random.choice(candidates)
                    door_infos[chosen].hidden = False

        doors_by_pos: Dict[Tuple[int, int], List[DoorInfo]] = {}
        for info in door_infos:
            doors_by_pos.setdefault((info.x, info.y), []).append(info)

        for pos, infos in doors_by_pos.items():
            visible = next((info for info in infos if not info.hidden), None)
            if visible is not None:
                self.grid[pos[1]][pos[0]] = visible.actual_tile
                continue

            hidden_info = infos[0]
            self.grid[pos[1]][pos[0]] = TileType.WALL
            hidden_doors[pos] = hidden_info.actual_tile

        ordered_rooms = self._order_rooms_for_compatibility(all_rooms, entrance_id, exit_id)
        self.rooms = ordered_rooms

        entrance_room = room_by_id[entrance_id]
        exit_room = room_by_id[exit_id]
        up_x, up_y = entrance_room.center
        down_x, down_y = exit_room.center
        self.grid[up_y][up_x] = TileType.STAIRS_UP
        self.grid[down_y][down_x] = TileType.STAIRS_DOWN

        traps = self._spawn_sewers_traps(profile, entrance_room, exit_room)
        terrain_excluded = {(up_x, up_y), (down_x, down_y)}
        for room in (entrance_room, exit_room):
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    terrain_excluded.add((x, y))
        self._apply_terrain(profile, traps, terrain_excluded)

        for key_id in sorted(set(locked_doors.values())):
            key_pos = self._pick_key_spawn_position(
                entrance_room=entrance_room,
                exit_room=exit_room,
                hidden_rooms=hidden_rooms,
                locked_doors=locked_doors,
            )
            if not key_pos:
                raise RuntimeError("Could not place key for locked room")
            key_spawns[key_id] = key_pos

        room_ids_by_kind = {
            RoomKind.STANDARD: [room.room_id for room in standard_rooms],
            RoomKind.SPECIAL: [room.room_id for room in special_rooms],
            RoomKind.HIDDEN: [room.room_id for room in hidden_rooms],
        }

        metadata = SewersGenerationMetadata(
            region="sewers",
            layout_kind=layout_kind,
            room_ids_by_kind=room_ids_by_kind,
            room_connections=[(edge.a, edge.b) for edge in edges],
            hidden_doors=hidden_doors,
            locked_doors=locked_doors,
            key_spawns=key_spawns,
            traps=traps,
            start_room_id=entrance_id,
            end_room_id=exit_id,
        )

        return SewersGenerationResult(grid=self.grid, rooms=self.rooms, metadata=metadata)

    def _place_standard_rooms(self, count: int, layout_kind: str) -> List[Room]:
        dims = [
            (
                random.randint(6, 10),
                random.randint(5, 8),
            )
            for _ in range(count)
        ]

        anchors: List[Tuple[int, int]] = []
        cx, cy = self.width // 2, self.height // 2

        if layout_kind == "loop":
            rx = max(10, self.width // 3)
            ry = max(7, self.height // 3)
            for i in range(count):
                angle = (2 * math.pi * i) / count
                ax = int(cx + rx * math.cos(angle))
                ay = int(cy + ry * math.sin(angle))
                anchors.append((ax, ay))
        else:
            largest_idx = max(range(len(dims)), key=lambda idx: dims[idx][0] * dims[idx][1])
            dims[0], dims[largest_idx] = dims[largest_idx], dims[0]
            anchors.append((cx, cy))

            remaining = count - 1
            left_count = (remaining + 1) // 2
            right_count = remaining - left_count

            left_center = (cx - max(10, self.width // 5), cy)
            right_center = (cx + max(10, self.width // 5), cy)
            left_radius = (max(5, self.width // 8), max(4, self.height // 6))
            right_radius = (max(5, self.width // 8), max(4, self.height // 6))

            for i in range(left_count):
                angle = (2 * math.pi * i) / max(1, left_count)
                ax = int(left_center[0] + left_radius[0] * math.cos(angle))
                ay = int(left_center[1] + left_radius[1] * math.sin(angle))
                anchors.append((ax, ay))

            for i in range(right_count):
                angle = (2 * math.pi * i) / max(1, right_count)
                ax = int(right_center[0] + right_radius[0] * math.cos(angle))
                ay = int(right_center[1] + right_radius[1] * math.sin(angle))
                anchors.append((ax, ay))

        rooms: List[Room] = []
        for idx in range(count):
            w, h = dims[idx]
            room = self._place_room_near_anchor(anchors[idx], w, h, rooms, padding=2)
            if not room:
                raise RuntimeError("Failed to place standard room")
            room.kind = RoomKind.STANDARD
            room.template = "standard"
            rooms.append(room)

        return rooms

    def _place_special_rooms(self, count: int, standard_rooms: List[Room]) -> List[Room]:
        templates = [
            {
                "name": "storage",
                "weight": 4,
                "w": (6, 8),
                "h": (5, 7),
                "tags": set(),
                "locked": False,
            },
            {
                "name": "flooded",
                "weight": 3,
                "w": (6, 9),
                "h": (6, 8),
                "tags": set(),
                "locked": False,
            },
            {
                "name": "shrine",
                "weight": 2,
                "w": (5, 7),
                "h": (5, 7),
                "tags": set(),
                "locked": False,
            },
            {
                "name": "treasure_vault",
                "weight": 2,
                "w": (6, 8),
                "h": (5, 7),
                "tags": set(),
                "locked": True,
            },
            {
                "name": "dangerous_arena",
                "weight": 1,
                "w": (7, 9),
                "h": (6, 8),
                "tags": {"dangerous"},
                "locked": False,
            },
        ]

        allowed_templates = [tpl for tpl in templates if "dangerous" not in tpl["tags"]]
        available_templates = list(allowed_templates)

        rooms: List[Room] = []
        lock_assigned = False

        for _ in range(count):
            if not available_templates:
                available_templates = list(allowed_templates)

            weights = [tpl["weight"] for tpl in available_templates]
            template = random.choices(available_templates, weights=weights, k=1)[0]
            available_templates = [tpl for tpl in available_templates if tpl["name"] != template["name"]]

            w = random.randint(template["w"][0], template["w"][1])
            h = random.randint(template["h"][0], template["h"][1])
            host = random.choice(standard_rooms)

            room = self._place_room_near_host(host, w, h, standard_rooms + rooms, padding=2)
            if not room:
                raise RuntimeError("Failed to place special room")

            room.kind = RoomKind.SPECIAL
            room.template = template["name"]
            room.tags = set(template["tags"])
            if template.get("locked") and not lock_assigned:
                room.tags.add("locked")
                lock_assigned = True

            rooms.append(room)

        return rooms

    def _place_hidden_rooms(self, count: int, host_candidates: List[Room]) -> List[Room]:
        rooms: List[Room] = []
        for _ in range(count):
            w = random.randint(5, 7)
            h = random.randint(5, 7)
            host = random.choice(host_candidates)
            room = self._place_room_near_host(host, w, h, host_candidates + rooms, padding=2)
            if not room:
                raise RuntimeError("Failed to place hidden room")
            room.kind = RoomKind.HIDDEN
            room.template = "hidden_cache"
            rooms.append(room)

        return rooms

    def _build_core_edges(self, standard_room_ids: List[int], layout_kind: str) -> List[Edge]:
        edges: List[Edge] = []

        if layout_kind == "loop":
            for idx in range(len(standard_room_ids)):
                a = standard_room_ids[idx]
                b = standard_room_ids[(idx + 1) % len(standard_room_ids)]
                edges.append(Edge(a=a, b=b))
            return edges

        center_id = standard_room_ids[0]
        others = standard_room_ids[1:]
        left_count = (len(others) + 1) // 2
        left = others[:left_count]
        right = others[left_count:]

        for seq in (left, right):
            if not seq:
                continue
            edges.append(Edge(a=center_id, b=seq[0]))
            for idx in range(len(seq) - 1):
                edges.append(Edge(a=seq[idx], b=seq[idx + 1]))
            edges.append(Edge(a=seq[-1], b=center_id))

        return edges

    def _build_branch_edges(
        self,
        standard_rooms: List[Room],
        special_rooms: List[Room],
        hidden_rooms: List[Room],
    ) -> List[Edge]:
        edges: List[Edge] = []
        hosts = list(standard_rooms)

        for room in special_rooms:
            host = min(hosts, key=lambda h: self._center_distance(h.center, room.center))
            locked_room_id = room.room_id if "locked" in room.tags else None
            edges.append(Edge(a=host.room_id, b=room.room_id, locked_room_id=locked_room_id))
            hosts.append(room)

        visible_hosts = standard_rooms + special_rooms
        for room in hidden_rooms:
            host = min(visible_hosts, key=lambda h: self._center_distance(h.center, room.center))
            edges.append(Edge(a=host.room_id, b=room.room_id, secret=True))

        return edges

    def _pick_entrance_and_exit(self, standard_ids: List[int], edges: List[Edge]) -> Tuple[int, int]:
        adjacency: Dict[int, List[int]] = {room_id: [] for room_id in standard_ids}
        for edge in edges:
            if edge.a in adjacency and edge.b in adjacency:
                adjacency[edge.a].append(edge.b)
                adjacency[edge.b].append(edge.a)

        best_pair = (standard_ids[0], standard_ids[-1])
        best_dist = -1

        for source in standard_ids:
            dists = self._bfs_distances(source, adjacency)
            for target in standard_ids:
                if dists.get(target, -1) > best_dist:
                    best_dist = dists[target]
                    best_pair = (source, target)

        return best_pair

    def _order_rooms_for_compatibility(
        self, rooms: List[Room], entrance_id: int, exit_id: int
    ) -> List[Room]:
        entrance = next(room for room in rooms if room.room_id == entrance_id)
        exit_room = next(room for room in rooms if room.room_id == exit_id)
        middle = [room for room in rooms if room.room_id not in {entrance_id, exit_id}]
        return [entrance] + middle + [exit_room]

    def _paint_room(self, room: Room):
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                self.grid[y][x] = TileType.FLOOR

        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    if self.grid[y][x] == TileType.VOID:
                        self.grid[y][x] = TileType.WALL

    def _build_room_mask(self, rooms: List[Room]) -> List[List[int]]:
        mask = [[-1 for _ in range(self.width)] for _ in range(self.height)]
        for room in rooms:
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
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
                door_a = (room_a.x + room_a.width - 1, ya)
                outside_a = (door_a[0] + 1, ya)
                door_b = (room_b.x, yb)
                outside_b = (door_b[0] - 1, yb)
            else:
                ya = random.randint(room_a.y + 1, room_a.y + room_a.height - 2)
                yb = random.randint(room_b.y + 1, room_b.y + room_b.height - 2)
                door_a = (room_a.x, ya)
                outside_a = (door_a[0] - 1, ya)
                door_b = (room_b.x + room_b.width - 1, yb)
                outside_b = (door_b[0] + 1, yb)
        else:
            if by >= ay:
                xa = random.randint(room_a.x + 1, room_a.x + room_a.width - 2)
                xb = random.randint(room_b.x + 1, room_b.x + room_b.width - 2)
                door_a = (xa, room_a.y + room_a.height - 1)
                outside_a = (xa, door_a[1] + 1)
                door_b = (xb, room_b.y)
                outside_b = (xb, door_b[1] - 1)
            else:
                xa = random.randint(room_a.x + 1, room_a.x + room_a.width - 2)
                xb = random.randint(room_b.x + 1, room_b.x + room_b.width - 2)
                door_a = (xa, room_a.y)
                outside_a = (xa, door_a[1] - 1)
                door_b = (xb, room_b.y + room_b.height - 1)
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

        for y in range(room.y - 1, room.y + room.height + 1):
            for x in range(room.x - 1, room.x + room.width + 1):
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
