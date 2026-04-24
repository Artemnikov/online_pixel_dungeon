"""Base Builder + geometric placement kernel.

Port of SPD `levels/builders/Builder.java`. The critical piece is
`place_room(collision, prev, next, angle)` — project a line from prev's
centre at the given angle (0 = straight up, CW positive), figure out
which edge of `prev` it exits, find the largest free rectangle reaching
from that edge, size `next` to fit, then slide it to guarantee at least
a 2-tile shared edge. Returns the realised angle or -1 on failure.

Every concrete Builder subclass uses this kernel plus `find_neighbours`
(to populate the neighbour graph after placement) and the utility
`angle_between_rooms` / `angle_between_points` helpers.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from app.engine.dungeon.rooms.room import Direction, Room


# Python equivalent of SPD's A = 180/pi (degree <-> radian converter).
_DEG_PER_RAD = 180.0 / math.pi


class Builder:
    def build(self, rooms: List[Room]) -> Optional[List[Room]]:
        raise NotImplementedError

    # ----- neighbour graph ----------------------------------------------
    @staticmethod
    def find_neighbours(rooms: List[Room]) -> None:
        """O(n^2) pass to populate Room.neighbours across the placed set."""
        for i, a in enumerate(rooms):
            for b in rooms[i + 1:]:
                a.add_neighbour(b)

    # ----- geometry helpers --------------------------------------------
    @staticmethod
    def angle_between_points(fx: float, fy: float, tx: float, ty: float) -> float:
        """Return the angle in degrees from `from` to `to`, 0 = straight up."""
        if tx == fx:
            return 0.0 if ty < fy else 180.0
        slope = (ty - fy) / (tx - fx)
        angle = _DEG_PER_RAD * (math.atan(slope) + math.pi / 2.0)
        if fx > tx:
            angle -= 180.0
        return angle

    @staticmethod
    def angle_between_rooms(a: Room, b: Room) -> float:
        ax = (a.left + a.right) / 2.0
        ay = (a.top + a.bottom) / 2.0
        bx = (b.left + b.right) / 2.0
        by = (b.top + b.bottom) / 2.0
        return Builder.angle_between_points(ax, ay, bx, by)

    # ----- free-space search (SPD Builder.findFreeSpace) ---------------
    @staticmethod
    def find_free_space(start: Tuple[int, int], collision: List[Room],
                         max_size: int) -> Tuple[int, int, int, int]:
        """Largest axis-aligned rectangle around `start` not hitting any room."""
        sx, sy = start
        left, top = sx - max_size, sy - max_size
        right, bottom = sx + max_size, sy + max_size

        colliding = [r for r in collision if not r.is_empty()]
        while True:
            # Drop rooms that no longer overlap the shrinking rect.
            colliding = [
                r for r in colliding
                if not (max(left, r.left) >= min(right, r.right)
                        or max(top, r.top) >= min(bottom, r.bottom))
            ]
            if not colliding:
                return left, top, right, bottom

            # If `start` is strictly inside some room, that's a zero-size result.
            closest = None
            closest_diff = math.inf
            for r in colliding:
                inside = True
                cur = 0
                if sx <= r.left:
                    inside = False
                    cur += r.left - sx
                elif sx >= r.right:
                    inside = False
                    cur += sx - r.right
                if sy <= r.top:
                    inside = False
                    cur += r.top - sy
                elif sy >= r.bottom:
                    inside = False
                    cur += sy - r.bottom
                if inside:
                    return sx, sy, sx, sy
                if cur < closest_diff:
                    closest_diff = cur
                    closest = r

            if closest is None:
                break

            # Shrink the rect on whichever axis costs less area.
            h = bottom - top + 1
            w = right - left + 1
            w_diff = math.inf
            if closest.left >= sx:
                w_diff = (right - closest.left) * h
            elif closest.right <= sx:
                w_diff = (closest.right - left) * h

            h_diff = math.inf
            if closest.top >= sy:
                h_diff = (bottom - closest.top) * w
            elif closest.bottom <= sy:
                h_diff = (closest.bottom - top) * w

            if w_diff < h_diff:
                if closest.left >= sx and closest.left < right:
                    right = closest.left
                if closest.right <= sx and closest.right > left:
                    left = closest.right
            else:
                if closest.top >= sy and closest.top < bottom:
                    bottom = closest.top
                if closest.bottom <= sy and closest.bottom > top:
                    top = closest.bottom
            colliding.remove(closest)

        return left, top, right, bottom

    # ----- the geometric kernel ----------------------------------------
    @staticmethod
    def place_room(rng, collision: List[Room], prev: Room, new: Room, angle: float) -> float:
        """Try to place `new` so the line from prev's centre at `angle` hits it.

        Returns the realised angle between `prev` and `new` centres on
        success, or -1 on failure (caller should try a different angle).
        """
        angle = angle % 360.0
        if angle < 0:
            angle += 360.0

        pcx = (prev.left + prev.right) / 2.0
        pcy = (prev.top + prev.bottom) / 2.0

        # Line y = m*x + b
        m = math.tan(angle / _DEG_PER_RAD + math.pi / 2.0)
        b = pcy - m * pcx

        # Pick which edge of `prev` the line exits through.
        if abs(m) >= 1:
            if angle < 90 or angle > 270:
                direction = Direction.TOP
                start = (round((prev.top - b) / m), prev.top)
            else:
                direction = Direction.BOTTOM
                start = (round((prev.bottom - b) / m), prev.bottom)
        else:
            if angle < 180:
                direction = Direction.RIGHT
                start = (prev.right, round(m * prev.right + b))
            else:
                direction = Direction.LEFT
                start = (prev.left, round(m * prev.left + b))

        # Clamp the start point off the corners (doors can't be at corners).
        sx, sy = start
        if direction in (Direction.TOP, Direction.BOTTOM):
            sx = max(prev.left + 1, min(sx, prev.right - 1))
        else:
            sy = max(prev.top + 1, min(sy, prev.bottom - 1))
        start = (sx, sy)

        # Max size hint — large enough that a reasonably-sized room fits.
        max_dim = max(new.max_width(), new.max_height())
        l, t, r, bot = Builder.find_free_space(start, collision, max_dim)
        avail_w = r - l + 1
        avail_h = bot - t + 1
        if not new.set_size_with_limit(rng, avail_w, avail_h):
            return -1.0

        # Target centre — continue the line from prev, offset by new's
        # half-dimensions.
        nw = new.width()
        nh = new.height()
        if direction == Direction.TOP:
            tcy = prev.top - (nh - 1) / 2.0
            tcx = (tcy - b) / m
            new.set_pos(round(tcx - (nw - 1) / 2.0), prev.top - (nh - 1))
        elif direction == Direction.BOTTOM:
            tcy = prev.bottom + (nh - 1) / 2.0
            tcx = (tcy - b) / m
            new.set_pos(round(tcx - (nw - 1) / 2.0), prev.bottom)
        elif direction == Direction.RIGHT:
            tcx = prev.right + (nw - 1) / 2.0
            tcy = m * tcx + b
            new.set_pos(prev.right, round(tcy - (nh - 1) / 2.0))
        else:  # LEFT
            tcx = prev.left - (nw - 1) / 2.0
            tcy = m * tcx + b
            new.set_pos(prev.left - (nw - 1), round(tcy - (nh - 1) / 2.0))

        # Slide `new` so there's always a >= 2-tile shared edge and we stay
        # inside the free space.
        if direction in (Direction.TOP, Direction.BOTTOM):
            if new.right < prev.left + 2:
                new.shift(prev.left + 2 - new.right, 0)
            elif new.left > prev.right - 2:
                new.shift(prev.right - 2 - new.left, 0)
            if new.right > r:
                new.shift(r - new.right, 0)
            elif new.left < l:
                new.shift(l - new.left, 0)
        else:
            if new.bottom < prev.top + 2:
                new.shift(0, prev.top + 2 - new.bottom)
            elif new.top > prev.bottom - 2:
                new.shift(0, prev.bottom - 2 - new.top)
            if new.bottom > bot:
                new.shift(0, bot - new.bottom)
            elif new.top < t:
                new.shift(0, t - new.top)

        if new.connect(prev):
            return Builder.angle_between_rooms(prev, new)
        return -1.0
