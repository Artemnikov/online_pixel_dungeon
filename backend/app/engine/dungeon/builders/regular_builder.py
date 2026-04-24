"""RegularBuilder: "main path + branches" layout base class.

Port of SPD `levels/builders/RegularBuilder.java`. Concrete subclasses
(LoopBuilder, FigureEightBuilder, LineBuilder, BranchesBuilder) override
`build()` to shape the main path. The shared `create_branches()` fans
remaining rooms out from the path, optionally interleaving tunnel
(ConnectionRoom) padding rooms. `setup_rooms()` partitions the input
into path/multi/single/shop/entrance/exit and weights larger rooms onto
the main path.
"""

from __future__ import annotations

import random as _random_mod
from typing import List, Optional

from app.engine.dungeon.builders.builder import Builder
from app.engine.dungeon.rooms.connection import ConnectionRoom, TunnelRoom
from app.engine.dungeon.rooms.room import Direction, Room
from app.engine.dungeon.rooms.standard.standard_room import StandardRoom


class RegularBuilder(Builder):
    # Shape knobs — mirror SPD defaults. Subclasses / callers tweak via setters.
    path_variance: float = 45.0
    path_length: float = 0.25
    path_len_jitter_chances: List[float] = [0, 0, 0, 1]
    path_tunnel_chances: List[float] = [2, 2, 1]
    branch_tunnel_chances: List[float] = [1, 1, 0]
    extra_connection_chance: float = 0.30

    def __init__(self, rng=None):
        # RNG is passed through from the orchestrator so all randomness is
        # seeded. Fallback to module RNG only for standalone unit tests.
        self.rng = rng if rng is not None else _random_mod.Random()

        self.entrance: Optional[Room] = None
        self.exit: Optional[Room] = None
        self.shop: Optional[Room] = None
        self.main_path_rooms: List[Room] = []
        self.multi_connections: List[Room] = []
        self.single_connections: List[Room] = []

    # ----- fluent setters ----------------------------------------------
    def set_path_variance(self, v: float) -> "RegularBuilder":
        self.path_variance = v
        return self

    def set_path_length(self, length: float, jitter: List[float]) -> "RegularBuilder":
        self.path_length = length
        self.path_len_jitter_chances = jitter
        return self

    def set_tunnel_length(self, path: List[float], branch: List[float]) -> "RegularBuilder":
        self.path_tunnel_chances = path
        self.branch_tunnel_chances = branch
        return self

    def set_extra_connection_chance(self, chance: float) -> "RegularBuilder":
        self.extra_connection_chance = chance
        return self

    # ----- partitioning ------------------------------------------------
    def setup_rooms(self, rooms: List[Room]) -> None:
        for r in rooms:
            r.set_empty()

        self.entrance = self.exit = self.shop = None
        self.main_path_rooms = []
        self.single_connections = []
        self.multi_connections = []

        for r in rooms:
            if r.is_entrance():
                self.entrance = r
            elif r.is_exit():
                self.exit = r
            elif r.max_connections(Direction.ALL) > 1:
                self.multi_connections.append(r)
            elif r.max_connections(Direction.ALL) == 1:
                self.single_connections.append(r)

        # Weight larger rooms onto the main path (SPD: connectionWeight = sizeFactor^2
        # entries in the shuffle pool), then dedupe and reshuffle.
        weighted = self._weight_rooms(self.multi_connections)
        self.rng.shuffle(weighted)
        # Dedupe preserving order.
        seen = set()
        deduped = []
        for r in weighted:
            if id(r) not in seen:
                seen.add(id(r))
                deduped.append(r)
        self.rng.shuffle(deduped)
        self.multi_connections = deduped

        rooms_on_main = int(len(self.multi_connections) * self.path_length) + \
            _weighted_choice(self.rng, self.path_len_jitter_chances)

        while rooms_on_main > 0 and self.multi_connections:
            r = self.multi_connections.pop(0)
            if isinstance(r, StandardRoom):
                rooms_on_main -= r.size_factor()
            else:
                rooms_on_main -= 1
            self.main_path_rooms.append(r)

    # ----- branching ---------------------------------------------------
    def _weight_rooms(self, rooms: List[Room]) -> List[Room]:
        out = []
        for r in rooms:
            out.append(r)
            if isinstance(r, StandardRoom):
                # sizeFactor - 1 extra copies (NORMAL=0 extras, LARGE=1, GIANT=2).
                for _ in range(max(0, r.size_factor() - 1)):
                    out.append(r)
        return out

    def create_branches(self, rooms: List[Room], branchable: List[Room],
                        rooms_to_branch: List[Room], conn_chances: List[float]) -> bool:
        """For each room in `rooms_to_branch`, pick a branch-host in `branchable`,
        optionally prepend 0..N tunnel rooms, then place the room.

        >100 consecutive failures returns False (caller restarts the whole build).
        """
        i = 0
        failed = 0
        conn_pool = list(conn_chances)

        while i < len(rooms_to_branch):
            if failed > 100:
                return False

            target = rooms_to_branch[i]
            # Pick a branch host. SecretRoom prohibits branching off a
            # ConnectionRoom (not implemented here yet).
            curr = self.rng.choice(branchable)

            n_tunnels = _weighted_choice(self.rng, conn_pool)
            if n_tunnels == -1:
                conn_pool = list(conn_chances)
                n_tunnels = _weighted_choice(self.rng, conn_pool)
            if 0 <= n_tunnels < len(conn_pool):
                conn_pool[n_tunnels] = max(0, conn_pool[n_tunnels] - 1)

            placed_tunnels: List[Room] = []
            ok = True
            for _ in range(n_tunnels):
                tunnel = TunnelRoom()
                angle = -1.0
                for _try in range(3):
                    angle = Builder.place_room(self.rng, rooms, curr, tunnel,
                                                self.random_branch_angle(curr))
                    if angle != -1.0:
                        break
                if angle == -1.0:
                    tunnel.clear_connections()
                    for t in placed_tunnels:
                        t.clear_connections()
                        if t in rooms:
                            rooms.remove(t)
                    ok = False
                    break
                placed_tunnels.append(tunnel)
                rooms.append(tunnel)
                curr = tunnel

            if not ok:
                failed += 1
                continue

            # Place the real room.
            angle = -1.0
            for _try in range(10):
                angle = Builder.place_room(self.rng, rooms, curr, target,
                                            self.random_branch_angle(curr))
                if angle != -1.0:
                    break
            if angle == -1.0:
                target.clear_connections()
                for t in placed_tunnels:
                    t.clear_connections()
                    if t in rooms:
                        rooms.remove(t)
                failed += 1
                continue

            # Feed some newly-placed rooms back into the branchable pool so
            # later branches can grow off them.
            for t in placed_tunnels:
                if self.rng.randint(0, 2) <= 1:
                    branchable.append(t)
            if target.max_connections(Direction.ALL) > 1 and self.rng.randint(0, 2) == 0:
                if isinstance(target, StandardRoom):
                    for _ in range(target.connection_weight()):
                        branchable.append(target)
                else:
                    branchable.append(target)

            i += 1

        return True

    def random_branch_angle(self, r: Room) -> float:
        return self.rng.random() * 360.0

    # ----- post-build sparse loops -------------------------------------
    def add_extra_connections(self, rooms: List[Room]) -> None:
        """After backbone + branches, add shortcut doors between neighbours."""
        for r in rooms:
            for n in list(r.neighbours):
                if n not in r.connected and self.rng.random() < self.extra_connection_chance:
                    r.connect(n)


def _weighted_choice(rng, weights: List[float]) -> int:
    """SPD Random.chances equivalent: pick an index weighted by the list,
    returns -1 if all weights are zero (signals "reset pool")."""
    total = sum(max(0.0, w) for w in weights)
    if total <= 0:
        return -1
    roll = rng.random() * total
    acc = 0.0
    for i, w in enumerate(weights):
        if w <= 0:
            continue
        acc += w
        if roll <= acc:
            return i
    return len(weights) - 1
