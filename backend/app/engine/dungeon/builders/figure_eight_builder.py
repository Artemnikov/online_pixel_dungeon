"""FigureEightBuilder: two LoopBuilder-style loops meeting at a landmark room.

Port of SPD `levels/builders/FigureEightBuilder.java`. Picks the biggest
main-path multi-connection room as the "landmark" (the pinch point
where the two loops meet), then runs two loop placements 180° apart.
Branches bias toward whichever loop centroid the branch host sits in.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from app.engine.dungeon.builders.builder import Builder
from app.engine.dungeon.builders.regular_builder import RegularBuilder, _weighted_choice
from app.engine.dungeon.rooms.connection import TunnelRoom
from app.engine.dungeon.rooms.room import Direction, Room


class FigureEightBuilder(RegularBuilder):
    def __init__(self, rng=None):
        super().__init__(rng=rng)
        self.curve_exponent: int = 0
        self.curve_intensity: float = 1.0
        self.curve_offset: float = 0.0
        self._first_loop: List[Room] = []
        self._second_loop: List[Room] = []
        self._first_center: Optional[Tuple[float, float]] = None
        self._second_center: Optional[Tuple[float, float]] = None
        self.landmark_room: Optional[Room] = None

    def set_loop_shape(self, exponent: int, intensity: float, offset: float) -> "FigureEightBuilder":
        self.curve_exponent = abs(exponent)
        self.curve_intensity = intensity % 1.0
        self.curve_offset = offset % 0.5
        return self

    def set_landmark_room(self, room: Room) -> "FigureEightBuilder":
        self.landmark_room = room
        return self

    def _target_angle(self, percent_along: float) -> float:
        percent_along += self.curve_offset
        half = percent_along % 0.5
        curved = (math.pow(4, 2 * self.curve_exponent)
                  * math.pow(half - 0.25, 2 * self.curve_exponent + 1)
                  + 0.25 + 0.5 * math.floor(2 * percent_along))
        linear = percent_along
        return 360.0 * (self.curve_intensity * curved
                        + (1 - self.curve_intensity) * linear
                        - self.curve_offset)

    def build(self, rooms: List[Room]) -> Optional[List[Room]]:
        self.setup_rooms(rooms)
        if self.entrance is None:
            return None

        # Pick or accept a landmark room — prefer the largest multi-connection
        # standard room on the main path.
        if self.landmark_room is None:
            for r in self.main_path_rooms:
                if r.max_connections(Direction.ALL) >= 4:
                    if (self.landmark_room is None or
                            r.min_width() * r.min_height() >
                            self.landmark_room.min_width() * self.landmark_room.min_height()):
                        self.landmark_room = r
            if self.landmark_room is None:
                # Fallback: no suitable landmark, degrade to single loop.
                from app.engine.dungeon.builders.loop_builder import LoopBuilder
                lb = LoopBuilder(rng=self.rng)
                lb.set_loop_shape(self.curve_exponent, self.curve_intensity, self.curve_offset)
                # Re-setup the rooms for the fresh builder.
                for r in rooms:
                    r.clear_connections()
                return lb.build(rooms)
            if self.multi_connections:
                self.main_path_rooms.append(self.multi_connections.pop(0))

        if self.landmark_room in self.main_path_rooms:
            self.main_path_rooms.remove(self.landmark_room)
        if self.landmark_room in self.multi_connections:
            self.multi_connections.remove(self.landmark_room)

        start_angle = self.rng.random() * 360.0
        half = len(self.main_path_rooms) // 2
        if len(self.main_path_rooms) % 2 == 1:
            half += self.rng.randint(0, 1)
        remaining = list(self.main_path_rooms)
        first_rooms_tmp: List[Room] = [self.landmark_room]
        for _ in range(min(half, len(remaining))):
            first_rooms_tmp.append(remaining.pop(0))
        first_rooms_tmp.insert((len(first_rooms_tmp) + 1) // 2, self.entrance)

        tunnel_pool = list(self.path_tunnel_chances)
        self._first_loop = self._interleave_tunnels(first_rooms_tmp, tunnel_pool)

        second_rooms_tmp: List[Room] = [self.landmark_room] + remaining
        if self.exit is not None:
            second_rooms_tmp.insert((len(second_rooms_tmp) + 1) // 2, self.exit)
        self._second_loop = self._interleave_tunnels(second_rooms_tmp, tunnel_pool)

        self.landmark_room.set_size(rng=self.rng)
        self.landmark_room.set_pos(0, 0)

        # Run the first loop.
        if not self._place_loop(rooms, self._first_loop, start_angle, self.landmark_room):
            return None
        # Run the second loop 180° rotated.
        if not self._place_loop(rooms, self._second_loop, start_angle + 180.0,
                                 self.landmark_room):
            return None

        # Record centroids for branch biasing.
        self._first_center = _centroid(self._first_loop)
        self._second_center = _centroid(self._second_loop)

        branchable: List[Room] = list(self._first_loop) + list(self._second_loop)
        # Landmark is in both lists; keep only one copy.
        while branchable.count(self.landmark_room) > 1:
            branchable.remove(self.landmark_room)
        weighted = self._weight_rooms(branchable)

        rooms_to_branch = list(self.multi_connections) + list(self.single_connections)
        if not self.create_branches(rooms, weighted, rooms_to_branch,
                                    self.branch_tunnel_chances):
            return None

        Builder.find_neighbours(rooms)
        self.add_extra_connections(rooms)
        return rooms

    # ----- helpers ------------------------------------------------------
    def _interleave_tunnels(self, room_list: List[Room], tunnel_pool: List[float]) -> List[Room]:
        out: List[Room] = []
        for r in room_list:
            out.append(r)
            n = _weighted_choice(self.rng, tunnel_pool)
            if n == -1:
                tunnel_pool[:] = list(self.path_tunnel_chances)
                n = _weighted_choice(self.rng, tunnel_pool)
            if 0 <= n < len(tunnel_pool):
                tunnel_pool[n] = max(0, tunnel_pool[n] - 1)
            for _ in range(max(0, n)):
                out.append(TunnelRoom())
        return out

    def _place_loop(self, rooms: List[Room], loop: List[Room], start_angle: float,
                    anchor: Room) -> bool:
        prev = anchor
        for i in range(1, len(loop)):
            r = loop[i]
            target = start_angle + self._target_angle(i / len(loop))
            if Builder.place_room(self.rng, rooms, prev, r, target) == -1.0:
                return False
            prev = r
            if r not in rooms:
                rooms.append(r)
        # Close.
        tries = 0
        while not prev.connect(anchor):
            tries += 1
            if tries > 20:
                return False
            t = TunnelRoom()
            if Builder.place_room(self.rng, rooms, prev, t,
                                  Builder.angle_between_rooms(prev, anchor)) == -1.0:
                return False
            loop.append(t)
            rooms.append(t)
            prev = t
        return True

    def random_branch_angle(self, r: Room) -> float:
        center = self._first_center if r in self._first_loop else self._second_center
        if center is None:
            return super().random_branch_angle(r)
        rx = (r.left + r.right) / 2.0
        ry = (r.top + r.bottom) / 2.0
        to_center = Builder.angle_between_points(rx, ry, center[0], center[1])
        if to_center < 0:
            to_center += 360.0
        best = self.rng.random() * 360.0
        for _ in range(4):
            cand = self.rng.random() * 360.0
            if abs(to_center - cand) < abs(to_center - best):
                best = cand
        return best


def _centroid(rooms: List[Room]) -> Tuple[float, float]:
    if not rooms:
        return (0.0, 0.0)
    cx = sum((r.left + r.right) / 2.0 for r in rooms) / len(rooms)
    cy = sum((r.top + r.bottom) / 2.0 for r in rooms) / len(rooms)
    return (cx, cy)
