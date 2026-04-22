import math
import random
from typing import Dict, List, Optional, Tuple

from app.engine.dungeon.constants import RoomKind, TileType
from app.engine.dungeon.models import (
    DoorInfo,
    Edge,
    Room,
    SewersGenerationMetadata,
    SewersGenerationResult,
    SewersProfile,
    TrapInfo,
)


class SewersGenerationMixin:
    """Mixin for the sewers dungeon layout: room placement, topology, and corridor wiring."""

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

            self._add_corridor_walls(path, room_mask)

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

        self._classify_walls()
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
