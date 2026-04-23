"""Regression tests for deterministic per-seed dungeon generation.

Mirrors the intent of SPD's `Dungeon.seedCurDepth()` — the same seed produces
the same map, so a client reconnecting to a game session sees the same floor.
"""

from app.engine.dungeon.generator import DungeonGenerator


def _gen(seed: int):
    generator = DungeonGenerator(width=64, height=40, seed=seed)
    return generator.generate_sewers()


def test_same_seed_produces_identical_grid():
    a = _gen(42)
    b = _gen(42)
    assert a.grid == b.grid
    assert [r.room_id for r in a.rooms] == [r.room_id for r in b.rooms]
    assert a.metadata.layout_kind == b.metadata.layout_kind
    assert a.metadata.seed == 42 == b.metadata.seed


def test_different_seeds_produce_different_grids():
    a = _gen(1)
    b = _gen(2)
    # Not a strict guarantee, but the collision probability on a 64x40 grid
    # with two distinct seeds is effectively zero.
    assert a.grid != b.grid


def test_none_seed_still_works():
    # Fallback path should not crash and should produce a valid grid.
    generator = DungeonGenerator(width=64, height=40)
    result = generator.generate_sewers()
    assert result.grid and result.rooms
    assert result.metadata.seed > 0
