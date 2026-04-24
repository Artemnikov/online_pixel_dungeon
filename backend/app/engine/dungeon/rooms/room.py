"""Base Room + Door abstractions.

Mirrors SPD `levels/rooms/Room.java`. Rooms are inclusive rectangles
(`right` and `bottom` are part of the room), so `width()` returns
`right - left + 1`. Interior cells are strictly inside the 1-tile wall
border: `left < x < right and top < y < bottom`.

Connections are placed on shared edges (canConnect requires the point be
on exactly one edge — no corners). Two rooms must share >= 2 edge tiles
to be neighbours, so a 1-tile door cell never lands at a corner.

Door.Type ordering matters: `set()` only ever upgrades the type
(empty < tunnel < ... < locked < crystal < wall), so a downstream pass
can't accidentally weaken an earlier decision.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple

if TYPE_CHECKING:
    from app.engine.dungeon.painters.level import LevelCanvas


# Direction labels for connection-quota queries. Mirrors SPD Room.ALL/LEFT/...
class Direction(enum.IntEnum):
    ALL = 0
    LEFT = 1
    TOP = 2
    RIGHT = 3
    BOTTOM = 4


class DoorType(enum.IntEnum):
    """Door types ordered for monotonic upgrades.

    Ordering matches SPD Room.Door.Type so that `Door.set(new_type)` can
    only ever strengthen the door (never replace LOCKED with EMPTY).
    Painters request a door type via `Door.set()`; the painter's
    `paint_doors()` resolves the final terrain tile from the type.
    """

    EMPTY = 0
    TUNNEL = 1
    WATER = 2
    REGULAR = 3
    UNLOCKED = 4
    HIDDEN = 5
    BARRICADE = 6
    LOCKED = 7
    CRYSTAL = 8
    WALL = 9


class Door:
    """A single connection point between two rooms."""

    __slots__ = ("x", "y", "type", "_locked")

    def __init__(self, x: int, y: int, door_type: DoorType = DoorType.EMPTY):
        self.x = x
        self.y = y
        self.type: DoorType = door_type
        self._locked = False

    def lock_type_changes(self, lock: bool) -> None:
        self._locked = lock

    def set(self, new_type: DoorType) -> None:
        """Upgrade-only. Calls trying to weaken the type are no-ops."""
        if self._locked:
            return
        if new_type > self.type:
            self.type = new_type

    def __repr__(self) -> str:
        return f"Door({self.x},{self.y},{self.type.name})"


class Room:
    """Inclusive rectangle + connection graph + paint hook.

    SPD's geometric convention: a room with left=0, top=0, right=4, bottom=4
    is 5x5 tiles — both endpoints are part of the room. The outer border
    becomes WALL; the strict interior (1 in from each edge) is room space.
    """

    # Subclasses override these; -1 means "subclass forgot".
    MIN_WIDTH = -1
    MAX_WIDTH = -1
    MIN_HEIGHT = -1
    MAX_HEIGHT = -1

    # Default direction quotas. SPD Room defaults are min=1 ALL, max=16 ALL,
    # max=4 per side.
    MIN_CONNECTIONS = {Direction.ALL: 1}
    MAX_CONNECTIONS = {Direction.ALL: 16, Direction.LEFT: 4, Direction.TOP: 4,
                       Direction.RIGHT: 4, Direction.BOTTOM: 4}

    def __init__(self, left: int = 0, top: int = 0, right: int = 0, bottom: int = 0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

        # Bidirectional graph state populated during build.
        self.neighbours: List[Room] = []
        self.connected: Dict[Room, Optional[Door]] = {}

        # Used by some builders for path planning.
        self.distance: int = 0
        self.price: int = 1

    # ----- size + position -----------------------------------------------
    def min_width(self) -> int: return self.MIN_WIDTH
    def max_width(self) -> int: return self.MAX_WIDTH
    def min_height(self) -> int: return self.MIN_HEIGHT
    def max_height(self) -> int: return self.MAX_HEIGHT

    def width(self) -> int:
        return self.right - self.left + 1

    def height(self) -> int:
        return self.bottom - self.top + 1

    def square(self) -> int:
        return self.width() * self.height()

    def is_empty(self) -> bool:
        return self.left == self.right == self.top == self.bottom == 0

    def set_empty(self) -> None:
        self.left = self.top = self.right = self.bottom = 0

    def set_pos(self, x: int, y: int) -> None:
        w = self.width() - 1
        h = self.height() - 1
        self.left = x
        self.top = y
        self.right = x + w
        self.bottom = y + h

    def shift(self, dx: int, dy: int) -> None:
        self.left += dx
        self.right += dx
        self.top += dy
        self.bottom += dy

    def resize(self, w: int, h: int) -> None:
        """Set width=w+1, height=h+1 (SPD's right/bottom-inclusive rule)."""
        self.right = self.left + w
        self.bottom = self.top + h

    def set_size(self, rng=None,
                 min_w: int = None, max_w: int = None,
                 min_h: int = None, max_h: int = None) -> bool:
        """Roll a random size within both subclass and call-site bounds."""
        if min_w is None: min_w = self.min_width()
        if max_w is None: max_w = self.max_width()
        if min_h is None: min_h = self.min_height()
        if max_h is None: max_h = self.max_height()

        if (min_w < self.min_width() or max_w > self.max_width()
                or min_h < self.min_height() or max_h > self.max_height()
                or min_w > max_w or min_h > max_h):
            return False

        rng_int = rng.randint if rng is not None else __import__("random").randint
        # SPD uses NormalIntRange (mean of two rolls); approximate similarly
        # for slightly-biased-toward-middle sizes.
        w = (rng_int(min_w, max_w) + rng_int(min_w, max_w)) // 2
        h = (rng_int(min_h, max_h) + rng_int(min_h, max_h)) // 2
        self.resize(w - 1, h - 1)
        return True

    def force_size(self, w: int, h: int) -> bool:
        return self.set_size(min_w=w, max_w=w, min_h=h, max_h=h)

    def set_size_with_limit(self, rng, w: int, h: int) -> bool:
        if w < self.min_width() or h < self.min_height():
            return False
        self.set_size(rng=rng)
        if self.width() > w or self.height() > h:
            self.resize(min(self.width(), w) - 1, min(self.height(), h) - 1)
        return True

    # ----- point queries -------------------------------------------------
    def inside(self, p: Tuple[int, int]) -> bool:
        """Strict interior (excludes the wall border)."""
        x, y = p
        return self.left < x < self.right and self.top < y < self.bottom

    def contains_point(self, x: int, y: int) -> bool:
        """Includes the wall border."""
        return self.left <= x <= self.right and self.top <= y <= self.bottom

    def random(self, rng, margin: int = 1) -> Tuple[int, int]:
        return (rng.randint(self.left + margin, self.right - margin),
                rng.randint(self.top + margin, self.bottom - margin))

    def center(self) -> Tuple[int, int]:
        return ((self.left + self.right) // 2, (self.top + self.bottom) // 2)

    # ----- connection logic ---------------------------------------------
    def min_connections(self, direction: Direction = Direction.ALL) -> int:
        return self.MIN_CONNECTIONS.get(direction, 0)

    def max_connections(self, direction: Direction = Direction.ALL) -> int:
        return self.MAX_CONNECTIONS.get(direction, 4 if direction != Direction.ALL else 16)

    def cur_connections(self, direction: Direction = Direction.ALL) -> int:
        if direction == Direction.ALL:
            return len(self.connected)
        total = 0
        for r in self.connected:
            i = self._intersect(r)
            if i is None:
                continue
            il, it, ir, ib = i
            iw = ir - il
            ih = ib - it
            if direction == Direction.LEFT and iw == 0 and il == self.left:
                total += 1
            elif direction == Direction.TOP and ih == 0 and it == self.top:
                total += 1
            elif direction == Direction.RIGHT and iw == 0 and ir == self.right:
                total += 1
            elif direction == Direction.BOTTOM and ih == 0 and ib == self.bottom:
                total += 1
        return total

    def rem_connections(self, direction: Direction = Direction.ALL) -> int:
        if self.cur_connections(Direction.ALL) >= self.max_connections(Direction.ALL):
            return 0
        return self.max_connections(direction) - self.cur_connections(direction)

    def can_connect_point(self, p: Tuple[int, int]) -> bool:
        """Point must be on exactly one edge (no corners)."""
        x, y = p
        on_vertical = (x == self.left or x == self.right)
        on_horizontal = (y == self.top or y == self.bottom)
        return on_vertical != on_horizontal

    def can_connect_direction(self, direction: Direction) -> bool:
        return self.rem_connections(direction) > 0

    def can_connect_room(self, other: Room) -> bool:
        if (self.is_exit() and other.is_entrance()) or (self.is_entrance() and other.is_exit()):
            return False
        i = self._intersect(other)
        if i is None:
            return False
        il, it, ir, ib = i
        # Need at least one shared edge point that both rooms allow.
        for p in self._iter_points(il, it, ir, ib):
            if self.can_connect_point(p) and other.can_connect_point(p):
                break
        else:
            return False
        # Direction quotas.
        iw, ih = ir - il, ib - it
        if iw == 0 and il == self.left:
            return self.can_connect_direction(Direction.LEFT) and other.can_connect_direction(Direction.RIGHT)
        if ih == 0 and it == self.top:
            return self.can_connect_direction(Direction.TOP) and other.can_connect_direction(Direction.BOTTOM)
        if iw == 0 and ir == self.right:
            return self.can_connect_direction(Direction.RIGHT) and other.can_connect_direction(Direction.LEFT)
        if ih == 0 and ib == self.bottom:
            return self.can_connect_direction(Direction.BOTTOM) and other.can_connect_direction(Direction.TOP)
        return False

    def add_neighbour(self, other: Room) -> bool:
        if other in self.neighbours:
            return True
        i = self._intersect(other)
        if i is None:
            return False
        il, it, ir, ib = i
        iw, ih = ir - il, ib - it
        # Need >=2 shared edge tiles so a door can avoid the corners.
        if (iw == 0 and ih >= 2) or (ih == 0 and iw >= 2):
            self.neighbours.append(other)
            other.neighbours.append(self)
            return True
        return False

    def connect(self, other: Room) -> bool:
        if (other in self.neighbours or self.add_neighbour(other)) \
                and other not in self.connected and self.can_connect_room(other):
            self.connected[other] = None
            other.connected[self] = None
            return True
        return False

    def clear_connections(self) -> None:
        for r in list(self.neighbours):
            if self in r.neighbours:
                r.neighbours.remove(self)
        self.neighbours.clear()
        for r in list(self.connected):
            r.connected.pop(self, None)
        self.connected.clear()

    def is_entrance(self) -> bool: return False
    def is_exit(self) -> bool: return False

    # ----- placement filters (subclasses can narrow) --------------------
    def can_place_water(self, p: Tuple[int, int]) -> bool: return True
    def can_place_grass(self, p: Tuple[int, int]) -> bool: return True
    def can_place_trap(self, p: Tuple[int, int]) -> bool: return True
    def can_place_item(self, p: Tuple[int, int]) -> bool: return self.inside(p)
    def can_place_character(self, p: Tuple[int, int]) -> bool: return self.inside(p)

    def water_placeable_points(self) -> List[Tuple[int, int]]:
        return [p for p in self._iter_all_points() if self.can_place_water(p)]

    def grass_placeable_points(self) -> List[Tuple[int, int]]:
        return [p for p in self._iter_all_points() if self.can_place_grass(p)]

    def trap_placeable_points(self) -> List[Tuple[int, int]]:
        return [p for p in self._iter_all_points() if self.can_place_trap(p)]

    # ----- paint hook ----------------------------------------------------
    def paint(self, level: "LevelCanvas") -> None:
        raise NotImplementedError(f"{type(self).__name__}.paint not implemented")

    # ----- internals -----------------------------------------------------
    def _intersect(self, other: Room) -> Optional[Tuple[int, int, int, int]]:
        l = max(self.left, other.left)
        t = max(self.top, other.top)
        r = min(self.right, other.right)
        b = min(self.bottom, other.bottom)
        if l > r or t > b:
            return None
        return l, t, r, b

    def _iter_points(self, l: int, t: int, r: int, b: int) -> Iterable[Tuple[int, int]]:
        for y in range(t, b + 1):
            for x in range(l, r + 1):
                yield (x, y)

    def _iter_all_points(self) -> Iterable[Tuple[int, int]]:
        return self._iter_points(self.left, self.top, self.right, self.bottom)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.left},{self.top},{self.right},{self.bottom})"
