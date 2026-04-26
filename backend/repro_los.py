"""Reproduce: Bresenham FOV leaks vision through wall corners diagonally.

Layout (width=9):

    012345678
  0 #########
  1 ####W####    <- the room's south wall; the BUG-VISIBLE wall is at (4,1)
  2 ###..e###    <- (3,2)/(4,2) are the corridor's mouth, (5..) is the room
  3 ###.#####    <- 1-tile corridor; (3,3) corridor floor, (4,3) corridor wall
  4 ###P#####    <- player at (3,4); (4,4) corridor wall
  5 #########

Player can NOT see (4,2) directly — the LOS line (3,4)→(4,2) crosses the
wall at (4,3) or (3,3)/(4,4) corner. It SHOULD also not see (4,1), since
the only physical paths to (4,1) go through (4,2) (which is itself blocked
from view).

But the Bresenham implementation in `_is_in_los`:
  iter 1  (3,4)→(3,3)   cardinal        floor    OK
  iter 2  (3,3)→(4,2)   diagonal step   skips (4,3) WALL — leak!
  iter 3  (4,2)→(4,1)   cardinal        target hit
returns True. The wall (4,1) lights up "behind" the corridor wall (4,3).

That matches the user's report: from a corridor you see the corridor wall
AND the room wall on the other side of it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.engine.dungeon.constants import TileType
from app.engine.dungeon.terrain_flags import build_flag_maps
from app.engine.entities.base import Position
from app.engine.manager import GameInstance


_M = {
    '#': TileType.WALL,
    '.': TileType.FLOOR,
    'e': TileType.EMPTY_DECO,
    'W': TileType.WALL,
    'P': TileType.FLOOR,
}
_INV = {TileType.WALL: '#', TileType.FLOOR: '.', TileType.EMPTY_DECO: 'e'}


def install(g, rows):
    floor = g._get_or_create_floor(g.depth)
    floor.grid = [[_M[c] for c in r] for r in rows]
    g.height = len(rows)
    g.width = len(rows[0])
    floor.flags = build_flag_maps(floor.grid)


def show(g, p):
    floor = g._get_or_create_floor(g.depth)
    vis = set(g.get_visible_tiles(p, radius=8))
    for y, row in enumerate(floor.grid):
        line = "  "
        for x, t in enumerate(row):
            ch = '@' if (x, y) == (p.x, p.y) else _INV[t]
            line += ch if (x, y) in vis else '·'
        print(line)


print("=== Bresenham FOV corner-leak repro ===")
g = GameInstance("repro")
install(g, [
    "#########",  # y=0
    "####W####",  # y=1  (4,1) WALL — should be invisible
    "###..e###",  # y=2  corridor mouth + alcove (e)
    "###.#####",  # y=3  corridor + corridor wall at (4,3)
    "###P#####",  # y=4  player + corridor wall at (4,4)
    "#########",  # y=5
])
p = Position(x=3, y=4)
show(g, p)

print()
print("Key checks (player 3,4):")
for tx, ty, label in [
    (4, 4, "(4,4) corridor wall — adjacent, expected visible"),
    (4, 3, "(4,3) corridor wall above first — expected visible"),
    (4, 2, "(4,2) alcove cell  — line crosses (4,3) wall, expected NOT visible"),
    (4, 1, "(4,1) ROOM WALL behind corridor wall — BUG if visible"),
    (5, 1, "(5,1) further-east room wall — BUG if visible"),
]:
    r = g._is_in_los(p, Position(x=tx, y=ty))
    print(f"  _is_in_los → ({tx},{ty}) : {r}    {label}")
