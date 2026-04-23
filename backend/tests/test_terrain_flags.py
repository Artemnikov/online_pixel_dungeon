"""Verifies per-tile flag table and derived bool arrays match SPD semantics.

The Level-equivalent bool maps (passable, solid, los_blocking, etc.) replace
the ad-hoc WALKABLE_TILES / BLOCKS_LOS_TILES sets and are what all LOS,
pathfinding, and placement code now consults.
"""

from app.engine.dungeon.constants import TileType
from app.engine.dungeon.terrain_flags import (
    AVOID,
    FLAMABLE,
    LIQUID,
    LOS_BLOCKING,
    PASSABLE,
    PIT,
    SECRET,
    SOLID,
    TILE_FLAGS,
    build_flag_maps,
    flags_of,
)


def test_flag_table_matches_spd_semantics():
    assert flags_of(TileType.FLOOR) & PASSABLE
    assert not flags_of(TileType.FLOOR) & SOLID

    # Walls block LOS and are solid.
    wall = flags_of(TileType.WALL)
    assert wall & LOS_BLOCKING and wall & SOLID
    assert not wall & PASSABLE

    # Closed door is passable (walking opens it) but also LOS-blocking +
    # SOLID for the closed state. Callers resolve open-state separately.
    door = flags_of(TileType.DOOR)
    assert door & PASSABLE
    assert door & LOS_BLOCKING
    assert door & SOLID

    # Secret door is a wall with the SECRET bit.
    sd = flags_of(TileType.SECRET_DOOR)
    assert sd & SOLID and sd & LOS_BLOCKING and sd & SECRET

    # Grass is flammable, water is liquid.
    assert flags_of(TileType.FLOOR_GRASS) & FLAMABLE
    assert flags_of(TileType.FLOOR_WATER) & LIQUID
    # VOID in the remake represents "outside the play area" (unpainted
    # cells), so it's solid + LOS-blocking — diverges from SPD's CHASM
    # (AVOID | PIT) by design.
    void = flags_of(TileType.VOID)
    assert void & SOLID and void & LOS_BLOCKING

    # High grass blocks LOS.
    assert flags_of(TileType.HIGH_GRASS) & LOS_BLOCKING

    # Unknown tile falls back to SOLID | LOS_BLOCKING (safe default).
    unk = flags_of(999)
    assert unk & SOLID and unk & LOS_BLOCKING


def test_build_flag_maps_simple_room():
    # 5x5 grid with a 3x3 floor room surrounded by WALL. No border row will
    # be "passable" because build_flag_maps forces the outer frame solid.
    W = TileType.WALL
    F = TileType.FLOOR
    grid = [
        [W, W, W, W, W],
        [W, F, F, F, W],
        [W, F, F, F, W],
        [W, F, F, F, W],
        [W, W, W, W, W],
    ]
    maps = build_flag_maps(grid)

    # Interior floors are passable; walls and border are not.
    for y in (1, 2, 3):
        for x in (1, 2, 3):
            assert maps.passable[y][x], (x, y)
            assert not maps.solid[y][x]
            assert not maps.los_blocking[y][x]

    for x in range(5):
        assert not maps.passable[0][x]
        assert not maps.passable[4][x]
        assert maps.solid[0][x]
        assert maps.solid[4][x]

    # open_space: center (2,2) is non-solid and has all non-solid corners.
    assert maps.open_space[2][2]

    # discoverable: every cell inside or adjacent to a non-wall is True;
    # the corners of this tiny map touch a wall-only neighbourhood and are
    # therefore False only if their 3x3 is all wall. At (0,0), the 3x3
    # includes (1,1) which is FLOOR, so (0,0) IS discoverable.
    assert maps.discoverable[0][0]
    # At a purely interior-wall cell there are no non-wall neighbours, so
    # discoverable is False; this tiny map has no such cell, so skip that case.


def test_border_is_always_impassable_even_if_grid_says_otherwise():
    # Grid with FLOOR on the border should still have an impassable frame
    # after build_flag_maps (SPD safety invariant).
    F = TileType.FLOOR
    grid = [[F for _ in range(4)] for _ in range(4)]
    maps = build_flag_maps(grid)
    for x in range(4):
        assert not maps.passable[0][x]
        assert not maps.passable[3][x]
    for y in range(4):
        assert not maps.passable[y][0]
        assert not maps.passable[y][3]


def test_floorstate_rebuild_flags_integration():
    """Going through GameInstance plumbing: flags are populated after gen."""
    from app.engine.manager import GameInstance

    g = GameInstance("flags-test")
    floor = g.generate_floor(1)

    assert floor.flags is not None
    # Entrance cell (STAIRS_UP) should be passable.
    for y, row in enumerate(floor.grid):
        for x, tile in enumerate(row):
            if tile == TileType.STAIRS_UP:
                assert floor.flags.passable[y][x]
                assert not floor.flags.solid[y][x]
                return
    raise AssertionError("No STAIRS_UP tile in generated floor")
