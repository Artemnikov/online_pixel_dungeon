"""LevelCanvas: the drawing surface Painters operate on.

Holds the raw tile grid (2D int list) plus metadata that paint steps
need (entrance/exit positions, RNG for deterministic painting, tile-ID
aliases so room implementations read like `level.WALL` instead of
importing the TileType enum directly). This isolates the tile ID
vocabulary used by paint() from the backend's TileType enum.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from app.engine.dungeon.constants import TileType


class LevelCanvas:
    # Tile-ID aliases — room paint() methods use these so they don't have
    # to import TileType.
    VOID = TileType.VOID
    WALL = TileType.WALL
    FLOOR = TileType.FLOOR
    DOOR = TileType.DOOR
    STAIRS_UP = TileType.STAIRS_UP
    STAIRS_DOWN = TileType.STAIRS_DOWN
    FLOOR_WATER = TileType.FLOOR_WATER
    FLOOR_GRASS = TileType.FLOOR_GRASS
    HIGH_GRASS = TileType.HIGH_GRASS
    WALL_DECO = TileType.WALL_DECO
    EMPTY_DECO = TileType.EMPTY_DECO
    LOCKED_DOOR = TileType.LOCKED_DOOR
    SECRET_DOOR = TileType.SECRET_DOOR

    def __init__(self, width: int, height: int, rng, fill: int = TileType.WALL):
        self.rng = rng
        self._fill = fill
        self.entrance: Optional[Tuple[int, int]] = None
        self.exit: Optional[Tuple[int, int]] = None
        self.width = width
        self.height = height
        self.grid: List[List[int]] = [[fill for _ in range(width)] for _ in range(height)]

    def resize(self, width: int, height: int) -> None:
        """Reallocate the grid with the given size, filled with the original
        fill tile. Painter calls this once it knows the room bounding box."""
        self.width = width
        self.height = height
        self.grid = [[self._fill for _ in range(width)] for _ in range(height)]

    def set_tile(self, x: int, y: int, tile: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile

    def get_tile(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return TileType.VOID

    def fill_rect(self, l: int, t: int, r: int, b: int, tile: int) -> None:
        """Inclusive fill — matches SPD's Painter.fill semantics for Rooms."""
        for y in range(max(0, t), min(self.height, b + 1)):
            row = self.grid[y]
            for x in range(max(0, l), min(self.width, r + 1)):
                row[x] = tile

    def tunnel_tile(self) -> int:
        """Tile ID used for tunnel floors. SPD varies this for chasm levels;
        the remake only has one floor ID so return it directly."""
        return TileType.FLOOR
