"""Geometric-kernel tests for the Phase D Builder.place_room.

Verifies the SPD-style placement contract: when place_room succeeds, the
two rooms share at least 2 edge tiles (so a door can avoid corners), do
not overlap each other or the collision set, and become connected in
each other's `connected` graph.
"""

import random

import pytest

from app.engine.dungeon.builders.builder import Builder
from app.engine.dungeon.rooms.standard import EmptyRoom


def _shared_edge_length(a, b) -> int:
    inter = a._intersect(b)
    if inter is None:
        return 0
    l, t, r, btm = inter
    iw = r - l
    ih = btm - t
    if iw == 0:
        return ih + 1
    if ih == 0:
        return iw + 1
    return 0


def _overlap_interior(a, b) -> bool:
    return not (a.right <= b.left or b.right <= a.left
                or a.bottom <= b.top or b.bottom <= a.top)


def test_place_room_succeeds_on_empty_canvas():
    rng = random.Random(123)
    a = EmptyRoom(); a.size_cat = a.size_cat
    a.set_size(rng=rng); a.set_pos(0, 0)
    b = EmptyRoom(); b.size_cat = b.size_cat
    angle = Builder.place_room(rng, [a], a, b, 0.0)
    assert angle != -1.0, "place_room failed on empty canvas"
    assert b in a.connected
    assert a in b.connected
    assert _shared_edge_length(a, b) >= 2


def test_place_room_respects_collision():
    rng = random.Random(99)
    a = EmptyRoom(); a.set_size(rng=rng); a.set_pos(0, 0)
    blocker = EmptyRoom(); blocker.set_size(rng=rng); blocker.set_pos(0, -10)
    c = EmptyRoom()
    angle = Builder.place_room(rng, [a, blocker], a, c, 90.0)
    if angle != -1.0:
        # When placement succeeds, c must not overlap blocker.
        assert not _overlap_interior(c, blocker)


def test_chain_of_three_rooms_all_connected():
    rng = random.Random(7)
    rooms = []
    a = EmptyRoom(); a.set_size(rng=rng); a.set_pos(0, 0)
    rooms.append(a)
    cur = a
    for angle in (0.0, 90.0):
        n = EmptyRoom()
        result = Builder.place_room(rng, rooms, cur, n, angle)
        assert result != -1.0, f"chain step at angle {angle} failed"
        rooms.append(n)
        cur = n
    # Each adjacent pair shares >=2 edge tiles.
    for x, y in zip(rooms, rooms[1:]):
        assert _shared_edge_length(x, y) >= 2
