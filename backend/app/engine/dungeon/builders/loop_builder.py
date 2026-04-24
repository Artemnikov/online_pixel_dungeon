"""LoopBuilder: places main-path rooms around a parametric closed curve.

Port of SPD `levels/builders/LoopBuilder.java`. The curve is essentially
a circle (with optional ovality via `curve_exponent`/`curve_intensity`/
`curve_offset`). Rooms are placed sequentially along the curve, then a
closing tunnel chain connects the final room back to the entrance.
Branches fan out from the loop, biased toward the loop centroid so they
don't spiral off into free space.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from app.engine.dungeon.builders.builder import Builder
from app.engine.dungeon.builders.regular_builder import RegularBuilder, _weighted_choice
from app.engine.dungeon.rooms.connection import TunnelRoom
from app.engine.dungeon.rooms.room import Room


class LoopBuilder(RegularBuilder):
    def __init__(self, rng=None):
        super().__init__(rng=rng)
        self.curve_exponent: int = 0
        self.curve_intensity: float = 1.0
        self.curve_offset: float = 0.0
        self._loop_center: Optional[Tuple[float, float]] = None

    def set_loop_shape(self, exponent: int, intensity: float, offset: float) -> "LoopBuilder":
        self.curve_exponent = abs(exponent)
        self.curve_intensity = intensity % 1.0
        self.curve_offset = offset % 0.5
        return self

    def _target_angle(self, percent_along: float) -> float:
        percent_along += self.curve_offset
        linear = percent_along
        curved = self._curve_eq(percent_along)
        return 360.0 * (self.curve_intensity * curved
                        + (1 - self.curve_intensity) * linear
                        - self.curve_offset)

    def _curve_eq(self, x: float) -> float:
        half = x % 0.5
        return (math.pow(4, 2 * self.curve_exponent)
                * math.pow(half - 0.25, 2 * self.curve_exponent + 1)
                + 0.25 + 0.5 * math.floor(2 * x))

    # ----- the build ---------------------------------------------------
    def build(self, rooms: List[Room]) -> Optional[List[Room]]:
        self.setup_rooms(rooms)
        if self.entrance is None:
            return None

        self.entrance.set_size(rng=self.rng)
        self.entrance.set_pos(0, 0)

        start_angle = self.rng.random() * 360.0

        # Interleave tunnels between path rooms.
        path: List[Room] = [self.entrance] + self.main_path_rooms
        if self.exit is not None:
            path.insert((len(path) + 1) // 2, self.exit)

        tunnel_pool = list(self.path_tunnel_chances)
        loop: List[Room] = []
        for r in path:
            loop.append(r)
            n = _weighted_choice(self.rng, tunnel_pool)
            if n == -1:
                tunnel_pool = list(self.path_tunnel_chances)
                n = _weighted_choice(self.rng, tunnel_pool)
            if 0 <= n < len(tunnel_pool):
                tunnel_pool[n] = max(0, tunnel_pool[n] - 1)
            for _ in range(max(0, n)):
                loop.append(TunnelRoom())

        # Sequential placement along the curve.
        prev = self.entrance
        for i in range(1, len(loop)):
            r = loop[i]
            target = start_angle + self._target_angle(i / len(loop))
            angle = Builder.place_room(self.rng, rooms, prev, r, target)
            if angle == -1.0:
                return None
            prev = r
            if r not in rooms:
                rooms.append(r)

        # Close the loop back to entrance. Append tunnels as needed.
        tries = 0
        while not prev.connect(self.entrance):
            tries += 1
            if tries > 20:
                return None
            t = TunnelRoom()
            bridge_angle = Builder.angle_between_rooms(prev, self.entrance)
            if Builder.place_room(self.rng, loop, prev, t, bridge_angle) == -1.0:
                return None
            loop.append(t)
            rooms.append(t)
            prev = t

        # Record loop centroid for branch angle biasing.
        cx = sum((r.left + r.right) / 2.0 for r in loop) / len(loop)
        cy = sum((r.top + r.bottom) / 2.0 for r in loop) / len(loop)
        self._loop_center = (cx, cy)

        # Branch the remaining rooms out.
        branchable = list(loop)
        # Weight pool with size factors.
        weighted = self._weight_rooms(branchable)
        rooms_to_branch = list(self.multi_connections) + list(self.single_connections)
        if not self.create_branches(rooms, weighted, rooms_to_branch,
                                    self.branch_tunnel_chances):
            return None

        # Ensure the neighbour graph is fully populated, then sparse extra loops.
        Builder.find_neighbours(rooms)
        self.add_extra_connections(rooms)
        return rooms

    # ----- centroid-biased branch angle --------------------------------
    def random_branch_angle(self, r: Room) -> float:
        if self._loop_center is None:
            return super().random_branch_angle(r)
        cx, cy = self._loop_center
        rx = (r.left + r.right) / 2.0
        ry = (r.top + r.bottom) / 2.0
        to_center = Builder.angle_between_points(rx, ry, cx, cy)
        if to_center < 0:
            to_center += 360.0
        # Pick the angle closest to `to_center` out of 4 random rolls.
        best = self.rng.random() * 360.0
        for _ in range(4):
            cand = self.rng.random() * 360.0
            if abs(to_center - cand) < abs(to_center - best):
                best = cand
        return best
