"""SewerPainter: region-specific decoration for the Sewers biome.

Port of SPD `levels/painters/SewerPainter.java`. Two passes:

1. WALL -> WALL_DECO when the cell directly below is WATER. Mimics the
   hanging plants / grates above water in SPD.
2. FLOOR -> EMPTY_DECO with chance proportional to (wall_count / 4)^2.
   Scatters decorative floor tiles near walls.
"""

from __future__ import annotations

from typing import List

from app.engine.dungeon.constants import TileType
from app.engine.dungeon.painters.level import LevelCanvas
from app.engine.dungeon.painters.regular_painter import RegularPainter
from app.engine.dungeon.rooms.room import Room


_WALL_SET = {TileType.WALL, TileType.WALL_DECO}


class SewerPainter(RegularPainter):
    def decorate(self, level: LevelCanvas, rooms: List[Room]) -> None:
        w = level.width
        h = level.height
        g = level.grid
        rng = self.rng

        # Pass 1: WALL above water -> WALL_DECO.
        for y in range(h - 1):
            row = g[y]
            below = g[y + 1]
            for x in range(w):
                if row[x] != TileType.WALL:
                    continue
                if below[x] != TileType.FLOOR_WATER:
                    continue
                above = g[y - 1][x] if y > 0 else TileType.VOID
                chance = 0.50 if above == TileType.WALL else 0.25
                if rng.random() < chance:
                    row[x] = TileType.WALL_DECO

        # Pass 2: FLOOR near walls -> EMPTY_DECO, higher chance the more
        # walls around it (SPD uses count^2 / 16).
        for y in range(h):
            for x in range(w):
                if g[y][x] != TileType.FLOOR:
                    continue
                wc = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and g[ny][nx] in _WALL_SET:
                            wc += 1
                if rng.random() < (wc ** 2) / 16.0:
                    g[y][x] = TileType.EMPTY_DECO
