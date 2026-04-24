"""Orchestrator for the new SPD-style sewers pipeline.

Builds a list of Rooms, hands them to a LoopBuilder or FigureEightBuilder
to assign rectangles + connections, then to a SewerPainter to stamp the
tile grid. Returns a SewersGenerationResult that's shape-compatible with
the legacy mixin's output so GameInstance can swap pipelines without
touching downstream code.

This is the D-phase replacement for sewers_generation.py's monolithic
`_generate_sewers_attempt`. It currently covers: entrance + exit, N
standard rooms (as EmptyRoom), tunnel corridors, doors (regular +
hidden), water/grass blobs, decorate pass. It does NOT yet cover:
special/hidden/shop rooms, locked-door+key gating, traps. Those remain
in the legacy path until ported in a follow-up.
"""

from __future__ import annotations

import random
from typing import List, Optional

from app.engine.dungeon.builders import FigureEightBuilder, LoopBuilder
from app.engine.dungeon.constants import RoomKind, TileType
from app.engine.dungeon.models import (
    Room as LegacyRoom,
    SewersGenerationMetadata,
    SewersGenerationResult,
    SewersProfile,
)
from app.engine.dungeon.painters import LevelCanvas, SewerPainter
from app.engine.dungeon.rooms.room import Room
from app.engine.dungeon.rooms.standard import EmptyRoom, EntranceRoom, ExitRoom


def generate_sewers_level(width: int, height: int, profile: SewersProfile,
                           seed: Optional[int] = None) -> SewersGenerationResult:
    rng = random.Random(seed if seed is not None else random.Random().getrandbits(32))

    # --- 1. Build the room list -----------------------------------------
    standard_count = rng.randint(profile.STANDARD_ROOMS_MIN, profile.STANDARD_ROOMS_MAX)

    entrance = EntranceRoom()
    entrance.size_cat = _roll_size_cat(entrance, rng)
    exit_room = ExitRoom()
    exit_room.size_cat = _roll_size_cat(exit_room, rng)

    init_rooms: List[Room] = [entrance, exit_room]
    for _ in range(standard_count):
        r = EmptyRoom()
        r.size_cat = _roll_size_cat(r, rng)
        init_rooms.append(r)

    # --- 2. Run the builder with up to ~20 attempts ---------------------
    rooms: Optional[List[Room]] = None
    for _ in range(20):
        for r in init_rooms:
            r.clear_connections()
            r.set_empty()
        # Pick layout randomly like the legacy path did.
        if standard_count >= 5 and rng.random() < 0.5:
            builder = (FigureEightBuilder(rng=rng)
                        .set_loop_shape(2, rng.uniform(0.3, 0.8), 0.0))
        else:
            builder = (LoopBuilder(rng=rng)
                        .set_loop_shape(2, rng.uniform(0.0, 0.65),
                                         rng.uniform(0.0, 0.50)))
        rooms = builder.build(list(init_rooms))
        if rooms is not None:
            break

    if rooms is None:
        raise RuntimeError("Sewers builder failed after 20 attempts")

    # --- 3. Paint -------------------------------------------------------
    canvas = LevelCanvas(width, height, rng, fill=TileType.WALL)
    painter = (SewerPainter(rng=rng, depth=profile.depth)
               .set_water(profile.WATER_RATIO, 5)
               .set_grass(profile.GRASS_RATIO, 4))
    if not painter.paint(canvas, rooms):
        raise RuntimeError("Sewers painter produced nothing")

    # --- 4. Convert to legacy shape (exclusive width/height) ------------
    # Downstream code (GameInstance, tests, AI) uses legacy Room where x,y
    # is the top-left floor cell and width/height count interior cells only
    # (walls are outside). Map each SPD-style Room's interior to that shape.
    # Skip ConnectionRooms — legacy code has no equivalent; its corridors
    # are implicit in the grid.
    from app.engine.dungeon.rooms.connection import ConnectionRoom
    id_for_new = {}
    legacy_rooms: List[LegacyRoom] = []
    for new_r in rooms:
        if isinstance(new_r, ConnectionRoom):
            continue
        rid = len(legacy_rooms)
        id_for_new[id(new_r)] = rid
        legacy_rooms.append(LegacyRoom(
            x=new_r.left + 1,
            y=new_r.top + 1,
            width=max(0, new_r.right - new_r.left - 1),
            height=max(0, new_r.bottom - new_r.top - 1),
            kind=RoomKind.STANDARD,
            room_id=rid,
        ))

    # Find entrance/exit IDs in the new-to-legacy mapping.
    entrance_id = id_for_new.get(id(entrance), 0)
    exit_id = id_for_new.get(id(exit_room), legacy_rooms[-1].room_id if legacy_rooms else 0)

    # Collapse the builder's Room graph (which includes ConnectionRooms as
    # transit nodes) down to an edge list over just the "real" rooms. From
    # each real room, BFS through any chain of ConnectionRooms and record
    # an edge to every real room the chain reaches.
    edges = []
    seen = set()
    from collections import deque
    for start_new in rooms:
        if id(start_new) not in id_for_new:
            continue
        a_id = id_for_new[id(start_new)]
        visited = {id(start_new)}
        q = deque(start_new.connected)
        while q:
            cur = q.popleft()
            if id(cur) in visited:
                continue
            visited.add(id(cur))
            if id(cur) in id_for_new:
                # Real-room endpoint — record the edge, don't traverse further.
                key = tuple(sorted((a_id, id_for_new[id(cur)])))
                if key not in seen:
                    seen.add(key)
                    edges.append(key)
                continue
            # Pass-through: keep walking through this ConnectionRoom.
            for onward in cur.connected:
                if id(onward) not in visited:
                    q.append(onward)

    metadata = SewersGenerationMetadata(
        region="sewers",
        layout_kind="loop_v2",
        room_ids_by_kind={
            RoomKind.STANDARD: [lr.room_id for lr in legacy_rooms],
            RoomKind.SPECIAL: [],
            RoomKind.HIDDEN: [],
        },
        room_connections=edges,
        hidden_doors={},  # door-type HIDDEN is rendered as SECRET_DOOR directly
        locked_doors={},
        key_spawns={},
        traps={},
        start_room_id=entrance_id,
        end_room_id=exit_id,
        seed=seed or 0,
    )
    return SewersGenerationResult(grid=canvas.grid, rooms=legacy_rooms, metadata=metadata)


def _roll_size_cat(room, rng):
    room.set_size_cat(rng)
    return room.size_cat
